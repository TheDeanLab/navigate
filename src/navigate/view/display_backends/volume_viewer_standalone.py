import os
import pathlib
import tifffile
import numpy as np

import tkinter as tk
from tkinter import colorchooser

from tkinterdnd2 import DND_FILES, TkinterDnD

from navigate.view.display_backends.gl_backend import GLVolumeViewBackend
from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from navigate.view.custom_widgets.validation import ValidatedSpinbox

WINDOW_DIMENSIONS = (400, 600)

DEFAULT_COLORS = [
    [255,   0,   0],
    [  0, 255,   0],
    [  0,   0, 255],
    [255, 255,   0],
    [255,   0, 255],
    [  0, 255, 255],
]

def rgb_to_hex(color: list):
    r, g, b = color
    return f'#{r:02x}{g:02x}{b:02x}'

class ChannelWidgetBox(tk.Frame):
    def __init__(self, master, channel_name):
        super().__init__(master)

        self.channel_name = channel_name
        self.label = tk.Label(self, text=channel_name, wraplength=WINDOW_DIMENSIONS[0]-20, justify=tk.LEFT)
        self.label.pack()

        widget_frame = tk.Frame(self)

        self.inputs = {
            "color": LabelInput(
                widget_frame, 
                label_pos="top",
                label="Color:",
                input_class=tk.Button
                ),
            "min": LabelInput(
                parent=self,
                label="Min:",
                input_class=ValidatedSpinbox,
                input_var=tk.IntVar(value=0),
                input_args={"from_": 0, "to": 65535, "increment": 255, "width": 8},
                label_pos="top",
            ),
            "max": LabelInput(
                parent=self,
                label="Min:",
                input_class=ValidatedSpinbox,
                input_var=tk.IntVar(value=65535),
                input_args={"from_": 0, "to": 65535, "increment": 255, "width": 8},
                label_pos="top",
            ),
        }

        for input_widget in self.inputs.values():
            input_widget.pack(padx=5, side=tk.LEFT)

        widget_frame.pack()

class VolumeViewerStandalone(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        self.title("Volume Viewer Standalone")
        self.geometry(f"{WINDOW_DIMENSIONS[0]}x{WINDOW_DIMENSIONS[1]}")

        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

class ChannelController:

    def __init__(self, parent, channel_name: str, id: int=0):

        self.parent = parent

        self.id = id
        self.channel_name = channel_name

        self.view = ChannelWidgetBox(parent.view.main_frame, channel_name)
        self.view.pack(pady=5)

        # Variables
        self.color = DEFAULT_COLORS[id]
        self.stack_data: np.ndarray = None
        self.resolution = {'dz': 1, 'px': 1}
        self.min = 0
        self.max = 3000

        # Widget command binds
        inputs = self.view.inputs

        inputs["color"].widget.configure(
            command=self.choose_color,
            bg=rgb_to_hex(self.color)
        )

    def _gl_upload_stack_to_backend(self):

        self.parent.backend.set_num_slices_and_dz(
            len(self.stack_data), self.resolution['dz']
            )

        self._gl_update_color()
        self._gl_update_min_max()

        for z, img in enumerate(self.stack_data):
            self.parent.backend.data_q.put_nowait((img, z, self.id))

    def _gl_update_color(self):

        self.parent.backend.request_set_channel_color(
            self.id,
            [float(c)/255. for c in self.color] + [0.5] # alpha = 1 for now
            )

    def _gl_update_min_max(self):

        self.parent.backend.set_min_max(
            [self.min, self.max],
            self.id
        )

    def load_stack(self, stack_path: str) -> np.ndarray:
        with tifffile.TiffFile(stack_path) as tif:
            
            # z-spacing
            image_desc = dict(eval(tif.pages[0].tags['ImageDescription'].value))
            self.resolution['dz'] = image_desc['spacing']
            
            # xy-resolution
            pixels, microns = tif.pages[0].tags.get('XResolution').value
            self.resolution['px'] = microns / pixels
        
            # load the data
            self.stack_data = tif.asarray()

    def choose_color(self):

        rgb, hex = colorchooser.askcolor(title=f"Select {self.channel_name} color...")

        self.color = list(rgb)
        self.view.inputs["color"].widget.configure(bg=hex)

        # Update on GL side
        self._gl_update_color()

class VVStandaloneController:
    def __init__(self, view: TkinterDnD.Tk, backend: GLVolumeViewBackend):
        self.view = view
        self.backend = backend

        self.view.main_frame.drop_target_register(DND_FILES)
        self.view.main_frame.dnd_bind('<<Drop>>', self.on_drop)

        self.channels = {}

    def on_drop(self, event):
        dropped_files = event.data.split()

        # Start GL backend
        self.backend.start()

        for i, file_path in enumerate(dropped_files):
            path = pathlib.Path(file_path)

            if path.suffix.lower() in ['.tif', '.tiff']:

                channel_name = path.name.split('.')[0]

                # Create a channel for this stack
                self.channels[channel_name] = ChannelController(self, channel_name, i)

                # Load the stack data/metadata into memory
                self.channels[channel_name].load_stack(file_path)

                # Queue a stack upload for this channel
                self.view.after(100, self.channels[channel_name]._gl_upload_stack_to_backend)

if __name__ == "__main__":
    app = VolumeViewerStandalone()
    gl_backend = GLVolumeViewBackend()

    controller = VVStandaloneController(app, gl_backend)

    app.mainloop()

    # Close behaviour
    if gl_backend.thread_is_running():
        gl_backend.stop()