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

# Standard Library Imports
import logging
from tkinter import *
from tkinter import ttk

# Third Party Library Imports

# Local Imports
from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class rgb_selection(ttk.Labelframe):
    def __init__(self, cam_view, *args, **kwargs):
        # Init Frame
        text_label = "RGB Selection"
        ttk.Labelframe.__init__(self, cam_view, text=text_label, *args, **kwargs)

        # Formatting
        Grid.columnconfigure(self, "all", weight=1)
        Grid.rowconfigure(self, "all", weight=1)

        # Dictionary for widgets
        self.inputs = {}

        # Labels and names
        self.color_labels = ["R", "G", "B"]
        self.color_values = ["R", "G", "B"]
        for i in range(len(self.color_labels)):
            self.inputs[self.color_labels[i]] = LabelInput(
                parent=self, label=self.color_labels[i], input_class=ttk.Label
            )
            self.inputs[self.color_labels[i]].grid(row=i + 1, column=0, sticky=NSEW)

        # Channels
        self.channel_labels = ["CH1", "CH2", "CH3", "CH4", "CH5"]
        self.labels = []
        self.frame_columns = []

        # CH1
        self.ch1_btns = []

        # CH2
        self.ch2_btns = []

        # CH3
        self.ch3_btns = []

        # CH4
        self.ch4_btns = []

        # CH5
        self.ch5_btns = []

        #  Creates a column frame for each widget
        for i in range(len(self.channel_labels)):
            self.frame_columns.append(ttk.Frame(self))
            self.frame_columns[i].columnconfigure(0, weight=1, uniform=1)
            self.frame_columns[i].rowconfigure("all", weight=1, uniform=1)
            self.frame_columns[i].grid(
                row=1, column=i + 1, sticky=NSEW, padx=1, pady=(4, 6), rowspan=3
            )
            self.labels.append(ttk.Label(self, text=self.channel_labels[i]))
            self.labels[i].grid(row=0, column=i + 1, sticky=N, pady=1, padx=1)
        self.frame_columns[3].grid(padx=(1, 4))
        self.frame_columns[0].grid(padx=(4, 1))

        #  Adds and grids widgets to respective column
        self.ch1 = StringVar()
        self.ch2 = StringVar()
        self.ch3 = StringVar()
        self.ch4 = StringVar()
        self.ch5 = StringVar()
        for num in range(0, 3):
            self.ch1_btns.append(
                LabelInput(
                    parent=self.frame_columns[0],
                    input_class=ttk.Radiobutton,
                    input_var=self.ch1,
                    input_args={"value": self.color_values[num]},
                )
            )
            self.ch1_btns[num].grid(row=num + 1, column=0, sticky=NSEW, padx=1, pady=1)

            self.ch2_btns.append(
                LabelInput(
                    parent=self.frame_columns[1],
                    input_class=ttk.Radiobutton,
                    input_var=self.ch2,
                    input_args={"value": self.color_values[num]},
                )
            )
            self.ch2_btns[num].grid(row=num + 1, column=0, sticky=NSEW, padx=1, pady=1)

            self.ch3_btns.append(
                LabelInput(
                    parent=self.frame_columns[2],
                    input_class=ttk.Radiobutton,
                    input_var=self.ch3,
                    input_args={"value": self.color_values[num]},
                )
            )
            self.ch3_btns[num].grid(row=num + 1, column=0, sticky=NSEW, padx=1, pady=1)

            self.ch4_btns.append(
                LabelInput(
                    parent=self.frame_columns[3],
                    input_class=ttk.Radiobutton,
                    input_var=self.ch4,
                    input_args={"value": self.color_values[num]},
                )
            )
            self.ch4_btns[num].grid(row=num + 1, column=0, sticky=NSEW, padx=1, pady=1)

            self.ch5_btns.append(
                LabelInput(
                    parent=self.frame_columns[4],
                    input_class=ttk.Radiobutton,
                    input_var=self.ch5,
                    input_args={"value": self.color_values[num]},
                )
            )
            self.ch5_btns[num].grid(row=num + 1, column=0, sticky=NSEW, padx=1, pady=1)

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
