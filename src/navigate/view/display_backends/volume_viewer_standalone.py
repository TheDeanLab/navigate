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
    [255, 255, 255],
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
                input_var=tk.IntVar(value=1000),
                input_args={"from_": 0, "to": 65535, "increment": 255, "width": 8},
                label_pos="top",
            ),
            "autoscale": LabelInput(
                parent=self,
                label="AUTO",
                label_pos="top",
                input_class=tk.Button,
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

        volume_settings_frame = tk.Frame(self.main_frame, borderwidth=2, relief="sunken")

        self.inputs = {
            "shear_angle": LabelInput(
                parent=volume_settings_frame,
                label="Shear Angle",
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(value=15),
                input_args={"from_": -90.0, "to": 90.0, "increment": 0.5, "width": 5},
                label_pos="top",
            ),
            "opacity": LabelInput(
                parent=volume_settings_frame,
                label="Opacity",
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(value=0.15),
                input_args={"from_": 0.01, "to": 1.0, "increment": 0.01, "width": 5},
                label_pos="top",
            ),
            "world_step": LabelInput(
                parent=volume_settings_frame,
                label="World Step",
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(value=1.0),
                input_args={"from_": 0.05, "to": 10.0, "increment": 0.05, "width": 5},
                label_pos="top",
            )
        }

        for input_widget in self.inputs.values():
            input_widget.pack(side=tk.LEFT, expand=True)

        volume_settings_frame.pack(fill=tk.X)

        self.channels_frame = tk.Frame(self.main_frame, borderwidth=2, relief="sunken")
        self.channels_frame.pack(fill=tk.BOTH)

class ChannelController:

    def __init__(self, parent, channel_name: str, id: int=0):

        self.parent = parent

        self.id = id
        self.channel_name = channel_name

        self.view = ChannelWidgetBox(parent.view.channels_frame, channel_name)
        self.view.pack(pady=5)

        # Variables
        self.color = DEFAULT_COLORS[id]
        self.stack_data: np.ndarray = None
        self.resolution = {'dz': 1, 'px': 1}
        self.min = 0
        self.max = 3000

        # Widget command binds
        inputs = self.view.inputs

        self.min = inputs["min"].variable
        self.max = inputs["max"].variable

        self.min.trace_add("write", self.update_min_max)
        self.max.trace_add("write", self.update_min_max)

        inputs["color"].widget.configure(
            command=self.choose_color,
            bg=rgb_to_hex(self.color)
        )
        inputs["autoscale"].widget.configure(
            command=self.scale_volume_min_max
        )

    def update_min_max(self, *args):
        self._gl_update_min_max()

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

        try:
            _min = float(self.min.get())
            _max = float(self.max.get())
        except:
            return

        self.parent.backend.set_min_max([_min, _max], self.id)

    def load_stack(self, stack_path: str) -> np.ndarray:
        with tifffile.TiffFile(stack_path) as tif:
            
            # z-spacing
            try:
                image_desc = dict(eval(tif.pages[0].tags['ImageDescription'].value))
                self.resolution['dz'] = image_desc['spacing']
            except:
                self.resolution['dz'] = 1.0

            # xy-resolution
            try:
                pixels, microns = tif.pages[0].tags.get('XResolution').value
                self.resolution['px'] = microns / pixels
            except:
                self.resolution['px'] = 1.0

            print("Resolution:", self.resolution)

            # load the data
            self.stack_data = tif.asarray()

    def choose_color(self):

        rgb, hex = colorchooser.askcolor(title=f"Select {self.channel_name} color...")

        self.color = list(rgb)
        self.view.inputs["color"].widget.configure(bg=hex)

        # Update on GL side
        self._gl_update_color()

    def scale_volume_min_max(self):

        self.min.set(int(self.stack_data.min()))
        self.max.set(int(self.stack_data.max()))

        self._gl_update_min_max()

class VVStandaloneController:
    def __init__(self, view: TkinterDnD.Tk, backend: GLVolumeViewBackend):
        self.view = view
        self.backend = backend

        self.view.main_frame.drop_target_register(DND_FILES)
        self.view.main_frame.dnd_bind('<<Drop>>', self.on_drop)

        # trace adds for inputs
        # Trace adds for volume display widgets
        def volume_setting_callback(field):
            return lambda *args: self._gl_on_volume_settings_changed(field, *args)

        for key, widget in self.view.inputs.items():
            widget.get_variable().trace_add("write", volume_setting_callback(key))

        # dict: holds Channels objects
        self.channels = {}

    def _gl_on_volume_settings_changed(self, field, *args):
        """Hook for OpenGL-based views to trigger a re-render when display settings are changed."""

        variable = self.view.inputs[field].get_variable()

        try:
            value = float(variable.get())
        except:
            # Handle "" and other such invalid inputs
            return
        
        exec(f"self.backend.set_{field}({value})")

    def on_drop(self, event):
        dropped_files = event.data.split()
        dropped_files.sort()

        # Reset if running
        if self.backend.thread_is_running():
            self.backend.stop()

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
        
        # Reinitialize shader uniforms on-load
        for key in self.view.inputs:
            self._gl_on_volume_settings_changed(key)

if __name__ == "__main__":
    app = VolumeViewerStandalone()
    gl_backend = GLVolumeViewBackend()

    controller = VVStandaloneController(app, gl_backend)

    app.mainloop()

    # Close behaviour
    if gl_backend.thread_is_running():
        gl_backend.stop()