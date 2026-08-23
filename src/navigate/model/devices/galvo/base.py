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

#  Standard Library Imports
import logging
from typing import Any
from abc import ABC, abstractmethod

# Third Party Imports

# Local Imports
from navigate.model.waveforms import (
    centered_cubic,
    quadratic,
    sawtooth,
    sine_wave,
    single_pulse,
)
from navigate.model.devices.configuration_schema import SettingSpec
from navigate.tools.decorators import log_initialization

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class GalvoBase(ABC):
    """Abstract base class for galvanometer devices.

    This class provides the interface and common functionality for controlling
    galvanometers with navigate. It handles waveform generation based on
    configuration parameters and experimental settings.

    The class generates appropriate control waveforms (sawtooth, sine, halfsaw)
    according to camera exposure times and configuration parameters. Child classes
    must implement the turn_off method to control hardware-specific behaviors.
    """

    configuration_schema = {
        "waveform": SettingSpec(
            str,
            default="sawtooth",
            label="Waveform",
            help_text="Waveform shape generated for this galvo.",
            choices=(
                "sawtooth",
                "centered_cubic",
                "quadratic",
                "sine",
                "pulse",
                "halfsaw",
            ),
            required=False,
        ),
        "phase": SettingSpec(
            float,
            default=1.57079,
            label="Phase",
            help_text="Phase offset used by sine waveforms, in radians.",
            required=True,
        ),
        "hardware/min": SettingSpec(
            float,
            default=-5.0,
            label="Minimum Voltage",
            help_text="Minimum galvo output voltage.",
            required=True,
        ),
        "hardware/max": SettingSpec(
            float,
            default=5.0,
            label="Maximum Voltage",
            help_text="Maximum galvo output voltage.",
            required=True,
        ),
    }

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        device_id: int = 0,
    ) -> None:
        """Initialize the GalvoBase class.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : Any
            Device connection.
        configuration : dict[str, Any]
            Dictionary of configuration parameters.
        device_id : int
            Galvo ID. Default is 0.
        """
        #: Any: Device connection.
        self.device_connection = device_connection

        #: dict: Dictionary of microscope configuration parameters.
        self.configuration = configuration

        #: str: Name of the microscope.
        self.microscope_name = microscope_name

        #: str: Name of the galvo.
        self.galvo_name = "Galvo " + str(device_id)

        #: dict: Dictionary of device connections.
        self.device_config = configuration["configuration"]["microscopes"][
            microscope_name
        ]["galvo"][device_id]

        #: int: Sample rate.
        self.sample_rate = configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["sample_rate"]

        #: float: Sweep time.
        self.sweep_time = 0

        #: float: Galvo max voltage.
        self.galvo_max_voltage = self.device_config["hardware"]["max"]

        #: float: Galvo min voltage.
        self.galvo_min_voltage = self.device_config["hardware"]["min"]

        # Galvo Waveform Information
        #: str: Galvo waveform. Waveform or Sawtooth.
        self.galvo_waveform = self.device_config.get("waveform", "sawtooth")

        #: dict: Dictionary of galvo waveforms.
        self.waveform_dict = {}

    def __str__(self) -> str:
        """Returns the string representation of the GalvoBase class."""
        return "GalvoBase"

    def __del__(self):
        """Destructor"""
        pass

    @property
    def camera_delay(self) -> float:
        """Return the current camera delay from waveform constants, in seconds."""
        return (
            float(
                self.configuration["waveform_constants"]["other_constants"][
                    "camera_delay"
                ]
            )
            / 1000
        )

    @abstractmethod
    def adjust(
        self, exposure_times: dict[str, float], sweep_times: dict[str, float]
    ) -> dict:
        """Adjust the galvo waveform to account for the camera readout time.

        Parameters
        ----------
        exposure_times : dict
            Dictionary of camera exposure time in seconds on a per-channel basis.
            e.g., exposure_times = {"channel_1": 0.1, "channel_2": 0.2}
        sweep_times : dict
            Dictionary of acquisition sweep time in seconds on a per-channel basis.
            e.g., sweep_times = {"channel_1": 0.1, "channel_2": 0.2}

        Returns
        -------
        waveform_dict : dict
            Dictionary that includes the galvo waveforms on a per-channel basis.
        """
        self.waveform_dict = dict.fromkeys(self.waveform_dict, None)
        microscope_state = self.configuration["experiment"]["MicroscopeState"]
        microscope_name = microscope_state["microscope_name"]
        zoom_value = microscope_state["zoom"]
        galvo_factor = self.configuration["waveform_constants"]["other_constants"].get(
            "galvo_factor", "none"
        )
        galvo_parameters = self.configuration["waveform_constants"]["galvo_constants"][
            self.galvo_name
        ][microscope_name][zoom_value]
        self.sample_rate = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["daq"]["sample_rate"]

        for channel_key in microscope_state["channels"].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state["channels"][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel["is_selected"] is True:
                # Get the Waveform Parameters - Assumes ETL Delay < Camera Delay.
                # Should Assert.
                exposure_time = exposure_times[channel_key]
                self.sweep_time = sweep_times[channel_key]

                # galvo Parameters
                try:
                    galvo_amplitude = float(galvo_parameters.get("amplitude", 0))
                    galvo_offset = float(galvo_parameters.get("offset", 0))
                    galvo_rising_ramp = float(galvo_parameters.get("rising_ramp", 50))
                    galvo_frequency = (
                        float(galvo_parameters.get("frequency", 0)) / exposure_time
                    )
                    factor_name = None
                    if galvo_factor == "channel":
                        factor_name = (
                            f"Channel {channel_key[channel_key.index('_') + 1 :]}"
                        )
                    elif galvo_factor == "laser":
                        factor_name = channel["laser"]
                    if factor_name and factor_name in galvo_parameters.keys():
                        galvo_amplitude = float(
                            galvo_parameters[factor_name].get("amplitude", 0)
                        )
                        galvo_offset = float(
                            galvo_parameters[factor_name].get("offset", 0)
                        )

                except ValueError as e:
                    logger.debug(
                        f"{e} waveform constants.yml doesn't have parameter "
                        f"amplitude/offset/frequency for {self.galvo_name}"
                    )
                    return

                # Calculate the Waveforms
                if self.galvo_waveform == "sawtooth":
                    self.waveform_dict[channel_key] = sawtooth(
                        sample_rate=self.sample_rate,
                        sweep_time=self.sweep_time,
                        frequency=galvo_frequency,
                        amplitude=galvo_amplitude,
                        offset=galvo_offset,
                        duty_cycle=galvo_rising_ramp,
                        phase=self.camera_delay,
                    )
                elif self.galvo_waveform == "centered_cubic":
                    self.waveform_dict[channel_key] = centered_cubic(
                        sample_rate=self.sample_rate,
                        sweep_time=self.sweep_time,
                        exposure=exposure_time,
                        delay=self.camera_delay,
                        amplitude=galvo_amplitude,
                        offset=galvo_offset,
                    )
                elif self.galvo_waveform == "quadratic":
                    self.waveform_dict[channel_key] = quadratic(
                        sample_rate=self.sample_rate,
                        sweep_time=self.sweep_time,
                        exposure=exposure_time,
                        delay=self.camera_delay,
                        amplitude=galvo_amplitude,
                        offset=galvo_offset,
                    )
                elif self.galvo_waveform == "sine":
                    self.waveform_dict[channel_key] = sine_wave(
                        sample_rate=self.sample_rate,
                        sweep_time=self.sweep_time,
                        frequency=galvo_frequency,
                        amplitude=galvo_amplitude,
                        offset=galvo_offset,
                        phase=self.device_config["phase"],
                    )
                elif self.galvo_waveform == "pulse":
                    pulse_delay = 100 * self.camera_delay / self.sweep_time
                    pulse_width = 100 - pulse_delay
                    pulse_wave = single_pulse(
                        sample_rate=self.sample_rate,
                        sweep_time=self.sweep_time,
                        pulse_width=pulse_width,
                        amplitude=galvo_amplitude,
                        offset=galvo_offset,
                        delay=pulse_delay,
                    )
                    pulse_wave[-1] = 0
                    self.waveform_dict[channel_key] = pulse_wave
                elif self.galvo_waveform == "halfsaw":
                    new_wave = sawtooth(
                        sample_rate=self.sample_rate,
                        sweep_time=self.sweep_time,
                        frequency=galvo_frequency,
                        amplitude=galvo_amplitude,
                        offset=galvo_offset,
                        phase=self.camera_delay,
                    )
                    half_samples = (
                        new_wave.argmax() if galvo_amplitude > 0 else new_wave.argmin()
                    )
                    new_wave[:half_samples] = -galvo_offset
                    self.waveform_dict[channel_key] = new_wave
                else:
                    print("Unknown Galvo waveform specified in configuration file.")
                    self.waveform_dict[channel_key] = None
                    continue
                self.waveform_dict[channel_key][
                    self.waveform_dict[channel_key] > self.galvo_max_voltage
                ] = self.galvo_max_voltage
                self.waveform_dict[channel_key][
                    self.waveform_dict[channel_key] < self.galvo_min_voltage
                ] = self.galvo_min_voltage

        return self.waveform_dict

    @abstractmethod
    def turn_off(self) -> None:
        """Turn off the galvo."""
        pass
