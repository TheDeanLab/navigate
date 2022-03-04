import tkinter as tk
from tkinter import *
from tkinter import ttk
from view.main_window_content.camera_display.camera_view.tabs.cam_counts import cam_counts
from view.main_window_content.camera_display.camera_view.tabs.pallete import pallete
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class camera_tab(ttk.Frame):
    def __init__(self, cam_wave, *args, **kwargs):
        #  TODO: Would like to split this Frame in half and provide some statistics on the right-hand side.
        #  Would include a Combobox for changing the CMAP.
        #  Would include a Spinbox for providing the maximum intensity of the image.
        #  Would include a Spinbox for providing a rolling average maximum intensity of the image
        #  Would include a Spinbox for providing the number of frames to include in the rolling average.
        #  Init Frame
        ttk.Frame.__init__(self, cam_wave, *args, **kwargs)

        #  Frame that will hold camera image
        self.cam_image = ttk.Frame(self)
        self.cam_image.grid(row=0, column=0, sticky=NSEW)

        self.canvas = tk.Canvas(self.cam_image, width=800, height=800)
        self.canvas.grid(row=0, column=0, sticky=NSEW)
        self.matplotlib_figure = Figure(figsize=[6, 6], tight_layout=True)
        self.matplotlib_canvas = FigureCanvasTkAgg(self.matplotlib_figure, self.canvas)

        #  Frame for camera selection and counts
        self.cam_counts = cam_counts(self)
        self.cam_counts.grid(row=1, column=0, sticky=NSEW)

        #  Frame for scale settings/pallete color
        self.scale_pallete = pallete(self)
        self.scale_pallete.grid(row=0, column=1, sticky=NSEW)
