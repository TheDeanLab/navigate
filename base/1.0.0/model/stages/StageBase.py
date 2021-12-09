'''
StageBase Class

Stage class with the skeleton functions. Important to keep track of the methods that are
exposed to the View. The class StageBase should be subclassed when developing new Models.
This ensures that all the methods are automatically inherited and there is no breaks downstream.

**IMPORTANT** Whatever new function is implemented in a specific model,
it should be first declared in the StageBase class.
In this way the other models will have access to the method and the
program will keep running (perhaps with non intended behavior though).

Adopted and modified from mesoSPIM

'''
class StageBase():
    def __init__(self, session, verbose):
        self.verbose = verbose
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
        self.x_max = session.StageParameters['x_max']
        self.x_min = session.StageParameters['x_min']
        self.y_max = session.StageParameters['y_max']
        self.y_min = session.StageParameters['y_min']
        self.z_max = session.StageParameters['z_max']
        self.z_min = session.StageParameters['z_min']
        self.f_max = session.StageParameters['f_max']
        self.f_min = session.StageParameters['f_min']
        self.theta_max = session.StageParameters['theta_max']
        self.theta_min = session.StageParameters['theta_min']
        self.x_rot_position = session.StageParameters['x_rot_position']
        self.y_rot_position = session.StageParameters['y_rot_position']
        self.z_rot_position = session.StageParameters['z_rot_position']

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
        print("Stage Position: ", self.int_position_dict)

    def move_relative(self, dict, wait_until_done=False):
        '''
        Move relative method
        '''
        if 'x_rel' in dict:
            x_rel = dict['x_rel']
            if self.x_min < self.x_pos + x_rel and self.x_max > self.x_pos + x_rel:
                self.x_pos = self.x_pos + x_rel
            else:
                print('Relative movement stopped: X limit would be reached!', 1000)

        if 'y_rel' in dict:
            y_rel = dict['y_rel']
            if self.y_min < self.y_pos + y_rel and self.y_max > self.y_pos + y_rel:
                self.y_pos = self.y_pos + y_rel
            else:
                print('Relative movement stopped: Y limit would be reached!', 1000)

        if 'z_rel' in dict:
            z_rel = dict['z_rel']
            if self.z_min < self.z_pos + z_rel and self.z_max > self.z_pos + z_rel:
                self.z_pos = self.z_pos + z_rel
            else:
                print('Relative movement stopped: Z limit would be reached!', 1000)

        if 'theta_rel' in dict:
            theta_rel = dict['theta_rel']
            if self.theta_min < self.theta_pos + theta_rel and self.theta_max > self.theta_pos + theta_rel:
                self.theta_pos = self.theta_pos + theta_rel
            else:
                print('Relative movement stopped: Rotation limit would be reached!', 1000)

        if 'f_rel' in dict:
            f_rel = dict['f_rel']
            if self.f_min < self.f_pos + f_rel and self.f_max > self.f_pos + f_rel:
                self.f_pos = self.f_pos + f_rel
            else:
                print('Relative movement stopped: Focus limit would be reached!', 1000)

        if wait_until_done == True:
            time.sleep(0.02)

    def move_absolute(self, dict, wait_until_done=False):
        '''
        Move absolute method
        '''

        if 'x_abs' in dict:
            x_abs = dict['x_abs']
            x_abs = x_abs - self.int_x_pos_offset
            if self.x_min < x_abs and self.x_max > x_abs:
                self.x_pos = x_abs
            else:
                print('Absolute movement stopped: X limit would be reached!', 1000)

        if 'y_abs' in dict:
            y_abs = dict['y_abs']
            y_abs = y_abs - self.int_y_pos_offset
            if self.y_min < y_abs and self.y_max > y_abs:
                self.y_pos = y_abs
            else:
                print('Absolute movement stopped: Y limit would be reached!', 1000)

        if 'z_abs' in dict:
            z_abs = dict['z_abs']
            z_abs = z_abs - self.int_z_pos_offset
            if self.z_min < z_abs and self.z_max > z_abs:
                self.z_pos = z_abs
            else:
                print('Absolute movement stopped: Z limit would be reached!', 1000)

        if 'f_abs' in dict:
            f_abs = dict['f_abs']
            f_abs = f_abs - self.int_f_pos_offset
            if self.f_min < f_abs and self.f_max > f_abs:
                self.f_pos = f_abs
            else:
                print('Absolute movement stopped: Focus limit would be reached!', 1000)

        if 'theta_abs' in dict:
            theta_abs = dict['theta_abs']
            theta_abs = theta_abs - self.int_theta_pos_offset
            if self.theta_min < theta_abs and self.theta_max > theta_abs:
                self.theta_pos = theta_abs
            else:
                print('Absolute movement stopped: Rotation limit would be reached!', 1000)

        if wait_until_done == True:
            time.sleep(3)

    def stop(self):
        pass #self.sig_status_message.emit('Stopped', 0)

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
        self.y_pos =  session.StageParameters['y_load_position']

    def unload_sample(self):
        self.y_pos = session.StageParameters['y_unload_position']

    def mark_rotation_position(self):
        ''' Take the current position and mark it as rotation location '''
        self.x_rot_position = self.x_pos
        self.y_rot_position = self.y_pos
        self.z_rot_position = self.z_pos
        if self.verbose:
            print('Marking new rotation position (absolute coordinates): X: ', self.x_pos, ' Y: ', self.y_pos, ' Z: ', self.z_pos)

    def go_to_rotation_position(self, wait_until_done=False):
        '''
        Move to the proper rotation position - Not implemented in the default
        '''
        print('Going to rotation position: NOT IMPLEMENTED / DEMO MODE')


if __name__ == '__main__':
    ''' Testing and Examples Section '''
    stage = StageBase()
    stage.report_position()