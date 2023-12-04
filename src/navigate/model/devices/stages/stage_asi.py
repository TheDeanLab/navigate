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
from navigate.model.devices.stages.stage_base import StageBase
from navigate.model.devices.APIs.asi.asi_tiger_controller import (
    TigerController,
    TigerException,
)

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_ASI_Stage_connection(com_port, baud_rate=115200):
    """Connect to the ASI Stage

    Parameters
    ----------
    com_port : str
        Communication port for ASI Tiger Controller - e.g., COM1
    baud_rate : int
        Baud rate for ASI Tiger Controller - e.g., 9600

    Returns
    -------
    asi_stage : object
        Successfully initialized stage object.
    """

    # wait until ASI device is ready
    asi_stage = TigerController(com_port, baud_rate)
    asi_stage.connect_to_serial()
    if not asi_stage.is_open():
        raise Exception("ASI stage connection failed.")

    return asi_stage


class ASIStage(StageBase):
    """Applied Scientific Instrumentation (ASI) Stage Class

    ASI Documentation: http://asiimaging.com/docs/products/serial_commands

    ASI Quick Start Guide: http://asiimaging.com/docs/command_quick_start

    Note
    ----
    ASI firmware requires all distances to be in a 10th of a micron.

    Warning
    -------
        Do not ever change the F axis. This will alter the relative position of each
        FTP stilt, adding strain to the system. Only move the Z axis, which will
        change both stilt positions simultaneously.
    """

    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        """Initialize the ASI Stage connection.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : object
            Hardware device to connect to
        configuration : multiprocessing.managers.DictProxy
            Global configuration of the microscope
        """
        super().__init__(microscope_name, device_connection, configuration, device_id)

        # Default axes mapping
        axes_mapping = {"x": "Z", "y": "Y", "z": "X", "f": "M"}
        if not self.axes_mapping:
            self.axes_mapping = {
                axis: axes_mapping[axis] for axis in self.axes if axis in axes_mapping
            }
        #: Mapping of axes to ASI axes
        else:
            # Force cast axes to uppercase
            self.axes_mapping = {k: v.upper() for k, v in self.axes_mapping.items()}

        self.asi_axes = dict(map(lambda v: (v[1], v[0]), self.axes_mapping.items()))

        # Set feedback alignment values - Default to 85 if not specified
        if self.stage_feedback is None:
            feedback_alignment = {axis: 85 for axis in self.asi_axes}
        else:
            feedback_alignment = {
                axis: self.stage_feedback
                for axis, self.stage_feedback in zip(self.asi_axes, self.stage_feedback)
            }

        self.tiger_controller = device_connection
        if device_connection is not None:
            # Set feedback alignment values
            for ax, aa in feedback_alignment.items():
                self.tiger_controller.set_feedback_alignment(ax, aa)
            logger.debug("ASI Stage Feedback Alignment Settings:", feedback_alignment)

            # Set finishing accuracy to half of the minimum pixel size we will use
            # pixel size is in microns, finishing accuracy is in mm
            # TODO: check this over all microscopes sharing this stage,
            #       not just the current one
            finishing_accuracy = (
                0.001
                * min(
                    list(
                        configuration["configuration"]["microscopes"][microscope_name][
                            "zoom"
                        ]["pixel_size"].values()
                    )
                )
                / 2
            )
            # If this is changing, the stage must be power cycled for these changes to
            # take effect.
            for ax in self.asi_axes.keys():
                if self.asi_axes[ax] == "theta":
                    self.tiger_controller.set_finishing_accuracy(ax, 0.003013)
                    self.tiger_controller.set_error(ax, 0.1)
                else:
                    self.tiger_controller.set_finishing_accuracy(ax, finishing_accuracy)
                    self.tiger_controller.set_error(ax, 1.2 * finishing_accuracy)

            # Set backlash to 0 (less accurate)
            for ax in self.asi_axes.keys():
                if self.asi_axes[ax] == "theta":
                    self.tiger_controller.set_backlash(ax, 0.1)
                self.tiger_controller.set_backlash(ax, 0.0)

            # Speed optimizations - Set speed to 90% of maximum on each axis
            self.set_speed(percent=0.9)

    def __del__(self):
        """Delete the ASI Stage connection."""
        try:
            if self.tiger_controller is not None:
                self.tiger_controller.disconnect_from_serial()
                logger.debug("ASI stage connection closed")
        except (AttributeError, BaseException) as e:
            logger.exception("ASI Stage Exception", e)
            raise

    def get_axis_position(self, axis):
        """Get position of specific axis

        Parameters
        ----------
        axis : str
            Axis to get position of

        Returns
        -------
            position: float
        """
        try:
            axis = self.axes_mapping[axis]
            pos = self.tiger_controller.get_axis_position_um(axis)
        except TigerException:
            return float("inf")
        except KeyError as e:
            logger.exception(f"ASI Stage - KeyError in get_axis_position: {e}")
            return float("inf")
        return pos

    def report_position(self):
        """Reports the position for all axes in microns, and create
        position dictionary."""
        try:
            # positions from the device are in microns
            pos_dict = self.tiger_controller.get_position(list(self.asi_axes.keys()))
            for axis, pos in pos_dict.items():
                ax = self.asi_axes[axis]
                if ax == "theta":
                    setattr(self, f"{ax}_pos", float(pos) / 1000.0)
                else:
                    setattr(self, f"{ax}_pos", float(pos) / 10.0)
        except TigerException as e:
            logger.exception("ASI Stage Exception", e)

        return self.get_position_dict()

    def move_axis_absolute(self, axis, abs_pos, wait_until_done=False):
        """Move stage along a single axis.

        Move absolute command for ASI is MOVE [Axis]=[units 1/10 microns]

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary. For example, axis='x' corresponds to
            'x_abs', 'x_min', etc.
        abs_pos : float
            Absolute position value
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        bool
            Was the move successful?
        """
        if axis not in self.axes_mapping:
            return False

        axis_abs = self.get_abs_position(axis, abs_pos)
        if axis_abs == -1e50:
            print("axis abs false")
            return False

        # Move stage
        try:
            if axis == "theta":
                self.tiger_controller.move_axis(
                    self.axes_mapping[axis], axis_abs * 1000
                )
            else:
                # The 10 is to account for the ASI units, 1/10 of a micron
                self.tiger_controller.move_axis(self.axes_mapping[axis], axis_abs * 10)

        except TigerException as e:
            print(
                f"ASI stage move axis absolute failed or is trying to move out of "
                f"range: {e}"
            )
            logger.exception("ASI Stage Exception", e)
            return False

        if wait_until_done:
            self.tiger_controller.wait_for_device()
        return True

    def verify_move(self, move_dictionary):
        """Don't submit a move command for axes that aren't moving.
        The Tiger controller wait time for each axis is additive.

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for
            one or more axes. Expect values in micrometers, except for theta, which is
            in degrees.

        Returns
        -------
        res_dict : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for
            one or more axes. Expect values in micrometers, except for theta, which is
            in degrees.
        """
        res_dict = {}
        for axis, val in move_dictionary.items():
            curr_pos = getattr(self, f"{axis}_pos", None)
            if curr_pos != val:
                res_dict[axis] = val
        return res_dict

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
        abs_pos_dict = self.verify_abs_position(move_dictionary)
        if not abs_pos_dict:
            return False
        abs_pos_dict = self.verify_move(abs_pos_dict)

        # This is to account for the asi 1/10 of a micron units
        pos_dict = {
            self.axes_mapping[axis]: pos * 1000 if axis == "theta" else pos * 10
            for axis, pos in abs_pos_dict.items()
        }
        try:
            self.tiger_controller.move(pos_dict)
        except TigerException as e:
            print(
                f"ASI stage move axis absolute failed or is trying to move out of "
                f"range: {e}"
            )
            logger.exception("ASI Stage Exception", e)
            return False
        if wait_until_done:
            self.tiger_controller.wait_for_device()

        return True

    def stop(self):
        """Stop all stage movement abruptly."""
        try:
            self.tiger_controller.stop()
        except TigerException as e:
            print(f"ASI stage halt command failed: {e}")
            logger.exception("ASI Stage Exception", e)

    def set_speed(self, velocity_dict=None, percent=None):
        """Set scan velocity.

        Parameters
        ----------
        velocity_dict: dict
            velocity for specific axis
            {'x': float, 'y': float, 'z': float}
        percent : float
            Percent of maximum speed

        Returns
        -------
        success: bool
            Was the setting successful?
        """
        if percent is not None:
            try:
                self.tiger_controller.set_speed_as_percent_max(percent)
            except TigerException as e:
                print(f"ASI Controller failed to set speed as a percent: {e}")
                return False
        else:
            try:
                self.tiger_controller.set_speed(velocity_dict)
            except TigerException:
                return False
            except KeyError as e:
                logger.exception(f"ASI Stage - KeyError in set_speed: {e}")
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
            logger.exception(f"ASI Stage - KeyError in get_speed: {e}")
            return 0
        return velocity

    def scanr(self, start_position_mm, end_position_mm, enc_divide, axis="z"):
        """Set scan range

        Parameters
        ----------
        start_position_mm: float
            scan start position
        end_position_mm: float
            scan end position
        enc_divide: float
            Step size desired.
        axis: str
            fast axis name

        Returns
        -------
        success: bool
            Was the setting successful?
        """
        try:
            axis = self.axes_mapping[axis]
            self.tiger_controller.scanr(
                start_position_mm, end_position_mm, enc_divide, axis
            )
        except TigerException as e:
            logger.exception(f"TigerException: {e}")
            print(logger.exception())
            return False
        except KeyError as e:
            logger.exception(f"ASI Stage - KeyError in scanr: {e}")
            return False
        # if wait_until_done:
        #     self.tiger_controller.wait_for_device()

        return True
        # return True

    def scanv(
        self, start_position_mm, end_position_mm, number_of_lines, overshoot, axis="z"
    ):
        """Set scan range

        Parameters
        ----------
        start_position_mm: float
            scan start position
        end_position_mm: float
            scan end position
        number of lines: int
            number of steps.
        overshoot: float
            overshoot_time ms
        axis: str
            fast axis name

        Returns
        -------
        success: bool
            Was the setting successful?
        """
        try:
            axis = self.axes_mapping[axis]
            self.tiger_controller.scanv(
                start_position_mm, end_position_mm, number_of_lines, overshoot, axis
            )
        except TigerException as e:
            logger.exception(f"TigerException: {e}")
            print(logger.exception())
            return False
        except KeyError as e:
            logger.exception(f"ASI Stage - KeyError in scanr: {e}")
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
        except TigerException as e:
            logger.exception(f"TigerException: {e}")
            return False
        except KeyError as e:
            logger.exception(f"ASI Stage - KeyError in start_scan: {e}")
            return False
        return True

    def stop_scan(self):
        """Stop scan"""
        try:
            self.tiger_controller.stop_scan()
        except TigerException as e:
            logger.exception("ASI Stage Exception", e)

    def wait_until_complete(self, axis):
        try:
            while self.tiger_controller.is_axis_busy(axis):
                time.sleep(0.1)
        except TigerException as e:
            print(f"ASI Stage Exception {e}")
            logger.exception(f"ASI Stage Exception {e}")
            return False
        return True
