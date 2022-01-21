from tkinter import *
from tkinter import ttk
from tkinter.font import Font
import numpy as np

# Local imports
#from view.notebooks.acquire_bar_frame.acquire_bar import AcquireBar

"""
  settings.channels_label_frame = channels_label_frame(settings.channel_main)
# Create a label frame.

        #Each of these is an attempt to get the labels lined up
        settings.channels_label_frame.grid_columnconfigure(0, weight=1)
        settings.channels_label_frame.grid_columnconfigure(1, weight=1)
        settings.channels_label_frame.grid_columnconfigure(2, weight=1)
        settings.channels_label_frame.grid_columnconfigure(3, weight=1)
        settings.channels_label_frame.grid_rowconfigure(0, weight=1)
        settings.channels_label_frame.grid(row=0,column=1, columnspan=3, sticky=(NSEW))

        settings.channel_1_frame = channel_frame(settings.channel_main, "1")
        settings.channel_1_frame.grid(row=1,column=0, columnspan=4, sticky=(NSEW))
        """

class stack_timepoint_frame(ttk.Frame):
    def __init__(stack_timepoint_label_frame, settings_tab, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(stack_timepoint_label_frame, settings_tab, *args, **kwargs)

        text_label = 'Timepoint Settings'
        ttk.Labelframe.__init__(stack_timepoint_label_frame, settings_tab, text=text_label, *args, **kwargs)

        #Save Data Label
        label_position = 0
        input_position = 4
        stack_timepoint_label_frame.laser_label = ttk.Label(stack_timepoint_label_frame, text='Save Data')
        stack_timepoint_label_frame.laser_label.grid(row=0, column=label_position, sticky=(NSEW))

        #Save Data Checkbox
        stack_timepoint_label_frame.save_data = BooleanVar()
        stack_timepoint_label_frame.save_data.set(False)
        stack_timepoint_label_frame.save_check = ttk.Checkbutton(stack_timepoint_label_frame, text='', variable=stack_timepoint_label_frame.save_data)
        stack_timepoint_label_frame.save_check.grid(row=0, column=input_position, sticky=(NSEW))


        # Timepoints Label, spinbox defaults to 1.
        stack_timepoint_label_frame.filterwheel_label = ttk.Label(stack_timepoint_label_frame, text='Timepoints')
        stack_timepoint_label_frame.filterwheel_label.grid(row=1, column=label_position, sticky=(NSEW))
        stack_timepoint_label_frame.exp_time_spinval = IntVar()
        stack_timepoint_label_frame.exp_time_spinbox = ttk.Spinbox(
            stack_timepoint_label_frame, from_=0, to=5000, textvariable=stack_timepoint_label_frame.exp_time_spinval,
            increment=1,
            width=9)
        stack_timepoint_label_frame.exp_time_spinbox.grid(row=1, column=input_position, sticky=(NSEW))

        #Stack Acq. Time Label
        stack_timepoint_label_frame.exp_time_label = ttk.Label(stack_timepoint_label_frame, text='Stack Acq. Time')
        stack_timepoint_label_frame.exp_time_label.grid(row=2, column=label_position, sticky=(NSEW))

        # Stack Acq. Time Spinbox
        stack_timepoint_label_frame.stack_acq_spinval = DoubleVar()
        stack_timepoint_label_frame.stack_acq_spinbox = ttk.Spinbox(
            stack_timepoint_label_frame,
            from_=0,
            to=5000.0,
            textvariable=stack_timepoint_label_frame.stack_acq_spinval, #this holds the data in the entry
            increment=25,
            width=9
        )
        stack_timepoint_label_frame.stack_acq_spinbox.grid(row=2, column=input_position, sticky=(NSEW))
        stack_timepoint_label_frame.stack_acq_spinbox.state(['disabled']) #Starts it disabled

        #Stack Pause Label
        stack_timepoint_label_frame.exp_time_label = ttk.Label(stack_timepoint_label_frame, text='Stack Pause (s)')
        stack_timepoint_label_frame.exp_time_label.grid(row=3, column=label_position, sticky=(NSEW))

        # Stack Pause Spinbox
        stack_timepoint_label_frame.stack_pause_spinval = DoubleVar()
        stack_timepoint_label_frame.stack_pause_spinbox = ttk.Spinbox(
            stack_timepoint_label_frame, from_=0,to=5000.0,
            textvariable=stack_timepoint_label_frame.stack_pause_spinval, increment=25, width=9)
        stack_timepoint_label_frame.stack_pause_spinbox.grid(row=3, column=input_position, sticky=(NSEW))

        #Timepoint Interval Label
        stack_timepoint_label_frame.exp_time_label = ttk.Label(stack_timepoint_label_frame, text='Timepoint Interval (hh:mm:ss)')
        stack_timepoint_label_frame.exp_time_label.grid(row=4, column=label_position, sticky=(NSEW))

        # Timepoint Interval Spinbox
        stack_timepoint_label_frame.timepoint_interval_spinval = StringVar()
        if stack_timepoint_label_frame.timepoint_interval_spinval.get() == '':
            stack_timepoint_label_frame.timepoint_interval_spinval.set('0')
        stack_timepoint_label_frame.timepoint_interval_spinbox = ttk.Spinbox(
            stack_timepoint_label_frame, from_=0, to=5000.0,
            textvariable=stack_timepoint_label_frame.timepoint_interval_spinval, increment=25, width=9)
        stack_timepoint_label_frame.timepoint_interval_spinbox.grid(row=4, column=input_position, sticky=(NSEW))
        stack_timepoint_label_frame.timepoint_interval_spinbox.state(['disabled']) #Starts it disabled


        #Total Time Label
        stack_timepoint_label_frame.exp_time_label = ttk.Label(stack_timepoint_label_frame, text='Experiment Duration (hh:mm:ss)')
        stack_timepoint_label_frame.exp_time_label.grid(row=5, column=label_position, sticky=(NSEW))

        # Total Time Spinbox
        stack_timepoint_label_frame.total_time_spinval = StringVar()
        if stack_timepoint_label_frame.total_time_spinval.get() == '':
            stack_timepoint_label_frame.total_time_spinval.set('0')
        stack_timepoint_label_frame.total_time_spinval = ttk.Spinbox(
            stack_timepoint_label_frame,
            from_=0, to=5000.0, textvariable=stack_timepoint_label_frame.total_time_spinval,
            increment=25, width=9)
        stack_timepoint_label_frame.total_time_spinval.grid(row=5, column=input_position, sticky=(NSEW))
        stack_timepoint_label_frame.total_time_spinval.state(['disabled'])

