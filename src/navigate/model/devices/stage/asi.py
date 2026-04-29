# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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
from typing import Any

# Third Party Imports

# Local Imports
from navigate.model.devices.stage.base import StageBase
from navigate.model.devices.device_types import SerialDevice, IntegratedDevice
from navigate.model.devices.APIs.asi.asi_tiger_controller import (
    TigerController,
    ASIException,
)
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

THETA_RUN_SPEED_DEG_PER_SEC = 5.0
THETA_MOVE_TIMEOUT_SECONDS = 120.0


@log_initialization
class ASIStage(StageBase, SerialDevice, IntegratedDevice):
    """Applied Scientific Instrumentation (ASI) Stage Class

    ASI Documentation: https://asiimaging.com/docs/products/serial_commands

    ASI Quick Start Guide: https://asiimaging.com/docs/command_quick_start

    Note
    ----
    ASI firmware requires all distances to be in a 10th of a micron.

    Warning
    -------
        Do not ever change the F axis. This will alter the relative position of each
        FTP stilt, adding strain to the system. Only move the Z axis, which will
        change both stilt positions simultaneously.
    """

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        device_id: int = 0,
    ):
        """Initialize the ASI Stage connection.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : Any
            Hardware device to connect to
        configuration : Dict[str, Any]
            Global configuration of the microscope
        device_id : int
            Device ID for the stage, defaults to 0
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

        self.asi_controller = device_connection
        if device_connection is not None:
            # Set feedback alignment values
            for ax, aa in feedback_alignment.items():
                self.asi_controller.set_feedback_alignment(ax, aa)
            logger.debug(f"ASI Stage Feedback Alignment Settings: {feedback_alignment}")

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
                    self.asi_controller.set_finishing_accuracy(ax, 0.003013)
                    self.asi_controller.set_error(ax, 0.1)
                else:
                    self.asi_controller.set_finishing_accuracy(ax, finishing_accuracy)
                    self.asi_controller.set_error(ax, 1.2 * finishing_accuracy)

            # Set backlash to 0 (less accurate)
            for ax in self.asi_axes.keys():
                if self.asi_axes[ax] == "theta":
                    self.asi_controller.set_backlash(ax, 0.1)
                self.asi_controller.set_backlash(ax, 0.0)

            # Speed optimizations - Set speed to 90% of maximum on each axis
            self.set_speed(percent=0.9)
            self.set_theta_speed()

    def __del__(self) -> None:
        """Delete the ASI Stage connection."""
        try:
            if self.asi_controller is not None:
                self.asi_controller.disconnect_from_serial()
                logger.debug("ASI stage connection closed")
        except (AttributeError, BaseException) as e:
            logger.error("ASI Stage Exception", e)
            raise

    @classmethod
    def connect(
        cls, port: str, baudrate: int = 115200, timeout: float = 0.25
    ) -> TigerController:
        """Connect to the ASI Stage

        Parameters
        ----------
        port : str
            Communication port for ASI Tiger Controller - e.g., COM1
        baudrate : int
            Baud rate for ASI Tiger Controller - e.g., 9600
        timeout : float
            Timeout value.

        Returns
        -------
        asi_stage : object
            Successfully initialized stage object.
        """

        # wait until ASI device is ready
        asi_stage = TigerController(port, baudrate)
        asi_stage.connect_to_serial()
        if not asi_stage.is_open():
            logger.error("ASI stage connection failed.")
            raise Exception("ASI stage connection failed.")

        return asi_stage

    def get_axis_position(self, axis: str) -> float:
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
            pos = self.asi_controller.get_axis_position_um(axis)
        except ASIException:
            return float("inf")
        except KeyError as e:
            logger.exception(f"ASI Stage - KeyError in get_axis_position: {e}")
            return float("inf")
        return pos

    def report_position(self) -> dict[str, float]:
        """Reports the position for all axes in microns, and create
        position dictionary.

        Returns
        -------
        dict
            Dictionary of positions for each axis in microns.
        """
        try:
            # positions from the device are in microns
            pos_dict = self.asi_controller.get_position(list(self.asi_axes.keys()))
            for axis, pos in pos_dict.items():
                ax = self.asi_axes[axis]
                if ax == "theta":
                    setattr(self, f"{ax}_pos", float(pos) / 1000.0)
                else:
                    setattr(self, f"{ax}_pos", float(pos) / 10.0)
        except ASIException as e:
            logger.exception("ASI Stage Exception", e)

        return self.get_position_dict()

    def move_axis_absolute(
        self, axis: str, abs_pos: float, wait_until_done: bool = False
    ) -> bool:
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
                self.asi_controller.move_axis(self.axes_mapping[axis], axis_abs * 1000)
            else:
                # The 10 is to account for the ASI units, 1/10 of a micron
                self.asi_controller.move_axis(self.axes_mapping[axis], axis_abs * 10)

        except ASIException as e:
            print(
                f"ASI stage move axis absolute failed or is trying to move out of "
                f"range: {e}"
            )
            logger.exception("ASI Stage Exception", e)
            return False

        if wait_until_done:
            return self._wait_for_move([axis])
        return True

    def verify_move(self, move_dictionary: dict[str, float]) -> dict[str, float]:
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

    def move_absolute(
        self, move_dictionary: dict[str, float], wait_until_done: bool = False
    ) -> bool:
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
        if len(abs_pos_dict) == 0:
            return False

        # This is to account for the asi 1/10 of a micron units
        pos_dict = {
            self.axes_mapping[axis]: pos * 1000 if axis == "theta" else pos * 10
            for axis, pos in abs_pos_dict.items()
        }
        try:
            self.asi_controller.move(pos_dict)
        except ASIException as e:
            print(
                f"ASI stage move axis absolute failed or is trying to move out of "
                f"range: {e}"
            )
            logger.exception("ASI Stage Exception", e)
            return False
        if wait_until_done:
            return self._wait_for_move(list(abs_pos_dict.keys()))

        return True

    def stop(self) -> None:
        """Stop all stage movement abruptly."""
        try:
            self.asi_controller.stop()
        except ASIException as e:
            print(f"ASI stage halt command failed: {e}")
            logger.exception("ASI Stage Exception", e)

    def set_speed(
        self, velocity_dict: dict[str, float] = None, percent: float = None
    ) -> bool:
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
                self.asi_controller.set_speed_as_percent_max(percent)
            except ASIException as e:
                print(f"ASI Controller failed to set speed as a percent: {e}")
                return False
        else:
            try:
                self.asi_controller.set_speed(velocity_dict)
            except ASIException:
                return False
            except KeyError as e:
                logger.exception(f"ASI Stage - KeyError in set_speed: {e}")
                return False
        return True

    def set_theta_speed(self) -> bool:
        """Set a conservative run speed for theta axes only."""
        theta_axes = [
            axis for axis, stage_axis in self.asi_axes.items() if stage_axis == "theta"
        ]
        if not theta_axes:
            return True

        try:
            self.asi_controller.set_speed(
                {axis: THETA_RUN_SPEED_DEG_PER_SEC for axis in theta_axes}
            )
        except ASIException as e:
            print(f"ASI Controller failed to set theta speed: {e}")
            logger.exception("ASI Stage Exception", e)
            return False
        return True

    def _wait_for_move(self, axes: list[str]) -> bool:
        """Wait for a move, using a longer axis-specific wait for theta."""
        self.asi_controller.wait_for_device()
        if "theta" in axes and "theta" in self.axes_mapping:
            return self.wait_until_complete(
                self.axes_mapping["theta"], timeout=THETA_MOVE_TIMEOUT_SECONDS
            )
        return True

    def get_speed(self, axis: str) -> float:
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
            velocity = self.asi_controller.get_speed(self.axes_mapping[axis])
        except ASIException:
            return 0
        except KeyError as e:
            logger.exception(f"ASI Stage - KeyError in get_speed: {e}")
            return 0
        return velocity

    def scanr(
        self,
        start_position_mm: float,
        end_position_mm: float,
        enc_divide: float,
        axis: str = "z",
    ) -> bool:
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
            self.asi_controller.scanr(
                start_position_mm, end_position_mm, enc_divide, axis
            )
        except ASIException as e:
            error_statement = f"ASIException: {e}"
            logger.exception(error_statement)
            print(error_statement)
            return False
        except KeyError as e:
            logger.exception(f"ASI Stage - KeyError in scanr: {e}")
            return False

        return True

    def scanv(
        self,
        start_position_mm: float,
        end_position_mm: float,
        number_of_lines: int,
        overshoot: float,
        axis: str = "z",
    ) -> bool:
        """Set scan range

        Parameters
        ----------
        start_position_mm: float
            scan start position
        end_position_mm: float
            scan end position
        number_of_lines: int
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
            self.asi_controller.scanv(
                start_position_mm, end_position_mm, number_of_lines, overshoot, axis
            )
        except ASIException as e:
            error_statement = f"ASIException: {e}"
            logger.exception(error_statement)
            print(error_statement)
            return False
        except KeyError as e:
            logger.exception(f"ASI Stage - KeyError in scanr: {e}")
            return False
        return True

    def start_scan(self, axis: str) -> bool:
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
            self.asi_controller.start_scan(axis)
        except ASIException as e:
            logger.exception(f"ASIException: {e}")
            return False
        except KeyError as e:
            logger.exception(f"ASI Stage - KeyError in start_scan: {e}")
            return False
        return True

    def stop_scan(self) -> None:
        """Stop scan"""
        try:
            self.asi_controller.stop_scan()
        except ASIException as e:
            logger.exception("ASI Stage Exception", e)

    def wait_until_complete(self, axis: str, timeout: float = None) -> bool:
        start_time = time.monotonic()
        try:
            while self.asi_controller.is_axis_busy(axis):
                if timeout is not None and time.monotonic() - start_time >= timeout:
                    logger.warning(
                        "ASI Stage wait timed out for axis %s after %.1f seconds",
                        axis,
                        timeout,
                    )
                    return False
                time.sleep(0.1)
        except ASIException as e:
            print(f"ASI Stage Exception {e}")
            logger.exception(f"ASI Stage Exception {e}")
            return False
        return True


@log_initialization
class MS2000Stage(ASIStage):
    """Applied Scientific Instrumentation (ASI) Stage Class

    ASI Documentation: https://asiimaging.com/docs/products/serial_commands

    ASI Quick Start Guide: https://asiimaging.com/docs/command_quick_start

    Note
    ----
        ASI firmware requires all distances to be in a 10th of a micron.
    """

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        device_id: int = 0,
    ):
        """Initialize the ASI Stage connection.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : Any
            Hardware device to connect to
        configuration : Dict[str, Any]
            Global configuration of the microscope
        device_id : int
            Device ID for the stage, default to 0
        """
        StageBase.__init__(
            self, microscope_name, device_connection, configuration, device_id
        )

        # Default axes mapping
        axes_mapping = {"x": "X", "y": "Y", "z": "Z"}
        if not self.axes_mapping:
            #: dict: Mapping of software axes to ASI hardware axes
            self.axes_mapping = {
                axis: axes_mapping[axis] for axis in self.axes if axis in axes_mapping
            }
        else:
            # Mapping of axes to ASI axes, force cast axes to uppercase
            self.axes_mapping = {k: v.upper() for k, v in self.axes_mapping.items()}

        #: dict: Dictionary of ASI axes to software axes
        self.asi_axes = dict(map(lambda v: (v[1], v[0]), self.axes_mapping.items()))

        # Set feedback alignment values - Default to 85 if not specified
        if self.stage_feedback is None:
            feedback_alignment = {axis: 85 for axis in self.asi_axes}
        else:
            feedback_alignment = {
                axis: self.stage_feedback
                for axis, self.stage_feedback in zip(self.asi_axes, self.stage_feedback)
            }

        #: object: ASI MS2000 Controller
        self.asi_controller = device_connection
        if device_connection is not None:
            # Set feedback alignment values
            for ax, aa in feedback_alignment.items():
                self.asi_controller.set_feedback_alignment(ax, aa)
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
                self.asi_controller.set_finishing_accuracy(ax, finishing_accuracy)
                self.asi_controller.set_error(ax, 1.2 * finishing_accuracy)

            # Set backlash to 0 (less accurate)
            for ax in self.asi_axes.keys():
                self.asi_controller.set_backlash(ax, 0.02)

            # Set wheel jog speed
            jsspd = configuration["configuration"]["microscopes"][microscope_name][
                "stage"
            ]["hardware"][device_id].get("jsspd", None)
            if jsspd is not None:
                self.asi_controller.set_jog_speed(axes=self.asi_axes, jsspd=int(jsspd))

            # Speed optimizations - Set speed to 90% of maximum on each axis
            self.set_speed(percent=0.9)

    @classmethod
    def connect(
        cls, port: str, baudrate: int = 115200, timeout: float = 0.25
    ) -> TigerController:
        """Connect to the ASI Stage

        Parameters
        ----------
        port : str
            Communication port for ASI Tiger Controller - e.g., COM1
        baudrate : int
            Baud rate for ASI Tiger Controller - e.g., 9600
        timeout : float
            Timeout value.

        Returns
        -------
        asi_stage : object
            Successfully initialized stage object.
        """
        from navigate.model.devices.APIs.asi.asi_MS2000_controller import (
            MS2000Controller,
        )

        # wait until ASI device is ready
        asi_stage = MS2000Controller(port, baudrate)
        asi_stage.connect_to_serial()
        if not asi_stage.is_open():
            logger.error("ASI stage connection failed.")
            raise Exception("ASI stage connection failed.")

        return asi_stage

    def move_axis_relative(
        self, axis: str, distance: float, wait_until_done: bool = False
    ) -> bool:
        """Move the stage relative to the current position along the specified axis.
        XYZ Values should remain in microns for the ASI API
        Theta Values are not accepted.

        Parameters
        ----------
        axis : str
            The axis along which to move the stage (e.g., 'x', 'y', 'z').
        distance : float
            The distance to move relative to the current position,
            in micrometers for XYZ axes.
        wait_until_done : bool
            Whether to wait until the stage has moved to its new position,
            by default False.

        Returns
        -------
        success : bool
            Indicates whether the move was successful.
        """
        if axis not in self.axes_mapping:
            return False

        abs_pos = self.get_axis_position(axis) + distance

        axis_abs = self.get_abs_position(axis, abs_pos)
        if axis_abs == -1e50:
            print("axis rel false")
            return False

        # Move stage
        try:
            # The 10 is to account for the ASI units, 1/10 of a micron
            self.asi_controller.moverel_axis(axis, distance * 10)

        except ASIException as e:
            print(
                f"ASI stage move axis absolute failed or is trying to move out of "
                f"range: {e}"
            )
            logger.exception("ASI Stage Exception", e)
            return False

        if wait_until_done:
            self.asi_controller.wait_for_device()
        return True

    def scan_axis_triggered_move(
        self,
        start_position: float,
        end_position: float,
        axis: str,
        ttl_triggered: bool = False,
    ) -> bool:
        """Move the stage along the specified axis from start position to end position,
        with optional TTL triggering.

        Parameters
        ----------
        start_position : float
            The starting position of the stage along the specified axis.
        end_position : float
            The desired end position of the stage along the specified axis.
        axis : str
            The axis along which the stage will be moved (e.g., 'x', 'y', 'z').
        ttl_triggered : bool
            Whether to trigger the move using TTL signal, by default False.

        Returns
        -------
        success : bool
            Indicates whether the move was successful.
        """

        self.move_axis_absolute(axis, start_position, True)

        distance = end_position - start_position
        self.move_axis_relative(axis, distance, True)

        try:
            self.asi_controller.set_backlash(axis, 0.05)
            if ttl_triggered:
                self.asi_controller.set_triggered_move(axis)
        except ASIException as e:
            logger.exception(f"ASIException: {e}")
            return False
        except KeyError as e:
            logger.exception(f"ASI Stage - KeyError in scan_axis_triggered_move: {e}")
            return False

        return True


class MFC2000Stage(ASIStage):
    """Applied Scientific Instrumentation (ASI) Stage Class

    ASI Documentation: https://asiimaging.com/docs/products/serial_commands

    ASI Quick Start Guide: https://asiimaging.com/docs/command_quick_start

    Note
    ----
        ASI firmware requires all distances to be in a 10th of a micron.
    """

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        device_id: int = 0,
    ):
        """Initialize the ASI Stage connection.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : Any
            Hardware device to connect to
        configuration : Dict[str, Any]
            Global configuration of the microscope
        device_id : int
            Device ID for the stage, default to 0
        """
        super().__init__(microscope_name, device_connection, configuration, device_id)

    @classmethod
    def connect(
        cls, port: str, baudrate: int = 115200, timeout: float = 0.25
    ) -> TigerController:
        """Connect to the ASI Stage

        Parameters
        ----------
        port : str
            Communication port for ASI Tiger Controller - e.g., COM1
        baudrate : int
            Baud rate for ASI Tiger Controller - e.g., 9600
        timeout : float
            Timeout value.

        Returns
        -------
        asi_stage : object
            Successfully initialized stage object.
        """
        from navigate.model.devices.APIs.asi.asi_MFC_controller import MFCTwoThousand

        # wait until ASI device is ready
        asi_stage = MFCTwoThousand(port, baudrate)
        asi_stage.connect_to_serial()
        if not asi_stage.is_open():
            logger.error("ASI stage connection failed.")
            raise Exception("ASI stage connection failed.")

        return asi_stage
