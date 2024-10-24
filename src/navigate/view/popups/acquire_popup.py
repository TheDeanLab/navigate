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


SOLVENTS = ("BABB", "Water", "CUBIC", "CLARITY", "uDISCO", "eFLASH")


class AcquirePopUp(CommonMethods):
    """Class creates the popup that is generated when the Acquire button is pressed and
    Save File checkbox is selected."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the AcquirePopUp class

        Parameters
        ----------
        root : tk.Tk
            The root window
        """
        #: int: Width of the first column
        self.column1_width = 20

        #: int: Width of the second column
        self.column2_width = 40

        #: PopUp: The popup window
        if platform.system() == "Windows":
            self.popup = PopUp(
                root, "File Saving Dialog", "450x390+320+180", transient=True
            )
        else:
            self.popup = PopUp(
                root, "File Saving Dialog", "600x500+320+180", transient=True
            )

        #: dict: Button dictionary.
        self.buttons = {}

        #: dict: Input dictionary.
        self.inputs = {}

        # Storing the content frame of the popup, this will be the parent of the widgets
        content_frame = self.popup.get_frame()

        path_entries = ttk.Frame(content_frame, padding=(0, 0, 0, 0))
        tab_frame = ttk.Frame(content_frame, padding=(0, 0, 0, 0))
        button_frame = ttk.Frame(content_frame, padding=(0, 0, 0, 0))
        separator1 = ttk.Separator(content_frame, orient="horizontal")
        separator2 = ttk.Separator(content_frame, orient="horizontal")

        path_entries.grid(row=0, column=0, sticky=tk.NSEW, padx=0, pady=3)
        separator1.grid(row=1, column=0, sticky=tk.NSEW, padx=0, pady=3)
        tab_frame.grid(row=2, column=0, sticky=tk.NSEW, padx=0, pady=3)
        separator2.grid(row=3, column=0, sticky=tk.NSEW, padx=0, pady=3)
        button_frame.grid(row=4, column=0, sticky=tk.NSEW, padx=0, pady=3)

        #: ButtonFrame: ButtonFrame object
        self.button_frame = ButtonFrame(parent=self, frame=button_frame)

        #: EntryFrame: EntryFrame object
        self.path_frame = EntryFrame(parent=self, frame=path_entries)

        #: TabFrame: TabFrame object
        self.tab_frame = TabFrame(parent=self, frame=tab_frame)


class ButtonFrame:
    def __init__(self, parent: AcquirePopUp, frame: ttk.Frame) -> None:
        """Initialize the ButtonFrame

        Parameters
        ----------
        parent : AcquirePopUp
            The AcquirePopup window.
        frame : ttk.Frame
            The AcquirePopup Window.
        """

        width = int((parent.column1_width + parent.column2_width - 10) / 2)
        parent.buttons["Cancel"] = ttk.Button(
            frame, text="Cancel Acquisition", width=width
        )
        parent.buttons["Done"] = ttk.Button(frame, text="Acquire Data", width=width)
        parent.buttons["Cancel"].grid(row=0, column=0, padx=5, sticky=tk.NSEW)
        parent.buttons["Done"].grid(row=0, column=1, padx=5, sticky=tk.NSEW)


class EntryFrame:
    def __init__(self, parent: AcquirePopUp, frame: ttk.Frame) -> None:
        """Initialize the EntryFrame

        Parameters
        ----------
        parent : AcquirePopUp
            The AcquirePopup window.
        frame : ttk.Frame
            The EntryFrame Window.
        """
        text = "Please Fill Out the Fields Below"

        #: ttk.Label: Label for the entries
        label = ttk.Label(frame, text=text)
        label.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW, pady=5, padx=5)

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
        ]

        # Loop for each entry and label
        for i in range(len(entry_names)):
            if entry_names[i] == "file_type":
                parent.inputs[entry_names[i]] = LabelInput(
                    parent=frame,
                    label=entry_labels[i],
                    input_class=ValidatedCombobox,
                    input_var=tk.StringVar(),
                )
                parent.inputs[entry_names[i]].widget.state(["!disabled", "readonly"])
                parent.inputs[entry_names[i]].set_values(tuple(FILE_TYPES))
                parent.inputs[entry_names[i]].set("TIFF")

            elif entry_names[i] == "solvent":
                parent.inputs[entry_names[i]] = LabelInput(
                    parent=frame,
                    label=entry_labels[i],
                    input_class=ValidatedCombobox,
                    input_var=tk.StringVar(),
                )
                parent.inputs[entry_names[i]].widget.state(["!disabled", "readonly"])
                parent.inputs[entry_names[i]].set_values(SOLVENTS)
                parent.inputs[entry_names[i]].set("BABB")

            else:
                parent.inputs[entry_names[i]] = LabelInput(
                    parent=frame,
                    label=entry_labels[i],
                    input_class=ttk.Entry,
                    input_var=tk.StringVar(),
                    input_args={"width": parent.column2_width},
                )

            # Widgets
            parent.inputs[entry_names[i]].grid(
                row=i + 1, column=0, columnspan=1, sticky=tk.NSEW
            )

            # Labels
            parent.inputs[entry_names[i]].label.grid(padx=(5, 0))
            parent.inputs[entry_names[i]].label.config(width=parent.column1_width)

        # Formatting
        parent.inputs["user"].widget.grid(padx=(0, 0))
        parent.inputs["tissue"].widget.grid(padx=(0, 0))
        parent.inputs["celltype"].widget.grid(padx=(0, 0))
        parent.inputs["prefix"].widget.grid(padx=(0, 0))
        parent.inputs["label"].widget.grid(padx=(0, 0))


class TabFrame:
    def __init__(self, parent: AcquirePopUp, frame: ttk.Frame) -> None:
        """Initialize the TabFrame

        Parameters
        ----------
        parent : AcquirePopUp
            The AcquirePopup window.
        frame : ttk.Frame
            The TabFrame Window.
        """

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        parent.inputs["misc"] = LabelInput(
            parent=frame,
            label="Notes",
            input_class=ScrolledText,
            input_args={
                "wrap": tk.WORD,
                "width": parent.column2_width + 10,
                "height": 10,
            },
        )

        # LabelInput
        parent.inputs["misc"].grid(row=0, column=1, columnspan=2, sticky=tk.NSEW)

        # Label
        parent.inputs["misc"].label.grid(padx=(5, 0))
        parent.inputs["misc"].label.config(width=parent.column1_width)

        # Widget
        parent.inputs["misc"].widget.grid(padx=(0, 0), sticky=tk.NSEW)
