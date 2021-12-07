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

        settings.channel_1_frame = channel_frame(settings.channel_main, "1", session)
        settings.channel_1_frame.grid(row=1,column=0, columnspan=4, sticky=(NSEW))
        """

class stack_timepoint_frame(ttk.Frame):
    def __init__(stack_timepoint_label_frame, settings_tab, session, verbose, *args, **kwargs):

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
        on_off = BooleanVar()
        on_off.set(False)
        stack_timepoint_label_frame.save_check = ttk.Checkbutton(
            stack_timepoint_label_frame,
            text='',
            variable=on_off)
        stack_timepoint_label_frame.save_check.grid(row=0, column=input_position, sticky=(NSEW))

        #Update Session
        def update_session_save_data(on_off, session, verbose):
            if on_off.get() == False:
                session.MicroscopeState['save_data'] = 0
            elif on_off.get() == True:
                session.MicroscopeState['save_data'] = 1
            if verbose:
                print("Save Data State:", session.MicroscopeState['save_data'])
        on_off.trace_add('write', lambda *args: update_session_save_data(on_off, session, verbose))

        #Timepoints Label
        stack_timepoint_label_frame.filterwheel_label = ttk.Label(stack_timepoint_label_frame, text='Timepoints')
        stack_timepoint_label_frame.filterwheel_label.grid(row=1, column=label_position, sticky=(NSEW))

        # Number of Timepoints Spinbox.  Defaults to 1
        stack_timepoint_label_frame.exp_time_spinval = StringVar()
        if stack_timepoint_label_frame.exp_time_spinval.get() == '':
            stack_timepoint_label_frame.exp_time_spinval.set('1')
        stack_timepoint_label_frame.exp_time_spinbox = ttk.Spinbox(
            stack_timepoint_label_frame,
            from_=0,
            to=5000.0,
            textvariable=stack_timepoint_label_frame.exp_time_spinval, #this holds the data in the entry
            increment=1,
            width=9
            #TODO command= function from connector.  Also, have it save parameters to session.
        )
        stack_timepoint_label_frame.exp_time_spinbox.grid(row=1, column=input_position, sticky=(NSEW))

        #Update Session
        def update_session_timepoints(stack_timepoint_label_frame, session, verbose):
            number_of_timepoints = stack_timepoint_label_frame.exp_time_spinval.get()
            session.MicroscopeState['timepoints'] = number_of_timepoints
            if verbose:
                print("Number of Timepoints:", session.MicroscopeState['timepoints'])
        stack_timepoint_label_frame.exp_time_spinval.trace_add('write', lambda *args: update_session_timepoints(stack_timepoint_label_frame, session, verbose))

        #Stack Acq. Time Label
        stack_timepoint_label_frame.exp_time_label = ttk.Label(stack_timepoint_label_frame, text='Stack Acq. Time')
        stack_timepoint_label_frame.exp_time_label.grid(row=2, column=label_position, sticky=(NSEW))

        # Stack Acq. Time Spinbox
        stack_timepoint_label_frame.stack_acq_spinval = StringVar()
        if stack_timepoint_label_frame.stack_acq_spinval.get() == '':
            stack_timepoint_label_frame.stack_acq_spinval.set('200')
        stack_timepoint_label_frame.stack_acq_spinval = ttk.Spinbox(
            stack_timepoint_label_frame,
            from_=0,
            to=5000.0,
            textvariable=stack_timepoint_label_frame.stack_acq_spinval, #this holds the data in the entry
            increment=25,
            width=9
            #TODO command= function from connector.  Also, have it save parameters to session.
        )
        stack_timepoint_label_frame.stack_acq_spinval.grid(row=2, column=input_position, sticky=(NSEW))
        stack_timepoint_label_frame.stack_acq_spinval.state(['disabled']) #Starts it disabled

        #Stack Pause Label
        stack_timepoint_label_frame.exp_time_label = ttk.Label(stack_timepoint_label_frame, text='Stack Pause (s)')
        stack_timepoint_label_frame.exp_time_label.grid(row=3, column=label_position, sticky=(NSEW))

        # Stack Pause Spinbox
        stack_timepoint_label_frame.stack_pause_spinval = StringVar()
        if stack_timepoint_label_frame.stack_pause_spinval.get() == '':
            stack_timepoint_label_frame.stack_pause_spinval.set('0')
        stack_timepoint_label_frame.stack_pause_spinval = ttk.Spinbox(
            stack_timepoint_label_frame,
            from_=0,
            to=5000.0,
            textvariable=stack_timepoint_label_frame.stack_pause_spinval, #this holds the data in the entry
            increment=25,
            width=9
            #TODO command= function from connector.  Also, have it save parameters to session.
        )
        stack_timepoint_label_frame.stack_pause_spinval.grid(row=3, column=input_position, sticky=(NSEW))

        # Update Session
        def update_session_stack_pause(stack_timepoint_label_frame, session, verbose):
            stack_pause = stack_timepoint_label_frame.stack_pause_spinval.get()
            session.MicroscopeState['stack_pause'] = stack_pause
            if verbose:
                print("Stack Pause Duration:", session.MicroscopeState['stack_pause'])
        #stack_timepoint_label_frame.stack_pause_spinval.trace_add('write', lambda *args: update_session_stack_pause(
            #stack_timepoint_label_frame, session, verbose))

        #Timepoint Interval Label
        stack_timepoint_label_frame.exp_time_label = ttk.Label(stack_timepoint_label_frame, text='Timepoint Interval (hh:mm:ss)')
        stack_timepoint_label_frame.exp_time_label.grid(row=4, column=label_position, sticky=(NSEW))

        # Timepoint Interval Spinbox
        stack_timepoint_label_frame.timepoint_interval_spinval = StringVar()
        if stack_timepoint_label_frame.timepoint_interval_spinval.get() == '':
            stack_timepoint_label_frame.timepoint_interval_spinval.set('0')
        stack_timepoint_label_frame.timepoint_interval_spinval = ttk.Spinbox(
            stack_timepoint_label_frame,
            from_=0,
            to=5000.0,
            textvariable=stack_timepoint_label_frame.timepoint_interval_spinval, #this holds the data in the entry
            increment=25,
            width=9
            #TODO command= function from connector.  Also, have it save parameters to session.
        )
        stack_timepoint_label_frame.timepoint_interval_spinval.grid(row=4, column=input_position, sticky=(NSEW))
        stack_timepoint_label_frame.timepoint_interval_spinval.state(['disabled']) #Starts it disabled


        #Total Time Label
        stack_timepoint_label_frame.exp_time_label = ttk.Label(stack_timepoint_label_frame, text='Experiment Duration (hh:mm:ss)')
        stack_timepoint_label_frame.exp_time_label.grid(row=5, column=label_position, sticky=(NSEW))

        # Total Time Spinbox
        stack_timepoint_label_frame.total_time_spinval = StringVar()
        if stack_timepoint_label_frame.total_time_spinval.get() == '':
            stack_timepoint_label_frame.total_time_spinval.set('0')
        stack_timepoint_label_frame.total_time_spinval = ttk.Spinbox(
            stack_timepoint_label_frame,
            from_=0,
            to=5000.0,
            textvariable=stack_timepoint_label_frame.total_time_spinval, #this holds the data in the entry
            increment=25,
            width=9
            #TODO command= function from connector.  Also, have it save parameters to session.
        )
        stack_timepoint_label_frame.total_time_spinval.grid(row=5, column=input_position, sticky=(NSEW))
        stack_timepoint_label_frame.total_time_spinval.state(['disabled'])

