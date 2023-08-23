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

from math import ceil

from aslm.model.analysis.boundary_detect import find_tissue_boundary_2d

def detect_tissue(image_data, percentage=0.0):
    width = 50
    boundary = find_tissue_boundary_2d(image_data, width)
    tissue_squares = 0
    for row in boundary:
        if row:
            tissue_squares += row[1] - row[0] + 1
    return tissue_squares / (ceil(image_data.shape[0]/width) * ceil(image_data.shape[1]/width)) > percentage

def detect_tissue2(image_data, percentage=0.0):
    return False

class DetectTissueInStack:
    def __init__(self, model, planes=1, percentage=0.75, detect_func=None):
        self.model = model
        self.planes = int(planes)
        self.percentage = float(percentage)
        #if not specify a detect function, use the default one
        if detect_func is None:
            self.detect_func = detect_tissue
        else:
            self.detect_func = detect_func

        self.config_table = {
            "signal": {
                "init": self.pre_func_signal,
                "main": self.in_func_signal,
                "end": self.end_func_signal,
            },
            "data": {
                "init": self.pre_func_data,
                "main": self.in_func_data,
                "end": self.end_func_data,
            },
            "node": {"node_type": "multi-step", "device_related": True},
        }

    def pre_func_signal(self):
        microscope_config = self.model.configuration["experiment"]["MicroscopeState"]
        # get current z and f position
        pos = self.model.get_stage_position()
        self.current_z_pos = pos["z_pos"] + float(microscope_config["start_position"])
        self.current_f_pos = pos["f_pos"] + float(microscope_config["start_focus"])
        # calculate Z and F stage step sizes
        # initialize place count
        z_pos_range = float(microscope_config["end_position"]) - float(microscope_config["start_position"])
        f_pos_range = float(microscope_config["end_focus"]) - float(microscope_config["start_focus"])
        if self.planes == 1:
            self.current_z_pos = self.current_z_pos + z_pos_range / 2
            self.current_f_pos = self.current_f_pos + f_pos_range / 2
        else:
            self.z_step = (z_pos_range) / (self.planes - 1)
            self.f_step = (f_pos_range) / (self.planes - 1)
        self.scan_num = 0

    def in_func_signal(self):
        # move to Z anf F position
        self.model.logger.debug(f"move to position (z, f): ({self.current_z_pos}, {self.current_f_pos}), {self.scan_num}, {self.model.frame_id}")
        self.model.move_stage(
            {
                "z_abs": self.current_z_pos,
                "f_abs": self.current_f_pos
            },
            wait_until_done = True
        )
        self.scan_num += 1

    def end_func_signal(self):
        self.model.logger.debug(f"*** detect tissue signal end function: "
                                f"{self.scan_num}")
        if self.scan_num >= self.planes:
            return True
        self.current_z_pos += self.z_step
        self.current_f_pos += self.f_step
        return False

    def pre_func_data(self):
        self.received_frames = 0
        self.has_tissue_flag = False

    def in_func_data(self, frame_ids):
        if not self.has_tissue_flag:
            for frame_id in frame_ids:
                # check if the frame has tissue
                r = self.detect_func(self.model.data_buffer[frame_id], self.percentage)
                if r:
                    self.model.logger.debug(f"*** this frame has enough percentage of tissue!{frame_id}")
                    self.has_tissue_flag = True
                    break
        self.received_frames += len(frame_ids)
        return self.has_tissue_flag

    def end_func_data(self):
        return self.received_frames >= self.planes


class DetectTissueInStackAndRecord(DetectTissueInStack):
    def __init__(self, model, planes=1, percentage=0.75, position_records=[], detect_func=None):
        super().__init__(model, planes, percentage, detect_func)
        self.position_records = position_records

    def pre_func_data(self):
        super().pre_func_data()
        self.position_records.append(True)

    def end_func_data(self):
        self.position_records[-1] = self.has_tissue_flag
        return super().end_func_data()

class RemoveEmptyPositions:
    def __init__(self, model, position_flags=[]):
        self.model = model
        self.position_records = position_flags
        self.config_table = {"signal": {"main": self.signal_func}}

    def signal_func(self):
        self.model.event_queue.put(("remove_positions", self.position_records))
        return True