# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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
from typing import Any

# Third Party Imports
import nidaqmx
from nidaqmx.errors import DaqError
from nidaqmx.constants import LineGrouping

# Local Imports
from navigate.model.devices.filter_wheel.base import FilterWheelBase
from navigate.model.devices.device_types import NIDevice
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class NIFilterWheel(FilterWheelBase, NIDevice):
    """DAQFilterWheel - Class for controlling filter wheels with a DAQ."""

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        device_id: int = 0,
    ) -> None:
        """Initialize the DAQFilterWheel class.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : Any
            The communication instance with the device.
        configuration : Dict[str, Any]
            Global configuration dictionary.
        device_id : int
            The ID of the device. Default is 0.
        """

        super().__init__(microscope_name, device_connection, configuration, device_id)

        #: float: Delay for filter wheel to change positions.
        self.wait_until_done_delay = self.device_config["filter_wheel_delay"]

        self.filter_wheel_task = None

    def __str__(self) -> str:
        """String representation of the class."""
        return "DAQFilterWheel"

    def __enter__(self) -> "NIFilterWheel":
        """Enter the NI Filter Wheel context manager."""
        return self

    def __exit__(self) -> bool:
        """Exit the NI Filter Wheel context manager.

        Returns
        -------
        bool
            True if the context was exited successfully, False otherwise.
        """
        if self.filter_wheel_task:
            try:
                self.filter_wheel_task.stop()
                self.filter_wheel_task.close()
            except Exception:
                pass
        return True

    def set_filter(self, filter_name: str, wait_until_done: bool = True) -> None:
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
