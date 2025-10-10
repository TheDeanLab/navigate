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

const int BIT_DEPTH = 65535;

uniform sampler2D pixels;
uniform vec2 viewportSize;
uniform vec2 colorMinMax = vec2(0, 65535);

void main()
{
    vec2 uv = gl_FragCoord.xy / viewportSize;
    uv.y = 1.0 - uv.y;
    
    float s = texture(pixels, uv).r;
    
    float sMin = float(colorMinMax.x) / BIT_DEPTH;
    float sMax = float(colorMinMax.y) / BIT_DEPTH;

    s = clamp(s, sMin, sMax);
    s = (s - sMin) / (sMax - sMin);

    FragColor = vec4(s, s, s, 1.0);
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
        self.width   = None
        self.height  = None
        self.min_max = None
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

            # bind sampler unit
            self.shader.use()
            self.shader.set_int('pixels', 0) # GL_TEXTURE0

            # --------- MAIN LOOP ---------
            while self.is_running.is_set() and not glfw.window_should_close(self.window):

                for _ in range(10):
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

    def update_texture(self, data : np.ndarray):
        """
            Update 2D texture pixels with new data.
        """
        # uint16 and C-contiguous
        if not data.flags['C_CONTIGUOUS']:
            data = np.ascontiguousarray(data)
        if data.dtype != np.uint16:
            data = data.astype(np.uint16)
        
        ny, nx = data.shape

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
            data
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

    # ----- update functions -----

    def set_min_max(self, min_max: list):
        self.min_max = min_max

        def _do():
            self._ensure_gl_ready()
            self.shader.use()
            self.shader.set_vec2('colorMinMax', min_max)

        self.cmd_queue.put(_do)

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

    viewer = ObjectInSubprocess(GLFrameViewer)

    def launch():
        viewer.start_render_loop((800, 800), "Camera Viewer")

    # import time
    # def play():
    #     for t, vol in enumerate(frames):
    #         print("Frame:", t)
    #         n_slices = len(vol)
    #         for z in range(n_slices):
    #             viewer.update_image(vol[z])

    def play():
        viewer.update_image(frames[0].max(0))

    def stop():
        viewer.stop_render_loop()

    experiment = {
        'cMin': 0,
        'cMax': 65535,
    }

    cMin = tk.IntVar(root, value=experiment['cMin'])
    cMax = tk.IntVar(root, value=experiment['cMax'])
    def c_change():
        viewer.set_min_max([cMin.get(), cMax.get()])

    settings = tk.LabelFrame(root, text="Settings").pack()

    LabelInput(
        settings, label_pos="left", label="cMin",
        input_class=ttk.Spinbox, input_var=cMin,
        input_args={
            "from_": 0, 
            "to": 65535, 
            "increment": 85,
            "command": c_change
            }
        ).pack()

    LabelInput(
        settings, label_pos="left", label="cMax",
        input_class=ttk.Spinbox, input_var=cMax,
        input_args={
            "from_": 0, 
            "to": 65535, 
            "increment": 85,
            "command": c_change
            }
        ).pack()

    tk.Button(root, text="LAUNCH", command=launch).pack()
    tk.Button(root, text="STOP", command=stop).pack()
    tk.Button(root, text="PLAY", command=play).pack()

    launch()

    root.mainloop()
