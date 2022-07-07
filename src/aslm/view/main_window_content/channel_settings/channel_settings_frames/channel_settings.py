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
import logging

import tkinter as tk
from tkinter import ttk
from tkinter.font import Font

from aslm.view.custom_widgets.validation import ValidatedSpinbox

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class channel_creator(ttk.Labelframe):
    def __init__(self, channels_tab, *args, **kwargs):
        #  Init Frame
        self.title = 'Channel Settings'
        ttk.Labelframe.__init__(self, channels_tab, text=self.title, *args, **kwargs)
        
        # Formatting
        tk.Grid.columnconfigure(self, 'all', weight=1)
        tk.Grid.rowconfigure(self, 'all', weight=1)

        #  Arrays with Widget Variables and widgets themselves
        #  TODO refactor using dicts for variables and one for widgets,
        #   allow access to arrays via a key. might be overly complicated.
        #   Below way is clear just a bit repetitive
        #  Channel Checkbuttons
        self.channel_variables = []
        self.channel_checks = []

        #  Laser Dropdowns
        self.laser_variables = []
        self.laser_pulldowns = []

        #  LaserPower Dropdowns
        self.laserpower_variables = []
        self.laserpower_pulldowns = []

        #  FilterWheel Dropdowns
        self.filterwheel_variables = []
        self.filterwheel_pulldowns = []

        #  Exposure Time Dropdowns
        self.exptime_variables = []
        self.exptime_pulldowns = []

        #  Time Interval Spinboxes
        self.interval_variables = []
        self.interval_spins = []

        # Defocus Spinboxes
        self.defocus_variables = []
        self.defocus_spins = []

        #  Channel Creation

        #  Grids labels them across the top row of each column
        self.label_text = ["Channel", "Laser", "Power", "Filter", "Exp. Time (ms)", "Interval", "Defocus"]
        self.labels = []
        self.frame_columns = []

        #  Creates a column frame for each widget, this is to help with the lables lining up
        for idx in range(len(self.label_text)):
            self.frame_columns.append(ttk.Frame(self))
            self.frame_columns[idx].columnconfigure(0, weight=1, uniform=1)
            self.frame_columns[idx].rowconfigure('all', weight=1, uniform=1)
            self.frame_columns[idx].grid(row=0, column=idx, sticky=tk.NSEW, padx=1, pady=(4, 6))
            self.labels.append(ttk.Label(self.frame_columns[idx], text=self.label_text[idx]))
            self.labels[idx].grid(row=0, column=0, sticky=tk.N, pady=1, padx=1)
        self.frame_columns[5].grid(padx=(1, 4))
        self.frame_columns[0].grid(padx=(4, 1))
            
        
        #  Adds and grids widgets to respective column
        #  TODO add connection to config file to specify the range.
        #   This will allow custom selection of amount of channels.
        #   Also may need further refactoring
        for num in range(0, 5):
            #  This will add a widget to each column frame for the respecitive types
            #  Channel Checkboxes
            self.channel_variables.append(tk.BooleanVar())
            self.channel_checks.append(ttk.Checkbutton(self.frame_columns[0], text='CH' + str(num+1),
                                                       variable=self.channel_variables[num]))
            self.channel_checks[num].grid(row=num+1, column=0, sticky=tk.NSEW, padx=1, pady=1)

            #  Laser Dropdowns
            self.laser_variables.append(tk.StringVar())
            self.laser_pulldowns.append(ttk.Combobox(self.frame_columns[1],
                                                     textvariable=self.laser_variables[num], width=8))
            self.laser_pulldowns[num].state(["readonly"])
            self.laser_pulldowns[num].grid(row=num+1, column=0, sticky=tk.NSEW, padx=1, pady=1)

            #  Laser Power Spinbox
            self.laserpower_variables.append(tk.StringVar())
            self.laserpower_pulldowns.append(ttk.Spinbox(self.frame_columns[2], from_=0, to=100.0,
                                                         textvariable=self.laserpower_variables[num],
                                                         increment=5, width=3, font=Font(size=11)))
            self.laserpower_pulldowns[num].grid(row=num+1, column=0, sticky=NS, padx=1, pady=1)

            #  FilterWheel Dropdowns
            self.filterwheel_variables.append(tk.StringVar())
            self.filterwheel_pulldowns.append(ttk.Combobox(self.frame_columns[3],
                                                           textvariable=self.filterwheel_variables[num], width=22))
            self.filterwheel_pulldowns[num].state(["readonly"])
            self.filterwheel_pulldowns[num].grid(row=num+1, column=0, sticky=tk.NSEW, padx=1, pady=1)

            #  Exposure Time Spinboxes
            self.exptime_variables.append(tk.StringVar())
            self.exptime_pulldowns.append(ttk.Spinbox(self.frame_columns[4], from_=0, to=5000.0,
                                                      textvariable=self.exptime_variables[num], increment=25, width=12, font=Font(size=11)))
            self.exptime_pulldowns[num].grid(row=num+1, column=0, sticky=tk.NSEW, padx=1, pady=1)

            #  Time Interval Spinboxes
            self.interval_variables.append(tk.StringVar())
            self.interval_spins.append(ttk.Spinbox(self.frame_columns[5], from_=0, to=5000.0,
                                                   textvariable=self.interval_variables[num], increment=1, width=6, font=Font(size=11)))
            self.interval_spins[num].grid(row=num+1, column=0, sticky=tk.NSEW, padx=1, pady=1)

            # Defocus Spinbox
            self.defocus_variables.append(tk.DoubleVar())
            self.defocus_spins.append(ValidatedSpinbox(self.frame_columns[6], from_=0.0, to=200.0,
                                                  textvariable=self.defocus_variables[num], increment=0.1, width=6, font=Font(size=11)))
            self.defocus_spins[num].grid(row=num+1, column=0, sticky=tk.NSEW, padx=1, pady=1)


        self.filterwheel_pulldowns[1].grid(pady=2)
        self.filterwheel_pulldowns[2].grid(pady=2)
        self.laser_pulldowns[1].grid(pady=2)
        self.laser_pulldowns[2].grid(pady=2)
        self.channel_checks[1].grid(pady=2)
        self.channel_checks[2].grid(pady=2)

if __name__ == '__main__':
    root = tk.Tk()
    channel_creator(root).grid(row=0, column=0, sticky=tk.NSEW)
    root.mainloop()