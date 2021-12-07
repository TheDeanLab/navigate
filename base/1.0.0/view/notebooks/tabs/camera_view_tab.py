from tkinter import *
from tkinter import ttk
from tkinter.font import Font
import numpy as np

from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from model.camera.SyntheticCamera import Camera as camera


class camera_tab(ttk.Frame):
    def __init__(camera_tab, cam_wave, *args, **kwargs):
        #TODO: WOuld like to split this Frame in half and provide some statistics on the right-hand side.
        # Would include a Combobox for changing the CMAP.
        # Would include a Spinbox for providing the maximum intensity of the image.
        # Would include a Spinbox for providing a rolling average maximum intensity of the image
        # Would include a Spinbox for providing the number of frames to include in the rolling average.
        #Init Frame
        ttk.Frame.__init__(camera_tab, cam_wave, *args, **kwargs)

        # the figure that will contain the plot
        fig = Figure(figsize=(4, 4), dpi=100)

        # Generate Waveform
        synthetic_image = camera.read_camera(camera)

        # adding the subplot
        plot1 = fig.add_subplot(111)
        plot1.axis('off')

        # add the image
        #TODO: Handle the synthetic and real images.
        plot1.imshow(synthetic_image, cmap='gray')

        # creating the Tkinter canvas containing the Matplotlib figure
        canvas = FigureCanvasTkAgg(fig, master=camera_tab)
        canvas.draw()

        # placing the canvas on the Tkinter window
        canvas.get_tk_widget().pack()

        #Need to add image code here, using a label to hold the image.
        #image_viewer = ttk.Label(camera_tab)
        #image_viewer.grid(row=0, column=0, sticky=NSEW)