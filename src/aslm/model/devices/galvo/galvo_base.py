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

#  Standard Library Imports
import logging

# Third Party Imports

# Local Imports
from aslm.model.aslm_model_waveforms import sawtooth

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class GalvoBase:
    r"""GalvoBase Class

     Parent class for voice coil models.
     """

    def __init__(self, microscope_name, device_connection, configuration, galvo_id=0):
        self.configuration = configuration
        self.microscope_name = microscope_name
        self.device_config = configuration['configuration']['microscopes'][microscope_name]['galvo'][galvo_id]
        self.sample_rate = configuration['configuration']['microscopes'][microscope_name]['daq']['sample_rate']
        self.sweep_time = configuration['configuration']['microscopes'][microscope_name]['daq']['sweep_time']
        self.camera_delay_percent = configuration['configuration']['microscopes'][microscope_name]['camera']['delay_percent']
        self.galvo_max_voltage = self.device_config['hardware']['max']
        self.galvo_min_voltage = self.device_config['hardware']['min']
        self.etl_ramp_falling = configuration['configuration']['microscopes'][microscope_name]['remote_focus_device']['ramp_falling_percent']

        self.samples = int(self.sample_rate * self.sweep_time)

        self.waveform_dict = {}
        for i in range(int(configuration['configuration']['gui']['channels']['count'])):
            self.waveform_dict['channel_'+str(i+1)] = None

    def __del__(self):
        pass

    def adjust(self, readout_time):
        # calculate waveform
        microscope_state = self.configuration['experiment']['MicroscopeState']
        galvo_parameters = self.configuration['experiment']['GalvoParameters'][self.microscope_name]

        for channel_key in microscope_state['channels'].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state['channels'][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel['is_selected'] is True:

                # Get the Waveform Parameters - Assumes ETL Delay < Camera Delay.  Should Assert.
                exposure_time = channel['camera_exposure_time'] / 1000
                self.sweep_time = exposure_time + exposure_time * ((self.camera_delay_percent + self.etl_ramp_falling) / 100)
                if readout_time > 0:
                    # This addresses the dovetail nature of the camera readout in normal mode. The camera reads middle
                    # out, and the delay in start of the last lines compared to the first lines causes the exposure
                    # to be net longer than exposure_time. This helps the galvo keep sweeping for the full camera
                    # exposure time.
                    self.sweep_time += readout_time
                self.samples = int(self.sample_rate * self.sweep_time)

                # galvo Parameters
                galvo_amplitude = float(galvo_parameters.get('amplitude', 0))
                galvo_offset = float(galvo_parameters.get('offset', 0))
                galvo_frequency = float(galvo_parameters.get('frequency', 0)) / exposure_time

                # Calculate the Waveforms
                self.waveform_dict[channel_key] = sawtooth(sample_rate=self.sample_rate,
                                                            sweep_time=self.sweep_time,
                                                            frequency=galvo_frequency,
                                                            amplitude=galvo_amplitude,
                                                            offset=galvo_offset,
                                                            phase=(self.camera_delay_percent/100)*exposure_time)
                self.waveform_dict[channel_key][self.waveform_dict[channel_key] > self.galvo_max_voltage] = self.galvo_max_voltage
                self.waveform_dict[channel_key][self.waveform_dict[channel_key] < self.galvo_min_voltage] = self.galvo_min_voltage

        return self.waveform_dict

    def prepare_task(self, channel_key):
        pass
    
    def start_task(self):
        pass

    def stop_task(self):
        pass

    def close_task(self):
        pass
