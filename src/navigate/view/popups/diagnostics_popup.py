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


# p = __name__.split(".")[1]
# logger = logging.getLogger(p)


class DiagnosticsPopup(ttk.Frame):
    """Popup window with plots that provide information on the software performance."""

    def __init__(self, root):
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
            width=6,
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

        # Create a label frame
        self.diagnostics_frame = ttk.LabelFrame(
            self.frame,
            padding=(5, 5, 5, 5),
        )
        self.diagnostics_frame.grid(
            row=1,
            column=0,
            padx=5,
            pady=5,
            sticky="NSEW",
        )

        # Create 6 label frames in a 3 row by 2 column grid
        labels = [
            "Time Necessary to Update Image Display",
            "Test-1",
            "Test",
            "Test2",
            "Test3",
            "Test4",
        ]
        counter = 0
        for i in range(2):
            for j in range(3):
                label_frame = ttk.LabelFrame(
                    self.diagnostics_frame,
                    text=labels[counter],
                    padding=(5, 5, 5, 5),
                )
                label_frame.grid(
                    row=i,
                    column=j,
                    padx=5,
                    pady=5,
                    sticky="NSEW",
                )
                # Add a matplotlib.figure.figure to the label frame
                self.inputs[f"diagnostics_{i * 3 + j + 1}"] = Figure(
                    figsize=(4.0, 3.0), tight_layout=True
                )
                self.inputs[f"canvas_{i * 3 + j + 1}"] = FigureCanvasTkAgg(
                    self.inputs[f"diagnostics_{i * 3 + j + 1}"], label_frame
                )
                self.inputs[f"diagnostics_{i * 3 + j + 1}"].add_subplot(111)

                counter += 1

        # Configure the frames to expand
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.diagnostics_frame.grid_columnconfigure(0, weight=1)
        self.diagnostics_frame.grid_columnconfigure(1, weight=1)
        self.diagnostics_frame.grid_rowconfigure(0, weight=1)
        self.diagnostics_frame.grid_rowconfigure(1, weight=1)
        self.diagnostics_frame.grid_rowconfigure(2, weight=1)

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


if __name__ == "__main__":
    root = tk.Tk()
    diagnostics_popup = DiagnosticsPopup(root)
    root.mainloop()
