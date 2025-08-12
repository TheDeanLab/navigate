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
        self.microscope = LabelInput(
            self.frame,
            label_pos="left",
            label="Microscope",
            input_class=ValidatedCombobox,
            input_var=tk.StringVar(),
            label_args={"font": ("Arial", 14, "bold")},
            input_args={
                "state": "readonly",
            },
        )
        self.microscope.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        #: dict: Holder for column frames (LabelFrames)
        self.column_frames = {}

        #: dict: Hold per-row widgets to normalize row heights across LabelFrames
        self._row_widgets = {}

        #: int: Fixed row height (px) to ensure perfect alignment across columns
        self.row_minsize = 34

    def populate_view(
        self,
        stages: list,
        min_dict: dict,
        max_dict: dict,
        flip_axes: dict,
        offsets: dict,
        home_dict: dict,
    ) -> None:
        """Populate the view with the stages.

        Add the widgets to the view for each stage in alphabetical order.
        Creates a row for each stage with: stage name, min_dict limit spinbox,
        update min_dict button, max limit spinbox, and update max button.

        Parameters
        ----------
        stages : list
            The list of stage names as strings.
        min_dict : dict
            A dictionary containing the minimum limits for each stage.
        max_dict : dict
            A dictionary containing the maximum limits for each stage.
        flip_axes : dict
            A dictionary containing the flip flags for each stage.
        offsets : dict
            A dictionary containing the offsets for each stage.
        """
        button_width = 6

        # Sort stages alphabetically
        sorted_stages = sorted(stages)

        # Create column LabelFrames to group each functional area
        self.column_frames = {
            "stage": ttk.LabelFrame(self.frame, text="Stage"),
            "min": ttk.LabelFrame(self.frame, text="Minimum Stage Limit"),
            "max": ttk.LabelFrame(self.frame, text="Maximum Stage Limit"),
            "home": ttk.LabelFrame(self.frame, text="Home Position"),
            "offset": ttk.LabelFrame(self.frame, text="Stage Offsets"),
            "flip": ttk.LabelFrame(self.frame, text="Reverse Direction"),
        }

        # Grid the LabelFrames in one row so they look like columns
        self.column_frames["stage"].grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.column_frames["min"].grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        self.column_frames["max"].grid(row=1, column=2, padx=5, pady=5, sticky="nsew")
        self.column_frames["home"].grid(row=1, column=3, padx=5, pady=5, sticky="nsew")
        self.column_frames["offset"].grid(
            row=1, column=4, padx=5, pady=5, sticky="nsew"
        )
        self.column_frames["flip"].grid(row=1, column=5, padx=5, pady=5, sticky="nsew")

        # Make the columns expand nicely
        for c in range(6):
            self.frame.grid_columnconfigure(c, weight=1)

        # Inside each framed column, set reasonable inner column weights
        # (min/max/home groups have two inner columns: value + Update button)
        for key in ("min", "max", "home"):
            self.column_frames[key].grid_columnconfigure(0, weight=1)
            self.column_frames[key].grid_columnconfigure(1, weight=0)
        self.column_frames["stage"].grid_columnconfigure(0, weight=1)
        self.column_frames["offset"].grid_columnconfigure(0, weight=1)
        self.column_frames["flip"].grid_columnconfigure(0, weight=1)

        # Create a row for each stage
        for i, stage_name in enumerate(sorted_stages):

            # Capitalize the first letter of the stage name
            display_name = stage_name.capitalize()

            # Column 1: Stage name label
            stage_lbl = tk.Label(
                self.column_frames["stage"],
                text=display_name,
                font=("Arial", 10, "bold"),
            )
            stage_lbl.grid(row=i, column=0, padx=5, pady=0, sticky="ew")

            # collect row widgets for height normalization
            self._row_widgets.setdefault(i, []).append(stage_lbl)

            # Column 2: Minimum limit spinbox
            self.spinboxes[stage_name + "_min"] = ValidatedSpinbox(
                self.column_frames["min"],
                from_=-100000,
                to=100000,
                width=10,
                format="%.0f",
                increment=1,
            )
            self.spinboxes[stage_name + "_min"].set(min_dict.get(stage_name, 0.0))
            self.spinboxes[stage_name + "_min"].grid(row=i, column=0, padx=5, pady=0)
            self.spinboxes[stage_name + "_min"].hover.setdescription(
                "The desired minimum limit for the stage."
            )
            self._row_widgets[i].append(self.spinboxes[stage_name + "_min"])

            # Column 3: Update minimum button
            self.buttons[stage_name + "_min"] = HoverButton(
                self.column_frames["min"], text="Update", width=button_width
            )
            self.buttons[stage_name + "_min"].grid(row=i, column=1, padx=5, pady=0)
            self.buttons[stage_name + "_min"].hover.setdescription(
                "Click to update the minimum limit for this stage to the current "
                "position."
            )
            self._row_widgets[i].append(self.buttons[stage_name + "_min"])

            # Column 4: Maximum limit spinbox
            self.spinboxes[stage_name + "_max"] = ValidatedSpinbox(
                self.column_frames["max"],
                from_=-100000,
                to=100000,
                width=10,
                format="%.0f",
                increment=1,
            )
            self.spinboxes[stage_name + "_max"].set(max_dict.get(stage_name, 0.0))
            self.spinboxes[stage_name + "_max"].grid(row=i, column=0, padx=5, pady=0)
            self.spinboxes[stage_name + "_max"].hover.setdescription(
                "The desired maximum limit for the stage."
            )
            self._row_widgets[i].append(self.spinboxes[stage_name + "_max"])

            # Column 5: Update maximum button
            self.buttons[stage_name + "_max"] = HoverButton(
                self.column_frames["max"], text="Update", width=button_width
            )
            self.buttons[stage_name + "_max"].grid(row=i, column=1, padx=5, pady=0)
            self.buttons[stage_name + "_max"].hover.setdescription(
                "Click to update the maximum limit for this stage to the current "
                "position."
            )
            self._row_widgets[i].append(self.buttons[stage_name + "_max"])

            # Column 6: Home position spinbox
            self.spinboxes[stage_name + "_home"] = ValidatedSpinbox(
                self.column_frames["home"],
                from_=-100000,
                to=100000,
                width=10,
                format="%.0f",
                increment=1,
                required=False,
            )

            # If the home_dict does not have the stage, set it to an empty string. We
            # want to make sure we don't by default set it to a position where there
            # is a crash hazard. Replace None or "None" with "" just in case.
            home_position = home_dict.get(stage_name, "")
            if home_position is None or home_position == "None":
                home_position = ""
            self.spinboxes[stage_name + "_home"].set(home_position)
            self.spinboxes[stage_name + "_home"].grid(row=i, column=0, padx=5, pady=0)
            self.spinboxes[stage_name + "_home"].hover.setdescription(
                "The desired home position for the stage."
            )
            self._row_widgets[i].append(self.spinboxes[stage_name + "_home"])

            # Column 7: Update home button
            self.buttons[stage_name + "_home"] = HoverButton(
                self.column_frames["home"], text="Update", width=button_width
            )
            self.buttons[stage_name + "_home"].grid(row=i, column=1, padx=5, pady=0)
            self.buttons[stage_name + "_home"].hover.setdescription(
                "Click to update the home position for this stage to the current "
                "position."
            )
            self._row_widgets[i].append(self.buttons[stage_name + "_home"])

            # Column 8: Offsets
            self.spinboxes[stage_name + "_offset"] = ValidatedSpinbox(
                self.column_frames["offset"],
                from_=-100000,
                to=100000,
                width=10,
                format="%.0f",
                increment=1,
            )
            self.spinboxes[stage_name + "_offset"].set(offsets.get(stage_name, 0.0))
            self.spinboxes[stage_name + "_offset"].grid(row=i, column=0, padx=5, pady=0)
            self.spinboxes[stage_name + "_offset"].hover.setdescription(
                f"The relative offset between different microscope instances for the "
                f"{stage_name} axis."
            )
            self._row_widgets[i].append(self.spinboxes[stage_name + "_offset"])

            # Column 9: Flip flags.
            self.flip_flags[stage_name] = tk.BooleanVar()
            self.flip_button[stage_name] = HoverCheckButton(
                self.column_frames["flip"],
                variable=self.flip_flags[stage_name],
            )
            self.flip_button[stage_name].grid(
                row=i,
                column=0,
                columnspan=1,
                padx=5,
                pady=0,
                sticky="",
            )
            self.flip_button[stage_name].hover.setdescription(
                f"Reverse the direction of the stage movement for the {stage_name} "
                "axis. "
            )
            # Set the initial state of the flip flag.
            self.flip_flags[stage_name].set(flip_axes.get(stage_name, False))
            self._row_widgets[i].append(self.flip_button[stage_name])

        # Enforce a fixed row height so rows line up exactly across columns
        for r in self._row_widgets.keys():
            for fr in self.column_frames.values():
                fr.grid_rowconfigure(r, minsize=self.row_minsize)

        # Provide a checkbox to disable the stage limits.
        style = ttk.Style()
        style.configure("Custom.TCheckbutton", font=("Arial", 10, "bold"))
        self.enable_stage_limits_var = tk.BooleanVar()
        self.stage_limits_enabled = HoverCheckButton(
            self.frame,
            text="Stage Limits Enabled",
            variable=self.enable_stage_limits_var,
            style="Custom.TCheckbutton",
        )
        self.stage_limits_enabled.grid(
            row=2,
            column=0,
            columnspan=3,
            padx=5,
            pady=5,
            sticky="w",
        )
        self.stage_limits_enabled.hover.setdescription(
            "Enable or disable the stage limits. If disabled, the limits will not be "
            "enforced."
        )

        # Save button.
        self.save_button = HoverButton(self.frame, text="Save", width=button_width)
        self.save_button.grid(
            row=2,
            column=5,
            columnspan=1,
            padx=5,
            pady=5,
            sticky="e",
        )
        self.save_button.hover.setdescription(
            "Click to save the limits for all stages."
        )

        # Center the flip flag checkboxes inside their column
        self.column_frames["flip"].grid_columnconfigure(0, weight=1)

    def clear_view(self) -> None:
        """Clear the view by destroying all widgets and resetting variables."""
        for widget_type in [self.spinboxes, self.buttons, self.flip_button]:
            for widget in widget_type.values():
                widget.destroy()
            widget_type.clear()
        self.flip_flags.clear()

        # Destroy column frames (LabelFrames) if they exist
        for fr in self.column_frames.values():
            fr.destroy()
        self.column_frames = {}

        for widget_type in [
            self.stage_limits_enabled,
            self.save_button,
        ]:
            if widget_type is not None:
                widget_type.destroy()

        # Clear all remaining widgets except the microscope dropdown
        # This removes stage labels and headers that aren't stored in dictionaries
        for widget in self.frame.winfo_children():
            grid_info = widget.grid_info()
            if grid_info and widget != self.microscope:
                # Keep row 0 (microscope dropdown), clear everything else
                if int(grid_info.get("row", 0)) > 0:
                    widget.destroy()

        # Reset per-row widgets
        self._row_widgets = {}

        # Reset the widget variables to None
        self.stage_limits_enabled = None
        self.save_button = None
