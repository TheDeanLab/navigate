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
from tkinter import ttk
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import platform

# Third Party Imports

# Local Imports
from navigate.view.custom_widgets.popup import PopUp
from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from navigate.view.custom_widgets.validation import ValidatedCombobox
from navigate.model.data_sources import FILE_TYPES
from navigate.view.custom_widgets.common import CommonMethods

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class AcquirePopUp(CommonMethods):
    """Class creates the popup that is generated when the Acquire button is pressed and
    Save File checkbox is selected."""

    def __init__(self, root, *args, **kwargs):
        """Initialize the AcquirePopUp class

        Parameters
        ----------
        root : tk.Tk
            The root window
        *args
            Variable length argument list
        **kwargs
            Arbitrary keyword arguments
        """
        # Creating popup window with this name and size/placement, PopUp is a Toplevel
        # window
        #: PopUp: The popup window
        if platform.system() == "Windows":
            self.popup = PopUp(
                root, "File Saving Dialog", "450x390+320+180", transient=True
            )
        else:
            self.popup = PopUp(
                root, "File Saving Dialog", "600x430+320+180", transient=True
            )

        # Storing the content frame of the popup, this will be the parent of the widgets
        content_frame = self.popup.get_frame()

        # Formatting
        tk.Grid.columnconfigure(content_frame, "all", weight=1)
        tk.Grid.rowconfigure(content_frame, "all", weight=1)

        # Dictionary for all the variables
        #: dict: Dictionary of all the variables
        self.inputs = {}

        #: dict: Dictionary of all the buttons
        self.buttons = {}

        # Label for entries
        #: ttk.Label: Label for the entries
        self.entries_label = ttk.Label(
            content_frame, text="Please fill out the fields below"
        )
        self.entries_label.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW, pady=5)

        # Creating Entry Widgets
        entry_names = [
            "root_directory",
            "user",
            "tissue",
            "celltype",
            "label",
            "prefix",
            "solvent",
            "file_type",
            "misc",
        ]

        entry_labels = [
            "Root Directory",
            "User",
            "Tissue Type",
            "Cell Type",
            "Label",
            "Prefix",
            "Solvent",
            "File Type",
            "Notes",
        ]

        # Loop for each entry and label
        for i in range(len(entry_names)):
            if entry_names[i] == "misc":
                self.inputs[entry_names[i]] = LabelInput(
                    parent=content_frame,
                    label=entry_labels[i],
                    input_class=ScrolledText,
                    input_args={"wrap": tk.WORD, "width": 40, "height": 10},
                )
            elif entry_names[i] == "file_type":
                self.inputs[entry_names[i]] = LabelInput(
                    parent=content_frame,
                    label=entry_labels[i],
                    input_class=ValidatedCombobox,
                    input_var=tk.StringVar(),
                    label_args={"padding": [0, 0, 30, 0]},
                )
                self.inputs[entry_names[i]].widget.state(["!disabled", "readonly"])
                self.inputs[entry_names[i]].set_values(tuple(FILE_TYPES))
                self.inputs[entry_names[i]].set("TIFF")

            elif entry_names[i] == "solvent":
                self.inputs[entry_names[i]] = LabelInput(
                    parent=content_frame,
                    label=entry_labels[i],
                    input_class=ValidatedCombobox,
                    input_var=tk.StringVar(),
                    label_args={"padding": [0, 0, 36, 0]},
                )
                self.inputs[entry_names[i]].widget.state(["!disabled", "readonly"])
                self.inputs[entry_names[i]].set_values(
                    ("BABB", "Water", "CUBIC", "CLARITY", "uDISCO", "eFLASH")
                )
                self.inputs[entry_names[i]].set("BABB")

            else:
                self.inputs[entry_names[i]] = LabelInput(
                    parent=content_frame,
                    label=entry_labels[i],
                    input_class=ttk.Entry,
                    input_var=tk.StringVar(),
                    input_args={"width": 50},
                )
            self.inputs[entry_names[i]].grid(
                row=i + 1, column=0, columnspan=2, sticky=tk.NSEW, padx=5
            )
            self.inputs[entry_names[i]].label.grid(padx=(0, 20))

        # Formatting
        self.inputs["user"].widget.grid(padx=(53, 0))
        self.inputs["tissue"].widget.grid(padx=(16, 0))
        self.inputs["celltype"].widget.grid(padx=(28, 0))
        self.inputs["prefix"].widget.grid(padx=(46, 0))
        self.inputs["label"].widget.grid(padx=(48, 0))
        self.inputs["misc"].widget.grid(padx=(40, 0))

        # Done and Cancel Buttons
        self.buttons["Cancel"] = ttk.Button(content_frame, text="Cancel Acquisition")
        self.buttons["Cancel"].grid(row=10, column=0, padx=5, sticky=tk.NSEW)

        self.buttons["Done"] = ttk.Button(content_frame, text="Acquire Data")
        self.buttons["Done"].grid(row=10, column=1, padx=(0, 5), sticky=tk.NSEW)
