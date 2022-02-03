"""
Physik Instrumente Stage Class

Model class for controlling Physik Instrumente stages via the PIPython package.

To start the stages, pitools.startup configures the 'stages' and references them with 'refmodes'.
@param stages: Name of  stages to initialize as string or list(not tuple!) or None to skip.
@param refmodes: Referencing command as string(for all stages) or list ( not tuple!) or None to skip.
@param servostates: Desired servo states as boolean(for all stages) or dict {axis: state} or None to skip.
@param kwargs: Optional arguments with keywords that are passed to sub functions.


Adopted and modified from mesoSPIM
"""

import time
from model.devices.stages.StageBase import StageBase

class Stage(StageBase):
    def __init__(self, model, verbose):
        '''
        Physik Instrumente Code    
        '''
        self.verbose = verbose
        from pipython import GCSDevice, pitools
        self.pitools = pitools

        ''' 
        Setting up the PI stages 
        '''
        # Convert YAML import to list
        pi_stages = model.StageParameters['stages']
        pi_refmodes = model.StageParameters['refmode']
        pi_stages = pi_stages.split()
        pi_refmodes = pi_refmodes.split()

        self.controllername = model.StageParameters['controllername']
        self.pi_stages = pi_stages
        self.refmode = pi_refmodes
        self.serialnum = str(model.StageParameters['serialnum'])
        self.pidevice = GCSDevice(self.controllername)
        self.pidevice.ConnectUSB(serialnum=self.serialnum)
        self.pitools.startup(self.pidevice, stages=list(self.pi_stages), refmodes=list(self.refmode))

        self.block_till_controller_is_ready()
        self.startfocus = model.StageParameters['startfocus']
        # Move the Focusing Stage to the Start Position
        self.pidevice.MOV(5, self.startfocus / 1000)

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

    def __del__(self):
        try:
            '''
            Close the PI connection
            '''
            self.pidevice.unload()
            if self.verbose:
                print('PI connection closed')
        except:
            print('Error while disconnecting the PI stage')

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
        positions = self.pidevice.qPOS(self.pidevice.axes)
        self.x_pos = round(positions['1'] * 1000, 2)
        self.y_pos = round(positions['2'] * 1000, 2)
        self.z_pos = round(positions['3'] * 1000, 2)
        self.f_pos = round(positions['5'] * 1000, 2)
        self.theta_pos = positions['4']
        self.create_position_dict()

        self.int_x_pos = self.x_pos + self.int_x_pos_offset
        self.int_y_pos = self.y_pos + self.int_y_pos_offset
        self.int_z_pos = self.z_pos + self.int_z_pos_offset
        self.int_f_pos = self.f_pos + self.int_f_pos_offset
        self.int_theta_pos = self.theta_pos + self.int_theta_pos_offset
        self.create_internal_position_dict()

        print("Stage Positions:", self.int_position_dict)

    def move_relative(self, dict, wait_until_done=False):
        '''
        PI move relative method
        Lots of implementation details in here, should be replaced by a facade
        '''
        if 'x_rel' in dict:
            x_rel = dict['x_rel']
            if self.x_min < self.x_pos + x_rel and self.x_max > self.x_pos + x_rel:
                x_rel = x_rel / 1000
                self.pidevice.MVR({1: x_rel})
            else:
                print('Relative movement stopped: X Motion limit would be reached!', 1000)

        if 'y_rel' in dict:
            y_rel = dict['y_rel']
            if self.y_min < self.y_pos + y_rel and self.y_max > self.y_pos + y_rel:
                y_rel = y_rel / 1000
                self.pidevice.MVR({2: y_rel})
            else:
                print('Relative movement stopped: Y Motion limit would be reached!', 1000)

        if 'z_rel' in dict:
            z_rel = dict['z_rel']
            if self.z_min < self.z_pos + z_rel and self.z_max > self.z_pos + z_rel:
                z_rel = z_rel / 1000
                self.pidevice.MVR({3: z_rel})
            else:
                print('Relative movement stopped: z Motion limit would be reached!', 1000)

        if 'theta_rel' in dict:
            theta_rel = dict['theta_rel']
            if self.theta_min < self.theta_pos + theta_rel and self.theta_max > self.theta_pos + theta_rel:
                self.pidevice.MVR({4: theta_rel})
            else:
                print('Relative movement stopped: theta Motion limit would be reached!', 1000)

        if 'f_rel' in dict:
            f_rel = dict['f_rel']
            if self.f_min < self.f_pos + f_rel and self.f_max > self.f_pos + f_rel:
                f_rel = f_rel / 1000
                self.pidevice.MVR({5: f_rel})
            else:
                print('Relative movement stopped: f Motion limit would be reached!', 1000)

        if wait_until_done == True:
            self.pitools.waitontarget(self.pidevice)

    def move_absolute(self, dict, wait_until_done=False):
        '''
        PI move absolute method
        Lots of implementation details in here, should be replaced by a facade
        '''

        if 'x_abs' in dict:
            x_abs = dict['X']
            x_abs = x_abs - self.int_x_pos_offset
            if self.x_min < x_abs and self.x_max > x_abs:
                ''' Conversion to mm and command emission'''
                x_abs = x_abs / 1000
                self.pidevice.MOV({1: x_abs})
            else:
                print('Absolute movement stopped: X Motion limit would be reached!', 1000)

        if 'y_abs' in dict:
            y_abs = dict['Y']
            y_abs = y_abs - self.int_y_pos_offset
            if self.y_min < y_abs and self.y_max > y_abs:
                ''' Conversion to mm and command emission'''
                y_abs = y_abs / 1000
                self.pidevice.MOV({2: y_abs})
            else:
                print('Absolute movement stopped: Y Motion limit would be reached!', 1000)

        if 'z_abs' in dict:
            z_abs = dict['Z']
            z_abs = z_abs - self.int_z_pos_offset
            if self.z_min < z_abs and self.z_max > z_abs:
                ''' Conversion to mm and command emission'''
                z_abs = z_abs / 1000
                self.pidevice.MOV({3: z_abs})
            else:
                print('Absolute movement stopped: Z Motion limit would be reached!', 1000)

        if 'f_abs' in dict:
            f_abs = dict['F']
            f_abs = f_abs - self.int_f_pos_offset
            if self.f_min < f_abs and self.f_max > f_abs:
                ''' Conversion to mm and command emission'''
                f_abs = f_abs / 1000
                self.pidevice.MOV({5: f_abs})
            else:
                print('Absolute movement stopped: F Motion limit would be reached!', 1000)

        if 'theta_abs' in dict:
            theta_abs = dict['R']
            theta_abs = theta_abs - self.int_theta_pos_offset
            if self.theta_min < theta_abs and self.theta_max > theta_abs:
                ''' No Conversion to mm !!!! and command emission'''
                self.pidevice.MOV({4: theta_abs})
            else:
                print('Absolute movement stopped: Theta Motion limit would be reached!', 1000)

        if wait_until_done == True:
            self.pitools.waitontarget(self.pidevice)

    def stop(self):
        self.pidevice.STP(noraise=True)

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
        y_abs = model.StageParameters['y_load_position'] / 1000
        self.pidevice.MOV({2: y_abs})

    def unload_sample(self):
        y_abs = model.StageParameters['y_unload_position'] / 1000
        self.pidevice.MOV({2: y_abs})

    def mark_rotation_position(self):
        '''
        Take the current position and mark it as rotation location
        '''
        self.x_rot_position = self.x_pos
        self.y_rot_position = self.y_pos
        self.z_rot_position = self.z_pos
        if self.verbose:
            print('Marking new rotation position (absolute coordinates): X: ', self.x_pos, ' Y: ', self.y_pos, ' Z: ', self.z_pos)

    def go_to_rotation_position(self, wait_until_done=False):
        x_abs = self.x_rot_position / 1000
        y_abs = self.y_rot_position / 1000
        z_abs = self.z_rot_position / 1000
        self.pidevice.MOV({1: x_abs, 2: y_abs, 3: z_abs})
        if wait_until_done == True:
            self.pitools.waitontarget(self.pidevice)

    def block_till_controller_is_ready(self):
        '''
        Blocks further execution (especially during referencing moves)
        till the PI controller returns ready
        '''
        blockflag = True
        while blockflag:
            if self.pidevice.IsControllerReady():
                blockflag = False
            else:
                time.sleep(0.1)
