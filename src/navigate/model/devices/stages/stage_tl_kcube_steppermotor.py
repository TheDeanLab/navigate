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
"""

Builds from
 stage:
      hardware:
        -
          name: stage
          type: PI
          serial_number: 119060508
          axes: [x, y, z, theta, f]
          axes_mapping: [1, 2, 3, 4, 5]
          volts_per_micron: None
          axes_channels: None
          max: None
          min: None

"""
# Standard Library imports
import importlib
import logging
import time
from multiprocessing.managers import ListProxy

# Local Imports
from navigate.model.devices.stages.stage_base import StageBase


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

"""

1. What are the stage axes equivelent for the linear 1d stage? Refers to for ax in axes...
2. How does the axes mapping affect how the rest of the code works?
"""
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
        super().__init__(
            microscope_name, device_connection, configuration, device_id
        )  # only initialize the focus axis

        # Default mapping from self.axes to corresponding KST channels
        axes_mapping = {"f": 1}
        if not self.axes_mapping:
            #: dict: Dictionary mapping software axes to hardware axes.
            self.axes_mapping = {
                axis: axes_mapping[axis] for axis in self.axes if axis in axes_mapping
            }

        #: list: List of KST axes available.
        self.KST_axes = list(self.axes_mapping.values())

        if device_connection is not None:
            #: object: Thorlabs KST Stage controller
            self.kst_controller = device_connection

        device_config = configuration["configuration"]["microscopes"][microscope_name]["stage"]["hardware"]
        if type(device_config) == ListProxy:
            #: str: Serial number of the stage.
            self.serial_number = str(device_config[device_id]["serial_number"])
        else:
            self.serial_number = device_config["serial_number"]

    def __del__(self):
        """Delete the KST Connection"""
        try:
            self.stop()
            self.kst_controller.KST_Close(self.serial_number)
        except AttributeError:
            pass

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
        for ax, i in self.axes_mapping.items():
            try:
                # need to request before we get the current position
                self.kst_controller.KST_RequestCurrentPosition(self.serial_number, i)
                pos = self.kst_controller.KST_GetCurrentPosition(self.serial_number, i)
                setattr(self, f"{ax}_pos", pos)
            except (
                self.kst_controller.TLFTDICommunicationError,
                self.kst_controller.TLDLLError,
                self.kst_controller.TLMotorDLLError,
            ):
                pass

        return self.get_position_dict()

    def move_axis_absolute(self, axis, abs_pos, wait_until_done=False):
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

        self.kst_controller.KST_MoveAbsolute(
            self.serial_number, self.axes_mapping[axis], int(axis_abs)
        )

        if wait_until_done:
            stage_pos, n_tries, i = -1e50, 10, 0
            target_pos = axis_abs
            while (stage_pos != target_pos) and (i < n_tries):
                # TODO: do we need to request before we get the current position
                # self.kst_controller.KST_RequestCurrentPosition(self.serial_number,
                # int(self.axes_mapping[axis]))
                stage_pos = self.kst_controller.KST_GetCurrentPosition(
                    self.serial_number, int(self.axes_mapping[axis])
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

    def stop(self):
        """Stop all stage channels move"""
        for i in self.KST_axes:
            self.kst_controller.KST_MoveStop(self.serial_number, i)
