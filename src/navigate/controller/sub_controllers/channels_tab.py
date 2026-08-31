# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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
#

# Standard Library Imports
import logging
import datetime
from typing import Optional, Dict, Any

# Third Party Imports
import numpy as np
import tkinter as tk

import navigate

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.controller.sub_controllers.channels_settings import (
    ChannelSettingController,
)
from navigate.controller.sub_controllers.tiling import TilingWizardController
from navigate.view.main_window_content.channels_tab import ChannelsTab
from navigate.view.popups.tiling_wizard_popup import TilingWizardPopup

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ChannelsTabController(GUIController):
    """Controller for the channels tab in the main window."""

    def __init__(
        self,
        view: ChannelsTab,
        parent_controller: Optional["navigate.controller.controller.Controller"],
    ) -> None:
        """Initialize the ChannelsTabController.

        Parameters
        ----------
        view : ChannelsTab
            The ChannelsTab Window.
        parent_controller : navigate.controller.controller.Controller
            The parent controller of this controller.
        """
        super().__init__(view, parent_controller)

        #: bool: Whether the user has selected to save the data.
        self.is_save = False

        #: str: The current acquisition mode.
        self.mode = "stop"

        #: bool: Whether the controller is in the initialization phase.
        self.in_initialization = True

        # sub-controllers
        self.channel_setting_controller = ChannelSettingController(
            self.view.channel_widgets_frame,
            self,
            self.parent_controller.configuration_controller,
        )

        self.view.stack_timepoint_frame.exp_time_spinbox.set_precision(0)

        #: dict: The widgets in the stack acquisition settings frame.
        self.stack_acq_widgets = self.view.stack_acq_frame.get_widgets()

        #: dict: The values in the stack acquisition settings frame.
        self.stack_acq_vals = self.view.stack_acq_frame.get_variables()

        #: dict: The buttons in the stack acquisition settings frame.
        self.stack_acq_buttons = self.view.stack_acq_frame.get_buttons()

        # stack acquisition event binds
        self.stack_acq_vals["step_size"].trace_add("write", self.update_z_steps)
        self.stack_acq_vals["start_position"].trace_add("write", self.update_z_steps)
        self.stack_acq_vals["end_position"].trace_add("write", self.update_z_steps)
        self.stack_acq_vals["start_focus"].trace_add("write", self.update_z_steps)
        self.stack_acq_vals["z_device"].trace_add(
            "write", self.update_additional_stacking_axes
        )
        self.stack_acq_vals["f_device"].trace_add(
            "write", self.update_additional_stacking_axes
        )
        self.stack_acq_buttons["set_start"].configure(
            command=self.update_start_position
        )
        self.stack_acq_buttons["set_end"].configure(command=self.update_end_position)

        # stack acquisition_variables
        #: float: The z origin of the stack.
        self.z_origin = 0

        #: float: The focus origin of the stack.
        self.focus_origin = 0

        #: float: The filter wheel delay.
        self.filter_wheel_delay = None

        #: dict: The microscope state dictionary.
        self.microscope_state_dict = {}

        #: dict: The GUI range settings used as non-stage fallbacks.
        self._spinbox_range_limit_settings = {}

        # laser/stack cycling event binds
        self.stack_acq_vals["cycling"].trace_add("write", self.update_cycling_setting)

        # time point setting variables
        temp = self.view.stack_timepoint_frame

        #: dict: Dictionary of time point settings.
        self.timepoint_vals = {
            "is_save": temp.save_data,
            "timepoints": temp.exp_time_spinval,
            "stack_acq_time": temp.stack_acq_spinval,
            "stack_pause": temp.stack_pause_spinval,
            "experiment_duration": temp.total_time_spinval,
            "timepoint_interval": temp.timepoint_interval_spinval,
        }

        # time point event binds
        self.timepoint_vals["is_save"].trace_add("write", self.update_save_setting)
        self.timepoint_vals["timepoints"].trace_add(
            "write", lambda *args: self.update_timepoint_setting()
        )
        self.timepoint_vals["stack_pause"].trace_add(
            "write", lambda *args: self.update_timepoint_setting()
        )

        # Multi Position Acquisition
        #: bool: Whether the user has selected to use multi-position.
        self.is_multiposition = False

        #: bool: cache multi-position flag
        self.is_multiposition_cache = False

        #: bool: Whether the user has selected to use multi-position.
        self.is_multiposition_val = self.view.multipoint_frame.on_off
        self.is_multiposition_val.trace_add("write", self.toggle_multiposition)

        self.view.multipoint_frame.buttons["tiling"].configure(
            command=self.launch_tiling_wizard
        )

        # Waveform Parameters
        self.view.quick_launch.buttons["waveform_parameters"].configure(
            command=self.launch_waveform_parameters
        )

        # Autofocus Settings
        self.view.quick_launch.buttons["autofocus_button"].configure(
            command=self.launch_autofocus_settings
        )

        self.initialize()

    def initialize(self) -> None:
        """Initializes widgets and gets other necessary configuration.

        The `initialize` method in the `ChannelsTabController` class is responsible
        for setting up the initial configuration and state of the channels tab in the
        main window.
        """
        config = self.parent_controller.configuration_controller
        self.channel_setting_controller.rebuild_view()
        self.stack_acq_widgets["cycling"].widget["values"] = ["Per Z", "Per Stack"]

        # Set the default stage for acquiring a z-stack.
        z_stages = config.get_stages_by_axis("z")
        self.stack_acq_widgets["z_device"].widget["values"] = z_stages
        if len(z_stages) >= 1:
            self.stack_acq_widgets["z_device"].widget.current(0)

        f_stages = config.get_stages_by_axis("f")
        self.stack_acq_widgets["f_device"].widget["values"] = f_stages
        if len(f_stages) >= 1:
            self.stack_acq_widgets["f_device"].widget.current(0)

        axes = config.stage_axes
        axes = [axis for axis in axes if axis not in ("x", "y", "theta")]
        devices_dict = {}
        for axis in axes:
            temp = config.get_stages_by_axis(axis)
            for device in temp:
                device_name, axis = device.split(" - ")
                devices_dict[axis] = device_name
        self.view.stack_acq_frame.create_additional_stack_widgets(axes, devices_dict)

        self.filter_wheel_delay = [
            config.filter_wheel_setting_dict[i]["filter_wheel_delay"]
            for i in range(config.number_of_filter_wheels)
        ]
        self.channel_setting_controller.initialize()
        self.set_spinbox_range_limits(self.parent_controller.configuration["gui"])
        self.show_verbose_info("channels tab has been initialized")

    def populate_experiment_values(self) -> None:
        """Distribute initial MicroscopeState values to this and sub-controllers and
        associated views.

        The populate_experiment_values method in the ChannelsTabController class is
        responsible for distributing initial MicroscopeState values to this and
        sub-controllers and associated views. It sets the initial values for various
        settings, validates the configuration for multi-position settings,
        and updates the GUI accordingly.

        """
        self.in_initialization = True
        self.microscope_state_dict = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]
        if self.microscope_state_dict["step_size"] < 0:
            self.microscope_state_dict["step_size"] = -self.microscope_state_dict[
                "step_size"
            ]
        self.set_info(self.stack_acq_vals, self.microscope_state_dict)
        self.set_info(self.timepoint_vals, self.microscope_state_dict)

        # set advanced stack acquistion settings
        for axis in ["z", "f"]:
            devices = self.stack_acq_widgets[f"{axis}_device"].widget["values"]
            idx = 0
            for i, device in enumerate(devices):
                if device.endswith(
                    self.microscope_state_dict.get(f"primary_{axis}_axis", axis)
                ):
                    idx = i
                    break
            self.stack_acq_widgets[f"{axis}_device"].widget.current(idx)

        secondary_stack_settings = self.microscope_state_dict.get(
            "secondary_stack_settings", {}
        )
        variable_dict = self.view.stack_acq_frame.additional_stack_setting_variables
        for axis in secondary_stack_settings.keys():
            index_axis = f"stack_{axis}"
            if index_axis in variable_dict:
                variable_dict[index_axis].set(True)
                self.view.stack_acq_frame.update_setting_widgets(axis)()
                variable_dict[f"{axis}_offset"].set(secondary_stack_settings[axis])

        self.update_additional_stacking_axes()

        # check configuration for multi-position settings
        self.is_multiposition_val.set(self.microscope_state_dict["is_multiposition"])
        self.is_multiposition_cache = self.is_multiposition
        self.toggle_multiposition()

        # validate
        self.view.stack_timepoint_frame.stack_pause_spinbox.trigger_focusout_validation()
        self.view.stack_timepoint_frame.exp_time_spinbox.trigger_focusout_validation()

        if self.microscope_state_dict["stack_cycling_mode"] not in [
            "per_z",
            "per_stack",
        ]:
            self.microscope_state_dict["stack_cycling_mode"] = "per_stack"
        self.stack_acq_vals["cycling"].set(
            "Per Z"
            if self.microscope_state_dict["stack_cycling_mode"] == "per_z"
            else "Per Stack"
        )
        if self.microscope_state_dict.get("speed", "") not in ["Auto", "Fixed"]:
            self.stack_acq_vals["speed"].set("Auto")

        self.channel_setting_controller.populate_experiment_values(
            self.microscope_state_dict["channels"]
        )

        # after initialization
        self.in_initialization = False
        self.channel_setting_controller.in_initialization = False
        # get primary z and f axis
        primary_z_axis = self.microscope_state_dict.get("primary_z_axis", "z")
        primary_f_axis = self.microscope_state_dict.get("primary_f_axis", "f")
        # update z and f position
        self.z_origin = self.parent_controller.configuration["experiment"][
            "StageParameters"
        ][primary_z_axis]
        self.focus_origin = self.parent_controller.configuration["experiment"][
            "StageParameters"
        ][primary_f_axis]
        self.update_stack_position_limits()
        self.update_z_steps()

        self.show_verbose_info("Channels tab has been set new values")

    def set_spinbox_range_limits(self, settings: Dict[str, Any]) -> None:
        """Sets range limits for various spinbox widgets based on the provided settings.

        This method configures the minimum, maximum, and increment values for the
        spinbox widgets in the stack acquisition settings frame and the time point
        settings frame based on the provided configuration settings.

        Parameters
        ----------
        settings : Dict[str, Any]
            dictionary of settings from configuration file
        """

        self._spinbox_range_limit_settings = settings

        # Z-Stack Step Size
        self.stack_acq_widgets["step_size"].widget.configure(
            from_=settings.get("stack_acquisition", {})
            .get("step_size", {})
            .get("min", 0.01),
            to=settings.get("stack_acquisition", {})
            .get("step_size", {})
            .get("max", 1000),
            increment=settings.get("stack_acquisition", {})
            .get("step_size", {})
            .get("step", 0.01),
        )

        self.update_stack_position_limits(settings)

        # Stack Pause Duration
        self.view.stack_timepoint_frame.stack_pause_spinbox.configure(
            from_=settings.get("time", {}).get("stack_pause", {}).get("min", 0),
            to=settings.get("time", {}).get("stack_pause", {}).get("max", 100),
            increment=settings.get("time", {}).get("stack_pause", {}).get("step", 1),
        )

        # Timepoints
        self.view.stack_timepoint_frame.exp_time_spinbox.configure(
            from_=settings.get("time", {}).get("timepoints", {}).get("min", 1),
            to=settings.get("time", {}).get("timepoints", {}).get("max", 5000),
            increment=settings.get("time", {}).get("timepoints", {}).get("step", 1),
        )

        # Channel settings
        self.channel_setting_controller.set_spinbox_range_limits(settings)

    def _stage_limits_enabled(self) -> bool:
        """Return whether stack widgets should honor configured stage limits."""

        stage_controller = getattr(self.parent_controller, "stage_controller", None)
        if stage_controller is not None:
            return bool(stage_controller.stage_limits)

        return bool(
            self.parent_controller.configuration["experiment"]
            .get("StageParameters", {})
            .get("limits", True)
        )

    def _get_stack_axis(self, device_name: str, fallback_axis: str) -> str:
        """Return the axis suffix from a stack device combobox value."""

        device = self.stack_acq_vals.get(device_name)
        if device is None:
            return fallback_axis

        value = device.get()
        if not value:
            return fallback_axis

        try:
            return value.split(" - ")[1]
        except IndexError:
            return fallback_axis

    def _get_gui_stack_range(
        self, settings: dict, setting_name: str
    ) -> tuple[float, float]:
        """Return stack range fallback limits from GUI configuration."""

        stack_settings = settings.get("stack_acquisition", {})
        setting = stack_settings.get(setting_name, {})
        return (
            float(setting.get("min", -1000)),
            float(setting.get("max", 1000)),
        )

    def _get_gui_stack_step(self, settings: dict, setting_name: str) -> float:
        """Return stack range increment from GUI configuration."""

        return float(
            settings.get("stack_acquisition", {}).get(setting_name, {}).get("step", 1)
        )

    def _get_relative_stage_limits(
        self, axis: str, origin: float
    ) -> Optional[tuple[float, float]]:
        """Return stage limits relative to the current stack origin."""

        config = self.parent_controller.configuration_controller
        min_limits = config.get_stage_position_limits("_min")
        max_limits = config.get_stage_position_limits("_max")
        if axis not in min_limits or axis not in max_limits:
            return None

        try:
            return float(min_limits[axis]) - origin, float(max_limits[axis]) - origin
        except (TypeError, ValueError):
            return None

    def _get_stack_position_range(
        self,
        axis: str,
        origin: float,
        settings: dict,
        setting_name: str,
    ) -> tuple[float, float]:
        """Return widget range, preferring relative stage limits when enabled."""

        gui_range = self._get_gui_stack_range(settings, setting_name)
        if not self._stage_limits_enabled():
            return gui_range

        stage_range = self._get_relative_stage_limits(axis, origin)
        return gui_range if stage_range is None else stage_range

    def update_stack_position_limits(
        self, settings: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update stack start/end widgets from stage limits or GUI fallback ranges."""

        if settings is None:
            settings = (
                self._spinbox_range_limit_settings
                or self.parent_controller.configuration["gui"]
            )
        else:
            self._spinbox_range_limit_settings = settings

        stack_positions = [
            ("start_position", "z_device", "z", self.z_origin, "z_start_pos"),
            ("end_position", "z_device", "z", self.z_origin, "z_end_pos"),
            ("start_focus", "f_device", "f", self.focus_origin, "f_start_pos"),
            ("end_focus", "f_device", "f", self.focus_origin, "f_end_pos"),
        ]
        for (
            widget_name,
            device_name,
            fallback_axis,
            origin,
            setting_name,
        ) in stack_positions:
            axis = self._get_stack_axis(device_name, fallback_axis)
            from_value, to_value = self._get_stack_position_range(
                axis, float(origin), settings, setting_name
            )
            self.stack_acq_widgets[widget_name].widget.configure(
                from_=from_value,
                to=to_value,
                increment=self._get_gui_stack_step(settings, setting_name),
            )

    def set_mode(self, mode: str) -> None:
        """Change acquisition mode.

        The set_mode method changes the acquisition mode and updates the state of
        various widgets accordingly

        Parameters
        ----------
        mode : str
            acquisition mode
        """

        # image_mode: imaging mode, e.g., "live", "single", "z-stack", "customized"
        # stack acquisition settings are disabled in "live" and "single" mode.
        image_mode = self.microscope_state_dict["image_mode"]
        self.mode = mode
        self.channel_setting_controller.set_mode(mode)

        # state_readonly = "readonly" if mode == "stop" else "disabled"
        if mode != "stop":
            state = "disabled"
        elif image_mode == "live" or image_mode == "single":
            state = "disabled"
        else:
            state = "normal"
        for widget_name in [
            "start_position",
            "start_focus",
            "end_position",
            "end_focus",
            "step_size",
        ]:
            self.stack_acq_widgets[widget_name].widget["state"] = state
        for widget_name in ["cycling", "z_device", "f_device", "speed"]:
            self.stack_acq_widgets[widget_name].widget["state"] = (
                "readonly" if state == "normal" else "disabled"
            )
        for widget_name in self.view.stack_acq_frame.additional_stack_setting_variables:
            if widget_name.startswith("stack_"):
                self.stack_acq_widgets[widget_name]["state"] = state
            elif widget_name.endswith("_offset"):
                self.stack_acq_widgets[widget_name]["state"] = state
        if state == "normal":
            self.update_additional_stacking_axes()

        self.view.stack_timepoint_frame.save_check["state"] = (
            "normal" if image_mode == "single" and mode == "stop" else state
        )
        self.view.stack_timepoint_frame.stack_pause_spinbox["state"] = state
        self.view.stack_timepoint_frame.exp_time_spinbox["state"] = state

        # multi-position flag
        if mode == "stop":
            self.is_multiposition_val.set(self.is_multiposition_cache)
        else:
            self.is_multiposition_cache = self.is_multiposition
            if mode == "customized":
                self.is_multiposition_val.set(False)

        if image_mode == "customized" or mode != "stop":
            self.disable_multiposition_btn()
        else:
            self.enable_multiposition_btn()

        self.show_verbose_info("acquisition mode has been changed to", mode)

    def update_z_steps(self, *_: tuple[str]) -> None:
        """Recalculates the number of slices that will be acquired in a z-stack.

        Requires GUI to have start position, end position, or step size changed.
        Sets the number of slices in the model and the GUI. Sends the current values
        to central/parent controller

        Parameters
        ----------
        _ : tuple[str]
            Values is a tuple of strings. e.g., ('PY_VAR0', '', 'write')
        """

        # won't do any calculation when initialization
        if self.in_initialization:
            return

        # Calculate the number of slices and set GUI
        try:
            # validate the spin box's value
            start_position = float(self.stack_acq_vals["start_position"].get())
            end_position = float(self.stack_acq_vals["end_position"].get())
            step_size = float(self.stack_acq_vals["step_size"].get())
            # Reject non-positive values independently of the configured minimum.
            if step_size <= 0 or step_size < self.stack_acq_widgets[
                "step_size"
            ].widget.cget("from"):
                self.stack_acq_vals["number_z_steps"].set(0)
                self.microscope_state_dict["abs_z_start"] = 0
                self.microscope_state_dict["abs_z_end"] = 0
                # self.stack_acq_vals["abs_z_start"].set(0)
                # self.stack_acq_vals["abs_z_end"].set(0)
                return
        except tk.TclError:
            self.stack_acq_vals["number_z_steps"].set(0)
            self.microscope_state_dict["abs_z_start"] = 0
            self.microscope_state_dict["abs_z_end"] = 0
            # self.stack_acq_vals["abs_z_start"].set(0)
            # self.stack_acq_vals["abs_z_end"].set(0)
            return
        except (KeyError, AttributeError):
            logger.error("Error caught: updating z_steps")
            return

        number_z_steps = int(
            np.ceil(np.abs((end_position - start_position) / step_size))
        )
        self.stack_acq_vals["number_z_steps"].set(number_z_steps)

        # get the primary z-stack and focus axis
        primary_z_stage = self.stack_acq_vals["z_device"].get()
        primary_z_axis = primary_z_stage.split(" - ")[1]

        # Shift the start/stop positions by the relative position
        flip_flags = self.parent_controller.configuration_controller.stage_flip_flags
        if flip_flags[primary_z_axis]:
            self.microscope_state_dict["abs_z_start"] = self.z_origin + end_position
            self.microscope_state_dict["abs_z_end"] = self.z_origin + start_position
            # self.stack_acq_vals["abs_z_start"].set(self.z_origin + end_position)
            # self.stack_acq_vals["abs_z_end"].set(self.z_origin + start_position)
        else:
            self.microscope_state_dict["abs_z_start"] = self.z_origin + start_position
            self.microscope_state_dict["abs_z_end"] = self.z_origin + end_position
            # self.stack_acq_vals["abs_z_start"].set(self.z_origin + start_position)
            # self.stack_acq_vals["abs_z_end"].set(self.z_origin + end_position)

        # update experiment MicroscopeState dict
        self.microscope_state_dict["start_position"] = start_position
        self.microscope_state_dict["end_position"] = end_position
        self.microscope_state_dict["step_size"] = step_size * (
            -1 if flip_flags[primary_z_axis] else 1
        )
        self.microscope_state_dict["number_z_steps"] = number_z_steps
        self.stack_acq_vals["bottom"].set(self.microscope_state_dict["abs_z_start"])
        self.stack_acq_vals["top"].set(self.microscope_state_dict["abs_z_end"])

        try:
            self.microscope_state_dict["start_focus"] = self.stack_acq_vals[
                "start_focus"
            ].get()
        except tk.TclError:
            self.microscope_state_dict["start_focus"] = 0
        try:
            self.microscope_state_dict["end_focus"] = self.stack_acq_vals[
                "end_focus"
            ].get()
        except tk.TclError:
            self.microscope_state_dict["end_focus"] = 0
        self.microscope_state_dict["stack_z_origin"] = self.z_origin
        self.microscope_state_dict["stack_focus_origin"] = self.focus_origin

        self.update_timepoint_setting()
        self.show_verbose_info(
            "stack acquisition settings on channels tab have been changed and "
            "recalculated"
        )

    def update_start_position(self, *_: tuple[str]) -> None:
        """Get new z starting position from current stage parameters.

        Parameters
        ----------
        _ : tuple[str]
            Values is a tuple of strings. e.g., ('PY_VAR0', '', 'write')
        """
        # get the primary z-stack and focus axis
        primary_z_stage = self.stack_acq_vals["z_device"].get()
        primary_z_axis = primary_z_stage.split(" - ")[1]
        primary_f_stage = self.stack_acq_vals["f_device"].get()
        primary_f_axis = primary_f_stage.split(" - ")[1]
        # We have a new origin
        self.z_origin = self.parent_controller.configuration["experiment"][
            "StageParameters"
        ][primary_z_axis]
        self.focus_origin = self.parent_controller.configuration["experiment"][
            "StageParameters"
        ][primary_f_axis]
        self.update_stack_position_limits()

        flip_flags = self.parent_controller.configuration_controller.stage_flip_flags
        if flip_flags[primary_z_axis]:
            self.stack_acq_vals["end_position"].set(0)
            self.stack_acq_vals["end_focus"].set(0)
        else:
            self.stack_acq_vals["start_position"].set(0)
            self.stack_acq_vals["start_focus"].set(0)

        # Propagate parameter changes to the GUI
        self.update_z_steps()

    def update_end_position(self, *_: tuple[str]) -> None:
        """Get new z ending position from current stage parameters

        Parameters
        ----------
        _ : tuple[str]
            Values is a tuple of strings. e.g., ('PY_VAR0', '', 'write')

        """
        # get the primary z-stack and focus axis
        primary_z_stage = self.stack_acq_vals["z_device"].get()
        primary_z_axis = primary_z_stage.split(" - ")[1]
        primary_f_stage = self.stack_acq_vals["f_device"].get()
        primary_f_axis = primary_f_stage.split(" - ")[1]
        # Grab current values
        z_end = self.parent_controller.configuration["experiment"]["StageParameters"][
            primary_z_axis
        ]
        focus_end = self.parent_controller.configuration["experiment"][
            "StageParameters"
        ][primary_f_axis]

        z_start = self.z_origin
        focus_start = self.focus_origin

        if z_end < z_start:
            # Sort so we are always going low to high
            z_start, z_end = z_end, z_start
            focus_start, focus_end = focus_end, focus_start

        # set origin to be in the middle of start and end
        self.z_origin = (z_start + z_end) / 2
        self.focus_origin = (focus_start + focus_end) / 2
        self.update_stack_position_limits()

        # Propagate parameter changes to the GUI
        flip_flags = self.parent_controller.configuration_controller.stage_flip_flags
        start_pos = z_start - self.z_origin
        end_pos = z_end - self.z_origin
        start_focus = focus_start - self.focus_origin
        end_focus = focus_end - self.focus_origin
        if flip_flags[primary_z_axis]:
            start_pos, end_pos = end_pos, start_pos
            start_focus, end_focus = end_focus, start_focus
        self.stack_acq_vals["start_position"].set(start_pos)
        self.stack_acq_vals["start_focus"].set(start_focus)
        self.stack_acq_vals["end_position"].set(end_pos)
        self.stack_acq_vals["end_focus"].set(end_focus)
        self.update_z_steps()

    def update_cycling_setting(self, *_: tuple[str]) -> None:
        """Update the cycling settings in the model and the GUI.

        You can collect different channels in different formats.
        In the perZ format: Slice 0/Ch0, Slice0/Ch1, Slice1/Ch0, Slice1/Ch1, etc.
        in the perStack format: Slice 0/Ch0, Slice1/Ch0... SliceN/Ch0.  Then it repeats
        with Ch1

        Parameters
        ----------
        _ : tuple[str]
            Values is a tuple of strings. e.g., ('PY_VAR0', '', 'write')
        """

        # won't do any calculation when initializing
        if self.in_initialization:
            return
        # update experiment MicroscopeState dict
        self.microscope_state_dict["stack_cycling_mode"] = (
            "per_stack"
            if self.stack_acq_vals["cycling"].get() == "Per Stack"
            else "per_z"
        )

        # recalculate time point settings
        self.update_timepoint_setting()

        self.show_verbose_info("Cycling setting on channels tab has been changed")

    def update_save_setting(self, *_: tuple[str]) -> None:
        """Tell the parent controller 'save_data' is selected.

        Does not do any calculation when initializing the software.

        Parameters
        ----------
        _ : tuple[str]
            Values is a tuple of strings. e.g., ('PY_VAR0', '', 'write')
        """

        if self.in_initialization:
            return
        self.is_save = self.timepoint_vals["is_save"].get()
        self.microscope_state_dict["is_save"] = self.is_save
        self.parent_controller.execute("set_save", self.is_save)
        self.show_verbose_info("Save data option has been changed to", self.is_save)

    def update_timepoint_setting(self) -> None:
        """Automatically calculates the stack acquisition time based on the number of
        time points, channels, and exposure time.

        TODO: Add necessary computation for 'Stack Acq.Time', 'Time point Interval',
        'Experiment Duration'?

        Does not do any calculation when initializing the software.
        Order of priority for per_stack: timepoints > positions > channels > z-steps
                                        > delay
        Order of priority for perZ: timepoints > positions > z-steps > delays > channels
        """

        if self.in_initialization:
            return
        channel_settings = self.microscope_state_dict["channels"]
        number_of_positions = (
            self.parent_controller.multiposition_tab_controller.get_position_num()
            if self.is_multiposition
            else 1
        )
        channel_exposure_time = []
        # validate the spin box's value
        try:
            number_of_timepoints = int(float(self.timepoint_vals["timepoints"].get()))
            number_of_slices = int(self.stack_acq_vals["number_z_steps"].get())
            for channel_id in channel_settings.keys():
                channel = channel_settings[channel_id]
                if channel["is_selected"]:
                    channel_exposure_time.append(float(channel["camera_exposure_time"]))
            if len(channel_exposure_time) == 0:
                return
        except (tk.TclError, ValueError):
            self.timepoint_vals["experiment_duration"].set("0")
            self.timepoint_vals["stack_acq_time"].set("0")
            return
        except (KeyError, AttributeError):
            logger.error("Error caught: updating time point setting")
            return

        per_stack = self.stack_acq_vals["cycling"].get() == "Per Stack"

        # Initialize variable to keep track of how long the entire experiment will take.
        # Includes time, positions, channels...
        experiment_duration = 0

        # Initialize variable to calculate how long it takes to acquire a single volume
        # for all the channels. Only calculate once at the beginning.
        stack_acquisition_duration = 0

        for position_idx in range(number_of_positions):
            # For multiple positions, need to account for the time necessary to move
            # the stages that distance. In theory, these positions would be
            # populated in that 'pandastable' or some other data structure.

            # Determine the largest distance to travel between positions.  Assume
            # all axes move the same velocity This assumes that we are in a
            # multi-position mode. Not yet implemented.
            # x1, y1, z1, theta1, f1, = position_start.values()
            # x2, y2, z1, theta2, f1 = position_end.values()
            # distance = [x2-x1, y2-y1, z2-z1, theta2-theta1, f2-f1]
            # max_distance_idx = np.argmax(distance)
            # Now if we are going to do this properly, we would need to do this for
            # all the positions so that we can calculate the total experiment
            # time. Probably assemble a matrix of all the positions and then do
            # the calculations.

            stage_delay = 0
            # TODO False value.

            # If we were actually acquiring the data, we would call the function to
            # move the stage here.
            experiment_duration = experiment_duration + stage_delay

            for channel_idx in range(len(channel_exposure_time)):
                if per_stack:
                    # In the per_stack mode, we only need to account for the time
                    # necessary for the filter wheel to change between each
                    # image stack.
                    if channel_idx == 0 and position_idx == 0:
                        stack_acquisition_duration += (
                            channel_exposure_time[channel_idx] / 1000 * number_of_slices
                        )
                else:
                    if position_idx == 0:
                        stack_acquisition_duration += (
                            channel_exposure_time[channel_idx] / 1000 * number_of_slices
                        )

                experiment_duration += (
                    channel_exposure_time[channel_idx] / 1000 * number_of_slices
                )

            try:
                stack_pause = float(self.timepoint_vals["stack_pause"].get())
            except ValueError:
                stack_pause = 0
            experiment_duration = experiment_duration + stack_pause
        experiment_duration *= number_of_timepoints

        # Change the filter wheel here before the start of the acquisition.
        if len(channel_exposure_time) > 1:
            filter_wheel_change_times = number_of_timepoints * (
                1 if per_stack else number_of_slices
            )
            experiment_duration += (
                sum(self.filter_wheel_delay) * filter_wheel_change_times
            )
        else:
            experiment_duration += sum(self.filter_wheel_delay)
        self.timepoint_vals["experiment_duration"].set(
            str(datetime.timedelta(seconds=experiment_duration))
        )
        self.timepoint_vals["stack_acq_time"].set(
            str(datetime.timedelta(seconds=stack_acquisition_duration))
        )

        # update experiment MicroscopeState dict
        self.microscope_state_dict["timepoints"] = number_of_timepoints
        self.microscope_state_dict["stack_pause"] = self.timepoint_vals[
            "stack_pause"
        ].get()
        self.microscope_state_dict["stack_acq_time"] = stack_acquisition_duration
        self.microscope_state_dict["experiment_duration"] = experiment_duration

        self.show_verbose_info(
            "time point settings on channels tab have been changed and recalculated"
        )

    def toggle_multiposition(self, *_: tuple[str]) -> None:
        """Toggle Multi-position Acquisition.

        Recalculates the experiment duration.

        Parameters
        ----------
        _ : tuple[str]
            Values is a tuple of strings. e.g., ('PY_VAR0', '', 'write')
        """
        self.is_multiposition = self.is_multiposition_val.get()
        self.microscope_state_dict["is_multiposition"] = self.is_multiposition
        self.update_timepoint_setting()
        self.show_verbose_info("Multi-position:", self.is_multiposition)

    def disable_multiposition_btn(self) -> None:
        """Disable multi-position button"""
        self.view.multipoint_frame.save_check.config(state="disabled")

    def enable_multiposition_btn(self) -> None:
        """Enable multi-position button"""
        self.view.multipoint_frame.save_check.config(state="normal")

    def launch_waveform_parameters(self) -> None:
        """Launches waveform parameters popup."""
        self.parent_controller.menu_controller.popup_waveform_setting()

    def launch_autofocus_settings(self) -> None:
        """Launches autofocus settings popup."""
        self.parent_controller.menu_controller.popup_autofocus_setting()

    def launch_tiling_wizard(self) -> None:
        """Launches tiling wizard popup.

        Will only launch when button in GUI is pressed, and will not duplicate.
        Pressing button again brings popup to top
        """

        if hasattr(self, "tiling_wizard_controller"):
            self.tiling_wizard_controller.showup()
            return
        stage_axes = self.parent_controller.configuration_controller.stage_axes
        tiling_wizard = TilingWizardPopup(
            self.view, axes=[axis.upper() for axis in stage_axes]
        )
        self.tiling_wizard_controller = TilingWizardController(tiling_wizard, self)

    @staticmethod
    def set_info(vals: Dict[str, Any], values: Dict[str, Any]) -> None:
        """Set values to a list of variables.

        Parameters
        ----------
        vals : Dict[str, Any]
            A dictionary of variables to set.
        values : Dict[str, Any]
            A dictionary of values to set to variables.
        """
        for name in values.keys():
            if name in vals:
                vals[name].set(values[name])

    def execute(self, command: str, *args: tuple[str]) -> None:
        """Execute Command in the parent controller.

        Parameters
        ----------
        command : str
            recalculate_timepoint, channel, move_stage_and_update_info,
            get_stage_position
        args : tuple[str]
            A tuple of arguments to pass to the command.
        """
        if command == "recalculate_timepoint":
            self.update_timepoint_setting()
            # update framerate info in camera setting tab
            exposure_time = max(
                map(
                    lambda channel: (
                        float(channel["camera_exposure_time"])
                        if channel["is_selected"]
                        else 0
                    ),
                    self.microscope_state_dict["channels"].values(),
                )
            )
            self.parent_controller.camera_setting_controller.update_exposure_time(
                exposure_time
            )
        elif (command == "channel") or (command == "update_setting"):
            self.view.after(
                1000, lambda: self.parent_controller.execute(command, *args)
            )

        self.show_verbose_info("Received command from child", command, args)

    def update_experiment_values(self) -> None:
        """Update experiment values"""
        self.channel_setting_controller.update_experiment_values()
        self.update_z_steps()

        # update primary/secondary stack acquisition stage settings
        primary_z_stage = self.stack_acq_vals["z_device"].get()
        primary_z_axis = primary_z_stage.split(" - ")[1]
        primary_f_stage = self.stack_acq_vals["f_device"].get()
        primary_f_axis = primary_f_stage.split(" - ")[1]

        self.microscope_state_dict["primary_z_axis"] = primary_z_axis
        self.microscope_state_dict["primary_f_axis"] = primary_f_axis

        self.microscope_state_dict["speed"] = self.stack_acq_vals["speed"].get()

        secondary_stack_settings = {}
        variable_dict = self.view.stack_acq_frame.additional_stack_setting_variables
        for k in variable_dict.keys():
            if k.startswith("stack_") and variable_dict[k].get():
                axis = k.split("_")[1]
                offset = variable_dict[f"{axis}_offset"].get()
                secondary_stack_settings[axis] = offset

        self.microscope_state_dict[
            "secondary_stack_settings"
        ] = secondary_stack_settings

    def verify_experiment_values(self) -> str:
        """Verify channel tab settings and return warning info

        Returns
        -------
        string: str
            Warning info
        """
        warning = self.channel_setting_controller.verify_experiment_values()
        if warning:
            return warning
        if self.microscope_state_dict["image_mode"] not in ["live", "single"]:
            if (
                self.microscope_state_dict["number_z_steps"]
                != self.stack_acq_vals["number_z_steps"].get()
            ):
                return "There is something wrong with the stack settings!"
            if self.microscope_state_dict["number_z_steps"] < 1:
                return "The number of Z steps should be at least 1!"
            try:
                float(self.microscope_state_dict["stack_pause"])
            except Exception as e:
                logger.exception(e)
                return "Stack pause should be a valid number!"
            if self.microscope_state_dict["timepoints"] < 1:
                return "Timepoints should be at least 1!"
            warning = self._verify_stack_position_limits()
            if warning:
                return warning
        return ""

    def _verify_stack_position_limits(self) -> str:
        """Return warning text if stack positions exceed relative stage limits."""

        if not self._stage_limits_enabled():
            return ""

        stack_positions = [
            ("start_position", "z_device", "z", self.z_origin),
            ("end_position", "z_device", "z", self.z_origin),
            ("start_focus", "f_device", "f", self.focus_origin),
            ("end_focus", "f_device", "f", self.focus_origin),
        ]
        for setting_name, device_name, fallback_axis, origin in stack_positions:
            axis = self._get_stack_axis(device_name, fallback_axis)
            limits = self._get_relative_stage_limits(axis, float(origin))
            if limits is None:
                continue

            try:
                value = float(self.microscope_state_dict[setting_name])
            except (KeyError, TypeError, ValueError):
                return f"{setting_name} should be a valid number!"

            min_value, max_value = limits
            if value < min_value or value > max_value:
                return (
                    f"{setting_name} is outside the {axis} stage limits "
                    f"({min_value:.3f} to {max_value:.3f} um relative to origin)."
                )

        return ""

    def set_exposure_time(self, channel_exposure_time: tuple[str, float]) -> None:
        """Set exposure time for a specified channel

        Parameters
        ----------
        channel_exposure_time : tuple(str, float)
            (channel_name, exposure_time)
            Channel name, such as "channel_1", "channel_2",...
            Exposure time in milliseconds.
        """
        channel, exposure_time = channel_exposure_time
        idx = int(channel[channel.index("_") + 1 :]) - 1
        self.channel_setting_controller.in_initialization = True
        self.channel_setting_controller.view.exptime_variables[idx].set(exposure_time)
        self.channel_setting_controller.in_initialization = False

    def set_channel_defocus(self, channel_defocus, defocus=None) -> None:
        """Set defocus for a specified channel."""
        if defocus is None:
            channel, defocus = channel_defocus
        else:
            channel = channel_defocus
        idx = int(channel[channel.index("_") + 1 :]) - 1
        self.channel_setting_controller.in_initialization = True
        self.channel_setting_controller.view.defocus_variables[idx].set(defocus)
        self.channel_setting_controller.in_initialization = False

    def set_defocus_reference(self, reference) -> None:
        """Set the active defocus reference status shown in Channel Settings."""
        # get reference channel info from experiment
        reference_channel = self.parent_controller.configuration["experiment"][
            "AutoFocusParameters"
        ].get("reference_channel", None)
        if not reference:
            self.channel_setting_controller.view.defocus_reference.set(
                f"Defocus Reference: {reference_channel or 'Not Set'}"
            )
            return

        channel = reference["channel"]
        channel_label = f"CH{channel[channel.index('_') + 1 :]}"
        focus_position = float(reference["focus_position"])
        self.channel_setting_controller.view.defocus_reference.set(
            f"Defocus Reference: {channel_label} @ {focus_position:.2f}"
        )
        if reference_channel is None:
            self.parent_controller.configuration["experiment"]["AutoFocusParameters"][
                "reference_channel"
            ] = channel_label

    def update_additional_stacking_axes(self, *args, **kwargs):
        if self.stack_acq_vals["z_device"].get():
            z_axis = self.stack_acq_vals["z_device"].get().split(" - ")[1]
        else:
            z_axis = ""
        if self.stack_acq_vals["f_device"].get():
            f_axis = self.stack_acq_vals["f_device"].get().split(" - ")[1]
        else:
            f_axis = ""

        # enable all axis
        for widget_name in self.view.stack_acq_frame.additional_stack_setting_variables:
            if widget_name.startswith("stack_"):
                self.stack_acq_widgets[widget_name].state(["!disabled"])

        # disable primary z and f
        variable_dict = self.view.stack_acq_frame.additional_stack_setting_variables
        if f"stack_{z_axis}" in variable_dict:
            self.stack_acq_widgets[f"stack_{z_axis}"].state(["disabled"])
            if variable_dict[f"stack_{z_axis}"].get():
                variable_dict[f"stack_{z_axis}"].set(False)
                self.view.stack_acq_frame.update_setting_widgets(z_axis)()
        if f"stack_{f_axis}" in variable_dict:
            self.stack_acq_widgets[f"stack_{f_axis}"].state(["disabled"])
            if variable_dict[f"stack_{f_axis}"].get():
                variable_dict[f"stack_{f_axis}"].set(False)
                self.view.stack_acq_frame.update_setting_widgets(f_axis)()
        self.update_stack_position_limits()

    @property
    def custom_events(self) -> dict[str, callable]:
        """Custom events for the channels tab."""
        return {
            "exposure_time": self.set_exposure_time,
            "channel_defocus": self.set_channel_defocus,
            "defocus_reference": self.set_defocus_reference,
        }
