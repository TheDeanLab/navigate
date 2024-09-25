# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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
from navigate.view.custom_widgets.popup import PopUp
from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from navigate.view.custom_widgets.validation import ValidatedSpinbox, ValidatedEntry

# Logging Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class TilingWizardPopup:
    """Popup for tiling parameters in View."""

    def __init__(self, root, *args, **kwargs):
        """Initialize the popup

        Parameters
        ----------
        root : tk.Tk
            The root Tk instance
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.
        """
        #: tk.TopLevel: The popup window
        self.popup = PopUp(
            root,
            "Multi-Position Tiling Wizard",
            "800x250+10+10",
            top=False,
            transient=False,
        )

        # Grab the axes we want to grid out. Optionally,
        # we can pass these in the kwargs
        axes = list(kwargs.get("axes", "XYZF"))

        nrow = len(axes) + 2  # +2 for percent overlay, total number of tiles, populate
        # <set x-start> [x-start] <set-x-end> [x-end]
        # [x-distance] [x-fov-width] [x-tiles]
        ncol = 7

        # Set up the grid on the popup's frame
        for col in range(ncol):
            self.popup.content_frame.columnconfigure(col, pad=5, weight=1)
        for row in range(nrow):
            self.popup.content_frame.rowconfigure(row, pad=5, weight=1)
        #: dict: The GUI elements used for input, mostly ttk.Frames
        self.inputs = {}
        #: dict: The GUI elements used for buttons, mostly ttk.Buttons
        self.buttons = {}

        # Add one row per axis
        for row, ax in enumerate(axes):
            # Set start position
            start_var = f"{ax.lower()}_start"
            self.buttons[start_var] = ttk.Button(
                self.popup.content_frame, text=f"Set {ax.upper()} Start"
            )
            self.buttons[start_var].grid(
                row=row, column=0, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0)
            )
            self.inputs[start_var] = LabelInput(
                parent=self.popup.content_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
                input_args={"width": 5},
            )
            self.inputs[start_var].grid(
                row=row, column=1, sticky=tk.NSEW, pady=(5, 0), padx=(5, 0)
            )
            self.inputs[start_var].widget.state(["disabled"])

            # Set end position
            end_var = f"{ax.lower()}_end"
            self.buttons[end_var] = ttk.Button(
                self.popup.content_frame, text=f"Set {ax.upper()} End"
            )
            self.buttons[end_var].grid(
                row=row, column=2, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0)
            )
            self.inputs[end_var] = LabelInput(
                parent=self.popup.content_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
                input_args={"width": 5},
            )
            self.inputs[end_var].grid(
                row=row, column=3, sticky=tk.NSEW, pady=(5, 0), padx=(5, 0)
            )
            self.inputs[end_var].widget.state(["disabled"])

            # Distance between start and end of this axis
            dist_var = f"{ax.lower()}_dist"
            self.inputs[dist_var] = LabelInput(
                parent=self.popup.content_frame,
                label=f"{ax.upper()} Distance",
                input_class=ValidatedEntry,
                input_var=tk.StringVar(),
                input_args={"width": 5},
            )
            self.inputs[dist_var].grid(
                row=row, column=4, sticky=tk.NSEW, pady=(5, 0), padx=(5, 0)
            )
            self.inputs[dist_var].widget.state(["disabled"])

            # FOV width for this particular axis (e.g. for X it is the number
            # of vertical pixels on the camera multipled by the effective
            # pixel size)
            fov_var = f"{ax.lower()}_fov"
            self.inputs[fov_var] = LabelInput(
                parent=self.popup.content_frame,
                label=f"{ax.upper()} FOV Dist",
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
                input_args={
                    "width": 5,
                    "from_": "-Infinity",
                    "to": "Infinity",
                    "increment": 100.0,
                },
            )
            self.inputs[fov_var].grid(
                row=row, column=5, sticky=tk.NSEW, pady=(5, 0), padx=(5, 0)
            )
            # self.inputs[fov_var].widget.state(["disabled"])

            # Number of tiles, roughly ceil((ax_end - ax_start) / fov_width)
            # (not accounting for percent overlap)
            tiles_var = f"{ax.lower()}_tiles"
            self.inputs[tiles_var] = LabelInput(
                parent=self.popup.content_frame,
                label="Num. Tiles",
                input_class=ValidatedEntry,
                input_var=tk.StringVar(),
                input_args={"width": 5},
            )
            self.inputs[tiles_var].grid(
                row=row, column=6, sticky=tk.NSEW, pady=(5, 0), padx=(5, 0)
            )
            self.inputs[tiles_var].widget.state(["disabled"])

        # In the final row, add percent overlap, total number of tiles, populate button
        self.inputs["percent_overlap"] = LabelInput(
            parent=self.popup.content_frame,
            label="% Overlap",
            input_class=ValidatedSpinbox,
            input_var=tk.StringVar(),
            input_args={"width": 5, "increment": 5, "from_": 0, "to": 100},
        )
        self.inputs["percent_overlap"].grid(
            row=len(axes), column=5, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0)
        )

        self.inputs["total_tiles"] = LabelInput(
            parent=self.popup.content_frame,
            label="Total Tiles",
            input_class=ValidatedEntry,
            input_var=tk.StringVar(),
            input_args={"width": 5},
        )
        self.inputs["total_tiles"].widget.state(["disabled"])
        self.inputs["total_tiles"].grid(
            row=len(axes), column=6, sticky=tk.NSEW, padx=(5, 0), pady=(5, 0)
        )

        self.buttons["set_table"] = ttk.Button(
            self.popup.content_frame, text="Populate Multi-Position Table"
        )
        self.buttons["set_table"].grid(
            row=len(axes) + 1,
            column=5,
            columnspan=2,
            sticky=tk.NE,
            padx=(0, 5),
            pady=(5, 0),
        )

    # Getters
    def get_variables(self):
        """Get the variables tied to the widgets

        This function returns a dictionary of all the variables that are tied to each
        widget name. The key is the widget name, value is the variable associated.

        Returns
        -------
        variables : dict
            A dictionary of all the variables that are tied to each widget name.
        """
        return {key: widget.get_variable() for key, widget in self.inputs.items()}

    def get_widgets(self):
        """Get the widgets

        This function returns the dictionary that holds the input widgets.
        The key is the widget name, value is the LabelInput class that has all the data.

        Returns
        -------
        self.inputs : dict
            A dictionary of all the widgets that are tied to each widget name.
        """
        return self.inputs

    def get_buttons(self):
        """Get the buttons

        This function returns the dictionary that holds the buttons.
        The key is the button name, value is the button.

        Returns
        -------
        self.buttons : dict
            A dictionary of all the buttons that are tied to each button name.
        """
        return self.buttons
