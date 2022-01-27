import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter.font import Font
from view.main_window_content.camera_display.camera_view.tabs.cam_counts import cam_counts
from view.main_window_content.camera_display.camera_view.tabs.pallete import pallete
import numpy as np
from PIL import Image, ImageTk


class camera_tab(ttk.Frame):
    def __init__(self, cam_wave, *args, **kwargs):
        #TODO: WOuld like to split this Frame in half and provide some statistics on the right-hand side.
        # Would include a Combobox for changing the CMAP.
        # Would include a Spinbox for providing the maximum intensity of the image.
        # Would include a Spinbox for providing a rolling average maximum intensity of the image
        # Would include a Spinbox for providing the number of frames to include in the rolling average.
        #Init Frame
        ttk.Frame.__init__(self, cam_wave, *args, **kwargs)

        #Frame that will hold camera image
        self.cam_image = ttk.Frame(self)
        self.cam_image.grid(row=0, column=0, sticky=(NSEW))
        self.canvas = tk.Canvas(self.cam_image, width=700, height=700)
        self.canvas.grid(row=0, column=0, sticky=(NSEW))

        #Putting starting image into canvas, change the number before the * to make it one color. ex 255 = white 
        #https://stackoverflow.com/questions/10465747/how-to-create-a-white-image-in-python
        self.image = ImageTk.PhotoImage(Image.fromarray(0 * np.ones((1000,1000,3), np.uint8))) # the numbers in the np.ones need to be at least as big as the canvas, othewise it will be too small
        self.canvas.create_image(0, 0, image=self.image, anchor='nw') # creates image and anchors to top left starting at 0,0


        #Frame for camera selection and counts
        self.cam_counts = cam_counts(self)
        self.cam_counts.grid(row=0, column=1, sticky=(NSEW))

        #Frame for scale settings/pallete color
        self.scale_pallete = pallete(self)
        self.scale_pallete.grid(row=0, column=2, sticky=(NSEW))
