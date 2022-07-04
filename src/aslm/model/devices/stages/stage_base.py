"""Class for mixed digital and analog modulation of laser devices.
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
    r"""StageBase Parent Class

    Attributes
    ----------
    configuration : Session
        Global configuration of the microscope
    verbose : bool
        Verbosity
    x_pos : float
        True x position
    y_pos : float
        True y position
    z_pos : float
        True z position
    f_pos : float
        True focus position
    theta_pos : float
        True rotation position
    position_dict : dict
        Dictionary of true stage positions
    int_x_pos : float
        Software x position
    int_y_pos : float
        Software y position
    int_z_pos : float
        Software z position
    int_f_pos : float
        Software focus position
    int_theta_pos : float
        Software theta position
    int_position_dict : dict
        Dictionary of software stage positions
    int_x_pos_offset : float
        x position offset
    int_y_pos_offset : float
        y position offset
    int_z_pos_offset : float
        z position offset
    int_f_pos_offset : float
        focus position offset
    int_theta_pos_offset : float
        theta position offset
    x_max : float
        Max x position
    y_max : float
        Max y position
    z_max : float
        Max y position
    f_max : float
        Max focus positoin
    theta_max : float
        Max rotation position
    x_min : float
        Min x position
    y_min : float
        Min y position
    z_min : float
        Min y position
    f_min : float
        Min focus positoin
    theta_min : float
        Min rotation position
    x_rot_position : float
        Location to move the specimen in x while rotating.
    y_rot_position : float
        Location to move the specimen in y while rotating.
    z_rot_position : float
        Location to move the specimen in z while rotating.
    startfocus : float
        Location to initialize the focusing stage to.

    Methods
    -------
    create_position_dict()
        Creates a dictionary with the hardware stage positions.
    create_internal_position_dict()
        Creates a dictionary with the software stage positions.
    """
    def __init__(self, configuration, verbose):
        self.verbose = verbose
        self.configuration = configuration

        r"""Initial setting for all positions
        self.x_pos, self.y_pos etc are the true axis positions, no matter whether
        the stages are zeroed or not.
        """
        self.x_pos = configuration.StageParameters['position']['x_pos']
        self.y_pos = configuration.StageParameters['position']['y_pos']
        self.z_pos = configuration.StageParameters['position']['z_pos']
        self.f_pos = configuration.StageParameters['position']['f_pos']
        self.theta_pos = configuration.StageParameters['position']['theta_pos']
        self.position_dict = {'x_pos': self.x_pos,
                              'y_pos': self.y_pos,
                              'z_pos': self.z_pos,
                              'f_pos': self.f_pos,
                              'theta_pos': self.theta_pos,
                              }

        r"""Internal (software) positions"""
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
        r"""Create offsets. It should be: int_x_pos = x_pos + int_x_pos_offset
        self.int_x_pos = self.x_pos + self.int_x_pos_offset
        OR x_pos = int_x_pos - int_x_pos_offset
        self.x_pos = self.int_x_pos - self.int_x_pos_offset
        """
        self.int_x_pos_offset = 0
        self.int_y_pos_offset = 0
        self.int_z_pos_offset = 0
        self.int_f_pos_offset = 0
        self.int_theta_pos_offset = 0

        r"""Stage movement limits: currently hardcoded: Units are in microns"""
        self.x_max = configuration.StageParameters['x_max']
        self.x_min = configuration.StageParameters['x_min']
        self.y_max = configuration.StageParameters['y_max']
        self.y_min = configuration.StageParameters['y_min']
        self.z_max = configuration.StageParameters['z_max']
        self.z_min = configuration.StageParameters['z_min']
        self.f_max = configuration.StageParameters['f_max']
        self.f_min = configuration.StageParameters['f_min']
        self.theta_max = configuration.StageParameters['theta_max']
        self.theta_min = configuration.StageParameters['theta_min']

        # Sample Position When Rotating
        self.x_rot_position = configuration.StageParameters['x_rot_position']
        self.y_rot_position = configuration.StageParameters['y_rot_position']
        self.z_rot_position = configuration.StageParameters['z_rot_position']

        # Starting Position of Focusing Device
        self.startfocus = configuration.StageParameters['startfocus']

    def create_position_dict(self):
        r"""Creates a dictionary with the hardware stage positions.
        """
        self.position_dict = {'x_pos': self.x_pos,
                              'y_pos': self.y_pos,
                              'z_pos': self.z_pos,
                              'f_pos': self.f_pos,
                              'theta_pos': self.theta_pos,
                              }

    def create_internal_position_dict(self):
        r"""Creates a dictionary with the software stage positions.
        Internal position includes the offset for each stage position.
        e.g, int_x_pos = x_pos + int_x_pos_offset
        """
        self.int_position_dict = {'x_pos': self.int_x_pos,
                                  'y_pos': self.int_y_pos,
                                  'z_pos': self.int_z_pos,
                                  'f_pos': self.int_f_pos,
                                  'theta_pos': self.int_theta_pos,
                                  }

