"""
ASLM stage communication classes.
Class for mixed digital and analog modulation of laser devices.
Goal is to set the DC value of the laser intensity with the analog voltage, and then rapidly turn it on and off
with the digital signal.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

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
    def __init__(self, configuration, verbose):
        super().__init__(configuration, verbose)

    def report_position(self):
        self.create_position_dict()
        self.int_x_pos = self.x_pos + self.int_x_pos_offset
        self.int_y_pos = self.y_pos + self.int_y_pos_offset
        self.int_z_pos = self.z_pos + self.int_z_pos_offset
        self.int_f_pos = self.f_pos + self.int_f_pos_offset
        self.int_theta_pos = self.theta_pos + self.int_theta_pos_offset
        self.create_internal_position_dict()
        if self.verbose:
            print("Stage Position: ", self.int_position_dict)
        logger.debug(f"Stage Position:, {self.int_position_dict}")

    def move_relative(self, move_dictionary, wait_until_done=False):
        """
        Move relative method
        """

        if 'x_rel' in move_dictionary:
            x_rel = move_dictionary['x_rel']
            if (self.x_min <= self.x_pos +
                    x_rel) and (self.x_max >= self.x_pos + x_rel):
                self.x_pos = self.x_pos + x_rel
            else:
                print('Relative movement stopped: X limit would be reached!', 1000)
                logger.info("Relative movement stopped: X limit would be reached!, 1000")

        if 'y_rel' in move_dictionary:
            y_rel = move_dictionary['y_rel']
            if (self.y_min <= self.y_pos +
                    y_rel) and (self.y_max >= self.y_pos + y_rel):
                self.y_pos = self.y_pos + y_rel
            else:
                print('Relative movement stopped: Y limit would be reached!', 1000)
                logger.info("Relative movement stopped: Y limit would be reached!")

        if 'z_rel' in move_dictionary:
            z_rel = move_dictionary['z_rel']
            if (self.z_min <= self.z_pos +
                    z_rel) and (self.z_max >= self.z_pos + z_rel):
                self.z_pos = self.z_pos + z_rel
            else:
                print('Relative movement stopped: Z limit would be reached!', 1000)
                logger.info("Relative movement stopped: Z limit would be reached!")

        if 'theta_rel' in move_dictionary:
            theta_rel = move_dictionary['theta_rel']
            if (self.theta_min <= self.theta_pos +
                    theta_rel) and (self.theta_max >= self.theta_pos + theta_rel):
                self.theta_pos = self.theta_pos + theta_rel
            else:
                print(
                    'Relative movement stopped: Rotation limit would be reached!',
                    1000)
                logger.info("Relative movement stopped: Rotation limit would be reached!")

        if 'f_rel' in move_dictionary:
            f_rel = move_dictionary['f_rel']
            if (self.f_min <= self.f_pos +
                    f_rel) and (self.f_max >= self.f_pos + f_rel):
                self.f_pos = self.f_pos + f_rel
            else:
                print(
                    'Relative movement stopped: Focus limit would be reached!',
                    1000)
                logger.info("Relative movement stopped: Focus limit would be reached!")

        if wait_until_done is True:
            time.sleep(0.02)

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """
        Move absolute method
        """

        if 'x_abs' in move_dictionary:
            x_abs = move_dictionary['x_abs']
            x_abs = x_abs - self.int_x_pos_offset
            if (self.x_min <= x_abs) and (self.x_max >= x_abs):
                self.x_pos = x_abs
            else:
                logger.info("Absolute movement stopped: X limit would be reached!, 1000")
                print('Absolute movement stopped: X limit would be reached!', 1000)

        if 'y_abs' in move_dictionary:
            y_abs = move_dictionary['y_abs']
            y_abs = y_abs - self.int_y_pos_offset
            if (self.y_min <= y_abs) and (self.y_max >= y_abs):
                self.y_pos = y_abs
            else:
                logger.info("Absolute movement stopped: Y limit would be reached!, 1000")
                print('Absolute movement stopped: Y limit would be reached!', 1000)

        if 'z_abs' in move_dictionary:
            z_abs = move_dictionary['z_abs']
            z_abs = z_abs - self.int_z_pos_offset
            if (self.z_min <= z_abs) and (self.z_max >= z_abs):
                self.z_pos = z_abs
            else:
                logger.info("Absolute movement stopped: Z limit would be reached!, 1000")
                print('Absolute movement stopped: Z limit would be reached!', 1000)

        if 'f_abs' in move_dictionary:
            f_abs = move_dictionary['f_abs']
            f_abs = f_abs - self.int_f_pos_offset
            if (self.f_min <= f_abs) and (self.f_max >= f_abs):
                self.f_pos = f_abs
            else:
                logger.info("Absolute movement stopped: Focus limit would be reached!, 1000")
                print(
                    'Absolute movement stopped: Focus limit would be reached!',
                    1000)

        if 'theta_abs' in move_dictionary:
            theta_abs = move_dictionary['theta_abs']
            theta_abs = theta_abs - self.int_theta_pos_offset
            if (self.theta_min <= theta_abs) and (self.theta_max >= theta_abs):
                self.theta_pos = theta_abs
            else:
                logger.info("Absolute movement stopped: Rotation limit would be reached!, 1000")
                print(
                    'Absolute movement stopped: Rotation limit would be reached!',
                    1000)

        if wait_until_done is True:
            time.sleep(.25)

        if self.verbose:
            print('stage moved to ', move_dictionary)
        logger.debug(f"stage moved to, {move_dictionary}")

    def zero_axes(self, list):
        for axis in list:
            try:
                exec(
                    'self.int_' +
                    axis +
                    '_pos_offset = -self.' +
                    axis +
                    '_pos')
            except BaseException:
                logger.exception(f"Zeroing of axis: {axis} failed")
                print('Zeroing of axis: ', axis, 'failed')

    def unzero_axes(self, list):
        for axis in list:
            try:
                exec('self.int_' + axis + '_pos_offset = 0')
            except BaseException:
                logger.exception(f"Unzeroing of axis: {axis} failed")
                print('Unzeroing of axis: ', axis, 'failed')

    def load_sample(self):
        self.y_pos = self.configuration.StageParameters['y_load_position']

    def unload_sample(self):
        self.y_pos = self.configuration.StageParameters['y_unload_position']

