"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""


class ChangeResolution:
    def __init__(self, model, resolution_mode='high'):
        self.model = model

        self.config_table={'signal': {'main': self.signal_func}}

        self.resolution_mode = resolution_mode

        
    def signal_func(self):
        self.model.logger.debug('prepare to change resolution')
        self.model.pause_data_ready_lock.acquire()
        self.model.ask_to_pause_data_thread = True
        self.model.logger.debug('wait to change resolution')
        self.model.pause_data_ready_lock.acquire()
        self.model.change_resolution(self.resolution_mode)
        self.model.logger.debug('changed resolution')
        self.model.ask_to_pause_data_thread = False
        self.model.prepare_acquisition(False)
        self.model.pause_data_event.set()
        self.model.logger.debug('wake up data thread ')
        self.model.pause_data_ready_lock.release()
        return True

    def generate_meta_data(self, *args):
        # print('This frame: change resolution', self.resolution_mode, self.model.frame_id)
        return True


class Snap:
    def __init__(self, model):
        self.model = model

        self.config_table={'data': {'main': self.data_func}}

    def data_func(self, *args):
        print('the camera is:', self.model.camera.serial_number, self.model.frame_id)
        return True

    def generate_meta_data(self, *args):
        # print('This frame: snap one frame', self.model.frame_id)
        return True


class ZStackAcquisition:
    def __init__(self, model):
        self.model = model

        self.number_z_steps = 0
        self.start_z_position = 0
        self.end_z_position = 0
        self.start_focus = 0
        self.end_focus = 0
        self.z_step_size = 0
        self.focus_step_size = 0
        self.timepoints = 0

        self.positions = {}
        self.current_position_idx = 0
        self.current_z_position = 0
        self.current_focus_position = 0
        self.need_to_move_new_position = True

        self.config_table = {'signal': {'init': self.pre_signal_func,
                                        'main': self.signal_func,
                                        'end': self.signal_end},
                             'node': {'node_type': 'multi-step',
                                      'device_related': True}}

    def pre_signal_func(self):
        microscope_state = self.model.experiment.MicroscopeState

        self.number_z_steps = int(microscope_state['number_z_steps'])

        self.start_z_position = float(microscope_state['start_position'])
        self.end_z_position = float(microscope_state['end_position'])
        self.z_step_size = (self.end_z_position - self.start_z_position) / self.number_z_steps
        
        self.start_focus = float(microscope_state['start_focus'])
        self.end_focus = float(microscope_state['end_focus'])
        self.focus_step_size = (self.end_focus - self.start_focus) / self.number_z_steps
        
        self.timepoints = int(microscope_state['timepoints'])

        if bool(microscope_state['is_multiposition']):
            self.positions = microscope_state['stage_positions']
        else:
            self.positions = dict({
                    0 : {
                        'x': float(self.model.experiment.StageParameters['x']),
                        'y': float(self.model.experiment.StageParameters['y']),
                        'z': float(microscope_state.get('stack_z_origin', self.model.experiment.StageParameters['z'])),
                        'theta': float(self.model.experiment.StageParameters['theta']),
                        'f': float(microscope_state.get('stack_focus_origin', self.model.experiment.StageParameters['f']))
                    }
                })
        self.current_position_idx = 0
        self.current_z_position = 0
        self.current_focus_position = 0
        self.z_position_moved_time = 0
        self.need_to_move_new_position = True

        self.restore_z = -1

        if not bool(microscope_state['is_multiposition']):
            # TODO: Make relative to stage coordinates.
            self.model.get_stage_position()
            self.restore_z = self.model.stages.z_pos
    
    def signal_func(self):
        if self.model.stop_acquisition:
            return False
        # move stage X, Y, Theta
        if self.need_to_move_new_position:
            self.need_to_move_new_position = False
            pos_dict = dict(map(lambda ax: (f'{ax}_abs', self.positions[self.current_position_idx][ax]), ['x', 'y', 'theta']))
            self.model.move_stage(pos_dict, wait_until_done=True)
            
            self.z_position_moved_time = 0
            # calculate first z, f position
            self.current_z_position = self.start_z_position + self.positions[self.current_position_idx]['z']
            self.current_focus_position = self.start_focus + self.positions[self.current_position_idx]['f']
            # move to next position
            self.current_position_idx += 1

        # move z, f
        self.model.move_stage({'z_abs': self.current_z_position, 'f_abs': self.current_focus_position}, wait_until_done=True)

        # next z, f position
        self.current_z_position += self.z_step_size
        self.current_focus_position += self.focus_step_size

        # update z position moved time
        self.z_position_moved_time += 1

        return True

    def signal_end(self):
        # end this node
        if self.model.stop_acquisition:
            return True
        
        # decide whether to move X,Y,Theta
        if self.z_position_moved_time > self.number_z_steps:
            self.need_to_move_new_position = True
            if self.current_position_idx == len(self.positions):
                self.timepoints -= 1
                self.current_position_idx = 0

        if self.timepoints == 0:
            # restore z if need
            if self.restore_z >= 0:
                self.model.move_stage({'z_abs': self.restore_z}, wait_until_done=True)  # Update position
            return True
        return False

    def generate_meta_data(self, *args):
        # print('This frame: z stack', self.model.frame_id)
        return True


class FindTissueSimple2D:
    def __init__(self, model, overlap=0.1, target_resolution='high'):
        """
        Detect tissue and grid out the space to image.
        """
        self.model = model

        self.config_table = {'signal': {},
                             'data': {'main': self.data_func}}

        self.overlap = overlap
        self.target_resolution = target_resolution

    def data_func(self, frame_ids):
        from skimage import filters
        from skimage.transform import downscale_local_mean
        import numpy as np
        from aslm.tools.multipos_table_tools import compute_tiles_from_bounding_box, calc_num_tiles

        for idx in frame_ids:
            img = self.model.data_buffer[idx]

            # Get current mag
            if self.model.experiment.MicroscopeState['resolution_mode'] == 'high':
                curr_pixel_size = self.model.configuration.ZoomParameters['high_res_zoom_pixel_size']
                curr_mag = 300/(12.19/1.56)  # TODO: Don't hardcode
            else:
                zoom = self.model.experiment.MicroscopeState['zoom']
                curr_pixel_size = self.model.configuration.ZoomParameters['low_res_zoom_pixel_size'][zoom]
                curr_mag = float(zoom[:-1])

            # get target mag
            if self.target_resolution == 'high':
                pixel_size = self.model.configuration.ZoomParameters['high_res_zoom_pixel_size']
                mag = 300/(12.19/1.56)  # TODO: Don't hardcode
            else:
                pixel_size = self.model.configuration.ZoomParameters['low_res_zoom_pixel_size'][self.target_resolution]
                mag = float(self.target_resolution)

            # Downsample according to the desired magnification change. Note, we could downsample by whatever we want.
            ds = int(mag/curr_mag)
            ds_img = downscale_local_mean(img, (ds, ds))

            # Threshold
            thresh_img = ds_img > filters.threshold_otsu(img)

            # Find the bounding box
            x, y = np.where(thresh_img)
            # + 0.5 accounts for center of FOV
            x_start, x_end = curr_pixel_size*ds*(np.min(x)+0.5), curr_pixel_size*ds*(np.max(x)+0.5)
            y_start, y_end = curr_pixel_size*ds*(np.min(y)+0.5), curr_pixel_size*ds*(np.max(y)+0.5)
            xd, yd = x_end - x_start, y_end - y_start

            # grab z, theta, f starting positions
            z_start = self.model.experiment.StageParameters['z']
            r_start = self.model.experiment.StageParameters['theta']
            if self.target_resolution == 'high':
                f_start = 0  # very different range of focus values in high-res
            else:
                f_start = self.model.experiment.StageParameters['f']

            # Update x and y start to initialize from the upper-left corner of the current image, since this is
            # how np.where indexed them. The + 0.5 in x_start/y_start calculation shifts their starts back to the
            # center of the field of view.
            curr_fov_x = float(self.model.experiment.CameraParameters['x_pixels']) * curr_pixel_size
            curr_fov_y = float(self.model.experiment.CameraParameters['y_pixels']) * curr_pixel_size
            x_start += self.model.experiment.StageParameters['x'] - curr_fov_x/2
            y_start += self.model.experiment.StageParameters['y'] - curr_fov_y/2

            # grid out the 2D space
            fov_x = float(self.model.experiment.CameraParameters['x_pixels']) * pixel_size
            fov_y = float(self.model.experiment.CameraParameters['y_pixels']) * pixel_size
            x_tiles = calc_num_tiles(xd, self.overlap, fov_x)
            y_tiles = calc_num_tiles(yd, self.overlap, fov_y)

            print(fov_x, fov_y)

            table_values = compute_tiles_from_bounding_box(x_start, x_tiles, fov_x, self.overlap,
                                                           y_start, y_tiles, fov_y, self.overlap,
                                                           z_start, 1, 0, self.overlap,
                                                           r_start, 1, 0, self.overlap,
                                                           f_start, 1, 0, self.overlap)

            print(table_values.shape)

            self.model.event_queue.put(('multiposition', table_values))
