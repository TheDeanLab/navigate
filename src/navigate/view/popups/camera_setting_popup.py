# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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

# Local Imports
from navigate.view.custom_widgets.popup import PopUp
from navigate.view.custom_widgets.hover import HoverButton, HoverCheckButton
from navigate.view.main_window_content.camera_tab import CameraSettingsTab
from navigate.view.theme import get_theme_space_px

# p = __name__.split(".")[1]
# logger = logging.getLogger(p)


class AdvancedCameraSettingPopup:
    """Popup window for advanced camera setting."""

    def __init__(self, root, *args, **kwargs):
        """Initialize the AdvancedCameraSettingPopup class.

        Parameters
        ----------
        root : tkinter.Tk
            Root window of the application.
        args : list
            List of arguments.
        kwargs : dict
            Dictionary of keyword arguments.
        """
        from navigate.view.custom_widgets.popup import PopUp
        from navigate.view.custom_widgets.validation import ValidatedCombobox
        from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput

        #: PopUp: Popup window for the camera settings.
        self.popup = PopUp(
            root,
            name="Advanced Camera Settings",
            size="+320+180",
            top=False,
            transient=False,
        )
        self.popup.resizable(tk.TRUE, tk.TRUE)

        # Creating the frame for the popup
        self.frame = self.popup.content_frame

        #: dict: Dictionary to hold the flip flags for each axis.
        self.flip_flags = {}

        #: dict: Dictionary to hold the flip buttons for each axis.
        self.flip_button = {}

        #: HoverButton: Button to save the settings.
        self.save_button = None

        #: LabelInput: Dropdown for selecting the microscope.
        self.microscope = LabelInput(
            self.frame,
            label_pos="left",
            label="Microscope",
            input_class=ValidatedCombobox,
            input_var=tk.StringVar(),
            label_args={"style": "Title.TLabel"},
            input_args={
                "state": "readonly",
            },
        )
        self.microscope.grid(row=0, column=0, columnspan=2, padx=get_theme_space_px(5), pady=get_theme_space_px(5), sticky="ew")

        #: ttk.Frame: Frame to hold camera control inputs.
        self.camera_control_frame = ttk.Labelframe(self.frame, text="Camera Control")
        self.camera_control_frame.grid(
            row=2, column=0, columnspan=2, sticky=tk.NSEW, padx=get_theme_space_px(10), pady=get_theme_space_px(10)
        )

        #: dict: Holder for column frames (LabelFrames)
        self.column_frames = {}

        #: int: Fixed row height (px) to ensure perfect alignment
        self.row_minsize = 34

        #: dict: widgets
        self.inputs = {}

        #: dict: buttons
        self.buttons = {}

        #: dict: variables
        self.variables = {}

    def populate_view(self, flip_flags: dict) -> None:
        """Populate the view with the camera flip flags.

        Parameters
        ----------
        flip_flags : dict
            A dictionary containing the flip flags for x and y axes.
        """
        # flip flags settings
        image_setting_frame = ttk.LabelFrame(self.frame, text="Imaging Settings")
        image_setting_frame.grid(
            row=3, column=0, columnspan=2, padx=get_theme_space_px(5), pady=get_theme_space_px(5), sticky="nsew"
        )
        # Create column LabelFrames for axis labels and flip flags
        self.column_frames = {
            "axis": ttk.LabelFrame(image_setting_frame, text="Axis"),
            "flip": ttk.LabelFrame(image_setting_frame, text="Flip Direction"),
        }

        # Grid the LabelFrames
        self.column_frames["axis"].grid(row=1, column=0, padx=get_theme_space_px(5), pady=get_theme_space_px(5), sticky="nsew")
        self.column_frames["flip"].grid(row=1, column=1, padx=get_theme_space_px(5), pady=get_theme_space_px(5), sticky="nsew")

        # Make the columns expand
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        # Configure inner columns
        self.column_frames["axis"].grid_columnconfigure(0, weight=1)
        self.column_frames["flip"].grid_columnconfigure(0, weight=1)

        # Camera axes are x and y
        axes = ["x", "y"]

        # Create a row for each axis
        for i, axis in enumerate(axes):
            # Capitalize the axis label
            display_name = axis.upper()

            # Column 1: Axis name label
            axis_lbl = ttk.Label(
                self.column_frames["axis"],
                text=display_name,
                style="BodyBold.TLabel",
            )
            axis_lbl.grid(row=i, column=0, padx=get_theme_space_px(5), pady=get_theme_space_px(0), sticky="ew")

            # Column 2: Flip flag checkbox
            self.flip_flags[axis] = tk.BooleanVar()
            self.flip_button[axis] = HoverCheckButton(
                self.column_frames["flip"],
                variable=self.flip_flags[axis],
            )
            self.flip_button[axis].grid(
                row=i,
                column=0,
                padx=get_theme_space_px(5),
                pady=get_theme_space_px(0),
                sticky="",
            )
            self.flip_button[axis].hover.setdescription(
                f"Reverse the direction of the camera image for the {axis} axis."
            )
            # Set the initial state of the flip flag
            self.flip_flags[axis].set(flip_flags.get(axis, False))

            # Enforce fixed row height
            for fr in self.column_frames.values():
                fr.grid_rowconfigure(i, minsize=self.row_minsize)

        # Save button
        self.save_button = HoverButton(self.frame, text="Save", width=10)
        self.save_button.grid(
            row=4,
            column=1,
            padx=get_theme_space_px(5),
            pady=get_theme_space_px(5),
            sticky="e",
        )
        self.save_button.hover.setdescription("Click to save the camera flip flags.")

        # Center the flip flag checkboxes inside their column
        self.column_frames["flip"].grid_columnconfigure(0, weight=1)

        label_1 = ttk.Label(
            self.camera_control_frame,
            text="Cooling Settings",
            style="Section.TLabel",
        )
        label_1.grid(row=0, column=0, pady=get_theme_space_px(5), padx=get_theme_space_px(5), sticky="w")
        self.inputs["cooling"] = ttk.Combobox(
            self.camera_control_frame, width=12, state="readonly"
        )
        self.inputs["cooling"].grid(row=0, column=1, pady=get_theme_space_px(5), padx=get_theme_space_px(5))
        label_2 = ttk.Label(
            self.camera_control_frame,
            text="Temperature (°C)",
            style="Section.TLabel",
        )
        label_2.grid(row=1, column=0, pady=get_theme_space_px(5), padx=get_theme_space_px(5), sticky="w")
        self.variables["cooling_temperature"] = tk.StringVar()
        self.inputs["cooling_temperature"] = ttk.Entry(
            self.camera_control_frame,
            textvariable=self.variables["cooling_temperature"],
            width=12,
            state="disabled",
        )
        self.inputs["cooling_temperature"].grid(row=1, column=1, pady=get_theme_space_px(5), padx=get_theme_space_px(5))
        self.buttons["refresh_temperature"] = HoverButton(
            self.camera_control_frame, text="Refresh", width=8
        )
        self.buttons["refresh_temperature"].grid(
            row=1, column=2, pady=get_theme_space_px(5), padx=get_theme_space_px(5), sticky="w"
        )
        self.buttons["refresh_temperature"].hover.setdescription(
            "Click to refresh the current cooling temperature."
        )

        label_3 = ttk.Label(
            self.camera_control_frame,
            text="Trigger Source",
            style="Section.TLabel",
        )
        label_3.grid(row=2, column=0, pady=get_theme_space_px(5), padx=get_theme_space_px(5), sticky="w")
        self.inputs["trigger_source"] = ttk.Combobox(
            self.camera_control_frame, width=12, state="readonly"
        )
        self.inputs["trigger_source"].grid(row=2, column=1, pady=get_theme_space_px(5), padx=get_theme_space_px(5))

    def clear_view(self) -> None:
        """Clear the view by destroying all widgets and resetting variables."""
        # destroy camera control inputs
        for widget in self.camera_control_frame.winfo_children():
            widget.destroy()
        self.inputs.clear()

        for widget in self.flip_button.values():
            widget.destroy()
        self.flip_button.clear()
        self.flip_flags.clear()

        # Destroy column frames if they exist
        for fr in self.column_frames.values():
            fr.destroy()
        self.column_frames = {}

        if self.save_button is not None:
            self.save_button.destroy()

        # Clear all remaining widgets except the microscope dropdown and camera control frame
        for widget in self.frame.winfo_children():
            grid_info = widget.grid_info()
            if (
                grid_info
                and widget != self.microscope
                and widget != self.camera_control_frame
            ):
                if int(grid_info.get("row", 0)) > 0:
                    widget.destroy()

        # Reset the widget variables
        self.save_button = None


class CameraSettingPopup:
    """Popup window for camera setting."""

    def __init__(self, root, microscope_name, *args, **kwargs):
        """Initialize the CameraSettingPopup class.

        Parameters
        ----------
        root : tkinter.Tk
            Root window of the application.
        microscope_name : str
            Name of the microscope.
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
            f"{microscope_name} Camera Setting",
            "+320+180",
            top=False,
            transient=False,
        )
        self.popup.resizable(tk.TRUE, tk.TRUE)

        # Storing the content frame of the popup, this will be the parent of
        # the widgets
        content_frame = self.popup.get_frame()
        content_frame.columnconfigure(0, pad=5)
        content_frame.columnconfigure(1, pad=5)
        content_frame.rowconfigure(0, pad=5)
        content_frame.rowconfigure(1, pad=5)
        content_frame.rowconfigure(2, pad=5)

        # Formatting
        tk.Grid.columnconfigure(content_frame, "all", weight=1)
        tk.Grid.rowconfigure(content_frame, "all", weight=1)

        #: dict: Dictionary of all the input widgets.
        self.inputs = {}
        #: dict: Dictionary of all the buttons.
        self.buttons = {}

        # Camera setting tab.
        self.camera_setting = CameraSettingsTab(content_frame)
        self.camera_setting.is_popup = True
        self.camera_setting.is_docked = False
        self.camera_setting.grid(row=0, column=0, sticky=tk.NSEW)

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
