# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
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

import pandas as pd
from aslm.view.main_window_content.multiposition.multi_position_table import (
    Multi_Position_Table as MPTable,
)
import tkinter as tk
from tkinter import ttk
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class multipoint_frame(ttk.Labelframe):
    def __init__(self, settings_tab, *args, **kwargs):
        text_label = "Multi-Position Acquisition"
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Dict

        # Save Data Label
        self.laser_label = ttk.Label(self, text="Enable")
        self.laser_label.grid(row=0, column=0, sticky=tk.NSEW, padx=(4, 1), pady=(4, 6))

        # Save Data Checkbox
        self.on_off = tk.BooleanVar()
        self.save_check = ttk.Checkbutton(self, text="", variable=self.on_off)
        self.save_check.grid(row=0, column=1, sticky=tk.NSEW, pady=(4, 6))

        # Getters

    def get_variables(self):
        """
        This function returns a dictionary of all the
        variables that are tied to each widget name.
        The key is the widget name,
        value is the variable associated.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get_variable()
        return variables

    def get_widgets(self):
        """
        This function returns the dictionary that holds the input widgets.
        The key is the widget name, value is the LabelInput class that has all the data.
        """
        return self.inputs


class multipoint_list(ttk.Frame):
    """
    Exploring using a pandastable for embedding an interactive list within a tk Frame.
    https://pandastable.readthedocs.io/en/latest/
    """

    def __init__(self, settings_tab, *args, **kwargs):
        # Init Frame
        ttk.Frame.__init__(self, settings_tab, *args, **kwargs)

        df = pd.DataFrame({"X": [0], "Y": [0], "Z": [0], "R": [0], "F": [0]})
        # pt = Table(self, showtoolbar=False)
        self.pt = MPTable(self, showtoolbar=False)
        self.pt.show()
        self.pt.model.df = df

    def get_table(self):
        """
        Returns a reference to multipoint table dataframe.

        Parameters
        ----------
        self : object
            Multipoint List instance


        Returns
        -------
        self.pt.model.df: Pandas DataFrame
            Reference to table data as dataframe
        """

        return self.pt
