"""
SyntheticStage
Dummy camera Stage for testing GUI and other functionalities. Based on the skeleton.
"""

import time
import numpy as np
from .StageBase import StageBase

class Stage(StageBase):
    def __init__(self, model, verbose):
        '''
        Initial setting of all positions
        self.x_pos, self.y_pos etc are the true axis positions, no matter whether
        the stages are zeroed or not.
        '''
        self.verbose = verbose
        self.x_pos = 0
        self.y_pos = 0
        self.z_pos = 0
        self.f_pos = 0
        self.theta_pos = 0

        '''
        Internal (software) positions
        '''
        self.int_x_pos = 0
        self.int_y_pos = 0
        self.int_z_pos = 0
        self.int_f_pos = 0
        self.int_theta_pos = 0

        '''
        Create offsets. It should be: int_x_pos = x_pos + int_x_pos_offset
        self.int_x_pos = self.x_pos + self.int_x_pos_offset
        OR x_pos = int_x_pos - int_x_pos_offset
        self.x_pos = self.int_x_pos - self.int_x_pos_offset
        '''
        self.int_x_pos_offset = 0
        self.int_y_pos_offset = 0
        self.int_z_pos_offset = 0
        self.int_f_pos_offset = 0
        self.int_theta_pos_offset = 0

        ''' 
        Setting movement limits: currently hardcoded: Units are in microns 
        '''
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
        self.x_rot_position = model.StageParameters['x_rot_position']
        self.y_rot_position = model.StageParameters['y_rot_position']
        self.z_rot_position = model.StageParameters['z_rot_position']

    def create_position_dict(self):
        return True

    def create_internal_position_dict(self):
        return True

    def report_position(self):
        return True

    def move_relative(self, dict, wait_until_done=False):
        return True

    def move_absolute(self, dict, wait_until_done=False):
        for axis in dict:
            assert axis in ['x_abs', 'y_abs', 'z_abs', 'theta_abs', 'f_abs']
        time.sleep(1)
        print('stage moved to', dict)
        return True

    def zero_axes(self, list):
        return True

    def unzero_axes(self, list):
        return True

    def load_sample(self):
        return True

    def unload_sample(self):
        return True

    def mark_rotation_position(self):
        return True

    def go_to_rotation_position(self, wait_until_done=False):
        return True



