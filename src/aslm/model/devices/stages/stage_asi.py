# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
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

# Local Imports
from aslm.model.devices.stages.stage_base import StageBase
from aslm.model.devices.APIs.asi.asi_tiger_controller import (
    TigerController,
    TigerException,
)

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_ASI_Stage_connection(com_port, baud_rate, timeout=1000):
    """Connect to the ASI Stage

    Parameters
    ----------
    com_port : str
        Communication port for ASI Tiger Controller - e.g., COM1
    baud_rate : int
        Baud rate for ASI Tiger Controller - e.g., 9600
    timeout: int
        Time to wait for stage in milliseconds.

    Returns
    -------
    asi_stage : object
        Successfully initialized stage object.
    """

    # wait until ASI device is ready
    block_flag = True
    wait_start = time.time()
    timeout_s = timeout / 1000
    while block_flag:
        asi_stage = TigerController(com_port, baud_rate, verbose=True)
        asi_stage.connect_to_serial()
        if asi_stage.is_open():
            block_flag = False
        else:
            print("Trying to connect to the ASI Stage again")
            elapsed = time.time()
            if (elapsed - wait_start) > timeout_s:
                break
            time.sleep(0.1)

    return asi_stage


class ASIStage(StageBase):
    """ASIStage Class

    Detailed documentation: http://asiimaging.com/docs/products/serial_commands
    Quick Start Guide: http://asiimaging.com/docs/command_quick_start

    Stage API provides all distances in a 10th of a micron unit.  To convert to microns,
    requires division by factor of 10 to get to micron units...

    NOTE: Do not ever change the F axis. This will alter the relative position of each
    FTP stilt, adding strain to the system. Only move the Z axis, which will change both
    stilt positions simultaneously.

         Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : object
            Hardware device to connect to
        configuration : multiprocessing.managers.DictProxy
            Global configuration of the microscope

        Attributes
        -----------
        x_pos : float
            True x position
        y_pos : float
            True y position
        z_pos : float
            True z position
        f_pos : float
            True focus position
        theta_pos : float
            True rotation position
        position_dict : dict
            Dictionary of true stage positions
        x_max : float
            Max x position
        y_max : float
            Max y position
        z_max : float
            Max y position
        f_max : float
            Max focus position
        theta_max : float
            Max rotation position
        x_min : float
            Min x position
        y_min : float
            Min y position
        z_min : float
            Min y position
        f_min : float
            Min focus position
        theta_min : float
            Min rotation position
        default_speed: float
            Default speed in millimeters per second

        Methods
        -------
        create_position_dict()
            Creates a dictionary with the hardware stage positions.
        get_abs_position()
            Makes sure that the move is within the min and max stage limits.
        stop()
            Emergency halt of stage operation.
        get_position()
            Get position of specific axis
        set_speed()
            Set velocity that the stage can move when scanning.
        get_speed()
            Get velocity
        scanr()
            Set scan start position, end position, and enc_divide
        start_scan()
            Start scan state machine
        stop_scan()
            Start scan and stop after scanning

    """

    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        super().__init__(microscope_name, device_connection, configuration, device_id)

        # Mapping from self.axes to corresponding ASI axis labelling
        self.axes_mapping = {"x": "Z", "y": "Y", "z": "X"}

        # Focus and Theta axes are not supported for ASI Stage
        if "theta" in self.axes:
            self.axes.remove("theta")
        if "f" in self.axes:
            self.axes.remove("f")

        self.asi_axes = list(map(lambda a: self.axes_mapping[a], self.axes))
        self.tiger_controller = device_connection
        # set default speed
        self.default_speed =5.745760 #7.68 * 0.67
        default_speeds = [(axis,self.default_speed) for axis in self.asi_axes]
        if self.tiger_controller != None:
            try:
                self.tiger_controller.set_speed(**dict(default_speeds))
            except TigerException:
                logger.exception(f"Initialize ASI Stage with default speed failed!")

    def __del__(self):
        """Delete the ASI Stage connection."""
        try:
            if self.tiger_controller != None:
                self.tiger_controller.disconnect_from_serial()
                logger.debug("ASI stage connection closed")
        except (AttributeError, BaseException) as e:
            print("Error while disconnecting the ASI stage")
            logger.exception(e)
            raise

    def get_position(self, axis):
        """Get position of specific axos
        
        Parameters
        ----------
        axis : str

        Returns
        -------
            position: float
        """
        try:
            axis = self.axes_mapping[axis]
            pos = self.tiger_controller.get_position_um(axis)
        except TigerException:
            return float("inf")
        except KeyError as e:
            logger.exception(f"KeyError in get_position: {e}")
            return float("inf")
        return pos

    def report_position(self):
        """Reports the position for all axes in microns, and create
        position dictionary."""
        try:
            # positions from the device are in microns
            for ax, n in zip(self.axes, self.asi_axes):
                try:
                    pos = self.tiger_controller.get_position_um(n)
                except:
                    print(f"*** axis {n} has error when getting its position")
                    pos = 0

                # Set class attributes and convert to microns
                setattr(self, f"{ax}_pos", pos)
        except TigerException as e:
            print("Failed to report ASI Stage Position")
            logger.exception(e)
        self.update_position_dict()
        return self.position_dict

    def move_axis_absolute(self, axis, axis_num, move_dictionary):
        """Move stage along a single axis.

        Move absolute command for ASI is MOVE [Axis]=[units 1/10 microns]

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary. For example, axis='x' corresponds to
            'x_abs', 'x_min', etc.
        axis_num : int
            The corresponding number of this axis on a PI stage. Not applicable to the
            ASI stage.
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', 'x_min',
            etc. for one or more axes. Expect values in micrometers.

        Returns
        -------
        bool
            Was the move successful?
        """
        axis_abs = self.get_abs_position(axis, move_dictionary)
        if axis_abs == -1e50:
            return False

        # Move stage
        try:
            axis_abs_um = (
                axis_abs * 10
            )  # This is to account for the asi 1/10 of a micron units
            print("*** trying to move stage:", axis_num, axis_abs_um)
            self.tiger_controller.move_axis(axis_num, axis_abs_um)
            return True
        except TigerException as e:
            print(
                f"ASI stage move axis absolute failed or is trying to move out of "
                f"range: {e}"
            )
            logger.exception(e)
            return False

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """Move Absolute Method.
        XYZ Values should remain in microns for the ASI API
        Theta Values are not accepted.

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for
            one or more axes. Expect values in micrometers, except for theta, which is
            in degrees.
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        success : bool
            Was the move successful?
        """
        for ax, n in zip(self.axes, self.asi_axes):
            if f"{ax}_abs" not in move_dictionary:
                continue
            success = self.move_axis_absolute(ax, n, move_dictionary)
            if wait_until_done:
                self.tiger_controller.wait_for_device()
                # Do we want to wait for device on hardware level? This is an ASI
                # command call

        #  TODO This seems to be handled by each individual move_axis_absolute bc of
        #  ASI's wait_for_device.
        #  Each axis will move and the stage waits until the axis is done before
        #  moving on
        # if success and wait_until_done is True:
        #     try:
        #         self.busy()
        #         success = True
        #     except BaseException as e:
        #         print("Problem communicating with tiger controller during "
        #               "wait command")
        #         success = False
        #         #logger.exception(e)
        return success

    def stop(self):
        """Stop all stage movement abruptly."""
        try:
            self.tiger_controller.stop()
        except TigerException as e:
            print(f"ASI stage halt command failed: {e}")
            logger.exception(e)

    def set_speed(self, velocity_dict):
        """Set scan velocity.

        Parameters
        ----------
        velocity_dict: dict
            velocity for specific axis
            {'x': float, 'y': float, 'z': float}

        Returns
        -------
        success: bool
            Was the setting successful?
        """
        temp = dict(map(lambda k: (self.axes_mapping[k], velocity_dict[k]), velocity_dict))
        try:
            self.tiger_controller.set_speed(**temp)
        except TigerException:
            return False
        except KeyError as e:
            logger.exception(f"KeyError in set_speed: {e}")
            return False
        return True
    
    def get_speed(self, axis):
        """Get scan velocity of the axis.

        Parameters
        ----------
        axis: str
            axis name, such as 'x', 'y', 'z'

        Returns
        -------
        velocity: float
            Velocity
        """
        try:
            velocity = self.tiger_controller.get_speed(self.axes_mapping[axis])
        except TigerException:
            return 0
        except KeyError as e:
            logger.exception(f"KeyError in get_speed: {e}")
            return 0
        return velocity
    
    def scanr(self, start_position_mm, end_position_mm, enc_divide, axis='z'):
        """Set scan range
        
        Parameters
        ----------
        start_position_mm: float
            scan start position
        end_position_mm: float
            scan end position
        enc_divide: float
            an output pulse will occur every enc_divide number of encoder counts
        axis: str
            fast axis name

        Returns
        -------
        success: bool
            Was the setting successful?
        """
        try:
            axis = self.axes_mapping[axis]
            self.tiger_controller.scanr(start_position_mm, end_position_mm, enc_divide, axis)
        except TigerException:
            return False
        except KeyError as e:
            logger.exception(f"KeyError in scanr: {e}")
            return False
        return True
    
    def start_scan(self, axis):
        """Start scan state machine
        
        Parameters
        ----------
        axis: str
            fast axis name, such as 'x', 'y', and 'z'

        Returns
        -------
        success: bool
            Was it successful?

        """
        try:
            axis = self.axes_mapping[axis]
            self.tiger_controller.start_scan(axis)
        except TigerException:
            return False
        except KeyError as e:
            logger.exception(f"KeyError in start_scan: {e}")
            return False
        return True
    
    def stop_scan(self):
        """Stop scan"""
        try:
            self.tiger_controller.stop_scan()
        except TigerException as e:
            logger.exception(e)