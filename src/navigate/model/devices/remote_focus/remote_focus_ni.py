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


#  Standard Library Imports
import logging

# Third Party Imports
import nidaqmx
from nidaqmx.constants import AcquisitionType

# Local Imports
from navigate.model.devices.remote_focus.remote_focus_base import RemoteFocusBase

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class RemoteFocusNI(RemoteFocusBase):
    """RemoteFocusNI Class - Analog control of the remote focus device."""

    def __init__(self, microscope_name, device_connection, configuration):
        """Initialize the RemoteFocusNI class.

        Parameters
        ----------
        microscope_name : str
            The microscope name.
        device_connection : object
            The device connection object.
        configuration : dict
            The configuration dictionary.

        """
        super().__init__(microscope_name, device_connection, configuration)

        #: object: National Instruments Analog Task
        self.task = None

        #: str: The trigger source (e.g., physical channel).
        self.trigger_source = configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["trigger_source"]

        #: object: The device connection object.
        self.daq = device_connection

        #: str: The board name.
        self.board_name = self.device_config["hardware"]["channel"].split("/")[0]

    def initialize_task(self):
        """Initialize the task.

        This method initializes the task.

        """
        # TODO: make sure the task is reusable, Or need to create and close each time.
        self.task = nidaqmx.Task()
        channel = self.device_config["hardware"]["channel"]
        self.task.ao_channels.add_ao_voltage_chan(channel)
        print(
            f"Initializing remote focus with sample rate {self.sample_rate} and"
            f"{self.samples} samples"
        )

        # TODO: does it work with confocal-projection?
        self.task.timing.cfg_samp_clk_timing(
            rate=self.sample_rate,
            sample_mode=AcquisitionType.FINITE,
            samps_per_chan=self.samples,
        )
        self.task.triggers.start_trigger.cfg_dig_edge_start_trig(self.trigger_source)

    def __del__(self):
        """Delete the task."""
        self.stop_task()
        self.close_task()

    def adjust(self, exposure_times, sweep_times, offset=None):
        """Adjust the waveform.

        This method adjusts the waveform.

        Parameters
        ----------
        exposure_times : dict
            Dictionary of exposure times for each selected channel
        sweep_times : dict
            Dictionary of sweep times for each selected channel
        offset : float
            The offset of the signal in volts.

        Returns
        -------
        waveform_dict : dict
            The waveform dictionary.
        """
        waveform_dict = super().adjust(exposure_times, sweep_times, offset)

        self.daq.analog_outputs[self.device_config["hardware"]["channel"]] = {
            "sample_rate": self.sample_rate,
            "samples": self.samples,
            "trigger_source": self.trigger_source,
            "waveform": waveform_dict,
        }

        return waveform_dict

    def move(self, exposure_times, sweep_times, offset=None):
        """Move the remote focus.

        This method moves the remote focus.

        Parameters
        ----------
        exposure_times : dict
            Dictionary of exposure times for each selected channel
        sweep_times : dict
            Dictionary of sweep times for each selected channel
        offset : float
            The offset of the signal in volts.
        """
        self.adjust(exposure_times, sweep_times, offset)
        self.daq.update_analog_task(self.board_name)

    def prepare_task(self, channel_key):
        """Prepare the task.

        This method prepares the task.

        Parameters
        ----------
        channel_key : str
            The channel key.

        """

        # write waveform
        # self.task.write(self.waveform_dict[channel_key])
        pass

    def start_task(self):
        """Start the task.

        This method starts the task.

        """
        # self.task.start()
        pass

    def stop_task(self, force=False):
        """Stop the task.

        This method stops the task.

        Parameters
        ----------
        force : bool
            Force the task to stop.
        """

        # if not force:
        #     self.task.wait_until_done()
        # self.task.stop()
        pass

    def close_task(self):
        """Close the task.

        This method closes the task.
        """
        # self.task.close()
        pass
