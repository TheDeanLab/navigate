"""
ASLM configuration controller.

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
import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ASLM_Configuration_Controller:
    def __init__(self, configuration):
        self.configuration = configuration

    def get_channels_info(self, verbose=False):
        """
        # Populates the channel combobox with the channels that are available in the model.configuration
        """

        setting = {'laser': self.get_lasers_info(verbose), 'filter': list(
            self.configuration.FilterWheelParameters['available_filters'].keys()), }
        return setting

    def get_lasers_info(self, verbose=False):
        """
        # Populates the laser combobox with the lasers that are available in the model.configuration
        """
        number_of_lasers = int(
            self.configuration.LaserParameters['number_of_lasers'])
        laser_list = []
        for i in range(number_of_lasers):
            laser_wavelength = self.configuration.LaserParameters['laser_' + str(
                i) + '_wavelength']
            laser_list.append(laser_wavelength)
        if verbose:
            print('Laser list: ', laser_list)
        return laser_list

    def get_pixels(self, verbose=False):
        """
        # Gets default pixel values from camera
        """
        return [self.configuration.CameraParameters['x_pixels'],
                self.configuration.CameraParameters['y_pixels']]

    def get_framerate(self, verbose=False):
        '''
        # Gets default framerate info from camera
        '''
        pass  # TODO Kevin this is where you pull in and then calculate the info from the config file to initializing the framerate widgets

    def get_stage_position(self):
        """
        # Returns the current position of the stage
        """
        stage_position = self.configuration.StageParameters['position']
        position = {
            'x': stage_position['x_pos'],
            'y': stage_position['y_pos'],
            'z': stage_position['z_pos'],
            'theta': stage_position['theta_pos'],
            'f': stage_position['f_pos']
        }
        return position

    def get_stage_step(self):
        """
        # Returns the step size of the stage
        """
        steps = {
            'x': self.configuration.StageParameters['xy_step'],
            'z': self.configuration.StageParameters['z_step'],
            'theta': self.configuration.StageParameters['theta_step'],
            'f': self.configuration.StageParameters['f_step']
        }
        return steps

    def get_stage_position_limits(self, suffix):
        """
        # Returns the position limits of the stage
        """
        axis = ['x', 'y', 'z', 'theta', 'f']
        position_limits = {}
        for a in axis:
            position_limits[a] = self.configuration.StageParameters[a + suffix]
        return position_limits

    def get_etl_info(self):
        """
        # return delay_percent, pulse_percent
        """
        temp = {
            'remote_focus_l_delay_percent': self.configuration.LaserParameters['laser_l_delay_percent'],
            'remote_focus_l_pulse_percent': self.configuration.LaserParameters['laser_l_pulse_percent'],
            'remote_focus_r_delay_percent': self.configuration.LaserParameters['laser_r_delay_percent'],
            'remote_focus_r_pulse_percent': self.configuration.LaserParameters['laser_r_pulse_percent']}
        return temp
