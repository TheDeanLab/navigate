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

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class StageBase:
    def __init__(self, model, verbose):
        self.verbose = verbose
        self.model = model

        """
        Initial setting of all positions
        self.x_pos, self.y_pos etc are the true axis positions, no matter whether
        the stages are zeroed or not.
        """
        self.x_pos = model.StageParameters['position']['x_pos']
        self.y_pos = model.StageParameters['position']['y_pos']
        self.z_pos = model.StageParameters['position']['z_pos']
        self.f_pos = model.StageParameters['position']['f_pos']
        self.theta_pos = model.StageParameters['position']['theta_pos']
        self.position_dict = {'x_pos': self.x_pos,
                              'y_pos': self.y_pos,
                              'z_pos': self.z_pos,
                              'f_pos': self.f_pos,
                              'theta_pos': self.theta_pos,
                              }
        """
        Internal (software) positions
        """
        self.int_x_pos = 0
        self.int_y_pos = 0
        self.int_z_pos = 0
        self.int_f_pos = 0
        self.int_theta_pos = 0
        self.int_position_dict = {'x_pos': self.int_x_pos,
                                  'y_pos': self.int_y_pos,
                                  'z_pos': self.int_z_pos,
                                  'f_pos': self.int_f_pos,
                                  'theta_pos': self.int_theta_pos,
                                  }
        """
        Create offsets. It should be: int_x_pos = x_pos + int_x_pos_offset
        self.int_x_pos = self.x_pos + self.int_x_pos_offset
        OR x_pos = int_x_pos - int_x_pos_offset
        self.x_pos = self.int_x_pos - self.int_x_pos_offset
        """
        self.int_x_pos_offset = 0
        self.int_y_pos_offset = 0
        self.int_z_pos_offset = 0
        self.int_f_pos_offset = 0
        self.int_theta_pos_offset = 0

        """
        Setting movement limits: currently hardcoded: Units are in microns
        """
        self.x_max = model.StageParameters['x_max']
        self.x_min = model.StageParameters['x_min']
        self.y_max = model.StageParameters['y_max']
        self.y_min = model.StageParameters['y_min']
        self.z_max = model.StageParameters['z_max']
        self.z_min = model.StageParameters['z_min']
        self.f_max = model.StageParameters['f_max']
        self.f_min = model.StageParameters['f_min']
        self.theta_max = model.StageParameters['theta_max']
        self.theta_min = model.StageParameters['theta_min']

        # Sample Position When Rotating
        self.x_rot_position = model.StageParameters['x_rot_position']
        self.y_rot_position = model.StageParameters['y_rot_position']
        self.z_rot_position = model.StageParameters['z_rot_position']

        # Starting Position of Focusing Device
        self.startfocus = model.StageParameters['startfocus']

    def create_position_dict(self):
        pass

    def create_internal_position_dict(self):
        pass

    def report_position(self):
        pass

    def move_relative(self, dict, wait_until_done=False):
        pass

    def move_absolute(self, dict, wait_until_done=False):
        pass

    def stop(self):
        pass

    def zero_axes(self, list):
        pass

    def unzero_axes(self, list):
        pass

    def load_sample(self):
        pass

    def unload_sample(self):
        pass

    def mark_rotation_position(self):
        pass

    def go_to_rotation_position(self, wait_until_done=False):
        pass



