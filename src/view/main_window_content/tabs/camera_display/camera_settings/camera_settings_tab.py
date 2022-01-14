from tkinter import *
from tkinter import ttk
from tkinter.font import Font

import numpy as np
from view.main_window_content.tabs.camera_display.camera_settings.camera_mode import camera_mode
from view.main_window_content.tabs.camera_display.camera_settings.framerate_info import framerate_info


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

        


