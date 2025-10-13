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
from navigate.model.concurrency.concurrency_tools import ObjectInSubprocess, SharedNDArray

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
    
    def _on_minmax_changed(self, *args):

        min_counts = self.image_palette["Min"].get()
        max_counts = self.image_palette["Max"].get()

        try:
            assert isinstance(min_counts, int)
            assert isinstance(max_counts, int)
        except AssertionError:
            return

        # send update commands to viewer queue
        if not self.autoscale.get():
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
        self.width        = None
        self.height       = None
        self.min_max      = None
        self.do_autoscale = True
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
        if stall_ms > 15:
            print(f"Swap stall: {stall_ms:.2f} ms")

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

    import os
    from navigate.model.concurrency.concurrency_tools import ObjectInSubprocess, SharedNDArray
    from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput
    import tkinter as tk

    root = tk.Tk()
    root.geometry("400x300")

    viewer = ObjectInSubprocess(GLFrameViewer)

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
            viewer.update_image(frame)
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
            viewer.update_image(snd)
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
            viewer.update_image(frame)
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
            viewer.update_image(frame)
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
                viewer.update_image(frame)
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
                viewer.update_image(frame)
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
        bench_size_sweep(viewer, sizes=((512,512),(1024,1024),(1536,1536)), per_size_seconds=1.0)
        bench_producer_rate(viewer, shape=(1024,1024), target_fps=120, seconds=3.0)

        print("\n[Done] You can close the window or leave it running.")

    # -----------------------

    tk.Button(root, text="RUN TESTS", command=run_tests).pack()

    root.mainloop()
