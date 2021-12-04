from tkinter import *
from tkinter import ttk
from tkinter.font import Font

import numpy as np
from view.tabs.camera_settings.camera_roi import camera_roi_frame, camera_roi_label_frame

class camera_settings_tab(ttk.Frame):
    def __init__(self, setntbk, session, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(self, setntbk, *args, **kwargs)

        #Camera ROI Settings
        self.camera_roi_label = ttk.Labelframe(self, text='Camera Settings')
        self.camera_roi_label.grid(row=0, column=0, sticky=(NSEW))
        self.camera_roi_label_frame = camera_roi_label_frame(self.camera_roi_label)
        self.camera_roi_label_frame.grid(row=0, column=1, columnspan=3, sticky=(NSEW))

        #Stack Cycling Settings
        self.roi_frame = camera_roi_frame(self)
        self.roi_frame.grid(row=1, column=0, columnspan=5, sticky=(NSEW), pady=10)