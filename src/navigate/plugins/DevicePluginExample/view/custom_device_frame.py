# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
#

# Standard Imports
import tkinter as tk
from tkinter import ttk

from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput


class CustomDeviceFrame(ttk.Frame):
    """Custom Device Frame: Just an example

    This frame contains the widgets for the custom device setting.
    """

    def __init__(self, root, *args, **kwargs):
        """Initilization of the  Frame

        Parameters
        ----------
        root : tkinter.ttk.Frame
            The frame that this frame will be placed in.
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.
        """
        ttk.Frame.__init__(self, root, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Dictionary for widgets and buttons
        #: dict: Dictionary of the widgets in the frame
        self.inputs = {}

        self.inputs["step_size"] = LabelInput(
            parent=self,
            label="Step Size",
            label_args={"padding": (0, 0, 10, 0)},
            input_class=ttk.Entry,
            input_var=tk.DoubleVar(),
        )
        self.inputs["step_size"].grid(row=0, column=0, sticky="N", padx=6)
        self.inputs["step_size"].label.grid(sticky="N")
        self.inputs["angle"] = LabelInput(
            parent=self,
            label="Angle",
            label_args={"padding": (0, 5, 25, 0)},
            input_class=ttk.Entry,
            input_var=tk.DoubleVar(),
        )
        self.inputs["angle"].grid(row=1, column=0, sticky="N", padx=6)
        self.inputs["angle"].label.grid(sticky="N")

        self.buttons = {}
        self.buttons["move"] = ttk.Button(self, text="MOVE")
        self.buttons["rotate"] = ttk.Button(self, text="ROTATE")
        self.buttons["stop"] = ttk.Button(self, text="STOP")
        self.buttons["move"].grid(row=0, column=1, sticky="N", padx=6)
        self.buttons["rotate"].grid(row=1, column=1, sticky="N", padx=6)
        self.buttons["stop"].grid(row=2, column=1, sticky="N", padx=6)

    # Getters
    def get_variables(self):
        """Returns a dictionary of the variables for the widgets in this frame.

        The key is the widget name, value is the variable associated.

        Returns
        -------
        variables : dict
            Dictionary of the variables for the widgets in this frame.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get_variable()
        return variables

    def get_widgets(self):
        """Returns a dictionary of the widgets in this frame.

        The key is the widget name, value is the LabelInput class that has all the data.

        Returns
        -------
        self.inputs : dict
            Dictionary of the widgets in this frame.
        """
        return self.inputs
