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

# Standard Library Imports
import importlib
import logging
import time

# Third Party Imports

# Local Imports
from navigate.tools.decorators import log_initialization
from navigate.model.devices.stages.base import StageBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_MCLStage_connection(serialnum):
    """Build a connection to the Mad City Lab stage.

    Parameters
    ----------
    serialnum : int
        Serial number of the stage.

    Returns
    -------
    stage_connection : dict
        Dictionary containing the connection information for the stage.
    """
    mcl_controller = importlib.import_module("navigate.model.devices.APIs.mcl.madlib")

    # Initialize
    mcl_controller.MCL_GrabAllHandles()

    handle = mcl_controller.MCL_GetHandleBySerial(int(serialnum))

    stage_connection = {"handle": handle, "controller": mcl_controller}

    return stage_connection


@log_initialization
class MCLStage(StageBase):
    """Mad City Lab stage class."""

    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        """Initialize the MCL stage.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : mcl_controller
            Communication object for the stage.
        configuration : dict
            Dictionary containing the configuration information for the device.
        device_id : int
            Device ID.
        """
        super().__init__(
            microscope_name, device_connection, configuration, device_id
        )  # only initialize the focus axis

        # Mapping from self.axes to corresponding MCL channels
        if device_connection is not None:

            #: mcl_controller: MCL controller object.
            self.mcl_controller = device_connection["controller"]

            #: int: MCL handle.
            self.handle = device_connection["handle"]

        # Default axes mapping
        # the API maps axis to a number
        axes_mapping = {"x": "x", "y": "y", "z": "z", "f": "f", "theta": "aux"}
        if not self.axes_mapping:
            #: dict: Dictionary of software axes and their corresponding hardware axes.
            self.axes_mapping = {
                axis: axes_mapping[axis] for axis in self.axes if axis in axes_mapping
            }

    def __del__(self):
        """Close the connection to the stage."""
        try:
            self.mcl_controller.MCL_ReleaseHandle(self.handle)
        except self.mcl_controller.MadlibError as e:
            logger.exception(f"{e}")

    def report_position(self):
        """Report the position of the stage.

        Reports the position of the stage for all axes, and creates the hardware
        position dictionary.
        """
        for ax in self.axes_mapping:
            try:
                pos = self.mcl_controller.MCL_SingleReadN(
                    self.axes_mapping[ax], self.handle
                )
                setattr(self, f"{ax}_pos", pos)
            except self.mcl_controller.MadlibError as e:
                logger.debug(f"MCL - {e}")
                pass

        return self.get_position_dict()

    def move_axis_absolute(self, axis, abs_pos, wait_until_done=False):
        """Implement movement logic along a single axis.

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

        axis_abs = self.get_abs_position(axis, abs_pos)
        if axis_abs == -1e50:
            return False

        self.mcl_controller.MCL_SingleWriteN(
            axis_abs, self.axes_mapping[axis], self.handle
        )

        if wait_until_done:
            stage_pos, n_tries, i = -1e50, 10, 0
            while (abs(stage_pos - abs_pos) < 0.01) and (i < n_tries):
                stage_pos = self.mcl_controller.MCL_SingleReadN(axis, self.handle)
                i += 1
                time.sleep(0.01)
            if abs(stage_pos - abs_pos) > 0.01:
                return False
        return True

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """Move the stage to an absolute position.

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
        abs_pos_dict = self.verify_abs_position(move_dictionary)
        if not abs_pos_dict:
            return False

        result = True
        for ax in abs_pos_dict:
            success = self.move_axis_absolute(ax, abs_pos_dict[ax], wait_until_done)
            result = result and success

        return result
