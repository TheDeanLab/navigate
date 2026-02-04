import math
import numpy as np
import glfw
import glm
from typing import Union
import threading
import queue
import time
import traceback
import logging
import json
import cv2

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.model.concurrency.concurrency_tools import SharedNDArray
from navigate.tools.decorators import performance_monitor

logger = None
if __name__ != "__main__":
    # Logger Setup
    p = __name__.split(".")[1]
    logger = logging.getLogger(p)

GL = None

RING_BUF_SIZE = 6

# SHADERS

VERT_SRC = """
// RAYMARCH_VERT_SRC
#version 430 core

out vec2 vUV;

void main()
{
    // 3 vertices: (0,0), (2,0), (0,2) in [0,2] → NDC [-1,1]
    vec2 p = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2);

    gl_Position = vec4(p*2.0 - 1.0, 0.0, 1.0);

    // uv [0..1] across viewport
    vUV = p;    
}
"""

FRAG_2D_SRC = """
#version 430 core
in vec2 vUV;
out vec4 FragColor;

uniform sampler2D pixels;
uniform vec2 viewportSize;
uniform vec2 cMinMax   = vec2(0, 65535);
uniform bool crosshair = true;

// zoom uniforms
uniform float zoom     = 1.0;
uniform vec2  focusUV  = vec2(0.5); // default center
uniform vec2  panPIX   = vec2(0.0); // default none

void main()
{
    // pixel pan to UV pan
    vec2 texSize = vec2(textureSize(pixels, 0));
    vec2 panUV   = panPIX / max(texSize, 1.0);
    
    // zoom centered on focusUV (zoom >= 1.0)
    vec2 uv = focusUV + (vUV - focusUV) / max(zoom, 1.0);
    // pan
    uv += panUV;
    
    // flip?
    // uv.y = 1.0 - uv.y;

    // pixel value
    float s = texture(pixels, uv).r;

    // lut
    float cMin = float(cMinMax.x/65535);
    float cMax = float(cMinMax.y/65535);
    // normalize
    s = (s - cMin) / (cMax - cMin);
    //clamp
    s = clamp(s, 0.0, 1.0);
    
    vec4 outColor = vec4(s, s, s, 1.0);
    
    if (crosshair &&
        (abs(vUV.x - 0.5) < 1.0 / viewportSize.x ||
         abs(vUV.y - 0.5) < 1.0 / viewportSize.y)) 
    {
        outColor = vec4(1.0);
    }

    FragColor = outColor;
}

"""

FRAG_3D_SRC = """
// RAYMARCH_FRAG_SRC  —  raymarch with shear (Y by Z) + step-size invariant opacity
#version 430 core

out vec4 FragColor;

uniform sampler3D volume;
uniform sampler2D transfer;

uniform mat4 invProjView;
uniform vec2 viewportSize;

uniform vec3 boxMin;
uniform vec3 boxMax;

uniform float stepWorld;       // step length in WORLD units

// contrast params
uniform float opacity = 0.15;  // global density/opacity
uniform vec2 cMinMax[4];
uniform float gamma   = 1.0;

// channels
uniform int nChannels = 4;

// OPM parameters
uniform float shear_angle = 50.0;   // degrees
uniform float dz = 0.4;             // um    
uniform float px = 0.1348;          // um

// ---------- utilities ----------

// test intersection
bool intersectAABB(vec3 ro, vec3 rd, vec3 bmin, vec3 bmax, out float t0, out float t1)
{
    vec3 invD = 1.0/rd;
    vec3 tA = (bmin - ro) * invD;
    vec3 tB = (bmax - ro) * invD;
    vec3 tmin = min(tA,tB), tmax = max(tA,tB);
    
    t0 = max(max(tmin.x, tmin.y), tmin.z);
    t1 = min(min(tmax.x, tmax.y), tmax.z);
    
    return t1 > max(t0, 0.0);
}

// OPM shear transform
// Build the inverse of the shear Y -= k*Z
mat4 inverseShearYZ(float angleDeg)
{
    float k = sin(radians(angleDeg));
    mat4 m = mat4(1.0);
    m[1][2] = k;
    
    // need to properly scale somehow: interpolation?
    // m[1][2] = px * k / dz;
    // m[0][0] = dz * k;
    // m[2][2] = dz * cos(radians(angleDeg));

    return m;
}

void main()
{
    // voxel size (um): note that we assume px = py
    vec3 spacing = vec3(px, px, dz);

    // scaled box min/max
    vec3 boxMin_um = boxMin * spacing;
    vec3 boxMax_um = boxMax * spacing;

    // -------- reconstruct world-space ray from pixel --------
    vec2 ndc = (gl_FragCoord.xy / viewportSize) * 2.0 - 1.0;
    vec4 p0w = invProjView * vec4(ndc, -1.0, 1.0);
    vec4 p1w = invProjView * vec4(ndc,  1.0, 1.0);
    vec3 roW = p0w.xyz / p0w.w;
    vec3 rdW = normalize(p1w.xyz / p1w.w - roW);

    // -------- transform ray to OBJECT space via inverse shear --------
    mat4 invShear  = inverseShearYZ(shear_angle);
    vec3 ro = (invShear * vec4(roW, 1.0)).xyz;
    vec3 rd = normalize(mat3(invShear) * rdW);   // direction uses linear part only

    // -------- AABB in object space --------
    float tEnter, tExit;
    if (!intersectAABB(ro, rd, boxMin_um, boxMax_um, tEnter, tExit)) 
        discard;
    tEnter = max(tEnter, 0.0);

    // -------- step-size invariant opacity terms --------
    vec3 dim = vec3(textureSize(volume, 0));       // voxel counts (X,Y,Z)

    // “steps per voxel” along this ray (orientation aware)
    float dVoxel  = max(dot(abs(rd), spacing), 1e-6);
    float kStep   = stepWorld / dVoxel;

    // -------- march --------
    
    vec3 invBoxSize = 1.0 / (boxMax_um - boxMin_um); // um^-1
    
    // accumulator
    vec4 acc = vec4(0.0);

    for (float t = tEnter; t < tExit && acc.a < 0.98; t += stepWorld) {
        vec3 pos = ro + rd * t;                           // position (um)
        vec3 uvw = (pos - boxMin_um) * invBoxSize;           // [0,1]^3

        // sample scalar (all 4 channels in RGBA)
        vec4 s = texture(volume, uvw);            

        for (int i = 0; i < 4; ++i)
        {
            if (i >= nChannels) break;

            // select current channel (rgba)
            float s_i = (i == 0) ? s.r :
                        (i == 1) ? s.g :
                        (i == 2) ? s.b : s.a;
            
            // scale and normalize
            float cMin = cMinMax[i].x;
            float cMax = cMinMax[i].y;
            float sW = (s_i - cMin) / max(cMax - cMin, 1e-6);
            sW = clamp(sW, 0.0, 1.0);

            // 2D transfer lookup: channels arranged by row
            float row = (float(i) + 0.5) / 4.0; // normalized row position
            vec4 tf = texture(transfer, vec2(sW, row));

            // don't composite zeros
            if (tf.rgb == vec3(0.0)) continue;

            // optional gamma
            vec3 rgb = tf.rgb;
            if (gamma != 1.0) rgb = pow(rgb, vec3(gamma));

            // Beer-Lambert step-invariant opacity based on tf.alpha
            float a = 1.0 - exp(-opacity * tf.a * kStep);
            vec3  c = rgb * a;

            // front-to-back premultiplied composite
            acc.rgb += (1.0 - acc.a) * c;
            acc.a   += (1.0 - acc.a) * a;
        }
    }
    
    FragColor = acc;
}

"""

class Shader:
    def __init__(self, vs, fs):
        
        v = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(v, vs)
        GL.glCompileShader(v)
        if not GL.glGetShaderiv(v, GL.GL_COMPILE_STATUS): 
            raise RuntimeError(GL.glGetShaderInfoLog(v).decode())
        
        f = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(f, fs) 
        GL.glCompileShader(f)
        if not GL.glGetShaderiv(f, GL.GL_COMPILE_STATUS): 
            raise RuntimeError(GL.glGetShaderInfoLog(f).decode())
        
        p = GL.glCreateProgram()
        GL.glAttachShader(p, v)
        GL.glAttachShader(p, f)
        GL.glLinkProgram(p)
        
        if not GL.glGetProgramiv(p, GL.GL_LINK_STATUS): 
            raise RuntimeError(GL.glGetProgramInfoLog(p).decode())
        
        GL.glDeleteShader(v)
        GL.glDeleteShader(f)
        
        self.id = p
        self._loc = {}
    
    def __del__(self):
        try:
            if getattr(self, "id", None) and GL.glIsProgram(self.id):
                GL.glDeleteProgram(self.id)
        except Exception: 
            pass
    
    def use(self): 
        GL.glUseProgram(self.id)
    
    def loc(self, name): 
        if name not in self._loc: 
            self._loc[name] = GL.glGetUniformLocation(self.id, name)
        
        return self._loc[name]
    
    def set_int(self, name : str, i : int):
        GL.glUniform1i(self.loc(name), i)

    def set_float(self, name : str, f : float):
        GL.glUniform1f(self.loc(name), f)

    def set_vec2(self, name : str, v : Union[list, np.ndarray, glm.vec2]):
        if isinstance(v, glm.vec2):
            v = v.to_list()

        GL.glUniform2fv(self.loc(name), 1, np.float32(v))

    def set_vec3(self, name : str, v : Union[list, np.ndarray, glm.vec3]):
        if isinstance(v, glm.vec3):
            v = v.to_list()

        GL.glUniform3fv(self.loc(name), 1, np.float32(v))

    def set_mat4(self, name : str, m : Union[list, np.ndarray, glm.mat4]):
        if isinstance(m, glm.mat4):
            m = m.to_list()

        GL.glUniformMatrix4fv(self.loc(name), 1, GL.GL_FALSE, np.float32(m))

class Camera:
    """
    Orbit (yaw/pitch + radius), pixel-accurate pan, dolly,
    and auto-recenter pivot to AABB under the cursor on RMB release.
    """
    def __init__(self, window, parent_viewer, position=glm.vec3(0,0,5), look_at=glm.vec3(0,0,0)):
        self.window = window
        self.parent_viewer = parent_viewer

        # window state
        self.win_w = self.win_h = 0
        self.win_x = self.win_y = 0

        # camera params
        self.FOV = 45.0
        self.NEAR_FIELD = 0.1
        self.FAR_FIELD  = 10000.0
        self.world_up   = glm.vec3(0,1,0)
        self.is_ortho_proj = False
        
        # control gains
        self.ROT_SENS   = 0.25   # deg/pixel
        self.PAN_SENS   = 1.0    # world-per-pixel multiplier
        self.ZOOM_SENS  = 2.0
        self.MIN_RADIUS = 0.01
        self.MAX_PITCH  = math.radians(89.0)

        # orbit state
        self.look_at = glm.vec3(look_at)
        off = glm.vec3(position) - self.look_at
        self.radius = float(glm.length(off)) if glm.length(off) > 0 else 1.0
        self.yaw    = math.atan2(off.x, off.z)  # yaw=0 → +Z
        self.pitch  = math.asin(max(-1.0, min(1.0, off.y / max(self.radius, 1e-8))))

        # zoom/pan state (2D)
        self.pan_xy  = [0., 0.]
        self.zoom_xy = 1.0

        # input state
        self.first_mouse = True
        self.last_mouse_x = 0.0
        self.last_mouse_y = 0.0
        self.scroll_offset = 0.0
        self.is_rotating = False
        self.is_translating = False
        self._was_panning = False

        # picking
        self.auto_recenter_on_pan = True
        self._pick_has_box = False  # set via set_pick_box()

        # callbacks
        glfw.set_scroll_callback(self.window, self._scroll_callback)
        glfw.set_mouse_button_callback(self.window, self._button_callback)

        # build initial matrices
        self._recompute_position()
        self.update()

    # ---------- public ----------
    def set_pick_box(self, bmin, bmax):
        """Provide AABB for pivot recenter: glm.vec3(bmin), glm.vec3(bmax)"""
        self._aabb_min = glm.vec3(bmin)
        self._aabb_max = glm.vec3(bmax)
        self._pick_has_box = True

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.look_at, self.up)

    def get_projection_matrix(self):
        if self.is_ortho_proj:
            # projection = glm.ortho(-self.win_h/8, self.win_w/8, -self.win_h/8, self.win_h/8, -1.0, 1.0)
            nz, ny, nx = self.parent_viewer.vol_shape
            opj_size = 25
            projection = glm.ortho(-opj_size, opj_size, -opj_size, opj_size, 0.1, 100.0)
        else:
            projection = glm.perspective(glm.radians(self.FOV), self.aspect_ratio, self.NEAR_FIELD, self.FAR_FIELD)
        
        return projection

    def set_ortho_view(self, pitch: float=0.0, yaw: float=0.0, radius: float=1.0):
        # self.position = glm.vec3(position)
        self.look_at = glm.vec3(0.0)

        self.pitch  = glm.radians(pitch)
        self.yaw    = glm.radians(yaw)
        self.radius = radius

        self._recompute_position()
        self._update_basis()
        self.view = self.get_view_matrix()
        # self.is_ortho_proj = True

    def update(self, dt=0.0):
        # window size/pos
        win_w, win_h = glfw.get_framebuffer_size(self.window)
        win_x, win_y = glfw.get_window_pos(self.window)
        if (win_w, win_h) != (self.win_w, self.win_h) or (win_x, win_y) != (self.win_x, self.win_y):
            self.win_w, self.win_h = win_w, win_h
            self.aspect_ratio = float(self.win_w) / max(1.0, float(self.win_h))
            self.win_x, self.win_y = win_x, win_y
            self.last_mouse_x = float(win_w) * 0.5
            self.last_mouse_y = float(win_h) * 0.5
            self.first_mouse = True

        # inputs
        self._mouse_move()     # pixels are frame-local; don't scale by dt
        self._scroll_move(dt)  # optional dt use is fine

        # bases + matrices
        self._update_basis()
        self.view = self.get_view_matrix()
        self.projection = self.get_projection_matrix()

    def clamp_panning_to_viewport(self, viewport: tuple):
        """
            TODO: Doesn't quite work well on window resize.
            Ok, for now...
        """
        vw, vh = viewport
        px, py = self.pan_xy
        z      = self.zoom_xy

        lim_x, lim_y = ((z-1)*vw/z/2, (z-1)*vh/z/2)
        
        px = np.clip(px, a_min=-lim_x, a_max=lim_x)
        py = np.clip(py, a_min=-lim_y, a_max=lim_y)

        self.pan_xy  = [px, py]
        self.zoom_xy = z

    # ---------- callbacks ----------
    def _scroll_callback(self, window, dx, dy):
        self.scroll_offset = dy

    def _button_callback(self, window, button, action, mods):
        """
            The Camera class is handling mouse events.
            Even in Frame view mode.
            Communicate to GLFrameViewer through parent_viewer.
        """
        viewer = self.parent_viewer

        # if viewer.mode == "volume":
            # 3D Events
        if action == glfw.PRESS:
            if button == glfw.MOUSE_BUTTON_LEFT:
                if viewer.mode == "frame":
                    # right button = crosshair in 2d mode
                    def _do():
                        viewer.crosshair = not viewer.crosshair
                    viewer.cmd_q.put_nowait(_do)
                else:
                    # do 3d rotation
                    self.is_rotating = True
                    self.first_mouse = True                                        
            elif button == glfw.MOUSE_BUTTON_RIGHT:
                self.is_translating = True
                self._was_panning = True
                self.first_mouse = True
        else:
            if button == glfw.MOUSE_BUTTON_LEFT:
                self.is_rotating = False
            elif button == glfw.MOUSE_BUTTON_RIGHT:
                self.is_translating = False
                # on pan end: recenter pivot under cursor
                if self._was_panning and self.auto_recenter_on_pan:
                    self._recenter_pivot_under_cursor()
                self._was_panning = False

    # ---------- internals ----------
    def _recompute_position(self):
        cp = math.cos(self.pitch)
        sp = math.sin(self.pitch)
        cy = math.cos(self.yaw)
        sy = math.sin(self.yaw)
        dir_vec = glm.vec3(cp * sy, sp, cp * cy)  # Y-up, yaw=0 → +Z
        self.position = self.look_at + self.radius * dir_vec

    def _update_basis(self):
        self.front = glm.normalize(self.look_at - self.position)
        self.right = glm.normalize(glm.cross(self.front, self.world_up))
        self.up    = glm.normalize(glm.cross(self.right, self.front))

    def _mouse_move(self):
        # viewer mode governs behaviour
        viewer = self.parent_viewer

        x_pos, y_pos = glfw.get_cursor_pos(self.window)
        if self.first_mouse:
            self.last_mouse_x = x_pos
            self.last_mouse_y = y_pos
            self.first_mouse = False
            return

        dx = x_pos - self.last_mouse_x
        dy = y_pos - self.last_mouse_y
        self.last_mouse_x = x_pos
        self.last_mouse_y = y_pos

        if self.is_rotating:
            # pixels → degrees → radians
            yaw_delta   = math.radians(-dx * self.ROT_SENS)
            pitch_delta = math.radians(-dy * self.ROT_SENS)
            self.yaw   += yaw_delta
            self.pitch += pitch_delta
            self.pitch = max(-self.MAX_PITCH, min(self.MAX_PITCH, self.pitch))
            self._recompute_position()

        elif self.is_translating:
            if viewer.mode == "volume":
                # screen pixels → world units at current radius
                vpp = (2.0 * self.radius * math.tan(math.radians(self.FOV)*0.5)) / max(1.0, float(self.win_h))
                sx = vpp * self.aspect_ratio * self.PAN_SENS
                sy = vpp * self.PAN_SENS
                pan = (-dx) * sx * self.right + (dy) * sy * self.up
                self.look_at  += pan
                self.position += pan
            elif viewer.mode == "frame":
                self.pan_xy = [
                    -(self.last_mouse_x - self.win_w/2),
                      self.last_mouse_y - self.win_h/2
                ]

    def _scroll_move(self, dt):
        if not self.scroll_offset or dt == 0.0:
            return
        elif self.parent_viewer.mode == "volume":
            # exponential dolly on radius
            scale = math.exp(-self.scroll_offset * self.ZOOM_SENS * (dt if dt > 0 else 1.0))
            self.radius = max(self.MIN_RADIUS, self.radius * scale)
            self._recompute_position()
        elif self.parent_viewer.mode == "frame":
            self.zoom_xy = np.clip(
                self.zoom_xy + self.scroll_offset * self.ZOOM_SENS/2.0,
                a_min=1.0,
                a_max=10.0
            )

        self.scroll_offset = 0.0
        
    # ---------- picking helpers ----------
    def _ray_from_screen(self, x, y):
        """Screen (pixels, origin top-left) → world ray (ro, rd)."""
        # screen → NDC
        ndc_x =  2.0 * (x / max(1.0, float(self.win_w))) - 1.0
        ndc_y = -2.0 * (y / max(1.0, float(self.win_h))) + 1.0  # flip Y

        invPV = glm.inverse(self.projection * self.view)
        p0 = invPV * glm.vec4(ndc_x, ndc_y, -1.0, 1.0)
        p1 = invPV * glm.vec4(ndc_x, ndc_y,  1.0, 1.0)
        p0 = glm.vec3(p0.x/p0.w, p0.y/p0.w, p0.z/p0.w)
        p1 = glm.vec3(p1.x/p1.w, p1.y/p1.w, p1.z/p1.w)
        ro = p0
        rd = glm.normalize(p1 - p0)
        return ro, rd

    @staticmethod
    def _intersect_aabb(ro, rd, bmin, bmax):
        """Return nearest hit point with AABB, or None."""
        invD = glm.vec3(1.0/rd.x if rd.x != 0 else 1e32,
                        1.0/rd.y if rd.y != 0 else 1e32,
                        1.0/rd.z if rd.z != 0 else 1e32)
        t0s = (bmin - ro) * invD
        t1s = (bmax - ro) * invD
        tmin = glm.vec3(min(t0s.x, t1s.x), min(t0s.y, t1s.y), min(t0s.z, t1s.z))
        tmax = glm.vec3(max(t0s.x, t1s.x), max(t0s.y, t1s.y), max(t0s.z, t1s.z))
        t_enter = max(max(tmin.x, tmin.y), tmin.z)
        t_exit  = min(min(tmax.x, tmax.y), tmax.z)
        if t_exit > max(t_enter, 0.0):
            return ro + rd * max(t_enter, 0.0)
        return None

    def _recenter_pivot_under_cursor(self):
        if not self._pick_has_box:
            return
        x, y = glfw.get_cursor_pos(self.window)
        ro, rd = self._ray_from_screen(x, y)
        hit = self._intersect_aabb(ro, rd, self._aabb_min, self._aabb_max)
        if hit is not None:
            # keep camera where it is; change pivot to hit and shrink radius accordingly
            self.look_at = hit
            self.radius = max(self.MIN_RADIUS, float(glm.length(self.position - self.look_at)))
            # recompute bases so next rotate is about new pivot
            self._update_basis()

class FrameTimer:

    def __init__(self, every=1.0):

        self.every = every
        self.delta_time = 0.
        self.last_frame = 0.
        self.frame_timer = 0.
        self.frame_ctr = 0

    def tick(self, verbose=False):
        
        current_frame = glfw.get_time()
        self.delta_time = current_frame - self.last_frame
        self.last_frame = current_frame
        self.frame_timer += self.delta_time
        self.frame_ctr += 1

        if self.frame_timer > self.every:
            avg_delta_time = self.frame_timer / self.frame_ctr
            if verbose:
                print(f"FPS: {1/avg_delta_time}")
            
            self.frame_ctr = 0
            self.frame_timer = 0.
        
        return self.frame_ctr

class GLFrameViewController(GUIController):

    def __init__(self, view, parent_controller=None, mode="frame"):
        """
            GUIController a-la CameraViewController:
            Has a GLFrameViewer that runs the render loop on it's
            own thread to maintain the GL Context separate from
            Tk.mainloop().
        """

        super().__init__(view, parent_controller)

        # OpenGL viewer
        self.viewer = GLFrameViewer(mode)

        # microscope state
        self.microscope_state = self.parent_controller.configuration["experiment"]["MicroscopeState"]

        # start rendering thread
        self.viewer.start_render_loop(window_dim=(512,512))

        # image widgets
        self.image_palette = view.lut.get_widgets()

        # str: display state
        self.display_state = None

        # Binding for adjusting lookup table min/max counts
        self.image_palette["Min"].get_variable().trace_add(
            "write", self._on_minmax_changed
        )
        self.image_palette["Max"].get_variable().trace_add(
            "write", self._on_minmax_changed
        )

        # autoscale variable
        self.autoscale = self.image_palette["Autoscale"]
        # TODO: Gets tripped up bc widget is already config'd in camera_view.py
        # Shouldn't be a problem if we scrap camera_view
        self.autoscale.widget.config(
            command=self._on_minmax_changed
        )

    def try_to_display_image(self, image: SharedNDArray) -> None:

        # stacking setup
        n_steps   = self.microscope_state["number_z_steps"]
        step_size = self.microscope_state["step_size"]
        self.viewer.set_dz(step_size)
        
        if self.microscope_state["image_mode"] == "z-stack":
            self.viewer.set_slices(n_steps)
        else:
            self.viewer.set_slices(2)

        # TODO: CPU min/max is inefficient
        # Try to do this with Compute Shaders on GPU
        if self.autoscale.get():
            cMin, cMax, _, _ = cv2.minMaxLoc(image)
            self.viewer.set_min_max([cMin, cMax])

        self.display_state = self.view.live_frame.live.get()
        if self.display_state == "OpenGL":
            self.viewer.try_to_display_image(image)

    # private util functions
    
    def reset(self):
        self.viewer.rendered_images = 0
        # self.viewer.vol_shape = None
        # self.viewer.vol_min_max = None

    def set_mode(self, mode: str):
        self.viewer.mode = mode

    def _on_minmax_changed(self, *args):

        if self.autoscale.get():
            return

        min_counts = self.image_palette["Min"].get()
        max_counts = self.image_palette["Max"].get()

        try:
            assert isinstance(min_counts, int)
            assert isinstance(max_counts, int)
        except AssertionError:
            return

        self.viewer.set_min_max([min_counts, max_counts])

class GLFrameViewer:

    def __init__(self, mode="volume"):

        # concurrency
        self.cmd_q      = queue.Queue()
        self.data_q     = queue.Queue(maxsize=RING_BUF_SIZE)
        self.is_running = threading.Event()
        self.is_ready   = threading.Event()
        self.thread     = None

        # GL objects (created in render thread)
        self.window  = None
        self.shaders = None
        self.vao     = None
        self.pbo     = None
        self.camera  = None
        self.timer   = FrameTimer(every=1.0)

        # stack attribs
        self.vol_shape = None
        self._z        = 0
        self._N        = 1
        self._dz       = 1.0

        # textures
        self.tex_3d = None
        self.tex_2d = None
        self.tex_tf = None

        # window attribs
        self.title = None

        # config
        self.mode         = mode
        self.tex_2d_shape = None
        self.vol_min_max  = None
        self.do_autoscale = False
        self.crosshair    = True
        self.cam_pos      = None

        # image properties
        self.gamma       = None
        self.step_world  = None
        self.shear_angle = None
        self.opacity     = None
        self.resolution  = None
        self.min_max     = [0, 65535]
        self.luts        = None
        self.n_channels  = None
        self.curr_chan   = 0

        # monitoring
        self.rendered_images = 0
        self._t0             = 0

    def set_slices(self, N: int):
        self._N = N

    def set_dz(self, dz: float):
        self._dz = dz

        def _do():
            shader = self.shaders["volume"]
            shader.use()
            shader.set_float("dz", self._dz)
        
        self.cmd_q.put_nowait(_do)

    def start_render_loop(self, window_dim=(1000,800), title="Camera View", cam_pos=[100, 100, 100]):
        # initial camera pos
        self.cam_pos = cam_pos

        if self.thread and self.thread.is_alive():
            return
        
        # create and start render thread
        self.is_running.set()
        self.thread = threading.Thread(
            target=self.render_thread,
            args=(window_dim, title),
            daemon=True
        )
        self.thread.start()

        # Wait until GL is ready
        self.is_ready.wait(timeout=1.0)

    def stop_render_loop(self):
        if not self.thread:
            return
        
        self.is_running.clear()

        # Wake the queues if waiting
        self.cmd_q.put(lambda: None)
        self.data_q.put(lambda: None)

        # Kill the thread
        self.thread.join(timeout=3.0)
        self.thread = None

    def render_thread(self, window_dim, title):
        """
            Lives entirely in the child process. Needs to own both the GLFW window
            and the GL Context. GL imports need to be handled within.
        """
        global GL

        try:
            """ ------------------------- CREATE GL CONTEXT ------------------------ """
            # init GLFW
            if not glfw.init():
                raise RuntimeError("ERROR: GLFW init failed!")         

            #version 430 core
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

            # always on top
            glfw.window_hint(glfw.FLOATING, glfw.TRUE)

            # create window
            init_width, init_height = window_dim
            self.title = title
            self.window = glfw.create_window(init_width, init_height, self.title + f" [{self.mode.upper()}]", None, None)

            # GL context
            glfw.make_context_current(self.window)
            
            # key callback
            glfw.set_key_callback(self.window, self.glfw_key_callback)

            """ ------------------------- OPEN GL IMPORTS/CALLS -------------------- """
            # Can import GL now that in-thread context exists
            from OpenGL import GL as _GL
            GL = _GL

            # two shaders: frame = 2D and volume = 3D
            self.shaders = {
                "frame":  Shader(VERT_SRC, FRAG_2D_SRC),
                "volume": Shader(VERT_SRC, FRAG_3D_SRC)
            }
            
            # VAO
            self.vao = GL.glGenVertexArrays(1) # quad

            # camera
            self.camera = Camera(self.window, self, position=self.cam_pos)

            # 2D shader uniform inits
            self.shaders['frame'].use()
            self.shaders['frame'].set_int('pixels', 0)    # GL_TEXTURE0

            # 3D shader uniform inits
            self.shaders['volume'].use()
            self.shaders['volume'].set_int('volume', 1)   # GL_TEXTURE1
            self.shaders['volume'].set_int('transfer', 2) # GL_TEXTURE2
            self.shaders['volume'].set_float('stepWorld', 0.25)
            self.shaders['volume'].set_float('opacity', 0.15)

            # ready to render
            self.is_ready.set()

            # --------- MAIN LOOP ---------
            while self.is_running.is_set() and not glfw.window_should_close(self.window):
                """
                    Still don't know best way to queue images to work with the ring buffer.
                    - Pull once from data_q and immediately update_texture
                    - Pull once from data_q and send update_image to cmd_q
                    - Pull RING_BUF_SIZE times from data_q and send update_image

                    Weird part is we max out at 40 FPS @ 5 msec no matter what we do.
                    Need to think about this more...
                """
                # VSync off for 2D mode
                # glfw.swap_interval(0 if self.mode == "frame" else 1)
                glfw.swap_interval(1)

                # command queue drains
                for _ in range(RING_BUF_SIZE):
                    try:
                        cmd = self.cmd_q.get_nowait()
                    except queue.Empty:
                        break
                    try:
                        cmd()
                    except Exception as e:
                        print(f"[GL Thread] Error Executing cmd={cmd}:", e)
                        traceback.print_exc()
                
                # data queue drain                   
                try:
                    image = self.data_q.get_nowait()
                    
                    # image received: start the timer
                    # self._t0 = time.perf_counter_ns()
                    # measure here...?

                    if self.mode == "frame":
                        self.update_image(image)
                    elif self.mode == "volume":
                        self.add_slice(image)
                    else:
                        raise Exception(f"Invalid draw mode: {self.mode}")
                except queue.Empty:
                    pass

                # draw frame
                self.draw_frame()
            
                # render
                glfw.swap_buffers(self.window)

                # user input
                glfw.poll_events()

            # cleanup
            try:
                if self.tex_tf: 
                    GL.glDeleteTextures([self.tex_tf])
                    self.tex_tf = None
                if self.tex_2d: 
                    GL.glDeleteTextures([self.tex_2d])
                    self.tex_2d = None
                if self.tex_3d: 
                    GL.glDeleteTextures([self.tex_3d])
                    self.tex_3d = None
                if self.vao:    
                    GL.glDeleteVertexArrays(1, [self.vao])
                    self.vao = None
            finally:
                glfw.destroy_window(self.window)
                glfw.terminate()
                self.window = None
        
        except Exception as e:
            print("[GL Thread] Fatal Error:", e)
            traceback.print_exc()
            
            # try to terminate GLFW
            try:
                glfw.terminate()
            except Exception:
                pass
            self.window = None
            self.is_ready.set()

    def glfw_key_callback(self, window, key, scancode, action, mods):
        if action == glfw.PRESS:
            if key == glfw.KEY_TAB:

                # pretty bad, but works for now...
                if self.mode == "frame":
                    self.mode = "volume"
                elif self.mode == "volume":
                    self.mode = "frame"
                
                # update window title
                glfw.set_window_title(self.window, self.title + f" [{self.mode.upper()}]")

                # apply lut
                self.set_min_max(self.min_max)
            
            elif key == glfw.KEY_X:
                self.camera.set_ortho_view( 0.0, 90.0, 350.0)
            elif key == glfw.KEY_Y:
                self.camera.set_ortho_view( 0.0,  0.0, 350.0)
            elif key == glfw.KEY_Z:
                self.camera.set_ortho_view(90.0, 90.0, 350.0)
            elif key == glfw.KEY_C:
                self.camera.set_ortho_view(45.0, 45.0, 350.0)

    def _ensure_gl_ready(self):
        window = self.window
        vao = self.vao
        shader = self.shaders[self.mode]

        if not (window and vao and shader):
            raise RuntimeError("GL not ready yet")
        
    def try_to_display_image(self, image: np.ndarray):

        try:
            # try to put the new frame into the queue
            self.data_q.put_nowait(image)
        
        except queue.Full:
            # queue is full: replace oldest image with newest
            try:
                # drain oldest
                _ = self.data_q.get_nowait()

                # Confirm that we successfully removed the oldest frame
                self.data_q.task_done()
            except queue.Empty:
                pass
            
            try:
                # now put the new frame into the queue
                self.data_q.put_nowait(image)
            except queue.Full:
                pass        

        # image sent: start the timer
        self._t0 = time.perf_counter_ns()
        # ...or here?

    def update_image(self, image: np.ndarray):

        # create new texture if image size has changed
        if image.shape != self.tex_2d_shape:
            # clear the old texture (if it exists)
            if self.tex_2d:
                GL.glDeleteTextures([self.tex_2d])
                self.tex_2d = None
            # make new            
            self.make_frame_texture(image.shape)
            nbytes = np.prod(image.shape) * 2
            self.make_pbo_ring(nbytes)
            # update image dims
            self.tex_2d_shape = image.shape

        def _do():
            self._ensure_gl_ready()
            self.update_texture(image)
        
        # self.cmd_q.put(_do)
        self.cmd_q.put_nowait(_do)

    def add_slice(self, image: np.ndarray):

        if self.vol_shape is not None:
            # if there is a mismatch between the current vol_shape
            # and the incoming volume shape...
            if (self._N,) + image.shape != self.vol_shape:
                # clear the volume shape
                self.vol_shape = None
                # clear texture
                GL.glDeleteTextures(1, [self.tex_3d])
                self.tex_3d = None
                # try again (will reallocate volume)
                self.add_slice(image)
                
            # else bind the slice
            self.bind_slice(image, self._z)

            # N-bounded increment
            self._z = (self._z + 1) % self._N
        else:
            new_shape = (self._N,) + image.shape
            # allocate new volume
            self.bind_volume(new_shape)
            # try again with correct vol_shape
            self.add_slice(image)

    def bind_slice(self, image: np.ndarray, z: int=0):

        def _do():
            self._ensure_gl_ready()
            self.update_texture_slice_z(image, z)

        self.cmd_q.put(_do)

    # def bind_volume(self, vol_f32: np.ndarray):
    def bind_volume(self, shape: tuple):
        """Upload / replace the 3D volume texture (runs on GL thread)."""
        
        # first thing: make this the vol_shape and set z = 0
        self._z = 0
        self.vol_shape = shape

        # object-space bounds: centered on origin
        nz, ny, nx = 0.5*np.float32(shape) - 0.5
        boxMin = (-nx, -ny, -nz)
        boxMax = ( nx,  ny,  nz)

        def _do():
            self._ensure_gl_ready()
            
            # (re)create textures
            if self.tex_3d is None:
                self.make_volume_texture(shape)
            if self.tex_tf is None:
                self.make_transfer_texture()

            # set uniforms
            self.shaders['volume'].use()
            self.shaders['volume'].set_int('volume',   1)
            self.shaders['volume'].set_int('transfer', 2)
            # self.shaders['volume'].set_float('stepWorld', 0.25)
            self.shaders['volume'].set_vec3('boxMin', boxMin)
            self.shaders['volume'].set_vec3('boxMax', boxMax)

        self.cmd_q.put(_do)

    def make_volume_texture(self, shape: tuple):

        z, y, x = shape

        self.tex_3d = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_3D, self.tex_3d)

        # params
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_R, GL.GL_CLAMP_TO_EDGE)
        
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glTexImage3D(
            GL.GL_TEXTURE_3D, 
            0,
            GL.GL_RGBA16,
            x, 
            y, 
            z, 
            0,
            GL.GL_RGBA, 
            GL.GL_UNSIGNED_SHORT,
            None # input: [[[R0, G0, B0, A0], [R1, G1, B1, A1], ... ] ... ]
            )        

    def make_frame_texture(self, shape: tuple):

        self.tex_2d = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex_2d)

        # params
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)

        # shape
        ny, nx = shape

        # pre-allocate the full image, only update pixels later
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,       # target
            0,                      # mipmap level
            GL.GL_R16,              # internal format (1-channel 16-bit normalized)
            nx,
            ny,
            0,                      # border
            GL.GL_RED,              # format
            GL.GL_UNSIGNED_SHORT,   # type (uint16)
            None
        )

    def make_transfer_texture(self, n_lanes: int=4):

        # guard against LUT = None
        if not self.luts:
            self.luts = [
                [1.0, 1.0, 1.0, 1.0],  # ch0
                [1.0, 0.0, 0.0, 1.0],  # ch1
                [0.0, 1.0, 0.0, 1.0],  # ch2
                [0.0, 0.0, 1.0, 1.0],  # ch3                
            ]

        print("Transfer LUTs:", self.luts)

        # RGBA 2D transfer textures with 4 lanes
        rgba = np.array(n_lanes*[np.linspace(0, 255, 256)])[..., np.newaxis] \
             * np.array(self.luts)[:, np.newaxis, :]
        rgba = rgba.astype(np.uint8)

        self.tex_tf = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex_tf)

        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D, 
            0,
            GL.GL_RGBA8,
            256, 
            4, 
            0,
            GL.GL_RGBA, 
            GL.GL_UNSIGNED_BYTE,
            rgba # shape: (4 lanes x 256 levels x 4 rgba)
        )               

    def make_pbo_ring(self, nbytes: int, N: int = RING_BUF_SIZE):
        """
            Create N pixel unpack buffers for async texture upload.
        """
        self.pbo = GL.glGenBuffers(N)

        # bind
        for b in self.pbo:
            GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, b)
            GL.glBufferData(GL.GL_PIXEL_UNPACK_BUFFER, nbytes, None, GL.GL_STREAM_DRAW)
        
        # unbind
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)
        self._pbo_index = 0

    def update_texture(self, data : np.ndarray):
        """
            Update 2D texture pixels with new data.
        """        
        ny, nx = data.shape
        nbytes = nx * ny * 2 # uint16

        # pick next PBO
        b = self.pbo[self._pbo_index]
        self._pbo_index = (self._pbo_index + 1) % len(self.pbo)

        # bind and orphan the buffer
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, b)
        GL.glBufferData(GL.GL_PIXEL_UNPACK_BUFFER, nbytes, None, GL.GL_STREAM_DRAW)

        # map and copy CPU -> PBO
        ptr = GL.glMapBuffer(GL.GL_PIXEL_UNPACK_BUFFER, GL.GL_WRITE_ONLY)
        import ctypes
        ctypes.memmove(int(ptr), data.ctypes.data, nbytes)
        GL.glUnmapBuffer(GL.GL_PIXEL_UNPACK_BUFFER)


        # bind texture and issue copy GPU <- PBO
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex_2d)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glTexSubImage2D(
            GL.GL_TEXTURE_2D,       # target
            0,                      # mipmap level
            0,                      # xoffset
            0,                      # yoffset
            nx,                     # width
            ny,                     # height
            GL.GL_RED,              # format
            GL.GL_UNSIGNED_SHORT,   # type: uint16
            None
        )

        # cleanup
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)

        self.rendered_images = (self.rendered_images + 1) % 100

        # render complete: update performance logger
        duration_ns = time.perf_counter_ns() - self._t0
        # print(f"Rendered: {(duration_ns/1000):.2f} us")
        if logger:
            logger.performance(
                json.dumps(
                    {
                        "kind": "GL: Update Texture",
                        "duration_ns": duration_ns,
                        "timestamp": time.time(),
                        "image_id": self.rendered_images
                    }
                )
            )

    def update_texture_slice_z(self, slice: np.ndarray, z: int):

        # TODO: Need to follow logic of update_volume_texture, but for single slices.
        #       Likely need to store self.slice as RGBA, pass in the current channel
        #       number and then write to specific chan. GL format needs to be GL_RGBA.

        y, x = slice.shape

        GL.glBindTexture(GL.GL_TEXTURE_3D, self.tex_3d)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

        self.set_n_channels(4)

        channel_slice = np.zeros((y, x, 4))

        channel_slice[..., self.curr_chan] = slice

        # update only the data for slice (z)
        GL.glTexSubImage3D(GL.GL_TEXTURE_3D, 
                           0,                    # level
                           0,                    # xoffset (none)
                           0,                    # yoffset (none)
                           int(z),               # zoffset (z-slice position)
                           x,                    # width
                           y,                    # height
                           1,                    # depth (one slice)
                           GL.GL_RGBA,            # format
                           GL.GL_UNSIGNED_SHORT, # uint16
                           channel_slice.astype(np.uint16)                 # image data
        )

    def update_volume_texture(self, 
                              channels: list[np.ndarray], 
                              luts: list[list]=[
                                  [1.0, 1.0, 1.0, 1.0], # ch0
                                  [1.0, 0.0, 0.0, 1.0], # ch1
                                  [0.0, 1.0, 0.0, 1.0], # ch2
                                  [0.0, 0.0, 1.0, 1.0], # ch3
                              ]
                              ):
        # update luts
        self.luts = luts

        try:
            # RGBA lanes only support 4 channels
            assert len(channels) <= 4
        except AssertionError:
            print("[GL] Can only accept 4 channels! Keeping last 4 in list...")
            channels = channels[-4:]

        # set nChannels in shader
        self.set_n_channels(len(channels))

        for c in range(1, len(channels)):
            try:
                # channels must all have the same shape
                assert channels[c].shape == channels[0].shape
            except AssertionError:
                print(f"[GL] Channel_{c} shape: {channels[c].shape} != {channels[0].shape}." \
                    "Replacing with zeros...")
                # throw away channels of unequal shape
                channels[c] = np.zeros(channels[0].shape)

        vol_shape = channels[0].shape
        try:
            assert vol_shape == self.vol_shape
        except AssertionError:
            print("[GL] Volume shape mismatch with allocated texture... Reallocating.")
            self.bind_volume(vol_shape)
            # try again
            self.update_volume_texture(channels, luts)

        # package channels as RGBA volume
        volume = np.zeros(vol_shape + (4,))
        for i in range(len(channels)):
            volume[..., i] = channels[i]

        def _do():
            z, y, x = vol_shape

            GL.glBindTexture(GL.GL_TEXTURE_3D, self.tex_3d)
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
            
            # updates the whole volume texture in one shot
            GL.glTexSubImage3D(
                GL.GL_TEXTURE_3D, 
                0, 0, 0, 0, 
                x, y, z,
                GL.GL_RGBA, GL.GL_UNSIGNED_SHORT,
                volume.astype(np.uint16)
                )

        self.cmd_q.put_nowait(_do)

    def config_gl_viewport(self):

        # if volume, just make viewport the full window
        vp_w, vp_h = glfw.get_framebuffer_size(self.window)
        x0, y0 = (0, 0)

        # if frame, center and scale
        if self.mode == "frame":
            tx_h, tx_w = self.tex_2d_shape
            
            # proportionally scale texture to window
            if tx_w > tx_h:
                tx_h *= vp_w/tx_w
                tx_w = vp_w
            else:
                tx_w *= vp_h/tx_h
                tx_h = vp_h

            # center shift
            x0 = (vp_w - tx_w) / 2
            y0 = (vp_h - tx_h) / 2

            # apply to viewport
            vp_w = tx_w
            vp_h = tx_h

        viewport = (int(x0), int(y0), int(vp_w), int(vp_h))

        return viewport

    def draw_frame(self):
        """
            Simply renders the texture once per frame.
        """
        # timer tick
        self.timer.tick(verbose=False)

        if self.mode == "frame":
            if not self.tex_2d:
                return
        elif self.mode == "volume":
            if not (self.tex_3d and self.tex_tf):
                return
        else:
            raise Exception(f"Invalid draw mode: {self.mode}")

        # adjust viewport based on window size
        vx, vy, vw, vh = self.config_gl_viewport()
        GL.glViewport(vx, vy, vw, vh)
        
        shader = self.shaders[self.mode]
        shader.use()
        shader.set_vec2('viewportSize', (vw, vh))    
        shader.set_int('crosshair', int(self.crosshair))

        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # update camera
        self.camera.update(self.timer.delta_time)

        if self.mode == "volume":
            # camera view-projection
            inv_vp = glm.inverse(self.camera.projection * self.camera.view)
            GL.glUniformMatrix4fv(shader.loc("invProjView"), 1, GL.GL_TRUE,
                                  np.array(inv_vp, np.float32))
            
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glBindTexture(GL.GL_TEXTURE_3D, self.tex_3d)
            GL.glActiveTexture(GL.GL_TEXTURE2)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex_tf)            

            GL.glDisable(GL.GL_DEPTH_TEST)
            GL.glDisable(GL.GL_CULL_FACE)
            GL.glDisable(GL.GL_BLEND)

        elif self.mode == "frame":
            self.camera.clamp_panning_to_viewport((vw, vh))

            # camera pan/zoom
            shader.set_vec2( 'panPIX', self.camera.pan_xy)
            shader.set_float('zoom',   self.camera.zoom_xy)

            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex_2d)
        
        # render vao no matter what
        GL.glBindVertexArray(self.vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
        GL.glBindVertexArray(0)

    # ----- update functions -----

    def set_n_channels(self, n_channels: int=4):
        self.n_channels = n_channels

        def _do():
            self._ensure_gl_ready()

            shader = self.shaders["volume"]
            shader.use()
            shader.set_int('nChannels', n_channels)
        
        self.cmd_q.put_nowait(_do)        

    def set_gamma(self, gamma: float=1.0):
        self.gamma = gamma

        def _do():
            self._ensure_gl_ready()

            shader = self.shaders[self.mode]
            shader.use()
            shader.set_float('gamma', gamma)
        
        self.cmd_q.put_nowait(_do)

    def set_step_world(self, step_world: float=0.25):
        self.step_world = step_world

        def _do():
            self._ensure_gl_ready()

            shader = self.shaders[self.mode]
            shader.use()
            shader.set_float('stepWorld', step_world)
        
        self.cmd_q.put_nowait(_do)

    def set_opacity(self, opacity: float=0.25):
        self.opacity = opacity

        def _do():
            self._ensure_gl_ready()

            shader = self.shaders[self.mode]
            shader.use()
            shader.set_float('opacity', opacity)
        
        self.cmd_q.put_nowait(_do)

    def set_shear_angle(self, theta: float=0.0):
        self.shear_angle = theta

        def _do():
            self._ensure_gl_ready()

            shader = self.shaders[self.mode]
            shader.use()
            shader.set_float('shear_angle', theta)
        
        self.cmd_q.put_nowait(_do)

    def set_resolution(self, px: float=1.0, dz: float=1.0):
        self.resolution = {
            'px': px,
            'dz': dz
        }

        def _do():
            self._ensure_gl_ready()

            shader = self.shaders[self.mode]
            shader.use()
            shader.set_float('px', px)
            shader.set_float('dz', dz)
        
        self.cmd_q.put_nowait(_do)


    def set_min_max(self, min_max: list, ch: int=-1):
        if ch < 0:
            ch = self.curr_chan
        
        self.min_max = min_max
        
        def _do():
            self._ensure_gl_ready()
            
            shader = self.shaders[self.mode]
            shader.use()
            if self.mode == "frame":
                shader.set_vec2('cMinMax', min_max)
            elif self.mode == "volume" and min_max:
                print("set_min_max:", ch, min_max)
                shader.set_vec2(
                    f"cMinMax[{ch}]", 
                    np.array(min_max, dtype=np.float32)/65535.
                    )

                # c_min, c_max = min_max
                
                # if self.vol_min_max is None:
                #     self.vol_min_max = min_max
                # else:
                #     v_min, v_max = self.vol_min_max
                #     self.vol_min_max = [
                #         min([v_min, c_min]),
                #         max([v_max, c_max])
                #     ]

                # shader.set_float('cMin', float(c_min)/65535.)
                # shader.set_float('cMax', float(c_max)/65535.)

        self.cmd_q.put(_do)

    def set_ortho_view(self, position):
        self.ortho_position = position

        def _do():
            self._ensure_gl_ready()

            self.camera.set_ortho_view(self.ortho_position)

        self.cmd_q.put_nowait(_do)

    def autoscale(self, image: np.ndarray):

        # only tax the CPU every timer tick
        if self.timer.frame_ctr > 0:
            return

        min_pix = image.min()
        max_pix = image.max()
        self.set_min_max([min_pix, max_pix])

#%%
if __name__ == '__main__':

    """
        We will use __main__ for testing, profiling and debugging.
        Run inside a Tk.mainloop() and have some widgets to test.
        Might be nice to let a user just run this file in a navigate env
        and view saved data as standalone?
    """

    TEST_MODE = "volume"

    import os
    import tkinter as tk
    from tkinter import ttk
    import tifffile

    from navigate.model.concurrency.concurrency_tools import SharedNDArray
    from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput

    root = tk.Tk()
    root.geometry("400x600")

    settings = tk.Frame(root).pack()

    viewer = GLFrameViewer(mode=TEST_MODE)

    # test data library
    data = {
        "beads_opm":    r"d:\VAST\Stephan_kdrl_rasmCherry_GFP_cancer_hindbrain_4dfp_24hpi\OPM\Coverslip\Beads\P0\2025-09-27\P001\CH00_000000.tiff",
        "vasc":         r"C:\Users\conor\Documents\Python\tkopengl\aliasing_decon\A12_P0_mCherry.tiff",
        "data_reto":    r"C:\Users\conor\Documents\Python\tkopengl\aliasing_decon\data_reto.tif",
        "beads_cs":     r"C:\Users\conor\Documents\Python\tkopengl\aliasing_decon\beads_coverslip.tiff",
        "LM-red":       r"C:\Users\conor\Documents\Lm_Images\C1-NT 002-Airyscan Processing.tif",
        "LM-blue":      r"C:\Users\conor\Documents\Lm_Images\C2-NT 002-Airyscan Processing.tif",
        "vast-cell":    r"Z:\bioinformatics\Danuser_lab\Fiolka\LabMembers\Conor\VAST\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H6\2025-10-25\P3001\CH00_000000.tiff",
        "vast-vasc":    r"Z:\bioinformatics\Danuser_lab\Fiolka\LabMembers\Conor\VAST\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H6\2025-10-25\P3001\CH01_000000.tiff",
    }

    # use_data = ["LM-red", "LM-blue"]
    use_data = ["vasc"]

    vol_channels = []

    resolution = {
        'px': 0.1248,
        'dz': 0.4
    }

    def add_channel(vol_path: str, ds: int=1):
        with tifffile.TiffFile(vol_path) as tif:
            meta = tif.imagej_metadata
            
            vol_channels.append(
                tif.asarray()[::ds, ::ds, ::ds]
                )

            try:
                resolution['dz'] = meta['spacing']
                pixels, microns = tif.pages[0].tags.get('XResolution').value
                resolution['px'] = microns / pixels
            except:
                pass
            finally:
                resolution['px'] *= ds
                resolution['dz'] *= ds

    # for chan in use_data:
    #     add_channel(data[chan])

    vast_expt_data = {
        # day 1
        "d1-h7-p1":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish\Tc32\H7\2025-10-24\P1001",
        "d1-h7-p2":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish\Tc32\H7\2025-10-24\P2001",
        "d1-h7-p3":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish\Tc32\H7\2025-10-24\P3001",
        "d1-h7-p4":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish\Tc32\H7\2025-10-24\P4001",
        "d1-h10-p1": r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish\Tc32\H10\2025-10-24\P1001",
        "d1-h10-p2": r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish\Tc32\H10\2025-10-24\P2002",
        "d1-h10-p3": r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish\Tc32\H10\2025-10-24\P3001",
        "d1-h11-p1": r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish\Tc32\H11\2025-10-25\P1001",
        "d1-h11-p3": r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish\Tc32\H11\2025-10-25\P3003",
        # day 2
        "d2-h3-p1":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H3\2025-10-25\P1001",
        "d2-h3-p2":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H3\2025-10-25\P2001",
        "d2-h3-p3":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H3\2025-10-25\P3001",
        "d2-h5-p1":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H5\2025-10-25\P1001",  # extravasation?
        "d2-h5-p2":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H5\2025-10-25\P2002",  # extravasation?
        "d2-h5-p3":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H5\2025-10-25\P3001",
        "d2-h6-p1":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H6\2025-10-25\P1001",
        "d2-h6-p2":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H6\2025-10-25\P2001",
        "d2-h6-p3":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H6\2025-10-25\P3001",
        "d2-h7-p1":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H7\2025-10-25\P1001",  # badly aberrated...
        "d2-h7-p2":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H7\2025-10-25\P2001",
        "d2-h7-p3":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H7\2025-10-25\P3001",  # extravasation?
        "d2-h10-p3": r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H10\2025-10-25\P3001",
        "d2-h10-p4": r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-2\Tc32\H10\2025-10-25\P4001",
        # day 3
        "d3-h6-p1":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-3\Tc32\H6\2025-10-26\P1001",
        "d3-h6-p2":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-3\Tc32\H6\2025-10-26\P2001",  # same site as d2-h6-p1?
        "d3-h6-p3":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-3\Tc32\H6\2025-10-26\P3001",
        "d3-h6-p4":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-3\Tc32\H6\2025-10-26\P4001",  # extravasation?
        "d3-h7-p1":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-3\Tc32\H7\2025-10-26\P1001",  # badly aberrated...
        "d3-h7-p2":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-3\Tc32\H7\2025-10-26\P2002",
        "d3-h7-p3":  r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-3\Tc32\H7\2025-10-26\P3001",  # extravasation?
        "d3-h10-p2": r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-3\Tc32\H10\2025-10-26\P2001", # extravasation?
        "d3-h10-p3": r"Z:\bioinformatics\Danuser_lab\zebrafish\VAST\Dagan\Dagan_ExtraVas_Tc32_0dpi\OPM\Fish-3\Tc32\H10\2025-10-26\P3002", # volume looks empty...
    }
    # vast_condition = "d3-h7-p3"
    vast_condition = "d2-h5-p2"

    add_channel(os.path.join(vast_expt_data[vast_condition], "CH00_000000.tiff"), ds=2)
    add_channel(os.path.join(vast_expt_data[vast_condition], "CH01_000000.tiff"), ds=2)

    viewer.start_render_loop(window_dim=(600,600), cam_pos=[-200, 200, 200])

    # pass the channels in as a list[np.ndarray]
    viewer.update_volume_texture(
        vol_channels,
        luts=[
            [0, 1, 1, 1], # ch0
            [1, 0, 1, 1], # ch1
            [0, 0, 0, 1], # ch2
            [0, 0, 0, 1], # ch3
        ])

    # for ch, vol in enumerate(vol_channels):
    #     viewer.set_min_max([vol.max()/15, vol.max()/1.15], ch=ch)

    # viewer.set_min_max([5000, 50000], ch=0)
    # viewer.set_min_max([500 , 10000], ch=1)

    lut_default = {
        'min_0': 5000, 'max_0': 45000,
        'min_1': 250,  'max_1':  5000,
    }

    min_0 = tk.StringVar(root, value=str(lut_default['min_0']))
    max_0 = tk.StringVar(root, value=str(lut_default['max_0']))
    lut_frame_0 = tk.Frame(settings).pack()
    LabelInput(
        lut_frame_0,
        input_class=ttk.Spinbox,
        input_var=min_0,
        label_pos="left",
        label="min_0",
        input_args={
            "from_": 0,
            "to": 65535,
            "increment": 50,
        }
    ).pack()
    LabelInput(
        lut_frame_0,
        input_class=ttk.Spinbox,
        input_var=max_0,
        label_pos="left",
        label="max_0",
        input_args={
            "from_": 0,
            "to": 65535,
            "increment": 50,
        }
    ).pack()
    min_0.trace_add("write", lambda *args: viewer.set_min_max([int(min_0.get()), int(max_0.get())], ch=0))
    max_0.trace_add("write", lambda *args: viewer.set_min_max([int(min_0.get()), int(max_0.get())], ch=0))

    min_1 = tk.StringVar(root, value=str(lut_default['min_1']))
    max_1 = tk.StringVar(root, value=str(lut_default['max_1']))
    lut_frame_1 = tk.Frame(settings).pack()
    LabelInput(
        lut_frame_1,
        input_class=ttk.Spinbox,
        input_var=min_1,
        label_pos="left",
        label="min_1",
        input_args={
            "from_": 0,
            "to": 65535,
            "increment": 50,
        }
    ).pack()
    LabelInput(
        lut_frame_1,
        input_class=ttk.Spinbox,
        input_var=max_1,
        label_pos="left",
        label="max_1",
        input_args={
            "from_": 0,
            "to": 65535,
            "increment": 50,
        }
    ).pack()
    min_1.trace_add("write", lambda *args: viewer.set_min_max([int(min_1.get()), int(max_1.get())], ch=1))
    max_1.trace_add("write", lambda *args: viewer.set_min_max([int(min_1.get()), int(max_1.get())], ch=1))

    viewer.set_min_max([lut_default['min_0'], lut_default['max_0']], ch=0)
    viewer.set_min_max([lut_default['min_1'], lut_default['max_1']], ch=1)

    # Tk widgets
    variables = {}
    def add_widget(root, kw: str, defaults: tuple):
        # for each arg: create the StringVar and LabelInput
        value, low, delta, high = defaults
        variables[kw] = tk.StringVar(root, value=str(value))
        LabelInput(
            root,
            input_class=ttk.Spinbox,
            input_var=variables[kw],
            label_pos="left",
            label=kw,
            input_args={
                "from_": low,
                "to": high,
                "increment": delta,
            }
        ).pack()

    add_widget(settings, "theta", (60.0, 0.0, 1.0, 90.0))
    variables["theta"].trace_add("write", lambda *args: viewer.set_shear_angle(float(variables["theta"].get())))
    
    add_widget(settings, "opacity", (0.25, 0.0, 0.01, 1.0))
    variables["opacity"].trace_add("write", lambda *args: viewer.set_opacity(float(variables["opacity"].get())))

    add_widget(settings, "gamma", (0.50, 0.00, 0.05, 2.0))
    variables["gamma"].trace_add("write", lambda *args: viewer.set_gamma(float(variables["gamma"].get())))
    
    add_widget(settings, "step_world", (0.25, 0.02, 0.02, 1.0))
    variables["step_world"].trace_add("write", lambda *args: viewer.set_step_world(float(variables["step_world"].get())))
    
    # for ch in range(len(vol_channels)):
    #     min_k, max_k = (f"min_{ch}", f"max_{ch}")
    #     add_widget(settings, min_k,   (5000,  0, 50,  65535))
    #     add_widget(settings, max_k,   (50000, 0, 250, 65535))
    #     def get_min_max():
    #         return [float(variables[min_k].get()), float(variables[max_k].get())]
    #     [variables[k].trace_add("write", lambda *args: viewer.set_min_max(get_min_max(), ch=ch)) for k in [min_k, max_k]]
    #     viewer.set_min_max(min_max=get_min_max(), ch=ch)

    viewer.set_resolution(px=resolution['px'], dz=resolution['dz'])
    viewer.set_shear_angle(theta=float(variables["theta"].get()))
    viewer.set_opacity(opacity=float(variables["opacity"].get()))
    viewer.set_gamma(gamma=float(variables["gamma"].get()))
    viewer.set_step_world(step_world=float(variables["step_world"].get()))

    # viewer.set_ortho_view([0, 0, 100])

    root.mainloop()