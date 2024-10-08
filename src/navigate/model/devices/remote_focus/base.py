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


#  Standard Library Imports
import logging
from typing import Any
from multiprocessing.managers import DictProxy

# Third Party Imports

# Local Imports
from navigate.model.waveforms import (
    remote_focus_ramp,
    smooth_waveform,
    remote_focus_ramp_triangular,
)
from navigate.tools.decorators import log_initialization

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class RemoteFocusBase:
    """RemoteFocusBase Class - Parent class for Remote Focusing Device."""

    def __init__(
        self, microscope_name: str, device_connection: Any, configuration: DictProxy
    ) -> None:
        """Initializes the RemoteFocusBase Class.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : Any
            Device connection object.
        configuration : DictProxy
            Configuration dictionary.
        """

        #: dict: Configuration dictionary.
        self.configuration = configuration

        #: str: Name of the microscope.
        self.microscope_name = microscope_name

        #: dict: Remote focus device parameters.
        self.device_config = configuration["configuration"]["microscopes"][
            microscope_name
        ]["remote_focus_device"]

        #: int: Sample rate of the DAQ.
        self.sample_rate = configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["sample_rate"]

        #: float: Sweep time of the DAQ.
        self.sweep_time = 0

        #: float: Camera delay percent.
        self.camera_delay = (
            configuration["configuration"]["microscopes"][microscope_name]["camera"][
                "delay"
            ]
            / 1000
        )

        # Waveform Parameters
        #: float: Remote focus max voltage.
        self.remote_focus_max_voltage = self.device_config["hardware"]["max"]

        #: float: Remote focus min voltage.
        self.remote_focus_min_voltage = self.device_config["hardware"]["min"]

        #: dict: Waveform dictionary.
        self.waveform_dict = {}

    def __str__(self):
        """String representation of the RemoteFocusBase class."""
        return "RemoteFocusBase"

    def __del__(self):
        """Destructor"""
        pass

    def adjust(self, exposure_times, sweep_times, offset=None):
        """Adjusts the remote focus waveform based on the readout time.

        Parameters
        ----------
        exposure_times : dict
            Dictionary of exposure times for each selected channel
        sweep_times : dict
            Dictionary of sweep times for each selected channel

        Returns
        -------
        waveform : numpy.ndarray
            Waveform for the remote focus device.
        """
        # to determine if the waveform has to be triangular
        sensor_mode = self.configuration["experiment"]["CameraParameters"][
            self.microscope_name
        ]["sensor_mode"]
        readout_direction = self.configuration["experiment"]["CameraParameters"][
            self.microscope_name
        ]["readout_direction"]

        self.waveform_dict = dict.fromkeys(self.waveform_dict, None)
        microscope_state = self.configuration["experiment"]["MicroscopeState"]
        waveform_constants = self.configuration["waveform_constants"]
        imaging_mode = microscope_state["microscope_name"]
        zoom = microscope_state["zoom"]
        # ramp_type = self.configuration["configuration"]["microscopes"][
        #     self.microscope_name]['remote focus device']['ramp_type']
        self.sample_rate = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["daq"]["sample_rate"]

        remote_focus_ramp_falling = (
            float(waveform_constants["other_constants"]["remote_focus_ramp_falling"])
            / 1000
        )
        remote_focus_delay = (
            float(waveform_constants["other_constants"]["remote_focus_delay"]) / 1000
        )
        percent_smoothing = float(
            waveform_constants["other_constants"]["percent_smoothing"]
        )

        for channel_key in microscope_state["channels"].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state["channels"][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel["is_selected"] is True:

                # Get the Waveform Parameters - Assumes ETL Delay < Camera Delay.
                # Should Assert.
                laser = channel["laser"]
                exposure_time = exposure_times[channel_key]
                self.sweep_time = sweep_times[channel_key]

                samples = int(self.sample_rate * self.sweep_time)

                # Remote Focus Parameters
                temp = waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                    laser
                ]["amplitude"]
                if temp == "-" or temp == ".":
                    waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                        laser
                    ]["amplitude"] = "0"

                remote_focus_amplitude = float(
                    waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                        laser
                    ]["amplitude"]
                )

                # Validation for when user puts a '-' in spinbox
                temp = waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                    laser
                ]["offset"]
                if temp == "-" or temp == ".":
                    waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                        laser
                    ]["offset"] = "0"

                remote_focus_offset = float(
                    waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                        laser
                    ]["offset"]
                )
                if offset is not None:
                    remote_focus_offset += offset

                # Calculate the Waveforms
                if sensor_mode == "Light-Sheet" and (
                    readout_direction == "Bidirectional"
                    or readout_direction == "Rev. Bidirectional"
                ):
                    self.waveform_dict[channel_key] = remote_focus_ramp_triangular(
                        sample_rate=self.sample_rate,
                        exposure_time=exposure_time,
                        sweep_time=self.sweep_time,
                        remote_focus_delay=remote_focus_delay,
                        camera_delay=self.camera_delay,
                        amplitude=remote_focus_amplitude,
                        offset=remote_focus_offset,
                    )
                    samples *= 2

                else:
                    self.waveform_dict[channel_key] = remote_focus_ramp(
                        sample_rate=self.sample_rate,
                        exposure_time=exposure_time,
                        sweep_time=self.sweep_time,
                        remote_focus_delay=remote_focus_delay,
                        camera_delay=self.camera_delay,
                        fall=remote_focus_ramp_falling,
                        amplitude=remote_focus_amplitude,
                        offset=remote_focus_offset,
                    )

                # Smooth the Waveform if specified
                if percent_smoothing > 0:
                    self.waveform_dict[channel_key] = smooth_waveform(
                        waveform=self.waveform_dict[channel_key],
                        percent_smoothing=percent_smoothing,
                    )[:samples]

                # Clip any values outside of the hardware limits
                self.waveform_dict[channel_key][
                    self.waveform_dict[channel_key] > self.remote_focus_max_voltage
                ] = self.remote_focus_max_voltage
                self.waveform_dict[channel_key][
                    self.waveform_dict[channel_key] < self.remote_focus_min_voltage
                ] = self.remote_focus_min_voltage

        return self.waveform_dict
