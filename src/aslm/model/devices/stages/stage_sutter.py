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

# Standard Imports
import logging
import sys

# Third Party Imports
import serial

# Local Imports
from aslm.model.devices.stages.stage_base import StageBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_sutter_stage_connection(com_port, baud_rate):
    """Build SutterStage Serial Port connection

    Attributes
    ----------
    comport : str
        Comport for communicating with the filter wheel, e.g., COM1.
    baudrate : int
        Baud rate for communicating with the filter wheel, e.g., 9600.
    """
    logging.debug(f"SutterStage - Opening Serial Port {com_port}")
    try:
        return serial.Serial(
            port=com_port,
            baudrate=baud_rate,
            timeout=0.25,
            parity=serial.PARITY_NONE,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=False,
        )
    except serial.SerialException:
        logger.warning("SutterStage - Could not establish Serial Port Connection")
        raise UserWarning(
            "Could not communicate with Sutter MP-285 via COMPORT", com_port
        )


class SutterStage(StageBase):
    """SutterStage Class

    Class for controlling Sutter MP-285 Stage.
    All commands return an ASCII CR (Carriage Return; 13 decimal, 0D hexadecimal) to
    indicate that the task associated with the command has completed. When the
    controller completes the task associated with a command, it sends ASCII CR back to
    the host computer indicating that it is ready to receive a new command. If a command
    returns data, the last byte returned is the task-completed indicator.

    Attributes
    ----------
    comport : str
        Comport for communicating with the filter wheel, e.g., COM1.
    baudrate : int
        Baud rate for communicating with the filter wheel, e.g., 9600.
    filter_dictionary : dict
        Dictionary with installed filter names, e.g., filter_dictionary = {'GFP', 0}.

    Methods
    -------
    read(num_bytes)
        Read num_bytes of bytes from the serial port.
    close()
        Set the filter wheel to the empty position and close the communication port.
    """

    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        super().__init__(microscope_name, device_connection, configuration, device_id)

        # Mapping from self.axes to corresponding ASI axis labelling
        axes_mapping = {"x": "X", "y": "Y", "z": "Z"}

        # Focus and Theta axes are not supported for Sutter Stage
        if "theta" in self.axes:
            self.axes.remove("theta")
        if "f" in self.axes:
            self.axes.remove("f")

        self.sutter_axes = list(map(lambda a: axes_mapping[a], self.axes))
        self.byte_order = sys.byteorder
        self.serial = device_connection
        self.wait_until_done = True
        self.resolution = "high"
        self.speed = 1000  # in units microns/s.

    def __del__(self):
        """Delete SutterStage Serial Port."""
        try:
            """
            Close the MP-285 Stage connection
            """
            self.serial.close()
            logger.debug("MP-285 stage connection closed")
        except (AttributeError, BaseException) as e:
            print("Error while disconnecting the MP-285 stage")
            logger.exception(e)
            raise

    def __enter__(self):
        """Establish SutterStage content manager."""
        return self

    def __exit__(self, type, value, traceback):
        """Releases the SutterStage resources"""
        logger.debug("SutterStage - Closing Device.")
        self.close()

    def close(self):
        """Close the SutterStage serial port."""
        logger.debug("SutterStage - Closing Serial Port")
        self.serial.close()

    def check_byte_order(self, command):
        """Confirm OS Byte Order
        MP-285 requires commands and responses to be interpreted as Little Endian.

        Parameters
        ----------
        command : bytes
            Command in format bytes.
        """

        if self.byte_order == "little":
            # No need to flip the received bytes.
            pass
        elif self.byte_order == "big":
            # Must flip the received bytes
            print("Sutter MP-285 - Detected Big Endian OS.  Not tested.")
            command = command[::-1]
        else:
            logger.error("Unknown byte order received from OS:", self.byte_order)
        return command

    def report_position(self):
        """
        Reports the position of the stage for all axes in microns
        Creates the hardware position dictionary.
        Updates the internal position dictionary.
        """

        try:
            # Send Command

            # Update internal dictionaries
            # self.update_position_dictionaries()
            return self.position_dict

        except serial.SerialException as error:
            logger.debug(f"MP-285 - Error: {error}")
            raise UserWarning("Communication error with MP-285 Stage")

    def move_axis_absolute(self, axis, axis_num, move_dictionary):
        """
        Implement movement logic along multiple axes for the MP-285 stage.

        The command sequence consists of 14 bytes:
        Command byte followed by three sets of four bytes containing position
        information in microsteps for X, Y, and Z, and ending with the terminator.
        Return data consists of 1 byte (task-complete indicator), which occurs after the
        move is complete.

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary. For example, axis='x' corresponds to
            'x_abs', 'x_min', etc.
        axis_num : int
            The corresponding number of this axis on a PI stage. Not applicable to the
            ASI stage.
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', 'x_min',
            etc. for one or more axes. Expects values in micrometers.
        Returns
        -------
        bool
            Was the move successful?
        """
        pass

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """
        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for one
            or more axes. Expects values in micrometers, except for theta, which is
            in degrees.
        wait_until_done : bool
            Block until stage has moved to its new spot.
        Returns
        -------
        success : bool
            Was the move successful?
        """
        pass
