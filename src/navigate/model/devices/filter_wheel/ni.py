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
import time
import traceback

# Third Party Imports
import nidaqmx
from nidaqmx.errors import DaqError
from nidaqmx.constants import LineGrouping

# Local Imports
from navigate.model.devices.filter_wheel.base import FilterWheelBase
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_filter_wheel_connection():
    """Build DAQFilterwheel connection.

    The NI DAQ task is created within the DAQFIlterWheel Instance, so a shared
    device connection is not needed. Accordingly, this function returns None.

    Returns
    -------
    daq_fw_controller : None
        No device is returned.
    """
    daq_fw_controller = None
    return daq_fw_controller


@log_initialization
class DAQFilterWheel(FilterWheelBase):
    """DAQFilterWheel - Class for controlling filter wheels with a DAQ."""

    def __init__(self, device_connection, device_config):
        """Initialize the DAQFilterWheel class.

        Parameters
        ----------
        device_connection : object
            Connection to the NIDAQ Instance. Imported but not used.
        device_config : dict
            Dictionary of device configuration parameters.
        """

        super().__init__(device_connection, device_config)

        #: object: Dummy device connection.
        self.device_connection = device_connection

        #: dict: Dictionary of filter names and corresponding digital port.
        self.device_config = device_config

        #: float: Delay for filter wheel to change positions.
        self.wait_until_done_delay = device_config["filter_wheel_delay"]

        self.filter_wheel_task = None

    def __str__(self):
        """String representation of the class."""
        return "DAQFilterWheel"

    def __enter__(self):
        """Enter the ASI Filter Wheel context manager."""
        return self

    def __exit__(self):
        """Exit the ASI Filter Wheel context manager."""
        if self.filter_wheel_task:
            try:
                self.filter_wheel_task.stop()
                self.filter_wheel_task.close()
            except Exception:
                pass

    def set_filter(self, filter_name, wait_until_done=True):
        """Change the filter wheel to the filter designated by the filter
        position argument. Requires a digital port on the DAQ.

        Parameters
        ----------
        filter_name : str
            Name of filter to move to.
        wait_until_done : bool
            Waits duration of time necessary for filter wheel to change positions.
        """
        if self.check_if_filter_in_filter_dictionary(filter_name) is True:
            try:
                # Create the nidaqmx Task, and add the DO channel.
                self.filter_wheel_task = nidaqmx.Task()
                self.filter_wheel_task.do_channels.add_do_chan(
                    lines=self.filter_dictionary[filter_name],
                    line_grouping=LineGrouping.CHAN_FOR_ALL_LINES,
                )

                # Trigger the nidaqmx Task to a 5V state.
                self.filter_wheel_task.write([True], auto_start=True)

                #  Wheel Position Change Delay in seconds
                if wait_until_done:
                    time.sleep(self.wait_until_done_delay)

                # Trigger the nidaqmx Task to a 0V state.
                self.filter_wheel_task.write([False], auto_start=True)

                # Clean up the task
                self.filter_wheel_task.stop()
                self.filter_wheel_task.close()
            except DaqError as e:
                logger.debug(e)

    def close(self) -> None:
        """Close the DAQ Filter Wheel

        Sets the filter wheel to the home position and then closes the port.
        """
        pass

    def __del__(self) -> None:
        """Delete the DAQFilterWheel object."""
        if self.filter_wheel_task:
            try:
                self.filter_wheel_task.stop()
                self.filter_wheel_task.close()
            except Exception:
                logger.exception(f"Error stopping task: {traceback.format_exc()}")
