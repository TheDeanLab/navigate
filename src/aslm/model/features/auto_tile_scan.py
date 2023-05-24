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

from aslm.model.features.autofocus import Autofocus

class CalculateFocusRange:
    def __init__(self, model):
        self.model = model

        self.autofocus = Autofocus(model)

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
        self.model.active_microscope.current_channel = 0
        self.model.active_microscope.prepare_next_channel()
        self.autofocus.pre_func_signal()
        self.autofocus_count = 0
        self.focus_start_pos = None
        self.focus_end_pos = None

        # get current z pos, calculate last z pos in a stack
        stage_pos = self.model.get_stage_position()
        self.current_z_pos = stage_pos["z_pos"]
        self.last_z_pos = self.current_z_pos + float(self.model.configuration["experiment"]["MicroscopeState"]["end_position"])

    def in_func_signal(self):
        if self.autofocus_count == 0:
            self.focus_start_pos = self.autofocus.in_func_signal()
        else:
            self.focus_end_pos = self.autofocus.in_func_signal()

            # calculate the slope and save it
            if self.focus_end_pos:
                microscope_state = self.model.configuration["experiment"]["MicroscopeState"]
                microscope_state["end_focus"] = float(microscope_state["start_focus"]) + self.focus_end_pos - self.focus_start_pos

    def end_func_signal(self):
        r = self.autofocus.end_func_signal()
        if r:
            self.autofocus_count += 1
            if self.autofocus_count == 1:
                # move one z step
                # TODO: should the focus move at the same time?
                self.model.move_stage({"z_abs": self.last_z_pos}, wait_until_done=True)
                self.autofocus.pre_func_signal()
        return self.autofocus_count >= 2
    
    def pre_func_data(self):
        self.autofocus.pre_func_data()

    def in_func_data(self, frame_ids=[]):
        self.autofocus.in_func_data(frame_ids)

    def end_func_data(self):
        r = self.autofocus.end_func_data()
        if r:
            self.autofocus.pre_func_data()

        return r and self.autofocus_count >= 2
