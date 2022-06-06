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
    def __init__(self, verbose):
        self.comport = 'COM1'
        self.baudrate = 115200
        self.bytesize = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopBits = serial.STOPBITS_ONE
        self.flowControl = None  # Not implemented yet.
        self.xonxoff = False
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
                                 timeout=self.timeout)
        except serial.SerialException:
            raise UserWarning("Could not Communicate with Voice Coil on COM:", self.comport)

        """
        The SCA814 has a single character input buffer that can be overflowed if the proper steps are not taken.
        To avoid overflowing the input buffer the user should send a single character at a time and wait for that
        same character to be echoed back by the controller. While not necessary, it is advisable to verify that the
        character received from the controller is the same character sent. Once the character is received the next
        character can be processed.
        """
        # Send command d0 and read returned information
        if self.read_on_init:
            if self.verbose:
                print("Sending Command d0 to the voice coil.")
            
            command = b'd0'
            print("Command Sent in Bytes:", command)
            time.sleep(2)
            self.serial.write(command)
            time.sleep(2)
            self.serial.write(b'\r')
            data = self.serial.read(9999)

            if len(data) > 0:
                print("Data received: " + data)
            else:
                print("Nothing received from", command)

            # return_byte = self.read_bytes(1)
            # if return_byte == bytes.fromhex('d0'):
            #     # Write octal literal for carriage return - 15
            #     self.serial.write(15)
            #     self.init_finished = True
            #     if self.verbose:
            #         print("Done Initializing the voice coil")

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
            if (msg == "close"):
                self.close_connection()
            else:
                # Send command to device
                self.serial.write(bytes.fromhex(msg))

            # Read data sent from device
            data = self.serial.read(9999)
            if len(data) > 0:
                print("Data received: " + data)
            time.sleep(self.timeout)

        except serial.SerialException:
            raise UserWarning('Error in communicating with Voice Coil via COMPORT', self.comport)

    # Function to close connection with device
    def close_connection(self):
        self.serial.close()


if __name__ == "__main__":
    vc = VoiceCoil(verbose=True)
    vc.send_command('k0')  # Turn off servo
    vc.send_command('k1')  # Engage servo
    vc.close_connection()

  # def openConnection():
    #     try:
    #         if VoiceCoil.verbose:
    #             print('Connecting to Voice Coil on Serial Port', VoiceCoil.comport)
    #
    #         # Send "d0" as initial command to device
    #         VoiceCoil.sendmsg("d0".encode('utf-8'))
    #
    #         # Read data sent from device
    #         data = VoiceCoil.ser.read(9999)
    #         if len(data) > 0:
    #             print("Data received: " + data)
    #         time.sleep(.5)
    #
    #     except serial.SerialException:
    #         raise UserWarning('Could not communicate with Voice Coil via COMPORT', VoiceCoil.comport)
    #