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

from aslm.model.analysis.boundary_detect import has_tissue

def detect_tissue(image_data):
    return has_tissue(image_data, 0, 0, image_data.shape[0], image_data.shape[1])

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
        # calculate Z and F stage step sizes
        # initialize place count
        microscope_config = self.model.configuration["experiment"]["MicroscopeState"]
        self.z_step = (float(microscope_config["end_position"]) - float(microscope_config["start_position"])) / (self.planes - 1)
        self.f_step = (float(microscope_config["end_focus"]) - float(microscope_config["start_focus"])) / (self.planes - 1)
        self.scan_num = 0
        # get current z position
        pos = self.model.get_stage_position()
        self.current_z_pos = pos["z_pos"] + float(microscope_config["start_position"])
        self.current_f_pos = pos["f_pos"] + float(microscope_config["start_focus"])
        # stop scanning flag
        self.stop_flag = False
        self.stop_signal_flag = False

    def in_func_signal(self):
        # move to Z anf F position
        self.model.logger.debug(f"move to position (z, f): ({self.current_z_pos}, {self.current_f_pos}), {self.scan_num}")
        self.model.move_stage(
            {
                "z_abs": self.current_z_pos,
                "f_abs": self.current_f_pos
            },
            wait_until_done = True
        )
        self.scan_num += 1

    def end_func_signal(self):
        # check if scan all positions
        if self.stop_flag or self.scan_num >= self.planes:
            self.stop_signal_flag = True
            return True
        self.current_z_pos += self.z_step
        self.current_f_pos += self.f_step
        return False

    def pre_func_data(self):
        # calculate non-tissue ratio
        self.non_tissue_ratio = 1 - self.percentage
        self.received_frames = 0
        self.non_tissue_num = 0
        self.has_tissue_flag = False

    def in_func_data(self, frame_ids):
        if not self.stop_flag:
            for i, frame_id in enumerate(frame_ids):
                # check if the frame has tissue
                r = self.detect_func(self.model.data_buffer[frame_id])
                if not r:
                    self.non_tissue_num += 1
                if (self.non_tissue_num / self.planes > self.non_tissue_ratio):
                    self.stop_flag = True
                    break
                elif (self.received_frames+i+1-self.non_tissue_num)/self.planes >= self.percentage:
                    self.stop_flag = True
                    self.has_tissue_flag = True
                    break
        self.received_frames += len(frame_ids)
        return not self.stop_flag

    def end_func_data(self):
        return self.stop_signal_flag and self.received_frames >= self.scan_num


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