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

# Third Party Imports

# Local Imports
from aslm.view.custom_widgets.popup import PopUp
from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from aslm.view.custom_widgets.validation import ValidatedSpinbox, ValidatedEntry

# Logging Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class tiling_wizard_popup:
    r"""Popup for tiling parameters in View.

    Parameters
    ----------
    root : object
        GUI root
    args : ...
        ...
    kwargs : ...
        ...

    """

    def __init__(self, root, *args, **kwargs):
        # Creating popup window with this name and size/placement, PopUp is a
        # Toplevel window #300x200 pixels, first +320 means 320 pixels from left edge, +180 means 180 pixels from top edge
        self.popup = PopUp(
            root,
            "Multiposition Tiling Wizard",
            "1250x550+330+330",
            top=False,
            transient=False,
        )

        # Storing the content frame of the popup, this will be the parent of
        # the widgets
        content_frame = self.popup.get_frame()
        content_frame.columnconfigure(0, pad=5)
        content_frame.columnconfigure(1, pad=5)
        content_frame.rowconfigure(0, pad=5)
        content_frame.rowconfigure(1, pad=5)
        content_frame.rowconfigure(2, pad=5)

        # Formatting
        tk.Grid.columnconfigure(content_frame, "all", weight=1)
        tk.Grid.rowconfigure(content_frame, "all", weight=1)

        # Sub Frames
        action_buttons = ttk.Frame(content_frame, padding=(0, 5, 0, 0))
        pos_grid = ttk.Frame(content_frame, padding=(0, 5, 0, 0))
        data = ttk.Frame(content_frame, padding=(0, 5, 0, 0))

        action_buttons.grid(row=0, sticky=(tk.NSEW))
        pos_grid.grid(row=1, sticky=tk.NSEW)
        data.grid(row=2, sticky=tk.NSEW)

        """Creating the widgets for the popup"""
        # Dictionary for all the variables
        self.inputs = {}
        self.buttons = {}

        names = [
            "save",
            "set_table",
            "x_start",
            "x_end",
            "y_start",
            "y_end",
            "z_start",
            "z_end",
        ]

        entry_names = ["x_dist", "x_tiles", "y_dist", "y_tiles", "z_dist", "z_tiles"]

        dist_labels = [
            "X Distance",
            "Num. Tiles",
            "Y Distance",
            "Num. Tiles",
            "Z Distance",
            "Num. Tiles",
        ]

        # Action buttons
        btn_labels = [
            "Save to Disk",
            "Populate Multiposition Table",
            "Set X Start",
            "Set X End",
            "Set Y Start",
            "Set Y End",
            "Set Z Start",
            "Set Z End",
        ]

        for i in range(2):
            self.buttons[names[i]] = ttk.Button(action_buttons, text=btn_labels[i])
            self.buttons[names[i]].grid(
                row=0, column=i, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0)
            )

        # Position buttons
        for i in range(len(names)):
            if i > 1:
                self.buttons[names[i]] = ttk.Button(pos_grid, text=btn_labels[i])
                self.buttons[names[i]].grid(
                    row=i - 2, column=0, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0)
                )

        # Position Spinboxes
        for i in range(len(names)):
            if i > 1:
                self.inputs[names[i]] = LabelInput(
                    parent=pos_grid,
                    input_class=ValidatedSpinbox,
                    input_var=tk.StringVar(),
                )
                self.inputs[names[i]].grid(
                    row=i - 2, column=1, sticky=(tk.NSEW), pady=(20, 0), padx=5
                )
                self.inputs[names[i]].widget.state(["disabled"])

        # Dist and Tile entries
        for i in range(len(entry_names)):
            self.inputs[entry_names[i]] = LabelInput(
                parent=pos_grid,
                label=dist_labels[i],
                input_class=ValidatedEntry,
                input_var=tk.StringVar(),
            )
            self.inputs[entry_names[i]].grid(
                row=i, column=2, sticky=tk.NSEW, padx=(5, 0), pady=(17, 0)
            )
            self.inputs[entry_names[i]].widget.state(["disabled"])

        # Data widgets
        data_labels = ["Percent Overlay", "Total Tiles"]

        data_names = ["percent_overlay", "total_tiles"]

        self.inputs["percent_overlay"] = LabelInput(
            parent=data,
            label="Percent Overlay",
            input_class=ValidatedSpinbox,
            input_var=tk.StringVar(),
            input_args={"width": 5, "increment": 5, "from_": 0, "to": 100},
        )
        self.inputs["percent_overlay"].grid(
            row=1, column=0, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0)
        )

        self.inputs["total_tiles"] = LabelInput(
            parent=data,
            label="Total Tiles",
            input_class=ValidatedEntry,
            input_var=tk.StringVar(),
        )
        self.inputs["total_tiles"].widget.state(["disabled"])
        self.inputs["total_tiles"].grid(
            row=0, column=1, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0)
        )

        # Formatting
        self.inputs["total_tiles"].grid(padx=(110, 0))

    # Getters
    def get_variables(self):
        """
        This function returns a dictionary of all the variables that are tied to each widget name.
        The key is the widget name, value is the variable associated.
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

    def get_buttons(self):
        """
        This function returns the dictionary that holds the buttons.
        The key is the button name, value is the button.
        """
        return self.buttons
