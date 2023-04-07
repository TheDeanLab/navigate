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

# Standard Imports
import logging
import time

# Third Party Imports

# Local Imports
from aslm.model.devices.stages.stage_base import StageBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class SyntheticStage(StageBase):
    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        super().__init__(microscope_name, device_connection, configuration, device_id)

        self.default_speed = 7.68 * 0.67

    def report_position(self):
        self.create_position_dict()
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
        axis_num : int
            The corresponding number of this axis on a PI stage.
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', 'x_min',
            etc. for one or more axes. Expects values in micrometers, except for theta,
            which is in degrees.

        Returns
        -------
        bool
            Was the move successful?
        """
        axis_abs = self.get_abs_position(axis, move_dictionary)
        if axis_abs == -1e50:
            return False

        # Move the stage
        setattr(self, f"{axis}_pos", axis_abs)
        return True

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for one
            or more axes. Expects values in micrometers, except for theta, which is
            in degrees.
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        success : bool
            Was the move successful?
        """
        success = False
        for ax in self.axes:
            if f"{ax}_abs" not in move_dictionary:
                continue
            success = self.move_axis_absolute(ax, move_dictionary)

        if wait_until_done is True:
            time.sleep(0.025)

        return success

    def zero_axes(self, list):
        for axis in list:
            try:
                exec("self.int_" + axis + "_pos_offset = -self." + axis + "_pos")
            except BaseException:
                logger.exception(f"Zeroing of axis: {axis} failed")
                print("Zeroing of axis: ", axis, "failed")

    def unzero_axes(self, list):
        for axis in list:
            try:
                exec("self.int_" + axis + "_pos_offset = 0")
            except BaseException:
                logger.exception(f"Unzeroing of axis: {axis} failed")
                print("Unzeroing of axis: ", axis, "failed")

    def load_sample(self):
        self.y_pos = self.y_load_position

    def unload_sample(self):
        self.y_pos = self.y_unload_position

    def get_position(self, axis):
        return getattr(self, f"{axis}_pos")
    
    def set_speed(self, velocity_dict):
        pass

    def get_speed(self, axis):
        return 1
    
    def scanr(self, start_position_mm, end_position_mm, enc_divide, axis='z'):
        pass

    def start_scan(self, axis):
        pass

    def stop_scan(self):
        pass
