# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
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


import random
from unittest.mock import MagicMock

import pytest
from navigate.model.devices.configuration_schema import CollectionSpec
from navigate.model.features.common_features import (
    ASIZStackAcquisition,
    MoveToNextPositionInMultiPositionTable,
    ZStackAcquisition,
    stage_move_requires_pause,
)


def test_theta_move_requires_pause_below_linear_threshold():
    assert stage_move_requires_pause([0, 0, 0], 1000, theta_delta=1)


def test_no_stage_move_does_not_require_pause():
    assert not stage_move_requires_pause([0, 0, 0], 1000, theta_delta=0)


def test_multiposition_theta_move_pauses_data_thread(dummy_model_to_test_features):
    model = dummy_model_to_test_features
    model.signal_records = []
    model.configuration["experiment"]["StageParameters"].update(
        {"x": 0, "y": 0, "z": 0, "theta": 0, "f": 0}
    )
    model.configuration["multi_positions"] = [
        ["X", "Y", "Z", "THETA", "F"],
        [0, 0, 0, 45, 0],
    ]
    feature = MoveToNextPositionInMultiPositionTable(model)

    feature.pre_signal_func()
    feature.signal_func()

    record_names = [record[0] for record in model.signal_records]
    assert record_names.index("pause_data_thread") < record_names.index("move_stage")
    assert record_names.index("move_stage") < record_names.index("resume_data_thread")


def test_multiposition_table_offset_schema_is_axis_mapping():
    """Position offsets are edited as an axis-keyed mapping."""
    offset_schema = MoveToNextPositionInMultiPositionTable.parameter_schema["offset"]

    assert isinstance(offset_schema, CollectionSpec)
    assert offset_schema.storage == "single_mapping"
    assert offset_schema.item_schema == {}
    assert offset_schema.dynamic_source == "stage_axes"


def test_multiposition_table_accepts_axis_offset_mapping(dummy_model_to_test_features):
    """Axis-keyed offsets are applied to multi-position moves."""
    model = dummy_model_to_test_features
    model.signal_records = []
    model.configuration["experiment"]["StageParameters"].update(
        {"x": 0, "y": 0, "z": 0, "theta": 0, "f": 0}
    )
    model.configuration["multi_positions"] = [
        ["X", "Y", "Z", "THETA", "F"],
        [1, 2, 3, 4, 5],
    ]
    feature = MoveToNextPositionInMultiPositionTable(
        model,
        offset={"x": 10, "y": "20", "z": None, "theta": -5, "f": 0.5},
    )

    feature.pre_signal_func()
    feature.signal_func()

    move_stage_records = [
        record for record in model.signal_records if record[0] == "move_stage"
    ]
    assert move_stage_records[-1][1][0] == {
        "x_abs": 11.0,
        "y_abs": 22.0,
        "z_abs": 3,
        "theta_abs": -1.0,
        "f_abs": 5.5,
    }


def test_z_stack_preserves_primary_axis_restore_and_pre_position(
    dummy_model_to_test_features,
):
    model = dummy_model_to_test_features
    model.virtual_microscopes = {}
    microscope_state = model.configuration["experiment"]["MicroscopeState"]
    stage_parameters = model.configuration["experiment"]["StageParameters"]
    previous_primary_z_axis = microscope_state.get("primary_z_axis")
    previous_primary_f_axis = microscope_state.get("primary_f_axis")
    previous_stage_parameters = dict(stage_parameters)

    try:
        microscope_state["is_multiposition"] = False
        microscope_state["primary_z_axis"] = "theta"
        microscope_state["primary_f_axis"] = "x"
        stage_parameters.update({"x": 11, "y": 22, "z": 33, "theta": 44, "f": 55})

        feature = ZStackAcquisition(model)
        feature.pre_signal_func()

        assert feature.restore_z == 44
        assert feature.restore_f == 11
        assert feature.pre_position == {
            "x": 11.0,
            "y": 22.0,
            "z": 33.0,
            "theta": 44.0,
            "f": 55.0,
        }
    finally:
        if previous_primary_z_axis is None:
            microscope_state.pop("primary_z_axis", None)
        else:
            microscope_state["primary_z_axis"] = previous_primary_z_axis
        if previous_primary_f_axis is None:
            microscope_state.pop("primary_f_axis", None)
        else:
            microscope_state["primary_f_axis"] = previous_primary_f_axis
        stage_parameters.update(previous_stage_parameters)


def test_z_stack_channel_defocus_is_relative_to_zero_defocus_reference(
    dummy_model_to_test_features,
):
    feature = ZStackAcquisition(dummy_model_to_test_features, saving_flag=False)
    feature.defocus = [3.0, -1.5]
    feature.first_channel_defocus = 3.0
    feature.start_focus = 103.0
    feature.current_position = {"f": 0.0}
    feature.primary_f_axis = "f"

    assert feature._focus_target_for_channel(0) == pytest.approx(103.0)
    assert feature._focus_target_for_channel(1) == pytest.approx(98.5)


def test_asi_z_stack_uses_channel_defocus_in_stage_move(
    dummy_model_to_test_features,
):
    model = dummy_model_to_test_features
    model.signal_records = []
    feature = ASIZStackAcquisition(model, saving_flag=False)
    feature.stage_axes = ["x", "y", "z", "theta", "f"]
    feature.axes_index = [0, 1, 2, 3, 4]
    feature.tiling_axes = ["x", "y", "theta"]
    feature.primary_z_axis = "z"
    feature.primary_f_axis = "f"
    feature.secondary_stack_settings = {}
    feature.positions = [[0.0, 0.0, 0.0, 0.0, 0.0]]
    feature.current_position_idx = 0
    feature.current_position = {"x": 0.0, "y": 0.0, "z": 0.0, "theta": 0.0, "f": 0.0}
    feature.pre_position = feature.current_position
    feature.need_to_move_new_position = True
    feature.start_z_position = 0.0
    feature.start_focus = 103.0
    feature.z_stack_distance = 0.0
    feature.f_stack_distance = 0.0
    feature.stage_distance_threshold = 1000
    feature.defocus = [3.0, -1.5]
    feature.first_channel_defocus = 3.0
    feature.current_channel_in_list = 1

    feature.signal_func()

    move_stage_records = [
        record for record in model.signal_records if record[0] == "move_stage"
    ]
    assert move_stage_records[-1][1][0]["f_abs"] == pytest.approx(98.5)


def test_z_stack_emits_highlight_event_for_active_position(
    dummy_model_to_test_features, monkeypatch
):
    model = dummy_model_to_test_features
    event_queue = MagicMock()
    monkeypatch.setattr(model, "event_queue", event_queue, raising=False)
    feature = ZStackAcquisition(model, saving_flag=False)
    feature.stage_axes = ["x", "y", "z", "theta", "f"]
    feature.axes_index = [0, 1, 2, 3, 4]
    feature.tiling_axes = ["x", "y", "theta"]
    feature.primary_z_axis = "z"
    feature.primary_f_axis = "f"
    feature.secondary_stack_settings = {}
    feature.positions = [
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 2.0, 3.0, 4.0, 5.0],
    ]
    feature.current_position_idx = 1
    feature.current_position = {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "theta": 0.0,
        "f": 0.0,
    }
    feature.pre_position = feature.current_position
    feature.need_to_move_new_position = True
    feature.need_to_move_z_position = False
    feature.start_z_position = 0.0
    feature.start_focus = 0.0
    feature.z_stack_distance = 0.0
    feature.f_stack_distance = 0.0
    feature.stage_distance_threshold = 1000
    feature.defocus = [0.0]
    feature.first_channel_defocus = 0.0
    feature.current_channel_in_list = 0

    feature.signal_func()

    event_queue.put.assert_called_once_with(("highlight_position", 1))


class TestZStack:
    @pytest.fixture(autouse=True)
    def _prepare_test(self, dummy_model_to_test_features):
        self.model = dummy_model_to_test_features
        self.model.virtual_microscopes = {}
        self.config = self.model.configuration["experiment"]["MicroscopeState"]
        self.record_num = 0
        self.feature_list = [[{"name": ZStackAcquisition}]]

        self.config["start_position"] = 0
        self.config["end_position"] = 200
        self.config["number_z_steps"] = 5
        self.config["step_size"] = (
            self.config["end_position"] - self.config["start_position"]
        ) / self.config["number_z_steps"]

        position_list = self.model.configuration["multi_positions"]
        if len(position_list) < 5:
            for i in range(5):
                pos = [0] * len(position_list[0])
                for i in range(len(position_list[0])):
                    pos[i] = random.randint(1, 10000)
                position_list.append(pos)

    def get_next_record(self, record_prefix, idx):
        idx += 1
        while self.model.signal_records[idx][0] != record_prefix:
            idx += 1
            if idx >= self.record_num:
                assert False, "Some device movements are missed!"
        return idx

    def exist_record(self, record_prefix, idx_start, idx_end):
        for i in range(idx_start, idx_end + 1):
            if self.model.signal_records[i][0] == record_prefix:
                return True
        return False

    def z_stack_verification(self):
        self.record_num = len(self.model.signal_records)
        change_channel_func_str = "active_microscope.prepare_next_channel"
        close_daq_tasks_str = "active_microscope.daq.stop_acquisition"
        create_daq_tasks_str = "active_microscope.daq.prepare_acquisition"
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
            positions = self.model.configuration["multi_positions"][1:]
        else:
            pos_dict = self.model.configuration["experiment"]["StageParameters"]
            positions = [
                [
                    pos_dict["x"],
                    pos_dict["y"],
                    self.config.get("stack_z_origin", pos_dict["z"]),
                    pos_dict["theta"],
                    self.config.get("stack_focus_origin", pos_dict["f"]),
                ]
            ]

        z_step = self.config["step_size"]
        f_step = (self.config["end_focus"] - self.config["start_focus"]) / self.config[
            "number_z_steps"
        ]

        frame_id = 0
        idx = -1
        z_moved_times = 0
        if mode == "per_z":
            z_should_move_times = len(positions) * int(self.config["number_z_steps"])
        else:
            z_should_move_times = (
                len(selected_channels)
                * len(positions)
                * int(self.config["number_z_steps"])
            )

        has_ni_galvo_stage = self.model.configuration["configuration"]["microscopes"][
            self.config["microscope_name"]
        ]["stage"]["has_ni_galvo_stage"]
        prepared_next_channel = False

        # prepare first channel in pre_signal_func
        idx = self.get_next_record(change_channel_func_str, idx)
        prepared_next_channel = True
        pre_change_channel_idx = idx
        assert (
            self.model.signal_records[idx][2]["__test_frame_id_completed"] == -1
        ), "prepare first channel should happen before 0"
        assert (
            self.model.signal_records[idx][2]["__test_frame_id"] == 0
        ), "prepare first channel should happen for frame: 0"

        for i, pos in enumerate(positions):

            idx = self.get_next_record("move_stage", idx)

            # x, y, theta
            pos_moved = self.model.signal_records[idx][1][0]
            for i, axis in [(0, "x"), (1, "y"), (3, "theta")]:
                assert pos[i] == pos_moved[axis + "_abs"], (
                    f"should move to {axis}: {pos[i]}, "
                    f"but moved to {pos_moved[axis + '_abs']}"
                )

            # (x, y, z, theta, f)
            z_pos = pos[2] + self.config["start_position"]
            first_channel_defocus = (
                selected_channels[0]["defocus"] if selected_channels else 0.0
            )
            zero_defocus_f_pos = (
                pos[4] + self.config["start_focus"] - first_channel_defocus
            )

            if mode == "per_z":
                f_pos = zero_defocus_f_pos + selected_channels[0]["defocus"]
                for j in range(self.config["number_z_steps"]):
                    idx = self.get_next_record("move_stage", idx)

                    pos_moved = self.model.signal_records[idx][1][0]
                    # z, f
                    assert pos_moved["z_abs"] == z_pos + j * z_step, (
                        f"should move to z: {z_pos + j * z_step}, "
                        f"but moved to {pos_moved['z_abs']}"
                    )
                    assert pos_moved["f_abs"] == f_pos + j * f_step, (
                        f"should move to f: {f_pos + j * f_step}, "
                        f"but moved to {pos_moved['f_abs']}"
                    )
                    z_moved_times += 1

                    # if the system has NIGalvo stage, should close the DAQ tasks and
                    # then create new tasks to override the new waveforms
                    if has_ni_galvo_stage and prepared_next_channel:
                        idx = self.get_next_record(close_daq_tasks_str, idx)
                        pre_change_channel_idx = idx
                        assert (
                            self.model.signal_records[idx][2]["__test_frame_id"]
                            == frame_id
                        ), f"close DAQ tasks should happen before {frame_id}"

                        idx = self.get_next_record(create_daq_tasks_str, idx)
                        pre_change_channel_idx = idx
                        assert (
                            self.model.signal_records[idx][2]["__test_frame_id"]
                            == frame_id
                        ), f"create DAQ tasks should happen before {frame_id}"

                    # channel
                    for k in range(len(selected_channels)):
                        idx = self.get_next_record(change_channel_func_str, idx)
                        prepared_next_channel = True
                        assert (
                            self.model.signal_records[idx][2]["__test_frame_id"]
                            == frame_id
                        ), (
                            "prepare next channel (change channel) "
                            f"should happen after {frame_id}"
                        )

                        assert (
                            self.model.signal_records[idx][2][
                                "__test_frame_id_completed"
                            ]
                            == self.model.signal_records[idx][2]["__test_frame_id"]
                        ), (
                            "prepare next channel (change channel) "
                            "should happen inside signal_end_func()"
                        )

                        assert (
                            self.exist_record(
                                change_channel_func_str,
                                pre_change_channel_idx + 1,
                                idx - 1,
                            )
                            is False
                        ), (
                            "prepare next channel (change channel) "
                            "should not happen more than once"
                        )
                        pre_change_channel_idx = idx
                        frame_id += 1

            else:  # per_stack
                for k in range(len(selected_channels)):
                    # z
                    f_pos = zero_defocus_f_pos + selected_channels[k]["defocus"]
                    for j in range(self.config["number_z_steps"]):
                        idx = self.get_next_record("move_stage", idx)

                        pos_moved = self.model.signal_records[idx][1][0]
                        # z, f
                        assert pos_moved["z_abs"] == z_pos + j * z_step, (
                            f"should move to z: {z_pos + j * z_step}, "
                            f"but moved to {pos_moved['z_abs']}"
                        )
                        assert pos_moved["f_abs"] == f_pos + j * f_step, (
                            f"should move to f: {f_pos + j * f_step}, "
                            f"but moved to {pos_moved['f_abs']}"
                        )
                        z_moved_times += 1
                        frame_id += 1
                    idx = self.get_next_record(change_channel_func_str, idx)
                    prepared_next_channel = True
                    assert (
                        self.model.signal_records[idx][2]["__test_frame_id"]
                        == frame_id - 1
                    ), (
                        "prepare next channel (change channel) "
                        f"should happen at {frame_id - 1}"
                    )

        # restore z, f
        idx = self.get_next_record("move_stage", idx)
        pos_moved = self.model.signal_records[idx][1][0]
        assert (
            pos_moved["z_abs"] == restore_z
        ), f"should restore z to {restore_z}, but moved to {pos_moved['z_abs']}"
        assert (
            pos_moved["f_abs"] == restore_f
        ), f"should restore f to {restore_f}, but moved to {pos_moved['f_abs']}"

        assert z_moved_times == z_should_move_times, (
            f"should verify all the stage movements! {z_moved_times} -- "
            f"{z_should_move_times}"
        )

    @pytest.mark.parametrize("has_ni_galvo_stage", [False])
    def test_single_position_one_channel_per_z(self, has_ni_galvo_stage):
        # single position
        self.config["is_multiposition"] = False
        self.model.configuration["configuration"]["microscopes"][
            self.config["microscope_name"]
        ]["stage"]["has_ni_galvo_stage"] = has_ni_galvo_stage

        # 1 channel per_z
        self.config["stack_cycling_mode"] = "per_z"
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = False
        self.config["channels"]["channel_3"]["is_selected"] = False
        self.model.start(self.feature_list)
        print(self.model.signal_records)
        self.z_stack_verification()

    @pytest.mark.parametrize("has_ni_galvo_stage", [False])
    def test_single_position_one_channel_per_stack(self, has_ni_galvo_stage):
        # single position
        self.config["is_multiposition"] = False
        self.model.configuration["configuration"]["microscopes"][
            self.config["microscope_name"]
        ]["stage"]["has_ni_galvo_stage"] = has_ni_galvo_stage

        # 1 channel per_stack
        self.config["stack_cycling_mode"] = "per_stack"
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = False
        self.config["channels"]["channel_3"]["is_selected"] = False
        self.model.start(self.feature_list)
        self.z_stack_verification()

    @pytest.mark.parametrize("has_ni_galvo_stage", [False])
    def test_single_position_two_channels_per_z(self, has_ni_galvo_stage):
        # single position
        self.config["is_multiposition"] = False
        self.model.configuration["configuration"]["microscopes"][
            self.config["microscope_name"]
        ]["stage"]["has_ni_galvo_stage"] = has_ni_galvo_stage

        # 2 channels per_z
        self.config["stack_cycling_mode"] = "per_z"
        for i in range(3):
            for j in range(3):
                self.config["channels"]["channel_" + str(j + 1)]["is_selected"] = True
            self.config["channels"]["channel_" + str(i + 1)]["is_selected"] = False
            self.model.start(self.feature_list)
            self.z_stack_verification()

    @pytest.mark.parametrize("has_ni_galvo_stage", [False])
    def test_single_position_two_channels_per_stack(self, has_ni_galvo_stage):
        # single position
        self.config["is_multiposition"] = False
        self.model.configuration["configuration"]["microscopes"][
            self.config["microscope_name"]
        ]["stage"]["has_ni_galvo_stage"] = has_ni_galvo_stage

        # 2 channels per_stack
        self.config["stack_cycling_mode"] = "per_stack"
        for i in range(3):
            for j in range(3):
                self.config["channels"]["channel_" + str(j + 1)]["is_selected"] = True
            self.config["channels"]["channel_" + str(i + 1)]["is_selected"] = False
            self.model.start(self.feature_list)
            self.z_stack_verification()

    @pytest.mark.parametrize("has_ni_galvo_stage", [False])
    def test_single_position_three_channels_per_stack(self, has_ni_galvo_stage):
        # single position
        self.config["is_multiposition"] = False
        self.model.configuration["configuration"]["microscopes"][
            self.config["microscope_name"]
        ]["stage"]["has_ni_galvo_stage"] = has_ni_galvo_stage

        # 3 channels per_stack
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = True
        self.config["channels"]["channel_3"]["is_selected"] = True
        self.config["stack_cycling_mode"] = "per_stack"
        self.model.start(self.feature_list)
        self.z_stack_verification()

    @pytest.mark.parametrize("has_ni_galvo_stage", [False])
    def test_single_position_three_channels_per_z(self, has_ni_galvo_stage):
        # single position
        self.config["is_multiposition"] = False
        self.model.configuration["configuration"]["microscopes"][
            self.config["microscope_name"]
        ]["stage"]["has_ni_galvo_stage"] = has_ni_galvo_stage

        # 3 channels per_z
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = True
        self.config["channels"]["channel_3"]["is_selected"] = True
        self.config["stack_cycling_mode"] = "per_z"
        self.model.start(self.feature_list)
        self.z_stack_verification()

    @pytest.mark.parametrize("has_ni_galvo_stage", [False])
    def test_multi_position_one_channel_per_z(self, has_ni_galvo_stage):
        # multi position
        self.config["is_multiposition"] = True
        self.model.configuration["configuration"]["microscopes"][
            self.config["microscope_name"]
        ]["stage"]["has_ni_galvo_stage"] = has_ni_galvo_stage

        # 1 channel per_z
        self.config["stack_cycling_mode"] = "per_z"
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = False
        self.config["channels"]["channel_3"]["is_selected"] = False
        self.model.start(self.feature_list)
        self.z_stack_verification()

        self.config["is_multiposition"] = False

    @pytest.mark.parametrize("has_ni_galvo_stage", [False])
    def test_multi_position_one_channel_per_stack(self, has_ni_galvo_stage):
        self.config["is_multiposition"] = True
        self.model.configuration["configuration"]["microscopes"][
            self.config["microscope_name"]
        ]["stage"]["has_ni_galvo_stage"] = has_ni_galvo_stage

        # 1 channel per_stack
        self.config["stack_cycling_mode"] = "per_stack"
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = False
        self.config["channels"]["channel_3"]["is_selected"] = False
        self.model.start(self.feature_list)
        self.z_stack_verification()

        self.config["is_multiposition"] = False

    @pytest.mark.parametrize("has_ni_galvo_stage", [False])
    def test_multi_position_two_channels_per_z(self, has_ni_galvo_stage):
        self.config["is_multiposition"] = True
        self.model.configuration["configuration"]["microscopes"][
            self.config["microscope_name"]
        ]["stage"]["has_ni_galvo_stage"] = has_ni_galvo_stage

        # 2 channels per_z
        self.config["stack_cycling_mode"] = "per_z"
        for i in range(3):
            for j in range(3):
                self.config["channels"]["channel_" + str(j + 1)]["is_selected"] = True
            self.config["channels"]["channel_" + str(i + 1)]["is_selected"] = False
            self.model.start(self.feature_list)
            self.z_stack_verification()

        self.config["is_multiposition"] = False

    @pytest.mark.parametrize("has_ni_galvo_stage", [False])
    def test_multi_position_two_channels_per_stack(self, has_ni_galvo_stage):
        self.config["is_multiposition"] = True
        self.model.configuration["configuration"]["microscopes"][
            self.config["microscope_name"]
        ]["stage"]["has_ni_galvo_stage"] = has_ni_galvo_stage

        # 2 channels per_stack
        self.config["stack_cycling_mode"] = "per_stack"
        for i in range(3):
            for j in range(3):
                self.config["channels"]["channel_" + str(j + 1)]["is_selected"] = True
            self.config["channels"]["channel_" + str(i + 1)]["is_selected"] = False
            self.model.start(self.feature_list)
            self.z_stack_verification()

        self.config["is_multiposition"] = False

    @pytest.mark.parametrize("has_ni_galvo_stage", [False])
    def test_multi_position_three_channels_per_stack(self, has_ni_galvo_stage):
        self.config["is_multiposition"] = True
        self.model.configuration["configuration"]["microscopes"][
            self.config["microscope_name"]
        ]["stage"]["has_ni_galvo_stage"] = has_ni_galvo_stage

        # 3 channels per_stack
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = True
        self.config["channels"]["channel_3"]["is_selected"] = True
        self.config["stack_cycling_mode"] = "per_stack"
        self.model.start(self.feature_list)
        self.z_stack_verification()

        self.config["is_multiposition"] = False

    @pytest.mark.parametrize("has_ni_galvo_stage", [False])
    def test_multi_position_three_channels_per_z(self, has_ni_galvo_stage):
        self.config["is_multiposition"] = True
        self.model.configuration["configuration"]["microscopes"][
            self.config["microscope_name"]
        ]["stage"]["has_ni_galvo_stage"] = has_ni_galvo_stage

        # 3 channels per_z
        self.config["channels"]["channel_1"]["is_selected"] = True
        self.config["channels"]["channel_2"]["is_selected"] = True
        self.config["channels"]["channel_3"]["is_selected"] = True
        self.config["stack_cycling_mode"] = "per_z"
        self.model.start(self.feature_list)
        self.z_stack_verification()

        self.config["is_multiposition"] = False
