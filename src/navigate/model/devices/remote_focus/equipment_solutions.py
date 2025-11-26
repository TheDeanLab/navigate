# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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


#  Standard Library Imports
import time
import serial
import logging
from typing import Any, Dict

# Third Party Imports
from navigate.tools.decorators import log_initialization

# Local Imports
from navigate.model.devices.remote_focus.ni import NIRemoteFocus
from navigate.model.devices.remote_focus.asi import ASIRemoteFocus
from navigate.model.devices.device_types import ASIDevice, SerialDevice

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class EquipmentSolutionsRemoteFocus(NIRemoteFocus, SerialDevice):
    """RemoteFocusEquipmentSolutions Class

    Note
    ----
        The SCA814 has a single character input buffer that can be overflowed if the
        proper steps are not taken. To avoid overflowing the input buffer the user
        should send a single character at a time and wait for that same character to
        be echoed back by the controller. While not necessary, it is advisable to
        verify that the character received from the controller is the same character
        sent. Once the character is received the next character can be processed.
    """

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        *args,
        **kwargs,
    ) -> None:
        """Initialize the RemoteFocusEquipmentSolutions Class

        Parameters
        ----------
        microscope_name : str
            Name of the microscope
        device_connection : Any
            Connection to the device
        configuration : Dict[str, Any]
            Configuration dictionary
        """
        super().__init__(microscope_name, device_connection, configuration)

        #: str: Name of the RS232 communication port.
        self.comport = configuration["configuration"]["microscopes"][microscope_name][
            "remote_focus"
        ]["hardware"].get("port", "COM1")

        #: float: Timeout for the serial port.
        self.timeout = 1.25

        #: bool: Read on initialization.
        self.read_on_init = True

        #: bool: Debug mode.
        self.debug = False

        # set connection
        self.serial = device_connection["connection"]
        self.daq = device_connection["daq_connection"]

        # Send command d0 and read returned information
        if self.read_on_init:
            string = b"d0\r"
            logger.debug(f"Sending command: {string}")
            try:
                self.serial.write(string)
            except serial.SerialTimeoutException as e:
                logger.error(f"Communication Error: {e}")
                raise UserWarning("RemoteFocusEquipmentSolutions Timeout Exception")

            # After write , Before read
            time.sleep(self.timeout)
            data = self.serial.readline()
            logger.debug(f"Received command: {data}")

            # Initialize Servo
            self.send_command("k0\r")  # Turn off servo
            self.send_command("k1\r")  # Engage servo
            logger.debug("Servo Engaged")

    def __del__(self):
        """Close the RemoteFocusEquipmentSolutions Class"""
        try:
            self.send_command("k0\r")
            self.serial.close()
        except Exception:
            pass

    @classmethod
    def connect(
        cls, port: str = "COM1", baudrate: int = 115200, timeout: float = 1.25
    ) -> serial.Serial:
        """Connect to Serial Communication Port
        port : str
            Serial Port (default is "COM1")
        baudrate : int, optional
            Baud rate of the serial port (default is 115200)
        timeout : float, optional
            Time out (default is 1.25)

        Returns
        -------
        serial.Serial
            An instance of the serial connection

        Raises
        ------
        UserWarning
            If there is a communication error with the serial port
        """
        # Open Serial Port
        try:
            logger.debug(f"Opening Voice Coil on COM: {port}")
            serial_connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout,
                dsrdtr=False,
                rtscts=False,
            )
            return serial_connection
        except (serial.SerialException, ValueError) as error:
            logger.error(f"Communication Error: {error}")
            raise UserWarning(
                "Could not Communicate with RemoteFocusEquipmentSolutions on COM:",
                port,
            )

    def read_bytes(self, num_bytes: int) -> bytes:
        """Read the specified number of bytes from RemoteFocusEquipmentSolutions.

        Parameters
        ----------
        num_bytes : int
            Number of bytes to receive

        Returns
        -------
        received_bytes : bytes
            Number of bytes received from the RemoteFocusEquipmentSolutions device.

        Raises
        ------
        UserWarning
            If the serial port to the RemoteFocusEquipmentSolutions is connected, but it
            isn't responding as expected.

        """
        for i in range(100):
            num_waiting = self.serial.in_waiting
            if num_waiting == num_bytes:
                break
            time.sleep(0.02)
        else:
            logger.error("Communication Error: Too many bytes waiting to be read")
            raise UserWarning(
                "The serial port to the Voice Coil is connected, but it isn't "
                "responding as expected."
            )
        received_bytes = self.serial.read(num_bytes)
        return received_bytes

    def send_command(self, message: str) -> None:
        """Send write command to the RemoteFocusEquipmentSolutions device.

        Parameters
        ----------
        message : str
            Message to send to the RemoteFocusEquipmentSolutions device. If str ==
            'close', shutdown device.

        Raises
        ------
        UserWarning
            If there is an error in communicating with the RemoteFocusEquipmentSolutions
            device.
        """
        try:
            if message == "close":
                self.close_connection()
            else:
                # Send command to device
                self.serial.write(message.encode("utf-8"))
            # Read data sent from device
            data = self.serial.read(9999)
            if len(data) > 0:
                if self.debug:
                    print("Data received: " + data.decode())
                else:
                    pass
            time.sleep(self.timeout)

        except serial.SerialException as e:
            logger.error(f"Communication Error: {e}")
            raise UserWarning(
                "Error in communicating with Voice Coil via COMPORT", self.comport
            )


class EquipmentSolutionsASIRemoteFocus(ASIRemoteFocus, SerialDevice, ASIDevice):
    """ASIRemoteFocusEquipmentSolutions Class

    Note
    ----
        The SCA814 has a single character input buffer that can be overflowed if the
        proper steps are not taken. To avoid overflowing the input buffer the user
        should send a single character at a time and wait for that same character to
        be echoed back by the controller. While not necessary, it is advisable to
        verify that the character received from the controller is the same character
        sent. Once the character is received the next character can be processed.
    """

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
        *args,
        **kwargs,
    ) -> None:
        """Initialize the RemoteFocusEquipmentSolutions Class

        Parameters
        ----------
        microscope_name : str
            Name of the microscope
        device_connection : Any
            Connection to the device
        configuration : Dict[str, Any]
            Configuration dictionary
        """
        super().__init__(microscope_name, device_connection, configuration)

        #: str: Name of the RS232 communication port.
        self.comport = configuration["configuration"]["microscopes"][microscope_name][
            "remote_focus"
        ]["hardware"].get("port", "COM1")

        #: float: Timeout for the serial port.
        self.timeout = 1.25

        #: bool: Read on initialization.
        self.read_on_init = True

        #: bool: Debug mode.
        self.debug = False

        # set connection
        self.serial = device_connection["connection"]
        self.remote_focus = device_connection["asi_connection"].daq

        # Send command d0 and read returned information
        if self.read_on_init:
            string = b"d0\r"
            logger.debug(f"Sending command: {string}")
            try:
                self.serial.write(string)
            except serial.SerialTimeoutException as e:
                logger.error(f"Communication Error: {e}")
                raise UserWarning("RemoteFocusEquipmentSolutions Timeout Exception")

            # After write , Before read
            time.sleep(self.timeout)
            data = self.serial.readline()
            logger.debug(f"Received command: {data}")

            # Initialize Servo
            self.send_command("k0\r")  # Turn off servo
            self.send_command("k1\r")  # Engage servo
            logger.debug("Servo Engaged")

    def __del__(self):
        """Close the RemoteFocusEquipmentSolutions Class"""
        try:
            self.send_command("k0\r")
            self.serial.close()
        except Exception:
            pass

    @classmethod
    def connect(cls, port: str="COM1", baudrate: int=115200, timeout: float=1.25) -> serial.Serial:
        """Connect to Serial Communication Port
        port : str
            Serial Port (default is "COM1")
        baudrate : int, optional
            Baud rate of the serial port (default is 115200)
        timeout : float, optional
            Time out (default is 1.25)

        Returns
        -------
        serial.Serial
            An instance of the serial connection

        Raises
        ------
        UserWarning
            If there is a communication error with the serial port
        """
        # Open Serial Port
        try:
            logger.debug(f"Opening Voice Coil on COM: {port}")
            serial_connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout,
                dsrdtr=False,
                rtscts=False,
            )
            return serial_connection
        except (serial.SerialException, ValueError) as error:
            logger.error(f"Communication Error: {error}")
            raise UserWarning(
                "Could not Communicate with RemoteFocusEquipmentSolutions on COM:",
                port,
            )

    def read_bytes(self, num_bytes: int) -> bytes:
        """Read the specified number of bytes from RemoteFocusEquipmentSolutions.

        Parameters
        ----------
        num_bytes : int
            Number of bytes to receive

        Returns
        -------
        received_bytes : bytes
            Number of bytes received from the RemoteFocusEquipmentSolutions device.

        Raises
        ------
        UserWarning
            If the serial port to the RemoteFocusEquipmentSolutions is connected, but it
            isn't responding as expected.

        """
        for i in range(100):
            num_waiting = self.serial.in_waiting
            if num_waiting == num_bytes:
                break
            time.sleep(0.02)
        else:
            logger.error("Communication Error: Too many bytes waiting to be read")
            raise UserWarning(
                "The serial port to the Voice Coil is connected, but it isn't "
                "responding as expected."
            )
        received_bytes = self.serial.read(num_bytes)
        return received_bytes

    def send_command(self, message: str):
        """Send write command to the RemoteFocusEquipmentSolutions device.

        Parameters
        ----------
        message : str
            Message to send to the RemoteFocusEquipmentSolutions device. If str ==
            'close', shutdown device.

        Raises
        ------
        UserWarning
            If there is an error in communicating with the RemoteFocusEquipmentSolutions
            device.
        """
        try:
            if message == "close":
                self.close_connection()
            else:
                # Send command to device
                self.serial.write(message.encode("utf-8"))
            # Read data sent from device
            data = self.serial.read(9999)
            if len(data) > 0:
                if self.debug:
                    print("Data received: " + data.decode())
                else:
                    pass
            time.sleep(self.timeout)

        except serial.SerialException as e:
            logger.error(f"Communication Error: {e}")
            raise UserWarning(
                "Error in communicating with Voice Coil via COMPORT", self.comport
            )



if __name__ == "__main__":
    vc = RemoteFocusEquipmentSolutions()
    vc.send_command("k0\r")  # Turn off servo
    vc.send_command("k1\r")  # Engage servo

