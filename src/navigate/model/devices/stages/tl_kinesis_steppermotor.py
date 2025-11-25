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
          type: KINESIS
          serial_number: "/dev/ttyUSB1"
          axes: [f]
          axes_mapping: [1]
          steps_per_um: 2008.623
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
from navigate.model.devices.APIs.thorlabs.pykinesis_controller import KinesisStage
# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

SLEEP_AFTER_WAIT = 0.100

def build_KINESIS_Stage_connection(serial_number):
    """Connect to the Thorlabs KST Stage

    Parameters
    ----------
    serialnum : str
        Serial number of the stage.

    Returns
    -------
    kin_controller
        Thorlabs KST Stage controller
    """
    kstage = KinesisStage(serial_number, False)
    if not kstage.stage.is_opened():
        logger.error("KinesisStage connection failed.")
        raise Exception("Kinesis stage connection failed.")
    return kstage


@log_initialization
class TLKINStage(StageBase):
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
            self.device_unit_scale = device_config[device_id]["steps_per_um"]
        else:
            self.serial_number = device_config["serial_number"]
            self.device_unit_scale = device_config["steps_per_um"]

        if device_connection is not None:
            #: object: Thorlabs KST Stage controller
            self.kin_controller = device_connection
        else:
            self.kin_controller = build_KINESIS_Stage_connection(self.serial_number)

    def __del__(self):
        """Delete the KST Connection"""
        try:
            self.kin_controller.stop()
            self.kin_controller.close()
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
        try:
            pos = self.kin_controller.get_current_position(self.device_unit_scale)
            setattr(self, f"{self.axes[0]}_pos", pos)
        except Exception:
            pass

        return self.get_position_dict()

    def move_axis_absolute(self, axes, abs_pos, wait_until_done=True):
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
        self.kin_controller.move_to_position(axis_abs,
                                             self.device_unit_scale, 
                                             wait_until_done)
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
        if SLEEP_AFTER_WAIT:
            time.sleep(SLEEP_AFTER_WAIT)
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
        self.kin_controller.move_to_position(position,
                                             self.device_unit_scale, 
                                             wait_until_done)
        if SLEEP_AFTER_WAIT:
            time.sleep(SLEEP_AFTER_WAIT)
        
    def run_homing(self):
        """Run homing sequence."""
        self.kin_controller.home_stage()
        # move to mid travel
        self.move_to_position(12.5, wait_until_done=True)

    def stop(self):
        """
        Stop all stage channels move
        """
        self.kin_controller.stop()
