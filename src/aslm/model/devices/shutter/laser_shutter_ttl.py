"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

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
# """

# Standard Library Imports
import logging

# Third Party Imports
import nidaqmx
from nidaqmx.constants import LineGrouping

# Local Imports
from aslm.model.devices.shutter.laser_shutter_base import ShutterBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ShutterTTL(ShutterBase):
    """ShutterTTL Class

    Triggering for shutters delivered from DAQ using digital outputs.
    Each output keeps their last digital state for as long the device is not powered down.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    """

    def __init__(self, microscope_name, device_connection, configuration):
        super().__init__(microscope_name, device_connection, configuration)

        shutter_channel = configuration['configuration']['microscopes'][microscope_name]['shutter']['hardware']['channel']

        self.shutter_task = nidaqmx.Task()
        self.shutter_task.do_channels.add_do_chan(shutter_channel, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        self.shutter_task.write(self.shutter_state, auto_start=True)

    def __del__(self):
        """Close the ShutterTTL at exit.
        """
        self.shutter_task.close()

    def open_shutter(self):
        r"""Open the shutter
        """
        self.shutter_state = True
        self.shutter_task.write(self.shutter_state, auto_start=True)
        logger.debug("ShutterTTL - Shutter opened")


    def close_shutter(self):
        r"""CLose the shutter
        """
        self.shutter_state = False
        self.shutter_task.write(self.shutter_state, auto_start=True)
        logger.debug("ShutterTTL - The shutter is closed")

    @property
    def state(self):
        r"""Return the state of both shutters

        Returns
        -------
        shutter_state : bool
            State of the shutter.
        """
        return self.shutter_state
