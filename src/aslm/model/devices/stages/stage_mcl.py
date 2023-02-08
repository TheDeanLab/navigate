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

import importlib
import logging
import time

from aslm.model.devices.stages.stage_base import StageBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_MCLStage_connection(serialnum):
    """Build MCLStage Connection

    Parameters
    ----------
    serialnum : str
        The serial number of the MCL stage.

    Returns
    -------
    MCLStage
        The MCL stage.

    Examples
    --------
    >>> from aslm.model.devices.stages.stage_mcl import build_MCLStage_connection
    >>> mcl = build_MCLStage_connection("123456")
    """
    mcl_controller = importlib.import_module("aslm.model.devices.APIs.mcl.madlib")

    # Initialize
    mcl_controller.MCL_GrabAllHandles()

    handle = mcl_controller.MCL_GetHandleBySerial(int(serialnum))

    stage_connection = {"handle": handle, "controller": mcl_controller}

    return stage_connection


class MCLStage(StageBase):
    """MCLStage Class

    This class is a wrapper for the MCL stage API.

    Parameters
    ----------
    microscope_name : str
        The name of the microscope.
    device_connection : dict
        The device connection dictionary.
    configuration : dict
        The configuration dictionary.
    device_id : int, optional
        The device ID, by default 0

    Attributes
    ----------
    microscope_name : str
        The name of the microscope.
    device_connection : dict
        The device connection dictionary.
    configuration : dict
        The configuration dictionary.
    device_id : int
        The device ID.
    mcl_controller : module
        The MCL controller module.
    handle : int
        The MCL handle.

    Methods
    -------
    report_position()
        Reports the position of the stage for all axes, and creates the hardware
        position dictionary.
    move_axis_absolute(axis, axis_num, move_dictionary)
        Implement movement logic along a single axis.
    get_abs_position(axis, move_dictionary)
        Get the absolute position of an axis.
    move_absolute(move_dictionary)
        Move the stage to an absolute position.
    """

    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        super().__init__(
            microscope_name, device_connection, configuration, device_id
        )  # only initialize the focus axis

        # Mapping from self.axes to corresponding MCL channels
        if device_connection is not None:
            self.mcl_controller = device_connection["controller"]
            self.handle = device_connection["handle"]

    def report_position(self):
        """Reports the position of the stage for all axes, creates position dictionary.

        Parameters
        ----------
        None

        Returns
        -------
        dict
            The position dictionary.

        Examples
        --------
        >>> from aslm.model.devices.stages.stage_mcl import build_MCLStage_connection
        >>> mcl = build_MCLStage_connection("123456")
        >>> mcl.report_position()
        """
        for ax in self.axes:
            try:
                pos = self.mcl_controller.MCL_SingleReadN(ax, self.handle)
                setattr(self, f"{ax}_pos", pos)
            except self.mcl_controller.MadlibError as e:
                logger.debug(f"MCL - {e}")
                pass

        # Update internal dictionaries
        # self.update_position_dictionaries()

        return self.position_dict

    def move_axis_absolute(self, axis, axis_num, move_dictionary):
        """Implement movement logic along a single axis.

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary. For example, axis='x' corresponds to
            'x_abs', 'x_min', etc.
        axis_num : int
            The corresponding number of this axis on a PI stage.
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', 'x_min',
            etc. for one or more axes.
            Expects values in micrometers, except for theta, which is in degrees.

        Returns
        -------
        bool
            Was the move successful?

        Examples
        --------
        >>> from aslm.model.devices.stages.stage_mcl import build_MCLStage_connection
        >>> mcl = build_MCLStage_connection("123456")
        >>> mcl.move_axis_absolute("x", 1, {"x_abs": 100})
        """

        axis_abs = self.get_abs_position(axis, move_dictionary)
        if axis_abs == -1e50:
            return False

        self.mcl_controller.MCL_SingleWriteN(axis_abs, axis, self.handle)
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

        Examples
        --------
        >>> from aslm.model.devices.stages.stage_mcl import build_MCLStage_connection
        >>> mcl = build_MCLStage_connection("123456")
        >>> mcl.move_absolute({"x_abs": 100, "y_abs": 100})
        """

        for ax in self.axes:
            success = self.move_axis_absolute(ax, None, move_dictionary)
            if success and wait_until_done is True:
                stage_pos, n_tries, i = -1e50, 10, 0
                target_pos = move_dictionary[f"{ax}_abs"] - getattr(
                    self, f"int_{ax}_pos_offset", 0
                )  # TODO: should we default to 0?
                while (abs(stage_pos - target_pos) < 0.01) and (i < n_tries):
                    stage_pos = self.mcl_controller.MCL_SingleReadN(ax, self.handle)
                    i += 1
                    time.sleep(0.01)
                if abs(stage_pos - target_pos) > 0.01:
                    success = False

        return success

    def get_abs_position(self, axis, move_dictionary):
        """Get absolute position of an axis.

        Hack in a lack of bounds checking. TODO: Don't do this.

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary. For example, axis='x' corresponds to
            'x_abs', 'x_min', etc.
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', 'x_min',
            etc. for one or more axes. Expects values in micrometers, except for theta,
            which is in degrees.

        Returns
        -------
        float
            The absolute position of the axis.

        Examples
        --------
        >>> from aslm.model.devices.stages.stage_mcl import build_MCLStage_connection
        >>> mcl = build_MCLStage_connection("123456")
        >>> mcl.get_abs_position("x", {"x_abs": 100})
        """
        try:
            # Get all necessary attributes. If we can't we'll move to the error case.
            axis_abs = move_dictionary[f"{axis}_abs"] - getattr(
                self, f"int_{axis}_pos_offset", 0
            )  # TODO: should we default to 0?

            axis_min, axis_max = -1e6, 1e6

            # Check that our position is within the axis bounds, fail if it's not.
            if (axis_min > axis_abs) or (axis_max < axis_abs):
                log_string = (
                    f"Absolute movement stopped: {axis} limit would be reached!"
                    f"{axis_abs} is not in the range {axis_min} to {axis_max}."
                )
                logger.info(log_string)
                print(log_string)
                # Return a ridiculous value to make it clear we've failed.
                # This is to avoid returning a duck type.
                return -1e50
            return axis_abs
        except (KeyError, AttributeError):
            return -1e50
