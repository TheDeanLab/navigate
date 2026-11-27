"""Sampling and reference contracts used by existing stack workflows."""

import copy
from dataclasses import FrozenInstanceError

import pytest

from navigate.tools.stack_geometry import (
    StackAxis,
    StackGeometry,
    StackReference,
    focus_position,
)


@pytest.mark.parametrize(
    "start,end,step,count",
    [
        (0, 200, 0.2, 1000),
        (-250, 250, 1, 500),
        (0, 1, 0.3, 4),
        (10, -10, 3, 7),
        (0, 0, 1, 0),
        (0, 0.1, 1, 1),
        (0, 0.30000000000000004, 0.1, 4),
    ],
)
@pytest.mark.parametrize("flipped", [False, True])
def test_legacy_ceiling_and_direction(start, end, step, count, flipped):
    axis = StackAxis.from_bounds(start, end, step, flipped=flipped)
    assert (axis.start, axis.end, axis.count) == (start, end, count)
    assert axis.step == (-step if flipped else step)
    assert axis.distance == abs(start - end)


@pytest.mark.parametrize("step", [0, -1])
def test_gui_requires_positive_step_magnitude(step):
    with pytest.raises(ValueError, match="positive"):
        StackAxis.from_bounds(0, 10, step)


def test_legacy_state_is_read_only_and_explicit_count_is_authoritative():
    state = {
        "start_position": "-2",
        "end_position": "2",
        "step_size": "0.7",
        "number_z_steps": "3",
        "start_focus": "10",
        "end_focus": "4",
    }
    original = copy.deepcopy(state)
    geometry = StackGeometry.from_legacy_state(state)
    assert state == original
    assert geometry.z.count == 3  # The GUI would choose 6; custom workflows need not.
    assert geometry.focus.step == -2
    assert geometry.first_plane(StackReference(100, 50)) == (98, 60)
    assert geometry.last_plane(StackReference(100, 50)) == (99.4, 56)
    with pytest.raises(FrozenInstanceError):
        geometry.z.start = 0


def test_last_plane_is_not_the_requested_end_boundary():
    geometry = StackGeometry(
        StackAxis.from_bounds(0, 200, 0.2), StackAxis.focus_ramp(10, 20, 1000)
    )
    assert geometry.last_plane(StackReference(100, 50)) == pytest.approx((299.8, 69.99))
    # Features calculate index N before checking their stop condition. Keep that
    # extrapolation available without treating it as an extra acquired plane.
    assert geometry.position(StackReference(100, 50), 1000) == (300, 70)


def test_empty_preview_and_zero_count_acquisition_keep_distinct_behavior():
    geometry = StackGeometry(StackAxis(0, 0, 1, 0), StackAxis(0, 0, 0, 0))
    assert geometry.first_plane(StackReference(100, 50)) is None
    assert geometry.last_plane(StackReference(100, 50)) is None
    with pytest.raises(ZeroDivisionError):
        StackAxis.focus_ramp(0, 0, 0)
    with pytest.raises(ValueError, match="same plane count"):
        StackGeometry(StackAxis(0, 1, 1, 1), StackAxis(0, 0, 0, 2))


@pytest.mark.parametrize("use_current", [False, True])
@pytest.mark.parametrize(
    "state",
    [{}, {"stack_z_origin": 100}, {"stack_z_origin": 100, "stack_focus_origin": 50}],
)
def test_saved_current_and_missing_origin_selection(state, use_current):
    reference = StackReference.for_single_position(
        state, 20, 30, use_current=use_current
    )
    assert reference == StackReference(
        20 if use_current else state.get("stack_z_origin", 20),
        30 if use_current else state.get("stack_focus_origin", 30),
    )


def test_channel_defocus_keeps_legacy_floating_point_operation_order():
    # Rearranging offset subtraction around the large origin can change the
    # result. Use the existing expression, without intermediate rounding.
    start, origin, reference, channel, step, index = 0.125, 1e16, 0.25, -1.5, 0.3, 7
    expected = (start - reference) + origin + index * step + channel
    assert focus_position(start, origin, step, index, reference, channel) == expected
