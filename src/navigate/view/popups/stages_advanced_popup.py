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
import tkinter as tk
from tkinter import ttk


# Local Imports
from navigate.view.custom_widgets.popup import PopUp
from navigate.view.custom_widgets.validation import ValidatedSpinbox, ValidatedCombobox
from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from navigate.view.custom_widgets.hover import HoverButton, HoverCheckButton


class AdvancedStageParametersPopup:
    """Class creates the popup to set advanced stage parameters."""

    def __init__(self, root, *args, **kwargs):
        """Initialize the CameraSettingPopup class.

        Parameters
        ----------
        root : tkinter.Tk
            Root window of the application.
        args : list
            List of arguments.
        kwargs : dict
            Dictionary of keyword arguments.
        """
        # Creating popup window with this name and size/placement, PopUp is a
        # Toplevel window
        #: PopUp: Popup window for the camera view.
        self.popup = PopUp(
            root,
            name="Advanced Stage Parameters",
            size="+320+180",
            top=False,
            transient=False,
        )
        self.popup.resizable(tk.TRUE, tk.TRUE)

        # Creating the frame for the popup
        self.frame = self.popup.content_frame

        #: dict: Dictionary to hold the buttons for updating limits.
        self.buttons = {}

        #: dict: Dictionary to hold the spinboxes for stage limits.
        self.spinboxes = {}

        #: dict: Dictionary to hold the flip flags for each stage.
        self.flip_flags = {}

        #: dict: Dictionary to hold the flip buttons for each stage.
        self.flip_button = {}

        #: BooleanVar: Variable to hold the state of the stage limits checkbox.
        self.enable_stage_limits_var = None

        #: Checkbutton: Checkbox for the stage limits.
        self.stage_limits_enabled = None

        #: HoverCheckButton: Button to save the limits.
        self.save_button = None

        #: LabelInput: Dropdown for selecting the microscope.
        self.microscope = None

        #: HoverCheckButton: Checkbutton for NI Galvo stage.
        self.ni_galvo_stage = None

        #: BooleanVar: Variable to hold the state of the NI Galvo stage checkbox.
        self.ni_galvo_flag = None

    def populate_view(
        self, stages: list, min: dict, max: dict, flip_axes: dict, ni_stage: bool
    ) -> None:
        """Populate the view with the stages.

        Add the widgets to the view for each stage in alphabetical order.
        Creates a row for each stage with: stage name, min limit spinbox,
        update min button, max limit spinbox, and update max button.

        Parameters
        ----------
        stages : list
            The list of stage names as strings.
        min : dict
            A dictionary containing the minimum limits for each stage.
        max : dict
            A dictionary containing the maximum limits for each stage.
        flip_axes : dict
            A dictionary containing the flip flags for each stage.
        ni_stage : bool
            A boolean indicating if the NI Galvo stage is being used.
        """
        button_width = 6

        # Sort stages alphabetically
        sorted_stages = sorted(stages)

        # Create a dropdown menu for selecting which microscope.
        self.microscope = LabelInput(
            self.frame,
            label_pos="left",
            label="Microscope",
            input_class=ValidatedCombobox,
            input_var=tk.StringVar(),
            label_args={"font": ("Arial", 12, "bold")},
            input_args={
                "state": "readonly",
            },
        )
        self.microscope.grid(row=0, column=0, columnspan=7, padx=5, pady=5, sticky="ew")

        # Create column headers
        tk.Label(self.frame, text="Stage", font=("Arial", 10, "bold")).grid(
            row=1, column=0, padx=5, pady=5, sticky="NSEW"
        )

        tk.Label(
            self.frame, text="Minimum Stage Limit", font=("Arial", 10, "bold")
        ).grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="NSEW")

        tk.Label(
            self.frame, text="Maximum Stage Limit", font=("Arial", 10, "bold")
        ).grid(row=1, column=3, columnspan=2, padx=5, pady=5, sticky="NSEW")

        tk.Label(self.frame, text="Stage Offsets", font=("Arial", 10, "bold")).grid(
            row=1, column=5, columnspan=1, padx=5, pady=5, sticky="NSEW"
        )

        tk.Label(self.frame, text="Reverse Direction", font=("Arial", 10, "bold")).grid(
            row=1, column=6, columnspan=1, padx=5, pady=5, sticky="NSEW"
        )
        # Create a row for each stage
        for i, stage_name in enumerate(sorted_stages, start=1):

            # Column 1: Stage name label
            tk.Label(self.frame, text=stage_name).grid(
                row=i + 2, column=0, padx=5, pady=2, sticky="w"
            )

            # Column 2: Minimum limit spinbox
            self.spinboxes[stage_name + "_min"] = ValidatedSpinbox(
                self.frame,
                from_=-100000,
                to=100000,
                width=10,
                format="%.3f",
                increment=0.1,
            )
            self.spinboxes[stage_name + "_min"].set(min.get(stage_name, 0.0))
            self.spinboxes[stage_name + "_min"].grid(
                row=i + 2, column=1, padx=5, pady=2
            )
            self.spinboxes[stage_name + "_min"].hover.setdescription(
                "The desired minimum limit for the stage."
            )

            # Column 3: Update minimum button
            self.buttons[stage_name + "_min"] = HoverButton(
                self.frame, text="Update", width=button_width
            )
            self.buttons[stage_name + "_min"].grid(row=i + 2, column=2, padx=5, pady=2)
            self.buttons[stage_name + "_min"].hover.setdescription(
                "Click to update the minimum limit for this stage to the current "
                "position."
            )

            # Column 4: Maximum limit spinbox
            self.spinboxes[stage_name + "_max"] = ValidatedSpinbox(
                self.frame,
                from_=-100000,
                to=100000,
                width=10,
                format="%.3f",
                increment=0.1,
            )
            self.spinboxes[stage_name + "_max"].set(max.get(stage_name, 0.0))
            self.spinboxes[stage_name + "_max"].grid(
                row=i + 2, column=3, padx=5, pady=2
            )
            self.spinboxes[stage_name + "_max"].hover.setdescription(
                "The desired maximum limit for the stage."
            )

            # Column 5: Update maximum button
            self.buttons[stage_name + "_max"] = HoverButton(
                self.frame, text="Update", width=button_width
            )
            self.buttons[stage_name + "_max"].grid(row=i + 2, column=4, padx=5, pady=2)
            self.buttons[stage_name + "_max"].hover.setdescription(
                "Click to update the maximum limit for this stage to the current "
                "position."
            )

            # Column 6: Offsets
            self.spinboxes[stage_name + "_offset"] = ValidatedSpinbox(
                self.frame,
                from_=-100000,
                to=100000,
                width=10,
                format="%.3f",
                increment=0.1,
            )
            self.spinboxes[stage_name + "_offset"].set(min.get(stage_name, 0.0))
            self.spinboxes[stage_name + "_offset"].grid(
                row=i + 2, column=5, padx=5, pady=2
            )
            self.spinboxes[stage_name + "_offset"].hover.setdescription(
                f"The relative offset between different microscope instances for the "
                f"{stage_name} axis."
            )

            # Column 7: Flip flags.
            self.flip_flags[stage_name] = tk.BooleanVar()

            self.flip_button[stage_name] = HoverCheckButton(
                self.frame,
                variable=self.flip_flags[stage_name],
            )

            self.flip_button[stage_name].grid(
                row=i + 2,
                column=6,
                columnspan=1,
                padx=5,
                pady=5,
                sticky="",
            )
            self.flip_button[stage_name].hover.setdescription(
                f"Reverse the direction of the stage movement for the {stage_name} "
                "axis. "
            )
            # Set the initial state of the flip flag.
            self.flip_flags[stage_name].set(flip_axes.get(stage_name, False))

        # Provide a checkbox to disable the stage limits.
        self.enable_stage_limits_var = tk.BooleanVar()
        self.stage_limits_enabled = HoverCheckButton(
            self.frame,
            text="Stage Limits Enabled",
            variable=self.enable_stage_limits_var,
        )
        self.stage_limits_enabled.grid(
            row=len(sorted_stages) + 3,
            column=0,
            columnspan=2,
            padx=5,
            pady=5,
            sticky="w",
        )
        self.stage_limits_enabled.hover.setdescription(
            "Enable or disable the stage limits. If disabled, the limits will not be "
            "enforced."
        )

        # NI Galvo Flag
        self.ni_galvo_flag = tk.BooleanVar()
        self.ni_galvo_stage = HoverCheckButton(
            self.frame,
            text="Analog Stage",
            variable=self.ni_galvo_flag,
        )
        self.ni_galvo_stage.grid(
            row=len(sorted_stages) + 3,
            column=2,
            columnspan=2,
            padx=5,
            pady=5,
            sticky="w",
        )
        self.ni_galvo_flag.set(ni_stage)

        # Save button.
        self.save_button = HoverButton(self.frame, text="Save", width=button_width)
        self.save_button.grid(
            row=len(sorted_stages) + 3,
            column=6,
            columnspan=1,
            padx=5,
            pady=5,
            sticky="e",
        )
        self.save_button.hover.setdescription(
            "Click to save the limits for all stages."
        )

        # Center the flip flag checkboxes
        self.frame.grid_columnconfigure(6, weight=1)
