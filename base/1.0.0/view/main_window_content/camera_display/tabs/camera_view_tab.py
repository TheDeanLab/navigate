from tkinter import *
from tkinter import ttk
from tkinter.font import Font
from view.main_window_content.camera_display.camera_view.cam_counts import cam_counts

class camera_tab(ttk.Frame):
    def __init__(self, cam_wave, *args, **kwargs):
        #TODO: WOuld like to split this Frame in half and provide some statistics on the right-hand side.
        # Would include a Combobox for changing the CMAP.
        # Would include a Spinbox for providing the maximum intensity of the image.
        # Would include a Spinbox for providing a rolling average maximum intensity of the image
        # Would include a Spinbox for providing the number of frames to include in the rolling average.
        #Init Frame
        ttk.Frame.__init__(self, cam_wave, *args, **kwargs)

        # #Frame that will hold camera image
        # self.cam_image = ttk.Frame(self)
        # self.cam_image.grid(row=0, column=0, sticky=(NSEW))

        # #Frame for camera selection and counts
        # self.cam_counts = ttk.Frame(self)
        # self.cam_counts.grid(row=0, column=1, sticky=(NSEW))

        # #Frame for scale settings/pallete color
        # self.scale_pallete = ttk.Frame(self)
        # self.scale_pallete.grid(row=0, column=2, sticky=(NSEW))