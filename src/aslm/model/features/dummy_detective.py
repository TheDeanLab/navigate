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

# Standard Library Imports
from queue import Queue
import random


class Dummy_Detective:
    def __init__(self, model):
        self.model = model
        # Queue
        self.detection_queue = Queue()
        self.frame_queue = Queue()
        # target frame id
        self.target_frame_id = -1

        self.config_table = {
            "signal": {
                "main": self.signal_func,
                "main-response": self.signal_response_func,
            },
            "data": {"pre-main": self.is_target_frame, "main": self.data_func},
            "node": {"need_response": True},
        }

    def signal_func(self):
        self.frame_queue.put(self.model.frame_id)

    def signal_response_func(self):
        frame_ids, r = self.detection_queue.get()
        print("******Signal detective get:", frame_ids, self.model.frame_id)
        return r

    def is_target_frame(self, frame_ids):
        try:
            if self.target_frame_id < 0:
                self.target_frame_id = self.frame_queue.get()
        except:
            return False
        return self.target_frame_id in frame_ids

    def data_func(self, frame_ids):
        # should detect #target_frame_id
        r = bool(random.getrandbits(1))
        print("detecting image: ", self.target_frame_id, "is", r)
        self.detection_queue.put((self.target_frame_id, r))
        return r

    def generate_meta_data(self, *args):
        print("This frame is detective", self.model.frame_id)
        return True
