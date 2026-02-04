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
#

# Standard Library Imports
import logging
from tkinter import messagebox
import os

# Third Party Imports

# Local Imports
from navigate.tools.multipos_table_tools import (
    sign,
    compute_tiles_from_bounding_box,
    calc_num_tiles,
    update_table,
)
from navigate.controller.sub_controllers.gui import GUIController
from navigate.tools.file_functions import save_yaml_file, load_yaml_file
from navigate.config.config import get_navigate_path


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class TilingWizardController(GUIController):
    """Tiling Wizard Controller

    Controller for tiling wizard parameters.
    Gathers the FOV from the camera settings tab and will
    update when user changes this value.
    Set start/end position buttons will grab the stage
    values for the respective axis when pressed and display in popup
    Number of images we need to acquire with our desired
    percent overlap is calculated and then displayed in third column
    """

    def __init__(self, view, parent_controller):
        """Initialize Tiling Wizard Controller

        Parameters
        ----------
        view : object
            GUI element containing widgets and variables to control.
            Likely tk.Toplevel-derived. In this case tiling_wizard_popup.py
        parent_controller : channels_tab_controller
            The controller that creates the popup/this controller.

        """
        super().__init__(view, parent_controller)

        # Getting widgets and buttons and vars of widgets
        #: dict: Dictionary of widgets in the view
        self.widgets = self.view.get_widgets()

        #: dict: Dictionary of buttons in the view
        self.buttons = self.view.get_buttons()

        #: dict: Dictionary of variables in the view
        self.variables = self.view.get_variables()

        #: int: Default percent overlap between tiles
        self._percent_overlap = 10.0  # default to 10% overlap

        #: dict: flags indicating if all the value are correct to set the table
        self.is_validated = {}

        # Initialize widgets to previous values
        #: list: List of axes to iterate over
        stage_axes = (
            self.parent_controller.parent_controller.configuration_controller.stage_axes
        )
        self._axes = list(stage_axes)
        self.is_validated = {axis: True for axis in self._axes}
        self.load_settings()

        # Ref to widgets in other views
        # (Camera Settings, Stage Control Positions, Stack Acq Settings)
        main_view = self.parent_controller.parent_controller.view
        self.cam_settings_widgets = (
            main_view.settings.camera_settings_tab.camera_roi.get_widgets()
        )
        self.stack_acq_widgets = (
            main_view.settings.channels_tab.stack_acq_frame.get_widgets()
        )
        self.stage_position_vars = (
            main_view.settings.stage_control_tab.position_frame.get_variables()
        )
        self.multipoint_table = (
            main_view.settings.multiposition_tab.multipoint_list.get_table()
        )

        # Setting/Tracing Percent Overlay, also handled in update_overlap
        self.variables["percent_overlap"].trace_add(
            "write", lambda *args: self.update_overlap()
        )

        # Trace cam_settings FOV to catch user changes
        # FOV change handled in update_fov
        self.cam_settings_widgets["FOV_X"].get_variable().trace_add(
            "write", lambda *args: self.update_fov("y")
        )
        self.cam_settings_widgets["FOV_Y"].get_variable().trace_add(
            "write", lambda *args: self.update_fov("x")
        )
        # primary z/f
        self.primary_z_axis = self.stack_acq_widgets["z_device"].get().split(" - ")[1]
        self.primary_f_axis = self.stack_acq_widgets["f_device"].get().split(" - ")[1]
        self.stack_acq_widgets["z_device"].get_variable().trace_add(
            "write", lambda *args: self.update_fov("z_device")
        )
        self.stack_acq_widgets["f_device"].get_variable().trace_add(
            "write", lambda *args: self.update_fov("f_device")
        )
        self.stack_acq_widgets["start_position"].get_variable().trace_add(
            "write", lambda *args: self.update_fov("z")
        )
        self.stack_acq_widgets["end_position"].get_variable().trace_add(
            "write", lambda *args: self.update_fov("z")
        )
        self.stack_acq_widgets["start_focus"].get_variable().trace_add(
            "write", lambda *args: self.update_fov("f")
        )
        self.stack_acq_widgets["end_focus"].get_variable().trace_add(
            "write", lambda *args: self.update_fov("f")
        )

        # Calculate distances
        for axis in self._axes:
            self.variables[f"{axis}_start"].trace_add(
                "write", lambda *args, axis=axis: self.calculate_distance(axis)
            )
            self.variables[f"{axis}_end"].trace_add(
                "write", lambda *args, axis=axis: self.calculate_distance(axis)
            )
            # Bind FOV changes
            self.variables[f"{axis}_fov"].trace_add(
                "write", lambda *args, axis=axis: self.calculate_tiles(axis)
            )

            # Calculating Number of Tiles traces
            self.variables[f"{axis}_dist"].trace_add(
                "write", lambda *args, axis=axis: self.calculate_tiles(axis)
            )

        # Populate Table trace
        self.buttons["set_table"].configure(command=self.set_table)

        for ax in self._axes:
            # Start/End buttons
            self.buttons[f"{ax}_start"].configure(
                command=self.position_handler(ax, "start")
            )
            self.buttons[f"{ax}_end"].configure(
                command=self.position_handler(ax, "end")
            )

            # Calculating total tile traces
            self.variables[f"{ax}_tiles"].trace_add(
                "write", lambda *args: self.update_total_tiles()
            )

            # Update widgets to current values in other views
            self.update_fov(ax)

        # Properly Closing Popup with parent controller
        self.view.popup.protocol(
            "WM_DELETE_WINDOW",
            self.close_window,
        )

        self.view.popup.bind("<Escape>", self.close_window)

    def load_settings(self):
        """Load positions from yaml file"""

        # Load positions from yaml file
        load_path = os.path.join(
            get_navigate_path(), "config", "tiling_wizard_settings.yaml"
        )

        if os.path.exists(load_path):
            positions = load_yaml_file(load_path)
            # for key, value in positions.items():
            #     self.variables[key].set(value)
        else:
            positions = {}

        self.variables["percent_overlap"].set(self._percent_overlap)
        self.variables["total_tiles"].set(1)
        stage_step = (
            self.parent_controller.parent_controller.configuration_controller.stage_step
        )
        for ax in self._axes:
            self.variables[f"{ax}_start"].set(positions.get(f"{ax}_start", 0.0))
            self.variables[f"{ax}_end"].set(positions.get(f"{ax}_end", 0.0))
            self.variables[f"{ax}_dist"].set(positions.get(f"{ax}_dist", 0.0))
            if f"{ax}_fov" in positions:
                default_fov = positions.get(f"{ax}_fov", 0.0)
            elif ax == "theta":
                default_fov = stage_step.get("theta", 0.0)
            else:
                default_fov = 0.0
            self.variables[f"{ax}_fov"].set(default_fov)
            self.variables[f"{ax}_tiles"].set(positions.get(f"{ax}_tiles", 1))

    def close_window(self, *args) -> None:
        """Save multiposition information and close the tiling wizard popup

        Save multiposition information to yaml file, and close tiling wizard.
        """
        positions = {key: var.get() for key, var in self.variables.items()}
        save_yaml_file(
            file_directory=os.path.join(get_navigate_path(), "config"),
            content_dict=positions,
            filename="tiling_wizard_settings.yaml",
        )

        # Close the popup
        self.view.popup.dismiss()
        delattr(self.parent_controller, "tiling_wizard_controller")

    def set_table(self):
        """Set the multipoint table to the values in the tiling wizard

        Sets multiposition table with values from tiling wizard after
        populate Multiposition Table button is pressed
        Compute grid will return a list of all position combinations.
        This list is then converted to a
        pandas dataframe which is then set as the new table data.
        The table is then redrawn.
        """

        def sort_vars(a, b):
            """Sort two variables from low to high

            Parameters
            ----------
            a : float
                First variable
            b : float
                Second variable

            Returns
            -------
            a, b : float
                Sorted variables
            """
            if a > b:
                return b, a
            return a, b

        if False in self.is_validated.values():
            messagebox.showwarning(
                title="Navigate",
                message="Can't calculate positions, "
                "please make sure all FOV Dists are correct!",
            )
            return

        tiling_setting = {}
        for axis in self._axes:
            start_pos = float(self.variables[f"{axis}_start"].get())
            stop_pos = float(self.variables[f"{axis}_end"].get())
            tiles = int(self.variables[f"{axis}_tiles"].get())
            fov = float(self.variables[f"{axis}_fov"].get())

            if axis == self.primary_z_axis:
                start_pos -= float(self.stack_acq_widgets["start_position"].get())
                stop_pos -= float(self.stack_acq_widgets["end_position"].get())
            elif axis == self.primary_f_axis:
                start_pos -= float(self.stack_acq_widgets["start_focus"].get())
                stop_pos -= float(self.stack_acq_widgets["end_focus"].get())

            start_pos, stop_pos = sort_vars(start_pos, stop_pos)
            tiling_setting[f"{axis}_start"] = start_pos
            # tiling_setting[f"{axis}_stop"] = stop_pos
            tiling_setting[f"{axis}_tiles"] = tiles
            tiling_setting[f"{axis}_length"] = fov

        if "theta" not in self._axes:
            tiling_setting["theta_start"] = float(
                self.stage_position_vars["theta"].get()
            )
            tiling_setting["theta_tiles"] = 1
            tiling_setting["theta_length"] = 0

        overlap = float(self._percent_overlap) / 100
        columns, table_values = compute_tiles_from_bounding_box(
            overlap=overlap, **tiling_setting
        )

        update_table(self.multipoint_table, table_values, columns)

        # If we have additional axes, create self.d{axis} for each
        # additional axis, to ensure we keep track of the step size
        config = self.parent_controller.parent_controller.configuration
        microscope_name = config["experiment"]["MicroscopeState"]["microscope_name"]
        scope = config["configuration"]["microscopes"][microscope_name]
        coupled_axes = scope["stage"].get("coupled_axes", None)
        if coupled_axes is not None:
            for follower in coupled_axes.values():
                config["experiment"]["MicroscopeState"][
                    f"{follower.lower()}_step_size"
                ] = self.variables[f"{follower.lower()}_fov"].get()

    def update_total_tiles(self):
        """Update the total number of tiles in the tiling wizard

        Sums the tiles for each axis in the tiling wizard.
        Will update when any axis has a tile amount change.
        """

        total_tiles = 1
        for ax in self._axes:
            total_tiles *= float(self.variables[f"{ax}_tiles"].get())

        self.variables["total_tiles"].set(total_tiles)

    def calculate_tiles(self, axis=None):
        """Calculate the number of tiles for a given axis

        Calculates the number of tiles of the acquisition for
        each axis or an individual axis
        Num of Tiles = dist - (overlay * FOV)  /  FOV * (1 - overlay)
        (D-OF)/(F-OF) = N

        Parameters
        ----------
        axis : str
            x, y, z, f axis of stage to calculate.
        """

        if axis not in self._axes + [None]:
            logger.warning(
                f"Controller - Tiling Wizard - Unknown axis {axis}, "
                "skipping calculate_tiles()."
            )
            return

        if axis is not None:
            if not isinstance(axis, list):
                axis = [axis]
        else:
            axis = self._axes

        for ax in axis:
            self.is_validated[ax] = True
            fov_value = self.variables[f"{ax}_fov"].get()
            if not fov_value or "inf" in fov_value:
                self.is_validated[ax] = False
                return
            try:
                dist = abs(float(self.variables[f"{ax}_dist"].get()))  # um
                fov = abs(float(self.variables[f"{ax}_fov"].get()))  # um

                if ax.lower() in ("x", "y", "theta"):
                    # + fov because distance is center of the fov to center of
                    # the fov and so we are covering a distance that is 2 *
                    # 1/2 * fov larger than dist
                    dist += fov

                overlay = (
                    0
                    if ax.lower() == "theta"
                    else float(self._percent_overlap) / 100
                )
                num_tiles = calc_num_tiles(dist, overlay, fov)

                self.variables[f"{ax}_tiles"].set(num_tiles)
            except ValueError as e:
                self.is_validated[ax] = False
                logger.warning(f"Controller - Tiling Wizard - {e}")

    def calculate_distance(self, axis):
        """Calculate the distance for a given axis

        This function will calculate the distance for a given
        axis of the stage when the start or end position is changed
        via the Set buttons

        Parameters
        ----------
        axis : str
            x, y, z axis of stage to calculate
        """

        start = float(self.variables[axis + "_start"].get())
        end = float(self.variables[axis + "_end"].get())
        dist = abs(end - start)
        self.variables[axis + "_dist"].set(dist)

    def update_overlap(self):
        """Update the overlay percentage for the tiling wizard

        Updates percent overlay when a user changes the widget in the popup.
        This value is used for backend calculations.
        The number of tiles will then be recalculated
        """

        try:
            self._percent_overlap = float(self.variables["percent_overlap"].get())
            self.calculate_tiles()
        except ValueError:
            # most likely an empty string was passed
            pass

    def position_handler(self, axis, start_end):
        """Set the start or end position for a given axis

        When the Set [axis] Start/End button is pressed then the
        stage position is polled from the stage controller

        Parameters
        ----------
        axis : str
            x, y, z, f axis that corresponds to stage axis
        start_end : str
            start or end will signify which spinbox gets updated upon button press

        Returns
        -------
        handler : func
            Function for setting positional spinbox based on parameters passed in
        """

        def handler():
            # Force us to get the current stage positions from the stage
            self.parent_controller.parent_controller.execute("stop_stage")

            def set_bounds(axis, start_end):
                # Now set the bounds
                pos = self.stage_position_vars[axis].get()
                self.widgets[axis + "_" + start_end].widget.set(pos)
                # if axis == "z":
                #     setattr(self, f"_f_{start_end}",
                #             self.stage_position_vars["f"].get())

            self.parent_controller.parent_controller.view.after(
                250, lambda: set_bounds(axis, start_end)
            )

        return handler

    def update_fov(self, axis=None):
        """Update the FOV for the tiling wizard

        Grabs the updated FOV if changed by user,
        will recalculate num of tiles for each axis after

        Parameters
        ----------
        axis : str
            Axis
        """

        if axis is None:
            axes = self._axes
        elif isinstance(axis, str):
            if axis == "z_device":
                # get the new primary z axis
                primary_z = self.stack_acq_widgets["z_device"].get().split(" - ")[1]
                if self.primary_z_axis != primary_z:
                    self.variables[f"{primary_z}_fov"].set(
                        self.variables[f"{self.primary_z_axis}_fov"].get()
                    )
                    self.variables[f"{self.primary_z_axis}_fov"].set(0)
                    self.primary_z_axis = primary_z
                return
            elif axis == "f_device":
                # get the new primary f axis
                primary_f = self.stack_acq_widgets["f_device"].get().split(" - ")[1]
                if self.primary_f_axis != primary_f:
                    self.variables[f"{primary_f}_fov"].set(
                        self.variables[f"{self.primary_f_axis}_fov"].get()
                    )
                    self.variables[f"{self.primary_f_axis}_fov"].set(0)
                    self.primary_f_axis = primary_f
                return
            else:
                axes = [axis]

        for ax in axes:
            try:
                # Calculate signed fov
                if ax == "y":
                    y = float(self.cam_settings_widgets["FOV_X"].get()) * sign(
                        float(self.variables["x_end"].get())
                        - float(self.variables["x_start"].get())
                    )
                    axis = "y"
                elif ax == "x":
                    x = float(self.cam_settings_widgets["FOV_Y"].get()) * sign(
                        float(self.variables["y_end"].get())
                        - float(self.variables["y_start"].get())
                    )
                    axis = "x"
                elif ax == "z":
                    z = float(self.stack_acq_widgets["end_position"].get()) - float(
                        self.stack_acq_widgets["start_position"].get()
                    )
                    axis = self.primary_z_axis
                elif ax == "f":
                    f = float(self.stack_acq_widgets["end_focus"].get()) - float(
                        self.stack_acq_widgets["start_focus"].get()
                    )
                    axis = self.primary_f_axis
                elif ax == "theta":
                    continue
                else:
                    continue

                # for ax in self._axes:
                # self._fov[ax] = locals().get(ax)
                self.variables[f"{axis}_fov"].set(
                    abs(locals().get(ax))
                )  # abs(self._fov[ax]))

                self.calculate_tiles(axis)
            except (TypeError, ValueError) as e:
                logger.debug(
                    f"Controller - Tiling Wizard - Caught ValueError: {e}. "
                    f"Declining to update {ax} FOV."
                )
                pass

    def showup(self):
        """Show the tiling wizard

        Brings popup window to front of screen
        """
        self.view.popup.deiconify()
        self.view.popup.attributes("-topmost", 1)
