from threading import Lock
from aslm.model.analysis.boundary_detect import *

class VolumeSearch:
    def __init__(self, model, target_resolution='Nanoscope', target_zoom='N/A'):
        self.model = model
        self.target_resolution = target_resolution
        self.target_zoom = target_zoom

        self.z_steps = 0
        self.z_step_size = 0
        self.z_pos = 0
        self.f_step_size = 0
        self.f_pos = 0
        self.f_offset = 0
        self.curr_z_index = 0

        self.synch_lock = Lock()
        self.direction = 1 # up: 1; down: -1
        self.has_tissue = False
        self.first_boundary = None
        self.pre_boundary = None

        self.config_table = {'signal': {'init': self.pre_signal_func,
                                        'main': self.signal_func,
                                        'end': self.signal_end},
                             'data': {'init': self.init_data_func,
                                      'main': self.data_func,
                                      'end': self.end_data_func},
                             'node': {'node_type': 'multi-step',
                                      'device_related': True}}

    def pre_signal_func(self):
        self.z_pos = float(self.model.configuration['experiment']['StageParameters']['z'])
        self.f_pos = float(self.model.configuration['experiment']['StageParameters']['f'])
        
        self.z_steps = float(self.model.configuration['experiment']['MicroscopeState']['number_z_steps'])
        self.z_step_size = float(self.model.configuration['experiment']['MicroscopeState']['step_size'])

        f_start = float(self.model.configuration['experiment']['MicroscopeState']['start_focus'])
        f_end = float(self.model.configuration['experiment']['MicroscopeState']['end_focus'])
        self.f_step_size = (f_end - f_start) / self.z_steps
        
        self.curr_z_index = int(self.z_steps/2)

        self.direction = 1 # up

    def signal_func(self):
        z = self.z_pos + self.curr_z_index * self.z_step_size
        f = self.f_pos + self.curr_z_index * self.f_step_size
        self.model.move_stage({'z_abs': z, 'f_abs': f})
        self.synch_lock.acquire()
        return True

    def signal_end(self):
        self.synch_lock.acquire()
        if self.end_flag:
            return True
        if not self.has_tissue or self.curr_z_index == self.z_steps - 1:
            self.curr_z_index = int(self.z_steps/2)
            self.direction = -1

        self.curr_z_index += self.direction
        
        self.synch_lock.release()
        return False

    def init_data_func(self):
        # calculate mag
        microscope_name = self.model.active_microscope_name
        curr_pixel_size = self.model.configuration['configuration']['microscopes'][microscope_name]['zoom']['pixel_size']
        target_pixel_size = self.model.configuration['configuration']['microscopes'][self.target_resolution]['zoom']['pixel_size']

        self.mag = math.ceil(curr_pixel_size / target_pixel_size)
        img_width = self.model.configuration['experiment']['CameraParameters']['x_pixels']
        self.grid_num = math.ceil(img_width / self.mag)
        self.first_boundary = None
        self.pre_boundary = None

    def data_func(self, frame_ids):
        for idx in frame_ids:
            img_data = self.model.data_buffer[idx]
            if self.pre_boundary is None:
                boundary = find_tissue_boundary_2d(img_data, self.mag)
                self.first_boundary = boundary
            else:
                boundary = binary_detect(img_data, self.pre_boundary, self.mag)
            self.has_tissue = any(boundary)
            # TODO:append boundary to the list, map positions

            if self.has_tissue and self.curr_z_index > 0 and self.curr_z_index < self.z_steps-1:
                self.pre_boundary = boundary
            elif self.direction == 1:
                self.pre_boundary = self.first_boundary
            else:
                self.end_flag = True

            if self.synch_lock.locked():
                self.synch_lock.release()

    def end_data_func(self, frame_ids):
        # TODO: add postions to multi-position table
        return self.end_flag
