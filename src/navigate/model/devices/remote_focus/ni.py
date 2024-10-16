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


#  Standard Library Imports
import logging
from typing import Any, Dict

# Third Party Imports

# Local Imports
from navigate.model.devices.remote_focus.base import RemoteFocusBase
from navigate.tools.decorators import log_initialization

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class RemoteFocusNI(RemoteFocusBase):
    """RemoteFocusNI Class - Analog control of the remote focus device."""

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
    ) -> None:
        """Initialize the RemoteFocusNI class.

        Parameters
        ----------
        microscope_name : str
            The microscope name.
        device_connection : Any
            The device connection object.
        configuration : Dict[str, Any]
            The configuration dictionary.

        """
        super().__init__(microscope_name, device_connection, configuration)

        #: str: The trigger source (e.g., physical channel).
        self.trigger_source = configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["trigger_source"]

        #: object: The device connection object.
        self.daq = device_connection

        #: str: The board name.
        self.board_name = self.device_config["hardware"]["channel"].split("/")[0]

    def __del__(self):
        """Delete the RemoteFocusNI object.

        Deletion of the NIDAQ task is handled by the NIDAQ object."""
        pass

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
