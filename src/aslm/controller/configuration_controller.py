"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
# """

# Standard Library Imports
import logging

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ConfigurationController:
    def __init__(self, configuration):
        self.configuration = configuration
        self.microscope_name = None
        self.microscope_config = None

        self.change_microscope()

    def change_microscope(self)->bool:
        r"""Get the new microscope configuration dict according to the name
        
        Returns
        -------
        result: bool
        """
        microscope_name = self.configuration['experiment']['MicroscopeState']['microscope_name']
        assert(microscope_name in self.configuration['configuration']['microscopes'].keys())
        
        if self.microscope_name == microscope_name:
            return False

        self.microscope_config = self.configuration['configuration']['microscopes'][microscope_name]
        self.microscope_name = microscope_name
        return True

    def get_microscope_configuration_dict(self):
        r"""Return microscope configuration dict
        
        Returns
        -------
        microscope_configuration_dict: dict
        """
        return self.microscope_config

    @property
    def channels_info(self):
        r"""Populate the channel combobox with the channels that are available in the configuration

        Returns
        -------
        setting : dict
            Channel settings, e.g. {
                'laser': ['488nm', '562nm', '642nm'],
                'filter': ['Empty-Alignment', 'GFP - FF01-515/30-32', '...}
        """
        if self.microscope_config is None:
            return {}

        setting = {'laser': self.lasers_info, 
                   'filter': list(self.microscope_config['filter_wheel']['available_filters'].keys())}
        return setting

    @property
    def lasers_info(self):
        r"""Populate the laser combobox with the lasers that are available in the configuration

        Returns
        -------
        laser_list : list
            List of lasers, e.g. ['488nm', '562nm', '642nm']
        """
        if self.microscope_config is None:
            return []
        
        return [str(laser['wavelength'])+'nm' for laser in self.microscope_config['lasers']]

    @property
    def camera_config_dict(self):
        r"""Get camera configuration dict

        Returns
        -------
        camera_setting: dict
            Camera Setting, e.g. {

            }
        """
        if self.microscope_config is not None:
            return self.microscope_config['camera']
        return None

    @property
    def camera_pixels(self):
        r"""Get default pixel values from camera

        Returns
        -------
        x_pixels : int
            Number of x pixels
        y_pixels : int
            Number of y pixels
        """
        if self.microscope_config is None:
            return [2048, 2048]
        
        return [self.microscope_config['camera']['x_pixels'],
                self.microscope_config['camera']['y_pixels']]

    @property
    def stage_default_position(self):
        r"""Get current position of the stage

        Returns
        -------
        position : dict
            Dictionary with x, y, z, theta, and f positions.
        """
        if self.microscope_config is not None:
            stage_position = self.microscope_config['stage']['position']
            position = {
                'x': stage_position['x_pos'],
                'y': stage_position['y_pos'],
                'z': stage_position['z_pos'],
                'theta': stage_position['theta_pos'],
                'f': stage_position['f_pos']
            }
        else:
            position = {
                'x': 0,
                'y': 0,
                'z': 0,
                'theta': 0,
                'f': 0
            }
        return position

    @property
    def stage_step(self):
        r"""Get the step size of the stage

        Returns
        -------
        steps : dict
            Step size in x (same step size for y), z, theta, and f.
        """
        if self.microscope_config is not None:
            stage_dict = self.microscope_config['stage']
            steps = {
                'x': stage_dict['x_step'],
                'y': stage_dict['y_step'],
                'z': stage_dict['z_step'],
                'theta': stage_dict['theta_step'],
                'f': stage_dict['f_step']
            }
        else:
            steps = {'x': 10, 'y': 10, 'z': 10, 'theta': 10, 'f': 10}
        return steps

    def get_stage_position_limits(self, suffix):
        r"""Return the position limits of the stage

        Parameters
        ----------
        suffix : str
            '_min' or '_max'

        Returns
        -------
        position_limits : dict
            Depending on suffix, min or max stage limits, e.g. {'x': 2000, 'y': 2000, 'z': 2000, 'theta': 0, 'f': 2000}.

        """
        axis = ['x', 'y', 'z', 'theta', 'f']
        if self.microscope_config is not None:
            stage_dict = self.microscope_config['stage']
            position_limits = {}
            for a in axis:
                position_limits[a] = stage_dict[a + suffix]
        else:
            for a in axis:
                position_limits[a] = 0 if suffix == '_min' else 100
        return position_limits

    @property
    def remote_focus_dict(self):
        r"""Return delay_percent, pulse_percent.

        Returns
        -------
        remote_focus_parameters : dict
            Dictionary with the remote focus percent delay and pulse percent.
        """
        if self.microscope_config is not None:
            return self.microscope_config['remote_focus_device']
        
        return None

    @property
    def galvo_parameter_dict(self):
        if self.microscope_config is not None:
            # Inject names into unnammed galvos
            for i, galvo in enumerate(self.microscope_config['galvo']):
                if galvo.get('name') is None:
                    self.microscope_config['galvo'][i]['name'] = f"Galvo {i}"
            return self.microscope_config['galvo']
        return None

    @property
    def daq_sample_rate(self):
        if self.microscope_config is not None:
            return self.microscope_config['daq']['sample_rate']
        return 100000

    @property
    def filter_wheel_setting_dict(self):
        if self.microscope_config is not None:
            return self.microscope_config['filter_wheel']
        return None

    @property
    def stage_setting_dict(self):
        if self.microscope_config is not None:
            return self.microscope_config['stage']
        return None

    @property
    def number_of_channels(self):
        if self.microscope_config is not None:
            return self.configuration['configuration']['gui']['channels']['count']
        return 5
    