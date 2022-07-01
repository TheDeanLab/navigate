"""
Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
from tkinter import *
from tkinter import ttk
import logging
from pathlib import Path

# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)
from tkinter.font import Font
import numpy as np

#Local imports
#from view.main_window_content.acquire_bar_frame.acquire_bar import AcquireBar

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

class stack_timepoint_frame(ttk.Labelframe):
    def __init__(stack_timepoint_label_frame, settings_tab, *args, **kwargs):
        text_label = 'Timepoint Settings'
        ttk.Labelframe.__init__(stack_timepoint_label_frame, settings_tab, text=text_label, *args, **kwargs)
        
        # Formatting
        Grid.columnconfigure(stack_timepoint_label_frame, 'all', weight=1)
        Grid.rowconfigure(stack_timepoint_label_frame, 'all', weight=1)

        #Save Data Label
        label_position = 0
        input_position = 4
        stack_timepoint_label_frame.laser_label = ttk.Label(stack_timepoint_label_frame, text='Save Data')
        stack_timepoint_label_frame.laser_label.grid(row=0, column=label_position, sticky=(NSEW), padx=(4,5), pady=(4,0))

        #Save Data Checkbox
        stack_timepoint_label_frame.save_data = BooleanVar()
        stack_timepoint_label_frame.save_data.set(False)
        stack_timepoint_label_frame.save_check = ttk.Checkbutton(stack_timepoint_label_frame, text='', variable=stack_timepoint_label_frame.save_data)
        stack_timepoint_label_frame.save_check.grid(row=0, column=input_position, sticky=(NSEW), pady=(4,0))
        


        # Timepoints Label, spinbox defaults to 1.
        stack_timepoint_label_frame.filterwheel_label = ttk.Label(stack_timepoint_label_frame, text='Timepoints')
        stack_timepoint_label_frame.filterwheel_label.grid(row=1, column=label_position, sticky=(NSEW), padx=(4,5), pady=2)
        stack_timepoint_label_frame.exp_time_spinval = StringVar()
        stack_timepoint_label_frame.exp_time_spinbox = ttk.Spinbox(
            stack_timepoint_label_frame, from_=0, to=5000, textvariable=stack_timepoint_label_frame.exp_time_spinval,
            increment=1,
            width=12)
        stack_timepoint_label_frame.exp_time_spinbox.grid(row=1, column=input_position, sticky=(NSEW), pady=2)

        #Stack Acq. Time Label
        stack_timepoint_label_frame.exp_time_label = ttk.Label(stack_timepoint_label_frame, text='Stack Acq. Time')
        stack_timepoint_label_frame.exp_time_label.grid(row=2, column=label_position, sticky=(NSEW), padx=(4,5), pady=2)

        # Stack Acq. Time Spinbox
        stack_timepoint_label_frame.stack_acq_spinval = StringVar()
        stack_timepoint_label_frame.stack_acq_spinbox = ttk.Spinbox(
            stack_timepoint_label_frame,
            from_=0,
            to=5000.0,
            textvariable=stack_timepoint_label_frame.stack_acq_spinval, #this holds the data in the entry
            increment=25,
            width=12
        )
        stack_timepoint_label_frame.stack_acq_spinbox.grid(row=2, column=input_position, sticky=(NSEW), pady=2)
        stack_timepoint_label_frame.stack_acq_spinbox.state(['disabled']) #Starts it disabled

        #Stack Pause Label
        stack_timepoint_label_frame.exp_time_label = ttk.Label(stack_timepoint_label_frame, text='Stack Pause (s)')
        stack_timepoint_label_frame.exp_time_label.grid(row=3, column=label_position, sticky=(NSEW), padx=(4,5), pady=2)

        # Stack Pause Spinbox
        stack_timepoint_label_frame.stack_pause_spinval = StringVar()
        stack_timepoint_label_frame.stack_pause_spinbox = ttk.Spinbox(
            stack_timepoint_label_frame, from_=0,to=5000.0,
            textvariable=stack_timepoint_label_frame.stack_pause_spinval, increment=25, width=12)
        stack_timepoint_label_frame.stack_pause_spinbox.grid(row=3, column=input_position, sticky=(NSEW), pady=2)

        #Timepoint Interval Label
        stack_timepoint_label_frame.exp_time_label = ttk.Label(stack_timepoint_label_frame, text='Timepoint Interval (hh:mm:ss)')
        stack_timepoint_label_frame.exp_time_label.grid(row=4, column=label_position, sticky=(NSEW), padx=(4,5), pady=2)

        # Timepoint Interval Spinbox
        stack_timepoint_label_frame.timepoint_interval_spinval = StringVar()
        if stack_timepoint_label_frame.timepoint_interval_spinval.get() == '':
            stack_timepoint_label_frame.timepoint_interval_spinval.set('0')
        stack_timepoint_label_frame.timepoint_interval_spinbox = ttk.Spinbox(
            stack_timepoint_label_frame, from_=0, to=5000.0,
            textvariable=stack_timepoint_label_frame.timepoint_interval_spinval, increment=25, width=12)
        stack_timepoint_label_frame.timepoint_interval_spinbox.grid(row=4, column=input_position, sticky=(NSEW), pady=2)
        stack_timepoint_label_frame.timepoint_interval_spinbox.state(['disabled']) #Starts it disabled


        #Total Time Label
        stack_timepoint_label_frame.exp_time_label = ttk.Label(stack_timepoint_label_frame, text='Experiment Duration (hh:mm:ss)')
        stack_timepoint_label_frame.exp_time_label.grid(row=5, column=label_position, sticky=(NSEW), padx=(4,5), pady=(2,6))

        # Total Time Spinbox
        stack_timepoint_label_frame.total_time_spinval = StringVar()
        if stack_timepoint_label_frame.total_time_spinval.get() == '':
            stack_timepoint_label_frame.total_time_spinval.set('0')
        stack_timepoint_label_frame.total_time_spinval = ttk.Spinbox(
            stack_timepoint_label_frame,
            from_=0, to=5000.0, textvariable=stack_timepoint_label_frame.total_time_spinval,
            increment=25, width=12)
        stack_timepoint_label_frame.total_time_spinval.grid(row=5, column=input_position, sticky=(NSEW), pady=(2,6))
        stack_timepoint_label_frame.total_time_spinval.state(['disabled'])

