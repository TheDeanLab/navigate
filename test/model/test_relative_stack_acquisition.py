"""Relative references are resolved once and retain legacy acquisition arithmetic."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from navigate.model.features.common_features import (
    ASIZStackAcquisition,
    ZStackAcquisition,
)
from navigate.model.microscope import Microscope
from navigate.model.model import Model
from navigate.model.stack_acquisition import freeze_relative_stack
from test.model.features.test_stack_geometry import make_model


def relative_model(**kwargs):
    model, state, current, moves = make_model(**kwargs)
    state.update(
        microscope_name="scope",
        stack_position_mode="relative",
        relative_stack_range=500,
        step_size=50,
    )
    stage = {
        f"{axis}_{bound}": value
        for axis in current
        for bound, value in (("min", -10000), ("max", 10000))
    }
    stage[f"flip_{state['primary_z_axis']}"] = kwargs.get("flipped", False)
    model.configuration["configuration"] = {"microscopes": {"scope": {"stage": stage}}}
    model.configuration["experiment"]["StageParameters"] = {"limits": True}
    model.stop_stage = Mock()
    model.imaging_mode = "z-stack"
    model.active_microscope_name = "scope"
    return model, state, current, moves


@pytest.mark.parametrize("feature_type", [ZStackAcquisition, ASIZStackAcquisition])
@pytest.mark.parametrize("cycling", ["per_stack", "per_z"])
@pytest.mark.parametrize("multiposition", [False, True])
@pytest.mark.parametrize("flipped", [False, True])
@pytest.mark.parametrize("ramp", [False, True])
def test_relative_trajectories_keep_frozen_references_across_timepoints(
    feature_type, cycling, multiposition, flipped, ramp, monkeypatch
):
    monkeypatch.setattr(
        "navigate.model.features.common_features.time.sleep", lambda _: None
    )
    model, state, _, _ = relative_model(
        cycling=cycling, multiposition=multiposition, flipped=flipped
    )
    state.update(
        relative_focus_ramp=ramp, relative_start_focus=-5, relative_end_focus=5
    )
    model._relative_stack_plan = plan = freeze_relative_stack(model)
    refs = [(3000, 90), (4500, 100)] if multiposition else [(1000, 50)]
    feature = feature_type(model)
    for timepoint in range(2):
        if timepoint:
            # Stage movement, later preview edits, and table edits cannot silently
            # recenter an acquisition already in progress.
            model.get_stage_position.return_value = {
                f"{axis}_pos": 999 for axis in model.active_microscope.stages
            }
            state.update(
                stack_z_origin=-99,
                start_position=-999,
                number_z_steps=99,
                is_multiposition=not multiposition,
            )
            model.configuration["multi_positions"][1][2] = -999
        feature.pre_signal_func()
        expected = []
        for p, (z, f) in enumerate(refs):
            if feature_type is ASIZStackAcquisition:
                indices = [(c, 0) for c in range(2 if cycling == "per_stack" else 1)]
            else:
                indices = (
                    [(c, i) for c in range(2) for i in range(10)]
                    if cycling == "per_stack"
                    else [(c, i) for i in range(10) for c in range(2)]
                )
            for c, i in indices:
                expected.append(
                    (
                        z + (250 if flipped else -250) + i * (-50 if flipped else 50),
                        (f - 5 + i if ramp else f) + [0, -4.5][c],
                    )
                )
        actual = []
        for _ in expected:
            feature.signal_func()
            actual.append((feature.current_z_position, feature.current_focus_position))
            model.frame_id += 1
            done = feature.signal_end()
        assert done
        assert actual == expected
        assert feature.number_z_steps == 10
        assert model._relative_stack_plan is plan


@pytest.mark.parametrize("alternate_axes", [False, True])
def test_fresh_reference_selected_axes_and_explicit_autofocus_reference(alternate_axes):
    model, state, current, _ = relative_model(alternate_axes=alternate_axes)
    model._relative_stack_plan = plan = freeze_relative_stack(model)
    model.stop_stage.assert_called_once()
    model.get_stage_position.assert_called_once_with(require_fresh=True)
    assert plan.reference.z == current[state["primary_z_axis"]]
    model.get_stage_position.return_value[f"{state['primary_f_axis']}_pos"] = 80
    feature = ZStackAcquisition(model, get_origin=True)
    feature.pre_signal_func()
    feature.signal_func()
    assert feature.current_z_position == plan.reference.z - 250
    assert feature.current_focus_position == 80


@pytest.mark.parametrize(
    "invalid",
    [
        "range",
        "step",
        "nan",
        "readback",
        "partial_readback",
        "z_limit",
        "focus_limit",
        "secondary_limit",
        "table",
        "missing_axis",
        "xy_limit",
    ],
)
def test_invalid_relative_plan_fails_before_publishing_or_camera_preparation(invalid):
    model, state, _, _ = relative_model(
        multiposition=invalid in ("table", "missing_axis", "xy_limit")
    )
    stage = model.configuration["configuration"]["microscopes"]["scope"]["stage"]
    if invalid == "range":
        state["relative_stack_range"] = 0
    elif invalid == "step":
        state["step_size"] = 0
    elif invalid == "nan":
        state["relative_stack_range"] = float("nan")
    elif invalid == "readback":
        model.get_stage_position.return_value["z_pos"] = float("nan")
    elif invalid == "partial_readback":
        del model.get_stage_position.return_value["x_pos"]
    elif invalid == "z_limit":
        stage["z_max"] = 1100
    elif invalid == "focus_limit":
        stage["f_min"] = 48  # The second channel needs F=45.5.
    elif invalid == "secondary_limit":
        stage["z2_max"] = 1100
    elif invalid == "table":
        model.configuration["multi_positions"][2][2] = 20000
    elif invalid == "xy_limit":
        stage["x_max"] = 160  # The second row requires X=175.
    else:
        model.configuration["multi_positions"][0][0] = "MISSING"
    model.is_acquiring = True
    model.active_microscope.prepare_acquisition = Mock()
    old_start = state["start_position"]
    with pytest.raises(ValueError):
        Model.prepare_acquisition(model)
    assert model.is_acquiring is False
    assert model._relative_stack_plan is None
    assert state["start_position"] == old_start
    model.active_microscope.prepare_acquisition.assert_not_called()
    assert model.event_queue.empty()


def test_new_acquisition_after_scope_switch_replaces_reference_and_respects_offsets():
    model, state, _, _ = relative_model()
    first = freeze_relative_stack(model)
    state["microscope_name"] = "other"
    model.active_microscope_name = "other"
    model.configuration["configuration"]["microscopes"]["other"] = {
        "stage": {"flip_z": True}
    }
    model.get_stage_position.return_value.update(z_pos=1025, f_pos=45)
    second = freeze_relative_stack(model)
    assert first.reference.z == 1000
    assert (second.reference.z, second.reference.focus) == (1025, 45)
    assert second.geometry.z.step == -50
    assert (state["abs_z_start"], state["abs_z_end"]) == (775, 1275)


@pytest.mark.parametrize("relative", [False, True])
def test_model_preflight_runs_before_camera_and_repreparation_keeps_reference(relative):
    model, state, _, _ = relative_model()
    state["stack_position_mode"] = "relative" if relative else "absolute"
    model.injected_flag = SimpleNamespace(value=False)
    model.microscopes = {"scope": model.active_microscope}
    model.plugin_acquisition_modes = {}
    calls = []
    model.active_microscope.prepare_acquisition = Mock(
        side_effect=lambda: calls.append("camera") or {}
    )
    readback = model.get_stage_position.return_value.copy()
    model.get_stage_position.side_effect = lambda **_: calls.append("read") or readback
    assert Model.prepare_acquisition(model)
    assert calls == (["read", "camera"] if relative else ["camera"])
    plan = model._relative_stack_plan
    assert (plan is not None) is relative
    assert Model.prepare_acquisition(model, turn_off_flags=False)
    assert model._relative_stack_plan is plan
    assert model.get_stage_position.call_count == int(relative)


def test_custom_relative_mode_rejected_before_hardware_preparation():
    model, _, _, _ = relative_model()
    model.imaging_mode = "customized"
    model.is_acquiring = True
    with pytest.raises(ValueError, match="Absolute"):
        Model.prepare_acquisition(model)
    assert model.is_acquiring is False
    model.stop_stage.assert_not_called()


def test_end_acquisition_discards_relative_reference():
    model, _, _, _ = relative_model()
    model._relative_stack_plan = freeze_relative_stack(model)
    model.active_microscope.end_acquisition = Mock()
    model.plugin_acquisition_modes = {}
    Model.end_acquisition(model)
    assert model._relative_stack_plan is None
    assert model.is_acquiring is False


@pytest.mark.parametrize("reply", [{}, {"f_pos": float("nan")}, {"f_pos": None}])
def test_strict_read_rejects_partial_replies_without_merging_old_coordinates(reply):
    z_stage = Mock(report_position=Mock(return_value={"z_pos": 1200}))
    f_stage = Mock(report_position=Mock(return_value=reply))
    scope = SimpleNamespace(
        stages_list=[(z_stage, ["z"]), (f_stage, ["f"])],
        ret_pos_dict={"z_pos": 1000, "f_pos": 50},
        ask_stage_for_position=False,
    )
    with pytest.raises(ValueError, match="fresh, finite f"):
        Microscope.get_stage_position(scope, require_fresh=True)
    assert scope.ret_pos_dict == {"z_pos": 1000, "f_pos": 50}
    assert scope.ask_stage_for_position is True


def test_strict_read_bypasses_cache_and_default_reader_keeps_legacy_cache_policy():
    stage = Mock(report_position=Mock(return_value={"z_pos": 1234.567, "f_pos": 80}))
    scope = SimpleNamespace(
        stages_list=[(stage, ["z", "f"])],
        ret_pos_dict={"z_pos": 1000, "f_pos": 50},
        ask_stage_for_position=False,
    )
    assert Microscope.get_stage_position(scope) == {"z_pos": 1000, "f_pos": 50}
    stage.report_position.assert_not_called()
    assert Microscope.get_stage_position(scope, require_fresh=True) == {
        "z_pos": 1234.57,
        "f_pos": 80,
    }
    stage.report_position.assert_called_once()
    assert scope.ask_stage_for_position is False
