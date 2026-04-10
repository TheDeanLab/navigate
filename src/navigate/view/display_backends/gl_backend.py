import math
import numpy as np
import glfw
import glm
from typing import Union, Optional
import threading
import queue
import time
import traceback
import logging
import json
import cv2

# To be imported after GLVolumeViewer render thread is 
# initialized, so that GL context is available.
GL = None

#%%
class Shader:
    """Shader class for compiling and managing OpenGL shaders."""

    def __init__(self, vs: str, fs: str, from_file: bool=False):
        """Initialize the shader program.
        
        Parameters
        ----------
        vs : str
            Vertex shader source code or file path.
        fs : str
            Fragment shader source code or file path.
        from_file : bool, optional
            Whether the shader sources are in files, by default False.
        """
        if from_file:
            with open(vs, "r", encoding="utf-8") as f:
                vs = f.read()
            with open(fs, "r", encoding="utf-8") as f:
                fs = f.read()
            f.close()

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

    def set_mat4(self, name : str, m : Union[list, np.ndarray, glm.mat4], transpose: bool=False):
        if isinstance(m, glm.mat4):
            m = m.to_list()
    
        GL.glUniformMatrix4fv(
            self.loc(name), 
            1, 
            GL.GL_FALSE if not transpose else GL.GL_TRUE, 
            np.float32(m)
            )

class Camera:
    """
    Orbit (yaw/pitch + radius), pixel-accurate pan, dolly,
    and auto-recenter pivot to AABB under the cursor on RMB release.
    """
    def __init__(self, window, parent_viewer, position=glm.vec3(100), look_at=glm.vec3(0,0,0)):
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

    def set_ortho_view(self, pitch: float=0.0, yaw: float=0.0):
        # self.position = glm.vec3(position)
        self.look_at = glm.vec3(0.0)

        self.pitch  = glm.radians(pitch)
        self.yaw    = glm.radians(yaw)

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
            # screen pixels → world units at current radius
            vpp = (2.0 * self.radius * math.tan(math.radians(self.FOV)*0.5)) / max(1.0, float(self.win_h))
            sx = vpp * self.aspect_ratio * self.PAN_SENS
            sy = vpp * self.PAN_SENS
            pan = (-dx) * sx * self.right + (dy) * sy * self.up
            self.look_at  += pan
            self.position += pan


    def _scroll_move(self, dt):
        if not self.scroll_offset or dt == 0.0:
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

class GLVolumeViewBackend:
    """
    OpenGL volume viewer using GLFW and GLM.
    Provides orbit camera controls, 2D panning/zooming, and auto-recenter pivot.
    Designed for efficient rendering of large 3D volumes with dynamic updates.
    Communicates with parent controller via command queue for thread safety.
    """
    def __init__(self):
        
        # concurrency
        self.cmd_q      = queue.Queue()
        self.data_q     = queue.Queue()
        self.is_running = threading.Event()
        self.is_ready   = threading.Event()
        self.thread     = None

        # GLFW window
        self.window = None

        # GL objects (to be created in render() thread
        #             after GL context is initialized)
        self.shader      = None
        self.vao         = None
        self.camera      = None
        self.frame_timer = FrameTimer(every=1.0)

        # textures
        self.volume_textures  = None
        self.transfer_texture = None

        # image properties
        self.max_n_color_channels = 4
        self.luts                 = None
        self.volume_shape         = None
        self.num_slices           = 1
        self.min_max              = [0, 65535]
        self.curr_chan            = 0

    def thread_is_running(self):
        return self.is_running.is_set()

    def start(self, window_dim: tuple=(800, 600)):
        """Start the rendering thread and create the GLFW window."""
        if self.thread and self.thread.is_alive():
            return  # already running

        self.thread = threading.Thread(
            target=self._render_thread, 
            args=(window_dim,)
            )
        self.thread.start()
        self.is_running.set()
        
        # Wait until the render thread signals it's ready
        self.is_ready.wait()
    
    def show_window(self):
        """Make the GLFW window visible (call after start())."""
        glfw.set_window_attrib(self.window, glfw.VISIBLE, glfw.TRUE)

    def stop(self):
        """Stop the rendering thread and clean up resources."""
        if not self.thread or not self.thread.is_alive():
            return  # already stopped
        
        self.is_running.clear()

        # Wake the queues (if waiting)
        self.cmd_q.put(lambda: None)
        self.data_q.put(lambda: None)

        # Kill the thread
        if self.thread:
            self.thread.join()
            self.thread = None

    def add_slice(self, image: np.ndarray, z: int, ch: int):
        """Submit a single slice (z, ch) of the volume for rendering."""

        if self.volume_shape is not None:
            incoming_shape = (self.num_slices,) + image.shape
            
            # Guard against shape mismatch
            if incoming_shape != self.volume_shape:
                # Clear current vol shape
                self.volume_shape = None
                # Free textures
                self._gl_clear_textures()
                # Try again
                self.add_slice(image, z, ch)

            # If no mismatch, we can request the slice upload
            self._request_slice_upload(image, z, ch)
        else:
            # Send a request to the queue to create a new volume texture with the new shape
            self._request_new_volume_texture((self.num_slices,) + image.shape)

            # Try to add the slice again (after texture is created)
            self.add_slice(image, z, ch)

    def set_num_channels_and_slices(self, n_channels: int, n_slices: int):
        """Set the expected number of color channels and slices in the volume."""
        self.max_n_color_channels = n_channels
        self.num_slices = n_slices

    def set_min_max(self, min_max: list, ch: int=-1):
        if ch < 0:
            ch = self.curr_chan
        
        self.min_max = min_max
        
        def _do():
            self._ensure_gl_ready()
            
            self.shader.use()
            self.shader.set_vec2(
                f"cMinMax[{ch}]", 
                np.array(min_max, dtype=np.float32)/65535.
                )

        self.cmd_q.put(_do)

    def _set_glfw_window_visible(self, visible: bool=True):
        if self.window:
            glfw.set_window_attrib(
                self.window, 
                glfw.VISIBLE, 
                glfw.TRUE if visible else glfw.FALSE
                )
            self.window_visible = visible

    def _ensure_gl_ready(self):
        window = self.window
        vao = self.vao
        shader = self.shader

        if not (window and vao and shader):
            raise RuntimeError("GL not ready yet")

    def _render_thread(self, window_dim: tuple):
        global GL

        try:
            # Initialize GLFW
            if not glfw.init():
                raise RuntimeError("Failed to initialize GLFW!")
            
            # Create window and GL context
            # glfw.window_hint(glfw.VISIBLE, glfw.FALSE)  # start hidden until ready
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
            self.window = glfw.create_window(window_dim[0], window_dim[1], "Volume Viewer", None, None)

            # Set GL context
            try:
                glfw.make_context_current(self.window)
            except:
                glfw.destroy_window(self.window)
                glfw.terminate()
                raise RuntimeError("Failed to create OpenGL context! Your system may not support the required OpenGL version.")

            # Import GL after context creation
            from OpenGL import GL as _GL
            GL = _GL

            # Set up OpenGL state
            self._init_gl_resources()

            # signal that we're ready to receive commands and data
            self.is_ready.set()  

            # run the render loop
            self._render_loop()

        except Exception as e:
            print("[GL Thread] Fatal Error:", e)
            traceback.print_exc()
            self.is_ready.set()  # unblock start() if waiting
        
        finally:
            # clean up GL textures
            self._gl_clear_textures()

            # try to terminate GLFW
            try:
                if self.window:
                    glfw.destroy_window(self.window)
                glfw.terminate()
            except Exception:
                pass

    def _gl_clear_textures(self):
        """Delete existing GL textures and reset state."""
        if self.transfer_texture:
            GL.glDeleteTextures([self.transfer_texture])
            self.transfer_texture = None
        if self.volume_textures:
            GL.glDeleteTextures(len(self.volume_textures), self.volume_textures)
            self.volume_textures = None

    def _render_loop(self):
        """Main render loop: process commands/data, update camera, get data and draw."""
        
        # Flag to ensure GPU isn't wasted rendering when there are no changes to render.
        render_needed = False

        while self.is_running.is_set() and not glfw.window_should_close(self.window):
                
            # Keep processing until both queues are empty
            # This is important because add_slice() may queue texture creation commands
            had_work = True
            while had_work:
                had_work = False
                
                # Process all pending commands
                while True:
                    try:
                        cmd = self.cmd_q.get_nowait()
                        try:
                            cmd()
                            had_work = True
                        except Exception as e:
                            print(f"[GL Thread] Error executing command: {e}")
                            traceback.print_exc()
                    except queue.Empty:
                        break
                
                # Process all pending slice data
                while True:
                    try:
                        image, z, ch = self.data_q.get_nowait()
                        self.add_slice(image, z, ch)
                        had_work = True
                    except queue.Empty:
                        break

            # Always render (even if no textures yet, to show black screen)
            self._gl_render_scene()
            glfw.swap_buffers(self.window)

            # Poll events to keep window responsive
            glfw.poll_events()
            time.sleep(0.001)            

    def _gl_render_scene(self):
        """Renders the full-screen quad with the raymarching shader."""

        # Update timer
        self.frame_timer.tick(verbose=True)

        # Set viewport (handles window resizing and frame vs volume mode)
        self._config_gl_viewport()
        
        # Clear screen
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # Texture guard
        if not (self.volume_textures and self.transfer_texture):
            return

        # Update camera
        self.camera.update(self.frame_timer.delta_time)

        # Camera view-projection matrix
        inverse_proj_view = glm.inverse(
            self.camera.projection * self.camera.view
        )
        self.shader.use()
        self.shader.set_mat4("invProjView", inverse_proj_view)

        # Bind volume textures for all n-channels
        for i, tex in enumerate(self.volume_textures):
            GL.glActiveTexture(GL.GL_TEXTURE0 + i)
            GL.glBindTexture(GL.GL_TEXTURE_3D, tex)

        # Bind transfer function texture (last texture unit)
        GL.glActiveTexture(GL.GL_TEXTURE0 + self.max_n_color_channels)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.transfer_texture)

        # Disable depth test, culling, and blending for volume rendering
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_CULL_FACE)
        GL.glDisable(GL.GL_BLEND)

        # Draw full-screen quad (no VBO needed, vertices are generated in shader)
        GL.glBindVertexArray(self.vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        GL.glBindVertexArray(0) # Unbind VAO

    def _init_gl_resources(self):
        """Initialize shaders and set uniforms, create VAO, and set up camera."""

        import os
        from pathlib import Path
        shader_dir = os.path.join(Path(__file__).parent, "shaders")

        # Compile shader
        self.shader = Shader(
            vs=os.path.join(shader_dir, "simple_quad.vert"), 
            fs=os.path.join(shader_dir, "raymarch.frag"), 
            from_file=True
            )

        # Set up full-screen quad VAO
        self.vao = GL.glGenVertexArrays(1)

        # Set up camera
        self.camera = Camera(self.window, parent_viewer=self,  position=glm.vec3(200), look_at=glm.vec3(0, 0, 0))

        # Set initial shader uniforms
        self.shader.use()
        self._set_volume_texture_units()
        self.shader.set_float("stepWorld", 0.25)
        self.shader.set_float("opacity", 0.10)

    def _set_volume_texture_units(self):
        """Assign shader texture units for volume (n-color channels) and transfer function."""

        for i in range(self.max_n_color_channels):
            self.shader.set_int(f"volume[{i}]", i) # volume[i] = GL_TEXTUREi
        
        # transfer = GL_TEXTURE[max_n_color_channels] (the last texture unit)
        self.shader.set_int("transfer", self.max_n_color_channels)

    def _config_gl_viewport(self):
        # if volume, just make viewport the full window
        vw, vh = glfw.get_framebuffer_size(self.window)
        vx, vy = (0, 0)

        # Set GL viewport
        GL.glViewport(vx, vy, vw, vh)

        # Set on shader side
        self.shader.use()
        self.shader.set_vec2("viewportSize", (vw, vh))

    # --- Command Enqueuing Helpers ---
    
    def _request_new_volume_texture(self, shape: tuple):
        """Enqueue a command to create a new GL volume texture with the given shape."""
        
        # Define new volume shape
        self.volume_shape = shape

        # Object-space boundaries: centered on origin
        nz, ny, nx = 0.5*np.float32(shape) - 0.5
        box_min = (-nx, -ny, -nz)
        box_max = ( nx,  ny,  nz)

        # Enqueue command to create new volume texture
        def _do():
            self._ensure_gl_ready()

            # Create textures (if needed)
            if not self.volume_textures:
                self._gl_make_volume_texture(shape)
            if not self.transfer_texture:
                self._gl_make_transfer_texture()
            
            # Set shader uniforms related to volume dimensions
            self.shader.use()
            self.shader.set_vec3("boxMin", box_min)
            self.shader.set_vec3("boxMax", box_max)

            # Reset volume texture unit assignments (unecessary..? if we always assign the same units, but safe to do here after creating new textures)
            self._set_volume_texture_units()

        # Submit to the command queue
        self.cmd_q.put(_do)

    def _request_slice_upload(self, image: np.ndarray, z: int, ch: int):
        """Enqueue a command to upload a single slice (z, ch) of the volume texture."""
        
        def _do():
            self._ensure_gl_ready()
            self._gl_upload_slice_z(image, z, ch)

        # Submit to the command queue
        self.cmd_q.put(_do)

    # --- GL Texture Creation and Updating ---

    def _gl_upload_slice_z(self, slice: np.ndarray, z: int=0, ch: int=0):
        """Upload a single slice (z) of a single color channel (ch) to the volume texture."""
        
        print(f"Uploading slice z={z} for channel {ch}...")

        ny, nx = slice.shape
        tex = self.volume_textures[ch]

        GL.glBindTexture(GL.GL_TEXTURE_3D, tex)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

        # update only the data for slice (z)
        GL.glTexSubImage3D(
            GL.GL_TEXTURE_3D, 
            0,                                   # level
            0,                                   # xoffset (none)
            0,                                   # yoffset (none)
            int(z),                              # zoffset (z-slice position)
            nx,                                  # width
            ny,                                  # height
            1,                                   # depth (one slice)
            GL.GL_RED,                           # format
            GL.GL_UNSIGNED_SHORT,                # uint16
            slice.astype(np.uint16, copy=False)  # image data
        )

    def _gl_make_volume_texture(self, shape: tuple):
        """Allocate a GL 3D texture for a single color channel with the given shape."""
        
        nz, ny, nx = shape

        # First create volume_textures
        self.volume_textures = list(GL.glGenTextures(self.max_n_color_channels))

        for tex in self.volume_textures:
            # Bind tex to a texture unit and set parameters
            GL.glBindTexture(GL.GL_TEXTURE_3D, tex)
            
            GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
            GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
            GL.glTexParameteri(GL.GL_TEXTURE_3D, GL.GL_TEXTURE_WRAP_R, GL.GL_CLAMP_TO_EDGE)

            # Initialize empty R16 volume texture (single channel, 16-bit unsigned)
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
            GL.glTexImage3D(
                GL.GL_TEXTURE_3D, 
                0, 
                GL.GL_R16, 
                nx, ny, nz, 
                0, 
                GL.GL_RED, 
                GL.GL_UNSIGNED_SHORT, 
                None # input: [[[R0, G0, B0, A0], [R1, G1, B1, A1], ... ] ... ]
            )

    def _gl_make_transfer_texture(self):
        """Create transfer function texture (2D)"""
        
        # Guard against LUT is None
        if not self.luts:
            self.luts = [
                [1., 1., 1., 1.], # ch0: white
                [1., 0., 0., 1.], # ch1: red
                [0., 1., 0., 1.], # ch2: green
                [0., 0., 1., 1.]  # ch3: blue
            ]

        # RGBA 2D transfer textures with 4 lanes
        rgba = np.array(self.max_n_color_channels \
                        * [np.linspace(0, 255, 256)])[..., np.newaxis] \
                        * np.array(self.luts)[:, np.newaxis, :]
        rgba = rgba.astype(np.uint8)

        # Create transfer texture
        self.transfer_texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.transfer_texture)

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

def try_to_add_slice(viewer: GLVolumeViewBackend, image: np.ndarray, z: int, ch: int):

    data = (image, z, ch)

    try:
        viewer.data_q.put_nowait(data)
    
    except queue.Full:
        print(f"Data queue is full. Dropping slice z={z}, ch={ch}.")

        try:
            # Drain oldest slice
            viewer.data_q.get_nowait()

            # Confirm done
            viewer.data_q.task_done()
        
        except queue.Empty:
            pass

        # Try again to add slice
        try:
            viewer.data_q.put_nowait(data)
        except queue.Full:
            return

def main():
    vol_path_0 = r"d:\OPM\divya\20260324_a02_a375_488nm_egfp_561nm_mcherry\p3001\CH00_000000.tiff"
    vol_path_1 = r"d:\OPM\divya\20260324_a02_a375_488nm_egfp_561nm_mcherry\p3001\CH01_000000.tiff"

    stack = {}

    import tifffile
    with tifffile.TiffFile(vol_path_0) as tif:
        stack['0'] = tif.asarray()
    with tifffile.TiffFile(vol_path_1) as tif:
        stack['1'] = tif.asarray()
        print("Loaded volume shape:", stack['1'].shape, "dtype:", stack['1'].dtype)

    # For testing the GLVolumeViewBackend independently
    viewer = GLVolumeViewBackend()
    viewer.start(window_dim=(800, 600))
    # viewer.show_window()

    n_slices = len(stack)

    viewer.set_num_channels_and_slices(n_channels=4, n_slices=n_slices)
    viewer.set_min_max([500, 35000], ch=0) # Assuming 16-bit data; adjust as needed
    viewer.set_min_max([500, 35000], ch=1) # Assuming 16-bit data; adjust as needed

    # Simulate adding slices (replace with actual image data)
    for z in range(n_slices):
        try_to_add_slice(viewer, stack['0'][z], z, 0)

    for z in range(n_slices):
        try_to_add_slice(viewer, stack['1'][z], z, 1)

    # Keep the main thread alive (render thread handles everything)
    print("Rendering. Close window to exit.")
    try:
        viewer.thread.join()  # Wait for render thread to finish
    except KeyboardInterrupt:
        pass
    
    viewer.stop()
    print("Viewer stopped.")

if __name__ == "__main__":
    main()
     