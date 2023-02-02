# Copyright (c) 2021-2023  The University of Texas Southwestern Medical Center.
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

import pytest

from aslm.model.features.volume_search import VolumeSearch


class TestVolumeSearch:
    @pytest.fixture(autouse=True)
    def _prepare_test(self, dummy_model_to_test_features):
        self.model = dummy_model_to_test_features
        self.config = self.model.configuration["experiment"]["MicroscopeState"]
        self.record_num = 0
        self.feature_list = [[{"name": VolumeSearch}]]

        self.model.configuration["experiment"]["StageParameters"]["z"] = 0
        self.model.configuration["experiment"]["StageParameters"]["f"] = 0

        self.config["start_position"] = 0
        self.config["end_position"] = 200
        self.config["number_z_steps"] = 5
        self.config["step_size"] = (
            self.config["end_position"] - self.config["start_position"]
        ) / self.config["number_z_steps"]

    def get_next_record(self, record_prefix, idx):
        idx += 1
        while self.model.signal_records[idx][0] != record_prefix:
            idx += 1
            if idx >= self.record_num:
                assert False, "Some device movements are missed!"
        return idx

    def verify_volume_search(self):
        idx = -1

        z_pos = self.config["start_position"]
        f_pos = self.config["start_focus"]

        for j in range(self.config["number_z_steps"]):
            idx = self.get_next_record("move_stage", idx)
            pos_moved = self.model.signal_records[idx][1][0]

            # z, f
            assert pos_moved["z_abs"] == z_pos + j * self.config["step_size"], (
                f"should move to z: {z_pos + j * self.config['step_size']}, "
                f"but moved to {pos_moved['z_abs']}"
            )
            assert pos_moved["f_abs"] == f_pos + j * self.config["step_size"], (
                f"should move to z: {f_pos + j * self.config['step_size']}, "
                f"but moved to {pos_moved['f_abs']}"
            )
        assert True

    @pytest.mark.skip("hangs")
    def test_box_volume_search(self):
        # from aslm.tools.sdf import volume_from_sdf, box

        print("starting test")
        # self.model.configuration["experiment"]["CameraParameters"]["x_pixels"] = 128
        # self.model.data_buffer = volume_from_sdf(lambda p: box(p, (15,15,30,)), 128)

        print("starting model")
        self.model.start(self.feature_list)
        self.verify_volume_search()
