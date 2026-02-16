# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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
from navigate.view.custom_widgets.validation import ValidatedCombobox, ValidatedSpinbox
from navigate.model.data_sources import FILE_TYPES
from navigate.view.custom_widgets.common import CommonMethods

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


SOLVENTS = ("BABB", "Water", "CUBIC", "CLARITY", "uDISCO", "eFLASH")


class AcquirePopUp(CommonMethods):
    """Class creates the popup that is generated when the Acquire button is pressed and
    Save File checkbox is selected."""

    def __init__(self, root: tk.Tk, configuration: dict = None) -> None:
        """Initialize the AcquirePopUp class

        Parameters
        ----------
        root : tk.Tk
            The root window
        configuration : dict, optional
            The configuration dictionary containing channel information
        """
        #: tk.Tk: The root window
        self.tk = root

        #: dict: Configuration dictionary
        self.configuration = configuration

        #: int: Width of the first column
        self.column1_width = 20

        #: int: Width of the second column
        self.column2_width = 40

        # Calculate the number of entry widgets dynamically
        num_base_entries = 8  # root_directory, user, tissue, celltype, prefix,
        # solvent, file_type
        num_channel_labels = 0

        # Count selected channels for dynamic label entries
        if configuration and "experiment" in configuration:
            channels = (
                configuration["experiment"]
                .get("MicroscopeState", {})
                .get("channels", {})
            )
            num_channel_labels = sum(
                1 for ch_info in channels.values() if ch_info.get("is_selected", False)
            )

        # If no channels selected, we still have 1 label field
        if num_channel_labels == 0:
            num_channel_labels = 1

        total_entries = (
            num_base_entries + num_channel_labels - 1
        )  # -1 because we replace the single label with channel labels

        # Calculate dynamic height: base height + (entries * height_per_entry)
        # Base height includes tabs, buttons, separators, and padding
        # Each entry widget takes approximately 30 pixels
        base_height = 480  # Height for tabs, buttons, separators, and header
        height_per_entry = 30
        calculated_height = base_height + (total_entries * height_per_entry)

        #: PopUp: The popup window
        if platform.system() == "Windows":
            self.global_width = 450
            self.global_height = calculated_height
            self.popup = PopUp(
                root,
                name="File Saving Dialog",
                size=f"{self.global_width}x{self.global_height}+320+180",
                transient=True,
            )
        else:
            self.global_width = 580
            self.global_height = calculated_height
            self.popup = PopUp(
                root,
                name="File Saving Dialog",
                size=f"{self.global_width}x{self.global_height}+320+180",
                transient=True,
            )

        #: dict: Button dictionary.
        self.buttons = {}

        #: dict: Input dictionary.
        self.inputs = {}

        content_frame = self.popup.get_frame()
        content_frame.columnconfigure(index=0, weight=1)
        content_frame.rowconfigure(index=0, weight=1)

        path_entries = ttk.Frame(content_frame, padding=(5, 5, 5, 5))
        tab_frame = ttk.Frame(content_frame, padding=(5, 5, 5, 5))
        button_frame = ttk.Frame(content_frame, padding=(5, 5, 5, 5))
        separator1 = ttk.Separator(content_frame, orient="horizontal")
        separator2 = ttk.Separator(content_frame, orient="horizontal")

        path_entries.grid(row=0, column=0, sticky=tk.NSEW, padx=0, pady=3)
        path_entries.grid_columnconfigure(index=0, weight=1)
        path_entries.grid_rowconfigure(index=1, weight=1)

        separator1.grid(row=1, column=0, sticky=tk.NSEW, padx=0, pady=3)

        tab_frame.grid(row=2, column=0, sticky=tk.NSEW, padx=0, pady=3)
        tab_frame.grid_columnconfigure(index=0, weight=1)
        tab_frame.grid_rowconfigure(index=1, weight=1)

        separator2.grid(row=3, column=0, sticky=tk.NSEW, padx=0, pady=3)

        button_frame.grid(row=4, column=0, sticky=tk.NSEW, padx=0, pady=3)
        button_frame.grid_columnconfigure(index=0, weight=1)
        button_frame.grid_rowconfigure(index=1, weight=1)

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
        row_index = 0
        text = "Please Fill Out the Fields Below"

        #: ttk.Label: Label for the entries
        label = ttk.Label(frame, text=text)
        label.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW, pady=5, padx=0)

        # Creating Entry Widgets
        entry_names = [
            "root_directory",
            "user",
            "tissue",
            "celltype",
        ]

        entry_labels = [
            "Root Directory",
            "User",
            "Tissue Type",
            "Cell Type",
        ]

        # Add dynamic label entries for each selected channel
        selected_channels = []
        if parent.configuration and "experiment" in parent.configuration:
            channels = (
                parent.configuration["experiment"]
                .get("MicroscopeState", {})
                .get("channels", {})
            )
            for channel_name, channel_info in channels.items():
                if channel_info.get("is_selected", False):
                    laser = channel_info.get("laser", "")
                    # Extract wavelength (e.g., "488nm" from "488nm")
                    wavelength = laser
                    selected_channels.append((channel_name, wavelength))
                    entry_names.append(f"label_{wavelength}")
                    entry_labels.append(f"Label ({wavelength})")

        # If no channels found or configuration not provided, use default single label
        if not selected_channels:
            entry_names.append("label")
            entry_labels.append("Label")

        # Add remaining standard entries
        entry_names.extend(["prefix", "solvent", "file_type"])
        entry_labels.extend(["Prefix", "Solvent", "File Type"])

        # Loop for each entry and label
        row_index += 1
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
                row=row_index,
                column=0,
                columnspan=1,
                sticky=tk.NSEW,
                padx=(0, 0),
                pady=(1, 1),
            )

            # Labels
            parent.inputs[entry_names[i]].label.grid(padx=(5, 5))
            parent.inputs[entry_names[i]].label.config(width=parent.column1_width)
            parent.inputs[entry_names[i]].widget.grid(padx=(0, 0), pady=(1, 1))
            row_index += 1


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
        notebook = ttk.Notebook(frame, padding=(5, 2, 5, 2))
        notebook.grid(row=0, column=0, sticky=tk.NSEW)

        tab1 = ttk.Frame(notebook)
        tab1.columnconfigure(index=0, weight=1)

        tab2 = ttk.Frame(notebook)
        tab2.columnconfigure(index=0, weight=1)
        tab2.columnconfigure(index=1, weight=1)
        tab2.columnconfigure(index=2, weight=1)

        notebook.add(tab1, text="Misc. Notes")
        notebook.add(tab2, text="BDV Settings")

        row_index = 0

        text = "All notes are saved in to the header of the image file."

        notes_label = ttk.Label(
            tab1,
            text=text,
            justify=tk.LEFT,
            width=parent.global_width - 30,
            wraplength=parent.global_width - 30,
        )

        notes_label.grid(
            row=row_index,
            column=0,
            columnspan=3,
            rowspan=2,
            sticky=tk.NSEW,
            pady=(5, 5),
        )

        row_index += 2
        separator1 = ttk.Separator(tab1, orient="horizontal")

        separator1.grid(
            row=row_index, column=0, columnspan=3, sticky=tk.NSEW, padx=0, pady=3
        )

        row_index += 1
        self.inputs = {
            "misc": ScrolledText(
                tab1,
                wrap=tk.WORD,
                height=20,
                width=parent.column2_width + parent.column2_width - 35,
            )
        }

        self.inputs["misc"].grid(row=row_index, column=0, columnspan=1, sticky=tk.NSEW)

        row_index = 0
        text = (
            "HDF5, N5, and Zarr files are saved with BDV metadata, "
            "enabling immediate visualization with BigDataViewer. "
            "All angles are in degrees."
        )

        bdv_label = ttk.Label(
            tab2,
            text=text,
            justify=tk.LEFT,
            width=parent.global_width - 40,
            wraplength=parent.global_width - 40,
        )

        bdv_label.grid(
            row=row_index,
            column=0,
            columnspan=3,
            rowspan=2,
            sticky=tk.NSEW,
            pady=(5, 5),
        )

        row_index += 2
        self.inputs["shear_data"] = LabelInput(
            parent=tab2,
            label_pos="left",
            label="Shear",
            input_class=ttk.Checkbutton,
            input_var=tk.BooleanVar(),
            input_args={"onvalue": True, "offvalue": False},
        )
        self.inputs["shear_data"].grid(
            row=row_index,
            column=0,
            columnspan=1,
            sticky=tk.NSEW,
            padx=(5, 5),
            pady=(1, 1),
        )

        values = ["XZ", "YZ", "XY"]
        self.inputs["shear_dimension"] = LabelInput(
            parent=tab2,
            label_pos="top",
            label="Dimension",
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            input_args={"values": values, "state": "readonly"},
        )

        self.inputs["shear_dimension"].grid(
            row=row_index, column=1, columnspan=1, sticky=tk.W, padx=(5, 5), pady=(1, 1)
        )

        self.inputs["shear_angle"] = LabelInput(
            parent=tab2,
            label_pos="top",
            label="Angle",
            input_class=ValidatedSpinbox,
            input_var=tk.StringVar(),
            input_args={
                "from_": 0,
                "to": 360,
                "increment": 1,
            },
        )
        self.inputs["shear_angle"].grid(
            row=row_index, column=2, columnspan=1, sticky=tk.W, padx=(5, 5), pady=(1, 1)
        )

        row_index += 1
        separator1 = ttk.Separator(tab2, orient="horizontal")

        separator1.grid(
            row=row_index, column=0, columnspan=3, sticky=tk.NSEW, padx=0, pady=3
        )

        row_index += 1
        self.inputs["rotate_data"] = LabelInput(
            parent=tab2,
            label_pos="left",
            label="Rotate",
            input_class=ttk.Checkbutton,
            input_var=tk.BooleanVar(),
            input_args={"onvalue": True, "offvalue": False},
        )

        self.inputs["rotate_data"].grid(
            row=row_index,
            column=0,
            columnspan=1,
            sticky=tk.NSEW,
            padx=(5, 5),
            pady=(1, 1),
        )

        # Insert a new frame here, and then add the widgets to that frame
        rotate_notebook = ttk.Notebook(tab2, padding=(5, 2, 5, 2))
        rotate_notebook.grid(row=row_index, column=1, columnspan=2, sticky=tk.NSEW)
        for i in range(3):
            rotate_notebook.columnconfigure(index=i, weight=1)

        self.inputs["rotate_angle_x"] = LabelInput(
            parent=rotate_notebook,
            label_pos="top",
            label="X Angle",
            input_class=ValidatedSpinbox,
            input_var=tk.StringVar(),
            input_args={
                "from_": 0,
                "to": 360,
                "increment": 1,
            },
        )

        self.inputs["rotate_angle_x"].grid(
            row=0, column=0, columnspan=1, sticky=tk.W, padx=(5, 5), pady=(1, 1)
        )

        self.inputs["rotate_angle_y"] = LabelInput(
            parent=rotate_notebook,
            label_pos="top",
            label="Y Angle",
            input_class=ValidatedSpinbox,
            input_var=tk.StringVar(),
            input_args={
                "from_": 0,
                "to": 360,
                "increment": 1,
            },
        )
        self.inputs["rotate_angle_y"].grid(
            row=0, column=1, columnspan=1, sticky=tk.W, padx=(5, 5), pady=(1, 1)
        )

        self.inputs["rotate_angle_z"] = LabelInput(
            parent=rotate_notebook,
            label_pos="top",
            label="Y Angle",
            input_class=ValidatedSpinbox,
            input_var=tk.StringVar(),
            input_args={
                "from_": 0,
                "to": 360,
                "increment": 1,
            },
        )
        self.inputs["rotate_angle_z"].grid(
            row=0, column=2, columnspan=1, sticky=tk.W, padx=(5, 5), pady=(1, 1)
        )

        row_index += 1
        separator1 = ttk.Separator(tab2, orient="horizontal")

        separator1.grid(
            row=row_index, column=0, columnspan=3, sticky=tk.NSEW, padx=0, pady=3
        )

        row_index += 1
        separator2 = ttk.Separator(tab2, orient="horizontal")
        separator2.grid(
            row=row_index, column=0, columnspan=3, sticky=tk.NSEW, padx=0, pady=3
        )

        row_index += 1
        self.inputs["down_sample_data"] = LabelInput(
            parent=tab2,
            label_pos="left",
            label="Downsample",
            input_class=ttk.Checkbutton,
            input_var=tk.BooleanVar(),
            input_args={"onvalue": True, "offvalue": False},
        )

        self.inputs["down_sample_data"].grid(
            row=row_index,
            column=0,
            columnspan=1,
            sticky=tk.NSEW,
            padx=(5, 5),
            pady=(1, 1),
        )

        values = ["1x", "2x", "4x", "8x", "16x", "32x", "64x", "128x"]
        self.inputs["lateral_down_sample"] = LabelInput(
            parent=tab2,
            label_pos="top",
            label="Lateral Downsample",
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            input_args={"values": values, "state": "readonly"},
        )

        self.inputs["lateral_down_sample"].grid(
            row=row_index, column=1, columnspan=1, sticky=tk.W, padx=(5, 5), pady=(1, 1)
        )

        values = ["1x", "2x", "4x", "8x", "16x", "32x", "64x", "128x"]
        self.inputs["axial_down_sample"] = LabelInput(
            parent=tab2,
            label_pos="top",
            label="Axial Downsample",
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            input_args={"values": values, "state": "readonly"},
        )

        self.inputs["axial_down_sample"].grid(
            row=row_index, column=2, columnspan=1, sticky=tk.W, padx=(5, 5), pady=(1, 1)
        )

        row_index += 1
        separator3 = ttk.Separator(tab2, orient="horizontal")
        separator3.grid(
            row=row_index, column=0, columnspan=3, sticky=tk.NSEW, padx=0, pady=3
        )

        row_index += 1
        text = (
            "Down-sampling is accompanied with additional computational overhead "
            "and slows data saving operations. Use with caution. The specified "
            "down-sampling is the maximum value, and intermediate values will "
            "automatically be calculated. "
        )

        bdv_label2 = ttk.Label(
            tab2,
            text=text,
            justify=tk.LEFT,
            width=parent.global_width - 40,
            wraplength=parent.global_width - 40,
        )

        bdv_label2.grid(
            row=row_index,
            column=0,
            columnspan=3,
            rowspan=2,
            sticky=tk.NSEW,
            pady=(5, 5),
        )
