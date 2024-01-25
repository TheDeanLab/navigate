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


# Standard Imports
import logging

# Third Party Imports

# Local Imports
from navigate.model.waveforms import camera_exposure

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class DAQBase:
    """DAQBase - Parent class for Data Acquisition (DAQ) classes."""

    def __init__(self, configuration):
        """Initializes the DAQBase class.

        Parameters
        ----------
        configuration : dict
            Dictionary of configuration parameters
        """

        #: dict: Dictionary of configuration parameters
        self.configuration = configuration

        #: dict: Dictionary of waveform constants
        self.waveform_constants = self.configuration["waveform_constants"]

        #: str: Name of the active microscope
        self.microscope_name = self.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ]

        #: dict: Dictionary of DAQ parameters
        self.daq_parameters = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["daq"]

        # Initialize Variables
        #: float: Sample rate of the DAQ
        self.sample_rate = self.daq_parameters["sample_rate"]

        #: dict: Sweep times for different channels
        self.sweep_times = None
        
        #: dict: exposure times for different channels
        self.exposure_times = None

        # Remote Focus Parameters
        #: dict: Dictionary of remote focus ramp falling percentages
        self.remote_focus_ramp_falling = {}
        for m in self.configuration["configuration"]["microscopes"].keys():
            self.remote_focus_ramp_falling[m] = self.configuration["configuration"][
                "microscopes"
            ][m]["remote_focus_device"]["ramp_falling_percent"]

        # Camera Parameters
        #: float: Camera delay percentage
        self.camera_delay_percent = self.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["camera"]["delay_percent"]

        #: dict: Dictionary of waveforms.
        self.waveform_dict = {}

        #: int: Number of times to repeat the waveform
        self.waveform_repeat_num = 1

        #: int: Number of times to expand the waveform
        self.waveform_expand_num = 1

    def calculate_all_waveforms(self, microscope_name, exposure_times, sweep_times):
        """Pre-calculates all waveforms necessary for the acquisition and organizes in
        a dictionary format.

        Parameters
        ----------
        microscope_name : str
            Name of the active microscope
        exposure_times : dict
            Dictionary of exposure times for each selected channel
        sweep_times : dict
            Dictionary of sweep times for each selected channel

        Returns
        -------
        self.waveform_dict : dict
            Dictionary of waveforms to pass to galvo and ETL, plus a camera waveform for
            display purposes.
        """
        self.exposure_times = exposure_times
        self.sweep_times = sweep_times
        self.waveform_dict = dict.fromkeys(self.waveform_dict, None)
        self.enable_microscope(microscope_name)

        microscope_state = self.configuration["experiment"]["MicroscopeState"]

        # Iterate through the dictionary.
        for channel_key in microscope_state["channels"].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state["channels"][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel["is_selected"] is True:
                exposure_time = exposure_times[channel_key]
                sweep_time = sweep_times[channel_key]

                # Create 5V TTL for 1 camera exposure.
                self.waveform_dict[channel_key] = camera_exposure(
                    sample_rate=self.sample_rate,
                    sweep_time=sweep_time,
                    exposure=exposure_time,
                    camera_delay=self.camera_delay_percent,
                )

        return self.waveform_dict

    def enable_microscope(self, microscope_name):
        """Enables the microscope.

        Parameters
        ----------
        microscope_name : str
            Name of the active microscope
        """
        if microscope_name != self.microscope_name:
            self.microscope_name = microscope_name

        self.camera_delay_percent = self.configuration["configuration"]["microscopes"][
            microscope_name
        ]["camera"]["delay_percent"]
        self.sample_rate = self.configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["sample_rate"]
