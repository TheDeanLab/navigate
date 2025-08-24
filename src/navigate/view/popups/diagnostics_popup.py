# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

# Third Party Imports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Local Imports
from navigate.view.custom_widgets.popup import PopUp
from navigate.view.custom_widgets.hover import HoverButton


class DiagnosticsPopup(ttk.Frame):
    """Popup window with plots that provide information on the software performance."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the DiagnosticsPopupWindow class.

        Parameters
        ----------
        root : tkinter.Tk
            Root window of the application.
        """
        ttk.Frame.__init__(self, root)

        #: PopUp: Resizable popup window for the diagnostics display.
        self.popup = PopUp(
            root,
            name="Navigate Diagnostics",
            size="+320+180",
            top=False,
            transient=False,
        )
        self.popup.resizable(tk.TRUE, tk.TRUE)

        #: dict: Dictionary to hold buttons in the popup.
        self.buttons = {}

        #: dict: Dictionary to hold input widgets in the popup.
        self.inputs = {}

        #: dict: Dictionary to hold label frames in the popup.
        self.label_frame = {}

        #: ttk.Labelframe: Frame for the diagnostics popup.
        self.frame = self.popup.get_frame()
        self.frame.grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="NSEW",
        )

        # Create a button to update the plots.
        self.buttons["update"] = HoverButton(
            self.frame,
            text="Update",
            width=10,
        )
        self.buttons["update"].grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="W",
        )
        self.buttons["update"].hover.setdescription(
            "Update the diagnostic plots using the most recent data."
        )

        # Create a button to save an image of the diagnostics.
        self.buttons["save_image"] = HoverButton(
            self.frame,
            text="Save Image",
            width=10,
        )
        self.buttons["save_image"].grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
            sticky="W",
        )
        self.buttons["save_image"].hover.setdescription(
            "Save a screenshot of the performance diagnostics."
        )

        self.buttons["close"] = HoverButton(
            self.frame,
            text="Close",
            width=10,
        )
        self.buttons["close"].grid(
            row=0,
            column=2,
            padx=5,
            pady=5,
            sticky="W",
        )
        self.buttons["close"].hover.setdescription("Close the diagnostics window.")

        # Create a label frame
        self.diagnostics_frame = ttk.LabelFrame(
            self.frame,
            padding=(5, 5, 5, 5),
        )
        self.diagnostics_frame.grid(
            row=1,
            column=0,
            columnspan=3,
            padx=5,
            pady=5,
            sticky="NSEW",
        )

        for i in range(8):
            self.add_plot_figure("")

        # Configure the frames to expand
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.diagnostics_frame.grid_columnconfigure(0, weight=1)
        self.diagnostics_frame.grid_columnconfigure(1, weight=1)
        self.diagnostics_frame.grid_columnconfigure(2, weight=1)  # Added
        self.diagnostics_frame.grid_columnconfigure(3, weight=1)  # Added
        self.diagnostics_frame.grid_rowconfigure(0, weight=1)
        self.diagnostics_frame.grid_rowconfigure(1, weight=1)

    # Add plot figure
    def add_plot_figure(self, title):
        counter = sum(k.startswith("canvas_") for k in self.inputs)
        i = counter // 4
        j = counter % 4
        self.label_frame[counter + 1] = ttk.LabelFrame(
            self.diagnostics_frame,
            text=title,
            padding=(5, 5, 5, 5),
        )
        self.label_frame[counter + 1].grid(
            row=i,
            column=j,
            padx=5,
            pady=5,
            sticky="NSEW",
        )
        # Add a matplotlib.figure.figure to the label frame
        self.inputs[f"diagnostics_{counter + 1}"] = Figure(
            figsize=(4.0, 3.0), tight_layout=True
        )
        self.inputs[f"canvas_{counter + 1}"] = FigureCanvasTkAgg(
            self.inputs[f"diagnostics_{counter + 1}"], self.label_frame[counter + 1]
        )
        self.inputs[f"diagnostics_{counter + 1}"].add_subplot(111)

    # Getters
    def get_variables(self):
        """Get the variables tied to the widgets.

        This function returns a dictionary of all the variables that are tied to each
        widget name.

        The key is the widget name, value is the variable associated.

        Returns
        -------
        dict
            Dictionary of all the variables that are tied to each widget name.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get_variable()
        return variables

    def get_widgets(self):
        """Get the dictionary that holds the input widgets.

        This function returns the dictionary that holds the input widgets.
        The key is the widget name, value is the LabelInput class that has all the data.

        Returns
        -------
        dict
            Dictionary that holds the input widgets.
        """
        return self.inputs

    def get_buttons(self):
        """Get the dictionary that holds the buttons.

        This function returns the dictionary that holds the buttons.
        The key is the button name, value is the button.

        Returns
        -------
        dict
            Dictionary that holds the buttons.
        """
        return self.buttons
