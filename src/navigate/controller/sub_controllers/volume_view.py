import numpy as np
from OpenGL import GL
import glfw
import glm
from typing import Union
import math
from multiprocessing import Process, shared_memory

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
uniform float opacity = 0.15;  // global density/opacity

// OPM parameters
uniform float shear_angle = 45.0;   // degrees
uniform float dz = 0.1345;          // um    
uniform float px = 0.1345;          // um

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
    m[1][2] = px * k / dz;
    
    return m;
}

void main()
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
        vec3  c  = tf.rgb * a;

        // front-to-back compositing (premultiplied)
        acc.rgb += (1.0 - acc.a) * c;
        acc.a   += (1.0 - acc.a) * a;
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

class GLVolumeViewer:

    def __init__(self):
        # texture storage
        self.tex_3d, self.tex_1d = None, None

    def create_window(self):

        if not glfw.init():
            print("Failed to initialize GLFW!")
            return
        
        self.window = glfw.create_window(1024, 800, "3D Viewer", None, None)

        self.camera = Camera(self.window, position=[-400, 400, 400])
        self.frame_timer = FrameTimer()

        if not self.window:
            glfw.terminate()
            return

        # create the GL context
        glfw.make_context_current(self.window)
        
        # create ray-marching shader
        self.shader = Shader(VERT_SRC, FRAG_SRC)
        
        # VAO
        self.vao = GL.glGenVertexArrays(1)

    def main_loop(self):

        while not glfw.window_should_close(self.window):

            # updates
            self.frame_timer.tick(True)
            self.camera.update(self.frame_timer.delta_time)

            GL.glViewport(0, 0, self.camera.win_w, self.camera.win_h)

            # render (if texture exists)
            if self.tex_3d and self.tex_1d:

                GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

                self.shader.use()
                # viewport
                self.shader.set_vec2('viewportSize', (self.camera.win_w, self.camera.win_h))

                # inverse(proj*view)
                inv_vp = glm.inverse(self.camera.projection * self.camera.view)
                GL.glUniformMatrix4fv(self.shader.loc("invProjView"), 1, GL.GL_TRUE, np.array(inv_vp, np.float32))

                # draw texture
                GL.glActiveTexture(GL.GL_TEXTURE0)
                GL.glBindTexture(GL.GL_TEXTURE_3D, self.tex_3d)
                GL.glActiveTexture(GL.GL_TEXTURE1)
                GL.glBindTexture(GL.GL_TEXTURE_1D, self.tex_1d)

                GL.glDisable(GL.GL_DEPTH_TEST)
                GL.glDisable(GL.GL_CULL_FACE)
                GL.glDisable(GL.GL_BLEND)  # blending handled inside the shader

                GL.glBindVertexArray(self.vao)
                GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
                GL.glBindVertexArray(0)


            # swap buffers
            glfw.swap_buffers(self.window)

            # poll events
            glfw.poll_events()

        # end
        glfw.terminate()

    def bind_image_data(self, vol : np.ndarray):
        
        # scaling and normalizing
        vol = np.power(vol, 0.9).astype(np.float32)
        vol /= vol.max()        

        # volume bounds
        nz, ny, nx = 0.5 * np.array(vol.shape) - 0.5

        # create textures
        self.tex_3d = self.make_volume_texture(vol)
        self.tex_1d = self.make_transfer_texture()

        # shader configs
        self.shader.use()
        self.shader.set_int('volume',   0)
        self.shader.set_int('transfer', 1)
        self.shader.set_float('stepWorld', 0.25)
        self.shader.set_vec3('boxMin', [-nx, -ny, -nz])
        self.shader.set_vec3('boxMax', [ nx,  ny,  nz])

    @staticmethod
    def make_volume_texture(vol_f32 : np.ndarray):  
        # vol_f32 shape = (Z,Y,X), values in [0,1]
        z, y, x = vol_f32.shape

        # create a texture to store the 3d volume
        tex = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_3D, tex)
        
        # texture params
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_R, GL.GL_CLAMP_TO_EDGE)

        # write image data to texture
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glTexImage3D(GL.GL_TEXTURE_3D, 0,
                        GL.GL_R16F,   # 16-bit float per voxel (enough for 0..1)
                        x, y, z, 0,
                        GL.GL_RED, GL.GL_FLOAT,
                        vol_f32.astype(np.float32))
        
        return tex

    @staticmethod
    def make_transfer_texture(N : int = 256):
        # grayscale ramp with alpha = value
        tf = np.linspace(0,1,N, dtype=np.float32)
        rgba = np.stack([tf, tf, tf, tf], axis=1)  # premultiplied in the shader
        
        # create a 1d transfer texture
        tex = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_1D, tex)
        
        # texture params
        GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        
        # write
        GL.glTexImage1D(GL.GL_TEXTURE_1D, 0,
                        GL.GL_RGBA8, N, 0,
                        GL.GL_RGBA, GL.GL_UNSIGNED_BYTE,
                        (rgba*255).astype(np.uint8))
        return tex

#%%
if __name__ == '__main__':

    import tkinter as tk

    root = tk.Tk('test')
    root.geometry('400x300')

    main_frame = tk.Frame(root, width=100, height=100)
    main_frame.pack()
    launch_button = tk.Button(main_frame, text='LAUNCH')    
    test_button = tk.Button(main_frame, text='TEST') 
    launch_button.pack()
    test_button.pack()

    def gauss_3d(pix, m=(0,0,0), s=(1,1,3)):

        x, y, z = np.array(np.meshgrid(range(pix), range(pix), range(pix)), dtype=np.float32)

        x -= x.mean()
        y -= y.mean()
        z -= z.mean()

        g = ((x - m[2])/s[2])**2 + ((y - m[1])/s[1])**2 + ((z - m[0])/s[0])**2
        g = np.exp(-g)

        return g

    # image data
    path = r"C:\Users\conor\Documents\Python\tkopengl\aliasing_decon\data_reto.tif"
    import tifffile as tiff
    im = tiff.imread(path)

    from navigate.model.concurrency.concurrency_tools import ObjectInSubprocess

    viewer = ObjectInSubprocess(GLVolumeViewer)

    def launch_viewer():
        viewer.create_window()
        viewer.bind_image_data(im)
        viewer.main_loop()

    launch_button.configure(command=launch_viewer)
    test_button.configure(command=lambda: print("Test!"))

    root.mainloop()