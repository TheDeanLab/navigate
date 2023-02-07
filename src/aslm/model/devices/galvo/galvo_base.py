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
#

#  Standard Library Imports
import logging

# Third Party Imports
import numpy as np

# Local Imports
from aslm.model.waveforms import sawtooth

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class GalvoBase:
    """GalvoBase Class

    Parent class for galvanometers.
    """

    def __init__(self, microscope_name, device_connection, configuration, galvo_id=0):
        self.configuration = configuration
        self.microscope_name = microscope_name
        self.galvo_name = "Galvo " + str(galvo_id)
        self.device_config = configuration["configuration"]["microscopes"][
            microscope_name
        ]["galvo"][galvo_id]
        self.sample_rate = configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["sample_rate"]
        self.sweep_time = configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["sweep_time"]
        self.camera_delay_percent = configuration["configuration"]["microscopes"][
            microscope_name
        ]["camera"]["delay_percent"]
        self.galvo_max_voltage = self.device_config["hardware"]["max"]
        self.galvo_min_voltage = self.device_config["hardware"]["min"]
        self.remote_focus_ramp_falling = configuration["configuration"]["microscopes"][
            microscope_name
        ]["remote_focus_device"]["ramp_falling_percent"]

        self.samples = int(self.sample_rate * self.sweep_time)

        self.waveform_dict = {}
        for k in configuration["configuration"]["gui"]["channels"].keys():
            self.waveform_dict[k] = None

    def __del__(self):
        """Destructor"""
        pass

    def adjust(self, readout_time):
        """Adjust the galvo waveform to account for the camera readout time.

        Parameters
        ----------
        readout_time : float
            Camera readout time in seconds.

        Returns
        -------
        None

        Examples
        --------
        >>> galvo.adjust(0.1)
        """
        self.waveform_dict = dict.fromkeys(self.waveform_dict, None)
        # calculate waveform
        microscope_state = self.configuration["experiment"]["MicroscopeState"]
        microscope_name = microscope_state["microscope_name"]
        zoom_value = microscope_state["zoom"]
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
                self.samples = int(self.sample_rate * self.sweep_time)

                # galvo Parameters
                galvo_amplitude = float(galvo_parameters.get("amplitude", 0))
                galvo_offset = float(galvo_parameters.get("offset", 0))
                galvo_frequency = (
                    float(galvo_parameters.get("frequency", 0)) / exposure_time
                )

                # Calculate the Waveforms
                self.waveform_dict[channel_key] = sawtooth(
                    sample_rate=self.sample_rate,
                    sweep_time=self.sweep_time,
                    frequency=galvo_frequency,
                    amplitude=galvo_amplitude,
                    offset=galvo_offset,
                    phase=(self.camera_delay_percent / 100) * exposure_time,
                )
                self.waveform_dict[channel_key][
                    self.waveform_dict[channel_key] > self.galvo_max_voltage
                ] = self.galvo_max_voltage
                self.waveform_dict[channel_key][
                    self.waveform_dict[channel_key] < self.galvo_min_voltage
                ] = self.galvo_min_voltage

                if microscope_state["image_mode"] == "confocal-projection":
                    self.waveform_dict[channel_key] = np.hstack(
                        [self.waveform_dict[channel_key]]
                        * int(microscope_state["n_plane"])
                    )
                    self.samples = int(
                        self.sample_rate * self.sweep_time * microscope_state["n_plane"]
                    )

        return self.waveform_dict

    def prepare_task(self, channel_key):
        """Prepare the task for the given channel.

        Parameters
        ----------
        channel_key : str
            Channel key.

        Returns
        -------
        None

        Examples
        --------
        >>> galvo.prepare_task('488')
        """

        pass

    def start_task(self):
        """Start the task.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> galvo.start_task()
        """

        pass

    def stop_task(self):
        """Stop the task.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> galvo.stop_task()
        """
        pass

    def close_task(self):
        """Close the task.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> galvo.close_task()
        """
        pass
