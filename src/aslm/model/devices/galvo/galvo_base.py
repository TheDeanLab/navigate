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

# Local Imports
from aslm.model.waveforms import sawtooth, sine_wave

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class GalvoBase:
    """GalvoBase Class

    Parent class for galvanometers.

    Parameters
    ----------
    microscope_name : str
        Microscope name.
    device_connection : str
        Device connection.
    configuration : dict
        Configuration dictionary.
    galvo_id : int, optional
        Galvo ID, by default 0

    Attributes
    ----------
    configuration : dict
        Configuration dictionary.
    microscope_name : str
        Microscope name.
    galvo_name : str
        Galvo name.
    device_config : dict
        Device configuration dictionary.
    sample_rate : int
        Sample rate.
    sweep_time : float
        Sweep time.
    camera_delay_percent : float
        Camera delay percent.
    galvo_max_voltage : float
        Galvo maximum voltage.
    galvo_min_voltage : float
        Galvo minimum voltage.
    remote_focus_ramp_falling : float
        Remote focus ramp falling percent.
    samples : int
        Number of samples.
    waveform_dict : dict
        Waveform dictionary.

    Methods
    -------
    prepare_task(channel_key)
        Prepare the task for the given channel.
    start_task()
        Start the task.
    stop_task()
        Stop the task.
    close_task()
        Close the task.
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

        # Galvo Waveform Information
        self.galvo_waveform = self.device_config.get("waveform", "sawtooth")

        self.samples = int(self.sample_rate * self.sweep_time)

        self.waveform_dict = {}

    def __del__(self):
        """Destructor"""
        pass

    def adjust(self, exposure_times, sweep_times):
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
        >>> galvo.adjust(exposure_times, sweep_times)
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
                exposure_time = exposure_times[channel_key]
                self.sweep_time = sweep_times[channel_key]

                self.samples = int(self.sample_rate * self.sweep_time)

                # galvo Parameters
                try:
                    galvo_amplitude = float(galvo_parameters.get("amplitude", 0))
                    galvo_offset = float(galvo_parameters.get("offset", 0))
                    galvo_frequency = (
                        float(galvo_parameters.get("frequency", 0)) / exposure_time
                    )
                except ValueError as e:
                    logger.error(
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
                        phase=(self.camera_delay_percent / 100) * exposure_time,
                    )
                    print("sawtooth amplitude")
                    print(galvo_amplitude)
                elif self.galvo_waveform == "sine":
                    self.waveform_dict[channel_key] = sine_wave(
                        sample_rate=self.sample_rate,
                        sweep_time=self.sweep_time,
                        frequency=galvo_frequency,
                        amplitude=galvo_amplitude,
                        offset=galvo_offset,
                        phase=self.device_config["phase"],
                    )
                else:
                    print(
                        "Mistakes were made. "
                        "Unknown waveform specified in configuration file."
                    )
                    self.waveform_dict[channel_key] = None
                    continue
                self.waveform_dict[channel_key][
                    self.waveform_dict[channel_key] > self.galvo_max_voltage
                ] = self.galvo_max_voltage
                self.waveform_dict[channel_key][
                    self.waveform_dict[channel_key] < self.galvo_min_voltage
                ] = self.galvo_min_voltage

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

    def turn_off(self):
        pass
