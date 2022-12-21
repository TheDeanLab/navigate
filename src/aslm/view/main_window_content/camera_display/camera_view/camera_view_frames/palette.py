# ASLM Model Waveforms

# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Standard Library Imports
import logging
import tkinter as tk
from tkinter import ttk
from pathlib import Path

from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class palette(ttk.Labelframe):
    def __init__(self, cam_view, *args, **kwargs):
        # Init Frame
        text_label = 'LUT'
        ttk.Labelframe.__init__(
            self,
            cam_view,
            text=text_label,
            *args,
            **kwargs)
        
        # Formatting
        tk.Grid.columnconfigure(self, 'all', weight=1)
        tk.Grid.rowconfigure(self, 'all', weight=1)

        # Dictionary for widgets
        self.inputs = {}

        # LUT Radio buttons - Gray is default
        self.color_labels = ['Gray', 'Gradient', 'Rainbow', 'SNR']       # Human-readable names
        self.color_values = ['gist_gray', 'plasma', 'afmhot', 'RdBu_r']  # maplotlib cmap names
        self.color = tk.StringVar()
        for i in range(len(self.color_labels)):
            self.inputs[self.color_labels[i]] = LabelInput(parent=self,
                                                           label=self.color_labels[i],
                                                           input_class=ttk.Radiobutton,
                                                           input_var=self.color,
                                                           input_args={'value': self.color_values[i]}
                                                           )
            self.inputs[self.color_labels[i]].grid(
                row=i, column=0, sticky=tk.NSEW, pady=3)

        # Flip xy
        self.transpose = tk.BooleanVar()
        self.trans = 'Flip XY'
        self.inputs[self.trans] = LabelInput(parent=self,
                                            label=self.trans,
                                            input_class=ttk.Checkbutton,
                                            input_var=self.transpose
                                            )
        self.inputs[self.trans].grid(row=len(self.color_labels), column=0, sticky=tk.NSEW, pady=3)

        # Autoscale
        self.autoscale = tk.BooleanVar()
        self.auto = 'Autoscale'
        self.minmax = ['Min Counts', 'Max Counts']
        self.minmax_names = ['Min', 'Max']
        self.inputs[self.auto] = LabelInput(parent=self,
                                            label=self.auto,
                                            input_class=ttk.Checkbutton,
                                            input_var=self.autoscale
                                            )
        self.inputs[self.auto].grid(row=len(self.color_labels)+1, column=0, sticky=tk.NSEW, pady=3)

        # Max and Min Counts
        for i in range(len(self.minmax)):
            self.inputs[self.minmax_names[i]] = LabelInput(parent=self,
                                                           label=self.minmax[i],
                                                           input_class=ttk.Spinbox,
                                                           input_var=tk.IntVar(),
                                                           input_args={'from_': 1,
                                                                       'to': 2**16-1,
                                                                       'increment': 1,
                                                                       'width': 5})
            self.inputs[self.minmax_names[i]].grid(row=i + len(self.color_labels) + 2, column=0, sticky=tk.NSEW, padx=3, pady=3)

    def get_variables(self):
        """
        # This function returns a dictionary of all the variables that are tied to each widget name.
        The key is the widget name, value is the variable associated.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get()
        return variables

    def get_widgets(self):
        """
        # This function returns the dictionary that holds the widgets.
        The key is the widget name, value is the LabelInput class that has all the data.
        """
        return self.inputs
