"""Compare real acquisition feature trajectories with the legacy equations."""

from queue import SimpleQueue
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from navigate.model.features.common_features import (
    ASIZStackAcquisition,
    ZStackAcquisition,
)
from navigate.tools.stack_geometry import StackGeometry, StackReference


def make_model(
    *, cycling="per_stack", multiposition=False, flipped=False, alternate_axes=False
):
    """Keep movement and channel hardware fake; run the actual feature state machine."""
    z_axis, f_axis = ("theta", "x") if alternate_axes else ("z", "f")
    state = {
        "start_position": 2.5 if flipped else -1.25,
        "end_position": -1.25 if flipped else 2.5,
        "step_size": -0.7 if flipped else 0.7,
        "number_z_steps": 5,  # Deliberately differs from the GUI's ceiling count.
        "start_focus": 3.0,
        "end_focus": -2.0,
        "stack_z_origin": 2000.0,
        "stack_focus_origin": 70.0,
        "primary_z_axis": z_axis,
        "primary_f_axis": f_axis,
        "secondary_stack_settings": {"z2": 0.25},
        "timepoints": 1,
        "stack_cycling_mode": cycling,
        "is_multiposition": multiposition,
        "channels": {
            "channel_1": {"is_selected": True, "defocus": 3.0},
            "channel_2": {"is_selected": True, "defocus": -1.5},
            "channel_3": {"is_selected": False, "defocus": 100},
        },
    }
    current = {
        "x": 100.0,
        "y": 200.0,
        "z": 1000.0,
        "theta": 20.0,
        "f": 50.0,
        "z2": 1000.25,
    }
    # Reordered headers must not change axis selection.
    headers = ["F", "THETA", "Z", "Y", "X", "Z2"]
    rows = [[90, 30, 3000, 250, 150, 3000.25], [100, 40, 4500, 350, 175, 4500.25]]
    moves = []

    def move_stage(target, wait_until_done=False):
        moves.append((dict(target), wait_until_done))
        return True

    model = SimpleNamespace(
        configuration={
            "experiment": {"MicroscopeState": state},
            "multi_positions": [headers, *rows],
        },
        active_microscope=SimpleNamespace(
            stages=dict.fromkeys(current), prepare_next_channel=Mock(), daq=Mock()
        ),
        virtual_microscopes={},
        get_stage_position=Mock(
            return_value={f"{axis}_pos": value for axis, value in current.items()}
        ),
        move_stage=move_stage,
        pause_data_thread=Mock(),
        resume_data_thread=Mock(),
        mark_saving_flags=Mock(),
        event_queue=SimpleQueue(),
        stop_acquisition=False,
        is_data_thread_on=True,
        frame_id=0,
        image_writer=None,
    )
    return model, state, current, moves


def expected_references(model, state, current, use_current):
    """Independent oracle for the pre-existing origin-selection rules."""
    z, f = state["primary_z_axis"], state["primary_f_axis"]
    if state["is_multiposition"]:
        headers, *rows = model.configuration["multi_positions"]
        return [
            (row[headers.index(z.upper())], row[headers.index(f.upper())])
            for row in rows
        ]
    return [(current[z], current[f])] if use_current else [(2000.0, 70.0)]


@pytest.mark.parametrize("cycling", ["per_stack", "per_z"])
@pytest.mark.parametrize(
    "multiposition,use_current",
    [(False, False), (False, True), (True, False), (True, True)],
)
@pytest.mark.parametrize("flipped", [False, True])
@pytest.mark.parametrize("alternate_axes", [False, True])
def test_generic_trajectory_matches_legacy(
    cycling, multiposition, use_current, flipped, alternate_axes
):
    model, state, current, moves = make_model(
        cycling=cycling,
        multiposition=multiposition,
        flipped=flipped,
        alternate_axes=alternate_axes,
    )
    references = expected_references(model, state, current, use_current)
    feature = ZStackAcquisition(model, get_origin=use_current)
    feature.pre_signal_func()
    actual = []
    for _ in range(5 * 2 * len(references)):
        assert feature.signal_func()
        actual.append(
            (
                feature.current_position_idx,
                feature.current_channel_in_list,
                feature.z_position_moved_time,
                feature.current_z_position,
                feature.current_focus_position,
            )
        )
        model.frame_id += 1
        if feature.signal_end():
            break
    else:
        pytest.fail("The stack feature did not finish at the legacy frame count")

    expected = []
    for p, (z_origin, f_origin) in enumerate(references):
        indices = (
            [(c, i) for c in range(2) for i in range(5)]
            if cycling == "per_stack"
            else [(c, i) for i in range(5) for c in range(2)]
        )
        for c, i in indices:
            expected.append(
                (
                    p,
                    c,
                    i,
                    state["start_position"] + z_origin + i * state["step_size"],
                    (3.0 - 3.0) + f_origin + i * -1.0 + [3.0, -1.5][c],
                )
            )
    assert actual == expected
    z_key, f_key = f"{state['primary_z_axis']}_abs", f"{state['primary_f_axis']}_abs"
    stack_moves = [target for target, _ in moves if z_key in target]
    expected_moves = [
        {z_key: z, f_key: f, "z2_abs": z + 0.25}
        for _, c, _, z, f in expected
        if cycling == "per_stack" or c == 0
    ]
    expected_moves.append(
        {
            z_key: current[state["primary_z_axis"]],
            f_key: current[state["primary_f_axis"]],
            "z2_abs": current[state["primary_z_axis"]] + 0.25,
        }
    )
    assert stack_moves == expected_moves
    model.get_stage_position.assert_called_once_with()
    assert model.mark_saving_flags.call_count == len(expected)


@pytest.mark.parametrize("cycling", ["per_stack", "per_z"])
@pytest.mark.parametrize(
    "multiposition,use_current", [(False, False), (False, True), (True, False)]
)
@pytest.mark.parametrize("flipped", [False, True])
def test_asi_stack_start_targets_match_legacy(
    cycling, multiposition, use_current, flipped, monkeypatch
):
    model, state, current, moves = make_model(
        cycling=cycling, multiposition=multiposition, flipped=flipped
    )
    monkeypatch.setattr(
        "navigate.model.features.common_features.time.sleep", lambda _: None
    )
    references = expected_references(model, state, current, use_current)
    feature = ASIZStackAcquisition(model, get_origin=use_current)
    feature.pre_signal_func()
    expected = []
    for z_origin, f_origin in references:
        for c in range(2 if cycling == "per_stack" else 1):
            expected.append(
                (state["start_position"] + z_origin, f_origin + [3.0, -1.5][c])
            )
    for _ in expected:
        feature.signal_func()
        done = feature.signal_end()
    assert done
    assert [(target["z_abs"], target["f_abs"]) for target, _ in moves] == expected
    assert feature.number_z_steps == 5
    assert feature.focus_step_size == -1
    model.get_stage_position.assert_called_once_with()


@pytest.mark.parametrize("feature_type", [ZStackAcquisition, ASIZStackAcquisition])
def test_workflow_reinitialization_uses_new_geometry_and_selected_axes(feature_type):
    model, state, _, _ = make_model()
    feature = feature_type(model)
    feature.pre_signal_func()
    # Model-side workflows can change scope, axes, origins and sampling between
    # stacks. No geometry or reference from the previous stack may override it.
    state.update(
        microscope_name="Other microscope",
        primary_z_axis="theta",
        primary_f_axis="x",
        stack_z_origin=123,
        stack_focus_origin=456,
        start_position=1,
        end_position=-4,
        step_size=-2,
        number_z_steps=2,
        start_focus=7,
        end_focus=9,
    )
    feature.pre_signal_func()
    feature.signal_func()
    assert (feature.current_z_position, feature.current_focus_position) == (124, 463)
    assert (feature.number_z_steps, feature.z_step_size, feature.focus_step_size) == (
        2,
        -2,
        1,
    )
    # Keep legacy feature attributes usable by custom workflows, rather than
    # executing a stale private geometry snapshot.
    feature.start_z_position = 10
    feature.start_focus = 20
    feature.z_position_moved_time = 1
    assert feature._z_target(1) == 131
    assert feature._focus_target_for_channel(1) == 472.5


@pytest.mark.parametrize("feature_type", [ZStackAcquisition, ASIZStackAcquisition])
def test_forced_multiposition_keeps_table_references(feature_type):
    model, state, _, _ = make_model()
    feature = feature_type(model, force_multiposition=True, get_origin=True)
    feature.pre_signal_func()
    feature.signal_func()
    assert state["is_multiposition"] is False
    assert len(feature.positions) == 2
    assert (feature.current_z_position, feature.current_focus_position) == (
        2998.75,
        93,
    )


@pytest.mark.parametrize("feature_type", [ZStackAcquisition, ASIZStackAcquisition])
def test_missing_saved_origins_and_constant_focus_match_legacy(feature_type):
    model, state, _, _ = make_model()
    del state["stack_z_origin"]
    del state["stack_focus_origin"]
    state["end_focus"] = state["start_focus"]
    feature = feature_type(model)
    feature.pre_signal_func()
    feature.signal_func()
    assert (feature.current_z_position, feature.current_focus_position) == (998.75, 53)
    assert feature.focus_step_size == 0
    feature.z_position_moved_time = 4
    assert feature._focus_target_for_channel(1) == 48.5


def test_resolved_geometry_matches_each_acquisition_reference():
    model, state, current, _ = make_model(multiposition=True, flipped=True)
    geometry = StackGeometry.from_legacy_state(state)
    for z, f in expected_references(model, state, current, False):
        for i in range(5):
            assert geometry.position(
                StackReference(z, f), i, reference_defocus=3, channel_defocus=-1.5
            ) == (
                2.5 + z + i * -0.7,
                f + i * -1.0 - 1.5,
            )
