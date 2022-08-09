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
import tkinter as tk
from tkinter import ttk
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)



class stack_timepoint_frame(ttk.Labelframe):
    def __init__(self, settings_tab, *args, **kwargs):
        text_label = 'Timepoint Settings'
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)
        
        # Formatting
        tk.Grid.columnconfigure(self, 'all', weight=1)
        tk.Grid.rowconfigure(self, 'all', weight=1)

        # Widget dictionary
        self.inputs = {}


        #Save Data Label
        self.laser_label = ttk.Label(self, text='Save Data')
        self.laser_label.grid(row=0, column=0, sticky=(tk.NSEW), padx=(4,5), pady=(4,0))

        #Save Data Checkbox
        self.save_data = tk.BooleanVar()
        self.save_data.set(False)
        self.save_check = ttk.Checkbutton(self, text='', variable=self.save_data)
        self.save_check.grid(row=0, column=1, sticky=(tk.NSEW), pady=(4,0))
        self.inputs['save_check'] = self.save_check


        # Timepoints Label, spinbox defaults to 1.
        self.filterwheel_label = ttk.Label(self, text='Timepoints')
        self.filterwheel_label.grid(row=1, column=0, sticky=(tk.NSEW), padx=(4,5), pady=2)
        self.exp_time_spinval = tk.StringVar()
        self.exp_time_spinbox = ttk.Spinbox(
            self, from_=0, to=5000, textvariable=self.exp_time_spinval,
            increment=1,
            width=3)
        self.exp_time_spinbox.grid(row=1, column=1, sticky=(tk.NSEW), pady=2)
        self.inputs['time_spin'] = self.exp_time_spinbox

        #Stack Acq. Time Label
        self.exp_time_label = ttk.Label(self, text='Stack Acq. Time')
        self.exp_time_label.grid(row=2, column=0, sticky=(tk.NSEW), padx=(4,5), pady=2)

        # Stack Acq. Time Spinbox
        self.stack_acq_spinval = tk.StringVar()
        self.stack_acq_spinbox = ttk.Spinbox(
            self,
            from_=0,
            to=5000.0,
            textvariable=self.stack_acq_spinval, #this holds the data in the entry
            increment=25,
            width=6
        )
        self.stack_acq_spinbox.grid(row=2, column=1, sticky=(tk.NSEW), pady=2)
        self.stack_acq_spinbox.state(['disabled']) #Starts it disabled

        #Stack Pause Label
        self.exp_time_label = ttk.Label(self, text='Stack Pause (s)')
        self.exp_time_label.grid(row=0, column=2, sticky=(tk.NSEW), padx=(4,5), pady=2)

        # Stack Pause Spinbox
        self.stack_pause_spinval = tk.StringVar()
        self.stack_pause_spinbox = ttk.Spinbox(
            self, from_=0,to=5000.0,
            textvariable=self.stack_pause_spinval, increment=25, width=6)
        self.stack_pause_spinbox.grid(row=0, column=3, sticky=(tk.NSEW), pady=2)
        self.inputs['stack_pause'] = self.stack_pause_spinbox

        #Timepoint Interval Label
        self.exp_time_label = ttk.Label(self, text='Timepoint Interval (hh:mm:ss)')
        self.exp_time_label.grid(row=1, column=2, sticky=(tk.NSEW), padx=(4,5), pady=2)

        # Timepoint Interval Spinbox
        self.timepoint_interval_spinval = tk.StringVar()
        if self.timepoint_interval_spinval.get() == '':
            self.timepoint_interval_spinval.set('0')
        self.timepoint_interval_spinbox = ttk.Spinbox(
            self, from_=0, to=5000.0,
            textvariable=self.timepoint_interval_spinval, increment=25, width=6)
        self.timepoint_interval_spinbox.grid(row=1, column=3, sticky=(tk.NSEW), pady=2)
        self.timepoint_interval_spinbox.state(['disabled']) #Starts it disabled


        #Total Time Label
        self.exp_time_label = ttk.Label(self, text='Experiment Duration (hh:mm:ss)')
        self.exp_time_label.grid(row=2, column=2, sticky=(tk.NSEW), padx=(4,5), pady=(2,6))

        # Total Time Spinbox
        self.total_time_spinval = tk.StringVar()
        if self.total_time_spinval.get() == '':
            self.total_time_spinval.set('0')
        self.total_time_spinval = ttk.Spinbox(
            self,
            from_=0, to=5000.0, textvariable=self.total_time_spinval,
            increment=25, width=6)
        self.total_time_spinval.grid(row=2, column=3, sticky=(tk.NSEW), pady=(2,6))
        self.total_time_spinval.state(['disabled'])


    # Getters
    def get_variables(self):
        """
        # This function returns a dictionary of all the variables that are tied to each widget name.
        The key is the widget name, value is the variable associated.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get_variable()
        return variables

    def get_widgets(self):
        """
        # This function returns the dictionary that holds the input widgets.
        The key is the widget name, value is the LabelInput class that has all the data.
        """
        return self.inputs

