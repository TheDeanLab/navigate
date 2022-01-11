from tkinter import *
from tkinter import ttk
from tkinter.font import Font
import numpy as np

class camera_mode_frame(ttk.Frame):
    def __init__(self, cam_settings, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(self, cam_settings, *args, **kwargs)

        # Creating Dropdowns
        cam_settings.laser_options = StringVar()
        cam_settings.laser_pull_down = ttk.Combobox(cam_settings)
        cam_settings.laser_pull_down['values'] = ['Normal Mode', 'Light-Sheet Mode']
        cam_settings.laser_pull_down.current(0)
        cam_settings.laser_pull_down.grid(row=0, column=1, sticky=(NSEW))
        #TODO: Have it save the parameters to session.


class camera_roi_label_frame(ttk.Frame):
    def __init__(self, settings_tab, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(self, settings_tab, *args, **kwargs)

        #Adding Labels to frame
        self.laser_label = ttk.Label(self, text='Camera ROI')
        self.laser_label.grid(row=0, column=0, sticky=(NSEW))

class camera_mode_label_frame(ttk.Frame):
    def __init__(self, settings_tab, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(self, settings_tab, *args, **kwargs)

        #Adding Labels to frame
        self.laser_label = ttk.Label(self, text='Camera Readout Mode')
        self.laser_label.grid(row=0, column=0, sticky=(NSEW))
