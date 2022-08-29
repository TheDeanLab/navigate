"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

#  Standard Library Imports
import logging
import time

# Third Party Imports
import numpy as np
import serial

# Local Imports
from aslm.model.devices.filter_wheel.filter_wheel_base import FilterWheelBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class SutterFilterWheel(FilterWheelBase):
    r"""SutterFilterWheel Class

    Class for controlling Sutter Lambda Filter Wheels
    https://www.sutter.com/manuals/LB10-3_OpMan.pdf

    Attributes
    ----------
    comport : str
        Comport for communicating with the filter wheel, e.g., COM1.
    baudrate : int
        Baud rate for communicating with the filter wheel, e.g., 9600.
    filter_dictionary : dict
        Dictionary with installed filter names, e.g., filter_dictionary = {'GFP', 0}.
    number_of_filter_wheels : int
        Number of installed filter wheels.
    wheel_position : int
        Default filter wheel position
    wait_until_done_delay = float
        Duration of time to wait for a filter wheel change.
    wait_until_done = bool
        Flag for enabling the wait period for a filter wheel change.
    delay_matrix = np.ndarray
        Matrix of duration in seconds needed to switch filter wheel positions
    speed = int
        Filter wheel movement speed.  0 = fastest, 8 = slowest.

    Methods
    -------
    check_if_filter_in_filter_dictionary()
        Checks to see if filter name exists in the filter dictionary.
    filter_change_delay(filter_name)
        Change the filter wheel to the position occupied by filter_name
    read(num_bytes)
        Read num_bytes of bytes from the serial port.
    close()
        Set the filter wheel to the empty position and close the communication port.
    """

    def __init__(self, model):
        super().__init__(model)
        self.read_on_init = True
        self.speed = 2

        # Delay in s for the wait until done function
        self.delay_matrix = np.matrix([[0, 0.031, 0.051, 0.074, 0.095, 0.115],
                                       [0, 0.040, 0.065, 0.095, 0.120, 0.148],
                                       [0, 0.044, 0.075, 0.105, 0.136, 0.168],
                                       [0, 0.050, 0.088, 0.127, 0.165, 0.205],
                                       [0, 0.060, 0.108, 0.156, 0.205, 0.250],
                                       [0, 0.068, 0.123, 0.178, 0.235, 0.290],
                                       [0, 0.124, 0.235, 0.350, 0.460, 0.580],
                                       [0, 0.230, 0.440, 0.650, 0.860, 1.100]])

        logging.debug(f"SutterFilterWheel - Opening Serial Port {self.comport}")
        try:
            self.serial = serial.Serial(self.comport, self.baudrate, timeout=.25)
        except serial.SerialException:
            logger.warning("SutterFilterWheel - Could not establish Serial Port Connection")
            raise UserWarning('Could not communicate with Sutter Lambda 10-B via COMPORT', self.comport)

        logger.debug("SutterFilterWheel - Placing device In Online Mode")
        self.serial.write(bytes.fromhex('ee'))
        if self.read_on_init:
            self.read(2)  # class 'bytes'
            self.init_finished = True
            logger.debug("SutterFilterWheel - Initialized.")
        else:
            self.init_finished = False
        self.set_filter('Empty-Alignment')
        logger.debug("SutterFilterWheel -  Placed in Default Filter Position.")

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        logger.debug("SutterFilterWheel - Closing Device.")
        self.close()

    def filter_change_delay(self, filter_name):
        r"""Calculate duration of time necessary to change filter wheel positions.
        Identifies the number of positions that must be switched, and then retrieves
        the duration of time necessary to perform the switch from self.delay_matrix.
        Detailed information on timing located on page 38: https://www.sutter.com/manuals/LB10-3_OpMan.pdf

        Parameters
        ----------
        filter_name : str
            Name of filter that we want to move to.
        """
        # Find the old and new positions, the distance between them, and the delay necessary.
        old_position = self.wheel_position
        self.wheel_position = self.filter_dictionary[filter_name]
        delta_position = int(abs(old_position - self.wheel_position))
        self.wait_until_done_delay = (self.delay_matrix[self.speed, delta_position])

    def set_filter(self, filter_name, wait_until_done=True):
        r"""Change the filter wheel to the filter designated by the filter position argument.

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

            # Make sure you are moving it to a reasonable filter position at a reasonable speed.
            assert self.wheel_position in range(10)
            assert self.speed in range(8)

            # If previously we did not confirm that the initialization was complete, check now.
            if not self.init_finished:
                self.read(2)
                self.init_finished = True
                logger.debug("SutterFilterWheel - Initialized.")

            for wheel_idx in range(self.number_of_filter_wheels):
                """Loop through each filter, and send the binary sequence via serial to
                move to the desired filter wheel position
                When number_of_filter_wheels = 1, loop executes once, and only wheel A changes.
                When number_of_filter_wheels = 2, loop executes twice, with both wheel A and
                B moving to the same position sequentially
                Filter Wheel Command Byte Encoding = wheel + (self.speed*16) + position = command byte
                """
                logger.debug(f"SutterFilterWheel - Moving to Position {wheel_idx}")
                output_command = wheel_idx * 128 + self.wheel_position + 16 * self.speed
                output_command = output_command.to_bytes(1, 'little')
                self.serial.write(output_command)

            #  Wheel Position Change Delay
            if wait_until_done:
                time.sleep(self.wait_until_done_delay)

    def read(self, num_bytes):
        r"""Reads the specified number of bytes from the serial port.

        Parameters
        ----------
        num_bytes : int
            Number of bytes to read from the serial port.
        """
        for i in range(100):
            num_waiting = self.serial.inWaiting()
            if num_waiting == num_bytes:
                break
            time.sleep(0.02)
        else:
            logger.error("The serial port to the Sutter Lambda 10-B is on, but it isn't responding as expected.")
            raise UserWarning("The serial port to the Sutter Lambda 10-B is on, but it isn't responding as expected.")
        return self.serial.read(num_bytes)

    def close(self):
        r"""Close the SutterFilterWheel serial port.

        Sets the filter wheel to the Empty-Alignment position and then closes the port.
        """
        logger.debug("SutterFilterWheel - Closing the Filter Wheel Serial Port")
        self.set_filter('Empty-Alignment')
        self.serial.close()
