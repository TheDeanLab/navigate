# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
from typing import Any, Dict

# Third Party Imports
from pipython import GCSDevice, pitools, GCSError

# Local Imports
from navigate.model.devices.stages.base import StageBase
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_PIStage_connection(controller_name, serial_number, stages, reference_modes):
    """Connect to the Physik Instrumente (PI) Stage

    Parameters
    ----------
    controller_name : str
        Name of the controller, e.g., "C-863.11"
    serial_number : str
        Serial number of the controller, e.g., "0112345678"
    stages : str
        Stages to connect to, e.g., "M-111.1DG"
    reference_modes : str
        Reference modes for the stages, e.g., "FRF"

    Returns
    -------
    stage_connection : dict
        Dictionary containing the pi_tools and pi_device objects
    """
    pi_stages = stages.split()
    pi_reference_modes = reference_modes.split()
    pi_tools = pitools
    pi_device = GCSDevice(controller_name)
    pi_device.ConnectUSB(serialnum=serial_number)
    pi_tools.startup(
        pi_device, stages=list(pi_stages), refmodes=list(pi_reference_modes)
    )

    # wait until pi_device is ready
    block_flag = True
    while block_flag:
        if pi_device.IsControllerReady():
            block_flag = False
        else:
            time.sleep(0.1)

    stage_connection = {"pi_tools": pi_tools, "pi_device": pi_device}
    return stage_connection


@log_initialization
class PIStage(StageBase):
    """Physik Instrumente (PI) Stage Class"""

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
        device_id: int = 0,
    ):
        """
        Initialize the Physik Instrumente (PI) Stage Class

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : Any
            Hardware device to connect to
        configuration : Dict[str, Any]
            Global configuration of the microscope
        device_id : int
            Unique identifier for the device, by default 0
        """

        super().__init__(microscope_name, device_connection, configuration, device_id)

        # Default mapping from self.axes to corresponding PI axis labelling
        axes_mapping = {"x": 1, "y": 2, "z": 3, "f": 5, "theta": 4}

        if device_connection is not None:
            #: object: Physik Instrumente (PI) device
            self.pi_tools = device_connection["pi_tools"]

            #: object: Physik Instrumente (PI) device
            self.pi_device = device_connection["pi_device"]

            # Non-default axes_mapping
            axes_mapping = {x: y for x, y in zip(self.axes, self.pi_device.axes)}

        if not self.axes_mapping:
            self.axes_mapping = {
                axis: axes_mapping[axis] for axis in self.axes if axis in axes_mapping
            }

        #: list: List of PI axes available.
        self.pi_axes = list(self.axes_mapping.values())

    def __del__(self) -> None:
        """Delete the PI Connection

        Raises
        ------
        GCSError
            If the PI connection cannot be closed
        """
        try:
            if hasattr(self, "pi_device"):
                self.stop()
                self.pi_device.CloseConnection()
            logger.debug("PI connection closed")
        except (AttributeError, GCSError) as e:
            print("Error while disconnecting the PI stage")
            logger.exception(f"Error while disconnecting the PI stage - {e}")
            raise e

    def report_position(self):
        """Reports the position for all axes, and create position dictionary.

        Positions from Physik Instrumente device are in millimeters

        Returns
        -------
        position_dict : dict
            Dictionary containing the position of all axes
        """
        for _ in range(10):
            try:
                positions = self.pi_device.qPOS(self.pi_axes)

                # convert to um
                for ax, n in self.axes_mapping.items():
                    pos = positions[str(n)]
                    if ax != "theta":
                        pos = round(pos * 1000, 2)
                    setattr(self, f"{ax}_pos", pos)
                break
            except GCSError as e:
                print("Physik Instrumente: Failed to report position")
                logger.exception(f"report_position failed - {e}")
                time.sleep(0.01)

        return self.get_position_dict()

    def move_axis_absolute(self, axis, abs_pos, wait_until_done=False):
        """Move stage along a single axis.

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

        # Move the stage
        try:
            axis_num = self.axes_mapping[axis]
            pos = axis_abs
            if axis != "theta":
                pos /= 1000  # convert to mm
            self.pi_device.MOV({axis_num: pos})
        except GCSError as e:
            logger.exception(f"move_axis_absolute failed - {e}")
            return False

        if wait_until_done is True:
            return self.wait_on_target(axes=[axis_num])

        return True

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """Move Absolute Method.

        XYZF Values are converted to millimeters for PI API.
        Theta Values are not converted.

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for one
            or more axes. Expect values in micrometers, except for theta, which is
            in degrees.
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        bool
            Was the move successful?
        """
        abs_pos_dict = self.verify_abs_position(move_dictionary)
        if not abs_pos_dict:
            return False

        pos_dict = {
            self.axes_mapping[axis]: abs_pos_dict[axis] / 1000
            if axis != "theta"
            else abs_pos_dict[axis]
            for axis in abs_pos_dict
        }

        try:
            self.pi_device.MOV(pos_dict)
        except GCSError as e:
            logger.exception(f"move_axis_absolute failed - {e}")
            return False

        if wait_until_done is True:
            return self.wait_on_target(axes=list(pos_dict.keys()))
        return True

    def stop(self):
        """Stop all stage movement abruptly."""
        try:
            self.pi_device.STP(noraise=True)
        except GCSError as e:
            logger.exception(f"Stage stop failed - {e}")

    def wait_on_target(self, axes=None):
        """Wait on target

        Parameters
        ----------
        axes : list or tuple or str
            Axes to wait for or None to wait for all axes.

        Returns
        -------
        bool
            Was the wait on target delay successful?
        """
        try:
            self.pi_tools.waitontarget(
                self.pi_device, axes=axes, timeout=10.75, polldelay=0.01
            )
        except GCSError as e:
            print("Wait on target failed")
            logger.exception(f"Wait on target failed - {e}")
            return False
        except Exception as e:
            logger.exception(f"Wait on target timeout error - {e}")
            return False
        return True
