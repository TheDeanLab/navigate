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

# Third Party Imports
import numpy as np
import serial

# Local Imports
from navigate.model.devices.filter_wheel.base import FilterWheelBase
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_filter_wheel_connection(comport, baudrate, timeout=0.25):
    """Build SutterFilterWheel Serial Port connection

    Attributes
    ----------
    comport : str
        Comport for communicating with the filter wheel, e.g., COM1.
    baudrate : int
        Baud rate for communicating with the filter wheel, e.g., 9600.
    timeout : float
        Timeout for communicating with the filter wheel, e.g., 0.25.

    Returns
    -------
    serial.Serial
        The serial port connection to the filter wheel.

    Raises
    ------
    UserWarning
        Could not communicate with Sutter Lambda 10-B via COMPORT.
    """
    logging.debug(f"SutterFilterWheel - Opening Serial Port {comport}")
    try:
        return serial.Serial(comport, baudrate, timeout=timeout)
    except serial.SerialException:
        logger.error("SutterFilterWheel - Could not establish Serial Port Connection")
        raise UserWarning(
            "Could not communicate with Sutter Lambda 10-B via COMPORT", comport
        )


@log_initialization
class SutterFilterWheel(FilterWheelBase):
    """SutterFilterWheel - Class for controlling Sutter Lambda Filter Wheels

    Note
    ----
        Additional information on the Sutter Lambda 10-B can be found at:
        https://www.sutter.com/manuals/LB10-3_OpMan.pdf
    """

    def __init__(self, device_connection, device_config):
        """Initialize the SutterFilterWheel class.

        Parameters
        ----------
        device_connection : serial.Serial
            The communication instance with the filter wheel.
        device_config : Dict[str, Any]
            Dictionary of device configuration parameters.
        """
        super().__init__(device_connection, device_config)

        #: serial.Serial: Serial port connection to the filter wheel.
        self.serial = device_connection

        #: Dict[str, Any]: Dictionary of filter names and corresponding filter wheel
        # positions.
        self.device_config = device_config

        #: bool: Wait until filter wheel has completed movement.
        self.wait_until_done = True

        #: float: Delay in s for the wait until done function.
        self.wait_until_done_delay = None

        #: bool: Read on initialization.
        self.read_on_init = True

        #: int: Filter wheel speed.
        self.speed = 2

        # Delay in s for the wait until done function
        #: np.matrix: Delay matrix for filter wheel.
        self.delay_matrix = np.array(
            [
                [0, 0.031, 0.051, 0.074, 0.095, 0.115],
                [0, 0.040, 0.065, 0.095, 0.120, 0.148],
                [0, 0.044, 0.075, 0.105, 0.136, 0.168],
                [0, 0.050, 0.088, 0.127, 0.165, 0.205],
                [0, 0.060, 0.108, 0.156, 0.205, 0.250],
                [0, 0.068, 0.123, 0.178, 0.235, 0.290],
                [0, 0.124, 0.235, 0.350, 0.460, 0.580],
                [0, 0.230, 0.440, 0.650, 0.860, 1.100],
            ]
        )

        self.serial.write(bytes.fromhex("ee"))

        if self.read_on_init:
            self.read(2)  # class 'bytes'
            #: bool: Software initialization complete flag.
            self.init_finished = True
        else:
            self.init_finished = False

        # Set filter to the 0th position by default upon initialization.
        self.set_filter(list(self.filter_dictionary.keys())[0])

    def __str__(self) -> str:
        """String representation of the class."""
        return "SutterFilterWheel"

    def filter_change_delay(self, filter_name: str) -> None:
        """Calculate duration of time necessary to change filter wheel positions.

        Calculate duration of time necessary to change filter wheel positions.
        Identifies the number of positions that must be switched, and then retrieves
        the duration of time necessary to perform the switch from self.delay_matrix.

        Parameters
        ----------
        filter_name : str
            Name of filter that we want to move to.

        Note
        ----
            Detailed information on timing located on page 38:
            https://www.sutter.com/manuals/LB10-3_OpMan.pdf

        Warn
        ----
            Delay matrix should be model specific.

        Returns
        -------
        Index Error
            If the filter wheel position is out of range.
        """
        # Find the old and new positions, the distance between them, and the
        # delay necessary.
        old_position = self.wheel_position
        self.wheel_position = self.filter_dictionary[filter_name]
        delta_position = int(abs(old_position - self.wheel_position))
        try:
            self.wait_until_done_delay = self.delay_matrix[self.speed, delta_position]
        except IndexError:
            self.wait_until_done_delay = 0.01

    def set_filter(self, filter_name: str, wait_until_done: bool = True):
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

            # Make sure you are moving it to a reasonable filter position at a
            # reasonable speed.
            assert self.wheel_position in range(10)
            assert self.speed in range(8)

            # If previously we did not confirm that the initialization was complete,
            # check now.
            if not self.init_finished:
                self.read(2)
                self.init_finished = True
                logger.debug("SutterFilterWheel - Initialized.")

            """send the binary sequence via serial to move to the desired
            filter wheel position
            When number_of_filter_wheels = 1, wheel A changes.
            When number_of_filter_wheels = 2, wheel B changes.
            Filter Wheel Command Byte Encoding = wheel + (self.speed*16) +
            position = command byte
            """
            logger.debug(
                f"SutterFilterWheel - Moving to Position {self.filter_wheel_number-1}"
            )
            output_command = (
                (self.filter_wheel_number - 1) * 128
                + self.wheel_position
                + 16 * self.speed
            )
            output_command = output_command.to_bytes(1, "little")
            self.serial.write(output_command)
            # read echoing back
            self.read(1)

            #  Wheel Position Change Delay
            if wait_until_done:
                time.sleep(self.wait_until_done_delay)
                # read 0D back.
                self.read(1)

    def read(self, num_bytes: int) -> bytes:
        """Reads the specified number of bytes from the serial port.

        Parameters
        ----------
        num_bytes : int
            Number of bytes to read from the serial port.

        Returns
        -------
        response : bytes
            The bytes read from the serial port.

        Raises
        ------
        UserWarning
            The serial port to the Sutter Lambda 10-B is on, but it isn't responding as
            expected.
        """
        for i in range(100):
            num_waiting = self.serial.inWaiting()
            # if there are unread returns from previous commands
            if num_waiting >= num_bytes:
                break
            time.sleep(0.02)
        else:
            logger.error(
                "The serial port to the Sutter Lambda 10-B is on, but it isn't "
                "responding as expected."
            )
            raise UserWarning(
                "The serial port to the Sutter Lambda 10-B is on, but it isn't "
                "responding as expected."
            )
        return self.serial.read(num_bytes)

    def close(self) -> None:
        """Close the SutterFilterWheel serial port.

        Sets the filter wheel to the Empty-Alignment position and then closes the port.
        """
        logger.debug("SutterFilterWheel - Closing the Filter Wheel Serial Port")
        self.set_filter(list(self.filter_dictionary.keys())[0])
        self.serial.close()

    def __del__(self) -> None:
        """Delete the SutterFilterWheel class."""
        if self.serial.is_open:
            self.close()
