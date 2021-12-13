"""
SyntheticStage
Dummy camera Stage for testing GUI and other functionalities. Based on the skeleton.
"""

import time
import numpy as np
from .StageBase import StageBase

class Stage(StageBase):
    def __init__(self, session, verbose):
        '''
        Initial setting of all positions
        self.x_pos, self.y_pos etc are the true axis positions, no matter whether
        the stages are zeroed or not.
        '''
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
        #TODO: Reference configuration file?
        self.x_max = self.cfg.x_max
        self.x_min = self.cfg.x_min
        self.y_max = self.cfg.y_max
        self.y_min = self.cfg.y_min
        self.z_max = self.cfg.z_max
        self.z_min = self.cfg.z_min
        self.f_max = self.cfg.f_max
        self.f_min = self.cfg.f_min
        self.theta_max = self.cfg.theta_max
        self.theta_min = self.cfg.theta_min
        self.x_rot_position = self.cfg.x_rot_position
        self.y_rot_position = self.cfg.y_rot_position
        self.z_rot_position = self.cfg.z_rot_position

    def create_position_dict(self):
        return True

    def create_internal_position_dict(self):
        return True

    def report_position(self):
        return True

    def move_relative(self, dict, wait_until_done=False):
        return True

    def move_absolute(self, dict, wait_until_done=False):
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



