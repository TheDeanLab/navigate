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

        # Default mapping from self.axes to corresponding KIM channels
        axes_mapping = {"x": 4, "y": 2, "z": 3, "f": 1}
        if not self.axes_mapping:
            self.axes_mapping = {axis: axes_mapping[axis] for axis in self.axes if axis in axes_mapping}

        self.kim_axes = list(self.axes_mapping.values())

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

        # Update internal dictionaries
        # self.update_position_dictionaries()

        return self.position_dict

    def move_axis_absolute(self, axis, move_dictionary):
        """
        Implement movement logic along a single axis.

        Example calls:

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
        bool
            Was the move successful?
        """
        if axis not in self.axes_mapping:
            return False
        
        axis_abs = self.get_abs_position(axis, move_dictionary)
        if axis_abs == -1e50:
            return False

        self.kim_controller.KIM_MoveAbsolute(
            self.serial_number, self.axes_mapping[axis], int(axis_abs)
        )
        return True

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """Move stage

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
            if ax not in move_dictionary:
                continue
            success = self.move_axis_absolute(ax, move_dictionary)
            if success and wait_until_done is True:
                stage_pos, n_tries, i = -1e50, 10, 0
                target_pos = move_dictionary[f"{ax}_abs"]
                while (stage_pos != target_pos) and (i < n_tries):
                    stage_pos = self.kim_controller.KIM_GetCurrentPosition(
                        self.serial_number, n
                    )
                    i += 1
                    time.sleep(0.01)
                if stage_pos != target_pos:
                    success = False
            result = result and success

        return result

    def stop(self):
        """Stop all stage channels move"""
        for i in self.kim_axes:
            self.kim_controller.KIM_MoveStop(self.serial_number, i)

