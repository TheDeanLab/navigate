from tkinter import *
from tkinter import ttk
from tkinter.font import Font

import numpy as np
from view.main_window_content.camera_display.camera_settings.tabs.camera_mode import camera_mode
from view.main_window_content.camera_display.camera_settings.tabs.framerate_info import framerate_info
from view.main_window_content.camera_display.camera_settings.tabs.camera_roi import camera_roi


class camera_settings_tab(ttk.Frame):
    '''
    # This class holds and controls the layout of the major label frames for the camera settings tab in the settings notebook. Any imported classes are children that makeup
    # the content of the major frames. If you need to adjust anything in the frames follow the children.
    '''
    def __init__(self, setntbk, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(self, setntbk, *args, **kwargs)

        #Camera Modes Frame
        self.camera_mode_frame = camera_mode(self)
        self.camera_mode_frame.grid(row=0, column=0, sticky=(NSEW), padx=10, pady=10)
        
        #Framerate Label Frame
        self.framerate_info_frame = framerate_info(self)
        self.framerate_info_frame.grid(row=0, column=1, sticky=(NSEW), padx=10, pady=10)

        #Region of Interest Settings
        self.camera_roi_frame = camera_roi(self)
        self.camera_roi_frame.grid(row=1, column=0,columnspan=2, sticky=(NSEW), padx=10, pady=10)


