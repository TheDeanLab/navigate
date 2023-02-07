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
from aslm.model.devices.remote_focus.remote_focus_base import RemoteFocusBase

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class RemoteFocusEquipmentSolutions(RemoteFocusBase):
    """RemoteFocusEquipmentSolutions Class

    The SCA814 has a single character input buffer that can be overflowed if the proper
    steps are not taken. To avoid overflowing the input buffer the user should send a
    single character at a time and wait for that same character to be echoed back by the
    controller. While not necessary, it is advisable to verify that the character
    received from the controller is the same character sent. Once the character is
    received the next character can be processed. Uses pyserial:
    https://pyserial.readthedocs.io/en/latest/pyserial_api.html

    Parameters
    ----------
    comport : str
        COM port to connect to the RemoteFocusEquipmentSolutions device.
    baudrate : int
        Baudrate to connect to the RemoteFocusEquipmentSolutions device.
    timeout : float
        Timeout to connect to the RemoteFocusEquipmentSolutions device.
    debug : bool
        Debug mode for the RemoteFocusEquipmentSolutions device.

    Attributes
    ----------
    comport : str
        COM port for communicating with the voice coil
    baud_rate : int
        Baud rate for communicating with the voice coil
    byte_size : Other
        Number of data bits
    parity : Other
        Enable parity checking
    stop_bits : Other
        Number of stop bits.
    timeout : float
        Timeout duration.
    read_on_init : bool
        Establish connection upon initialization.
    debug : bool
        Debugging mode.  Prints statements for debugging.

    Methods
    -------
    read_bytes()
        Read bytes from the RemoteFocusEquipmentSolutions device.
    send_command()
        Send command to the RemoteFocusEquipmentSolutions device.
    close_connection()
        Close connection with the RemoteFocusEquipmentSolutions device.
    """

    def __init__(self):
        self.comport = "COM1"
        self.baud_rate = 115200
        self.byte_size = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stop_bits = serial.STOPBITS_ONE
        self.timeout = 1.25
        self.read_on_init = True
        self.debug = False

        # Open Serial Port
        try:
            logger.debug(
                f"RemoteFocusEquipmentSolutions - Opening Voice Coil on COM: "
                f"{self.comport}"
            )
            self.serial = serial.Serial(
                port=self.comport,
                baudrate=self.baud_rate,
                bytesize=self.byte_size,
                parity=self.parity,
                stopbits=self.stop_bits,
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
            string = b"d0\r"  # Can also use str.encode()
            if self.debug:
                print("RemoteFocusEquipmentSolutions - Before Write")
                print(
                    "RemoteFocusEquipmentSolutions - Bytes in Input Buffer: ",
                    self.serial.in_waiting,
                )
                print(
                    "RemoteFocusEquipmentSolutions - Bytes in Output Buffer: ",
                    self.serial.out_waiting,
                )
                print(
                    "RemoteFocusEquipmentSolutions - "
                    "Sending Command to the voice coil:",
                    string,
                )
            logger.debug(f"RemoteFocusEquipmentSolutions - Sending command: {string}")
            try:
                self.serial.write(string)
            except serial.SerialTimeoutException as e:
                logger.debug(f"RemoteFocusEquipmentSolutions - Error: {e}")
                raise UserWarning("RemoteFocusEquipmentSolutions Timeout Exception")

            # After write , Before read
            if self.debug:
                print("RemoteFocusEquipmentSolutions - After Write, Before Read")
                print(
                    "RemoteFocusEquipmentSolutions - Bytes in Input Buffer: ",
                    self.serial.in_waiting,
                )
                print(
                    "RemoteFocusEquipmentSolutions - Bytes in Output Buffer: ",
                    self.serial.out_waiting,
                )

            time.sleep(self.timeout)
            data = self.serial.readline()
            if self.debug:
                print("RemoteFocusEquipmentSolutions - After Read")
                print("RemoteFocusEquipmentSolutions - Raw Data Received:", data)
                print(
                    "RemoteFocusEquipmentSolutions - Bytes in Input Buffer: ",
                    self.serial.in_waiting,
                )
                print(
                    "RemoteFocusEquipmentSolutions - Bytes in Output Buffer: ",
                    self.serial.out_waiting,
                )
                if len(data) > 0:
                    print(
                        "RemoteFocusEquipmentSolutions - Encoded Data received: "
                        + data.decode()
                    )
                else:
                    print(
                        "RemoteFocusEquipmentSolutions - Nothing received from", string
                    )

    def __del__(self):
        """Close the RemoteFocusEquipmentSolutions Class"""
        logger.debug("Closing RemoteFocusEquipmentSolutions Serial Port")
        self.serial.close()

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

        Examples
        --------
        >>> read_bytes(1)

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

        Returns
        -------
        None

        Examples
        --------
        >>> remote_focus_equipment_solutions.send_command('d0')
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

        except serial.SerialException:
            raise UserWarning(
                "Error in communicating with Voice Coil via COMPORT", self.comport
            )

    def close_connection(self):
        """Close RemoteFocusEquipmentSolutions class

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> remote_focus_equipment_solutions.close_connection()
        """
        self.serial.close()


if __name__ == "__main__":
    vc = RemoteFocusEquipmentSolutions()
    vc.send_command("k0\r")  # Turn off servo
    vc.send_command("k1\r")  # Engage servo
