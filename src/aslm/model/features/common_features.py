# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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

import time
from functools import reduce
from threading import Lock

from .image_writer import ImageWriter
from aslm.tools.common_functions import VariableWithLock


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
    """This feature is used to synchronize signal and data.

    Let the faster one wait until the other one ends.
    """

    def __init__(self, model):
        self.model = model
        self.pause_signal_lock = Lock()
        self.pause_data_lock = Lock()
        self.first_enter_node = VariableWithLock(str)

        self.config_table = {
            "signal": {
                "init": self.pre_signal_func,
                "main": self.signal_func,
                "cleanup": self.cleanup,
            },
            "data": {
                "init": self.pre_data_func,
                "main": self.data_func,
                "cleanup": self.cleanup,
            },
        }

    def pre_signal_func(self):
        with self.first_enter_node as first_enter_node:
            if first_enter_node.value == "":
                self.model.logger.debug("*** wait to continue enters signal "
                                        "first!")
                first_enter_node.value = "signal"
                if not self.pause_signal_lock.locked():
                    self.pause_signal_lock.acquire()
                if self.pause_data_lock.locked():
                    self.pause_data_lock.release()

    def signal_func(self):
        self.model.logger.debug(f"--wait to continue: {self.model.frame_id}")
        if self.pause_signal_lock.locked():
            self.pause_signal_lock.acquire()
        elif self.pause_data_lock.locked():
            self.pause_data_lock.release()
        self.first_enter_node.value = ""
        self.model.logger.debug(f"--wait to continue is done!: {self.model.frame_id}")
        return True

    def pre_data_func(self):
        with self.first_enter_node as first_enter_node:
            if first_enter_node.value == "":
                self.model.logger.debug("*** wait to continue enters data "
                                        "node first!")
                first_enter_node.value = "data"
                if not self.pause_data_lock.locked():
                    self.pause_data_lock.acquire()
                if self.pause_signal_lock.locked():
                    self.pause_signal_lock.release()

    def data_func(self, frame_ids):
        self.model.logger.debug(f"**wait to continue? {frame_ids}")
        if self.pause_data_lock.locked():
            self.pause_data_lock.acquire()
        elif self.pause_signal_lock.locked():
            self.pause_signal_lock.release()
        self.first_enter_node.value = ""
        self.model.logger.debug(f"**wait to continue is done! {frame_ids}")
        return True

    def cleanup(self):
        if self.pause_signal_lock.locked():
            self.pause_signal_lock.release()
        if self.pause_data_lock.locked():
            self.pause_data_lock.release()


class LoopByCount:
    def __init__(self, model, steps=1):
        self.model = model
        self.step_by_frame = True
        self.steps = steps
        if type(steps) is str:
            self.step_by_frame = False
            try:
                parameters = steps.split(".")
                config_ref = reduce((lambda pre, n: f"{pre}['{n}']"), parameters, "")
                exec(f"self.steps = int(self.model.configuration{config_ref})")
            except:  # noqa
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
        if self.step_by_frame:
            self.data_frames -= len(frame_ids)
        else:
            self.data_frames -= 1
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


class MoveToNextPositionInMultiPostionTable:
    def __init__(self, model):
        self.model = model
        self.config_table = {
            "signal": {
                "main": self.signal_func,
                "cleanup": self.cleanup,
            },
            "node": {"device_related": True},
        }
        self.pre_z = None
        self.current_idx = 0
        self.multipostion_table = self.model.configuration["experiment"][
            "MultiPositions"
        ]
        self.postion_count = self.model.configuration["experiment"]["MicroscopeState"][
            "multiposition_count"
        ]
        self.stage_distance_threshold = 1000

    def signal_func(self):
        self.model.logger.debug(
            f"multi-position current idx: {self.current_idx}, {self.postion_count}"
        )
        if self.current_idx >= self.postion_count:
            return False
        pos_dict = self.multipostion_table[self.current_idx]
        # pause data thread if necessary
        if self.current_idx == 0:
            temp = self.model.get_stage_position()
            pre_stage_pos = dict(map(lambda k: (k, temp[f"{k}_pos"]), ["x", "y", "z", "f", "theta"]))
        else:
            pre_stage_pos = self.multipostion_table[self.current_idx-1]
        delta_x = abs(pos_dict["x"] - pre_stage_pos["x"])
        delta_y = abs(pos_dict["y"] - pre_stage_pos["y"])
        delta_z = abs(pos_dict["z"] - pre_stage_pos["z"])
        delta_f = abs(pos_dict["f"] - pre_stage_pos["f"])
        should_pause_data_thread = any(
            distance > self.stage_distance_threshold
            for distance in [delta_x, delta_y, delta_z, delta_f]
        )
        if should_pause_data_thread:
            self.model.pause_data_thread()

        self.current_idx += 1
        abs_pos_dict = dict(map(lambda k: (f"{k}_abs", pos_dict[k]), pos_dict.keys()))
        self.model.logger.debug(f"MoveToNextPositionInMultiPosition: "
                                f"{pos_dict}")
        self.model.move_stage(abs_pos_dict, wait_until_done=True)

        self.model.logger.debug("MoveToNextPositionInMultiPosition: move done")
        # resume data thread
        if should_pause_data_thread:
            self.model.resume_data_thread()
        self.model.active_microscope.central_focus = None
        if self.pre_z != pos_dict["z"]:
            self.pre_z = pos_dict["z"]
            return True

    def cleanup(self):
        self.model.resume_data_thread()


class StackPause:
    def __init__(self, model, pause_num="experiment.MicroscopeState.timepoints"):
        self.model = model
        self.pause_num = pause_num
        if type(pause_num) is str:
            try:
                parameters = pause_num.split(".")
                config_ref = reduce((lambda pre, n: f"{pre}['{n}']"), parameters, "")
                exec(f"self.pause_num = int(self.model.configuration{config_ref})")
            except:  # noqa
                self.pause_num = 1
        self.config_table = {"signal": {"main": self.signal_func}}

    def signal_func(self):
        self.pause_num -= 1
        if self.pause_num <= 0:
            return
        pause_time = float(
            self.model.configuration["experiment"]["MicroscopeState"]["stack_pause"]
        )
        if pause_time <= 0:
            return
        current_channel = f"channel_{self.model.active_microscope.current_channel}"
        current_exposure_time = (
            float(
                self.model.configuration["experiment"]["MicroscopeState"]["channels"][
                    current_channel
                ]["camera_exposure_time"]
            )
            / 1000.0
        )
        if pause_time < 5 * current_exposure_time:
            time.sleep(pause_time)
        else:
            self.model.pause_data_thread()
            pause_time -= 2 * current_exposure_time
            while pause_time > 0:
                pt = min(pause_time, 0.1)
                time.sleep(pt)
                if self.model.stop_acquisition:
                    self.model.resume_data_thread()
                    return
                pause_time -= 0.1
            self.model.resume_data_thread()


class ZStackAcquisition:
    def __init__(
        self, model, get_origin=False, saving_flag=False, saving_dir="z-stack"
    ):
        self.model = model
        self.get_origin = get_origin

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

        self.image_writer = None
        if saving_flag:
            self.image_writer = ImageWriter(model, sub_dir=saving_dir)

        self.config_table = {
            "signal": {
                "init": self.pre_signal_func,
                "main": self.signal_func,
                "end": self.signal_end,
            },
            "data": {
                "init": self.pre_data_func,
                "main": self.in_data_func,
                "end": self.end_data_func,
                "cleanup": self.cleanup_data_func,
            },
            "node": {"node_type": "multi-step", "device_related": True},
        }

    def pre_signal_func(self):
        """prepare for z-stack acquisition"""

        microscope_state = self.model.configuration["experiment"]["MicroscopeState"]

        self.stack_cycling_mode = microscope_state["stack_cycling_mode"]
        # get available channels
        self.channels = microscope_state["selected_channels"]
        self.current_channel_in_list = 0
        self.model.active_microscope.current_channel = 0
        self.model.active_microscope.prepare_next_channel()

        self.number_z_steps = int(microscope_state["number_z_steps"])

        self.start_z_position = float(microscope_state["start_position"])
        # end_z_position = float(microscope_state["end_position"])
        self.z_step_size = float(microscope_state["step_size"])
        self.z_stack_distance = abs(
            self.start_z_position - float(microscope_state["end_position"])
        )

        self.start_focus = float(microscope_state["start_focus"])
        end_focus = float(microscope_state["end_focus"])
        self.focus_step_size = (end_focus - self.start_focus) / self.number_z_steps
        self.f_stack_distance = abs(end_focus - self.start_focus)

        # restore z, f
        pos_dict = self.model.get_stage_position()
        self.model.logger.debug(f"**** ZStack get stage position: {pos_dict}")
        self.restore_z = pos_dict["z_pos"]
        self.restore_f = pos_dict["f_pos"]

        if bool(microscope_state["is_multiposition"]):
            self.positions = self.model.configuration["experiment"]["MultiPositions"]
        else:
            self.positions = [
                {
                    "x": float(pos_dict["x_pos"]),
                    "y": float(pos_dict["y_pos"]),
                    "z": float(
                        microscope_state.get(
                            "stack_z_origin",
                            pos_dict["z_pos"],
                        )
                        if not self.get_origin
                        else pos_dict["z_pos"]
                    ),
                    "theta": float(pos_dict["theta_pos"]),
                    "f": float(
                        microscope_state.get(
                            "stack_focus_origin",
                            pos_dict["f_pos"],
                        )
                        if not self.get_origin
                        else pos_dict["f_pos"]
                    ),
                }
            ]

        self.model.logger.debug(
            f"*** ZStack pre_signal_func: {self.positions}, {self.start_focus}, "
            f"{self.start_z_position}"
        )
        self.current_position_idx = 0
        self.z_position_moved_time = 0
        self.need_to_move_new_position = True
        self.need_to_move_z_position = True
        self.should_pause_data_thread = False
        # TODO: distance > 1000 should not be hardcoded and somehow related to different kinds of stage devices.
        self.stage_distance_threshold = 1000

    def signal_func(self):
        if self.model.stop_acquisition:
            return False
        data_thread_is_paused = False
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

            # calculate delta_x, delta_y
            # TODO: Here.
            pos_dict = dict(
                map(
                    lambda ax: (
                        f"{ax}_abs",
                        self.positions[self.current_position_idx][ax],
                    ),
                    ["x", "y", "theta"],
                )
            )

            if self.current_position_idx > 0:
                delta_x = (
                    self.positions[self.current_position_idx]["x"]
                    - self.positions[self.current_position_idx - 1]["x"]
                )
                delta_y = (
                    self.positions[self.current_position_idx]["y"]
                    - self.positions[self.current_position_idx - 1]["y"]
                )
                delta_z = (
                    self.positions[self.current_position_idx]["z"]
                    - self.positions[self.current_position_idx - 1]["z"]
                    + self.z_stack_distance
                )
                delta_f = (
                    self.positions[self.current_position_idx]["f"]
                    - self.positions[self.current_position_idx - 1]["f"]
                    + self.f_stack_distance
                )
            else:
                delta_x = 0
                delta_y = 0
                delta_z = 0
                delta_f = 0

            # displacement = [delta_z, delta_f, delta_x, delta_y]
            # Check the distance between current position and previous position,
            # if it is too far, then we can call self.model.pause_data_thread() and
            # self.model.resume_data_thread() after the stage has completed the move
            # to the next position.

            self.should_pause_data_thread = any(
                distance > self.stage_distance_threshold
                for distance in [delta_x, delta_y, delta_z, delta_f]
            )
            if self.should_pause_data_thread:
                self.model.pause_data_thread()
                data_thread_is_paused = True

            self.model.move_stage(pos_dict, wait_until_done=True)
            self.model.logger.debug(f"*** ZStack move stage: {pos_dict}")

        if self.need_to_move_z_position:
            # move z, f
            # self.model.pause_data_thread()

            self.model.logger.debug(
                f"*** Zstack move stage: (z: {self.current_z_position}), "
                f"(f: {self.current_focus_position})"
            )
            print(
                f"*** Zstack move stage: (z: {self.current_z_position}), "
                f"(f: {self.current_focus_position})"
            )


            if self.should_pause_data_thread and not data_thread_is_paused:
                self.model.pause_data_thread()

            self.model.move_stage(
                {
                    "z_abs": self.current_z_position,
                    "f_abs": self.current_focus_position,
                },
                wait_until_done=True,
            )

        if self.should_pause_data_thread:
            self.model.resume_data_thread()
            self.should_pause_data_thread = False
        return True

    def signal_end(self):
        # end this node
        print("end signal")
        print(f"self.need_to_move_z_position = {self.need_to_move_z_position}")
        if self.model.stop_acquisition:
            return True

        if self.stack_cycling_mode != "per_stack":
            # update channel for each z position in 'per_slice'
            print("in != stack cycling mode")
            self.update_channel()
            self.need_to_move_z_position = self.current_channel_in_list == 0

        # in 'per_slice', move to next z position if all the channels have been acquired
        if self.need_to_move_z_position:
            print(f"self.need_to_move_z_position = {self.need_to_move_z_position}, if statement")
            # next z, f position
            self.current_z_position += self.z_step_size
            self.current_focus_position += self.focus_step_size

            # update z position moved time
            self.z_position_moved_time += 1

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
            if (
                self.z_stack_distance > self.stage_distance_threshold
                or self.f_stack_distance > self.stage_distance_threshold
            ):
                self.should_pause_data_thread = True

            # after running through a z-stack, update channel
            if self.stack_cycling_mode == "per_stack":
                print("in per stack if statment")
                print(f"self.current_channel_in_list = {self.current_channel_in_list}")
                print(f"self.need_to_move_new_position = {self.need_to_move_new_position}")
                self.update_channel()
                # if run through all the channels, move to next position
                if self.current_channel_in_list == 0:
                    print(f"channel list = 0, {self.current_channel_in_list}")
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
                {"z_abs": self.restore_z, "f_abs": self.restore_f},
                wait_until_done=False,
            )  # Update position
            return True

        return False

    def update_channel(self):
        print("in updated channel function")
        print(f"self.channels before + = {self.channels}")
        print(f"self.current_channel_in_list before + = {self.current_channel_in_list}")
        print(f"(self.current_channel_in_list + 1) % self.channels = {(self.current_channel_in_list + 1) % self.channels}")
        self.current_channel_in_list = (self.current_channel_in_list + 1) % self.channels
        print(f"self.channels after + = {self.channels}")
        print(f"self.current_channel_in_list after + = {self.current_channel_in_list}")
        self.model.active_microscope.prepare_next_channel()
        print("next channel prepared in update chanel")

    def pre_data_func(self):
        self.received_frames = 0
        self.total_frames = self.channels * self.number_z_steps * len(self.positions)

    def in_data_func(self, frame_ids):
        self.received_frames += len(frame_ids)
        if self.image_writer is not None:
            self.image_writer.save_image(frame_ids)

    def end_data_func(self):
        return self.received_frames >= self.total_frames

    def cleanup_data_func(self):
        if self.image_writer:
            self.image_writer.cleanup()


class ConProAcquisition:  # don't have the multi-position part for now
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

        self.conpro_cycling_mode = "per_stack"
        self.channels = [1]

        self.config_table = {
            "signal": {
                "init": self.pre_signal_func,
                "main": self.signal_func,
                "end": self.signal_end,
            },
            "node": {"node_type": "multi-step", "device_related": True},
        }
 
        self.model.move_stage({"z_abs": 0 })

    def pre_signal_func(self):
        import copy
        print("confocal projection started")

        microscope_state = self.model.configuration["experiment"]["MicroscopeState"]

        self.conpro_cycling_mode = microscope_state["conpro_cycling_mode"]
        # get available channels
        self.channels = microscope_state["selected_channels"]
        self.current_channel_in_list = 0

        self.n_plane = int(microscope_state["n_plane"])

        self.start_offset = float(copy.copy(microscope_state["offset_start"]))
        self.end_offset = float(copy.copy(microscope_state["offset_end"]))
        if self.n_plane == 1:
            self.offset_step_size = 0
        else:
            self.offset_step_size = (self.end_offset - self.start_offset) / float(
                self.n_plane - 1
            )

        self.timepoints = 1  # int(microscope_state['timepoints'])

        self.need_update_offset = True
        self.current_offset = self.start_offset
        self.offset_update_time = 0

        # self.model.move_stage({'z_abs': 0})

    def signal_func(self):
        print("signal func started")
        print(f"Signal with time {self.offset_update_time} and offset "
               f"{self.current_offset}")
        if self.model.stop_acquisition:
            return False

        if self.conpro_cycling_mode != "per_stack":
            # update channel for each z position in 'per_slice'
            self.update_channel()
            self.need_update_offset = self.current_channel_in_list == 0
            print("conpro per_stack")

        # in 'per_slice', update the offset if all the channels have been acquired
        if self.need_update_offset:
            # next z, f position
            # self.current_offset += self.offset_step_size
            print("offset movement")

            # update offset moved time
            self.offset_update_time += 1

        return True

    def signal_end(self):
        # end this node
        print("end signal started")
        if self.model.stop_acquisition:
            self.model.configuration["experiment"]["MicroscopeState"][
                "offset_start"
            ] = self.start_offset
            self.model.configuration["experiment"]["MicroscopeState"][
                "offset_end"
            ] = self.end_offset
            return True

        # decide whether to update offset
        if self.offset_update_time >= self.n_plane:
            self.timepoints -= 1

            self.model.configuration["experiment"]["MicroscopeState"][
                "offset_start"
            ] = self.start_offset
            self.model.configuration["experiment"]["MicroscopeState"][
                "offset_end"
            ] = self.end_offset

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
        print("Update Channel")
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

            # Downsample according to the desired magnification change. Note, we
            # could downsample by whatever we want.
            ds = int(curr_pixel_size / pixel_size)
            ds_img = downscale_local_mean(img, (ds, ds))

            # Threshold
            thresh_img = ds_img > filters.threshold_otsu(img)

            # Find the bounding box
            # In the real-deal, non-transposed image, x increase corresponds to a
            # decrease in row number y increase responds to an increase in row number
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

            # Update x and y start to initialize from the upper-left corner of the
            # current image, since this is how np.where indexed them. The + 0.5 in
            # x_start/y_start calculation shifts their starts back to the center of the
            # field of view.
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
