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
#

#  Standard Library Imports
import time
import serial
import logging

# Third Party Imports

# Local Imports
from navigate.model.devices.remote_focus.ni import RemoteFocusNI

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class RemoteFocusEquipmentSolutions(RemoteFocusNI):
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

    def __init__(self, microscope_name, device_connection, configuration):
        """Initialize the RemoteFocusEquipmentSolutions Class

        Parameters
        ----------
        microscope_name : str
            Name of the microscope
        device_connection : str
            Name of the device connection
        configuration : dict
            Configuration dictionary
        """
        super().__init__(microscope_name, device_connection, configuration)

        #: str: Name of the RS232 communication port.
        self.comport = configuration["configuration"]["microscopes"][microscope_name][
            "remote_focus_device"
        ]["hardware"].get("port", "COM1")

        #: float: Timeout for the serial port.
        self.timeout = 1.25

        #: bool: Read on initialization.
        self.read_on_init = True

        # Open Serial Port
        try:
            logger.debug(
                f"RemoteFocusEquipmentSolutions - Opening Voice Coil on COM: "
                f"{self.comport}"
            )
            self.serial = serial.Serial(
                port=self.comport,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                dsrdtr=False,
                rtscts=False,
            )

        except (serial.SerialException, ValueError) as error:
            logger.debug(f"RemoteFocusEquipmentSolutions - Error: {error}")
            raise UserWarning(
                "Could not Communicate with RemoteFocusEquipmentSolutions on COM:",
                self.comport,
            )

        # Send command d0 and read returned information
        if self.read_on_init:
            string = b"d0\r"
            logger.debug(f"RemoteFocusEquipmentSolutions - Sending command: {string}")
            try:
                self.serial.write(string)
            except serial.SerialTimeoutException as e:
                logger.debug(f"RemoteFocusEquipmentSolutions - Error: {e}")
                raise UserWarning("RemoteFocusEquipmentSolutions Timeout Exception")

            data = self.serial.readline()
            logger.debug(f"RemoteFocusEquipmentSolutions - Received command: {data}")

            # Initialize Servo
            self.send_command("k0\r")  # Turn off servo
            self.send_command("k1\r")  # Engage servo
            logger.debug("RemoteFocusEquipmentSolutions - Servo Engaged")

    def __del__(self):
        """Close the RemoteFocusEquipmentSolutions Class"""
        self.serial.close()
        super().__del__()

    def read_bytes(self, num_bytes):
        """Read the specified number of bytes from RemoteFocusEquipmentSolutions.

        Parameters
        ----------
        num_bytes : int
            Number of bytes to receive

        Returns
        -------
        received_bytes : bytearray
            Number of bytes received from the RemoteFocusEquipmentSolutions device.

        Raises
        ------
        UserWarning
            If the serial port to the RemoteFocusEquipmentSolutions is connected, but it
            isn't responding as expected.

        """
        for i in range(100):
            num_waiting = self.serial.inWaiting()
            if num_waiting == num_bytes:
                break
            time.sleep(0.02)
        else:
            logger.debug(
                "The serial port to the RemoteFocusEquipmentSolutions is connected, "
                "but it isn't responding as expected."
            )
            raise UserWarning(
                "The serial port to the Voice Coil is connected, but it isn't "
                "responding as expected."
            )
        received_bytes = self.serial.read(num_bytes)
        return received_bytes

    def send_command(self, message):
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
            self.serial.write(message.encode("utf-8"))
            data = self.serial.read(9999)
            if len(data) > 0:
                pass
            time.sleep(0.02)

        except serial.SerialException:
            raise UserWarning(
                "Error in communicating with Voice Coil via COMPORT", self.comport
            )
