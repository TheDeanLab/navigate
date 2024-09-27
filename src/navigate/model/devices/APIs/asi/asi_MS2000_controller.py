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


# Standard Imports
import threading
import time
import logging

# Third Party Imports
from serial import Serial
from serial import SerialException
from serial import SerialTimeoutException
from serial import EIGHTBITS
from serial import PARITY_NONE
from serial import STOPBITS_ONE
from serial.tools import list_ports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class MS2000Exception(Exception):
    """
    Exception raised when error code from MS2000 Console is received.

    Attributes:
        - command: error code received from MS2000 Console
    """

    def __init__(self, code: str):
        """Initialize the MS2000Exception class
        Parameters
        ----------
        code : str
            Error code received from MS2000 Console
        """

        #: dict: Dictionary of error codes and their corresponding error messages
        self.error_codes = {
            ":N-1": "Unknown Command (Not Issued in MS-2000)",
            ":N-2": "Unrecognized Axis Parameter (valid axes are dependent on the "
            "controller)",
            ":N-3": "Missing parameters (command received requires an axis parameter "
            "such as x=1234)",
            ":N-4": "Parameter Out of Range",
            ":N-5": "Operation failed",
            ":N-6": "Undefined Error (command is incorrect, but the controller does "
            "not know exactly why.",
            ":N-21": "Serial Command halted by the HALT command",
        }
        #: str: Error code received from MS2000 Console
        self.code = code

        #: str: Error message
        self.message = self.error_codes[code]

        # Gets the proper message based on error code received.
        super().__init__(self.message)
        # Sends message to base exception constructor for python purposes

    def __str__(self):
        """Overrides base Exception string to be displayed
        in traceback"""
        return f"{self.code} -> {self.message}"


class MS2000Controller:
    """MS2000 Controller class"""

    def __init__(self, com_port: str, baud_rate: int, verbose: bool = False):
        """Initialize the MS2000 Controller class


        Parameters
        ----------
        com_port : str
            COM port of the MS2000 Controller
        baud_rate : int
            Baud rate of the MS2000 Controller
        verbose : bool
            If True, will print out messages to the console

        """
        #: Serial: Serial port object
        self.serial_port = Serial()

        #: str: COM port of the MS2000 Controller
        self.com_port = com_port

        #: int: Baud rate of the MS2000 Controller
        self.baud_rate = baud_rate

        #: bool: If True, will print out messages to the console
        self.verbose = verbose

        #: list[str]: Default axes sequence of the MS2000 Controller
        self.default_axes_sequence = None

        #: list[float]: Maximum speeds of the MS2000 Controller
        self._max_speeds = None

        #: threading.Event: Event to indicate if it is safe to write to the serial port
        self.safe_to_write = threading.Event()

        #: threading.Event.set(): Set the safe_to_write event
        self.safe_to_write.set()

        #: float: Last time a command was sent to the MS2000 Controller
        self._last_cmd_send_time = time.perf_counter()

    def __str__(self) -> str:
        """Returns the string representation of the MS2000 Controller class"""
        return "MS2000Controller"

    @staticmethod
    def scan_ports() -> list[str]:
        """Scans for available COM ports

        Returns a sorted list of COM ports.

        Returns
        -------
        list[str]
            Sorted list of COM ports
        """
        com_ports = [port.device for port in list_ports.comports()]
        com_ports.sort(key=lambda value: int(value[3:]))
        return com_ports

    def connect_to_serial(
        self,
        rx_size: int = 12800,
        tx_size: int = 12800,
        read_timeout: int = 1,
        write_timeout: int = 1,
    ) -> None:
        """
        Connect to the serial port.

        Parameters
        ----------
        rx_size : int
            Size of the rx buffer
        tx_size : int
            Size of the tx buffer
        read_timeout : int
            Read timeout in seconds
        write_timeout : int
            Write timeout in seconds
        """
        self.serial_port.port = self.com_port
        self.serial_port.baudrate = self.baud_rate
        self.serial_port.parity = PARITY_NONE
        self.serial_port.bytesize = EIGHTBITS
        self.serial_port.stopbits = STOPBITS_ONE
        self.serial_port.xonoff = False
        self.serial_port.rtscts = False
        self.serial_port.dsrdtr = False
        self.serial_port.write_timeout = write_timeout
        self.serial_port.timeout = read_timeout

        # set the size of the rx and tx buffers before calling open
        self.serial_port.set_buffer_size(rx_size, tx_size)
        try:
            self.serial_port.open()
        except SerialException:
            self.report_to_console(
                f"SerialException: can't connect to {self.com_port} at "
                f"{self.baud_rate}!"
            )

        if self.is_open():
            # clear the rx and tx buffers
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            # report connection status to user
            self.report_to_console("Connected to the serial port.")
            self.report_to_console(
                f"Serial port = {self.com_port} :: Baud rate = {self.baud_rate}"
            )

            #: list[str]: Default axes sequence of the MS2000 Controller
            self.default_axes_sequence = [
                "X",
                "Y",
                "Z",
            ]  # self.get_default_motor_axis_sequence()

    def get_default_motor_axis_sequence(self) -> None:
        """Get the default motor axis sequence from the ASI device

        Returns
        -------
        list[str]
            Default motor axis sequence
        """
        self.send_command("BU X")
        response = self.read_response()
        lines = response.split("\r")
        for line in lines:
            if line.startswith("Motor Axes:"):
                default_axes_sequence = line[line.index(":") + 2 :].split(" ")[:-2]
                self.report_to_console(
                    "Get the default axes sequence from the ASI device " "successfully!"
                )
                break

        return default_axes_sequence

    def set_feedback_alignment(self, axis, aa):
        """Set the stage feedback alignment.

        Parameters
        ----------
        axis : str
            Stage axis
        """
        self.send_command(f"AA {axis}={aa}\r")
        self.read_response()
        self.send_command(f"AZ {axis}\r")
        self.read_response()

    def set_backlash(self, axis, val):
        """Enable/disable stage backlash correction.

        Parameters
        ----------
        axis : str
            Stage axis
        val : float
            Distance of anti-backlash motion [mm]
        """
        self.send_command(f"B {axis}={val:.7f}\r")
        self.read_response()

    def set_finishing_accuracy(self, axis, ac):
        """Set the stage finishing accuracy.

        Parameters
        ----------
        axis : str
            Stage axis
        ac : float
            Position error [mm]
        """
        self.send_command(f"PC {axis}={ac:.7f}\r")
        self.read_response()

    def set_error(self, axis, ac):
        """
        Set the stage drift error

        Parameters
        ----------
        axis : str
            Stage axis
        ac : float
            Position error [mm]
        """
        self.send_command(f"E {axis}={ac:.7f}\r")
        self.read_response()

    def disconnect_from_serial(self) -> None:
        """Disconnect from the serial port if it's open."""
        if self.is_open():
            self.serial_port.close()
            self.report_to_console("Disconnected from the serial port.")

    def is_open(self) -> bool:
        """Returns True if the serial port exists and is open.

        Returns
        -------
        bool
            True if the serial port exists and is open
        """
        # short circuits if serial port is None
        return self.serial_port and self.serial_port.is_open

    def report_to_console(self, message: str) -> None:
        """Print message to the output device, usually the console.

        Parameters
        ----------
        message : str
            Message to print to the output device
        """
        # useful if we want to output data to something other than the console
        if self.verbose:
            print(message)

    def wait_for_device(self, report: bool = False):
        """Waits for the all motors to stop moving."""
        if not report:
            print("Waiting for device...")
        temp = self.report
        self.report = report
        busy = True
        while busy:
            busy = self.is_device_busy()
        self.report = temp

    def send_command(self, cmd: str) -> None:
        """Send a serial command to the device.

        Parameters
        ----------
        cmd : str
            Serial command to send to the device
        """
        # always reset the buffers before a new command is sent
        self.safe_to_write.wait()
        self.safe_to_write.clear()
        self.serial_port.read_all()
        self.serial_port.reset_input_buffer()
        self.serial_port.reset_output_buffer()

        # send the serial command to the controller
        self.report_to_console(cmd)
        command = bytes(f"{cmd}\r", encoding="ascii")
        try:
            self.serial_port.write(command)
        except SerialTimeoutException as e:
            print(f"MS2000 Controller -- SerialTimeoutException: {e}")
            pass

        # sleep to avoid error, empirically found this made it work
        time.sleep(0.1)

    def read_response(self) -> str:
        """Read a line from the serial response.

        Returns
        -------
        str
            Response from the serial port
        """
        response = self.serial_port.readline()
        self.safe_to_write.set()
        response = response.decode(encoding="ascii")
        # Remove leading and trailing empty spaces
        self.report_to_console(f"Received Response: {response.strip()}")
        if response.startswith(":N"):
            logger.error(f"Incorrect response received: {response}")
            raise MS2000Exception(response)

        return response  # in case we want to read the response

    def moverel(self, x: int = 0, y: int = 0, z: int = 0) -> None:
        """Move the stage with a relative move on multiple axes.

        Parameters
        ----------
        x : int
            Relative move on the x-axis
        y : int
            Relative move on the y-axis
        z : int
            Relative move on the z-axis
        """
        self.send_command(f"MOVREL X={x} Y={y} Z={z}\r")
        self.read_response()

    def moverel_axis(self, axis: str, distance: float) -> None:
        """Move the stage with a relative move on one axis

        Parameters
        ----------
        axis : str
            Stage axis
        distance : float
            Relative move distance
        """
        self.send_command(f"MOVREL {axis}={round(distance, 6)}\r")
        self.read_response()

    def move(self, pos_dict) -> None:
        """Move the stage with an absolute move on multiple axes

        Parameters
        ----------
        pos_dict : dict
            Dictionary of the form {axis: position}
        """
        pos_str = " ".join(
            [f"{axis}={round(pos, 6)}" for axis, pos in pos_dict.items()]
        )
        self.send_command(f"MOVE {pos_str}\r")
        self.read_response()

    def move_axis(self, axis: str, distance: float) -> None:
        """Move the stage with an absolute move on one axis

        Parameters
        ----------
        axis : str
            Stage axis
        distance : float
            Absolute move distance
        """
        self.send_command(f"MOVE {axis}={round(distance, 6)}\r")
        self.read_response()

    def set_max_speed(self, axis: str, speed: float) -> None:
        """Set the speed on a specific axis. Speed is in mm/s.

        Parameters
        ----------
        axis : str
            Stage axis
        speed : float
            Speed in mm/s
        """
        self.send_command("/")
        self.read_response()

        self.send_command(f"SPEED {axis}={speed}\r")
        self.read_response()

    def get_axis_position(self, axis: str) -> int:
        """Return the position of the stage in ASI units (tenths of microns).

        Parameters
        ----------
        axis : str
            Stage axis
        Returns
        -------
        int
            Position of the stage in ASI units
        """
        self.send_command(f"WHERE {axis}\r")
        response = self.read_response()
        pos = float(response.split(" ")[1])
        return pos

    def get_axis_position_um(self, axis: str) -> float:
        """Return the position of the stage in microns.

        Parameters
        ----------
        axis : str
            Stage axis
        Returns
        -------
        float
            Position of the stage in microns
        """
        self.send_command(f"WHERE {axis}\r")
        response = self.read_response()
        return float(response.split(" ")[1]) / 10.0

    def get_position(self, axes) -> dict:
        """Return current stage position in ASI units.

        If default axes sequence has gotten from the ASI device,
        then it will ask the device all the position in one command,
        else it will ask each axis position one by one.

        WATCH OUT! This will return the positions in the order
        of the underlying hardware no matter what order the axes
        are passed in.

        See https://asiimaging.com/docs/products/serial_commands#commandwhere_w

        Parameters
        ----------
        axes : list[str]
            List of axes to query

        Returns
        -------
        dictionary:
             {axis: position}
        """

        if self.default_axes_sequence:
            cmd = f"WHERE {' '.join(axes)}\r"
            self.send_command(cmd)
            response = self.read_response()

            pos = response.split(" ")
            axes_seq = list(
                filter(
                    lambda axis: axis if axis in axes else False,
                    self.default_axes_sequence,
                )
            )
            # return {axis: float(pos[1 + i]) for i, axis in enumerate(axes_seq)}
            axis_dict = {}
            for i, axis in enumerate(axes_seq):
                try:
                    axis_dict[axis] = float(pos[1 + i])
                except (ValueError, IndexError):
                    # Report position failed. Don't crash, we can try again.
                    pass
            return axis_dict

        else:
            result = {}
            for axis in axes:
                result[axis] = self.get_axis_position(axis)
            return result

    # Utility Functions

    def is_axis_busy(self, axis: str) -> bool:
        """Returns True if the axis is busy.

        Parameters
        ----------
        axis : str
            Stage axis
        Returns
        -------
        bool
            True if the axis is busy
        """
        self.send_command(f"RS {axis}?\r")
        res = self.read_response()
        return "B" in res

    def is_device_busy(self) -> bool:
        """Returns True if any axis is busy.

        Returns
        -------
        bool
            True if any axis is busy
        """
        self.send_command("/")
        res = self.read_response()
        return "B" in res

    def wait_for_device(self, timeout: float = 1.75) -> None:
        """Waits for the all motors to stop moving.

        timeout : float
            Timeout in seconds. Default is 1.75 seconds.
        """

        if self.verbose:
            print("Waiting for device...")
        busy = self.is_device_busy()
        waiting_time = 0.0

        # t_start = time.time()
        while busy:
            waiting_time += 0.001
            if waiting_time >= timeout:
                break
            time.sleep(0.001)
            busy = self.is_device_busy()

        if self.verbose:
            print(f"Waited {waiting_time:.2f} s")

    def stop(self):
        """Stop all stage movement immediately"""

        self.send_command("HALT")
        self.read_response()
        if self.verbose:
            print("ASI Stages stopped successfully")

    def set_speed(self, speed_dict):
        """Set speed

        Parameters
        ----------
        speed_dict : dict
            Dictionary of the form {axis: speed}
        """
        axes = " ".join([f"{x}={round(v, 6)}" for x, v in speed_dict.items()])
        self.send_command(f"S {axes}")
        self.read_response()

    def set_speed_as_percent_max(self, pct):
        """Set speed as a percentage of the maximum speed

        Parameters
        ----------
        pct : float
            Percentage of the maximum speed
        """
        if self.default_axes_sequence is None:
            logger.error(f"{str(self)}, Unknown default axes sequence.")
            raise MS2000Exception(
                "Unable to query system for axis sequence. Cannot set speed."
            )
        if self._max_speeds is None:
            # find the maximum speed by setting high, then sending query

            # First, set the speed crazy high
            self.send_command(
                f"SPEED {' '.join([f'{ax}=1000' for ax in self.default_axes_sequence])}\r"
            )
            self.read_response()

            # Next query the maximum speed
            self.send_command(
                f"SPEED {' '.join([f'{ax}?' for ax in self.default_axes_sequence])}\r"
            )
            res = self.read_response()
            self._max_speeds = [float(x.split("=")[1]) for x in res.split()[1:]]

        # Now set to pct of max speed
        self.send_command(
            f"SPEED {' '.join([f'{ax}={pct*speed:.7f}' for ax, speed in zip(self.default_axes_sequence, self._max_speeds)])}\r"
        )
        self.read_response()

    def get_speed(self, axis: str):
        """Get speed

        Parameters
        ----------
        axis : str
            Stage axis
        """
        self.send_command(f"SPEED {axis}?")
        response = self.read_response()
        return float(response.split("=")[1])

    def get_encoder_counts_per_mm(self, axis: str):
        """Get encoder counts pre mm of axis

        Parameters
        ----------
        axis : str
            Stage axis

        Returns
        -------
        float
            Encoder counts per mm of axis
        """

        self.send_command(f"CNTS {axis}?")
        response = self.read_response()
        return float(response.split("=")[1].split()[0])

    def scanr(
        self,
        start_position_mm: float,
        end_position_mm: float,
        enc_divide: float = 0,
        axis: str = "X",
    ):
        """Set scanr operation mode.

        Parameters
        ----------
        start_position_mm : float
            Start position in mm
        end_position_mm : float
            End position in mm
        enc_divide : float
            Encoder divide
        axis : str
            Stage axis
        """
        enc_divide_mm = self.get_encoder_counts_per_mm(axis)
        if enc_divide == 0:
            enc_divide = enc_divide_mm
        else:
            enc_divide = int(enc_divide * enc_divide_mm)

        command = (
            f"SCANR "
            f"X={round(start_position_mm, 6)} "
            f"Y={round(end_position_mm, 6)} "
            f"Z={round(enc_divide)}"
        )

        self.send_command(command)
        self.read_response()

    def scanv(
        self,
        start_position_mm: float,
        end_position_mm: float,
        number_of_lines: float,
        overshoot: float = 1.0,
        axis: str = "X",
    ):
        """Set scanv operation mode.

        Parameters
        ----------
        start_position_mm : float
            Start position in mm
        end_position_mm : float
            End position in mm
        number_of_lines : float
            Number of lines
        overshoot : float
            Overshoot
        axis : str
            Stage axis
        """
        command = (
            f"SCANV "
            f"X={round(start_position_mm, 6)} "
            f"Y={round(end_position_mm, 6)} "
            f"Z={round(number_of_lines, 6)}"
            f"F={round(overshoot, 6)}"
        )

        self.send_command(command)
        self.read_response()

    def start_scan(self, axis: str, is_single_axis_scan: bool = True):
        """
        Start scan

        Parameters
        ----------
        axis : str
            Stage axis
        is_single_axis_scan : bool
            If True, will only scan on one axis
        """
        self.send_command("SCAN")
        self.read_response()

    def stop_scan(self):
        """Stop scan."""
        self.send_command("SCAN P")
        self.read_response()

    def is_moving(self):
        """Check to see if the stage is moving.

        Sends the command / which is equivalent to STATUS

        Gets response:
        N - there are no motors running from a serial command
        B - there is a motor running from a serial command

        Returns
        -------
        response: Bool
            True if any axis is moving. False if not.
        """

        # Calculate duration of time since last command.
        time_since_last_cmd = time.perf_counter() - self._last_cmd_send_time

        # Wait 50 milliseconds before pinging controller again.
        sleep_time = 0.050 - time_since_last_cmd
        if sleep_time > 0:
            time.sleep(sleep_time)

        self.send_command("/")
        response = self.read_response().rstrip().rstrip("\r\n")
        if response == "ACK":
            self.send_command("/")
            response = self.read_response().rstrip().rstrip("\r\n")
        if response == "B":
            return True
        elif response == "N":
            return False
        else:
            print("WARNING: WAIT UNTIL DONE RECEIVED NO RESPONSE")
            return False

    def set_triggered_move(self, axis):
        """
        Set ASI to repeat the latest relative movement
        upon receiving a TTL pulse

        Parameters
        ----------
        axis : str
            Stage axis
        """
        self.send_command(f"TTL {axis}=2")
        self.read_response()
