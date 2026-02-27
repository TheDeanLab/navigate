from types import SimpleNamespace
from unittest.mock import MagicMock

from navigate.model.features.common_features import (
    MoveToNextPositionInMultiPositionTable,
    ZStackAcquisition,
)


class MoveModelStub:
    def __init__(self):
        self.configuration = {
            "multi_positions": [
                ["X", "Y", "Z", "THETA", "F"],
                [0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 10.0, 0.0],
            ]
        }
        self.active_microscope_name = "Mesoscale"
        self.active_microscope = SimpleNamespace(
            stages={
                "x": object(),
                "y": object(),
                "z": object(),
                "theta": object(),
                "f": object(),
            },
            zoom=SimpleNamespace(zoomvalue="N/A"),
            central_focus=None,
            ask_stage_for_position=False,
        )
        self.stop_acquisition = False
        self._stage_position = {
            "x_pos": 0.0,
            "y_pos": 0.0,
            "z_pos": 0.0,
            "theta_pos": 0.0,
            "f_pos": 0.0,
        }
        self.pause_calls = 0
        self.resume_calls = 0
        self.move_calls = []

    def get_stage_position(self):
        return dict(self._stage_position)

    def pause_data_thread(self):
        self.pause_calls += 1

    def resume_data_thread(self):
        self.resume_calls += 1

    def move_stage(self, pos_dict, wait_until_done=False):
        self.move_calls.append((pos_dict, wait_until_done))
        for axis_key, value in pos_dict.items():
            axis = axis_key.split("_")[0]
            self._stage_position[f"{axis}_pos"] = value
        return True


def _build_zstack_feature(model, positions):
    feature = ZStackAcquisition(model)
    feature.stage_axes = ["x", "y", "z", "theta", "f"]
    feature.primary_z_axis = "z"
    feature.primary_f_axis = "f"
    feature.secondary_stack_settings = {}
    feature.tiling_axes = ["x", "y", "theta"]
    feature.current_channel_in_list = 0
    feature.defocus = None
    feature.start_z_position = 0
    feature.start_focus = 0
    feature.z_stack_distance = 0
    feature.f_stack_distance = 0
    feature.stage_distance_threshold = 1000
    feature.need_to_move_new_position = True
    feature.need_to_move_z_position = False
    feature.current_position_idx = 1
    feature.positions = positions
    feature.axes_index = [0, 1, 2, 3, 4]
    feature.current_position = dict(zip(feature.stage_axes, positions[0]))
    feature.pre_position = feature.current_position
    return feature


def test_move_to_next_position_pauses_when_theta_changes():
    model = MoveModelStub()
    feature = MoveToNextPositionInMultiPositionTable(model)
    feature.pre_signal_func()

    # First move keeps theta fixed.
    feature.signal_func()
    assert model.pause_calls == 0
    assert model.resume_calls == 0

    # Second move rotates theta and should pause/resume data thread.
    feature.signal_func()
    assert model.pause_calls == 1
    assert model.resume_calls == 1
    assert model.move_calls[-1][1] is True
    assert model.move_calls[-1][0]["theta_abs"] == 10.0


def test_zstack_pauses_when_theta_changes():
    model = SimpleNamespace(
        stop_acquisition=False,
        frame_id=0,
        pause_data_thread=MagicMock(),
        resume_data_thread=MagicMock(),
        move_stage=MagicMock(return_value=True),
        mark_saving_flags=MagicMock(),
        active_microscope=SimpleNamespace(central_focus=None),
    )
    feature = _build_zstack_feature(
        model,
        positions=[
            [0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 10.0, 0.0],
        ],
    )

    feature.signal_func()
    assert model.pause_data_thread.call_count == 1
    assert model.resume_data_thread.call_count == 1


def test_zstack_pauses_for_large_negative_translation():
    model = SimpleNamespace(
        stop_acquisition=False,
        frame_id=0,
        pause_data_thread=MagicMock(),
        resume_data_thread=MagicMock(),
        move_stage=MagicMock(return_value=True),
        mark_saving_flags=MagicMock(),
        active_microscope=SimpleNamespace(central_focus=None),
    )
    feature = _build_zstack_feature(
        model,
        positions=[
            [2001.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    )

    feature.signal_func()
    assert model.pause_data_thread.call_count == 1
    assert model.resume_data_thread.call_count == 1
