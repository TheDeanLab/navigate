import os
import tifffile
import numpy as np
import tkinter as tk

from navigate.view.display_backends.gl_backend import GLVolumeViewBackend

class TestWidget(tk.Frame):
    def __init__(self, master=None):
        super().__init__(
            master=tk.Tk() if master is None else master,
            width=400,
            height=400
            )
        
        self.pack()

if __name__ == "__main__":

    """Run this __main__ to test the GLVolumeViewBackend!"""
    app = TestWidget()
    
    gl_backend = GLVolumeViewBackend()
    gl_backend.start()

    def load_stack(stack_path: str) -> np.ndarray:
        with tifffile.TiffFile(stack_path) as tif:
            return tif.asarray()

    def load_from_directory():
        import glob
        from tkinter import filedialog

        dir_path = filedialog.askdirectory(title="Directory containing stacks:")
        if not dir_path:
            raise FileNotFoundError

        file_list = glob.glob(os.path.join(dir_path, "*.tif*"))

        stacks = {}
        for i, f in enumerate(file_list):
            stacks[f"CH{i}"] = load_stack(f)

        return stacks

    try:
        stacks = load_from_directory()
    except FileNotFoundError:
        print("Couldn't find stacks! Using noise.")
        stacks = {
            ch: np.random.randint(0, 65535, (100, 64, 128), dtype=np.uint16)
            for ch in ["CH0", "CH1"]
            }    

    def upload_stack(stack: np.ndarray, ch: int=0, downsample_factor: int=2):
        if downsample_factor > 1:
            stack = stack[::downsample_factor, ::downsample_factor, ::downsample_factor]
        
        min_pix, max_pix = np.min(stack), np.max(stack)
        gl_backend.set_min_max([min_pix, max_pix/4], ch=ch)

        gl_backend.set_num_slices(n_slices=len(stack))

        for z, image in enumerate(stack):
            gl_backend.data_q.put_nowait((image, z, ch))
            
    app.after(100, lambda: gl_backend.request_set_channel_color(0, [1., 0., 1., 0.5]))
    app.after(100, lambda: upload_stack(stacks["CH0"], ch=0))
    # app.after(100, lambda: upload_stack(stacks["CH1"], ch=1))
    
    # app.after(100, lambda: gl_backend.request_set_channel_color(1, [0., 1., 1., 0.5]))
    
    app.mainloop()