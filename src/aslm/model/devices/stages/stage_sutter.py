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
from serial import SerialException

# Local Imports
from aslm.model.devices.stages.stage_base import StageBase
from aslm.model.devices.APIs.sutter.MP285 import MP285

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_MP285_connection(com_port, baud_rate, timeout=0.25):
    """Build SutterStage Serial Port connection

    Parameters
    ----------
    com_port : str
        COM Port for the SutterStage.
    baud_rate : int
        Baud Rate for the SutterStage.
    timeout : float
        Duration of time for timeout to be triggered (s)

    Returns
    -------
    MP285
        MP285 SutterStage.
    """
    try:
        mp285_stage = MP285(com_port, baud_rate, timeout)
        mp285_stage.connect_to_serial()
        return mp285_stage
    except SerialException as e:
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
    device_connection : MP285
        MP285 stage.
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

    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        super().__init__(microscope_name, device_connection, configuration, device_id)

        # Device Connection
        if device_connection is None:
            logger.error("The MP285 stage is unavailable!")
            raise UserWarning("The MP285 stage is unavailable!")
        
        self.stage = device_connection
        self.stage.wait_until_done = True

        # Default mapping from self.axes to corresponding MP285 axis labelling
        axes_mapping = {"x": "x", "y": "y", "z": "z"}
        if not self.axes_mapping:
            self.axes_mapping = {axis: axes_mapping[axis] for axis in self.axes if axis in axes_mapping}

        self.device_axes = dict(map(lambda v: (v[1], v[0]), self.axes_mapping.items()))

        # Default Operating Parameters
        self.resolution = "low" #"high"
        self.speed = 3000  #1300  # in units microns/s.
        self.stage_x_pos, self.stage_y_pos, self.stage_z_pos = None, None, None

        # Set the resolution and velocity of the stage
        try:
            self.stage.set_resolution_and_velocity(
                resolution=self.resolution, speed=self.speed
            )
        except Exception as e:
            logger.debug(f"Sutter MP-285 - Error setting resolution and velocity: {e}")
            raise UserWarning("Sutter MP-285 - Error setting resolution and velocity")

        # Set the operating mode of the stage.
        try:
            self.stage.set_absolute_mode()
        except Exception as e:
            logger.debug(f"Sutter MP-285 - Error setting absolute operation mode: {e}")
            raise UserWarning("Sutter MP-285 - Error setting absolute operation mode")

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
        self.close()

    def report_position(self):
        """Reports the position for all axes, and creates a position dictionary.

        Positions from the MP-285 are converted to microns.

        Returns
        -------
        position_dict : dict
            Dictionary containing the position of all axes
        """
        position = {}
        try:
            self.stage_x_pos, self.stage_y_pos, self.stage_z_pos = self.stage.get_current_position()
            for axis, hardware_axis in self.axes_mapping.items():
                hardware_position = getattr(self, f"stage_{hardware_axis}_pos")
                self.__setattr__(f"{axis}_pos", hardware_position)

            position = self.get_position_dict()
            logger.debug(f"MP-285 - Position: {position}")
        except SerialException as e:
            print("MP-285: Failed to report position: {e}")
            logger.debug(f"MP-285 - Error: {e}")
            time.sleep(0.01)

        return position
    
    def move_axis_absolute(self, axis, abs_pos, wait_until_done=False):
        """
        Implement movement logic along a single axis.

        Example calls:

        Parameters
        ----------
        axis : str
            An axis. For example, 'x', 'y', 'z', 'f', 'theta'.
        abs_pos : float
            Absolute position value
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        bool
            Was the move successful?
        """
        move_dictionary = {f"{axis}_abs": abs_pos}
        return self.move_absolute(move_dictionary, wait_until_done)

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
        pos_dict = self.verify_abs_position(move_dictionary)
        if not pos_dict:
            return False

        # rely on cached positions
        # if len(pos_dict.keys()) < 3:
        #     self.report_position()
        self.stage.wait_until_done = wait_until_done
        move_stage = {}
        for axis in pos_dict:
            if abs(getattr(self, f"stage_{self.axes_mapping[axis]}_pos") - pos_dict[axis]) < 0.02:
                move_stage[axis] = False
            else:
                move_stage[axis] = True
                setattr(self, f"stage_{self.axes_mapping[axis]}_pos", pos_dict[axis])

        move_stage = any(move_stage.values())
        if move_stage is True:
            try:
                self.stage.move_to_specified_position(
                    x_pos=self.stage_x_pos,
                    y_pos=self.stage_y_pos,
                    z_pos=self.stage_z_pos
                )
            except SerialException as e:
                logger.debug(f"MP285: move_axis_absolute failed - {e}")
                # make sure the cached positions are the "same" as device
                self.report_position()
                return False

        return True

    def stop(self):
        """Stop all stage movement abruptly.

        Returns
        -------
        None
        """
        try:
            self.stage.interrupt_move()
        except SerialException as error:
            logger.exception(f"MP-285 - Stage stop failed: {error}")

    def close(self):
        try:
            self.stop()
            self.stage.close()
            logger.debug("MP-285 stage connection closed")
        except (AttributeError, BaseException) as e:
            print("Error while closing the MP-285 stage connection", e)
            logger.debug("Error while disconnecting the MP-285 stage", e)
