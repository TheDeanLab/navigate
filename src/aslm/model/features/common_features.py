# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

from functools import reduce


class ChangeResolution:
    def __init__(self, model, resolution_mode="high", zoom_value="N/A"):
        self.model = model

        self.config_table = {
            "signal": {"main": self.signal_func, "cleanup": self.cleanup},
            "node": {"device_related": True},
        }

        self.resolution_mode = resolution_mode
        self.zoom_value = zoom_value

    def signal_func(self):
        # pause data thread
        self.model.pause_data_thread()
        # end active microscope
        self.model.active_microscope.end_acquisition()
        # prepare new microscope
        self.model.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ] = self.resolution_mode
        self.model.configuration["experiment"]["MicroscopeState"][
            "zoom"
        ] = self.zoom_value
        self.model.change_resolution(self.resolution_mode)
        self.model.logger.debug(f"current resolution is {self.resolution_mode}")
        self.model.logger.debug(
            f"current active microscope is {self.model.active_microscope_name}"
        )
        # prepare active microscope
        waveform_dict = self.model.active_microscope.prepare_acquisition()
        self.model.event_queue.put(("waveform", waveform_dict))
        # resume data thread
        self.model.resume_data_thread()
        return True

    def cleanup(self):
        self.model.resume_data_thread()


class Snap:
    def __init__(self, model):
        self.model = model

        self.config_table = {"data": {"main": self.data_func}}

    def data_func(self, frame_ids):
        self.model.logger.info(
            f"the camera is:{self.model.active_microscope_name}, {frame_ids}"
        )
        return True


class WaitToContinue:
    def __init__(self, model):
        self.model = model
        self.can_continue = False
        self.target_frame_id = -1

        self.config_table = {
            "signal": {"main": self.signal_func},
            "data": {"pre-main": self.data_func},
        }

    def signal_func(self):
        self.can_continue = True
        self.target_frame_id = self.model.frame_id
        print("--wait to continue:", self.target_frame_id)
        return True

    def data_func(self, frame_ids):
        print("??continue??", self.target_frame_id, frame_ids)
        return self.can_continue and (self.target_frame_id in frame_ids)


class LoopByCount:
    def __init__(self, model, steps=1):
        self.model = model
        self.steps = steps
        if type(steps) is str:
            try:
                parameters = steps.split(".")
                config_ref = reduce((lambda pre, n: f"{pre}['{n}']"), parameters, "")
                exec(f"self.steps = int(self.model.configuration{config_ref})")
            except:
                self.steps = 1

        self.signals = self.steps
        self.data_frames = self.steps

        self.config_table = {
            "signal": {"main": self.signal_func},
            "data": {"main": self.data_func},
        }

    def signal_func(self):
        self.signals -= 1
        if self.signals <= 0:
            self.signals = self.steps
            return False
        return True

    def data_func(self, frame_ids):
        self.data_frames -= len(frame_ids)
        if self.data_frames <= 0:
            self.data_frames = self.steps
            return False
        return True


class PrepareNextChannel:
    def __init__(self, model):
        self.model = model
        self.config_table = {"signal": {"main": self.signal_func}}

    def signal_func(self):
        # prepare virtual microscopes before the primary microscope
        for microscope_name in self.model.virtual_microscopes:
            self.model.virtual_microscopes[microscope_name].prepare_next_channel()

        self.model.active_microscope.prepare_next_channel()

        return True


class ZStackAcquisition:
    def __init__(self, model):
        self.model = model

        self.number_z_steps = 0
        self.start_z_position = 0
        self.start_focus = 0
        self.z_step_size = 0
        self.focus_step_size = 0

        self.positions = {}
        self.current_position_idx = 0
        self.current_z_position = 0
        self.current_focus_position = 0
        self.need_to_move_new_position = True
        self.need_to_move_z_position = True
        self.z_position_moved_time = 0

        self.stack_cycling_mode = "per_stack"
        self.channels = 1

        self.config_table = {
            "signal": {
                "init": self.pre_signal_func,
                "main": self.signal_func,
                "end": self.signal_end,
            },
            "node": {"node_type": "multi-step", "device_related": True},
        }

    def pre_signal_func(self):
        microscope_state = self.model.configuration["experiment"]["MicroscopeState"]

        self.stack_cycling_mode = microscope_state["stack_cycling_mode"]
        # get available channels
        prefix_len = len("channel_")
        channel_dict = microscope_state["channels"]
        self.channels = microscope_state["selected_channels"]
        self.current_channel_in_list = 0
        self.model.active_microscope.current_channel = 0
        self.model.active_microscope.prepare_next_channel()

        self.number_z_steps = int(microscope_state["number_z_steps"])

        self.start_z_position = float(microscope_state["start_position"])
        end_z_position = float(microscope_state["end_position"])
        self.z_step_size = float(microscope_state["step_size"])

        self.start_focus = float(microscope_state["start_focus"])
        end_focus = float(microscope_state["end_focus"])
        self.focus_step_size = (end_focus - self.start_focus) / self.number_z_steps

        if bool(microscope_state["is_multiposition"]):
            self.positions = self.model.configuration["experiment"]["MultiPositions"][
                "stage_positions"
            ]
        else:
            self.positions = [
                {
                    "x": float(
                        self.model.configuration["experiment"]["StageParameters"]["x"]
                    ),
                    "y": float(
                        self.model.configuration["experiment"]["StageParameters"]["y"]
                    ),
                    "z": float(
                        microscope_state.get(
                            "stack_z_origin",
                            self.model.configuration["experiment"]["StageParameters"][
                                "z"
                            ],
                        )
                    ),
                    "theta": float(
                        self.model.configuration["experiment"]["StageParameters"][
                            "theta"
                        ]
                    ),
                    "f": float(
                        microscope_state.get(
                            "stack_focus_origin",
                            self.model.configuration["experiment"]["StageParameters"][
                                "f"
                            ],
                        )
                    ),
                }
            ]
        self.current_position_idx = 0
        self.z_position_moved_time = 0
        self.need_to_move_new_position = True
        self.need_to_move_z_position = True
        # self.current_z_position = self.start_z_position + self.positions[self.current_position_idx]['z']
        # self.current_focus_position = self.start_focus + self.positions[self.current_position_idx]['f']

        # restore z, f
        pos_dict = self.model.get_stage_position()
        self.restore_z = pos_dict["z_pos"]
        self.restore_f = pos_dict["f_pos"]

    def signal_func(self):
        if self.model.stop_acquisition:
            return False
        # move stage X, Y, Theta
        if self.need_to_move_new_position:
            self.need_to_move_new_position = False

            # calculate first z, f position
            self.current_z_position = (
                self.start_z_position + self.positions[self.current_position_idx]["z"]
            )
            self.current_focus_position = (
                self.start_focus + self.positions[self.current_position_idx]["f"]
            )

            # self.model.pause_data_ready_lock.acquire()
            # self.model.ask_to_pause_data_thread = True
            # self.model.pause_data_ready_lock.acquire()

            pos_dict = dict(
                map(
                    lambda ax: (
                        f"{ax}_abs",
                        self.positions[self.current_position_idx][ax],
                    ),
                    ["x", "y", "theta"],
                )
            )
            self.model.move_stage(pos_dict, wait_until_done=True)

            # self.model.ask_to_pause_data_thread = False
            # self.model.pause_data_event.set()
            # self.model.pause_data_ready_lock.release()

            # self.z_position_moved_time = 0

        if self.need_to_move_z_position:
            # move z, f
            # self.model.pause_data_thread()

            self.model.move_stage(
                {
                    "z_abs": self.current_z_position,
                    "f_abs": self.current_focus_position,
                },
                wait_until_done=True,
            )

            # self.model.resume_data_thread()

        if self.stack_cycling_mode != "per_stack":
            # update channel for each z position in 'per_slice'
            self.update_channel()
            self.need_to_move_z_position = self.current_channel_in_list == 0

        # in 'per_slice', move to next z position if all the channels have been acquired
        if self.need_to_move_z_position:
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
        if self.z_position_moved_time >= self.number_z_steps:
            self.z_position_moved_time = 0
            # calculate first z, f position
            self.current_z_position = (
                self.start_z_position + self.positions[self.current_position_idx]["z"]
            )
            self.current_focus_position = (
                self.start_focus + self.positions[self.current_position_idx]["f"]
            )

            # after running through a z-stack, update channel
            if self.stack_cycling_mode == "per_stack":
                self.update_channel()
                # if run through all the channels, move to next position
                if self.current_channel_in_list == 0:
                    self.need_to_move_new_position = True
            else:
                self.need_to_move_new_position = True

            if self.need_to_move_new_position:
                # move to next position
                self.current_position_idx += 1

        if self.current_position_idx >= len(self.positions):
            self.current_position_idx = 0
            # restore z
            self.model.move_stage(
                {"z_abs": self.restore_z, "f_abs": self.restore_f}, wait_until_done=False
            )  # Update position
            return True

        return False

    def update_channel(self):
        self.current_channel_in_list = (
            self.current_channel_in_list + 1
        ) % self.channels
        self.model.active_microscope.prepare_next_channel()


class ConProAcquisition:   # don't have the multi-position part for now
    def __init__(self, model):

        self.model = model

        self.scanrange = 0
        self.n_plane = 0
        self.offset_start = 0
        self.offset_end = 0
        self.offset_step_size = 0
        self.timepoints = 0

        self.need_to_move_new_plane = True
        self.offset_update_time = 0

        self.conpro_cycling_mode = 'per_stack'
        self.channels = [1]

        self.config_table = {'signal': {'init': self.pre_signal_func,
                                        'main': self.signal_func,
                                        'end': self.signal_end},
                             'node': {'node_type': 'multi-step',
                                      'device_related': True}}

        self.model.move_stage({'z_abs': 0})

    def pre_signal_func(self):
        import copy
        microscope_state = self.model.configuration['experiment']['MicroscopeState']

        self.conpro_cycling_mode = microscope_state['conpro_cycling_mode']
        # get available channels
        self.channels = microscope_state["selected_channels"]
        self.current_channel_in_list = 0

        self.n_plane = int(microscope_state['n_plane'])

        self.start_offset = float(copy.copy(microscope_state['offset_start']))
        self.end_offset = float(copy.copy(microscope_state['offset_end']))
        if self.n_plane == 1:
            self.offset_step_size = 0
        else:
            self.offset_step_size = (self.end_offset - self.start_offset) / float(self.n_plane-1)
        
        self.timepoints = 1  # int(microscope_state['timepoints'])

        self.need_update_offset = True
        self.current_offset = self.start_offset
        self.offset_update_time = 0

        # self.model.move_stage({'z_abs': 0})
    
    def signal_func(self):
        # print(f"Signal with time {self.offset_update_time} and offset {self.current_offset}")
        if self.model.stop_acquisition:
            return False

        # if self.need_update_offset:
        #     # update offset
        #     # self.model.pause_data_thread()CH00_000000

        #     # self.model.update_offset({'offset_abs': self.current_offset}, wait_until_done=True)
            
        #     # Update the offset by changing the dictionary value used by GalvoNIStage
        #     self.model.configuration['experiment']['MicroscopeState']['offset_start'] = self.current_offset
        #     self.model.configuration['experiment']['MicroscopeState']['offset_end'] = self.current_offset
            
        #     # Call a modification of the waveform
        #     self.model.move_stage({'z_abs': 0})

        #     # self.model.resume_data_thread()

        if self.conpro_cycling_mode != 'per_stack':
            # update channel for each z position in 'per_slice'
            self.update_channel()
            self.need_update_offset = (self.current_channel_in_list == 0)

        # in 'per_slice', update the offset if all the channels have been acquired
        if self.need_update_offset:
            # next z, f position
            # self.current_offset += self.offset_step_size

            # update offset moved time
            self.offset_update_time += 1

        return True

    def signal_end(self):
        # end this node
        if self.model.stop_acquisition:
            self.model.configuration['experiment']['MicroscopeState']['offset_start'] = self.start_offset
            self.model.configuration['experiment']['MicroscopeState']['offset_end'] = self.end_offset
            return True
        
        # decide whether to update offset
        if self.offset_update_time >= self.n_plane:
            self.timepoints -=1

            self.model.configuration['experiment']['MicroscopeState']['offset_start'] = self.start_offset
            self.model.configuration['experiment']['MicroscopeState']['offset_end'] = self.end_offset

            self.current_offset = self.start_offset

            self.offset_update_time = 0

        if self.timepoints == 0:
            return True

        return False

    def generate_meta_data(self, *args):
        # print('This frame: z stack', self.model.frame_id)
        return True

    def update_channel(self):
        self.current_channel_in_list = (
            self.current_channel_in_list + 1
        ) % self.channels
        self.model.active_microscope.prepare_next_channel()

class FindTissueSimple2D:
    def __init__(
        self, model, overlap=0.1, target_resolution="Nanoscale", target_zoom="N/A"
    ):
        """
        Detect tissue and grid out the space to image.
        """
        self.model = model

        self.config_table = {"signal": {}, "data": {"main": self.data_func}}

        self.overlap = overlap
        self.target_resolution = target_resolution
        self.target_zoom = target_zoom

    def data_func(self, frame_ids):
        from skimage import filters
        from skimage.transform import downscale_local_mean
        import numpy as np
        from aslm.tools.multipos_table_tools import (
            compute_tiles_from_bounding_box,
            calc_num_tiles,
        )
        import tifffile

        for idx in frame_ids:
            img = self.model.data_buffer[idx]

            # Get current mag
            microscope_name = self.model.configuration["experiment"]["MicroscopeState"][
                "microscope_name"
            ]
            zoom = self.model.configuration["experiment"]["MicroscopeState"]["zoom"]
            curr_pixel_size = self.model.configuration["configuration"]["microscopes"][
                microscope_name
            ]["zoom"][zoom]["pixel_size"]
            # get target pixel size
            pixel_size = self.model.configuration["configuration"]["microscopes"][
                self.target_resolution
            ]["zoom"][self.target_zoom]["pixel_size"]

            # Downsample according to the desired magnification change. Note, we could downsample by whatever we want.
            ds = int(curr_pixel_size / pixel_size)
            ds_img = downscale_local_mean(img, (ds, ds))

            # Threshold
            thresh_img = ds_img > filters.threshold_otsu(img)

            # tifffile.imwrite("C:\\Users\\MicroscopyInnovation\\Desktop\\Data\\Zach\\thresh.tiff", thresh_img)

            # Find the bounding box
            # In the real-deal, non-transposed image, x increase corresponds to a decrease in row number
            # y increase responds to an increase in row number
            # This means the smallest x coordinate is actually the largest
            x, y = np.where(thresh_img)
            # + 0.5 accounts for center of FOV
            x_start, x_end = -curr_pixel_size * ds * (
                np.max(x) + 0.5
            ), -curr_pixel_size * ds * (np.min(x) + 0.5)
            y_start, y_end = curr_pixel_size * ds * (
                np.min(y) + 0.5
            ), curr_pixel_size * ds * (np.max(y) + 0.5)
            xd, yd = abs(x_start - x_end), y_end - y_start

            # grab z, theta, f starting positions
            z_start = self.model.configuration["experiment"]["StageParameters"]["z"]
            r_start = self.model.configuration["experiment"]["StageParameters"]["theta"]
            if self.target_resolution == "Nanoscale":
                f_start = 0  # very different range of focus values in high-res
            else:
                f_start = self.model.configuration["experiment"]["StageParameters"]["f"]

            # Update x and y start to initialize from the upper-left corner of the current image, since this is
            # how np.where indexed them. The + 0.5 in x_start/y_start calculation shifts their starts back to the
            # center of the field of view.
            curr_fov_x = (
                float(
                    self.model.configuration["experiment"]["CameraParameters"][
                        "x_pixels"
                    ]
                )
                * curr_pixel_size
            )
            curr_fov_y = (
                float(
                    self.model.configuration["experiment"]["CameraParameters"][
                        "y_pixels"
                    ]
                )
                * curr_pixel_size
            )
            x_start += (
                self.model.configuration["experiment"]["StageParameters"]["x"]
                + curr_fov_x / 2
            )
            y_start += (
                self.model.configuration["experiment"]["StageParameters"]["y"]
                - curr_fov_y / 2
            )

            # stage offset
            x_start += float(
                self.model.configuration["configuration"]["microscopes"][
                    self.target_resolution
                ]["stage"]["x_offset"]
            ) - float(
                self.model.configuration["configuration"]["microscopes"][
                    microscope_name
                ]["stage"]["x_offset"]
            )
            y_start += float(
                self.model.configuration["configuration"]["microscopes"][
                    self.target_resolution
                ]["stage"]["y_offset"]
            ) - float(
                self.model.configuration["configuration"]["microscopes"][
                    microscope_name
                ]["stage"]["y_offset"]
            )
            z_start += float(
                self.model.configuration["configuration"]["microscopes"][
                    self.target_resolution
                ]["stage"]["z_offset"]
            ) - float(
                self.model.configuration["configuration"]["microscopes"][
                    microscope_name
                ]["stage"]["z_offset"]
            )
            r_start += float(
                self.model.configuration["configuration"]["microscopes"][
                    self.target_resolution
                ]["stage"]["r_offset"]
            ) - float(
                self.model.configuration["configuration"]["microscopes"][
                    microscope_name
                ]["stage"]["r_offset"]
            )

            # grid out the 2D space
            fov_x = (
                float(
                    self.model.configuration["experiment"]["CameraParameters"][
                        "x_pixels"
                    ]
                )
                * pixel_size
            )
            fov_y = (
                float(
                    self.model.configuration["experiment"]["CameraParameters"][
                        "y_pixels"
                    ]
                )
                * pixel_size
            )
            x_tiles = calc_num_tiles(xd, self.overlap, fov_x)
            y_tiles = calc_num_tiles(yd, self.overlap, fov_y)

            table_values = compute_tiles_from_bounding_box(
                x_start,
                x_tiles,
                fov_x,
                self.overlap,
                y_start,
                y_tiles,
                fov_y,
                self.overlap,
                z_start,
                1,
                0,
                self.overlap,
                r_start,
                1,
                0,
                self.overlap,
                f_start,
                1,
                0,
                self.overlap,
            )

            self.model.event_queue.put(("multiposition", table_values))
