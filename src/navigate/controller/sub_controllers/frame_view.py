import math
import numpy as np
import glfw
import glm
from typing import Union
import threading
import queue
import time
import traceback

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.model.concurrency.concurrency_tools import SharedNDArray
from navigate.tools.decorators import performance_monitor

GL = None

RING_BUF_SIZE = 6

# SHADERS

VERT_SRC = """
// RAYMARCH_VERT_SRC
#version 330 core

void main()
{
    // 3 vertices: (0,0), (2,0), (0,2) in [0,2] → NDC [-1,1]
    vec2 p = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2);

    gl_Position = vec4(p*2.0 - 1.0, 0.0, 1.0);
}
"""

FRAG_2D_SRC = """
#version 330 core

out vec4 FragColor;

uniform sampler2D pixels;
uniform vec2 viewportSize;
uniform vec2 cMinMax = vec2(0, 65535);

void main()
{
    vec2 uv = gl_FragCoord.xy / viewportSize;
    // uv.y = 1.0 - uv.y;

    float s = texture(pixels, uv).r;

    // lut
    float cMin = float(cMinMax.x/65535);
    float cMax = float(cMinMax.y/65535);
    //clamp
    s = clamp(s, cMin, cMax);
    // normalize
    s = (s - cMin) / (cMax - cMin);
    
    FragColor = vec4(s, s, s, 1.0);
}

"""

FRAG_3D_SRC = """
// RAYMARCH_FRAG_SRC  —  raymarch with shear (Y by Z) + step-size invariant opacity
#version 330 core

out vec4 FragColor;

uniform sampler3D volume;
uniform sampler1D transfer;

uniform mat4 invProjView;
uniform vec2 viewportSize;

uniform vec3 boxMin;
uniform vec3 boxMax;

uniform float stepWorld;       // step length in WORLD units

// contrast params
uniform float opacity = 0.15;  // global density/opacity
uniform float cMin = 0.0;
uniform float cMax = 1.0;
uniform float gamma = 1.0;

// OPM parameters
uniform float shear_angle = 45.0;   // degrees
uniform float dz = 0.4;             // um    
uniform float px = 0.1348;          // um

uniform float zSlice;

// 2D-3D toggle
uniform bool is3DMode = true;

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
    // out color
    vec4 outColor;

    if (is3DMode) 
    {
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
        if (!intersectAABB(ro, rd, boxMin, boxMax, tEnter, tExit)) 
            discard;
        tEnter = max(tEnter, 0.0);

        // -------- step-size invariant opacity terms --------
        vec3 boxSizeO = boxMax - boxMin;                    // object-space size
        vec3 dim      = vec3(textureSize(volume, 0));       // voxel counts (X,Y,Z)
        vec3 voxelO   = boxSizeO / dim;                     // voxel size (object units)

        // world-object length of one marching step along this ray
        float stepObj = length(mat3(invShear) * (rdW * stepWorld));

        // “steps per voxel” along this ray (orientation aware)
        float dVoxel  = max(dot(abs(rd), voxelO), 1e-6);
        float kStep   = stepObj / dVoxel;

        // -------- march --------
        vec3 invBoxSize = 1.0 / boxSizeO;
        vec4 acc = vec4(0.0);

        for (float t = tEnter; t < tExit && acc.a < 0.98; t += stepObj) {
            vec3 pos = ro + rd * t;                           // object-space position
            vec3 uvw = (pos - boxMin) * invBoxSize;           // [0,1]^3

            float s  = texture(volume, uvw).r;                // scalar sample
            vec4 tf  = texture(transfer, s);                  // color + base alpha

            // convert TF alpha to per-step alpha (Beer-Lambert) and premultiply
            float a  = 1.0 - exp(-opacity * tf.a * kStep);

            // color
            vec3  c  = tf.rgb;
                // c  /= 1000; // bit-depth scaling
                c  = pow(c, vec3(gamma)); // gamma
                c  *= a; // alpha
                c  = clamp(c, cMin, cMax); // clipping
                c = (c - cMin) / (cMax - cMin);
                
            // front-to-back compositing (premultiplied)
            acc.rgb += (1.0 - acc.a) * c;
            acc.a   += (1.0 - acc.a) * a;
        }
        
        outColor = acc;
    } else {
        // pixel → [0,1] UV across the screen
        vec2 uv = gl_FragCoord.xy / viewportSize;

        // convert voxel index → normalized texture coord at the *center* of the slice
        ivec3 dim = textureSize(volume, 0);
        float z   = clamp(zSlice, 0.0, float(dim.z - 1));
        float tz  = (z + 0.5) / float(dim.z);   // sample at slice center to avoid mixing

        // sample and show as grayscale
        float s = texture(volume, vec3(uv, tz)).r;
        
        outColor = vec4(s, s, s, 1.0);    
    }
    
    FragColor = outColor;
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
    def __init__(self, window, position=glm.vec3(0,0,5), look_at=glm.vec3(0,0,0)):
        self.window = window

        # window state
        self.win_w = self.win_h = 0
        self.win_x = self.win_y = 0

        # camera params
        self.FOV = 45.0
        self.NEAR_FIELD = 0.1
        self.FAR_FIELD  = 10000.0
        self.world_up   = glm.vec3(0,1,0)

        # control gains
        self.ROT_SENS   = 0.25   # deg/pixel
        self.PAN_SENS   = 1.0    # world-per-pixel multiplier
        self.ZOOM_SENS  = 1.0
        self.MIN_RADIUS = 0.01
        self.MAX_PITCH  = math.radians(89.0)

        # orbit state
        self.look_at = glm.vec3(look_at)
        off = glm.vec3(position) - self.look_at
        self.radius = float(glm.length(off)) if glm.length(off) > 0 else 1.0
        self.yaw    = math.atan2(off.x, off.z)  # yaw=0 → +Z
        self.pitch  = math.asin(max(-1.0, min(1.0, off.y / max(self.radius, 1e-8))))

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
        return glm.perspective(glm.radians(self.FOV), self.aspect_ratio, self.NEAR_FIELD, self.FAR_FIELD)

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

    # ---------- callbacks ----------
    def _scroll_callback(self, window, dx, dy):
        self.scroll_offset = dy

    def _button_callback(self, window, button, action, mods):
        if action == glfw.PRESS:
            if button == glfw.MOUSE_BUTTON_LEFT:
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
        cp = math.cos(self.pitch); sp = math.sin(self.pitch)
        cy = math.cos(self.yaw);   sy = math.sin(self.yaw)
        dir_vec = glm.vec3(cp * sy, sp, cp * cy)  # Y-up, yaw=0 → +Z
        self.position = self.look_at + self.radius * dir_vec

    def _update_basis(self):
        self.front = glm.normalize(self.look_at - self.position)
        self.right = glm.normalize(glm.cross(self.front, self.world_up))
        self.up    = glm.normalize(glm.cross(self.right, self.front))

    def _mouse_move(self):
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
            # screen pixels → world units at current radius
            vpp = (2.0 * self.radius * math.tan(math.radians(self.FOV)*0.5)) / max(1.0, float(self.win_h))
            sx = vpp * self.aspect_ratio * self.PAN_SENS
            sy = vpp * self.PAN_SENS
            pan = (-dx) * sx * self.right + (dy) * sy * self.up
            self.look_at  += pan
            self.position += pan

    def _scroll_move(self, dt):
        if not self.scroll_offset:
            return
        # exponential dolly on radius
        scale = math.exp(-self.scroll_offset * self.ZOOM_SENS * (dt if dt > 0 else 1.0))
        self.radius = max(self.MIN_RADIUS, self.radius * scale)
        self._recompute_position()
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

    def __init__(self, view, parent_controller=None):
        """
            GUIController a-la CameraViewController:
            Has a GLFrameViewer that runs the render loop on it's
            own thread to maintain the GL Context separate from
            Tk.mainloop().
        """

        super().__init__(view, parent_controller)

        # OpenGL viewer
        self.viewer = GLFrameViewer()

        # start rendering thread
        self.viewer.start_render_loop(window_dim=(512,512))

        # image widgets
        self.image_palette = view.lut.get_widgets()

        # Binding for adjusting lookup table min/max counts
        self.image_palette["Min"].get_variable().trace_add(
            "write", self._on_minmax_changed
        )
        self.image_palette["Max"].get_variable().trace_add(
            "write", self._on_minmax_changed
        )

    def display_image(self, image: SharedNDArray) -> None:

        self.viewer.try_to_display_image(image)

    # private util functions
    
    def reset(self):
        self.viewer.rendered_images = 0

    def _on_minmax_changed(self, *args):

        min_counts = self.image_palette["Min"].get()
        max_counts = self.image_palette["Max"].get()

        try:
            assert isinstance(min_counts, int)
            assert isinstance(max_counts, int)
        except AssertionError:
            return

        self.viewer.set_min_max([min_counts, max_counts])

class GLFrameViewer:

    def __init__(self):

        # concurrency
        self.cmd_q      = queue.Queue()
        self.data_q     = queue.Queue(maxsize=RING_BUF_SIZE)
        self.is_running = threading.Event()
        self.is_ready   = threading.Event()
        self.thread     = None

        # GL objects (created in render thread)
        self.window = None
        self.shader = None
        self.vao    = None
        self.pbo    = None
        self.timer  = FrameTimer(every=0.2)

        # texture
        self.tex = None

        # config
        self.mode         = "frame"
        self.width        = None
        self.height       = None
        self.min_max      = None
        self.do_autoscale = False
        # ...

        # monitoring
        self.rendered_images = 0

    def start_render_loop(self, window_dim=(1000,800), title="Camera View"):
        if self.thread and self.thread.is_alive():
            return
        
        # create and start render thread
        self.is_running.set()
        self.thread = threading.Thread(
            target=self.render_thread,
            args=(window_dim, title)
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
            # init GLFW
            if not glfw.init():
                raise RuntimeError("ERROR: GLFW init failed!")

            #version 330 core
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

            # create window
            self.width, self.height = window_dim
            self.window = glfw.create_window(self.width, self.height, title, None, None)

            # GL context
            glfw.make_context_current(self.window)
            glfw.swap_interval(0) # VSync off?

            # Can import GL now that in-thread context exists
            from OpenGL import GL as _GL
            GL = _GL

            # can now create GL objects
            self.shader = Shader(VERT_SRC, FRAG_2D_SRC)
            self.vao    = GL.glGenVertexArrays(1) # quad

            # ready to render
            self.is_ready.set()

            # if the texture doesn't exist, create it
            if not self.tex:
                self.make_texture()
            if not self.pbo:
                nbytes = self.width * self.height * 2
                self.make_pbo_ring(nbytes)

            # bind sampler unit
            self.shader.use()
            self.shader.set_int('pixels', 0) # GL_TEXTURE0

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
                    self.update_image(image)
                except queue.Empty:
                    pass

                if self.timer.tick() == 0 and self.do_autoscale:
                    try:
                        self.autoscale(image)
                    except NameError:
                        pass

                # render frame
                self.draw_frame()
            
            # cleanup
            try:
                if self.tex: 
                    GL.glDeleteTextures([self.tex])
                    self.tex = None
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

    def _ensure_gl_ready(self):
        if not (self.window and self.shader and self.vao):
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

    def update_image(self, im : np.ndarray):

        def _do():
            self._ensure_gl_ready()
            self.update_texture(im)
        
        # self.cmd_q.put(_do)
        self.cmd_q.put_nowait(_do)

    def make_texture(self):

        self.tex = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex)

        # params
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)

        nx, ny = (self.width, self.height)
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

    @performance_monitor(prefix="GL: Update Texture", display_result=lambda i: {"image_id": int(i)})
    def update_texture(self, data : np.ndarray):
        """
            Update 2D texture pixels with new data.
        """
        # uint16 and C-contiguous
        if not data.flags['C_CONTIGUOUS']:
            data = np.ascontiguousarray(data)
            print("Made contiguous!")
        if data.dtype != np.uint16:
            data = data.astype(np.uint16)
            print("Converted to uint16!")
        
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
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glTexSubImage2D(
            GL.GL_TEXTURE_2D,       # target
            0,                      # mipmap level
            0,                      # xoffset
            0,                      # yoffset
            nx,                     # width
            ny,                     # height
            GL.GL_RED,              # format
            GL.GL_UNSIGNED_SHORT,   # type
            None
        )

        # cleanup
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)

        self.rendered_images = (self.rendered_images + 1) % 100

        return self.rendered_images

    def draw_frame(self):
        """
            Simply renders the texture once per frame.
        """
        if not self.tex:
            return # don't render if no texture    

        GL.glViewport(0, 0, self.width, self.height)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        self.shader.use()
        self.shader.set_vec2('viewportSize', (self.width, self.height))

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex)

        GL.glBindVertexArray(self.vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
        GL.glBindVertexArray(0)
        
        # render
        t0 = time.perf_counter()
        glfw.swap_buffers(self.window)
        stall_ms = (time.perf_counter() - t0) * 1000
        # if stall_ms > 15:
        #     print(f"Swap stall: {stall_ms:.2f} ms")

        # user input
        glfw.poll_events()

    # ----- update functions -----

    def set_min_max(self, min_max: list):
        # self.min_max = min_max

        def _do():
            self._ensure_gl_ready()
            self.shader.use()
            self.shader.set_vec2('cMinMax', min_max)

        self.cmd_q.put(_do)

    def autoscale(self, image: np.ndarray):

        # only tax the CPU every timer tick
        if self.timer.frame_ctr > 0:
            return

        min_pix = image.min()
        max_pix = image.max()
        self.set_min_max([min_pix, max_pix])

#%%
if __name__ == '__main__':

    TEST_MODE = "volume"

    from navigate.model.concurrency.concurrency_tools import SharedNDArray
    import tkinter as tk

    root = tk.Tk()
    root.geometry("400x300")

    viewer = GLFrameViewer()

    if TEST_MODE == "performance":

        # --- profiling tests ---
        import statistics as stats

        def print_stats(label, samples_ms):
            if not samples_ms:
                print(f"{label}: no samples")
                return
            ms = samples_ms
            print(f"\n{label}")
            print("-"*max(24, len(label)))
            print(f"count={len(ms)}  min={min(ms):.3f} ms  med={stats.median(ms):.3f} ms  "
                f"p90={np.percentile(ms,90):.3f} ms  p99={np.percentile(ms,99):.3f} ms  max={max(ms):.3f} ms")

        def warm_start(viewer):
            print("\n[Warmup] starting render loop…")
            viewer.start_render_loop((1024, 1024), "GLFrameViewer Profile")
            time.sleep(1.0)  # let GLFW/driver settle

        def bench_enqueue_numpy(viewer, shape=(1024,1024), seconds=2.0):
            print("\n[Test 1] Enqueue cost: numpy.ndarray → update_image")
            h, w = shape
            frame = (np.random.randint(0, 65535, (h, w)).astype(np.uint16))
            times = []
            t_end = time.perf_counter() + seconds
            i = 0
            while time.perf_counter() < t_end:
                t0 = time.perf_counter()
                viewer.try_to_display_image(frame)
                times.append((time.perf_counter() - t0)*1000)
                i += 1
            print_stats("Enqueue (numpy) ms", times)
            print(f"approx calls/s: {i/seconds:.1f}")

        def bench_enqueue_shared(viewer, shape=(1024,1024), seconds=2.0):
            print("\n[Test 2] Enqueue cost: SharedNDArray → update_image")
            h, w = shape
            snd = SharedNDArray(shape=(h,w), dtype=np.uint16)
            # fill once (in this process)
            snd[:] = np.random.randint(0, 65535, (h, w), dtype=np.uint16)
            times = []
            t_end = time.perf_counter() + seconds
            i = 0
            while time.perf_counter() < t_end:
                t0 = time.perf_counter()
                viewer.try_to_display_image(snd)
                times.append((time.perf_counter() - t0)*1000)
                i += 1
            print_stats("Enqueue (SharedNDArray) ms", times)
            print(f"approx calls/s: {i/seconds:.1f}")

        def bench_upload_static(viewer, shape=(1024,1024), seconds=2.0):
            print("\n[Test 3] Upload pressure: static frame (no per-frame CPU work)")
            h, w = shape
            frame = np.random.randint(0, 65535, (h, w), dtype=np.uint16)
            sends = 0
            t_end = time.perf_counter() + seconds
            while time.perf_counter() < t_end:
                viewer.try_to_display_image(frame)
                sends += 1
            print(f"static uploads issued: {sends} in {seconds}s  → {sends/seconds:.1f} calls/s")
            print("(Correlate with swap stall prints from GL thread above.)")

        def bench_upload_random(viewer, shape=(1024,1024), seconds=2.0):
            print("\n[Test 4] Upload pressure: per-frame randomize (adds CPU work)")
            h, w = shape
            sends = 0
            t_end = time.perf_counter() + seconds
            while time.perf_counter() < t_end:
                frame = np.random.randint(0, 65535, (h, w), dtype=np.uint16)
                viewer.try_to_display_image(frame)
                sends += 1
            print(f"randomized uploads issued: {sends} in {seconds}s  → {sends/seconds:.1f} calls/s")
            print("(If this drops a lot vs static, CPU frame gen is part of the bottleneck.)")

        def bench_size_sweep(viewer, sizes=((512,512),(1024,1024),(1536,1536),(2048,2048)), per_size_seconds=1.0):
            print("\n[Test 5] Throughput vs image size (static frame per size)")
            for h, w in sizes:
                frame = np.random.randint(0, 65535, (h, w), dtype=np.uint16)
                sends = 0
                t_end = time.perf_counter() + per_size_seconds
                while time.perf_counter() < t_end:
                    viewer.try_to_display_image(frame)
                    sends += 1
                mb = (h*w*2)/1e6
                print(f"  {h}x{w} ({mb:.1f} MB): {sends/per_size_seconds:.1f} calls/s")

        def bench_producer_rate(viewer, shape=(1024,1024), target_fps=120, seconds=3.0):
            print(f"\n[Test 6] Producer thread @ {target_fps} Hz: queue contention test")
            h, w = shape
            frame = np.random.randint(0, 65535, (h, w), dtype=np.uint16)
            period = 1.0/target_fps
            sends = 0
            stop = threading.Event()

            def producer():
                nonlocal sends
                next_t = time.perf_counter()
                while not stop.is_set():
                    viewer.try_to_display_image(frame)
                    sends += 1
                    next_t += period
                    # sleep with catch-up
                    dt = next_t - time.perf_counter()
                    if dt > 0:
                        time.sleep(dt)

            th = threading.Thread(target=producer, daemon=True)
            th.start()
            time.sleep(seconds)
            stop.set()
            th.join(timeout=1.0)
            print(f"sent {sends} frames in {seconds}s → {sends/seconds:.1f} Hz")
            print("Watch for any '[GL] Command queue backlog' (if you added that) or swap stalls; if we can't keep up, the consumer (GL thread) is the limiter.")

        # ---- run the suite ----
        warm_start(viewer)

        # idle settle
        print("\n[Idle] Letting viewer run idle for 0.5s… (baseline swap stalls)")
        time.sleep(0.5)

        def run_tests():

            bench_enqueue_numpy(viewer, shape=(1024,1024), seconds=2.0)
            bench_enqueue_shared(viewer, shape=(1024,1024), seconds=2.0)
            bench_upload_static(viewer, shape=(1024,1024), seconds=2.0)
            bench_upload_random(viewer, shape=(1024,1024), seconds=2.0)
            bench_size_sweep(viewer, sizes=((256,256),(512,512),(1024,1024)), per_size_seconds=1.0)
            bench_producer_rate(viewer, shape=(1024,1024), target_fps=120, seconds=3.0)

            print("\n[Done] You can close the window or leave it running.")
        # -----------------------

        tk.Button(root, text="RUN TESTS", command=run_tests).pack()

    root.mainloop()
