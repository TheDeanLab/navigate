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
import time

# Third Party Imports
import serial

# Local Imports
from aslm.model.devices.stages.stage_base import StageBase
from aslm.model.devices.APIs.sutter.MP285 import MP285

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_MP285_connection(com_port, baud_rate):
    """Build SutterStage Serial Port connection

    Parameters
    ----------
    com_port : str
        COM Port for the SutterStage.
    baud_rate : int
        Baud Rate for the SutterStage.

    Returns
    -------
    serial.Serial
        Serial Port connection to the SutterStage.
    """
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
    except serial.SerialException as e:
        logger.debug(f"Sutter MP-285 - Could not establish Serial Port Connection: {e}")
        raise UserWarning(
            "Could not communicate with Sutter MP-285 via COMPORT", com_port
        )


class SutterStage(StageBase):
    """SutterStage Class for MP-285

    Parameters
    ----------
    microscope_name : str
        Name of the microscope.
    device_connection : serial.Serial
        Serial port connection to the SutterStage.
    configuration : dict
        Configuration dictionary for the SutterStage.

    Attributes
    ----------
    stage : MP285
        MP285 stage object.
    resolution : str
        Resolution of the stage.
    speed : int
        Speed of the stage.
    sutter_axes : list
        List of SutterStage axes.

    Methods
    -------
    read(num_bytes)
        Read num_bytes of bytes from the serial port.
    close()
        Set the filter wheel to the empty position and close the communication port.
    """

    def __init__(self, microscope_name, device_connection, configuration):
        super().__init__(microscope_name, device_connection, configuration)

        # Device Connection
        self.device_connection = device_connection
        self.stage = MP285(self.device_connection)

        # Default Operating Parameters
        self.stage.wait_until_done = True
        self.resolution = "high"
        self.speed = 1000  # in units microns/s.

        # Mapping from self.axes to corresponding ASI axis labelling
        axes_mapping = {"x": "X", "y": "Y", "z": "Z"}

        # Focus and Theta axes are not supported for Sutter Stage
        if "theta" in self.axes:
            self.axes.remove("theta")
        if "f" in self.axes:
            self.axes.remove("f")

        self.sutter_axes = list(map(lambda a: axes_mapping[a], self.axes))

        # Set the resolution and velocity of the stage
        response = self.stage.set_resolution_and_velocity(
            resolution=self.resolution, speed=self.speed
        )
        assert response is True, "Error setting MP-285 resolution and velocity"

        # Set the operating mode of the stage.
        response = self.stage.set_absolute_mode()
        assert response is True, "Error setting MP-285 operating mode"

        # Get the current position of the stage.
        self.x_pos = None
        self.y_pos = None
        self.z_pos = None
        self.report_position()

    def __del__(self):
        """Delete SutterStage Serial Port.

        Returns
        -------
        None

        Raises
        ------
        UserWarning
            Error while closing the SutterStage Serial Port.
        """
        try:
            self.stop()
            self.device_connection.close()
            logger.debug("MP-285 stage connection closed")
        except (AttributeError, BaseException) as e:
            print("Error while closing the MP-285 stage connection", e)
            logger.debug("Error while disconnecting the MP-285 stage", e)
            raise

    def report_position(self):
        """Reports the position for all axes, and creates a position dictionary.

        Positions from the MP-285 are converted to microns.

        Returns
        -------
        position_dict : dict
            Dictionary of positions for all axes.
        """
        for _ in range(10):
            try:
                x_pos, y_pos, z_pos = self.stage.get_current_position()
                self.x_pos = x_pos
                self.y_pos = y_pos
                self.z_pos = z_pos
                position = {"x": x_pos, "y": y_pos, "z": z_pos}
                logger.debug(f"MP-285 - Position: {position}")
                break
            except serial.SerialException as e:
                print("MP-285: Failed to report position.")
                logger.exception(f"MP-285 - Error: {e}")
                time.sleep(0.01)
        self.create_position_dict()
        return self.position_dict

    def move_absolute(self, move_dictionary, wait_until_done=True):
        """Move stage along a single axis.

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', 'x_min',
            etc. for one or more axes. Expects values in micrometers, except for theta,
            which is in degrees.
        wait_until_done : bool
            Wait until the stage has finished moving before returning.

        Returns
        -------
        bool
            Was the move successful?
        """
        self.stage.wait_until_done = wait_until_done
        for axis in self.axes:
            axis_abs = self.get_abs_position(axis, move_dictionary)
            if axis_abs == -1e50:
                return False

        # Move the stage
        try:
            x_pos = move_dictionary["x_abs"]
            y_pos = move_dictionary["y_abs"]
            z_pos = move_dictionary["z_abs"]
            self.stage.move_to_specified_position(x_pos=x_pos, y_pos=y_pos, z_pos=z_pos)
            return True
        except serial.SerialException as e:
            logger.exception(f"MP285: move_axis_absolute failed - {e}")
            return False

    def stop(self):
        """Stop all stage movement abruptly.

        Returns
        -------
        None
        """
        try:
            self.stage.interrupt_move()
        except serial.SerialException as error:
            logger.exception(f"MP-285 - Stage stop failed: {error}")
