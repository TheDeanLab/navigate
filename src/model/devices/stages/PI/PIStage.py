import time
from model.devices.stages.StageBase import StageBase
from pipython import GCSDevice, pitools


class Stage(StageBase):
    def __init__(self, model, verbose):
        super().__init__(model, verbose)

        """ 
        #  Set up the PI stages 
        """
        pi_stages = self.model.StageParameters['stages']
        pi_refmodes = self.model.StageParameters['refmode']
        pi_stages = pi_stages.split()
        pi_refmodes = pi_refmodes.split()

        self.pitools = pitools
        self.controllername = self.model.StageParameters['controllername']
        self.pi_stages = pi_stages
        self.refmode = pi_refmodes
        self.serialnum = str(self.model.StageParameters['serialnum'])
        self.pidevice = GCSDevice(self.controllername)
        self.pidevice.ConnectUSB(serialnum=self.serialnum)
        self.pitools.startup(self.pidevice, stages=list(self.pi_stages), refmodes=list(self.refmode))
        self.block_till_controller_is_ready()

        # Move the Focusing Stage to the Start Position
        self.pidevice.MOV(5, self.startfocus / 1000)

    def __del__(self):
        try:
            """
            # Close the PI connection
            """
            self.pidevice.unload()
            if self.verbose:
                print('PI connection closed')
        except:
            print('Error while disconnecting the PI stage')

    def create_position_dict(self):
        """
        # Creates a dictionary with the hardware stage positions.
        """
        self.position_dict = {'x_pos': self.x_pos,
                              'y_pos': self.y_pos,
                              'z_pos': self.z_pos,
                              'f_pos': self.f_pos,
                              'theta_pos': self.theta_pos,
                              }

    def create_internal_position_dict(self):
        """
        # Creates a dictionary with the software stage positions.
        # Internal position includes the offset for each stage position.
        # e.g, int_x_pos = x_pos + int_x_pos_offset
        """
        self.int_position_dict = {'x_pos': self.int_x_pos,
                                  'y_pos': self.int_y_pos,
                                  'z_pos': self.int_z_pos,
                                  'f_pos': self.int_f_pos,
                                  'theta_pos': self.int_theta_pos,
                                  }

    def report_position(self):
        """
        # Reports the position of the stage for all axes, and creates the hardware
        # position dictionary.
        """
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

        if self.verbose:
            print("Stage Positions:", self.int_position_dict)

    def move_relative(self, move_dictionary, wait_until_done=False):
        """
        # PI move relative method.
        # Checks to make sure that the move does not exceed the stage limits prior to movement.
        """
        if 'x_rel' in move_dictionary:
            x_rel = move_dictionary['x_rel']
            if (self.x_min < self.x_pos + x_rel) and (self.x_max > self.x_pos + x_rel):
                x_rel = x_rel / 1000
                self.pidevice.MVR({1: x_rel})
            else:
                print('Relative movement stopped: X Motion limit would be reached!', 1000)

        if 'y_rel' in move_dictionary:
            y_rel = move_dictionary['y_rel']
            if (self.y_min < self.y_pos + y_rel) and (self.y_max > self.y_pos + y_rel):
                y_rel = y_rel / 1000
                self.pidevice.MVR({2: y_rel})
            else:
                print('Relative movement stopped: Y Motion limit would be reached!', 1000)

        if 'z_rel' in move_dictionary:
            z_rel = move_dictionary['z_rel']
            if (self.z_min < self.z_pos + z_rel) and (self.z_max > self.z_pos + z_rel):
                z_rel = z_rel / 1000
                self.pidevice.MVR({3: z_rel})
            else:
                print('Relative movement stopped: z Motion limit would be reached!', 1000)

        if 'theta_rel' in move_dictionary:
            theta_rel = move_dictionary['theta_rel']
            if (self.theta_min < self.theta_pos + theta_rel) and (self.theta_max > self.theta_pos + theta_rel):
                self.pidevice.MVR({4: theta_rel})
            else:
                print('Relative movement stopped: theta Motion limit would be reached!', 1000)

        if 'f_rel' in move_dictionary:
            f_rel = move_dictionary['f_rel']
            if (self.f_min < self.f_pos + f_rel) and (self.f_max > self.f_pos + f_rel):
                f_rel = f_rel / 1000
                self.pidevice.MVR({5: f_rel})
            else:
                print('Relative movement stopped: f Motion limit would be reached!', 1000)

        if wait_until_done is True:
            self.pitools.waitontarget(self.pidevice)

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """
        # PI move absolute method.
        # XYZF Values are converted to millimeters for PI API.
        # Theta Values are not converted.
        """

        if 'x_abs' in move_dictionary:
            x_abs = move_dictionary['X']
            x_abs = x_abs - self.int_x_pos_offset
            if (self.x_min < x_abs) and (self.x_max > x_abs):
                x_abs = x_abs / 1000
                self.pidevice.MOV({1: x_abs})
            else:
                print('Absolute movement stopped: X Motion limit would be reached!', 1000)

        if 'y_abs' in move_dictionary:
            y_abs = move_dictionary['Y']
            y_abs = y_abs - self.int_y_pos_offset
            if (self.y_min < y_abs) and (self.y_max > y_abs):
                y_abs = y_abs / 1000
                self.pidevice.MOV({2: y_abs})
            else:
                print('Absolute movement stopped: Y Motion limit would be reached!', 1000)

        if 'z_abs' in move_dictionary:
            z_abs = move_dictionary['Z']
            z_abs = z_abs - self.int_z_pos_offset
            if (self.z_min < z_abs) and (self.z_max > z_abs):
                z_abs = z_abs / 1000
                self.pidevice.MOV({3: z_abs})
            else:
                print('Absolute movement stopped: Z Motion limit would be reached!', 1000)

        if 'f_abs' in move_dictionary:
            f_abs = move_dictionary['F']
            f_abs = f_abs - self.int_f_pos_offset
            if (self.f_min < f_abs) and (self.f_max > f_abs):
                f_abs = f_abs / 1000
                self.pidevice.MOV({5: f_abs})
            else:
                print('Absolute movement stopped: F Motion limit would be reached!', 1000)

        if 'theta_abs' in move_dictionary:
            theta_abs = move_dictionary['R']
            theta_abs = theta_abs - self.int_theta_pos_offset
            if (self.theta_min < theta_abs) and (self.theta_max > theta_abs):
                self.pidevice.MOV({4: theta_abs})
            else:
                print('Absolute movement stopped: Theta Motion limit would be reached!', 1000)

        if wait_until_done is True:
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
        y_abs = self.model.StageParameters['y_load_position'] / 1000
        self.pidevice.MOV({2: y_abs})

    def unload_sample(self):
        y_abs = self.model.StageParameters['y_unload_position'] / 1000
        self.pidevice.MOV({2: y_abs})

    def mark_rotation_position(self):
        """
        Take the current position and mark it as rotation location
        """
        self.x_rot_position = self.x_pos
        self.y_rot_position = self.y_pos
        self.z_rot_position = self.z_pos
        if self.verbose:
            print('Marking new rotation position (absolute coordinates): X: ',
                  self.x_pos, ' Y: ', self.y_pos, ' Z: ', self.z_pos)

    def go_to_rotation_position(self, wait_until_done=False):
        x_abs = self.x_rot_position / 1000
        y_abs = self.y_rot_position / 1000
        z_abs = self.z_rot_position / 1000
        self.pidevice.MOV({1: x_abs, 2: y_abs, 3: z_abs})
        if wait_until_done is True:
            self.pitools.waitontarget(self.pidevice)

    def block_till_controller_is_ready(self):
        """
        Blocks further execution (especially during referencing moves)
        till the PI controller returns ready
        """
        blockflag = True
        while blockflag:
            if self.pidevice.IsControllerReady():
                blockflag = False
            else:
                time.sleep(0.1)
