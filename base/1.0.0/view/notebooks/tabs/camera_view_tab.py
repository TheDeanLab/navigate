from tkinter import *
from tkinter import ttk
from tkinter.font import Font


class camera_tab(ttk.Frame):
    def __init__(camera_tab, cam_wave, *args, **kwargs):
        #TODO: WOuld like to split this Frame in half and provide some statistics on the right-hand side.
        # Would include a Combobox for changing the CMAP.
        # Would include a Spinbox for providing the maximum intensity of the image.
        # Would include a Spinbox for providing a rolling average maximum intensity of the image
        # Would include a Spinbox for providing the number of frames to include in the rolling average.
        #Init Frame
        ttk.Frame.__init__(camera_tab, cam_wave, *args, **kwargs)
