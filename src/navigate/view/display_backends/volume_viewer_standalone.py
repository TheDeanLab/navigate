import os
import pathlib
import tifffile
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD

from navigate.view.display_backends.gl_backend import GLVolumeViewBackend
from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from navigate.view.custom_widgets.validation import ValidatedSpinbox

WINDOW_DIMENSIONS = (400, 600)

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
                input_args={"from_": 0, "to": 65535, "increment": 255, "width": 5},
                label_pos="top",
            ),
            "max": LabelInput(
                parent=self,
                label="Min:",
                input_class=ValidatedSpinbox,
                input_var=tk.IntVar(value=65535),
                input_args={"from_": 0, "to": 65535, "increment": 255, "width": 5},
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

        self.channel_widgets = {}

    def add_channel_widget(self, channel_name):
        self.channel_widgets[channel_name] = ChannelWidgetBox(self.main_frame, channel_name)
        self.channel_widgets[channel_name].pack(pady=5)

class VVStandaloneController:
    def __init__(self, view: TkinterDnD.Tk, backend: GLVolumeViewBackend):
        self.view = view
        self.backend = backend

        self.view.main_frame.drop_target_register(DND_FILES)
        self.view.main_frame.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        dropped_files = event.data.split()

        for i, file_path in enumerate(dropped_files):
            path = pathlib.Path(file_path)

            if path.suffix.lower() in ['.tif', '.tiff']:

                channel_name = path.name.split('.')[0]

                self.view.add_channel_widget(channel_name)

                def change_color():
                    print(f"Changing color for {channel_name}")

                self.view.channel_widgets[channel_name].inputs["color"].widget.configure(command=change_color)

if __name__ == "__main__":
    app = VolumeViewerStandalone()
    gl_backend = GLVolumeViewBackend()

    controller = VVStandaloneController(app, gl_backend)

    app.mainloop()