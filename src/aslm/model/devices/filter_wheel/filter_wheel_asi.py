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
import time

# Third Party Imports

# Local Imports
from aslm.model.devices.filter_wheel.filter_wheel_base import FilterWheelBase
from aslm.model.devices.APIs.asi.asi_tiger_controller import TigerController

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_filter_wheel_connection(comport, baudrate=115200, timeout=0.25):
    """Build ASIFilterWheel Serial Port connection

    Parameters
    ----------
    comport : str
        Comport for communicating with the filter wheel, e.g., COM1.
    baudrate : int
        Baud rate for communicating with the filter wheel, default is 115200.
    timeout : float
        Timeout for communicating with the filter wheel, default is 0.25.

    Returns
    -------
    tiger_controller : TigerController
        ASI Tiger Controller object.
    """
    # wait until ASI device is ready
    tiger_controller = TigerController(comport, baudrate)
    tiger_controller.connect_to_serial()
    if not tiger_controller.is_open():
        raise Exception("ASI stage connection failed.")
    return tiger_controller


class ASIFilterWheel(FilterWheelBase):
    """ASIFilterWheel - Class for controlling ASI Filter Wheels

    Note
    ----
        Additional information on the ASI Filter Wheel can be found at:
        https://asiimaging.com/docs/fw_1000#fw-1000_ascii_command_set
    """

    def __init__(self, microscope_name, device_connection, configuration):
        """Initialize the ASIFilterWheel class.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : dict
            Dictionary of device connections.
        configuration : dict
            Dictionary of configuration parameters.
        """

        super().__init__(microscope_name, device_connection, configuration)

        #: obj: ASI Tiger Controller object.
        self.filter_wheel = device_connection

        #: str: Name of the ASI Filter Wheel.
        self.microscope_name = microscope_name

        #: int: Number of filter wheels.
        self.number_of_filter_wheels = configuration["configuration"]["microscopes"][
            microscope_name
        ]["filter_wheel"]["hardware"]["wheel_number"]

        #: float: Delay for filter wheel to change positions.
        self.wait_until_done_delay = configuration["configuration"]["microscopes"][
            microscope_name
        ]["filter_wheel"]["filter_wheel_delay"]

        # Send Filter Wheel/Wheels to Zeroth Position
        for i in range(self.number_of_filter_wheels):
            self.filter_wheel.select_filter_wheel(filter_wheel_number=i)

            #: int: Active filter wheel.
            self.active_filter_wheel = i
            self.filter_wheel.move_filter_wheel(filter_wheel_position=0)

            #: int: Filter wheel position.
            self.filter_wheel_position = 0

    def __enter__(self):
        """Enter the ASI Filter Wheel context manager."""
        return self

    def __exit__(self):
        """Exit the ASI Filter Wheel context manager."""
        if self.filter_wheel.is_open():
            logger.debug("ASI Filter Wheel - Closing Device.")
            self.filter_wheel.disconnect_from_serial()

    def filter_change_delay(self, filter_name):
        """Estimate duration of time necessary to move the filter wheel

        Assumes that it is ~40ms per adjacent position.
        Depends on filter wheel parameters and load.

        Parameters
        ----------
        filter_name : str
            Name of filter to move to.

        """
        old_position = self.filter_wheel_position
        new_position = self.filter_dictionary[filter_name]
        delta_position = int(abs(old_position - new_position))
        self.wait_until_done_delay = delta_position * 0.04

    def set_filter(self, filter_name, wait_until_done=True):
        """Change the filter wheel to the filter designated by the filter
        position argument.

        Parameters
        ----------
        filter_name : str
            Name of filter to move to.
        wait_until_done : bool
            Waits duration of time necessary for filter wheel to change positions.
        """
        if self.check_if_filter_in_filter_dictionary(filter_name) is True:

            # Calculate the Delay Needed to Change the Positions
            self.filter_change_delay(filter_name)

            for wheel_idx in range(self.number_of_filter_wheels):
                self.filter_wheel.select_filter_wheel(filter_wheel_number=wheel_idx)
                self.filter_wheel.move_filter_wheel(self.filter_dictionary[filter_name])

            #  Wheel Position Change Delay
            if wait_until_done:
                time.sleep(self.wait_until_done_delay)

    def close(self):
        """Close the ASI Filter Wheel serial port.

        Sets the filter wheel to the home position and then closes the port.
        """
        if self.filter_wheel.is_open():
            self.filter_wheel.move_filter_wheel_to_home()
            logger.debug("ASI Filter Wheel - Closing Device.")
            self.filter_wheel.disconnect_from_serial()
