"""
ASLM data acquisition card communication classes.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
import time

# Third Party Imports
from pathlib import Path

import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import LineGrouping
from scipy import signal
import numpy as np

# Local Imports
from model.aslm_model_waveforms import tunable_lens_ramp, sawtooth, dc_value, single_pulse

# Logger Setup
p = Path(__file__).resolve().parts[7]
logger = logging.getLogger(p)

class DAQBase:
    def __init__(self, model, experiment, etl_constants, verbose=False):
        self.model = model
        self.experiment = experiment
        self.etl_constants = etl_constants
        self.verbose = verbose

        # Initialize Variables
        self.sample_rate = self.model.DAQParameters['sample_rate']
        self.sweep_time = self.model.DAQParameters['sweep_time']
        self.samples = int(self.sample_rate * self.sweep_time)

        # ETL Parameters
        self.etl_l_waveform = None
        self.etl_l_delay = self.model.RemoteFocusParameters['remote_focus_l_delay_percent']
        self.etl_l_ramp_rising = self.model.RemoteFocusParameters['remote_focus_l_ramp_rising_percent']
        self.etl_l_ramp_falling = self.model.RemoteFocusParameters['remote_focus_l_ramp_falling_percent']
        self.etl_l_amplitude = self.model.RemoteFocusParameters['remote_focus_l_amplitude']
        self.etl_l_offset = self.model.RemoteFocusParameters['remote_focus_l_offset']
        self.etl_l_min_ao = self.model.RemoteFocusParameters['remote_focus_l_min_ao']
        self.etl_l_max_ao = self.model.RemoteFocusParameters['remote_focus_l_max_ao']

        # Remote Focus Parameters
        self.etl_r_waveform = None
        self.etl_r_delay = self.model.RemoteFocusParameters['remote_focus_r_delay_percent']
        self.etl_r_ramp_rising = self.model.RemoteFocusParameters['remote_focus_r_ramp_rising_percent']
        self.etl_r_ramp_falling = self.model.RemoteFocusParameters['remote_focus_r_ramp_falling_percent']
        self.etl_r_amplitude = self.model.RemoteFocusParameters['remote_focus_r_amplitude']
        self.etl_r_offset = self.model.RemoteFocusParameters['remote_focus_r_offset']
        self.etl_r_min_ao = self.model.RemoteFocusParameters['remote_focus_r_min_ao']
        self.etl_r_max_ao = self.model.RemoteFocusParameters['remote_focus_r_max_ao']

        # Left Galvo Parameters
        self.galvo_l_waveform = None
        self.galvo_and_etl_waveforms = None
        self.galvo_l_frequency = self.model.GalvoParameters['galvo_l_frequency']
        self.galvo_l_amplitude = self.model.GalvoParameters['galvo_l_amplitude']
        self.galvo_l_offset = self.model.GalvoParameters['galvo_l_offset']
        self.galvo_l_duty_cycle = self.model.GalvoParameters['galvo_l_duty_cycle']
        self.galvo_l_phase = self.model.GalvoParameters['galvo_l_phase']
        self.galvo_l_min_ao = self.model.GalvoParameters['galvo_l_min_ao']

        # Right Galvo Parameters
        self.galvo_r_max_ao = self.model.GalvoParameters['galvo_l_max_ao']
        self.galvo_r_amplitude = self.model.GalvoParameters['galvo_r_amplitude']
        self.galvo_r_min_ao = self.model.GalvoParameters['galvo_r_min_ao']
        self.galvo_r_max_ao = self.model.GalvoParameters['galvo_r_max_ao']
        self.galvo_r_waveform = None

        # Camera Parameters
        self.camera_delay_percent = self.model.CameraParameters['delay_percent']
        self.camera_pulse_percent = self.model.CameraParameters['pulse_percent']
        self.camera_high_time = self.camera_pulse_percent * 0.01 * self.sweep_time
        self.camera_delay = self.camera_delay_percent * 0.01 * self.sweep_time

        # Laser Parameters
        self.laser_ao_waveforms = None
        self.laser_do_waveforms = None
        self.number_of_lasers = self.model.LaserParameters['number_of_lasers']
        self.laser_l_delay = self.model.LaserParameters['laser_l_delay_percent']
        self.laser_l_pulse = self.model.LaserParameters['laser_l_pulse_percent']

        self.laser_power = 0
        self.laser_idx = 0

    def calculate_samples(self):
        """
        # Calculate the number of samples for the waveforms.
        # Product of the sampling frequency and the duration of the waveform/exposure time.
        # sweep_time units originally seconds.
        """
        self.samples = int(self.sample_rate * self.sweep_time)

    def create_waveforms(self):
        """
        # Create the waveforms for the ETL, Galvos, and sends it to the tasks for execution.
        """
        self.calculate_samples()

        # ETL - Currently creates both ETL L and ETL R
        self.create_etl_waveform()

        # Galvos
        self.create_high_res_galvo_waveform()
        self.create_low_res_galvo_waveform()

        # Bundle the waveforms into a single waveform.
        self.bundle_galvo_and_etl_waveforms()

        # Write the waveforms to the tasks.
        self.write_waveforms_to_tasks()

    def update_etl_parameters(self, microscope_state, channel):
        """
        # Update the ETL parameters according to the zoom and excitation wavelength.
        """
        laser = channel['laser']
        resolution_mode = microscope_state['resolution_mode']

        if resolution_mode == 'high':
            zoom = 'one'
            self.etl_r_amplitude = float(
                self.etl_constants.ETLConstants[resolution_mode][zoom][laser]['amplitude'])
            self.etl_r_offset = float(
                self.etl_constants.ETLConstants[resolution_mode][zoom][laser]['offset'])
            if self.verbose:
                print(
                    "High Resolution Mode.  Amp/Off:",
                    self.etl_r_amplitude,
                    self.etl_r_offset)

        elif resolution_mode == 'low':
            zoom = microscope_state['zoom']
            self.etl_l_amplitude = float(
                self.etl_constants.ETLConstants[resolution_mode][zoom][laser]['amplitude'])
            self.etl_l_offset = float(
                self.etl_constants.ETLConstants[resolution_mode][zoom][laser]['offset'])
            if self.verbose:
                print(
                    "Low Resolution Mode.  Amp/Off:",
                    self.etl_l_amplitude,
                    self.etl_l_offset)

        else:
            print("ETL setting not pulled properly.")

    def create_etl_waveform(self):
        """
        # Create the waveforms for the Electrotunable Lens
        # This needs to know what resolution mode, what channel, laser, etc...
        """
        self.etl_l_waveform = tunable_lens_ramp(
            self.sample_rate,
            self.sweep_time,
            self.etl_l_delay,
            self.etl_l_ramp_rising,
            self.etl_l_ramp_falling,
            self.etl_l_amplitude,
            self.etl_l_offset)

        self.etl_r_waveform = tunable_lens_ramp(
            self.sample_rate,
            self.sweep_time,
            self.etl_r_delay,
            self.etl_r_ramp_rising,
            self.etl_r_ramp_falling,
            self.etl_r_amplitude,
            self.etl_r_offset)
        # Scale the ETL waveforms to the AO range.
        self.etl_l_waveform[self.etl_l_waveform <
                            self.etl_l_min_ao] = self.etl_l_min_ao
        self.etl_l_waveform[self.etl_l_waveform >
                            self.etl_l_max_ao] = self.etl_l_max_ao
        self.etl_r_waveform[self.etl_r_waveform <
                            self.etl_r_min_ao] = self.etl_r_min_ao
        self.etl_r_waveform[self.etl_r_waveform >
                            self.etl_r_max_ao] = self.etl_r_max_ao

    def create_low_res_galvo_waveform(self):
        """
        # Calculate the sawtooth waveforms for the low-resolution digitally scanned galvo.
        """
        self.galvo_l_waveform = sawtooth(
            self.sample_rate,
            self.sweep_time,
            self.galvo_l_frequency,
            self.galvo_l_amplitude,
            self.galvo_l_offset,
            self.galvo_l_duty_cycle,
            self.galvo_l_phase)

        # Scale the Galvo waveforms to the AO range.
        self.galvo_l_waveform[self.galvo_l_waveform <
                              self.galvo_l_min_ao] = self.galvo_l_min_ao
        self.galvo_l_waveform[self.galvo_l_waveform >
                              self.galvo_r_max_ao] = self.galvo_r_max_ao

    def create_high_res_galvo_waveform(self):
        """
        # Calculate the DC waveform for the resonant galvanometer drive signal.
        """
        self.galvo_r_waveform = dc_value(
            self.sample_rate, self.sweep_time, self.galvo_r_amplitude, 0)

        # Scale the Galvo waveforms to the AO range.
        self.galvo_r_waveform[self.galvo_r_waveform <
                              self.galvo_r_min_ao] = self.galvo_r_min_ao
        self.galvo_r_waveform[self.galvo_r_waveform >
                              self.galvo_r_max_ao] = self.galvo_r_max_ao

    def bundle_galvo_and_etl_waveforms(self):
        """
        # Stacks the Galvo and ETL waveforms into a numpy array adequate for
        # the NI cards. In here, the assignment of output channels of the Galvo / ETL card to the
        # corresponding output channel is hardcoded: This could be improved.
        """
        self.galvo_and_etl_waveforms = np.stack((self.galvo_l_waveform,
                                                 self.galvo_r_waveform,
                                                 self.etl_l_waveform,
                                                 self.etl_r_waveform))


class SyntheticDAQ(DAQBase):
    def __init__(self, model, experiment, etl_constants, verbose=False):
        super().__init__(model, experiment, etl_constants, verbose)

    def create_camera_task(self):
        """
        # Set up the camera trigger
        # Calculate camera high time and initial delay.
        # Disadvantage: high time and delay can only be set after a task has been created
        """
        # Configure camera triggers
        camera_trigger_out_line = self.model.DAQParameters['camera_trigger_out_line']
        pass

    def create_master_trigger_task(self):
        """
        # Set up the DO master trigger task
        """
        master_trigger_out_line = self.model.DAQParameters['master_trigger_out_line']
        pass

    def create_galvo_etl_task(self):
        """
        # Set up the Galvo and electrotunable lens - Each start with the trigger_source.
        PXI6259/ao0:3 -> 4 channels
        """
        galvo_etl_task_line = self.model.DAQParameters['galvo_etl_task_line']
        trigger_source = self.model.DAQParameters['trigger_source']
        pass

    def start_tasks(self):
        """
        # Start the tasks for camera triggering and analog outputs
        # If the tasks are configured to be triggered, they won't output any signals until run_tasks() is called.
        """
        pass

    def stop_tasks(self):
        """
        # Stop the tasks for triggering, analog and counter outputs.
        """
        pass

    def close_tasks(self):
        """
        # Close the tasks for triggering, analog, and counter outputs.
        """
        pass

    def prepare_acquisition(self):
        """
        # Initialize the nidaqmx tasks.
        """
        pass

    def run_acquisition(self):
        """
        # Run the tasks for triggering, analog and counter outputs.
        # the master trigger initiates all other tasks via a shared trigger
        # For this to work, all analog output and counter tasks have to be started so
        # that they are waiting for the trigger signal.
        """
        time.sleep(0.01)
        self.camera.generate_new_frame()

    def stop_acquisition(self):
        pass

    def write_waveforms_to_tasks(self):
        """
        # Write the galvo, etl, and laser waveforms to the NI DAQ tasks
        """
        pass

    def set_camera(self, camera):
        """
        # connect camera with daq: only in syntheticDAQ
        """
        self.camera = camera
        pass


class NIDAQ(DAQBase):
    def __init__(self, model, experiment, etl_constants, verbose=False):
        super().__init__(model, experiment, etl_constants, verbose)

    def __del__(self):
        pass

    def create_camera_task(self):
        """
        # Set up the camera trigger
        # Calculate camera high time and initial delay.
        # Disadvantage: high time and delay can only be set after a task has been created
        """
        # Configure camera triggers
        camera_trigger_out_line = self.model.DAQParameters['camera_trigger_out_line']
        self.camera_trigger_task.co_channels.add_co_pulse_chan_time(
            camera_trigger_out_line,
            high_time=self.camera_high_time,
            initial_delay=self.camera_delay)
        trigger_source = self.model.DAQParameters['trigger_source']
        self.camera_trigger_task.triggers.start_trigger.cfg_dig_edge_start_trig(
            trigger_source)

    def create_master_trigger_task(self):
        """
        # Set up the DO master trigger task
        """
        master_trigger_out_line = self.model.DAQParameters['master_trigger_out_line']
        self.master_trigger_task.do_channels.add_do_chan(
            master_trigger_out_line, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)

    def create_galvo_etl_task(self):
        """
        # Set up the Galvo and electrotunable lens - Each start with the trigger_source.
        PXI6259/ao0:3 -> 4 channels
        """
        galvo_etl_task_line = self.model.DAQParameters['galvo_etl_task_line']
        self.galvo_etl_task.ao_channels.add_ao_voltage_chan(
            galvo_etl_task_line)
        self.galvo_etl_task.timing.cfg_samp_clk_timing(
            rate=self.sample_rate,
            sample_mode=AcquisitionType.FINITE,
            samps_per_chan=self.samples)

        trigger_source = self.model.DAQParameters['trigger_source']
        self.galvo_etl_task.triggers.start_trigger.cfg_dig_edge_start_trig(
            trigger_source)

    def start_tasks(self):
        """
        # Start the tasks for camera triggering and analog outputs
        # If the tasks are configured to be triggered, they won't output any signals until run_tasks() is called.
        """
        self.camera_trigger_task.start()
        self.galvo_etl_task.start()

    def stop_tasks(self):
        """
        # Stop the tasks for triggering, analog and counter outputs.
        """
        self.galvo_etl_task.stop()
        self.camera_trigger_task.stop()
        self.master_trigger_task.stop()

    def close_tasks(self):
        """
        # Close the tasks for triggering, analog, and counter outputs.
        """
        self.galvo_etl_task.close()
        self.camera_trigger_task.close()
        self.master_trigger_task.close()

    def prepare_acquisition(self):
        """
        # Initialize the nidaqmx tasks.
        """
        self.camera_trigger_task = nidaqmx.Task()
        self.master_trigger_task = nidaqmx.Task()
        self.galvo_etl_task = nidaqmx.Task()

        # Specify ports, timing, and triggering
        self.create_master_trigger_task()
        self.create_camera_task()
        self.create_galvo_etl_task()

        # Calculate the waveforms and start tasks.
        self.create_waveforms()
        self.start_tasks()

    def run_acquisition(self):
        """
        # Run the tasks for triggering, analog and counter outputs.
        # the master trigger initiates all other tasks via a shared trigger
        # For this to work, all analog output and counter tasks have to be started so
        # that they are waiting for the trigger signal.
        """
        self.master_trigger_task.write([False, True, True, True, False], auto_start=True)
        self.galvo_etl_task.wait_until_done()
        self.camera_trigger_task.wait_until_done()

    def stop_acquisition(self):
        self.stop_tasks()
        self.close_tasks()

    def write_waveforms_to_tasks(self):
        """
        # Write the galvo, etl, and laser waveforms to the NI DAQ tasks
        """
        self.galvo_etl_task.write(self.galvo_and_etl_waveforms)

    def set_camera(self, camera):
        """
        # connect camera with daq: only in syntheticDAQ
        """
    pass
