# Standard Imports
from tkinter import *
from tkinter import ttk
from tkinter.font import Font

# Third Party Imports
import numpy as np

# Import Sub-Frames
from view.tabs.camera_settings_tab import camera_settings_tab
from view.tabs.advanced_settings_tab import advanced_settings_tab
from view.tabs.channels_tab import channels_tab


class settings_notebook(ttk.Notebook):
    def __init__(setntbk, frame_left, session, *args, **kwargs):
        #Init notebook
        ttk.Notebook.__init__(setntbk, frame_left, *args, **kwargs)

        #Putting notebook 1 into left frame
        setntbk.grid(row=0,column=0)

        #Creating the Channels tab
        setntbk.channels_tab = channels_tab(setntbk, session)

        #Creating the Camera tab
        setntbk.camera_settings_tab = camera_settings_tab(setntbk, session)

        #Creating the advanced settings tab
        setntbk.advanced_settings_tab = advanced_settings_tab(setntbk, session)

        #Adding tabs to settings notebook
        setntbk.add(setntbk.channels_tab, text='Channels', sticky=NSEW)
        setntbk.add(setntbk.camera_settings_tab, text='Camera Settings', sticky=NSEW)
        setntbk.add(setntbk.advanced_settings_tab, text='Advanced Configuration', sticky=NSEW)






