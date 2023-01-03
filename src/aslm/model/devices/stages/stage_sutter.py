# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Standard Imports
from curses import baudrate
import logging
import time
import sys

# Third Party Imports
import numpy as np
import serial

# Local Imports
from aslm.model.devices.stages.stage_base import StageBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_sutter_stage_connection(com_port, baud_rate):
    r"""Build SutterStage Serial Port connection

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
    r"""SutterStage Class

    Class for controlling Sutter MP-285 Stage.
    All commands return an ASCII CR (Carriage Return; 13 decimal, 0D hexadecimal) to indicate that the task associated
    with the command has completed. When the controller completes the task associated with a command, it sends ASCII CR
    back to the host computer indicating that it is ready to receive a new command. If a command returns data, the last
    byte returned is the task-completed indicator.

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
        self.sutter_axes = list(map(lambda a: axes_mapping[a], self.axes))
        self.byte_order = sys.byteorder
        self.serial = device_connection
        self.wait_until_done = True
        self.resolution = "high"
        self.speed = 1000  # in units microns/s.

    def __del__(self):
        r"""Delete SutterStage Serial Port."""
        try:
            """
            Close the MP-285 Stage connection
            """
            self.serial.close()
            logger.debug("MP-285 stage connection closed")
        except BaseException as e:
            print("Error while disconnecting the MP-285 stage")
            logger.exception(e)
            raise

    def __enter__(self):
        r"""Establish SutterStage content manager."""
        return self

    def __exit__(self, type, value, traceback):
        r"""Releases the SutterStage resources"""
        logger.debug("SutterStage - Closing Device.")
        self.close()

    def close(self):
        r"""Close the SutterStage serial port."""
        logger.debug("SutterStage - Closing Serial Port")
        self.serial.close()

    def flush_buffers(self):
        r"""Flush Serial I/O Buffers"""
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

    def check_byte_order(self, command):
        r"""Confirm OS Byte Order
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

    @staticmethod
    def convert_microsteps_to_microns(self, microsteps):
        r"""Converts MP-285 microsteps to microns

        Parameters
        ----------
        microsteps : float
            Distance in microsteps

        Returns
        ---------
        microns : float
            Distance in microns
        """

        microns = np.multiply(microsteps, 0.04)
        return microns

    @staticmethod
    def convert_microns_to_microsteps(self, microns):
        r"""Converts microsteps to microns for MP-285 communication.

        Parameters
        ----------
        microns : float
            Distance in microns.

        Returns
        -------
        microsteps : float
            Distance in microsteps
        """

        microsteps = np.divide(microns, 0.04)
        return microsteps

    def set_stage_speed_and_resolution(self, speed, resolution):
        r"""Sets the MP-285 stage speed and resolution.

        Parameters
        ----------
        speed : int
            Low Resolution = 0-3000 microns/sec
            High Resolution = 0-1310 microns/sec
        resolution : int
            Low - 0.2 microns/microstep = 10 microsteps/step
            High - 0.04 microns/microstep = 50 microsteps/step

        """
        logger.debug(f"Setting MP-285 Stage Speed")
        if self.resolution == "high":
            resolution_bit = 1
            if speed > 1310:
                logger.error(
                    "MP-285 - Speed value for high-resolution mode too high:", speed
                )
                speed = 1310

        elif self.resolution == "low":
            resolution_bit = 0
            if speed > 3000:
                logger.error(
                    "MP-285 - Speed value for low-resolution mode too high:", speed
                )
                speed = 3000
        else:
            logger.error("Unknown MP-285 stage resolution:", self.resolution)

        # Generate Command
        # One unsigned short (16-bit integer (2 bytes) containing both resolution and velocity values.
        speed_and_res = int(resolution_bit * 32768 + speed)
        command = (
            bytes.fromhex("56")
            + speed_and_res.to_bytes(length=2, byteorder="little", signed=False)
            + bytes.fromhex("0d")
        )

        # Write Command
        self.flush_buffers()
        self.serial.write(command)

        # Get Response
        response = self.serial.read_until(expected=bytes.fromhex("0d"), size=100)
        if response == bytes.fromhex("0d"):
            self.resolution = resolution
            self.speed = speed
        else:
            logger.error("MP-285 unable to change resolution and/or speed.")
            raise UserWarning("MP-285 unable to change resolution and/or speed")

    def report_position(self):
        """
        Reports the position of the stage for all axes in microns
        Creates the hardware position dictionary.
        Updates the internal position dictionary.
        """

        try:
            # Send Command
            self.flush_buffers()
            command = bytes.fromhex("63") + bytes.fromhex("0d")
            self.serial.write(command)

            # Receive Position Information -  The data returned consists of 13 bytes: 12 bytes containing X, Y, & Z
            # position values in microsteps (4 bytes each), followed with the task-complete indicator (1 byte).
            position_information = self.serial.read_until(
                expected=bytes.fromhex("0d"), size=100
            )
            self.x_pos = self.convert_microsteps_to_microns(
                int.from_bytes(
                    position_information[0:3], byteorder="little", signed=True
                )
            )
            self.y_pos = self.convert_microsteps_to_microns(
                int.from_bytes(
                    position_information[4:7], byteorder="little", signed=True
                )
            )
            self.z_pos = self.convert_microsteps_to_microns(
                int.from_bytes(
                    position_information[8:11], byteorder="little", signed=True
                )
            )

            # Update internal dictionaries
            self.update_position_dictionaries()
            return self.position_dict

        except serial.SerialException as error:
            logger.debug(f"MP-285 - Error: {error}")
            raise UserWarning("Communication error with MP-285 Stage")

    def move_axis_absolute(self, axis, axis_num, move_dictionary):
        """
        Implement movement logic along multiple axes for the MP-285 stage.

        The command sequence consists of 14 bytes:
        Command byte followed by three sets of four bytes containing position information in microsteps for X, Y, and Z,
        and ending with the terminator.
        Return data consists of 1 byte (task-complete indicator), which occurs after the move is complete.

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary. For example, axis='x' corresponds to 'x_abs', 'x_min', etc.
        axis_num : int
            The corresponding number of this axis on a PI stage. Not applicable to the ASI stage.
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', 'x_min', etc. for one or more axes.
            Expects values in micrometers.
        Returns
        -------
        bool
            Was the move successful?
        """
        axis_abs = self.get_abs_position(axis, move_dictionary)
        if axis_abs == -1e50:
            return False

        x_target = int(self.convert_microns_to_microsteps(self.x_pos))
        y_target = int(self.convert_microns_to_microsteps(self.y_pos))
        z_target = int(self.convert_microns_to_microsteps(self.z_pos))

        x_steps = x_target.to_bytes(length=4, byteorder="little", signed=True)
        y_steps = y_target.to_bytes(length=4, byteorder="little", signed=True)
        z_steps = z_target.to_bytes(length=4, byteorder="little", signed=True)

        # Move stage
        try:
            self.serial.write(
                bytes.fromhex("6d") + x_steps + y_steps + z_steps + bytes.fromhex("0d")
            )
            response = self.serial.read(1)
            if response == bytes.fromhex("0d"):
                pass
            else:
                logger.debug("MP-285 - Unknown response after attempt to mvoe stage")
                raise UserWarning(
                    "MP-285 - Unknown response after attempt to mvoe stage"
                )

        except BaseException as e:
            print(
                f"MP-285 stage move axis absolute failed or is trying to move out of range: {e}"
            )
            logger.exception(e)
            return False

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """
        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for one or more axes.
            Expects values in micrometers, except for theta, which is in degrees.
        wait_until_done : bool
            Block until stage has moved to its new spot.
        Returns
        -------
        success : bool
            Was the move successful?
        """
        pass

    def stop(self):
        r"""This command interrupts and stops a move in progress that originally initiated by the Move (‘m’) command.
        The command sequence consists of 1 byte: Command byte (no terminator).

        Return data consists of 1 byte if movement is not in progress, or 2 bytes (‘=’ (move-in- progress indicator)
        and task-complete indicator."""

        try:
            # Send Command
            self.flush_buffers()
            self.serial.write(bytes.fromhex("03"))

            # Get Response
            response = self.serial.read(1)
            if response == bytes.fromhex("0d"):
                # Stage halted.
                pass
            elif response == bytes.fromhex("3d"):
                # Move in progress
                second_response = self.serial.read(1)
                assert second_response == bytes.fromhex("0d")
        except BaseException as e:
            print(f"MP-285 stage halt command failed: {e}")
            logger.exception(e)
