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

# Standard Library Imports
import tkinter as tk
from tkinter import ttk
import logging

# Third Party Imports
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Local Imports
from aslm.view.custom_widgets.popup import PopUp
from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from aslm.view.custom_widgets.validation import ValidatedSpinbox

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class AutofocusPopup:
    """Class creates the popup to configure autofocus parameters.

    Parameters
    ----------
    root : tkinter.Tk
        The root window of the application.
    *args
        Variable length argument list.
    **kwargs
        Arbitrary keyword arguments.

    Attributes
    ----------
    popup : aslm.view.custom_widgets.popup.PopUp
        The popup window.
    inputs : dict
        Dictionary of all the input widgets.
    stage_vars : list
        List of booleans for the stage checkboxes.
    autofocus_btn : ttk.Button
        The autofocus button.
    fig : matplotlib.figure.Figure
        The matplotlib figure.
    coarse : matplotlib.axes._subplots.AxesSubplot
        The coarse autofocus subplot.
    fine : matplotlib.axes._subplots.AxesSubplot
        The fine autofocus subplot.

    Methods
    -------
    get_widgets()
        Returns the dictionary of input widgets.
    """

    def __init__(self, root, *args, **kwargs):
        # Creating popup window with this name and size/placement,
        # PopUp is a Toplevel window
        self.popup = PopUp(
            root, "Autofocus Settings", "+320+180", top=False, transient=False
        )
        # Change background of popup window to white
        self.popup.configure(bg="white")

        # Creating content frame
        content_frame = self.popup.get_frame()

        # Dictionary for all the variables
        self.inputs = {}
        self.stage_vars = [
            tk.BooleanVar(False),
            tk.BooleanVar(False),
            tk.BooleanVar(False),
        ]

        # Row 0, Column Titles
        title_labels = ["Select", "Ranges", "Step Size"]
        for i in range(3):
            title = ttk.Label(content_frame, text=title_labels[i], padding=(2, 5, 0, 0))
            title.grid(row=0, column=i, sticky=tk.NSEW)

        # Row 1, 2 - Autofocus Settings
        setting_names = ["coarse", "fine", "robust_fit"]
        setting_labels = ["Coarse", "Fine", "Robust Fit"]
        for i in range(2):
            # Column 0 - Checkboxes
            stage = ttk.Checkbutton(
                content_frame, text=setting_labels[i], variable=self.stage_vars[i]
            )
            stage.grid(row=i + 1, column=0, sticky=tk.NSEW, padx=5)

            # Column 1 - Ranges
            self.inputs[setting_names[i] + "_range"] = LabelInput(
                parent=content_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
                input_args={"from_": 0.0, "to": 50000},
            )
            self.inputs[setting_names[i] + "_range"].grid(
                row=i + 1, column=1, sticky=tk.NSEW, padx=(0, 5), pady=(15, 0)
            )

            # Column 2 - Step Sizes
            self.inputs[setting_names[i] + "_step_size"] = LabelInput(
                parent=content_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
                input_args={"from_": 0.0, "to": 50000},
            )
            self.inputs[setting_names[i] + "_step_size"].grid(
                row=i + 1, column=2, sticky=tk.NSEW, padx=(0, 5), pady=(15, 0)
            )

        # Row 4, Autofocus Button
        self.autofocus_btn = ttk.Button(content_frame, text="Autofocus")
        self.autofocus_btn.grid(row=4, column=2, pady=(0, 10))

        robust_fit = ttk.Checkbutton(
            content_frame, text=setting_labels[2], variable=self.stage_vars[2]
        )
        robust_fit.grid(row=4, column=0, sticky=tk.NSEW, padx=5)

        # Row 5, Plot
        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.coarse = self.fig.add_subplot(211)
        self.coarse.set_title("Coarse Autofocus")
        self.coarse.set_ylabel("DCTS")
        self.coarse.set_xlabel("Focus Position")

        self.fine = self.fig.add_subplot(212)
        self.fine.set_title("Fine Autofocus")
        self.fine.set_ylabel("DCTS")
        self.fine.set_xlabel("Focus Position")

        self.fig.tight_layout()
        canvas = FigureCanvasTkAgg(self.fig, master=content_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(
            row=5, column=0, columnspan=3, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5)
        )

    def get_widgets(self):
        """Returns the dictionary of input widgets.

        Parameters
        ----------
        None

        Returns
        -------
        dict
            Dictionary of all the input widgets.
        """
        return self.inputs
