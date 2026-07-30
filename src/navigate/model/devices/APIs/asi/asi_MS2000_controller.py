# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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
import platform
import time
import logging

# Third Party Imports
from serial import SerialException
from serial import SerialTimeoutException
from serial import EIGHTBITS
from serial import PARITY_NONE
from serial import STOPBITS_ONE

# Local Imports
from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class MS2000Controller(TigerController):
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
        super().__init__(com_port, baud_rate, verbose)

    def __str__(self) -> str:
        """Returns the string representation of the MS2000 Controller class"""
        return "MS2000Controller"

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
        self.serial.port = self.com_port
        self.serial.baudrate = self.baud_rate
        self.serial.parity = PARITY_NONE
        self.serial.bytesize = EIGHTBITS
        self.serial.stopbits = STOPBITS_ONE
        self.serial.xonoff = False
        self.serial.rtscts = False
        self.serial.dsrdtr = False
        self.serial.write_timeout = write_timeout
        self.serial.timeout = read_timeout

        # set_buffer_size is only available/reliable on some platforms
        if platform.system() == "Windows" and hasattr(self.serial, "set_buffer_size"):
            try:
                self.serial.set_buffer_size(rx_size, tx_size)
            except Exception as e:
                logger.debug(f"Unable to set serial buffer size on Windows: {e}")
        try:
            self.serial.open()
        except SerialException:
            self.report_to_console(
                f"SerialException: can't connect to {self.com_port} at "
                f"{self.baud_rate}!"
            )

        if self.is_open():
            # clear the rx and tx buffers
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
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
        self.serial.read_all()
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

        # send the serial command to the controller
        self.report_to_console(cmd)
        command = bytes(f"{cmd}\r", encoding="ascii")
        try:
            self.serial.write(command)
        except SerialTimeoutException as e:
            print(f"MS2000 Controller -- SerialTimeoutException: {e}")
            pass

        # sleep to avoid error, empirically found this made it work
        time.sleep(0.1)

    def set_jog_speed(self, axes: list, jsspd: int):
        """Set jog wheel speed.

        Parameters
        ----------
        axes: list
            List of axes to set
        jsspd: int
            Jog wheel speed (0.1 - 100)
        """
        cmd = "JSSPD " + " ".join(f"{ax.upper()}={jsspd}" for ax in axes)

        # send JSSPD command to MS2000 controller: set jog wheel speed
        self.send_command(cmd)

        # get response (:A if successful)
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

    # Utility Functions

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
