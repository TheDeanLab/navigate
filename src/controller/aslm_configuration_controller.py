class ASLM_Configuration_Controller:
    def __init__(self, configuration):
        self.configuration = configuration

    def get_channels_info(self, verbose=False):
        """
        # Populates the channel combobox with the channels that are available in the model.configuration
        """

        setting = {
            'laser': self.get_lasers_info(verbose),
            'filter': list(self.configuration.FilterWheelParameters['available_filters'].keys()),
            'camera_exposure_time': self.configuration.CameraParameters['exposure_time']
        }
        return setting

    def get_lasers_info(self, verbose=False):
        """
        # Populates the laser combobox with the lasers that are available in the model.configuration
        """
        number_of_lasers = int(self.configuration.LaserParameters['number_of_lasers'])
        laser_list = []
        for i in range(number_of_lasers):
            laser_wavelength = self.configuration.LaserParameters['laser_'+str(i)+'_wavelength']
            laser_list.append(laser_wavelength)
        if verbose:
            print('Laser list: ', laser_list)
        return laser_list

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
            position_limits[a] = self.configuration.StageParameters[a+suffix]
        return position_limits

    def get_etl_info(self):
        """
        # return delay_percent, pulse_percent
        """
        temp = {
            'remote_focus_l_delay_percent': self.configuration.LaserParameters['laser_l_delay_percent'],
            'remote_focus_l_pulse_percent': self.configuration.LaserParameters['laser_l_pulse_percent'],
            'remote_focus_r_delay_percent': self.configuration.LaserParameters['laser_r_delay_percent'],
            'remote_focus_r_pulse_percent': self.configuration.LaserParameters['laser_r_pulse_percent']
        }
        return temp
