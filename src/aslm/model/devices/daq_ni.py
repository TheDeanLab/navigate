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

# Third Party Imports
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import LineGrouping
import numpy as np

# Local Imports
from aslm.model.devices.daq_base import DAQBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class NIDAQ(DAQBase):
    def __init__(self, model, experiment, etl_constants, verbose=False):
        super().__init__(model, experiment, etl_constants, verbose)

    def __del__(self):
        pass

    def create_camera_task(self, exposure_time):
        """
        # Set up the camera trigger
        # Calculate camera high time and initial delay.
        # Disadvantage: high time and delay can only be set after a task has been created
        """
        # Configure camera triggers
        camera_trigger_out_line = self.model.DAQParameters['camera_trigger_out_line']
        self.camera_high_time = 0.004  # (self.camera_pulse_percent / 100) * (exposure_time/1000)  # self.sweep_time
        self.camera_delay = (self.camera_delay_percent / 100) * (exposure_time/1000)  # * 0.01 * self.sweep_time

        self.camera_trigger_task.co_channels.add_co_pulse_chan_time(camera_trigger_out_line,
                                                                    high_time=self.camera_high_time,
                                                                    initial_delay=self.camera_delay)
        trigger_source = self.model.DAQParameters['trigger_source']
        self.camera_trigger_task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source)

    def create_master_trigger_task(self):
        """
        # Set up the DO master trigger task
        """
        master_trigger_out_line = self.model.DAQParameters['master_trigger_out_line']
        self.master_trigger_task.do_channels.add_do_chan(master_trigger_out_line,
                                                         line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)

    def create_galvo_etl_task(self):
        """
        # Set up the Galvo and electrotunable lens - Each start with the trigger_source.
        PXI6259/ao0:3 -> 4 channels
        """
        # TODO: Does this task line change for the right galvo?
        galvo_etl_task_line = self.model.DAQParameters['galvo_etl_task_line']
        self.galvo_etl_task.ao_channels.add_ao_voltage_chan(galvo_etl_task_line)
        self.galvo_etl_task.timing.cfg_samp_clk_timing(rate=self.sample_rate,
                                                       sample_mode=AcquisitionType.FINITE,
                                                       samps_per_chan=self.samples)

        trigger_source = self.model.DAQParameters['trigger_source']
        self.galvo_etl_task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source)

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

    def prepare_acquisition(self, channel_key, exposure_time):
        """
        # Initialize the nidaqmx tasks.
        """
        self.camera_trigger_task = nidaqmx.Task()
        self.master_trigger_task = nidaqmx.Task()
        self.galvo_etl_task = nidaqmx.Task()

        self.calculate_samples()

        # Specify ports, timing, and triggering
        self.create_master_trigger_task()
        self.create_camera_task(exposure_time)
        self.create_galvo_etl_task()

        # Calculate the waveforms and start tasks.
        etl_waveform = self.waveform_dict[channel_key]['etl_waveform']
        galvo_waveform = self.waveform_dict[channel_key]['galvo_waveform']
        self.galvo_and_etl_waveforms = np.stack((galvo_waveform, galvo_waveform, etl_waveform, etl_waveform))

        # Write pre-calculated waveforms to the tasks...
        self.write_waveforms_to_tasks()

    def run_acquisition(self):
        """
        # Run the tasks for triggering, analog and counter outputs.
        # the master trigger initiates all other tasks via a shared trigger
        # For this to work, all analog output and counter tasks have to be started so
        # that they are waiting for the trigger signal.
        """
        self.start_tasks()
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
