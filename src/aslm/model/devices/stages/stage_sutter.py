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

# Standard Imports
import logging

# Third Party Imports
import serial

# Local Imports
from aslm.model.devices.stages.stage_base import StageBase
from aslm.model.devices.APIs.sutter.MP285 import MP285

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_sutter_stage_connection(com_port, baud_rate):
    """Build SutterStage Serial Port connection

    Attributes
    ----------
    comport : str
        Comport for communicating with the filter wheel, e.g., COM1.
    baudrate : int
        Baud rate for communicating with the filter wheel, e.g., 9600.
    """
    logging.debug(f"SutterStage - Opening Serial Port {com_port}")
    try:
        return serial.Serial(
            port=com_port,
            baudrate=baud_rate,
            timeout=0.25,
            parity=serial.PARITY_NONE,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=False,
        )
    except serial.SerialException:
        logger.warning("SutterStage - Could not establish Serial Port Connection")
        raise UserWarning(
            "Could not communicate with Sutter MP-285 via COMPORT", com_port
        )


class SutterStage(StageBase):
    """SutterStage Class for MP-285 Stage

    Attributes
    ----------
    microscope_name : str
        Name of the microscope.
    device_connection : serial.Serial
        Serial port connection to the SutterStage.
    configuration : dict
        Configuration dictionary for the SutterStage.
    device_id : int
        Device ID for the SutterStage.

    Attributes
    ----------
    stage : MP285
        MP285 stage object.
    resolution : str
        Resolution of the stage.
    speed : int
        Speed of the stage.
    sutter_axes : list
        List of axes supported by the SutterStage.


    Methods
    -------
    read(num_bytes)
        Read num_bytes of bytes from the serial port.
    close()
        Set the filter wheel to the empty position and close the communication port.
    """

    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        super().__init__(microscope_name, device_connection, configuration, device_id)
        self.device_connection = device_connection
        self.stage = MP285(self.device_connection)
        self.stage.wait_until_done = True
        self.resolution = "high"
        self.speed = 1000  # in units microns/s.

        # Set the resolution and velocity of the stage
        response = self.stage.set_resolution_and_velocity(
            resolution=self.resolution, speed=self.speed
        )
        assert response is True, "Error setting MP-285 resolution and velocity"

        # Set the operating mode of the stage.
        response = self.stage.set_absolute_mode()
        assert response is True, "Error setting MP-285 operating mode"

        # Mapping from self.axes to corresponding ASI axis labelling
        axes_mapping = {"x": "X", "y": "Y", "z": "Z"}

        # Focus and Theta axes are not supported for Sutter Stage
        if "theta" in self.axes:
            self.axes.remove("theta")
        if "f" in self.axes:
            self.axes.remove("f")

        self.sutter_axes = list(map(lambda a: axes_mapping[a], self.axes))

    def __del__(self):
        """Delete SutterStage Serial Port."""
        try:
            self.close()
            logger.debug("MP-285 stage connection closed")
        except (AttributeError, BaseException) as e:
            logger.debug("Error while disconnecting the MP-285 stage", e)

    def __exit__(self, type, value, traceback):
        """Releases the SutterStage resources"""
        try:
            self.close()
        except (AttributeError, BaseException) as e:
            logger.debug("Error while disconnecting the MP-285 stage", e)

    def close(self):
        """Close the SutterStage serial port."""
        logger.debug("SutterStage - Closing Serial Port")
        self.device_connection.close()

    def report_position(self):
        """
        Reports the position of the stage for all axes in microns
        """

        try:
            position = self.stage.get_position()
            logger.debug(f"MP-285 - Position: {position}")
            return position
        except serial.SerialException as error:
            logger.debug(f"MP-285 - Error: {error}")
            raise UserWarning("Communication error with MP-285 Stage")

    def move_absolute(self, move_dictionary):
        """Move the stage to the absolute position specified in move_dictionary

        Returns
        -------
        bool
            Was the move successful?
        """
        try:
            # position = move_dictionary[axis]
            # logger.debug(f"MP-285 - Moving {axis} to {position}")
            # response = self.stage.move_axis_absolute(axis_num, position)
            # assert response is True, f"Error moving {axis} to {position}"
            # return True
            pass
        except serial.SerialException as error:
            logger.debug(f"MP-285 - Error: {error}")
            raise UserWarning("Communication error with MP-285 Stage")
