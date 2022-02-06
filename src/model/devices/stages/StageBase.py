"""
StageBase Class

Stage class with the skeleton functions. Important to keep track of the methods that are
exposed to the View. The class StageBase should be subclassed when developing new Models.
This ensures that all the methods are automatically inherited and there is no breaks downstream.

**IMPORTANT** Whatever new function is implemented in a specific model,
it should be first declared in the StageBase class.
In this way the other models will have access to the method and the
program will keep running (perhaps with non intended behavior though).

Adopted and modified from mesoSPIM

"""
class StageBase:
    def __init__(self, model, verbose):
        self.verbose = verbose
        self.model = model

        """
        Initial setting of all positions
        self.x_pos, self.y_pos etc are the true axis positions, no matter whether
        the stages are zeroed or not.
        """
        self.x_pos = 0
        self.y_pos = 0
        self.z_pos = 0
        self.f_pos = 0
        self.theta_pos = 0
        self.position_dict = {'x_pos': self.x_pos,
                              'y_pos': self.y_pos,
                              'z_pos': self.z_pos,
                              'f_pos': self.f_pos,
                              'theta_pos': self.theta_pos,
                              }
        """
        Internal (software) positions
        """
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
        """
        Create offsets. It should be: int_x_pos = x_pos + int_x_pos_offset
        self.int_x_pos = self.x_pos + self.int_x_pos_offset
        OR x_pos = int_x_pos - int_x_pos_offset
        self.x_pos = self.int_x_pos - self.int_x_pos_offset
        """
        self.int_x_pos_offset = 0
        self.int_y_pos_offset = 0
        self.int_z_pos_offset = 0
        self.int_f_pos_offset = 0
        self.int_theta_pos_offset = 0

        """ 
        Setting movement limits: currently hardcoded: Units are in microns 
        """
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
        self.startfocus = model.StageParameters['startfocus']

    def create_position_dict(self):
        pass

    def create_internal_position_dict(self):
        pass

    def report_position(self):
        pass

    def move_relative(self, dict, wait_until_done=False):
        pass

    def move_absolute(self, dict, wait_until_done=False):
        pass

    def stop(self):
        pass

    def zero_axes(self, list):
        pass

    def unzero_axes(self, list):
        pass

    def load_sample(self):
        pass

    def unload_sample(self):
        pass

    def mark_rotation_position(self):
        pass

    def go_to_rotation_position(self, wait_until_done=False):
        pass

