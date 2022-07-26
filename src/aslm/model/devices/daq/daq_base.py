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
    configuration : Session
        Global configuration of the microscope
    experiment : Session
        Experiment configuration of the microscope
    etl_constants : dict
        Dictionary with all of the wavelength, magnification, and imaging mode-specific amplitudes/offsets
    """

    def __init__(self, configuration, experiment, etl_constants):
        self.configuration = configuration
        self.experiment = experiment
        self.etl_constants = etl_constants

        # Initialize Variables
        self.sample_rate = self.configuration.DAQParameters['sample_rate']
        self.sweep_time = self.configuration.DAQParameters['sweep_time']
        self.samples = int(self.sample_rate * self.sweep_time)

        # New DAQ Attempt
        self.etl_delay = self.configuration.RemoteFocusParameters['remote_focus_l_delay_percent']
        self.etl_ramp_rising = self.configuration.RemoteFocusParameters['remote_focus_l_ramp_rising_percent']
        self.etl_ramp_falling = self.configuration.RemoteFocusParameters['remote_focus_l_ramp_falling_percent']

        # ETL Parameters
        self.etl_l_waveform = None
        self.etl_l_delay = self.configuration.RemoteFocusParameters['remote_focus_l_delay_percent']
        self.etl_l_ramp_rising = self.configuration.RemoteFocusParameters['remote_focus_l_ramp_rising_percent']
        self.etl_l_ramp_falling = self.configuration.RemoteFocusParameters['remote_focus_l_ramp_falling_percent']
        self.etl_l_amplitude = self.configuration.RemoteFocusParameters['remote_focus_l_amplitude']
        self.etl_l_offset = self.configuration.RemoteFocusParameters['remote_focus_l_offset']
        self.etl_l_min_ao = self.configuration.RemoteFocusParameters['remote_focus_l_min_ao']
        self.etl_l_max_ao = self.configuration.RemoteFocusParameters['remote_focus_l_max_ao']

        # Remote Focus Parameters
        self.etl_r_waveform = None
        self.etl_r_delay = self.configuration.RemoteFocusParameters['remote_focus_r_delay_percent']
        self.etl_r_ramp_rising = self.configuration.RemoteFocusParameters['remote_focus_r_ramp_rising_percent']
        self.etl_r_ramp_falling = self.configuration.RemoteFocusParameters['remote_focus_r_ramp_falling_percent']
        self.etl_r_amplitude = self.configuration.RemoteFocusParameters['remote_focus_r_amplitude']
        self.etl_r_offset = self.configuration.RemoteFocusParameters['remote_focus_r_offset']
        self.etl_r_min_ao = self.configuration.RemoteFocusParameters['remote_focus_r_min_ao']
        self.etl_r_max_ao = self.configuration.RemoteFocusParameters['remote_focus_r_max_ao']

        # ETL history parameters
        self.prev_etl_r_amplitude = self.etl_r_amplitude
        self.prev_etl_r_offset = self.etl_r_offset
        self.prev_etl_l_amplitude = self.etl_l_amplitude
        self.prev_etl_l_offset = self.etl_l_offset

        # Bundled Waveform
        self.galvo_and_etl_waveforms = None

        # Left Galvo Parameters
        self.galvo_l_waveform = None
        self.galvo_l_frequency = self.configuration.GalvoParameters['galvo_l_frequency']
        self.galvo_l_amplitude = self.configuration.GalvoParameters['galvo_l_amplitude']
        self.galvo_l_offset = self.configuration.GalvoParameters['galvo_l_offset']
        self.galvo_l_duty_cycle = self.configuration.GalvoParameters['galvo_l_duty_cycle']
        self.galvo_l_phase = self.configuration.GalvoParameters['galvo_l_phase']
        self.galvo_l_min_ao = self.configuration.GalvoParameters['galvo_l_min_ao']
        self.galvo_l_max_ao = self.configuration.GalvoParameters['galvo_l_max_ao']

        # Right Galvo Parameters
        self.galvo_r_waveform = None
        self.galvo_r_frequency = None
        self.galvo_r_amplitude = self.configuration.GalvoParameters.get('galvo_r_amplitude', 0)
        self.galvo_r_offset = self.configuration.GalvoParameters.get('galvo_r_offset', 0)
        self.galvo_r_duty_cycle = None
        self.galvo_r_phase = None
        self.galvo_r_max_ao = self.configuration.GalvoParameters['galvo_r_max_ao']
        self.galvo_r_min_ao = self.configuration.GalvoParameters['galvo_r_min_ao']

        # Camera Parameters
        self.camera_delay_percent = self.configuration.CameraParameters['delay_percent']
        self.camera_pulse_percent = self.configuration.CameraParameters['pulse_percent']
        self.camera_high_time = self.camera_pulse_percent * 0.01 * self.sweep_time
        self.camera_delay = self.camera_delay_percent * 0.01 * self.sweep_time

        # Laser Parameters
        self.laser_ao_waveforms = None
        self.laser_do_waveforms = None
        self.number_of_lasers = self.configuration.LaserParameters['number_of_lasers']
        self.laser_l_delay = self.configuration.LaserParameters['laser_l_delay_percent']
        self.laser_l_pulse = self.configuration.LaserParameters['laser_l_pulse_percent']

        self.laser_power = 0
        self.laser_idx = 0
        self.imaging_mode = None

        self.waveform_dict = {
            'channel_1':
                {'etl_waveform': None,
                 'galvo_waveform': None,
                 'camera_waveform': None},
            'channel_2':
                {'etl_waveform': None,
                 'galvo_waveform': None,
                 'camera_waveform': None},
            'channel_3':
                {'etl_waveform': None,
                 'galvo_waveform': None,
                 'camera_waveform': None},
            'channel_4':
                {'etl_waveform': None,
                 'galvo_waveform': None,
                 'camera_waveform': None},
            'channel_5':
                {'etl_waveform': None,
                 'galvo_waveform': None,
                 'camera_waveform': None}
        }

    def calculate_all_waveforms(self, microscope_state, etl_constants, galvo_parameters, readout_time):
        r"""Pre-calculates all waveforms necessary for the acquisition and organizes in a dictionary format.

            Parameters
            ----------
            microscope_state : dict
                Dictionary of experiment MicroscopeState parameters (see config/experiment.yml)
            etl_constants : dict
                Dictionary of ETL parameters (see config/etl_constants.yml)
            galvo_parameters : dict
                Dictionary of experiment GalvoParameters parameters (see config/experiment.yml)
            readout_time : float
                Readout time of the camera (seconds) if we are operating the camera in Normal mode, otherwise -1.

            Returns
            -------
            self.waveform_dict : dict
                Dictionary of waveforms to pass to galvo and ETL, plus a camera waveform for display purposes.
            """

        # Imaging Mode = 'high' or 'low'
        self.imaging_mode = microscope_state['resolution_mode']

        # Zoom = 'N/A' in high resolution mode, or '0.63x', '1x', '2x'... in low-resolution mode.
        if self.imaging_mode == 'high':
            focus_prefix = 'r'
            zoom = 'N/A'  # TODO: Why do I need this safety check here? It seems that zoom update lags imaging mode update.
        else:
            focus_prefix = 'l'
            zoom = microscope_state['zoom']

        # Iterate through the dictionary.
        for channel_key in microscope_state['channels']:
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state['channels'][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel['is_selected'] is True:

                # Get the Waveform Parameters - Assumes ETL Delay < Camera Delay.  Should Assert.
                laser = channel['laser']
                exposure_time = channel['camera_exposure_time'] / 1000
                self.sweep_time = exposure_time + exposure_time * ((self.camera_delay_percent + self.etl_ramp_falling) / 100)
                if readout_time > 0:
                    # This addresses the dovetail nature of the camera readout in normal mode. The camera reads middle
                    # out, and the delay in start of the last lines compared to the first lines causes the exposure
                    # to be net longer than exposure_time. This helps the galvo keep sweeping for the full camera
                    # exposure time.
                    self.sweep_time += readout_time

                # ETL Parameters
                etl_amplitude = float(etl_constants.ETLConstants[self.imaging_mode][zoom][laser]['amplitude'])
                etl_offset = float(etl_constants.ETLConstants[self.imaging_mode][zoom][laser]['offset'])

                # Galvo Parameters
                galvo_amplitude = float(galvo_parameters.get(f'galvo_{focus_prefix}_amplitude', 0))
                galvo_offset = float(galvo_parameters.get(f'galvo_{focus_prefix}_offset', 0))

                # We need the camera to experience N sweeps of the galvo. As such,
                # frequency should divide evenly into exposure_time
                galvo_frequency = float(galvo_parameters.get(f'galvo_{focus_prefix}_frequency',0))/exposure_time  # 100.5/exposure_time

                # Calculate the Waveforms
                self.waveform_dict[channel_key]['etl_waveform'] = tunable_lens_ramp(sample_rate=self.sample_rate,
                                                                                       exposure_time=exposure_time,
                                                                                       sweep_time=self.sweep_time,
                                                                                       etl_delay=self.etl_delay,
                                                                                       camera_delay=self.camera_delay_percent,
                                                                                       fall=self.etl_ramp_falling,
                                                                                       amplitude=etl_amplitude,
                                                                                       offset=etl_offset)

                self.waveform_dict[channel_key]['galvo_waveform'] = sawtooth(sample_rate=self.sample_rate,
                                                                             sweep_time=self.sweep_time,
                                                                             frequency=galvo_frequency,
                                                                             amplitude=galvo_amplitude,
                                                                             offset=galvo_offset,
                                                                             phase=(self.camera_delay_percent/100)*exposure_time)

                self.waveform_dict[channel_key]['camera_waveform'] = camera_exposure(sample_rate=self.sample_rate,
                                                                                     sweep_time=self.sweep_time,
                                                                                     exposure=exposure_time,
                                                                                     camera_delay=self.camera_delay_percent)

                # Confirm that the values are between the minimum and maximum voltages.
                max_etl_voltage = getattr(self, f"etl_{focus_prefix}_max_ao")
                min_etl_voltage = getattr(self, f"etl_{focus_prefix}_min_ao")
                max_galvo_voltage = getattr(self, f"galvo_{focus_prefix}_max_ao")
                min_galvo_voltage = getattr(self, f"galvo_{focus_prefix}_min_ao")

                # Clip waveforms with min and max.
                self.waveform_dict[channel_key]['etl_waveform'][self.waveform_dict[channel_key]['etl_waveform'] >
                                                                max_etl_voltage] = max_etl_voltage
                self.waveform_dict[channel_key]['etl_waveform'][self.waveform_dict[channel_key]['etl_waveform'] <
                                                                min_etl_voltage] = min_etl_voltage
                self.waveform_dict[channel_key]['galvo_waveform'][self.waveform_dict[channel_key]['galvo_waveform'] >
                                                                max_galvo_voltage] = max_galvo_voltage
                self.waveform_dict[channel_key]['galvo_waveform'][self.waveform_dict[channel_key]['galvo_waveform'] <
                                                                min_galvo_voltage] = min_galvo_voltage

        return self.waveform_dict

    def calculate_samples(self):
        r"""Calculate the number of samples for the waveforms.
        Product of the sampling frequency and the duration of the waveform/exposure time in seconds."""
        self.samples = int(self.sample_rate * self.sweep_time)

    def update_etl_parameters(self, microscope_state, channel, galvo_parameters, readout_time):
        r"""Update the ETL parameters according to the zoom and excitation wavelength.

        Parameters
        ----------
        microscope_state : dict
            Dictionary of current experimental configuration.  Derivied from experiment Session object.
        channel : int
            Current microscope channel
        galvo_parameters : dict
            Dictionary of experiment GalvoParameters parameters (see config/experiment.yml).
        readout_time : float
            Duration of time necessary to readout a camera frame.
        """
        laser, resolution_mode, zoom = channel['laser'], microscope_state['resolution_mode'],  microscope_state['zoom']
        remote_focus_dict = self.etl_constants.ETLConstants[resolution_mode][zoom][laser]

        # Use defaults of 0 in the case they are not provided
        amp = float(remote_focus_dict.get('amplitude', 0))
        off = float(remote_focus_dict.get('offset', 0))

        if resolution_mode == 'high':
            self.etl_r_amplitude, self.etl_r_offset = amp, off
            logger.debug(f"High Resolution Mode.  Amp/Off:, {self.etl_r_amplitude}, {self.etl_r_offset})")
        elif resolution_mode == 'low':
            self.etl_l_amplitude, self.etl_l_offset = amp, off
            logger.debug(f"Low Resolution Mode.  Amp/Off:, {self.etl_l_amplitude}, {self.etl_l_offset})")
        else:
            logger.info("DAQBase - ETL setting not pulled properly")

        update_waveforms = (self.prev_etl_l_amplitude != self.etl_l_amplitude) \
                           or (self.prev_etl_l_offset != self.etl_l_offset) \
                           or (self.prev_etl_r_amplitude != self.etl_r_amplitude) \
                           or (self.prev_etl_r_offset != self.etl_r_offset)

        if update_waveforms:
            # Compute the waveforms
            self.calculate_all_waveforms(microscope_state, self.etl_constants, galvo_parameters, readout_time)
            # Make sure we write out a sufficient number of samples to capture the full waveform
            self.calculate_samples()
            # Set up previous values for next update_waveforms check
            self.prev_etl_r_amplitude = self.etl_r_amplitude
            self.prev_etl_r_offset = self.etl_r_offset
            self.prev_etl_l_amplitude = self.etl_l_amplitude
            self.prev_etl_l_offset = self.etl_l_offset

    def set_camera(self, camera):
        r"""Connect camera with daq: only in syntheticDAQ."""
        pass
