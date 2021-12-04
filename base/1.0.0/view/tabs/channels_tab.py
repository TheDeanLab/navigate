from tkinter import *
from tkinter import ttk
from tkinter.font import Font

import numpy as np

from view.tabs.channels.channel_settings import channels_label_frame, channel_frame
from view.tabs.channels.stack_settings import stack_acq_frame
from view.tabs.channels.stack_cycling_settings import stack_cycling_frame
from view.tabs.channels.stack_timepoint_settings import stack_timepoint_frame
from view.tabs.channels.multipoint_settings import multipoint_frame, multipoint_list


class channels_tab(ttk.Frame):
    def __init__(self, setntbk, session, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(self, setntbk, *args, **kwargs)

        #Channel Settings
        #Gridding Major frames
        self.channel_main = ttk.Labelframe(self, text='Channel Settings')
        self.channel_main.grid(row=0, column=0, sticky=(NSEW))
        self.channels_label_frame = channels_label_frame(self.channel_main)

        #Each of these is an attempt to get the labels lined up
        self.channels_label_frame.grid_columnconfigure(0, weight=1)
        self.channels_label_frame.grid_columnconfigure(1, weight=1)
        self.channels_label_frame.grid_columnconfigure(2, weight=1)
        self.channels_label_frame.grid_columnconfigure(3, weight=1)
        self.channels_label_frame.grid_rowconfigure(0, weight=1)
        self.channels_label_frame.grid(row=0,column=1, columnspan=3, sticky=(NSEW))

        self.channel_1_frame = channel_frame(self.channel_main, "1", session)
        self.channel_1_frame.grid(row=1,column=0, columnspan=4, sticky=(NSEW))

        self.channel_2_frame = channel_frame(self.channel_main, "2", session)
        self.channel_2_frame.grid(row=2,column=0, columnspan=4, sticky=(NSEW))

        self.channel_3_frame = channel_frame(self.channel_main, "3", session)
        self.channel_3_frame.grid(row=3,column=0, columnspan=4, sticky=(NSEW))

        self.channel_4_frame = channel_frame(self.channel_main, "4", session)
        self.channel_4_frame.grid(row=4,column=0, columnspan=4, sticky=(NSEW))

        self.channel_5_frame = channel_frame(self.channel_main, "5", session)
        self.channel_5_frame.grid(row=5,column=0, columnspan=4, sticky=(NSEW))

        #Stack Acquisition Settings
        self.stack_acq_frame = stack_acq_frame(self)
        self.stack_acq_frame.grid(row=5, column=0, columnspan=5, sticky=(NSEW), pady=10)

        #Stack Cycling Settings
        self.stack_cycling_frame = stack_cycling_frame(self)
        self.stack_cycling_frame.grid(row=6, column=0, columnspan=5, sticky=(NSEW), pady=10)

        #Time Settings
        self.stack_timepoint_frame = stack_timepoint_frame(self)
        self.stack_timepoint_frame.grid(row=6, column=0, columnspan=5, sticky=(NSEW), pady=10)

        #Multipoint Enable
        self.multipoint_frame = multipoint_frame(self)
        self.multipoint_frame.grid(row=7, column=0, columnspan=5, sticky=(NSEW), pady=10)

        #Multipoint List
        self.multipoint_list = multipoint_list(self)
        self.multipoint_list.grid(row=8, column=0, columnspan=5, sticky=(NSEW), pady=10)
