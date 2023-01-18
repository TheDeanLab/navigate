# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

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

from aslm.model.devices.stages.stage_base import StageBase

import importlib
import logging
import time

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_TLKIMStage_connection(serialnum):
    kim_controller = importlib.import_module(
        "aslm.model.devices.APIs.thorlabs.kcube_inertial"
    )

    # Initialize
    kim_controller.TLI_BuildDeviceList()

    # Cheat for now by opening just the first stage of this type.
    # TODO: Pass this from the configuration file
    available_serialnum = kim_controller.TLI_GetDeviceListExt()[0]
    assert str(available_serialnum) == str(serialnum)
    kim_controller.KIM_Open(str(serialnum))
    return kim_controller


class TLKIMStage(StageBase):
    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        super().__init__(
            microscope_name, device_connection, configuration, device_id
        )  # only initialize the focus axis

        # Mapping from self.axes to corresponding KIM channels
        self.kim_axes = [1]

        if device_connection is not None:
            self.kim_controller = device_connection

        self.serial_number = str(
            configuration["configuration"]["microscopes"][microscope_name]["stage"][
                "hardware"
            ][device_id]["serial_number"]
        )

    def __del__(self):
        try:
            self.stop()
            self.kim_controller.KIM_Close(self.serial_number)
        except AttributeError:
            pass

    def report_position(self):
        """
        # Reports the position of the stage for all axes, and creates the hardware
        # position dictionary.
        """
        for i, ax in zip(self.kim_axes, self.axes):
            try:
                # need to request before we get the current position
                err = self.kim_controller.KIM_RequestCurrentPosition(
                    self.serial_number, i
                )
                pos = self.kim_controller.KIM_GetCurrentPosition(self.serial_number, i)
                setattr(self, f"{ax}_pos", pos)
            except (
                self.kim_controller.TLFTDICommunicationError,
                self.kim_controller.TLDLLError,
                self.kim_controller.TLMotorDLLError,
            ):
                pass

        # Update internal dictionaries
        # self.update_position_dictionaries()

        return self.position_dict

    def move_axis_absolute(self, axis, axis_num, move_dictionary):
        """
        Implement movement logic along a single axis.

        Example calls:

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary. For example, axis='x' corresponds to 'x_abs', 'x_min', etc.
        axis_num : int
            The corresponding number of this axis on a PI stage.
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', 'x_min', etc. for one or more axes.
            Expects values in micrometers, except for theta, which is in degrees.

        Returns
        -------
        bool
            Was the move successful?
        """

        axis_abs = self.get_abs_position(axis, move_dictionary)
        if axis_abs == -1e50:
            return False

        self.kim_controller.KIM_MoveAbsolute(
            self.serial_number, axis_num, int(axis_abs)
        )
        return True

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for one or more axes.
            Expects values in micrometers, except for theta, which is in degrees.
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        success : bool
            Was the move successful?
        """

        for ax, n in zip(self.axes, self.kim_axes):
            success = self.move_axis_absolute(ax, n, move_dictionary)
            if success and wait_until_done is True:
                stage_pos, n_tries, i = -1e50, 10, 0
                target_pos = move_dictionary[f"{ax}_abs"] - getattr(
                    self, f"int_{ax}_pos_offset", 0
                )  # TODO: should we default to 0?
                while (stage_pos != target_pos) and (i < n_tries):
                    stage_pos = self.kim_controller.KIM_GetCurrentPosition(
                        self.serial_number, n
                    )
                    i += 1
                    time.sleep(0.01)
                if stage_pos != target_pos:
                    success = False

        return success

    def stop(self):
        for i in self.kim_axes:
            self.kim_controller.KIM_MoveStop(self.serial_number, i)

    def get_abs_position(self, axis, move_dictionary):
        """ "
        Hack in a lack of bounds checking. TODO: Don't do this.
        """
        try:
            # Get all necessary attributes. If we can't we'll move to the error case.
            axis_abs = move_dictionary[f"{axis}_abs"] - getattr(
                self, f"int_{axis}_pos_offset", 0
            )  # TODO: should we default to 0?

            # axis_min, axis_max = getattr(self, f"{axis}_min"), getattr(self, f"{axis}_max")
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
