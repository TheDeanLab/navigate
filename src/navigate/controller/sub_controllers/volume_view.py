import numpy as np
# from OpenGL import GL
import glfw
import glm
from typing import Union
import math
# from multiprocessing import Process, shared_memory
import threading
import queue
import time
import traceback

GL = None

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

void main()
{
    vec2 uv = gl_FragCoord.xy / viewportSize;

    FragColor = texture(pixels, uv);
}

"""

FRAG_SRC = """
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

    def __init__(self):

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

        if self.frame_timer > 2.0:
            avg_delta_time = self.frame_timer / self.frame_ctr
            if verbose:
                print(f"FPS: {1/avg_delta_time}")
            
            self.frame_ctr = 0
            self.frame_timer = 0.

class GLFrameViewer:

    def __init__(self):

        # concurrency
        self.cmd_queue = queue.Queue()
        self.is_running  = threading.Event()
        self.is_ready    = threading.Event()
        self.thread      = None

        # GL objects (created in render thread)
        self.window = None
        self.shader = None
        self.vao    = None
        self.timer  = FrameTimer()

        # texture
        self.tex = None

        # config
        self.width  = None
        self.height = None
        # ...

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

        # Wake the queue if waiting
        self.cmd_queue.put(lambda: None)

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

            # --------- MAIN LOOP ---------
            while self.is_running.is_set() and not glfw.window_should_close(self.window):

                for _ in range(64):
                    try:
                        cmd = self.cmd_queue.get_nowait()
                    except queue.Empty:
                        break
                    try:
                        cmd()
                    except Exception as e:
                        print(f"[GL Thread] Error Executing cmd={cmd}:", e)
                        traceback.print_exc()
                
                # render frame
                self.draw_frame()

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

    def update_image(self, im : np.ndarray):

        def _do():
            self._ensure_gl_ready()
            self.update_texture(im)
        
        self.cmd_queue.put(_do)

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
            GL.GL_TEXTURE_2D,   # target
            0,                  # mipmap level
            GL.GL_R16F,         # internal format
            nx,
            ny,
            0,                  # border
            GL.GL_RED,          # format
            GL.GL_FLOAT,        # type
            np.zeros((ny, nx), dtype=np.float32)        
        )

    def update_texture(self, data : np.ndarray):
        """
            Update 2D texture pixels with new data.
        """
        ny, nx = data.shape

        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

        GL.glTexSubImage2D(
            GL.GL_TEXTURE_2D,   # target
            0,                  # mipmap level
            0,                  # xoffset
            0,                  # yoffset
            nx,                 # width
            ny,                 # height
            GL.GL_RED,          # format
            GL.GL_FLOAT,        # type
            data.astype(np.float32)
        )

    def draw_frame(self):
        """
            Simply renders the texture once per frame.
        """
        if not self.tex:
            return # don't render if no texture
        
        self.timer.tick()
        
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
        glfw.swap_buffers(self.window)

        # user input
        glfw.poll_events()

class GLVolumeViewer:
    def __init__(self):
        # thread/loop state
        self._cmd_q = queue.Queue()
        self._running = threading.Event()
        self._ready   = threading.Event()
        self._thread  = None

        # window / GL objects (created in render thread)
        self.window = None
        self.shader = None
        self.vao    = None
        self.camera = None
        self.timer  = FrameTimer()

        # stack data
        self.stack = None

        # textures
        self.tex_3d = None
        self.tex_1d = None

        # cached config
        self._opacity   = 0.15
        self._stepWorld = 0.25
        self._cRange    = []
        self._gamma     = 1.0
        self._shear_ang = None
        self._boxMin    = None
        self._boxMax    = None

    # ---------------- public API (non-blocking) ----------------

    def start_render_loop(self, width=1024, height=800, title="3D Viewer"):
        """Spawn the render thread and return immediately."""
        if self._thread and self._thread.is_alive():
            return
        self._running.set()
        self._thread = threading.Thread(
            target=self._render_thread, args=(width, height, title), daemon=True
        )
        self._thread.start()
        # Optionally wait until GL is ready before returning:
        self._ready.wait(timeout=5.0)

    def stop_render_loop(self):
        """Ask the render thread to exit, and wait for it."""
        if not self._thread:
            return
        self._running.clear()
        # Post a no-op to wake queue in case it’s waiting
        self._cmd_q.put(lambda: None)
        self._thread.join(timeout=3.0)
        self._thread = None

    # High-level commands (enqueue small callables):

    def add_slice(self, image : np.ndarray, n_slices : int, i: int):

        # new_slice = image[np.newaxis].astype(np.float32)

        # print(f"new_slice {i}:", new_slice.shape)

        # try:
        #     self.stack = np.vstack([
        #         self.stack,
        #         new_slice
        #     ])
        # except ValueError:
        #     self.stack = new_slice

        # if len(self.stack) == n_slices-1:
        #     self.tex_3d, self.tex_1d = None, None
        #     self.bind_volume(self.stack)
        #     self.stack = None

        if self.stack is not None:
            if (n_slices,) + image.shape != self.stack.shape:
                # print("Dimension mismatch... stack = None")
                self.stack = None
                self.add_slice(image, n_slices, i)
                
            t0 = time.time()
            self.stack[i] = image
            self.bind_slice(image, i)
            # print(f"Added {image.shape} {image.astype(np.float32).nbytes/1e6:.2f} MB slice {i}/{n_slices} in {1000.*(time.time() - t0):.3f} ms")
        else:
            ny, nx = image.shape
            # print("Allocating volume...", (n_slices, ny, nx))
            self.stack = np.zeros((n_slices, ny, nx), dtype=np.float32)
            self.bind_volume(self.stack)
            self.add_slice(image, n_slices, i)

    def bind_slice(self, im_f32: np.ndarray, z: int = 0):

        # im_f32 /= self.stack.max() # Extremely slow! Scale in shader...
        im_f32 = im_f32 / 1000.

        def _do():
            self._ensure_gl_ready()

            # assumes textures created...
            self._update_texture_slice_z(self.tex_3d, im_f32, z)
        
        self._cmd_q.put(_do)

    def bind_volume(self, vol_f32: np.ndarray):
        """Upload / replace the 3D volume texture (runs on GL thread)."""
        vol_f32 = np.asarray(vol_f32, dtype=np.float32)
        # vol_f32 = np.clip(vol_f32, a_min=0, a_max=4000)
        m = vol_f32.max()
        if m > 0:
            vol_f32 /= m
        # vol_f32 = np.power(vol_f32, 0.9)

        # object-space bounds: centered on origin
        nz, ny, nx = 0.5*np.array(vol_f32.shape, dtype=np.float32) - 0.5
        boxMin = (-nx, -ny, -nz)
        boxMax = ( nx,  ny,  nz)

        def _do():
            self._ensure_gl_ready()
            # (re)create textures
            if self.tex_3d is None:
                self.tex_3d = self._make_volume_texture(vol_f32)
            else:
                self._update_volume_texture(self.tex_3d, vol_f32)
            if self.tex_1d is None:
                self.tex_1d = self._make_transfer_texture()

            # set uniforms
            self.shader.use()
            self.shader.set_int('volume',   0)
            self.shader.set_int('transfer', 1)
            self.shader.set_float('stepWorld', self._stepWorld)
            self.shader.set_vec3('boxMin', boxMin)
            self.shader.set_vec3('boxMax', boxMax)

            self._boxMin, self._boxMax = glm.vec3(*boxMin), glm.vec3(*boxMax)

        self._cmd_q.put(_do)

    def set_opacity(self, value: float):
        self._opacity = float(value)
        def _do():
            self._ensure_gl_ready()
            self.shader.use()
            self.shader.set_float('opacity', self._opacity)
        self._cmd_q.put(_do)

    def set_gamma(self, value: float):
        self._gamma = float(value)
        def _do():
            self._ensure_gl_ready()
            self.shader.use()
            self.shader.set_float('gamma', self._gamma)
        self._cmd_q.put(_do)

    def set_shear_angle(self, value: float):
        self._shear_ang = float(value)
        def _do():
            self._ensure_gl_ready()
            self.shader.use()
            self.shader.set_float('shear_angle', self._shear_ang)
        self._cmd_q.put(_do)

    def set_c_range(self, value: list):
        self._cRange = list(value)
        def _do():
            self._ensure_gl_ready()
            self.shader.use()
            self.shader.set_float('cMin', self._cRange[0])
            self.shader.set_float('cMax', self._cRange[1])
        self._cmd_q.put(_do)            

    def set_zstep(self, value: float):
        self._dz = float(value)
        def _do():
            self._ensure_gl_ready()
            self.shader.use()
            self.shader.set_float('dz', self._dz)
        self._cmd_q.put(_do)

    def set_step_world(self, value: float):
        self._stepWorld = float(value)
        def _do():
            self._ensure_gl_ready()
            self.shader.use()
            self.shader.set_float('stepWorld', self._stepWorld)
        self._cmd_q.put(_do)

    def set_shear_angle(self, degrees: float):
        def _do():
            self._ensure_gl_ready()
            self.shader.use()
            self.shader.set_float('shear_angle', float(degrees))
        self._cmd_q.put(_do)

    # ---------------- render thread ----------------

    def _render_thread(self, width, height, title):
        """Lives entirely in the child; owns the window + GL context."""
        global GL
        try:
            # All GLFW/GL calls in this thread:
            if not glfw.init():
                raise RuntimeError("GLFW init failed")
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
            self.window = glfw.create_window(width, height, title, None, None)
            if not self.window:
                raise RuntimeError("Failed to create GLFW window")

            glfw.make_context_current(self.window)

            # Import GL *now* (context thread)
            from OpenGL import GL as _GL
            GL = _GL

            # Build pipeline objects now that GL is bound to this thread
            self.shader = Shader(VERT_SRC, FRAG_SRC)
            self.vao    = GL.glGenVertexArrays(1)

            # camera + timer
            self.camera = Camera(self.window, position=[-400, 400, 400])

            # defaults on shader
            self.shader.use()
            self.shader.set_int('volume',   0)
            self.shader.set_int('transfer', 1)
            self.shader.set_float('opacity', self._opacity)
            self.shader.set_float('stepWorld', self._stepWorld)

            self._ready.set()

            # main loop
            while self._running.is_set() and not glfw.window_should_close(self.window):
                # drain pending commands (without blocking the frame)
                for _ in range(64):  # avoid starving rendering
                    try:
                        cmd = self._cmd_q.get_nowait()
                    except queue.Empty:
                        break
                    try:
                        cmd()
                    except Exception as e:
                        print("[GL thread] command error:", e)

                # draw one frame
                self._frame()

            # cleanup
            try:
                if self.tex_3d: 
                    GL.glDeleteTextures([self.tex_3d])
                    self.tex_3d = None
                if self.tex_1d: 
                    GL.glDeleteTextures([self.tex_1d])
                    self.tex_1d = None
                if self.vao:    
                    GL.glDeleteVertexArrays(1, [self.vao])
                    self.vao = None
            finally:
                glfw.destroy_window(self.window)
                glfw.terminate()
                self.window = None
        except Exception as e:
            print("[GL thread] fatal:", e)
            try:
                glfw.terminate()
            except Exception:
                pass
            self.window = None
            self._ready.set()  # unblock waiters even on failure

    # ---------------- per-frame ----------------

    def _frame(self):
        self.timer.tick(False)
        self.camera.update(self.timer.delta_time)

        GL.glViewport(0, 0, self.camera.win_w, self.camera.win_h)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        if self.tex_3d and self.tex_1d:
            self.shader.use()
            self.shader.set_vec2('viewportSize', (self.camera.win_w, self.camera.win_h))

            inv_vp = glm.inverse(self.camera.projection * self.camera.view)
            # transpose=True to feed row-major numpy as column-major
            GL.glUniformMatrix4fv(self.shader.loc("invProjView"), 1, GL.GL_TRUE,
                                  np.array(inv_vp, np.float32))

            GL.glActiveTexture(GL.GL_TEXTURE0); GL.glBindTexture(GL.GL_TEXTURE_3D, self.tex_3d)
            GL.glActiveTexture(GL.GL_TEXTURE1); GL.glBindTexture(GL.GL_TEXTURE_1D, self.tex_1d)

            GL.glDisable(GL.GL_DEPTH_TEST)
            GL.glDisable(GL.GL_CULL_FACE)
            GL.glDisable(GL.GL_BLEND)

            GL.glBindVertexArray(self.vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
            GL.glBindVertexArray(0)

        glfw.swap_buffers(self.window)
        glfw.poll_events()

    # ---------------- GL helpers (GL thread only) ----------------

    def _ensure_gl_ready(self):
        if not (self.window and self.shader and self.vao):
            raise RuntimeError("GL not ready yet")

    def _make_volume_texture(self, vol_f32: np.ndarray):
        z, y, x = vol_f32.shape
        tex = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_3D, tex)
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_R, GL.GL_CLAMP_TO_EDGE)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glTexImage3D(GL.GL_TEXTURE_3D, 0,
                        GL.GL_R16F,
                        x, y, z, 0,
                        GL.GL_RED, GL.GL_FLOAT,
                        vol_f32.astype(np.float32))
        return tex

    def _update_texture_slice_z(self, tex, im_f32 : np.ndarray, z : int):
        ny, nx = im_f32.shape

        data = np.ascontiguousarray(im_f32, dtype=np.float32)

        GL.glBindTexture(GL.GL_TEXTURE_3D, tex)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        
        # update only the data for slice (z)
        GL.glTexSubImage3D(GL.GL_TEXTURE_3D, 
                           0,           # level
                           0,           # xoffset (none)
                           0,           # yoffset (none)
                           # int(z),      # zoffset (z-slice position)
                           int(0),      # zoffset (z-slice position)
                           nx,          # width
                           ny,          # height
                           1,           # depth (one slice)
                           GL.GL_RED,   # format
                           GL.GL_FLOAT, # type
                           data         # image data
        )

    def _update_volume_texture(self, tex, vol_f32: np.ndarray):
        z, y, x = vol_f32.shape
        
        GL.glBindTexture(GL.GL_TEXTURE_3D, tex)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        
        # updates the whole volume texture in one shot
        GL.glTexSubImage3D(GL.GL_TEXTURE_3D, 0,
                           0, 0, 0, x, y, z,
                           GL.GL_RED, GL.GL_FLOAT,
                           vol_f32.astype(np.float32))

    def _make_transfer_texture(self, N: int = 256):
        tf = np.linspace(0, 1, N, dtype=np.float32)
        rgba = (np.stack([tf, tf, tf, tf], axis=1) * 255).astype(np.uint8)

        tex = GL.glGenTextures(1)
        
        GL.glBindTexture(GL.GL_TEXTURE_1D, tex)
        GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexImage1D(GL.GL_TEXTURE_1D, 0,
                        GL.GL_RGBA8, N, 0,
                        GL.GL_RGBA, GL.GL_UNSIGNED_BYTE,
                        rgba)
        return tex

#%%
if __name__ == '__main__':

    import os
    from navigate.model.concurrency.concurrency_tools import ObjectInSubprocess
    from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput
    import tkinter as tk
    from tkinter import ttk
    import tifffile as tiff

    root = tk.Tk()
    root.geometry("400x300")



    # your data
    # im = tiff.imread(r"C:\Users\conor\Documents\Python\tkopengl\aliasing_decon\beads_coverslip.tiff").astype(np.float32)
    # im = tiff.imread(r"C:\Users\conor\Documents\Python\tkopengl\aliasing_decon\data_reto.tif").astype(np.float32)
    # im = tiff.imread(r"C:\Users\conor\Documents\Python\tkopengl\aliasing_decon\A12_P0_mCherry.tiff").astype(np.float32)

    def downsample_if_needed(im : np.ndarray, max_gb=0.5):
        while True:
            im_size_GB = im.nbytes / 1e9
            print(f"Image size: {im_size_GB} GB...")
            if im_size_GB > max_gb:
                print(f"...exceeds 1.0 GB. Downsampling 2x...")
                im = im[::2, ::2, ::2]
            else:
                break
        
        return im

    frames = [
        downsample_if_needed(tiff.imread(
            os.path.join(r"C:\Users\conor\Documents\Python\tkopengl\aliasing_decon\movie", f"1_CH00_00000{t}.tif")
        ).astype(np.float32))
        for t in range(10)
    ]

    TEST_MODE = '2d'
    def launch():
        pass

    if TEST_MODE == '2d':
        viewer_2d = ObjectInSubprocess(GLFrameViewer)

        def launch():
            viewer_2d.start_render_loop((1000, 800), "Camera Viewer")

        import time
        def play():
            for t, vol in enumerate(frames):
                print("Frame:", t)
                n_slices = len(vol)
                for z in range(n_slices):
                    viewer_2d.update_image(vol[z])

        def stop():
            viewer_3d.stop_render_loop()

    elif TEST_MODE == '3d':
        viewer_3d = ObjectInSubprocess(GLVolumeViewer)

        def launch():
            viewer_3d.start_render_loop(1024, 800, "3D Viewer")

        import time
        def play():
            for t, vol in enumerate(frames):
                print("Frame:", t)
                n_slices = len(vol)
                for z in range(n_slices):
                    # print(f"Frame {t} slice {z}...")
                    viewer_3d.add_slice(vol[z], n_slices, z)

        def stop():
            viewer_3d.stop_render_loop()

        experiment = {
            'opacity': 0.10,
            'cMin': 0.0002,
            'cMax': 0.3000,
            'gamma': 1.2,
            'shear_angle': -30,
        }

        opacity = tk.DoubleVar(root, value=experiment['opacity'])
        def opacity_change():
            viewer_3d.set_opacity(opacity.get())
        
        cMin = tk.DoubleVar(root, value=experiment['cMin'])
        cMax = tk.DoubleVar(root, value=experiment['cMax'])
        def c_change():
            viewer_3d.set_c_range([cMin.get(), cMax.get()])

        gamma = tk.DoubleVar(root, value=experiment['gamma'])
        def gamma_change():
            viewer_3d.set_gamma(gamma.get())

        shear_angle = tk.DoubleVar(root, value=experiment['shear_angle'])
        def shear_angle_change():
            viewer_3d.set_shear_angle(shear_angle.get())

        settings = tk.LabelFrame(root, text="Settings").pack()
        
        LabelInput(
            settings, label_pos="left", label="Opacity",
            input_class=ttk.Spinbox, input_var=opacity,
            input_args={
                "from_": 0.05, 
                "to": 1.0, 
                "increment": 0.05,
                "command": opacity_change
                }
            ).pack()

        LabelInput(
            settings, label_pos="left", label="cMin",
            input_class=ttk.Spinbox, input_var=cMin,
            input_args={
                "from_": 0.0, 
                "to": 0.5, 
                "increment": 0.0001,
                "command": c_change
                }
            ).pack()

        LabelInput(
            settings, label_pos="left", label="cMax",
            input_class=ttk.Spinbox, input_var=cMax,
            input_args={
                "from_": 0.02, 
                "to": 1.0, 
                "increment": 0.01,
                "command": c_change
                }
            ).pack()

        LabelInput(
            settings, label_pos="left", label="Gamma",
            input_class=ttk.Spinbox, input_var=gamma,
            input_args={
                "from_": 0.05, 
                "to": 2.0, 
                "increment": 0.05,
                "command": gamma_change
                }
            ).pack()

        LabelInput(
            settings, label_pos="left", label="Shear Angle",
            input_class=ttk.Spinbox, input_var=shear_angle,
            input_args={
                "from_": -90.0, 
                "to": 90.0, 
                "increment": 2.5,
                "command": shear_angle_change
                }
            ).pack()

        opacity_change()
        c_change()
        gamma_change()
        shear_angle_change()

    tk.Button(root, text="LAUNCH", command=launch).pack()
    tk.Button(root, text="STOP", command=stop).pack()
    tk.Button(root, text="PLAY", command=play).pack()

    launch()
    root.mainloop()
