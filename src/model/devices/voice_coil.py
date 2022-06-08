"""
ASLM Voice Coil Model.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

#  Standard Library Imports
import logging
import time
import serial


# # Logger Setup
# p = __name__.split(".")[0]
# logger = logging.getLogger(p)


class VoiceCoil:
    """
    The SCA814 has a single character input buffer that can be overflowed if the proper steps are not taken.
    To avoid overflowing the input buffer the user should send a single character at a time and wait for that
    same character to be echoed back by the controller. While not necessary, it is advisable to verify that the
    character received from the controller is the same character sent. Once the character is received the next
    character can be processed.
    """

    def __init__(self, verbose):
        self.comport = 'COM1'
        self.baudrate = 115200
        self.bytesize = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopBits = serial.STOPBITS_ONE
        self.timeout = 1.25
        self.verbose = verbose
        self.init_finished = False
        self.read_on_init = True

        # Open Serial Port
        # https://pyserial.readthedocs.io/en/latest/pyserial_api.html
        try:
            if self.verbose:
                print("Opening Voice Coil on COM:", self.comport)
            self.serial = serial.Serial(port=self.comport,
                                 baudrate=self.baudrate,
                                 bytesize=self.bytesize,
                                 parity=self.parity,
                                 stopbits=self.stopBits,
                                 timeout=self.timeout,
                                 dsrdtr=False,
                                 rtscts=False)
        except (serial.SerialException, ValueError) as error:
            print(error)
            raise UserWarning("Could not Communicate with Voice Coil on COM:", self.comport)

        # Send command d0 and read returned information
        if self.read_on_init:
            string = b'd0\r'  # Can also use str.encode()
            if self.verbose:
                print("Before Write")
                print("Bytes in Input Buffer: ", self.serial.in_waiting)
                print("Bytes in Output Buffer: ", self.serial.out_waiting)
                print("Sending Command to the voice coil:", string)

            try:
                hold = self.serial.write(string)
                if self.verbose:
                    print("Number of Bytes Sent: ", hold)
            except serial.SerialTimeoutException as e:
                print(e)

            # After write , Before read
            if self.verbose:
                print("After Write, Before Read")
                print("Bytes in Input Buffer: ", self.serial.in_waiting)
                print("Bytes in Output Buffer: ", self.serial.out_waiting)

            time.sleep(2.0)

            data = self.serial.readline()
            if self.verbose:
                print(data)
                print("After Read")
                print("Bytes in Input Buffer: ", self.serial.in_waiting)
                print("Bytes in Output Buffer: ", self.serial.out_waiting)


            if len(data) > 0:
               print("Data received: " + data.decode())
            else:
               print("Nothing received from", string)


    def __del__(self):
        self.serial.close()

    def read_bytes(self, num_bytes):
        """
        Reads the specified number of bytes from the serial port.
        """
        for i in range(100):
            num_waiting = self.serial.inWaiting()
            if num_waiting == num_bytes:
                break
            time.sleep(0.02)
        else:
            raise UserWarning(
                "The serial port to the Voice Coil is on, but it isn't responding as expected.")
        return self.serial.read(num_bytes)

    def send_command(self, msg):
        """
        Function to Write Commands to the Device
        """
        try:

            # Close Connection with Device
            if msg == "close":
                self.close_connection()
            else:
                # Send command to device
                self.serial.write(bytes.fromhex(msg))

            # Read data sent from device
            data = self.serial.read(9999)
            if len(data) > 0:
                print("Data received: " + data.decode())
            time.sleep(self.timeout)

        except serial.SerialException:
            raise UserWarning('Error in communicating with Voice Coil via COMPORT', self.comport)

    def close_connection(self):
        """
        Function to close the connection of the Voice Coil
        """
        self.serial.close()


if __name__ == "__main__":
    
    #Open and close the connection
    vc = VoiceCoil(verbose=True)
    vc.send_command('k0\r')  # Turn off servo
    vc.send_command('k1\r')  # Engage servo

