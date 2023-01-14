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

import random
import pytest

from aslm.model.features.common_features import ZStackAcquisition


class TestZStack:
    @pytest.fixture(autouse=True)
    def _prepare_test(self, dummy_model_to_test_features):
        self.model = dummy_model_to_test_features
        self.config = self.model.configuration["experiment"]["MicroscopeState"]
        self.record_num = 0
        self.feature_list = [[{"name": ZStackAcquisition}]]

        self.config["start_position"] = 0
        self.config["end_position"] = 200
        self.config["number_z_steps"] = 5
        self.config["step_size"] = (
            self.config["end_position"] - self.config["start_position"]
        ) / self.config["number_z_steps"]

        position_list = self.model.configuration["experiment"]["MultiPositions"][
            "stage_positions"
        ]
        if len(position_list) < 5:
            for i in range(5):
                pos = {}
                for axis in ["x", "y", "z", "theta", "f"]:
                    pos[axis] = random.randint(1, 10000)
                position_list.append(pos)

    def get_next_record(self, record_prefix, idx):
        idx += 1
        while self.model.signal_records[idx][0] != record_prefix:
            idx += 1
            if idx >= self.record_num:
                assert False, "Some device movements are missed!"
        return idx

    def z_stack_verification(self):
        self.record_num = len(self.model.signal_records)
        # save all the selected channels
        selected_channels = []
        for channel_key in self.config["channels"].keys():
            if self.config["channels"][channel_key]["is_selected"]:
                selected_channels.append(dict(self.config["channels"][channel_key]))
                selected_channels[-1]["id"] = int(channel_key[len("channel_") :])

        # restore z and f
        pos_dict = self.model.get_stage_position()
        restore_z = pos_dict["z_pos"]
        restore_f = pos_dict["f_pos"]

        mode = self.config["stack_cycling_mode"]  # per_z/pre_stack
        is_multiposition = self.config["is_multiposition"]
        if is_multiposition:
            positions = self.model.configuration["experiment"]["MultiPositions"][
                "stage_positions"
            ]
        else:
            pos_dict = self.model.configuration["experiment"]["StageParameters"]
            positions = [
                {
                    "x": pos_dict["x"],
                    "y": pos_dict["y"],
                    "z": self.config.get("stack_z_origin", pos_dict["z"]),
                    "theta": pos_dict["theta"],
                    "f": self.config.get("stack_focus_origin", pos_dict["f"]),
                }
            ]

        z_step = self.config["step_size"]
        f_step = (self.config["end_focus"] - self.config["start_focus"]) / self.config[
            "number_z_steps"
        ]

        frame_id = 0
        idx = -1
        change_channel_func_str = "active_microscope.prepare_next_channel"

        for i, pos in enumerate(positions):

            idx = self.get_next_record("move_stage", idx)

            # x, y, theta
            pos_moved = self.model.signal_records[idx][1][0]
            for axis in ["x", "y", "theta"]:
                assert (
                    pos[axis] == pos_moved[axis + "_abs"]
                ), f"should move to {axis}: {pos[axis]}, but moved to {pos_moved[axis + '_abs']}"

            z_pos = pos["z"] + self.config["start_position"]
            f_pos = pos["f"] + self.config["start_focus"]

            if mode == "per_z":
                for j in range(self.config["number_z_steps"]):
                    idx = self.get_next_record("move_stage", idx)

                    pos_moved = self.model.signal_records[idx][1][0]
                    # z, f
                    assert (
                        pos_moved["z_abs"] == z_pos + j * z_step
                    ), f"should move to z: {z_pos + j * z_step}, but moved to {pos_moved['z_abs']}"
                    assert (
                        pos_moved["f_abs"] == f_pos + j * f_step
                    ), f"should move to z: {f_pos + j * f_step}, but moved to {pos_moved['f_abs']}"

                    # channel
                    for k in range(len(selected_channels)):
                        idx = self.get_next_record(change_channel_func_str, idx)
                        # c = selected_channels[(k+1) % len(selected_channels)]['id']
                        # assert self.model.signal_records[idx][1][0] == c, f"{frame_id} should change to channel {c}, but it's {model.signal_records[idx][1][0]}"
                        assert (
                            self.model.signal_records[idx][2]["__test_frame_id"]
                            == frame_id
                        ), f"prepare next channel(change chanel) should happen at {frame_id}"
                        frame_id += 1

            else:  # per_stack
                for k in range(len(selected_channels)):
                    # z
                    for j in range(self.config["number_z_steps"]):
                        idx = self.get_next_record("move_stage", idx)

                        pos_moved = self.model.signal_records[idx][1][0]
                        # z, f
                        assert (
                            pos_moved["z_abs"] == z_pos + j * z_step
                        ), f"should move to z: {z_pos + j * z_step}, but moved to {pos_moved['z_abs']}"
                        assert (
                            pos_moved["f_abs"] == f_pos + j * f_step
                        ), f"should move to z: {f_pos + j * f_step}, but moved to {pos_moved['f_abs']}"
                        frame_id += 1

                    idx = self.get_next_record(change_channel_func_str, idx)
                    # c = selected_channels[(k+1) % len(selected_channels)]['id']
                    # assert self.model.signal_records[idx][1][0] == c, f"{frame_id} should change to channel {c}, but it's {self.model.signal_records[idx][1][0]}"
                    assert (
                        self.model.signal_records[idx][2]["__test_frame_id"]
                        == frame_id - 1
                    ), f"prepare next channel(change chanel) should happen at {frame_id - 1}"

        # restore z, f
        idx = self.get_next_record("move_stage", idx)
        pos_moved = self.model.signal_records[idx][1][0]
        assert (
            pos_moved["z_abs"] == restore_z
        ), f"should restore z to {restore_z}, but moved to {pos_moved['z_abs']}"
        assert (
            pos_moved["f_abs"] == restore_f
        ), f"should restore f to {restore_f}, but moved to {pos_moved['f_abs']}"

        assert (
            idx == self.record_num - 1
        ), f"should verify all the stage movements! {idx} -- {self.record_num - 1}"

    def test_single_position_one_channel_per_z(self):
        # single position
        self.config["is_multiposition"] = False

        # 1 channel per_z
        self.config["stack_cycling_mode"] = "per_z"
        self.config["selected_channels"] = 1
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = False
        self.config["channels"]["channel_3"]["is_selected"] = False
        self.model.start(self.feature_list)
        print(self.model.signal_records)
        self.z_stack_verification()

    def test_single_position_one_channel_per_stack(self):
        # single position
        self.config["is_multiposition"] = False

        # 1 channel per_stack
        self.config["stack_cycling_mode"] = "per_stack"
        self.config["selected_channels"] = 1
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = False
        self.config["channels"]["channel_3"]["is_selected"] = False
        self.model.start(self.feature_list)
        self.z_stack_verification()

    def test_single_position_two_channels_per_z(self):
        # single position
        self.config["is_multiposition"] = False

        # 2 channels per_z
        self.config["stack_cycling_mode"] = "per_z"
        self.config["selected_channels"] = 2
        for i in range(3):
            for j in range(3):
                self.config["channels"]["channel_" + str(j + 1)]["is_selected"] = True
            self.config["channels"]["channel_" + str(i + 1)]["is_selected"] = False
            self.model.start(self.feature_list)
            self.z_stack_verification()

    def test_single_position_two_channels_per_stack(self):
        # single position
        self.config["is_multiposition"] = False

        # 2 channels per_stack
        self.config["stack_cycling_mode"] = "per_stack"
        self.config["selected_channels"] = 2
        for i in range(3):
            for j in range(3):
                self.config["channels"]["channel_" + str(j + 1)]["is_selected"] = True
            self.config["channels"]["channel_" + str(i + 1)]["is_selected"] = False
            self.model.start(self.feature_list)
            self.z_stack_verification()

    def test_single_position_three_channels_per_stack(self):
        # single position
        self.config["is_multiposition"] = False

        # 3 channels per_stack
        self.config["selected_channels"] = 3
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = True
        self.config["channels"]["channel_3"]["is_selected"] = True
        self.config["stack_cycling_mode"] = "per_stack"
        self.model.start(self.feature_list)
        self.z_stack_verification()

    def test_single_position_three_channels_per_z(self):
        # single position
        self.config["is_multiposition"] = False

        # 3 channels per_z
        self.config["selected_channels"] = 3
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = True
        self.config["channels"]["channel_3"]["is_selected"] = True
        self.config["stack_cycling_mode"] = "per_z"
        self.model.start(self.feature_list)
        self.z_stack_verification()

    def test_multi_position_one_channel_per_z(self):
        # multi position
        self.config["is_multiposition"] = True

        # 1 channel per_z
        self.config["stack_cycling_mode"] = "per_z"
        self.config["selected_channels"] = 1
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = False
        self.config["channels"]["channel_3"]["is_selected"] = False
        self.model.start(self.feature_list)
        self.z_stack_verification()

        self.config["is_multiposition"] = False

    def test_multi_position_one_channel_per_stack(self):
        self.config["is_multiposition"] = True

        # 1 channel per_stack
        self.config["stack_cycling_mode"] = "per_stack"
        self.config["selected_channels"] = 1
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = False
        self.config["channels"]["channel_3"]["is_selected"] = False
        self.model.start(self.feature_list)
        self.z_stack_verification()

        self.config["is_multiposition"] = False

    def test_multi_position_two_channels_per_z(self):
        self.config["is_multiposition"] = True

        # 2 channels per_z
        self.config["stack_cycling_mode"] = "per_z"
        self.config["selected_channels"] = 2
        for i in range(3):
            for j in range(3):
                self.config["channels"]["channel_" + str(j + 1)]["is_selected"] = True
            self.config["channels"]["channel_" + str(i + 1)]["is_selected"] = False
            self.model.start(self.feature_list)
            self.z_stack_verification()

        self.config["is_multiposition"] = False

    def test_multi_position_two_channels_per_stack(self):
        self.config["is_multiposition"] = True

        # 2 channels per_stack
        self.config["stack_cycling_mode"] = "per_stack"
        self.config["selected_channels"] = 2
        for i in range(3):
            for j in range(3):
                self.config["channels"]["channel_" + str(j + 1)]["is_selected"] = True
            self.config["channels"]["channel_" + str(i + 1)]["is_selected"] = False
            self.model.start(self.feature_list)
            self.z_stack_verification()

        self.config["is_multiposition"] = False

    def test_multi_position_three_channels_per_stack(self):
        self.config["is_multiposition"] = True

        # 3 channels per_stack
        self.config["selected_channels"] = 3
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = True
        self.config["channels"]["channel_3"]["is_selected"] = True
        self.config["stack_cycling_mode"] = "per_stack"
        self.model.start(self.feature_list)
        self.z_stack_verification()

        self.config["is_multiposition"] = False

    def test_multi_position_three_channels_per_z(self):
        self.config["is_multiposition"] = True

        # 3 channels per_z
        self.config["selected_channels"] = 3
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = True
        self.config["channels"]["channel_3"]["is_selected"] = True
        self.config["stack_cycling_mode"] = "per_z"
        self.model.start(self.feature_list)
        self.z_stack_verification()

        self.config["is_multiposition"] = False
