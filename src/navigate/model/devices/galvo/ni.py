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

#  Standard Library Imports
import logging
import traceback
from typing import Any, Dict

# Third Party Imports
import nidaqmx

# Local Imports
from navigate.model.devices.galvo.base import GalvoBase
from navigate.tools.decorators import log_initialization

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class GalvoNI(GalvoBase):
    """GalvoNI Class - NI DAQ Control of Galvanometers"""

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
        galvo_id: int = 0,
    ) -> None:
        """Initialize the GalvoNI class.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : Any
            Connection to the NI DAQ device.
        configuration : Dict[str, Any]
            Dictionary of configuration parameters.
        galvo_id : int
            Galvo ID. Default is 0.
        """
        super().__init__(microscope_name, device_connection, configuration, galvo_id)

        #: str: Name of the microscope.
        self.microscope_name = microscope_name

        #: dict: Configuration parameters.
        self.configuration = configuration

        #: int: Galvo ID.
        self.galvo_id = galvo_id

        #: str: Name of the NI port for galvo control.
        self.trigger_source = configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["trigger_source"]

        #: obj: NI DAQ device connection.
        self.daq = device_connection

    def __str__(self) -> str:
        """Return string representation of the GalvoNI."""
        return "GalvoNI"

    def adjust(self, exposure_times, sweep_times) -> Dict[str, Any]:
        """Adjust the galvo to the readout time

        Parameters
        ----------
        exposure_times : dict
            Dictionary of exposure times for each selected channel
        sweep_times : dict
            Dictionary of sweep times for each selected channel

        Returns
        -------
        waveform_dict
            Dictionary with the adjusted waveforms.
        """
        waveform_dict = super().adjust(exposure_times, sweep_times)

        self.daq.analog_outputs[self.device_config["hardware"]["channel"]] = {
            "trigger_source": self.trigger_source,
            "waveform": waveform_dict,
        }
        return waveform_dict

    def turn_off(self) -> None:
        """Turn off the galvo.
        Turns off the galvo. NOTE: This will only work if there isn't another task
        bound to this channel. This should only be called in microscope.terminate().
        """
        try:
            task = nidaqmx.Task()
            task.ao_channels.add_ao_voltage_chan(
                self.device_config["hardware"]["channel"]
            )
            task.write([0], auto_start=True)
            task.stop()
            task.close()
        except Exception:
            logger.exception(f"Error stopping task: {traceback.format_exc()}")

    def __del__(self):
        """Close the GalvoNI at exit."""
        self.turn_off()
