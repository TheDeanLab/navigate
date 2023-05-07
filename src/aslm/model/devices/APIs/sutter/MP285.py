# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
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

# Standard library imports
import time

# Third-party imports
import numpy as np

# Local application imports


class MP285:
    """Sutter MP285 3D Stage API

    The USB interface expects a baud rate of 9600, 8 data bits, 1 stop bits,
    no parity, and no flow control.

    The serial interface expects a baud rate of 9600, 8 data bits, 1 stop bits,
    no parity, and hardware or RTS/CTS flow control.

    Little-endian byte order is used for all commands and responses.

    Each command sequence consists of at least one byte, the first of which is the
    “command byte”. Those commands that have parameters or arguments require a
    sequence of bytes that follow the command byte. No delimiters are used between
    command sequence arguments, and command sequence terminators are used in most cases.

    Most command sequences have a terminator: ASCII CR (Carriage Return; 13 decimal,
    0D hexadecimal) to indicate that the task associated with the command has completed.
    When the controller completes the task associated with a command, it sends ASCII CR
    back to the host computer indicating that it is ready to receive a new command.
    If a command returns data, the last byte returned is the task-completed indicator.
    """

    def __init__(self, device_connection):
        super().__init__(device_connection)
        self.serial = None
        self.speed = None
        self.resolution = None
        self.wait_until_done = True

    def flush_buffers(self):
        """Flush Serial I/O Buffers.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

    @staticmethod
    def convert_microsteps_to_microns(self, microsteps):
        """Converts microsteps to microns

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
        """Converts microsteps to microns.

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

    def get_current_position(self):
        """Get the current stage position.

        Gets the stage position. The data returned consists of 13 bytes:
        12 bytes containing X, Y, & Z position values in microsteps (4 bytes each),
        followed with the task-complete indicator (1 byte).

        Returns
        -------
        x_pos : float
            X position in microns
        y_pos : float
            Y position in microns
        z_pos : float
            Z position in microns

        """
        self.flush_buffers()
        command = bytes.fromhex("63") + bytes.fromhex("0d")
        self.serial.write(command)
        position_information = self.serial.read_until(
            expected=bytes.fromhex("0d"), size=100
        )
        x_pos = self.convert_microsteps_to_microns(
            int.from_bytes(position_information[0:3], byteorder="little", signed=True)
        )
        y_pos = self.convert_microsteps_to_microns(
            int.from_bytes(position_information[4:7], byteorder="little", signed=True)
        )
        z_pos = self.convert_microsteps_to_microns(
            int.from_bytes(position_information[8:11], byteorder="little", signed=True)
        )
        return x_pos, y_pos, z_pos

    def move_to_specified_position(self, x_pos, y_pos, z_pos):
        """Move to Specified Position (‘m’) Command

        This command instructs the controller to move all three axes to the position
        specified.

        The command sequence consists of 14 bytes: Command byte followed by three
        sets of four bytes containing position information in microsteps for X, Y,
        and Z, and ending with the terminator.
        Return data consists of 1 byte (task-complete indicator), which occurs after
        the  move is complete.

        Parameters
        ----------
        x_pos : float
            X position in microns
        y_pos : float
            Y position in microns
        z_pos : float
            Z position in microns

        Returns
        -------
        move_complete : bool
            True if move was successful, False if not.
        """

        # Calculate time to move
        current_x, current_y, current_z = self.get_current_position()
        delta_x = abs(x_pos - current_x)
        delta_y = abs(y_pos - current_y)
        delta_z = abs(z_pos - current_z)
        max_distance = max(delta_x, delta_y, delta_z)
        time_to_move = max_distance / self.speed

        # Convert microns to microsteps and create command.
        x_target = int(self.convert_microns_to_microsteps(x_pos))
        y_target = int(self.convert_microns_to_microsteps(y_pos))
        z_target = int(self.convert_microns_to_microsteps(z_pos))
        x_steps = x_target.to_bytes(length=4, byteorder="little", signed=True)
        y_steps = y_target.to_bytes(length=4, byteorder="little", signed=True)
        z_steps = z_target.to_bytes(length=4, byteorder="little", signed=True)

        # Move stage
        self.serial.write(
            bytes.fromhex("6d") + x_steps + y_steps + z_steps + bytes.fromhex("0d")
        )

        if self.wait_until_done is True:
            time.sleep(time_to_move)

        response = self.serial.read(1)
        if response == bytes.fromhex("0d"):
            move_complete = True
        else:
            move_complete = False
        return move_complete

    def set_resolution_and_velocity(self, speed, resolution):
        """Sets the MP-285 stage speed and resolution.

        This command instructs the controller to move all three axes to the position
        specified. The command sequence consists of 4 bytes: Command byte, followed
        by 2 bytes containing resolution and velocity information, and ending with
        the  terminator. Return data consists of 1 byte (task-complete indicator).

        Parameters
        ----------
        speed : int
            Low Resolution = 0-3000 microns/sec
            High Resolution = 0-1310 microns/sec
        resolution : str
            Low - 0.2 microns/microstep = 10 microsteps/step
            High - 0.04 microns/microstep = 50 microsteps/step

        Returns
        -------
        command_complete : bool
            True if command was successful, False if not.
        """
        if resolution == "high":
            resolution_bit = 1
            if speed > 1310:
                speed = 1310
                raise UserWarning(
                    "High resolution mode of Sutter MP285 speed too "
                    "high. Setting to 1310 microns/sec."
                )
        elif resolution == "low":
            resolution_bit = 0
            if speed > 3000:
                speed = 3000
                raise UserWarning(
                    "Low resolution mode of Sutter MP285 speed too "
                    "high. Setting to 3000 microns/sec."
                )
        else:
            raise UserWarning("MP-285 resolution must be 'high' or 'low'")

        speed_and_res = int(resolution_bit * 32768 + speed)
        command = (
            bytes.fromhex("56")
            + speed_and_res.to_bytes(length=2, byteorder="little", signed=False)
            + bytes.fromhex("0d")
        )

        # Write Command and get response
        self.flush_buffers()
        self.serial.write(command)
        response = self.serial.read_until(expected=bytes.fromhex("0d"), size=100)
        if response == bytes.fromhex("0d"):
            self.speed = speed
            self.resolution = resolution
            command_complete = True
        else:
            command_complete = False
        return command_complete

    def interrupt_move(self):
        """Interrupt stage movement.

        This command interrupts and stops a move in progress that originally
        initiated by the Move (‘m’) command. The command sequence consists of 1 byte:
        Command byte (no terminator).

        Return data consists of 1 byte if movement is not in progress, or 2 bytes
        ('=' (move-in- progress indicator)and task-complete indicator.

        Returns
        -------
        stage_stopped : bool
            True if move was successful, False if not.
        """

        # Send Command
        self.flush_buffers()
        self.serial.write(bytes.fromhex("03"))

        # Get Response
        response = self.serial.read(1)
        if response == bytes.fromhex("0d"):
            stage_stopped = True
        else:
            second_response = self.serial.read(1)
            if second_response == bytes.fromhex("0d"):
                stage_stopped = True
            else:
                stage_stopped = False

        return stage_stopped

    def set_absolute_mode(self):
        """Set MP285 to Absolute Position Mode.

        This command sets the nature of the positional values specified with the Move
        (‘m’) command as absolute positions as measured from the point of origin
        (Position 0). The command sequence consists of 2 bytes: Command byte, followed
        by the terminator. Return data consists of 1 byte (task-complete indicator).

        Returns
        -------
        command_complete : bool
            True if command was successful, False if not.

        """
        self.flush_buffers()
        self.serial.write(bytes.fromhex("61") + bytes.fromhex("0d"))
        response = self.serial.read(1)
        if response == bytes.fromhex("0d"):
            command_complete = True
        else:
            command_complete = False
        return command_complete

    def set_relative_mode(self):
        """Set MP285 to Relative Position Mode.

        This command sets the nature of the positional values specified with the Move
        (‘m’) command as relative positions as measured from the current position
        (absolute position returned by the Get Current Position (‘c’) command).
        The command sequence consists of 2 bytes: Command byte, followed by the
        terminator. Return data consists of 1 byte (task-complete indicator).

        Returns
        -------
        command_complete : bool
            True if command was successful, False if not.
        """
        self.flush_buffers()
        self.serial.write(bytes.fromhex("62") + bytes.fromhex("0d"))
        response = self.serial.read(1)
        if response == bytes.fromhex("0d"):
            command_complete = True
        else:
            command_complete = False
        return command_complete

    def refresh_display(self):
        """Refresh the display on the MP-285 controller.

        This command refreshes the VFD (Vacuum Fluorescent Display) of the controller.
        The command sequence consists of 2 bytes: Command byte and terminator.
        Return data consists of 1 byte: task-complete indicator.

        Returns
        -------
        command_complete : bool
            True if command was successful, False if not.
        """
        self.flush_buffers()
        self.serial.write(bytes.fromhex("6E") + bytes.fromhex("0d"))
        response = self.serial.read(1)
        if response == bytes.fromhex("0d"):
            command_complete = True
        else:
            command_complete = False
        return command_complete

    def reset_controller(self):
        """Reset the MP-285 controller.

        This command resets the controller. The command sequence consists of 2 bytes:
        Command byte and terminator. Return data consists of 1 byte: task-complete
        indicator.

        Returns
        -------
        command_complete : bool
            True if command was successful, False if not.
        """
        self.flush_buffers()
        self.serial.write(bytes.fromhex("72") + bytes.fromhex("0d"))
        response = self.serial.read(1)
        if response == bytes.fromhex("0d"):
            command_complete = True
        else:
            command_complete = False
        return command_complete

    def get_controller_status(self):
        """Get the status of the MP-285 controller.

        This command gets status information from the controller and returns it in
        fixed-sized block of data. The command sequence consists of 2 bytes: Command
        byte and terminator. Return data consists of 33 bytes: 32 bytes of
        information and task-complete indicator.

        Returns
        -------
        command_complete = bool
            True if command was successful, False if not.
        """
        self.flush_buffers()
        self.serial.write(bytes.fromhex("73") + bytes.fromhex("0d"))
        response = self.serial.read(33)
        if response[-1] == bytes.fromhex("0d"):
            command_complete = True
        else:
            command_complete = False

        # not implemented yet. See page 74 of documentation.
        return command_complete
