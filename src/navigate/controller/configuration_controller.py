# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
from typing import Any, Dict, List, Optional, Union, Iterable

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ConfigurationController:
    """Configuration Controller - Used to query and expose microscope configuration.

    Parameters
    ----------
    configuration : Dict[str, Any]
        The shared configuration dictionary (possibly using Manager proxies).
    """

    def __init__(self, configuration: Dict[str, Any]) -> None:
        """Initialize the Configuration Controller.

        Parameters
        ----------
        configuration : Dict[str, Any]
            The configuration dictionary (from manager).
        """
        #: Dict[str, Any]: shared configuration dictionary.
        self.configuration: Dict[str, Any] = configuration

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

    def change_microscope(self) -> bool:
        """Update to the microscope specified in the configuration.

        Reads the 'microscope_name' key from the experiment section and
        updates this controller's microscope_config and microscope_name.

        Returns
        -------
        bool
            True if the microscope was changed; False if it remained the same.

        Raises
        ------
        AssertionError
            If the microscope name in the configuration is not found in the
            configuration.yaml file.
        """
        microscope_name = self.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ]
        assert (
            microscope_name
            in self.configuration["configuration"]["microscopes"].keys(),
            f"Microscope {microscope_name} not found in configuration.yaml file",
        )

        if self.microscope_name == microscope_name:
            return False

        self.microscope_config = self.configuration["configuration"]["microscopes"][
            microscope_name
        ]
        self.microscope_name = microscope_name
        return True

    def get_microscope_configuration_dict(self) -> DictProxy:
        """Return the current microscope's configuration dictionary.

        Returns
        -------
        DictProxy
            The microscope-specific configuration mapping.
        """
        return self.microscope_config

    @property
    def channels_info(self) -> Dict[str, Any]:
        """Return the channel settings.

        Populate the channel combobox with the channels that are available in the
        configuration

        Returns
        -------
        setting : dict
            Channel settings, e.g. {
                'laser': ['488 nm', '561 nm', '642 nm'],
                'filter': ['Empty-Alignment', 'GFP - FF01-515/30-32']}
        """
        if self.microscope_config is None:
            return {}

        setting = {
            "laser": self.lasers_info,
        }
        for i, filter_wheel_config in enumerate(self.microscope_config["filter_wheel"]):
            setting[f"filter_wheel_{i}"] = list(
                filter_wheel_config["available_filters"].keys()
            )
        return setting

    @property
    def lasers_info(self) -> List[str]:
        """Return the laser information.

        Populate the laser combobox with the lasers that are available in the
        configuration

        Returns
        -------
        laser_list : list
            List of lasers, e.g. ['488 nm', '561 nm', '642 nm']
        """
        if self.microscope_config is None:
            return []

        return [
            str(laser["wavelength"]) + "nm" for laser in self.microscope_config["laser"]
        ]

    @property
    def camera_config_dict(self) -> Optional[Dict[str, Any]]:
        """Get camera configuration dictionary.

        Returns
        -------
        camera_setting: dict
            Camera Settings.
        """
        if self.microscope_config is not None:
            return self.microscope_config["camera"]
        return None

    @property
    def camera_pixels(self) -> List[int]:
        """Get default pixel values from camera

        Returns
        -------
        x_pixels : int
            Number of x pixels
        y_pixels : int
            Number of y pixels
        """
        if self.microscope_config is None:
            # Default to 2048x2048 if no config is available
            return [2048, 2048]

        return [
            self.microscope_config["camera"]["x_pixels"],
            self.microscope_config["camera"]["y_pixels"],
        ]

    @property
    def stage_default_position(self) -> Dict[str, Union[int, float]]:
        """Get the current position of the stage.

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
    def stage_step(self) -> Dict[str, Union[int, float]]:
        """Get the step size of the stage.

        Returns
        -------
        steps : dict
            Step size in x (same step size for y), z, theta, and f.
        """
        if self.microscope_config is not None:
            stage_dict = self.microscope_config["stage"]
            steps = {
                "x": stage_dict["x_step"],
                "y": stage_dict["y_step"],
                "z": stage_dict["z_step"],
                "theta": stage_dict["theta_step"],
                "f": stage_dict["f_step"],
            }
        else:
            steps = {"x": 10, "y": 10, "z": 10, "theta": 10, "f": 10}
        return steps

    def get_stage_position_limits(self, suffix: str) -> Dict[str, Union[int, float]]:
        """Return the position limits of the stage.

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
                position_limits[a] = stage_dict.get(
                    a + suffix, 0 if suffix == "_min" else 100
                )
        else:
            for a in axes:
                position_limits[a] = 0 if suffix == "_min" else 100
        return position_limits

    @property
    def stage_flip_flags(self) -> Dict[str, bool]:
        """Return the flip flags of the stage.

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
    def stage_axes(self) -> List[str]:
        """Return the axes of the stage.

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
    def all_stage_axes(self) -> List[str]:
        """Return all the axes of the stage.

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
    def camera_flip_flags(self) -> Dict[str, bool]:
        """Return the flip flags of the camera.

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
    def remote_focus_dict(self) -> Optional[Dict[str, Any]]:
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
    def galvo_parameter_dict(self) -> Optional[List[Dict[str, Any]]]:
        """Return galvo parameter dict.

        Returns
        -------
        galvo_parameter_dict : dict
            Dictionary with the galvo parameters.
        """
        if self.microscope_config is not None:
            # Inject names into unnamed galvos
            for i, galvo in enumerate(self.microscope_config["galvo"]):
                if galvo.get("name") is None:
                    self.microscope_config["galvo"][i]["name"] = f"Galvo {i}"
            return self.microscope_config["galvo"]
        return None

    @property
    def daq_sample_rate(self) -> float:
        """Return daq sample rate.

        Returns
        -------
        daq_sample_rate : float
            Sample rate of the daq.
        """
        if self.microscope_config is not None:
            return self.microscope_config["daq"]["sample_rate"]
        return 100000

    @property
    def filter_wheel_setting_dict(self) -> Optional[List[Dict[str, Any]]]:
        """Return filter wheel setting dict.

        Returns
        -------
        filter_wheel_setting_dict : dict
            Dictionary with the filter-wheel settings.
        """
        if self.microscope_config is not None:
            return self.microscope_config["filter_wheel"]
        return None

    @property
    def stage_setting_dict(self) -> Optional[Dict[str, Any]]:
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
    def z_stages(self) -> List[str]:
        """Return a list of all z stage names.

        Returns
        -------
        z_stages : list
            A list of z stage names.
        """
        z_stages = []
        if self.microscope_config is not None:
            stages = self.microscope_config["stage"]["hardware"]
            if isinstance(stages, ListProxy):
                stages = list(stages)
                z_stages = [stage["type"] for stage in stages if "z" in stage["axes"]]
            elif isinstance(stages, DictProxy):
                stages = dict(stages)
                z_stages = [stages["type"]] if "z" in stages["axes"] else []
        return z_stages

    @property
    def number_of_channels(self) -> int:
        """Return number of channels.

        Returns
        -------
        number_of_channels : int
            Number of channels.
        """
        if self.microscope_config is not None:
            return self.configuration["gui"]["channel_settings"].get("count", 5)
        return 5

    @property
    def number_of_filter_wheels(self) -> int:
        """Return the number of filter wheels.

        Returns
        -------
        number_of_filter_wheels : int
            Number of filter wheels
        """

        if self.microscope_config is not None:
            return len(self.microscope_config["filter_wheel"])
        return 1

    @property
    def filter_wheel_names(self) -> List[str]:
        """Return a list of filter-wheel names

        Returns
        -------
        filter_wheel_names : list
            List of filter-wheel names.
        """
        filter_wheel_names = []
        if self.microscope_config is not None:
            for i in range(self.number_of_filter_wheels):
                name = self.microscope_config["filter_wheel"][i]["hardware"].get(
                    "name", f"Filter Wheel {i}"
                )
                filter_wheel_names.append(name)
        return filter_wheel_names

    @property
    def microscope_list(self) -> List[str]:
        """Return a list of microscope names

        Returns
        -------
        microscope_list : list
            List of microscope names.
        """
        return list(self.configuration["configuration"]["microscopes"].keys())

    def get_zoom_value_list(self, microscope_name: str) -> Iterable[str]:
        """Return available zoom values for a given microscope.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.

        Returns
        -------
        Iterable[str]
            Zoom setting keys for the specified microscope.
        """
        return self.configuration["waveform_constants"]["remote_focus_constants"][
            microscope_name
        ].keys()

    @property
    def gui_setting(self) -> Dict[str, Any]:
        """Return GUI configuration settings.

        Returns
        -------
        Dict[str, Any]
            GUI-related configuration dictionary.
        """
        return self.configuration["configuration"]["gui"]
