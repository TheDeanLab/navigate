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
import os

# Third Party Imports

# Local Imports
from navigate.config.config import update_config_dict, get_navigate_path
from navigate.tools.file_functions import save_yaml_file
from navigate.view.popups.stages_advanced_popup import AdvancedStageParametersPopup
from navigate.controller.configuration_controller import ConfigurationController

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class AdvancedStageParametersController:
    """Controller for the Stage Limits popup."""

    def __init__(
        self,
        popup: AdvancedStageParametersPopup,
        parent_controller: "Controller",
        *args,
        **kwargs,
    ) -> None:
        """Initialize the AdvancedStageParametersController class.

        Parameters
        ----------
        root : tk.Tk
            The root window
        popup : AdvancedStageParametersPopup
            The popup window for stage limits
        parent_controller : Controller
            The parent controller that manages this popup
        *args
            Variable length argument list
        **kwargs
            Arbitrary keyword arguments
        """

        # Initialize the parent controller
        self.parent_controller = parent_controller

        #: PopUp: Popup window for the stage limits.
        self.view = popup

        #: ConfigurationController: Controller for the local configuration.
        self.local_config_controller = ConfigurationController(
            self.parent_controller.configuration
        )

        # Populate the list of microscopes in the dropdown.
        self.view.microscope.set_values(self.local_config_controller.microscope_list)

        #: str: The current microscope name.
        self.current_microscope = self.local_config_controller.microscope_name

        # Set the current microscope in the dropdown.
        self.view.microscope.set(self.current_microscope)

        #: dict: Stage configuration dictionary for the current microscope.
        self.stage_dict = self.local_config_controller.microscope_config["stage"]

        self.update_microscope(in_initialization=True)

        # Add a trace to the microscope dropdown to detect microscope changes.
        self.view.microscope.variable.trace_add("write", self.update_microscope)

        # Configure traces for the widgets in the popup.
        self._configure_widget_traces()

        # Configure traces for closing the window or pressing escape.
        self.view.popup.protocol("WM_DELETE_WINDOW", self.close_popup)
        self.view.popup.bind("<Escape>", lambda event: self.close_popup())

        logger.debug("Stage limits popup initialized.")

    def save_stage_parameters(self) -> None:
        """Save the current stage parameters to the configuration file."""

        # Update the stage dictionary.
        update_config_dict(
            manager=self.parent_controller.manager,
            parent_dict=self.parent_controller.configuration["configuration"][
                "microscopes"
            ][self.current_microscope],
            config_name="stage",
            new_config=self.stage_dict,
        )

        # Save the updated configuration to a YAML file.
        save_yaml_file(
            file_directory=os.path.join(get_navigate_path(), "config"),
            content_dict=self.parent_controller.configuration["configuration"],
            filename="configuration.yaml",
        )

        # Update the configuration controller with the new configuration.
        self.parent_controller.configuration_controller.update_configuration()

        # Reinitialize the stage controller with the new configuration.
        self.parent_controller.stage_controller.initialize()

    def toggle_limits(self, *args) -> None:
        """Toggle the stage limits on or off."""

        # Get the current state of the checkbox.
        limits_enabled = self.view.enable_stage_limits_var.get()

        # Update the stage controller with the new state.
        self.parent_controller.execute("stage_limits", limits_enabled)

        # Update the menu item state.
        if limits_enabled is True:
            self.parent_controller.menu_controller.disable_stage_limits.set(0)
        else:
            self.parent_controller.menu_controller.disable_stage_limits.set(1)

    def flip_axis(self, axis: str) -> None:
        """Flip the stage axis in the configuration.

        Parameters
        ----------
        axis : str
            The axis to flip, e.g., 'x', 'y', or 'z'.
        """
        # Update the loaded configuration.
        self.parent_controller.configuration["configuration"]["microscopes"][
            self.current_microscope
        ]["stage"][f"flip_{axis}"] = self.view.flip_flags[axis].get()

        # Update our local stage dictionary with the new flip flag.
        self.stage_dict[f"flip_{axis}"] = self.view.flip_flags[axis].get()
        logger.debug(
            f"Updating {axis} flip flag to {self.stage_dict[f'flip_{axis}']}..."
        )

    def update_axis(self, axis: str) -> None:
        """Get the current stage position, and update the stage limits in the
        configuration. Only applied when someone presses the "update" button.

        axis: str
            The stage limit to update, e.g., 'x_min', 'y_max', etc.
        """
        # Identify the axis and whether it's a minimum or maximum limit.
        axis, min_or_max = axis.split("_")

        # Get our current position.
        self.parent_controller.execute("query_stages")
        current_position = self.parent_controller.stage_controller.get_position()

        # Update the popup window.
        self.view.spinboxes[f"{axis}_{min_or_max}"].set(current_position[axis])

        # Update the loaded configuration.
        self.parent_controller.configuration["configuration"]["microscopes"][
            self.current_microscope
        ]["stage"][f"{axis}_{min_or_max}"] = current_position[axis]

        # Update the stage dictionary with the new limit and/or flip flag.
        self.stage_dict[f"{axis}_{min_or_max}"] = current_position[axis]

        logger.debug(
            f"Updating {axis} {min_or_max} limits to" f" {current_position[axis]}..."
        )

    def close_popup(self) -> None:
        """Close the popup window."""
        self.save_stage_parameters()
        self.view.popup.destroy()

        if hasattr(self.parent_controller, "stage_limits_popup_controller"):
            del self.parent_controller.stage_limits_popup_controller

        logger.debug("Stage limits popup closed and sub-controller deleted.")

    def update_microscope(self, *args, in_initialization=False) -> None:
        """Update the microscope configuration when the microscope is changed.

        Parameters
        ----------
        in_initialization : bool, optional
            If True, this method is called during initialization and does not
            save the previous stage parameters.
        """
        # Save the configuration for the previous microscope before switching.
        if not in_initialization:
            self.save_stage_parameters()

        # Get the current microscope from the dropdown.
        self.current_microscope = self.view.microscope.get()
        self.view.clear_view()

        # Update the local configuration controller with the new microscope.
        self.local_config_controller.change_microscope(
            microscope_name=self.current_microscope
        )

        # Set the number of stage axes for the most recently selected microscope.
        num_stages = self.local_config_controller.stage_axes

        # Get the minimum and maximum limits for each stage axis.
        min_limits = self.local_config_controller.get_stage_position_limits(
            suffix="_min"
        )

        max_limits = self.local_config_controller.get_stage_position_limits(
            suffix="_max"
        )

        # Get the current flip flags for each stage axis.
        current_flip_flags = self.local_config_controller.stage_flip_flags

        # Initialize the view with the number of stages and their limits
        self.view.populate_view(num_stages, min_limits, max_limits, current_flip_flags)

        # Reconfigure traces for the new widgets
        self._configure_widget_traces()

    def update_spinboxes(self, axis) -> None:
        """Update the spinboxes for the stage limits.

        Parameters
        ----------
        axis : str
            The axis to update, e.g., 'x', 'y', or 'z'.
        """
        # Get the current value from the spinbox.
        value = int(self.view.spinboxes[axis].get())

        # Update the loaded configuration.
        self.parent_controller.configuration["configuration"]["microscopes"][
            self.current_microscope
        ]["stage"][axis] = value

        # Update our local stage dictionary with the new value.
        self.stage_dict[axis] = value

        logger.debug(f"Updating {axis} limit to {value}...")

    def _configure_widget_traces(self):
        """Configure traces and commands for widgets after they're created."""
        # Configure the spinboxes for each stage limit.
        for key, value in self.view.buttons.items():
            value.configure(command=lambda k=key: self.update_axis(k))

        # Configure the reverse flags for each stage axis.
        for key, value in self.view.flip_flags.items():
            value.trace_add("write", lambda *args, k=key: self.flip_axis(k))

        # Configure trace for minimum limit, maximum limit, and offset spinboxes.
        for key, value in self.view.spinboxes.items():
            value.bind("<FocusOut>", lambda event, k=key: self.update_spinboxes(k))

        # Save button trace.
        self.view.save_button.configure(command=self.save_stage_parameters)

        # See if the stage limits are currently enabled or disabled.
        self.stage_limits_enabled = self.parent_controller.stage_controller.stage_limits
        self.view.enable_stage_limits_var.set(self.stage_limits_enabled)

        # Checkbox trace for enabling/disabling stage limits.
        self.view.enable_stage_limits_var.trace_add("write", self.toggle_limits)
