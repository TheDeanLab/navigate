#Adds the contents of the camera selection/counts frame
from tkinter import *
from tkinter import ttk
import tkinter as tk

from view.custom_widgets.LabelInputWidgetFactory import LabelInput


class cam_counts(ttk.Frame):
    def __init__(self, cam_view, *args, **kwargs):
        ttk.Frame.__init__(self, cam_view, *args, **kwargs)
        text_label = 'Image Metrics'
        ttk.Labelframe.__init__(self, cam_view, text=text_label, *args, **kwargs)
        self.metrics = ttk.Frame(self)
        self.metrics.grid(row=0, column=0, sticky=NSEW)

        #  Max Counts Entry
        self.count = DoubleVar()
        self.count.set(0)
        self.count_entry_frame = ttk.Frame(self)
        self.count_entry = ttk.Entry(self.count_entry_frame, textvariable=self.count, width=15)
        self.count_entry_label = ttk.Label(self.count_entry_frame, text="Image Max Counts")
        self.count_entry_label.grid(row=0, column=2, sticky="s")
        self.count_entry.grid(row=0, column=3, sticky="n")
        self.count_entry_frame.grid(row=0, column=3, sticky=NSEW)

        #  Frames to Avg spinbox
        self.avg_frame = IntVar()
        self.avg_frame.set(1)
        self.avg_frame_holder = ttk.Frame(self)
        self.avg_frame_label = ttk.Label(self.avg_frame_holder, text="Frames to Avg")
        self.avg_frame_spinbox = ttk.Spinbox(self.avg_frame_holder, from_=1, to=20, textvariable=self.avg_frame,
                                             increment=1, width=9)
        self.avg_frame_label.grid(row=0, column=0, sticky=NSEW)
        self.avg_frame_spinbox.grid(row=0, column=1, sticky=NSEW)
        self.avg_frame_holder.grid(row=0, column=1, sticky=NSEW)

        #  Channel Entry
        self.channel_idx = IntVar()
        self.channel_idx.set(0)
        self.channel_entry_frame = ttk.Frame(self)
        self.channel_entry = ttk.Entry(self.count_entry_frame, textvariable=self.channel_idx, width=15)
        self.channel_entry_label = ttk.Label(self.count_entry_frame, text="Channel")
        self.channel_entry_label.grid(row=0, column=4, sticky="s")
        self.channel_entry.grid(row=0, column=5, sticky="n")
        self.channel_entry_frame.grid(row=0, column=5, sticky=NSEW)

        #Stack Max entry
        # self.stack = DoubleVar()
        # self.stack_frame = ttk.Frame(self)
        # self.stack_entry = ttk.Entry(self.stack_frame, textvariable=self.stack, width=15)
        # self.stack_entry_label = ttk.Label(self.stack_frame, text="Stack Max")
        # self.stack_entry_label.grid(row=0, column=0, sticky="s")
        # self.stack_entry.grid(row=0, column=1, sticky="n")
        # self.stack_frame.grid(row=0, column=1, sticky=NSEW)
