# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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

# Standard Library imports
import importlib
import logging
import time
from multiprocessing.managers import ListProxy
from typing import Any

# Local Imports
from navigate.model.devices.stage.base import StageBase
from navigate.model.devices.device_types import IntegratedDevice
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def _get_stage_device_entry(
    configuration: dict[str, Any], microscope_name: str, device_id: int
) -> dict[str, Any]:
    """Return stage device config entry regardless of list/single configuration."""
    stage_hardware = configuration["configuration"]["microscopes"][microscope_name][
        "stage"
    ]["hardware"]
    if type(stage_hardware) == ListProxy:
        return stage_hardware[device_id]
    return stage_hardware


def _get_device_unit_scale(device_entry: dict[str, Any]) -> float:
    """Return device-units-per-mm with safe fallbacks for legacy configs."""
    device_units_per_mm = device_entry.get("device_units_per_mm")
    if device_units_per_mm is not None:
        return float(device_units_per_mm)

    # Legacy KINESIS configs may define steps_per_um instead.
    steps_per_um = device_entry.get("steps_per_um")
    if steps_per_um is not None:
        return float(steps_per_um) * 1000.0

    return 1000.0


@log_initialization
class KIM001Stage(StageBase, IntegratedDevice):
    """Thorlabs KIM Stage"""

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        device_id: int = 0,
    ) -> None:
        """Initialize the stage.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : str
            Connection string for the device.
        configuration : dict
            Configuration dictionary for the device.
        device_id : int
            Device ID for the device.
        """
        super().__init__(
            microscope_name, device_connection, configuration, device_id
        )  # only initialize the focus axis

        # Default mapping from self.axes to corresponding KIM channels
        axes_mapping = {"x": 4, "y": 2, "z": 3, "f": 1}
        if not self.axes_mapping:
            #: dict: Dictionary mapping software axes to hardware axes.
            self.axes_mapping = {
                axis: axes_mapping[axis] for axis in self.axes if axis in axes_mapping
            }

        #: list: List of KIM axes available.
        self.kim_axes = list(self.axes_mapping.values())

        if device_connection is not None:
            #: navigate.model.devices.APIs.thorlabs.kcube_inertial: Thorlabs KIM Stage
            self.kim_controller = device_connection

        device_config = configuration["configuration"]["microscopes"][microscope_name][
            "stage"
        ]["hardware"]
        if type(device_config) == ListProxy:
            #: str: Serial number of the stage.
            self.serial_number = str(device_config[device_id]["serial_number"])
        else:
            self.serial_number = device_config["serial_number"]

    def __del__(self) -> None:
        """Delete the KIM Connection"""
        try:
            self.stop()
            self.kim_controller.KIM_Close(self.serial_number)
        except Exception as e:
            logger.exception(e)

    @classmethod
    def get_connect_params(cls) -> list[str]:
        """Register the parameters required to connect to the stage.

        Returns
        -------
        list
            List of parameters required to connect to the stage.
        """
        return ["serial_number"]

    @classmethod
    def connect(cls, serial_number: str) -> Any:
        """Connect to the Thorlabs KIM Stage

        Parameters
        ----------
        serial_number : str
            Serial number of the stage.

        Returns
        -------
        kim_controller
            Thorlabs KIM Stage controller
        """
        kim_controller = importlib.import_module(
            "navigate.model.devices.APIs.thorlabs.kcube_inertial"
        )

        # Initialize
        kim_controller.TLI_BuildDeviceList()

        # Open the same serial number device if there are several devices connected to the
        # computer
        available_serialnum = kim_controller.TLI_GetDeviceListExt()
        if not list(
            filter(lambda s: str(s) == str(serial_number), available_serialnum)
        ):
            print(
                f"** Please make sure Thorlabs stage with serial number {serial_number} "
                f"is connected to the computer!"
            )
            raise RuntimeError
        kim_controller.KIM_Open(str(serial_number))
        return kim_controller

    def report_position(self) -> dict[str, float]:
        """Report the position of the stage.

        Reports the position of the stage for all axes, and creates the hardware
        position dictionary.

        Returns
        -------
        position_dict : dict
            Dictionary containing the current position of the stage.
        """
        for ax, i in self.axes_mapping.items():
            try:
                # need to request before we get the current position
                self.kim_controller.KIM_RequestCurrentPosition(self.serial_number, i)
                pos = self.kim_controller.KIM_GetCurrentPosition(self.serial_number, i)
                setattr(self, f"{ax}_pos", pos)
            except (
                self.kim_controller.TLFTDICommunicationError,
                self.kim_controller.TLDLLError,
                self.kim_controller.TLMotorDLLError,
            ):
                pass

        return self.get_position_dict()

    def move_axis_absolute(
        self, axis: str, abs_pos: float, wait_until_done: bool = False
    ) -> bool:
        """Implement movement logic along a single axis.

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
        if axis not in self.axes_mapping:
            return False

        axis_abs = self.get_abs_position(axis, abs_pos)
        if axis_abs == -1e50:
            return False

        self.kim_controller.KIM_MoveAbsolute(
            self.serial_number, self.axes_mapping[axis], int(axis_abs)
        )

        if wait_until_done:
            stage_pos, n_tries, i = -1e50, 10, 0
            target_pos = axis_abs
            while (stage_pos != target_pos) and (i < n_tries):
                # TODO: do we need to request before we get the current position
                # self.kim_controller.KIM_RequestCurrentPosition(self.serial_number,
                # int(self.axes_mapping[axis]))
                stage_pos = self.kim_controller.KIM_GetCurrentPosition(
                    self.serial_number, int(self.axes_mapping[axis])
                )
                i += 1
                time.sleep(0.01)
            if stage_pos != target_pos:
                return False
        return True

    def move_absolute(
        self, move_dictionary: dict[str, float], wait_until_done: bool = False
    ) -> bool:
        """Move stage along a single axis.

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for
            one or more axes. Expects values in micrometers, except for theta, which is
            in degrees.
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        success : bool
            Was the move successful?
        """

        result = True
        for ax, n in self.axes_mapping.items():
            if f"{ax}_abs" not in move_dictionary:
                continue
            result = (
                self.move_axis_absolute(
                    ax, move_dictionary[f"{ax}_abs"], wait_until_done
                )
                and result
            )

        return result

    def stop(self) -> None:
        """Stop all stage channels move"""
        for i in self.kim_axes:
            self.kim_controller.KIM_MoveStop(self.serial_number, i)


@log_initialization
class KST101Stage(StageBase):
    """Thorlabs KST Stage"""

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        device_id: int = 0,
    ) -> None:
        """Initialize the stage.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : str
            Connection string for the device.
        configuration : dict
            Configuration dictionary for the device.
        device_id : int
            Device ID for the device.
        """
        super().__init__(microscope_name, device_connection, configuration, device_id)

        #: dict: Mapping of axes to KST axes. Only support one axis.
        axes_mapping = {"x": 1, "y": 1, "z": 1, "f": 1}

        if not self.axes_mapping:
            if self.axes[0] not in axes_mapping:
                raise KeyError(f"KTS101 doesn't support axis: {self.axes[0]}")
            self.axes_mapping = {self.axes[0]: axes_mapping[self.axes[0]]}

        #: list: List of KST axes available.
        self.KST_axes = list(self.axes_mapping.values())

        device_entry = _get_stage_device_entry(
            configuration, microscope_name, device_id
        )
        #: str: Serial number of the stage.
        self.serial_number = str(device_entry.get("serial_number", ""))
        #: float: Device units per mm.
        self.device_unit_scale = _get_device_unit_scale(device_entry)

        if device_connection is not None:
            #: object: Thorlabs KST Stage controller
            self.kst_controller = device_connection
        # else:
        #     self.kst_controller = self.connect(self.serial_number)

    def __del__(self):
        """Delete the KST Connection"""
        try:
            self.stop()
            self.kst_controller.KST_Close(self.serial_number)
        except Exception as e:
            logger.exception(e)

    @classmethod
    def get_connect_params(cls) -> list[str]:
        """Register the parameters required to connect to the stage.

        Returns
        -------
        list
            List of parameters required to connect to the stage.
        """
        return ["serial_number"]

    @classmethod
    def connect(cls, serial_number: str) -> Any:
        """Connect to the Thorlabs KST Stage

        Parameters
        ----------
        serial_number : str
            Serial number of the stage.

        Returns
        -------
        kst_controller
            Thorlabs KST Stage controller
        """
        kst_controller = importlib.import_module(
            "navigate.model.devices.APIs.thorlabs.kcube_steppermotor"
        )

        # Initialize
        kst_controller.TLI_BuildDeviceList()

        # Open the same serial number device if there are several devices connected to the
        # computer
        available_serial_numbers = kst_controller.TLI_GetDeviceListExt()
        if not list(
            filter(lambda s: str(s) == str(serial_number), available_serial_numbers)
        ):
            print(
                f"** Please make sure Thorlabs stage with serial number {serial_number} "
                f"is connected to the computer!"
            )
            raise RuntimeError
        kst_controller.KST_Open(str(serial_number))
        return kst_controller

    def report_position(self) -> dict[str, float]:
        """
        Report the position of the stage.

        Reports the position of the stage for all axes, and creates the hardware
        position dictionary.

        Returns
        -------
        position_dict : dict
            Dictionary containing the current position of the stage.
        """

        try:
            pos = self.kst_controller.KST_GetCurrentPosition(
                self.serial_number
            ) / float(self.device_unit_scale)
            setattr(self, f"{self.axes[0]}_pos", pos)
        except (
            self.kst_controller.TLFTDICommunicationError,
            self.kst_controller.TLDLLError,
            self.kst_controller.TLMotorDLLError,
        ):
            pass

        return self.get_position_dict()

    def move_axis_absolute(
        self, axes: str, abs_pos: float, wait_until_done: bool = False
    ) -> bool:
        """
        Implement movement.

        Parameters
        ----------
        axes : str
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
        axis_abs = self.get_abs_position(axes, abs_pos)
        if axis_abs == -1e50:
            return False

        self.kst_controller.KST_SetAbsolutePosition(
            self.serial_number, int(axis_abs * self.device_unit_scale)
        )
        self.kst_controller.KST_MoveAbsolute(self.serial_number)

        if wait_until_done:
            stage_pos, n_tries, i = -1e50, 1000, 0
            target_pos = axis_abs
            while (round(stage_pos, 6) != round(target_pos, 6)) and (i < n_tries):
                stage_pos = (
                    self.kst_controller.KST_GetCurrentPosition(self.serial_number)
                    / self.device_unit_scale
                )
                i += 1
                time.sleep(0.01)
            if stage_pos != target_pos:
                return False
        return True

    def move_absolute(
        self, move_dictionary: dict[str, float], wait_until_done: bool = False
    ) -> bool:
        """Move stage along a single axis.

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for
            one or more axes. Expects values in micrometers, except for theta, which is
            in degrees.
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        success : bool
            Was the move successful?
        """

        result = True
        result = (
            self.move_axis_absolute("f", move_dictionary["f_abs"], wait_until_done),
            result,
        )

        return result

    def move_to_position(self, position: float, wait_until_done: bool = False) -> bool:
        """Perform a move to position

        Parameters
        ----------
        position : float
            Stage position in mm.
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        success : bool
            Was the move successful?
        """
        self.kst_controller.KST_MoveToPosition(
            self.serial_number, position * self.device_unit_scale
        )

        if wait_until_done:
            stage_pos, n_tries, i = -1e50, 1000, 0
            target_pos = position
            while (round(stage_pos, 4) != round(target_pos, 4)) and (i < n_tries):
                stage_pos = (
                    self.kst_controller.KST_GetCurrentPosition(self.serial_number)
                    / self.device_unit_scale
                )
                i += 1
                time.sleep(0.01)
            if stage_pos != target_pos:
                return False
            else:
                return True

    def run_homing(self) -> None:
        """Run homing sequence."""
        self.kst_controller.KST_HomeDevice(self.serial_number)
        self.move_to_position(12.5, wait_until_done=True)

    def stop(self) -> None:
        """
        Stop all stage channels move
        """
        self.kst_controller.KST_MoveStop(self.serial_number)


@log_initialization
class KINESISStage(StageBase):
    """Thorlabs Kinesis stage via pylablib (serial backend)."""

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        device_id: int = 0,
    ) -> None:
        super().__init__(microscope_name, device_connection, configuration, device_id)

        axes_mapping = {"x": 1, "y": 1, "z": 1, "f": 1}
        if not self.axes_mapping:
            if self.axes[0] not in axes_mapping:
                raise KeyError(f"KINESIS stage does not support axis: {self.axes[0]}")
            self.axes_mapping = {self.axes[0]: axes_mapping[self.axes[0]]}

        device_entry = _get_stage_device_entry(
            configuration, microscope_name, device_id
        )
        self.serial_number = str(device_entry.get("serial_number", ""))

        steps_per_um = device_entry.get("steps_per_um")
        if steps_per_um is None:
            # Fallback to existing stage field so configs do not need to change.
            device_units_per_mm = _get_device_unit_scale(device_entry)
            steps_per_um = float(device_units_per_mm) / 1000.0
        self.steps_per_um = float(steps_per_um)

        self.kinesis_controller = device_connection

    def __del__(self) -> None:
        try:
            self.stop()
            self.kinesis_controller.close()
        except Exception:
            pass

    @classmethod
    def get_connect_params(cls) -> list[str]:
        return ["serial_number"]

    @classmethod
    def connect(cls, serial_number: str) -> Any:
        kinesis_module = importlib.import_module(
            "navigate.model.devices.APIs.thorlabs.pykinesis_controller"
        )
        return kinesis_module.KinesisStage(str(serial_number), False)

    def report_position(self) -> dict[str, float]:
        try:
            pos = self.kinesis_controller.get_current_position(self.steps_per_um)
            setattr(self, f"{self.axes[0]}_pos", pos)
        except Exception:
            pass
        return self.get_position_dict()

    def move_axis_absolute(
        self, axis: str, abs_pos: float, wait_until_done: bool = False
    ) -> bool:
        if axis not in self.axes_mapping:
            return False

        axis_abs = self.get_abs_position(axis, abs_pos)
        if axis_abs == -1e50:
            return False

        self.kinesis_controller.move_to_position(
            axis_abs, self.steps_per_um, wait_until_done
        )
        return True

    def move_absolute(
        self, move_dictionary: dict[str, float], wait_until_done: bool = False
    ) -> bool:
        result = True
        for axis in self.axes_mapping.keys():
            if f"{axis}_abs" not in move_dictionary:
                continue
            result = (
                self.move_axis_absolute(
                    axis, move_dictionary[f"{axis}_abs"], wait_until_done
                )
                and result
            )
        return result

    def move_to_position(self, position: float, wait_until_done: bool = False) -> bool:
        return self.move_axis_absolute(self.axes[0], position, wait_until_done)

    def run_homing(self) -> None:
        self.kinesis_controller.home_stage()
        axis = self.axes[0]
        midpoint = (
            getattr(self, f"{axis}_min", 0) + getattr(self, f"{axis}_max", 25)
        ) / 2
        self.move_axis_absolute(axis, midpoint, wait_until_done=True)

    def stop(self) -> None:
        self.kinesis_controller.stop()
