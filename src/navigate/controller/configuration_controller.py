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
import logging
from multiprocessing.managers import ListProxy, DictProxy
from typing import Optional

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ConfigurationController:
    """Configuration Controller - Used to get the configuration of the microscope."""

    def __init__(self, configuration: DictProxy) -> None:
        """Initialize the Configuration Controller

        Parameters
        ----------
        configuration : DictProxy
            The configuration dictionary.
        """
        #: DictProxy: The configuration dictionary.
        self.configuration = configuration

        #: str: The microscope name.
        self.microscope_name = None

        #: dict: The microscope configuration dictionary.
        self.microscope_config = None
        self.change_microscope()

        microscopes_config = configuration["configuration"]["microscopes"]

        #: int: The number of galvos.
        self.galvo_num = max(
            map(
                lambda microscope_name: len(
                    microscopes_config[microscope_name]["galvo"]
                ),
                microscopes_config.keys(),
            )
        )

    def update_configuration(self) -> None:
        """Update the microscope configuration to reflect any changes made to it."""

        self.microscope_config = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]

    def change_microscope(self, microscope_name=None) -> bool:
        """Get the new microscope configuration dict according to the name.

        Gets the name of the microscope, retrieves its configuration, and updates the
        Configuration Controller's attributes.

        Returns
        -------
        result: bool
        """
        if microscope_name is None:
            microscope_name = self.configuration["experiment"]["MicroscopeState"][
                "microscope_name"
            ]

        assert (
            microscope_name in self.configuration["configuration"]["microscopes"].keys()
        )

        if self.microscope_name == microscope_name:
            return False

        self.microscope_config = self.configuration["configuration"]["microscopes"][
            microscope_name
        ]
        self.microscope_name = microscope_name
        return True

    def get_microscope_configuration_dict(self) -> dict:
        """Return microscope configuration dictionary

        Returns
        -------
        microscope_configuration_dict: dict
        """
        return self.microscope_config

    @property
    def channels_info(self) -> dict:
        """Return the channels info

        Populate the channel combobox with the channels
        that are available in the configuration

        Returns
        -------
        setting : dict
            Channel settings, e.g. {
                'laser': ['488nm', '561nm', '642nm'],
                'filter': ['Empty-Alignment', 'GFP - FF01-515/30-32', '...}
        """
        if self.microscope_config is None:
            return {}

        setting = {
            "laser": self.lasers_info,
        }
        for i, filter_wheel_config in enumerate(self.microscope_config["filter_wheel"]):
            filter_wheel_name = filter_wheel_config.get("name", f"FilterWheel-{i}")
            setting[filter_wheel_name] = list(
                filter_wheel_config["available_filters"].keys()
            )
        return setting

    @property
    def lasers_info(self) -> list:
        """Return the lasers info

        Populate the laser combobox with the lasers
        that are available in the configuration

        Returns
        -------
        laser_list : list
            List of lasers, e.g. ['488nm', '561nm', '642nm']
        """
        if self.microscope_config is None:
            return []

        return [
            str(laser["wavelength"]) + "nm" for laser in self.microscope_config["laser"]
        ]

    @property
    def camera_config_dict(self) -> dict:
        """Get camera configuration dict

        Returns
        -------
        camera_setting: dict
            Camera Setting, e.g. {

            }
        """
        if self.microscope_config is not None:
            return self.microscope_config["camera"]
        return None

    @property
    def camera_pixels(self) -> list[int]:
        """Get default pixel values from camera

        Returns
        -------
        x_pixels : int
            Number of x pixels
        y_pixels : int
            Number of y pixels
        """
        if self.microscope_config is None:
            return [2048, 2048]

        return [
            self.microscope_config["camera"]["x_pixels"],
            self.microscope_config["camera"]["y_pixels"],
        ]

    @property
    def stage_default_position(self) -> dict:
        """Get current position of the stage

        Returns
        -------
        position : dict
            Dictionary with x, y, z, theta, and f positions.
        """
        if self.microscope_config is not None:
            stage_position = self.microscope_config["stage"]["position"]
            position = {
                "x": stage_position["x_pos"],
                "y": stage_position["y_pos"],
                "z": stage_position["z_pos"],
                "theta": stage_position["theta_pos"],
                "f": stage_position["f_pos"],
            }
        else:
            position = {"x": 0, "y": 0, "z": 0, "theta": 0, "f": 0}
        return position

    @property
    def stage_home_position(self) -> dict:
        """Get the home position of the stage. If not set, return None.

        Returns
        -------
        position : dict
            Dictionary with all stage home positions.
        """

        # Get all stage axes, not just the core X, Y, Z, F, and Theta.
        axes = self.all_stage_axes

        # Create a dictionary for every axis in axes with a default value of None.
        position = {axis: None for axis in axes}
        if self.microscope_config is not None:
            for axis in axes:
                key = f"{axis}_home"
                position[axis] = self.microscope_config["stage"].get(key, None)
                if position[axis] is None:
                    del position[axis]
        return position

    @property
    def stage_step(self) -> dict:
        """Get the step size of the stage

        Returns
        -------
        steps : dict
            Step size in x (same step size for y), z, theta, and f.
        """
        if self.microscope_config is not None:
            stage_dict = self.microscope_config.get("stage", {})
            steps = {
                "x": stage_dict.get("x_step", 1),
                "y": stage_dict.get("y_step", 1),
                "z": stage_dict.get("z_step", 1),
                "theta": stage_dict.get("theta_step", 1),
                "f": stage_dict.get("f_step", 1),
            }
        else:
            steps = {"x": 10, "y": 10, "z": 10, "theta": 10, "f": 10}
        return steps

    @property
    def stage_offsets(self) -> dict:
        """Get the offsets of the stage

        Returns
        -------
        offsets : dict
            Offsets in x, y, z, theta, and f.
        """
        if self.microscope_config is not None:
            stage_dict = self.microscope_config["stage"]
        else:
            stage_dict = {}
        offsets = {}
        for axis in self.stage_axes:
            offsets[axis] = stage_dict.get(f"{axis}_offset", 0)
        return offsets

    def get_stage_position_limits(self, suffix: str) -> dict:
        """Return the position limits of the stage

        Parameters
        ----------
        suffix : str
            '_min' or '_max'

        Returns
        -------
        position_limits : dict
            Depending on suffix, min or max stage limits, e.g.
            {'x': 2000, 'y': 2000, 'z': 2000, 'theta': 0, 'f': 2000}.

        """
        axes = self.stage_axes
        position_limits = {}
        if self.microscope_config is not None:
            stage_dict = self.microscope_config["stage"]
            for a in axes:
                position_limits[a] = float(
                    stage_dict.get(a + suffix, 0 if suffix == "_min" else 100)
                )
        else:
            for a in axes:
                position_limits[a] = 0 if suffix == "_min" else 100
        return position_limits

    @property
    def stage_flip_flags(self) -> dict[str, bool]:
        """Return the flip flags of the stage

        Returns
        -------
        flip_flags : dict
            {'x': bool, 'y': bool, 'z': bool, 'theta': bool, 'f': bool}.

        """
        if self.microscope_config is not None:
            stage_dict = self.microscope_config["stage"]
        else:
            stage_dict = {}
        flip_flags = {}
        for axis in self.stage_axes:
            flip_flags[axis] = stage_dict.get(f"flip_{axis}", False)
        return flip_flags

    @property
    def stage_axes(self) -> list[str]:
        """Return the axes of the stage

        Returns
        -------
        axes : list
            List of axes, e.g. ['x', 'y', 'z', 'theta', 'f'].
        """
        if self.microscope_config is not None:
            stage_config = self.microscope_config["stage"]["hardware"]
            axes = []
            if isinstance(stage_config, ListProxy):
                for stage in stage_config:
                    axes.extend(list(stage["axes"]))
            else:
                axes = list(stage_config["axes"])
            return axes

        return ["x", "y"]

    @property
    def all_stage_axes(self) -> list[str]:
        """Return all the axes of the stage

        Returns
        -------
        axes : list
            List of all axes, e.g. ['x', 'y', 'z', 'theta', 'f'].
        """
        axes = []
        for microscope_name in self.microscope_list:
            stage_config = self.configuration["configuration"]["microscopes"][
                microscope_name
            ]["stage"]["hardware"]
            if isinstance(stage_config, ListProxy):
                for stage in stage_config:
                    axes.extend(list(stage["axes"]))
            else:
                axes.extend(list(stage_config["axes"]))
        return list(set(axes))

    @property
    def camera_flip_flags(self) -> dict[str, bool]:
        """Return the flip flags of the camera

        Returns
        -------
        flip_flags : dict
            {'x': bool, 'y': bool}.
        """
        if self.microscope_config is not None:
            camera_dict = self.microscope_config["camera"]
        else:
            camera_dict = {}
        flip_flags = {
            "x": camera_dict.get("flip_x", False),
            "y": camera_dict.get("flip_y", False),
        }
        return flip_flags

    @property
    def remote_focus_dict(self) -> dict:
        """Return delay_percent, pulse_percent.

        Returns
        -------
        remote_focus_parameters : dict
            Dictionary with the remote focus percent delay and pulse percent.
        """
        if self.microscope_config is not None:
            return self.microscope_config["remote_focus"]

        return None

    @property
    def galvo_parameter_dict(self) -> dict:
        """Return galvo parameter dict.

        Returns
        -------
        galvo_parameter_dict : dict
            Dictionary with the galvo parameters.
        """
        if self.microscope_config is not None:
            # Inject names into unnammed galvos
            for i, galvo in enumerate(self.microscope_config["galvo"]):
                if galvo.get("name") is None:
                    self.microscope_config["galvo"][i]["name"] = f"Galvo {i}"
            return self.microscope_config["galvo"]
        return None

    @property
    def daq_sample_rate(self) -> int:
        """Return daq sample rate.

        Returns
        -------
        daq_sample_rate : int
            Sample rate of the daq.
        """
        if self.microscope_config is not None:
            return self.microscope_config["daq"]["sample_rate"]
        return 100000

    @property
    def filter_wheel_setting_dict(self) -> dict:
        """Return filter wheel setting dict.

        Returns
        -------
        filter_wheel_setting_dict : dict
            Dictionary with the filter wheel settings.
        """
        if self.microscope_config is not None:
            return self.microscope_config["filter_wheel"]
        return None

    @property
    def stage_setting_dict(self) -> dict:
        """Return stage setting dict.

        Returns
        -------
        stage_setting_dict : dict
            Dictionary with the stage settings.
        """
        if self.microscope_config is not None:
            return self.microscope_config["stage"]
        return None

    @property
    def has_analog_stage(self) -> bool:
        """Check to see if the has_ni_galvo_stage flag is set in the configuration.

        Returns
        -------
        has_ni_galvo_stage : bool
            True if the microscope has an NI galvo stage, False otherwise.
        """

        if self.microscope_config is not None:
            return self.microscope_config["stage"].get("has_ni_galvo_stage", False)
        return False

    def get_stages_by_axis(self, axis_prefix: Optional[str] = "z"):
        """Return a list of all stage names.

        Parameters
        ----------
        axis_prefix : str
            The axis prefix to get the stage names for.

        Returns
        -------
        stages : list
            A list of stage names.
        """
        if self.microscope_config is not None:
            stages = self.microscope_config["stage"]["hardware"]
            if isinstance(stages, ListProxy):
                stages = list(stages)
            else:
                stages = [stages]
            return [
                f"{stage['type']} - {axis}"
                for stage in stages
                for axis in stage["axes"]
                if axis.startswith(axis_prefix)
            ]
        return []

    @property
    def number_of_channels(self) -> int:
        """Return number of channels.

        Returns
        -------
        number_of_channels : int
            Number of channels.
        """
        if self.microscope_config is not None:
            number_of_channels = (
                self.configuration["gui"].get("channel_settings", {}).get("count", 5)
            )
            return number_of_channels
        return 5

    @property
    def number_of_filter_wheels(self) -> int:
        """Return number of filter wheels

        Returns
        -------
        number_of_filter_wheels : int
            Number of filter wheels
        """

        if self.microscope_config is not None:
            return len(self.microscope_config["filter_wheel"])
        return 1

    @property
    def filter_wheel_types(self) -> list[str]:
        """Return a list of filter wheel hardware types.

        Returns
        -------
        filter_wheel_types : list
            List of filter wheel hardware types.
        """
        filter_wheel_types = []
        if self.microscope_config is not None:
            for i in range(self.number_of_filter_wheels):
                hardware_config = self.microscope_config["filter_wheel"][i].get(
                    "hardware", {}
                )
                filter_wheel_types.append(hardware_config.get("type", ""))
        return filter_wheel_types

    @property
    def filter_wheel_visibility(self) -> list[bool]:
        """Return a list indicating which filter wheels are native to microscope.

        Returns
        -------
        filter_wheel_visibility : list
            ``True`` for wheels that are defined for this microscope.
        """
        if self.microscope_config is None:
            return []

        visibility = self.microscope_config.get("filter_wheel_visibility")
        if isinstance(visibility, ListProxy):
            visibility = list(visibility)

        if not isinstance(visibility, list):
            return [True] * self.number_of_filter_wheels

        if len(visibility) != self.number_of_filter_wheels:
            return [True] * self.number_of_filter_wheels

        return [bool(value) for value in visibility]

    @property
    def filter_wheel_names(self) -> list[str]:
        """Return a list of filter wheel names

        Returns
        -------
        filter_wheel_names : list
            List of filter wheel names.
        """
        filter_wheel_names = []
        if self.microscope_config is not None:
            for i in range(self.number_of_filter_wheels):
                name = self.microscope_config["filter_wheel"][i].get(
                    "name", f"Filter Wheel {i}"
                )
                filter_wheel_names.append(name)
        return filter_wheel_names

    @property
    def microscope_list(self) -> list[str]:
        """Return a list of microscope names

        Returns
        -------
        microscope_list : list
            List of microscope names.
        """
        return list(self.configuration["configuration"]["microscopes"].keys())

    def get_zoom_value_list(self, microscope_name: str) -> list:
        """Return a list of zoom values

        Returns
        -------
        zoom_value_list : list
            List of zoom values.
        """
        return self.configuration["waveform_constants"]["remote_focus_constants"][
            microscope_name
        ].keys()

    @property
    def gui_setting(self) -> dict:
        """Return the GUI settings

        Returns
        -------
        gui_setting : dict
            Dictionary with the GUI settings.
        """
        return self.configuration["configuration"]["gui"]

    def is_same_camera(self, microscope_name: str) -> bool:
        """Check if the current microscope uses the same camera as the given microscope.

        Parameters
        ----------
        microscope_name : str
            The name of the microscope to compare with.

        Returns
        -------
        is_same : bool
            True if the cameras are the same, False otherwise.
        """
        if self.microscope_config is None:
            return False

        if microscope_name == self.microscope_name:
            return True

        if microscope_name not in self.configuration["configuration"]["microscopes"]:
            return False

        current_camera_type = self.microscope_config["camera"]["hardware"]["type"]
        other_camera_type = self.configuration["configuration"]["microscopes"][
            microscope_name
        ]["camera"]["hardware"]["type"]

        if current_camera_type != other_camera_type:
            return False

        for param in ["serial_number", "camera_connection"]:
            if (
                param in self.microscope_config["camera"]["hardware"].keys()
                and param
                in self.configuration["configuration"]["microscopes"][microscope_name][
                    "camera"
                ]["hardware"].keys()
            ):
                current_value = self.microscope_config["camera"]["hardware"][param]
                other_value = self.configuration["configuration"]["microscopes"][
                    microscope_name
                ]["camera"]["hardware"][param]

                if current_value != other_value:
                    return False

        return True
