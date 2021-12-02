from tkinter import *
from tkinter import ttk
from tkinter.font import Font

import numpy as np

# Import Sub-Frames
from view.settings_subframes.channel_settings import channels_label_frame, channel_frame
from view.settings_subframes.stack_settings import stack_acq_frame
from view.settings_subframes.stack_cycling_settings import stack_cycling_frame
from view.settings_subframes.stack_timepoint_settings import stack_timepoint_frame
from view.settings_subframes.multipoint_settings import multipoint_frame, multipoint_list

class settings_notebook(ttk.Notebook):
    def __init__(setntbk, frame_left, session, *args, **kwargs):
        #Init notebook
        ttk.Notebook.__init__(setntbk, frame_left, *args, **kwargs)

        #Putting notebook 1 into left frame
        setntbk.grid(row=0,column=0)

        #Creating the settings tab
        setntbk.settings_tab = settings_tab(setntbk, session)

        #Creating the advanced settings tab
        setntbk.adv_settings_tab = adv_settings_tab(setntbk)

        #Adding tabs to settings notebook
        setntbk.add(setntbk.settings_tab, text='Settings', sticky=NSEW)
        setntbk.add(setntbk.adv_settings_tab, text='Advanced Settings', sticky=NSEW)

class settings_tab(ttk.Frame):
    def __init__(settings, setntbk, session, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(settings, setntbk, *args, **kwargs)

        #Channel Settings
        #Gridding Major frames
        settings.channel_main = ttk.Labelframe(settings, text='Channel Settings')
        settings.channel_main.grid(row=0, column=0, sticky=(NSEW))
        settings.channels_label_frame = channels_label_frame(settings.channel_main)

        #Each of these is an attempt to get the labels lined up
        settings.channels_label_frame.grid_columnconfigure(0, weight=1)
        settings.channels_label_frame.grid_columnconfigure(1, weight=1)
        settings.channels_label_frame.grid_columnconfigure(2, weight=1)
        settings.channels_label_frame.grid_columnconfigure(3, weight=1)
        settings.channels_label_frame.grid_rowconfigure(0, weight=1)
        settings.channels_label_frame.grid(row=0,column=1, columnspan=3, sticky=(NSEW))

        settings.channel_1_frame = channel_frame(settings.channel_main, "1", session)
        settings.channel_1_frame.grid(row=1,column=0, columnspan=4, sticky=(NSEW))

        settings.channel_2_frame = channel_frame(settings.channel_main, "2", session)
        settings.channel_2_frame.grid(row=2,column=0, columnspan=4, sticky=(NSEW))

        settings.channel_3_frame = channel_frame(settings.channel_main, "3", session)
        settings.channel_3_frame.grid(row=3,column=0, columnspan=4, sticky=(NSEW))

        settings.channel_4_frame = channel_frame(settings.channel_main, "4", session)
        settings.channel_4_frame.grid(row=4,column=0, columnspan=4, sticky=(NSEW))

        settings.channel_5_frame = channel_frame(settings.channel_main, "5", session)
        settings.channel_5_frame.grid(row=5,column=0, columnspan=4, sticky=(NSEW))

        #Stack Acquisition Settings
        settings.stack_acq_frame = stack_acq_frame(settings)
        settings.stack_acq_frame.grid(row=5, column=0, columnspan=5, sticky=(NSEW), pady=10)

        #Stack Cycling Settings
        settings.stack_cycling_frame = stack_cycling_frame(settings)
        settings.stack_cycling_frame.grid(row=6, column=0, columnspan=5, sticky=(NSEW), pady=10)

        #Time Settings
        settings.stack_timepoint_frame = stack_timepoint_frame(settings)
        settings.stack_timepoint_frame.grid(row=6, column=0, columnspan=5, sticky=(NSEW), pady=10)

        #Multipoint Enable
        settings.multipoint_frame = multipoint_frame(settings)
        settings.multipoint_frame.grid(row=7, column=0, columnspan=5, sticky=(NSEW), pady=10)

        #Multipoint List
        settings.multipoint_list = multipoint_list(settings)
        settings.multipoint_list.grid(row=8, column=0, columnspan=5, sticky=(NSEW), pady=10)

class adv_settings_tab(ttk.Frame):
    def __init__(adv_settings, setntbk, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(adv_settings, setntbk, *args, **kwargs)
