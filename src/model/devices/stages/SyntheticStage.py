"""
SyntheticStage
Dummy camera Stage for testing GUI and other functionalities. Based on the skeleton.
"""

import time
from .StageBase import StageBase


class Stage(StageBase):
    def __init__(self, model, verbose):
        super().__init__(model, verbose)

    def create_position_dict(self):
        self.position_dict = {'x_pos': self.x_pos,
                              'y_pos': self.y_pos,
                              'z_pos': self.z_pos,
                              'f_pos': self.f_pos,
                              'theta_pos': self.theta_pos,
                              }

    def create_internal_position_dict(self):
        self.int_position_dict = {'x_pos': self.int_x_pos,
                                  'y_pos': self.int_y_pos,
                                  'z_pos': self.int_z_pos,
                                  'f_pos': self.int_f_pos,
                                  'theta_pos': self.int_theta_pos,
                                  }

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

    def move_relative(self, move_dictionary, wait_until_done=False):
        """
        Move relative method
        """

        if 'x_rel' in move_dictionary:
            x_rel = move_dictionary['x_rel']
            if (self.x_min <= self.x_pos + x_rel) and (self.x_max >= self.x_pos + x_rel):
                self.x_pos = self.x_pos + x_rel
            else:
                print('Relative movement stopped: X limit would be reached!', 1000)

        if 'y_rel' in move_dictionary:
            y_rel = move_dictionary['y_rel']
            if (self.y_min <= self.y_pos + y_rel) and (self.y_max >= self.y_pos + y_rel):
                self.y_pos = self.y_pos + y_rel
            else:
                print('Relative movement stopped: Y limit would be reached!', 1000)

        if 'z_rel' in move_dictionary:
            z_rel = move_dictionary['z_rel']
            if (self.z_min <= self.z_pos + z_rel) and (self.z_max >= self.z_pos + z_rel):
                self.z_pos = self.z_pos + z_rel
            else:
                print('Relative movement stopped: Z limit would be reached!', 1000)

        if 'theta_rel' in move_dictionary:
            theta_rel = move_dictionary['theta_rel']
            if (self.theta_min <= self.theta_pos + theta_rel) and (self.theta_max >= self.theta_pos + theta_rel):
                self.theta_pos = self.theta_pos + theta_rel
            else:
                print('Relative movement stopped: Rotation limit would be reached!', 1000)

        if 'f_rel' in move_dictionary:
            f_rel = move_dictionary['f_rel']
            if (self.f_min <= self.f_pos + f_rel) and (self.f_max >= self.f_pos + f_rel):
                self.f_pos = self.f_pos + f_rel
            else:
                print('Relative movement stopped: Focus limit would be reached!', 1000)

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
                print('Absolute movement stopped: X limit would be reached!', 1000)

        if 'y_abs' in move_dictionary:
            y_abs = move_dictionary['y_abs']
            y_abs = y_abs - self.int_y_pos_offset
            if (self.y_min <= y_abs) and (self.y_max >= y_abs):
                self.y_pos = y_abs
            else:
                print('Absolute movement stopped: Y limit would be reached!', 1000)

        if 'z_abs' in move_dictionary:
            z_abs = move_dictionary['z_abs']
            z_abs = z_abs - self.int_z_pos_offset
            if (self.z_min <= z_abs) and (self.z_max >= z_abs):
                self.z_pos = z_abs
            else:
                print('Absolute movement stopped: Z limit would be reached!', 1000)

        if 'f_abs' in move_dictionary:
            f_abs = move_dictionary['f_abs']
            f_abs = f_abs - self.int_f_pos_offset
            if (self.f_min <= f_abs) and (self.f_max >= f_abs):
                self.f_pos = f_abs
            else:
                print('Absolute movement stopped: Focus limit would be reached!', 1000)

        if 'theta_abs' in move_dictionary:
            theta_abs = move_dictionary['theta_abs']
            theta_abs = theta_abs - self.int_theta_pos_offset
            if (self.theta_min <= theta_abs) and (self.theta_max >= theta_abs):
                self.theta_pos = theta_abs
            else:
                print('Absolute movement stopped: Rotation limit would be reached!', 1000)

        if wait_until_done is True:
            time.sleep(.25)

        if self.verbose:
            print('stage moved to ', move_dictionary)

    def zero_axes(self, list):
        for axis in list:
            try:
                exec('self.int_' + axis + '_pos_offset = -self.' + axis + '_pos')
            except:
                print('Zeroing of axis: ', axis, 'failed')

    def unzero_axes(self, list):
        for axis in list:
            try:
                exec('self.int_' + axis + '_pos_offset = 0')
            except:
                print('Unzeroing of axis: ', axis, 'failed')

    def load_sample(self):
        self.y_pos = self.model.StageParameters['y_load_position']

    def unload_sample(self):
        self.y_pos = self.model.StageParameters['y_unload_position']

    def mark_rotation_position(self):
        """
        # Take the current position and mark it as rotation location
        """
        self.x_rot_position = self.x_pos
        self.y_rot_position = self.y_pos
        self.z_rot_position = self.z_pos
        if self.verbose:
            print('Marking new rotation position (absolute coordinates): X: ',
                  self.x_pos, ' Y: ', self.y_pos, ' Z: ', self.z_pos)

    def go_to_rotation_position(self, wait_until_done=False):
        pass
