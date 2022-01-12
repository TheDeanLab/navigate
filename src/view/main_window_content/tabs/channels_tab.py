from tkinter import *
from tkinter import ttk
from tkinter.font import Font

import numpy as np

from view.main_window_content.tabs.channels.channel_settings import channel_creator
from view.main_window_content.tabs.channels.stack_settings import stack_acq_frame
from view.main_window_content.tabs.channels.stack_cycling_settings import stack_cycling_frame
from view.main_window_content.tabs.channels.stack_timepoint_settings import stack_timepoint_frame
from view.main_window_content.tabs.channels.multipoint_settings import multipoint_frame, multipoint_list


class channels_tab(ttk.Frame):
    def __init__(self, setntbk, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(self, setntbk, *args, **kwargs)

        #Channel Settings
        #Gridding Major frames
        self.channel_main = ttk.Labelframe(self, text='Channel Settings')
        self.channel_main.grid(row=0, column=0, sticky=(NSEW), padx=10, pady=10)

        #Channel Creation
        self.channel_widgets_frame = channel_creator(self.channel_main)
        self.channel_widgets_frame.grid(row=1, column=0, columnspan=5, sticky=(NSEW), padx=10, pady=10)

        #Stack Acquisition Settings
        self.stack_acq_frame = stack_acq_frame(self)
        self.stack_acq_frame.grid(row=2, column=0, columnspan=5, sticky=(NSEW), padx=10, pady=10)

        #Stack Cycling Settings
        self.stack_cycling_frame = stack_cycling_frame(self)
        self.stack_cycling_frame.grid(row=3, column=0, columnspan=5, sticky=(NSEW), padx=10, pady=10)

        #Time Settings
        self.stack_timepoint_frame = stack_timepoint_frame(self)
        self.stack_timepoint_frame.grid(row=4, column=0, columnspan=5, sticky=(NSEW), padx=10, pady=10)

        #Multipoint Enable
        self.multipoint_frame = multipoint_frame(self)
        self.multipoint_frame.grid(row=5, column=0, columnspan=5, sticky=(NSEW), padx=10, pady=10)

        #Multipoint List
        self.multipoint_list = multipoint_list(self)
        self.multipoint_list.grid(row=6, column=0, columnspan=5, sticky=(NSEW), padx=10, pady=10)
