# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
import logging

# Third-party imports
import numpy as np

# Local application imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


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
        self.write_done_flag = threading.Lock()
        self.is_moving = False
        self.last_write_time = time.time()

        self.commands_num = 10
        self.top_command_idx = 0
        self.last_command_idx = 0
        self.is_interrupted = False
        self.is_moving = False
        self.unreceived_bytes = 0
        self.commands_buffer = [1] * self.commands_num


    def send_command(self, command, response_num=1):
        self.safe_to_write.wait()
        self.safe_to_write.clear()
        self.write_done_flag.acquire()
        # wait_num = self.serial.in_waiting
        # if wait_num > 0:
        #     self.serial.read(wait_num)
        self.serial.write(command)
        logger.debug(f"MP285 send command {command}")
        self.commands_buffer[self.last_command_idx] = response_num
        idx = self.last_command_idx
        self.last_command_idx = (self.last_command_idx + 1) % self.commands_num
        self.write_done_flag.release()
        return idx
    
    def read_response(self, idx):
        if idx != self.top_command_idx:
            return None
        
        l = self.commands_buffer[self.top_command_idx]
        r = ""
        for _ in range(self.n_waits):
            if self.unreceived_bytes > 0 and self.serial.in_waiting >= l + self.unreceived_bytes:
                r = self.serial.read(l + self.unreceived_bytes)
                logger.debug(f"MP285 read response {r}")
                if r[self.unreceived_bytes-1] == 13: #b'\r'
                    r = r[self.unreceived_bytes:]
                else:
                    r = r[:l]
                logger.debug(f"MP285 valid response: {r}")
                self.unreceived_bytes = 0
                self.n_waits -= 5
                break
            elif self.serial.in_waiting >= self.commands_buffer[self.top_command_idx]:
                r = self.serial.read(self.commands_buffer[self.top_command_idx])
                logger.debug(f"MP285 read response {r}")
                break
            time.sleep(self.wait_time)
        
        if r == "":
            logger.error("Haven't received any responses from MP285! Please check the stage device!")
            self.unreceived_bytes += self.commands_buffer[self.top_command_idx]
            logger.error(f"MP285 unreceived bytes: {self.unreceived_bytes}")
            # let the waiting time a little bit longer
            self.n_waits += 5
        self.top_command_idx = (self.top_command_idx + 1) % self.commands_num
        self.safe_to_write.set()
        return r
        # raise TimeoutError("Haven't received any responses from MP285! Please check the stage device!")

    def connect_to_serial(self):
        try:
            self.serial.open()
        except serial.SerialException as e:
            print("MP285 serial connection failed.")
            logger.error(f"{str(self)}, Could not open port {self.serial.port}")
            raise e

    def disconnect_from_serial(self):
        self.serial.close()

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
        # self.flush_buffers()
        command = bytes.fromhex("63") + bytes.fromhex("0d")
        idx = self.send_command(command, 13)

        while True:
            position_information = self.read_response(idx)
            if position_information is not None:
                break
            time.sleep(self.wait_time)

        if len(position_information) < 13:
            return None, None, None
        xs = int.from_bytes(position_information[0:4], byteorder="little", signed=True)
        ys = int.from_bytes(position_information[4:8], byteorder="little", signed=True)
        zs = int.from_bytes(position_information[8:12], byteorder="little", signed=True)
        x_pos = self.convert_microsteps_to_microns(xs)
        y_pos = self.convert_microsteps_to_microns(ys)
        z_pos = self.convert_microsteps_to_microns(zs)

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

        idx = self.send_command(move_cmd)
        self.is_moving = True
        while True:
            r = self.read_response(idx)
            if r is not None:
                break
            time.sleep(self.wait_time)
        self.is_moving = False

        return r == bytes.fromhex("0d")

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
                logger.error(f"Speed for the high-resolution mode is too fast.")
                raise UserWarning(
                    "High resolution mode of Sutter MP285 speed too "
                    "high. Setting to 1310 microns/sec."
                )
        elif resolution == "low":
            resolution_bit = 0
            if speed > 3000:
                speed = 3000
                logger.error(f"Speed for the low-resolution mode is too fast.")
                raise UserWarning(
                    "Low resolution mode of Sutter MP285 speed too "
                    "high. Setting to 3000 microns/sec."
                )
        else:
            logger.error(f"MP-285 resolution must be 'high' or 'low'")
            raise UserWarning("MP-285 resolution must be 'high' or 'low'")

        speed_and_res = int(resolution_bit * 32768 + speed)
        command = (
            bytes.fromhex("56")
            + speed_and_res.to_bytes(length=2, byteorder="little", signed=False)
            + bytes.fromhex("0d")
        )

        # Write Command and get response
        idx = self.send_command(command, 1)
        while True:
            response = self.read_response(idx)
            if response is not None:
                break
            time.sleep(self.wait_time)
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
        if not self.is_moving or self.is_interrupted:
            return True

        # send commands: interrupt and get position
        if self.serial.in_waiting == 0:
            self.is_interrupted = True
            self.write_done_flag.acquire()
            self.serial.write(bytes.fromhex("03630d"))
            logger.debug("MP285 write command 03630d")
            idx = (self.top_command_idx - 1) % self.commands_num
            self.commands_buffer[idx] = 14
            self.top_command_idx = idx
            self.write_done_flag.release()

            while True:
                position_information = self.read_response(idx)
                if position_information is not None:
                    break
                time.sleep(self.wait_time)

            if len(position_information) < 14:
                logger.error("MP285 didn't get full position information after interruption")
            self.is_interrupted = False

        return True

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
        # self.flush_buffers()
        abs_cmd = bytes.fromhex("61") + bytes.fromhex("0d")
        idx = self.send_command(abs_cmd)
        while True:
            r = self.read_response(idx)
            if r is not None:
                break
            time.sleep(self.wait_time)
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
        # self.flush_buffers()
        idx = self.send_command(bytes.fromhex("6E") + bytes.fromhex("0d"))
        while True:
            response = self.read_response(idx)
            if response is not None:
                break
            time.sleep(self.wait_time)

        return response == bytes.fromhex("0d")

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
        idx = self.send_command(bytes.fromhex("72") + bytes.fromhex("0d"))
        
        response = self.read_response(idx)
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
        # print("calling get_controller_status")
        # self.flush_buffers()
        idx = self.send_command(bytes.fromhex("73") + bytes.fromhex("0d"), response_num=33)
        response = self.read_response(idx)
        if len(response) == 33 and response[-1] == bytes.fromhex("0d"):
            command_complete = True
        else:
            command_complete = False

        # not implemented yet. See page 74 of documentation.
        return command_complete

    def close(self):
        """Close the serial connection to the stage"""
        self.serial.close()
