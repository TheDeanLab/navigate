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
#

#  Standard Library Imports
import logging

# Third Party Imports

# Local Imports
from aslm.model.devices.remote_focus.remote_focus_base import RemoteFocusBase

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class SyntheticRemoteFocus(RemoteFocusBase):
    """SyntheticRemoteFocus Class

    Attributes
    ----------
    microscope_name : str
        The name of the microscope.
    device_connection : nidaqmx.Task
        The connection to the device.
    configuration : dict
        The configuration of the device.

    Methods
    -------
    prepare_task(channel_key)
        Prepares the task for the given channel.
    start_task()
        Starts the task.
    stop_task()
        Stops the task.
    close_task()
        Closes the task.


    """

    def __init__(self, microscope_name, device_connection, configuration):
        super().__init__(microscope_name, device_connection, configuration)
        pass

    def __del__(self):
        """Destructor"""
        self.stop_task()
        self.close_task()

    def prepare_task(self, channel_key):
        """Prepares the task for the given channel.

        Parameters
        ----------
        channel_key : str
            The channel key.

        Returns
        -------
        None

        Examples
        --------
        >>> prepare_task("remote_focus")
        """
        # write waveform
        logger.debug(f"remote focus writes the waveform for {channel_key}")

    def start_task(self):
        """Starts the task.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> start_task()
        """

        logger.debug("remote focus started task!")

    def stop_task(self):
        """Stops the task.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> stop_task()
        """
        logger.debug("remote focus stopped task!")

    def close_task(self):
        """Closes the task.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> close_task()
        """
        logger.debug("remote focus closed task!")
