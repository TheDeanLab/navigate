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
import serial
import threading

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

    def __init__(self, com_port, baud_rate, timeout=0.25):
        self.serial = serial.Serial()
        self.serial.port = com_port
        self.serial.baudrate = baud_rate
        self.serial.timeout = timeout
        self.serial.parity = serial.PARITY_NONE
        self.serial.bytesize = serial.EIGHTBITS
        self.serial.stopbits = serial.STOPBITS_ONE
        self.serial.xonxoff = False
        self.serial.rtscts = True

        self.speed = 1000  # None
        self.resolution = "high"  # None
        self.wait_until_done = True

        self.wait_time = 0.002
        self.n_waits = max(int(timeout / self.wait_time), 1)

        # Thread blocking here to prevent calls to get_current_position()
        # while move_to_specified_position is waiting for a response. Serial
        # commands must complete or the MP-285A completely locks up and has
        # to be power cycled.
        self.safe_to_write = threading.Event()
        self.safe_to_write.set()

    def safe_write(self, command):
        self.safe_to_write.wait()
        self.safe_to_write.clear()
        self.serial.write(command)

    def connect_to_serial(self):
        try:
            self.serial.open()
        except serial.SerialException as e:
            print("MP285 serial connection failed!")
            raise e

    def disconnect_from_serial(self):
        self.serial.close()

    def flush_buffers(self):
        """Flush Serial I/O Buffers.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.safe_to_write.wait()
        self.safe_to_write.clear()
        self.serial.read_all()
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        self.safe_to_write.set()

    @staticmethod
    def convert_microsteps_to_microns(microsteps):
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
    def convert_microns_to_microsteps(microns):
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
        # print("calling get_current_position")
        self.flush_buffers()
        command = bytes.fromhex("63") + bytes.fromhex("0d")
        self.safe_write(command)
        # position_information = self.serial.read_until(
        #     expected=bytes.fromhex("0d"), size=100
        # )
        # print(f"sending: {command}")
        position_information = b""
        for _ in range(self.n_waits):
            position_information = self.serial.read(13)
            if position_information == b"":
                time.sleep(self.wait_time)
            elif len(position_information) == 13:
                break
            else:
                # print(f"Ah hell: {position_information}")
                raise UserWarning(
                    "Encountered response {position_information}. "
                    "You probably need to power cycle the stage."
                )
        self.safe_to_write.set()
        # print(f"received: {position_information}")
        xs = int.from_bytes(position_information[0:4], byteorder="little", signed=True)
        ys = int.from_bytes(position_information[4:8], byteorder="little", signed=True)
        zs = int.from_bytes(position_information[8:12], byteorder="little", signed=True)
        # print(f"converted to microsteps: {xs} {ys} {zs}")
        x_pos = self.convert_microsteps_to_microns(xs)
        y_pos = self.convert_microsteps_to_microns(ys)
        z_pos = self.convert_microsteps_to_microns(zs)
        # print(f"converted to position: {x_pos} {y_pos} {z_pos}")
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
        # print("calling move_to_specified_position")
        # print(f"moving to {x_pos} {y_pos} {z_pos}")
        # Calculate time to move
        # current_x, current_y, current_z = self.get_current_position()
        # delta_x = abs(x_pos - current_x)
        # delta_y = abs(y_pos - current_y)
        # delta_z = abs(z_pos - current_z)
        # max_distance = max(delta_x, delta_y, delta_z)
        # time_to_move = np.clip(max_distance / self.speed, 0.02, 1.0)
        # print(f"time to move: {time_to_move} s")

        # Convert microns to microsteps and create command.
        x_target = int(self.convert_microns_to_microsteps(x_pos))
        y_target = int(self.convert_microns_to_microsteps(y_pos))
        z_target = int(self.convert_microns_to_microsteps(z_pos))
        x_steps = x_target.to_bytes(length=4, byteorder="little", signed=True)
        y_steps = y_target.to_bytes(length=4, byteorder="little", signed=True)
        z_steps = z_target.to_bytes(length=4, byteorder="little", signed=True)

        # Move stage
        move_cmd = (
            bytes.fromhex("6d") + x_steps + y_steps + z_steps + bytes.fromhex("0d")
        )
        self.safe_write(move_cmd)
        # print(f"move command: {move_cmd} wait_until_done {self.wait_until_done}")

        for _ in range(self.n_waits):
            # time.sleep(time_to_move)
            response = self.serial.read(1)
            # print(f"move response: {response}")
            if response == b"":
                time.sleep(self.wait_time)
            elif response == bytes.fromhex("0d"):
                self.safe_to_write.set()
                return True
            else:
                self.safe_to_write.set()
                self.flush_buffers()
                # print(f"Uh oh: {response}")
                raise UserWarning(
                    "Encountered response {response}. "
                    "You probably need to power cycle the stage."
                )

        # # time.sleep(time_to_move)
        # self.safe_to_write.set()

        # response = self.serial.read(1)
        # print(f"move response: {response}")
        # if response == bytes.fromhex("0d"):
        #     move_complete = True
        # else:
        #     move_complete = False
        # return move_complete

        self.safe_to_write.set()
        return False

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
        # print("calling set_resolution_and_velocity")
        # print(f"resolution: {resolution}")
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
        self.safe_write(command)
        response = self.serial.read(1)
        # print(f"Response {response}")
        if response == bytes.fromhex("0d"):
            self.speed = speed
            self.resolution = resolution
            command_complete = True
        else:
            command_complete = False
        # print(f"Command complete? {command_complete}")
        self.safe_to_write.set()
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
        # print("calling interrupt_move")

        # Send Command
        self.safe_to_write.set()
        self.flush_buffers()
        self.safe_write(bytes.fromhex("03"))

        # Get Response
        for _ in range(self.n_waits):
            # time.sleep(time_to_move)
            response = self.serial.read(1)
            # print(f"move response: {response}")
            if response == b"":
                time.sleep(self.wait_time)
            elif response == bytes.fromhex("0d"):
                self.safe_to_write.set()
                return True
            elif response == bytes.fromhex("3d"):
                for _ in range(self.n_waits):
                    response2 = self.serial.read(1)
                    if response2 == b"":
                        time.sleep(self.wait_time)
                    elif response == bytes.fromhex("0d"):
                        self.safe_to_write.set()
                        return True

        self.safe_to_write.set()
        return False

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
        # print("calling set_absolute_mode")
        self.flush_buffers()
        abs_cmd = bytes.fromhex("61") + bytes.fromhex("0d")
        self.safe_write(abs_cmd)

        for _ in range(self.n_waits):
            # time.sleep(time_to_move)
            response = self.serial.read(1)
            # print(f"move response: {response}")
            if response == b"":
                time.sleep(self.wait_time)
            elif response == bytes.fromhex("0d"):
                self.safe_to_write.set()
                return True
        self.safe_to_write.set()
        return False

    # def set_relative_mode(self):
    #     """Set MP285 to Relative Position Mode.
    #
    #     This command sets the nature of the positional values specified with the Move
    #     (‘m’) command as relative positions as measured from the current position
    #     (absolute position returned by the Get Current Position (‘c’) command).
    #     The command sequence consists of 2 bytes: Command byte, followed by the
    #     terminator. Return data consists of 1 byte (task-complete indicator).
    #
    #     Returns
    #     -------
    #     command_complete : bool
    #         True if command was successful, False if not.
    #     """
    #     # print("calling set_relative_mode")
    #     self.flush_buffers()
    #     self.safe_write(bytes.fromhex("62") + bytes.fromhex("0d"))
    #     response = self.serial.read(1)
    #     if response == bytes.fromhex("0d"):
    #         command_complete = True
    #     else:
    #         command_complete = False
    #     self.safe_to_write.set()
    #     return command_complete

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
        # print("calling refresh_display")
        self.flush_buffers()
        self.safe_write(bytes.fromhex("6E") + bytes.fromhex("0d"))
        response = self.serial.read(1)
        if response == bytes.fromhex("0d"):
            command_complete = True
        else:
            command_complete = False
        self.safe_to_write.set()
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
        # print("calling reset_controller")
        self.flush_buffers()
        self.safe_write(bytes.fromhex("72") + bytes.fromhex("0d"))
        response = self.serial.read(1)
        if response == bytes.fromhex("0d"):
            command_complete = True
        else:
            command_complete = False
        self.safe_to_write.set()
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
        # print("calling get_controller_status")
        self.flush_buffers()
        self.safe_write(bytes.fromhex("73") + bytes.fromhex("0d"))
        response = self.serial.read(33)
        if response[-1] == bytes.fromhex("0d"):
            command_complete = True
        else:
            command_complete = False

        # print(response)
        self.safe_to_write.set()
        # not implemented yet. See page 74 of documentation.
        return command_complete

    def close(self):
        """Close the serial connection to the stage"""
        self.serial.close()
