# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

# Standard Imports
import logging
import time
from threading import Lock

# Third Party Imports

# Local Imports
from navigate.model.devices.daq.base import DAQBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class SyntheticDAQ(DAQBase):
    """SyntheticDAQ class for Data Acquisition (DAQ)."""

    def __init__(self, configuration):
        """Initialize the Synthetic DAQ.

        Parameters
        ----------
        configuration : dict
            Configuration dictionary.
        """
        super().__init__(configuration)

        #: dict: Configuration dictionary.
        self.configuration = configuration

        #: dict: Camera object.
        self.camera = {}

        #: Lock: Lock for waiting to run.
        self.wait_to_run_lock = Lock()

        #: dict: Analog output tasks.
        self.analog_outputs = {}

        #: bool: Flag for updating analog task.
        self.is_updating_analog_task = False

        #: str: Trigger mode. Self-trigger or external-trigger.
        self.trigger_mode = "self-trigger"

        # logger.info(self.__repr__())
        logger.info(self.__repr__())

    def __str__(self):
        """String representation of the class."""
        return "SyntheticDAQ"

    def __repr__(self):
        """String representation of the class."""
        return f'SyntheticDAQ("{self.configuration}")'

    def create_camera_task(self):
        """Set up the camera trigger task."""
        pass

    def create_master_trigger_task(self):
        """Set up the DO master trigger task."""
        pass

    def create_galvo_remote_focus_tasks(self):
        """Create galvo and remote focus tasks"""
        pass

    def start_tasks(self):
        """Start the tasks for camera triggering and analog outputs.

        If the tasks are configured to be triggered, they won't start until
        run_tasks() is called."""
        pass

    def stop_tasks(self):
        """Stop the tasks for triggering, analog and counter outputs."""
        pass

    def close_tasks(self):
        """Close the tasks for triggering, analog, and counter outputs."""
        pass

    def prepare_acquisition(self, channel_key):
        """Prepare the acquisition.

        Parameters
        ----------
        channel_key : str
            Channel key for current channel.
        """
        self.current_channel_key = channel_key
        self.is_updating_analog_task = False
        if self.wait_to_run_lock.locked():
            self.wait_to_run_lock.release()

    def run_acquisition(self):
        """Run DAQ Acquisition.

        Run the tasks for triggering, analog and counter outputs.
        The master trigger initiates all other tasks via a shared trigger
        For this to work, all analog output and counter tasks have to be started so that
        they are waiting for the trigger signal."""
        # wait if writing analog tasks
        if self.is_updating_analog_task:
            self.wait_to_run_lock.acquire()
            self.wait_to_run_lock.release()
        time.sleep(0.01)
        if self.trigger_mode == "self-trigger":
            for microscope_name in self.camera:
                self.camera[microscope_name].generate_new_frame()

    def stop_acquisition(self):
        """Stop Acquisition."""
        pass

    def write_waveforms_to_tasks(self):
        """Write the galvo, remote focus, and laser waveforms to each task."""
        pass

    def add_camera(self, microscope_name, camera):
        """Connect camera with daq: only in syntheticDAQ.

        Parameters
        ----------
        microscope_name : str
            Name of microscope.
        camera : Camera
            Camera object.
        """
        self.camera[microscope_name] = camera

    def update_analog_task(self, board_name):
        """Update the analog task.

        Parameters
        ----------
        board_name : str
            Name of board.
        """
        # can't update an analog task while updating one.
        if self.is_updating_analog_task:
            return False

        self.wait_to_run_lock.acquire()
        self.is_updating_analog_task = True

        self.is_updating_analog_task = False
        self.wait_to_run_lock.release()

    def set_external_trigger(self, external_trigger=None):
        """Set the external trigger.

        Parameters
        ----------
        external_trigger : str, optional
            Name of external trigger.
        """

        self.trigger_mode = (
            "self-trigger" if external_trigger is None else "external-trigger"
        )
