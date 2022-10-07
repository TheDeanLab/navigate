"""
ASLM stage communication classes.
Class for mixed digital and analog modulation of laser devices.
Goal is to set the DC value of the laser intensity with the analog voltage, and then rapidly turn it on and off
with the digital signal.

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

# Standard Imports
import logging
import time
from enum import IntEnum

# Third Party Imports
import serial

# Local Imports
from aslm.model.devices.stages.stage_base import StageBase

# Logger Setup
# p = __name__.split(".")[1]
# logger = logging.getLogger(p)


class ASIStageScanMode(IntEnum):
    """
    0 for raster, 1 for serpentine
    """

    RASTER = 0
    SERPENTINE = 1


class ASIStageException(Exception):
    pass

class ASIStage:
    def __init__(self):
        # super().__init__(microscope_name, device_connection, configuration, device_id)

        #self.com_port = com_port if com_port else "COM7"
        self.com_port = "COM7"
        self.serial_connection = serial.Serial()
        self.serial_connection.port = self.com_port
        self.serial_connection.baudrate = 115200
        self.serial_connection.parity = serial.PARITY_NONE
        self.serial_connection.bytesize = serial.EIGHTBITS
        self.serial_connection.stopbits = serial.STOPBITS_ONE
        self.serial_connection.xonoff = False
        self.serial_connection.rtscts = False
        self.serial_connection.dsrdtr = False
        self.serial_connection.write_timeout = 1
        self.serial_connection.timeout = 1

        self.serial_connection.set_buffer_size(12800, 12800)
        self.serial_connection.open()

        if self.serial_connection.is_open:
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()

        print(self.serial_connection.name)

    def __del__(self):
        self.serial_connection.close()


    def report_position(self):
        """
        # Reports the position of the stage for all axes, and creates the hardware
        # position dictionary.
        """
        pass

    def move_axis_absolute(self, axis, axis_num, move_dictionary):
        """
        Implement movement logic along a single axis.

        To move relative, self.pidevice.MVR({1: x_rel}).

        Example calls:

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary. For example, axis='x' corresponds to 'x_abs', 'x_min', etc.
        axis_num : int
            The corresponding number of this axis on a PI stage.
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', 'x_min', etc. for one or more axes.
            Expects values in micrometers, except for theta, which is in degrees.

        Returns
        -------
        bool
            Was the move successful?
        """
        pass

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """
        # ASI move absolute method.
        # XYZF Values are converted to millimeters for PI API.
        # Theta Values are not converted.

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for one or more axes.
            Expects values in micrometers, except for theta, which is in degrees.
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        success : bool
            Was the move successful?
        """

        pass

    def stop(self):
        pass

    def zero_axes(self, list):
        pass

    def unzero_axes(self, list):
        pass

    def load_sample(self):
        pass

    def unload_sample(self):
        pass

    def _send_message(self, message: str):
        """
        Send message over serial connection.
        """
        self.serial_connection.write(bytes(f"{message}\r", encoding="ascii"))

    def _read_response(self) -> str:
        """
        Receive and read the response from serial communication.
        """
        return self.serial_connection.readline().decode(encoding="ascii")

    def execute_message(self, message: str):
        """
        Sends a message and reads and prints and returns the response.
        
        Parameters
        ----------
        message : str
        Returns
        -------
        str
        """
        self._send_message(message)
        response = self._read_response()
        print(response)
        return response

    def set_speed_x(self, speed):
        """
        Set speed of the stage.
        
        Parameters
        ----------
        speed
        """
        message = f"SPEED x={speed}"
        print("set speed to scan: " + message)
        self.execute_message(message)

    def set_speed_y(self, speed):
        """
        Set speed of the stage.
        
        Parameters
        ----------
        speed
        """
        message = f"SPEED y={speed}"
        print("set speed to scan: " + message)
        self.execute_message(message)

    def set_default_speed_xy(self):
        """
        Set the default speed as the stage speed.
        Currently default values are x=10 y=10.
        """
        message = "SPEED x=10 y=10"
        print("set speed to scan: " + message)
        self.execute_message(message)

    def set_backlash(self):
        """
        Set backlash on the stage.
        """
        message = "BACKLASH x=0.04 y=0.0"
        print("set backlash: " + message)
        self.execute_message(message)

    def set_scan_mode(self, mode: ASIStageScanMode = ASIStageScanMode.RASTER):
        """
        Method to set scan mode.
        
        Parameters
        ----------
        mode : ASIStageScanMode
        """
        message = f"SCAN f={int(mode)}"
        self.execute_message(message)

    def zero(self):
        """
        Set current position to zero.
        """
        message = "ZERO\r"
        self.execute_message(message)

    def start_scan(self):
        """
        Start the stage scan
        """
        message = "SCAN\r"
        self.execute_message(message)

    def scanr(self, x=0, y=0):
        """
        Set scan raster scan start and stop.
        
        Parameters
        ----------
        x
        y
        """
        message = f"SCANR x={x} y={y}"
        self.execute_message(message)

    def scanv(self, x=0, y=0, f=1.0):
        """
        Set vertical scan.
        
        Parameters
        ----------
        x
        y
        f
        Returns
        -------
        """
        message = f"SCANV x={x} y={y} f={f}"
        self.execute_message(message)

    def info(self, axis_letter):
        """
        Method to fetch various information on stage axes.
        
        Parameters
        ----------
        axis_letter : str
            Single letter, can be 'X' or 'Y' with XY stage.
        """
        message = f"INFO {axis_letter}"
        self._send_message(message)

        # Read and parse the response in the specific required way
        lines = self.serial_connection.readlines()[1].split(bytes('\r', encoding="ascii"))
        response = "\n".join([line.decode() for line in lines])
        print(response)

if __name__ == "__main__":
    stage = ASIStage()
    print("Connected to the ASI Stage!")
    # stage.info(axis_letter='X')
    stage.__del__
    print("Closed connection!")
