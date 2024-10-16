# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
"""

Builds from
 stage:
      hardware:
        -
          name: stage
          type: KST101
          serial_number: 26001318
          axes: [f]
          axes_mapping: [1]
          device_units_per_mm: 20000000/9.957067
          axes_channels: autofocus
          max: 0
          min: 25

"""
# Standard Library imports
import importlib
import logging
import time
from multiprocessing.managers import ListProxy
from numpy import round

# Third Party Library imports

# Local Imports
from navigate.model.devices.stages.base import StageBase
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_TLKSTStage_connection(serialnum):
    """Connect to the Thorlabs KST Stage

    Parameters
    ----------
    serialnum : str
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
    available_serialnum = kst_controller.TLI_GetDeviceListExt()
    if not list(filter(lambda s: str(s) == str(serialnum), available_serialnum)):
        print(
            f"** Please make sure Thorlabs stage with serial number {serialnum} "
            f"is connected to the computer!"
        )
        raise RuntimeError
    kst_controller.KST_Open(str(serialnum))
    return kst_controller


@log_initialization
class TLKSTStage(StageBase):
    """Thorlabs KST Stage"""

    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
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

        device_config = configuration["configuration"]["microscopes"][microscope_name][
            "stage"
        ]["hardware"]
        if type(device_config) == ListProxy:
            #: str: Serial number of the stage.
            self.serial_number = str(device_config[device_id]["serial_number"])

            #: float: Device units per mm.
            self.device_unit_scale = device_config[device_id]["device_units_per_mm"]
        else:
            self.serial_number = device_config["serial_number"]
            self.device_unit_scale = device_config["device_units_per_mm"]

        if device_connection is not None:
            #: object: Thorlabs KST Stage controller
            self.kst_controller = device_connection
        else:
            self.kst_controller = build_TLKSTStage_connection(self.serial_number)

    def __del__(self):
        """Delete the KST Connection"""
        try:
            self.stop()
            self.kst_controller.KST_Close(self.serial_number)
        except Exception as e:
            logger.exception(e)

    def report_position(self):
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

    def move_axis_absolute(self, axes, abs_pos, wait_until_done=False):
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

    def move_absolute(self, move_dictionary, wait_until_done=False):
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

    def move_to_position(self, position, wait_until_done=False):
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

    def run_homing(self):
        """Run homing sequence."""
        self.kst_controller.KST_HomeDevice(self.serial_number)
        self.move_to_position(12.5, wait_until_done=True)

    def stop(self):
        """
        Stop all stage channels move
        """
        self.kst_controller.KST_MoveStop(self.serial_number)
