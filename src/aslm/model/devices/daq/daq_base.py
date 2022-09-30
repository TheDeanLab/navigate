"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

# Standard Imports
import logging

# Third Party Imports

# Local Imports
from aslm.model.aslm_model_waveforms import tunable_lens_ramp, sawtooth, camera_exposure

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class DAQBase:
    r"""Parent class for Data Acquisition (DAQ) classes.

    Attributes
    ----------
    configuration : Configurator
        Global configuration of the microscope
    experiment : Configurator
        Experiment configuration of the microscope
    etl_constants : dict
        Dictionary with all of the wavelength, magnification, and imaging mode-specific amplitudes/offsets
    """

    def __init__(self, configuration):
        self.configuration = configuration
        self.etl_constants = self.configuration['etl_constants']
        self.microscope_name = self.configuration['experiment']['MicroscopeState']['resolution_mode']
        self.daq_parameters = self.configuration['configuration']['microscopes'][self.microscope_name]['daq']

        # Initialize Variables
        self.sample_rate = self.daq_parameters['sample_rate']
        self.sweep_time = self.daq_parameters['sweep_time']

        # ETL Parameters
        self.etl_ramp_falling = {}
        for m in self.configuration['configuration']['microscopes'].keys():
            self.etl_ramp_falling[m] = self.configuration['configuration']['microscopes'][m]['remote_focus_device']['ramp_rising_percent']

        # Camera Parameters
        self.camera_delay_percent = self.configuration['configuration']['microscopes'][self.microscope_name]['camera']['delay_percent']
        self.camera_pulse_percent = self.configuration['configuration']['microscopes'][self.microscope_name]['camera']['pulse_percent']
        self.camera_high_time = self.camera_pulse_percent * 0.01 * self.sweep_time
        self.camera_delay = self.camera_delay_percent * 0.01 * self.sweep_time

        self.waveform_dict = {}
        for i in range(int(configuration['configuration']['gui']['channels']['count'])):
            self.waveform_dict['channel_'+str(i+1)] = None

    def calculate_all_waveforms(self, microscope_name, readout_time):
        r"""Pre-calculates all waveforms necessary for the acquisition and organizes in a dictionary format.

            Parameters
            ----------
            microscope_name : str
                Name of the active microscope
            readout_time : float
                Readout time of the camera (seconds) if we are operating the camera in Normal mode, otherwise -1.

            Returns
            -------
            self.waveform_dict : dict
                Dictionary of waveforms to pass to galvo and ETL, plus a camera waveform for display purposes.
            """
        self.enable_microscope(microscope_name)

        microscope_state = self.configuration['experiment']['MicroscopeState']
        self.camera_delay_percent = self.configuration['configuration']['microscopes'][microscope_name]['camera']['delay_percent']
        self.sample_rate = self.configuration['configuration']['microscopes'][microscope_name]['daq']['sample_rate']
        
        # Iterate through the dictionary.
        for channel_key in microscope_state['channels'].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state['channels'][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel['is_selected'] is True:
                exposure_time = channel['camera_exposure_time'] / 1000
                self.sweep_time = exposure_time + exposure_time * ((self.camera_delay_percent + self.etl_ramp_falling[microscope_name]) / 100)
                if readout_time > 0:
                    # This addresses the dovetail nature of the camera readout in normal mode. The camera reads middle
                    # out, and the delay in start of the last lines compared to the first lines causes the exposure
                    # to be net longer than exposure_time. This helps the galvo keep sweeping for the full camera
                    # exposure time.
                    self.sweep_time += readout_time

                self.waveform_dict[channel_key] = camera_exposure(sample_rate=self.sample_rate,
                                                                                     sweep_time=self.sweep_time,
                                                                                     exposure=exposure_time,
                                                                                     camera_delay=self.camera_delay_percent)

        return self.waveform_dict

    def enable_microscope(self, microscope_name):
        if microscope_name != self.microscope_name:
            self.microscope_name = microscope_name