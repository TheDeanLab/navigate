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
import io

# Third Party Imports
import serial

# Local Imports
from navigate.model.devices.filter_wheel.base import FilterWheelBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_filter_wheel_connection(comport, baudrate, timeout=0.25):
    """Build LUDLFilterWheel Serial Port connection

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
        Serial port connection to the filter wheel.

    Raises
    ------
    UserWarning
        Could not communicate with LUDL MAC6000 via COMPORT.
    """
    logging.debug(f"LUDLFilterWheel - Opening Serial Port {comport}")
    try:
        return serial.Serial(
            comport,
            baudrate,
            parity=serial.PARITY_NONE,
            timeout=timeout,
            xonxoff=False,
            stopbits=serial.STOPBITS_TWO,
        )
    except serial.SerialException:
        logger.error("LUDLFilterWheel - Could not establish Serial Port Connection")
        raise UserWarning(
            "Could not communicate with LUDL MAC6000 via COMPORT", comport
        )


class LUDLFilterWheel(FilterWheelBase):

    """LUDLFilterWheel - Class for controlling LUDL Electronic Products Filter Wheels

    Testing using MAC6000 controller over RS-232. USB or Ethernet not tested.
    Single filter wheel only, but MAC6000 can handle max 2. Would need to modify code.

    Note
    ----
        Code for class adapted from Dr. Fabian Voigt's mesoSPIM code:
        https://github.com/ffvoigt/mesoSPIM-control/blob/master/mesoSPIM/src/mesoSPIM_FilterWheel.py

    """

    def __init__(self, device_connection, device_config):
        """Initialize the LUDLFilterWheel class.

        Parameters
        ----------
        device_connection : serial.Serial
            Serial port connection to the filter wheel.
        device_config : dict
            Dictionary of device configuration parameters.
        """

        super().__init__(device_connection, device_config)

        #: obj: Serial port connection to the filter wheel.
        self.serial = device_connection

        #: dict: Configuration dictionary.
        self.device_config = device_config

        #: io.TextIOWrapper: Text I/O wrapper for the serial port.
        self.sio = io.TextIOWrapper(io.BufferedRWPair(self.serial, self.serial))

        #: float: Delay for filter wheel to change positions.
        self.wait_until_done_delay = device_config["filter_wheel_delay"]

    def __str__(self):
        """String representation of the class."""
        return "LUDLFilterWheel"

    def set_filter(self, filter_name, wait_until_done=True):
        """Set the filter wheel to a specific filter position.

        Parameters
        ----------
        filter_name : str
            Name of the filter position.
        wait_until_done : bool
            Wait until the filter wheel has changed positions.
        """

        if self.check_if_filter_in_filter_dictionary(filter_name) is True:

            # single wheel code only...

            # Set the new position by cross-referencing the filter dict
            self.wheel_position = self.filter_dictionary[filter_name]

            # Send the command to go to the new position
            self.sio.write(f"Rotat S M {self.wheel_position}\n")
            self.sio.flush()

            if wait_until_done:
                time.sleep(self.wait_until_done_delay)

    def close(self):
        """Close the LUDLFilterWheel serial port.

        Sets the filter wheel to the Empty-Alignment position and then closes the port.
        """
        logger.debug("LUDLFilterWheel - Closing the Filter Wheel Serial Port")
        self.set_filter(list(self.filter_dictionary.keys())[0])
        self.serial.close()

    def __del__(self):
        """Destructor for the LUDLFilterWheel class."""
        if self.serial.is_open:
            self.close()
