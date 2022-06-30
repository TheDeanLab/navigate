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

# Local Imports
from aslm.model.devices.daq.daq_base import DAQBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


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

    def prepare_acquisition(self, channel_key, exposure_time):
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
