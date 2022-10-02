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
import time

# Third Party Imports

# Local Imports
from aslm.model.devices.daq.daq_base import DAQBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class SyntheticDAQ(DAQBase):
    r"""SyntheticDAQ class for Data Acquisition (DAQ).

    Attributes
    ----------
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    """
    def __init__(self, configuration):
        super().__init__(configuration)
        self.camera = {}

    def create_camera_task(self):
        r"""Set up the camera trigger task."""
        pass

    def create_master_trigger_task(self):
        r"""Set up the DO master trigger task."""
        pass

    def create_galvo_etl_task(self):
        r"""Create galvo and ETL tasks"""
        pass

    def start_tasks(self):
        r"""Start the tasks for camera triggering and analog outputs
        # If the tasks are configured to be triggered, they won't start until run_tasks() is called."""
        pass

    def stop_tasks(self):
        r"""Stop the tasks for triggering, analog and counter outputs."""
        pass

    def close_tasks(self):
        r"""Close the tasks for triggering, analog, and counter outputs."""
        pass

    def prepare_acquisition(self, channel_key, exposure_time):
        r"""Prepare the acquisition.

        Parameters
        ----------
        channel_key : int
            Index of channel to be imaged.
        exposure_time : float
            Camera exposure duration.
        """
        pass

    def run_acquisition(self):
        r"""Run DAQ Acquisition.
        Run the tasks for triggering, analog and counter outputs.
        The master trigger initiates all other tasks via a shared trigger
        For this to work, all analog output and counter tasks have to be started so that
        they are waiting for the trigger signal."""
        time.sleep(0.01)
        self.camera[self.microscope_name].generate_new_frame()

    def stop_acquisition(self):
        r"""Stop Acquisition."""
        pass

    def write_waveforms_to_tasks(self):
        r"""Write the galvo, etl, and laser waveforms to each task."""
        pass

    def add_camera(self, microscope_name, camera):
        r"""Connect camera with daq: only in syntheticDAQ."""
        self.camera[microscope_name] = camera
