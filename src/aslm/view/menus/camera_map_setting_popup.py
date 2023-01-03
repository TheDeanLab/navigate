import tkinter as tk
from tkinter import ttk

from aslm.view.custom_widgets.popup import PopUp
from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from aslm.view.custom_widgets.validation import ValidatedSpinbox

from matplotlib.pyplot import subplots
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class CameraMapSettingPopup(PopUp):
    """Popup to create and visualize camera offset and variance map generation."""

    def __init__(
        self,
        root,
        name="Camera Map Settings",
        size="+320+180",
        top=True,
        transient=True,
        *args,
        **kwargs
    ):
        super().__init__(root, name, size, top, transient, *args, **kwargs)

        self.inputs = {}

        title = ttk.Label(self.content_frame, text="File: ", padding=(2, 5, 0, 0))
        title.grid(row=0, column=0, sticky=(tk.NSEW))
        self.file_name = tk.StringVar()
        self.inputs["file_name"] = tk.Entry(
            self.content_frame, textvariable=self.file_name
        )
        self.inputs["file_name"].grid(
            row=0, column=1, sticky=tk.NSEW, padx=(0, 5), pady=(15, 0)
        )

        self.open_btn = ttk.Button(self.content_frame, text="Open")
        self.open_btn.grid(row=0, column=2, pady=(0, 10))

        title = ttk.Label(self.content_frame, text="Camera: ", padding=(2, 5, 0, 0))
        self.camera = tk.StringVar()
        title.grid(row=0, column=3, sticky=(tk.NSEW))
        self.inputs["camera"] = ttk.OptionMenu(self.content_frame, self.camera)
        self.inputs["camera"].grid(
            row=0, column=4, sticky=tk.NSEW, padx=(0, 5), pady=(15, 0)
        )

        self.map_btn = ttk.Button(self.content_frame, text="Create maps")
        self.map_btn.grid(row=0, column=5, pady=(0, 10))

        # Plot
        self.fig, self.axs = subplots(1, 2, figsize=(5, 5))
        canvas = FigureCanvasTkAgg(self.fig, master=self.content_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(
            row=1, column=0, columnspan=6, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5)
        )

    def get_widgets(self):
        return self.inputs
