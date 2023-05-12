# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Third Party Imports
import numpy as np

# Local Imports
from aslm.model.waveforms import remote_focus_ramp, smooth_waveform

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class RemoteFocusBase:
    """RemoteFocusBase Class

    Parent class for Remote Focusing Device.

    Attributes
    ----------
    configuration : dict
        Configuration dictionary.
    microscope_name : str
        Microscope name.
    device_config : dict
        Remote focus device configuration dictionary.
    sample_rate : int
        Sample rate.
    sweep_time : float
        Sweep time.
    camera_delay_percent : float
        Camera delay percent.
    remote_focus_delay : float
        Remote focus delay percent.
    remote_focus_ramp_falling : float
        Remote focus ramp falling percent.
    remote_focus_max_voltage : float
        Remote focus maximum voltage.
    remote_focus_min_voltage : float
        Remote focus minimum voltage.
    samples : int
        Number of samples.
    waveform_dict : dict
        Dictionary of waveforms.

    Methods
    -------
    prepare_task(channel_key)
        Prepares the task for the remote focus device.
    start_task()
        Starts the task for the remote focus device.
    stop_task()
        Stops the task for the remote focus device.
    close_task()
        Closes the task for the remote focus device.
    """

    def __init__(self, microscope_name, device_connection, configuration):

        self.configuration = configuration
        self.microscope_name = microscope_name
        self.device_config = configuration["configuration"]["microscopes"][
            microscope_name
        ]["remote_focus_device"]
        self.sample_rate = configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["sample_rate"]
        self.sweep_time = configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["sweep_time"]
        self.camera_delay_percent = configuration["configuration"]["microscopes"][
            microscope_name
        ]["camera"]["delay_percent"]

        # Waveform Parameters
        self.remote_focus_delay = self.device_config.get("delay_percent", 7.5)
        self.percent_smoothing = self.device_config.get("smoothing", 0)
        self.remote_focus_ramp_falling = self.device_config["ramp_falling_percent"]
        self.remote_focus_max_voltage = self.device_config["hardware"]["max"]
        self.remote_focus_min_voltage = self.device_config["hardware"]["min"]
        self.samples = int(self.sample_rate * self.sweep_time)
        self.waveform_dict = {}

    def __del__(self):
        """Destructor"""
        pass

    def adjust(self, readout_time):
        """Adjusts the remote focus waveform based on the readout time.

        Parameters
        ----------
        readout_time : float
            Readout time in seconds.

        Returns
        -------
        waveform : numpy.ndarray
            Waveform for the remote focus device.

        Examples
        --------
        >>> remote_focus.adjust(0.1)
        """

        # calculate waveform
        self.waveform_dict = dict.fromkeys(self.waveform_dict, None)
        microscope_state = self.configuration["experiment"]["MicroscopeState"]
        waveform_constants = self.configuration["waveform_constants"]
        imaging_mode = microscope_state["microscope_name"]
        zoom = microscope_state["zoom"]
        self.sample_rate = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["daq"]["sample_rate"]
        # duty wait duration
        duty_cycle_wait_duration = (
            float(
                waveform_constants.get("other_constants", {}).get(
                    "remote_focus_settle_duration", 0
                )
            )
            / 1000
        )

        for channel_key in microscope_state["channels"].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state["channels"][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel["is_selected"] is True:

                # Get the Waveform Parameters - Assumes ETL Delay < Camera Delay.
                # Should Assert.
                laser = channel["laser"]
                exposure_time = channel["camera_exposure_time"] / 1000
                self.sweep_time = exposure_time + exposure_time * (
                    (self.camera_delay_percent + self.remote_focus_ramp_falling) / 100
                )
                if readout_time > 0:
                    # This addresses the dovetail nature of the camera readout in normal
                    # mode. The camera reads middle out, and the delay in start of the
                    # last lines compared to the first lines causes the exposure to be
                    # net longer than exposure_time. This helps the galvo keep sweeping
                    # for the full camera exposure time.
                    self.sweep_time += readout_time

                self.sweep_time += duty_cycle_wait_duration

                self.samples = int(self.sample_rate * self.sweep_time)

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

                self.remote_focus_delay = float(
                    waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                        laser
                    ]["percent_delay"]
                )
                self.percent_smoothing = float(
                    waveform_constants["remote_focus_constants"][imaging_mode][zoom][
                        laser
                    ]["percent_smoothing"]
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

                # Calculate the Waveforms
                self.waveform_dict[channel_key] = remote_focus_ramp(
                    sample_rate=self.sample_rate,
                    exposure_time=exposure_time,
                    sweep_time=self.sweep_time,
                    remote_focus_delay=self.remote_focus_delay,
                    camera_delay=self.camera_delay_percent,
                    fall=self.remote_focus_ramp_falling,
                    amplitude=remote_focus_amplitude,
                    offset=remote_focus_offset,
                )

                # Smooth the Waveform if specified
                if self.percent_smoothing > 0:
                    self.waveform_dict[channel_key] = smooth_waveform(
                        waveform=self.waveform_dict[channel_key],
                        percent_smoothing=self.percent_smoothing,
                    )

                # Clip any values outside of the hardware limits
                self.waveform_dict[channel_key][
                    self.waveform_dict[channel_key] > self.remote_focus_max_voltage
                ] = self.remote_focus_max_voltage
                self.waveform_dict[channel_key][
                    self.waveform_dict[channel_key] < self.remote_focus_min_voltage
                ] = self.remote_focus_min_voltage


        return self.waveform_dict

    def prepare_task(self, channel_key):
        """Prepares the task for the remote focus device.

        Parameters
        ----------
        channel_key : str
            Channel key.

        Returns
        -------
        task : nidaqmx.Task
            Task for the remote focus device.

        Examples
        --------
        >>> remote_focus.prepare_task('488')
        """

        pass

    def start_task(self):
        """Starts the task for the remote focus device.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> remote_focus.start_task()
        """

        pass

    def stop_task(self):
        """Stops the task for the remote focus device.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> remote_focus.stop_task()
        """

        pass

    def close_task(self):
        pass
