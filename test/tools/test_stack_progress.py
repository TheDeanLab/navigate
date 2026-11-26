"""Progress is bounded telemetry, not another acquisition or hardware clock."""

from multiprocessing import get_context
from queue import Empty, Full, Queue
from unittest.mock import Mock

import pytest

from navigate.tools.stack_geometry import StackGeometry, StackReference
from navigate.tools.stack_progress import StackProgressPlan, StackProgressTracker


def plan(**kwargs):
    values = {
        "capture_token": (1, "scope"),
        "geometry": StackGeometry.relative(500, 50),
        "references": (StackReference(1000, 50), StackReference(2000, 60)),
        "channels": ("channel_1", "channel_3"),
        "defocus": (3, -1.5),
        "cycling": "per_stack",
        "timepoints": 2,
        "z_axis": "z",
        "f_axis": "f",
        "relative": True,
    }
    values.update(kwargs)
    return StackProgressPlan(**values)


def test_throttles_progress_but_counts_all_frames_and_publishes_final(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr("navigate.tools.stack_progress.monotonic", lambda: clock[0])
    output = Queue(1)
    tracker = StackProgressTracker(plan(), output)
    tracker.advance(1)
    assert output.get_nowait().completed == 1
    for _ in range(29):
        tracker.advance(1)
    assert output.empty()
    clock[0] = 0.1
    tracker.advance(3)
    assert output.get_nowait().completed == 33
    tracker.advance(47)
    final = output.get_nowait()
    assert (final.completed, final.total) == (80, 80)
    assert (final.plane, final.position, final.timepoint) == (10, 2, 2)
    tracker.advance(1)
    tracker.advance(0)
    assert output.empty()


def test_full_queue_replaces_old_value_instead_of_growing(monkeypatch):
    monkeypatch.setattr("navigate.tools.stack_progress.monotonic", lambda: 0)
    output = Queue(1)
    output.put("obsolete")
    tracker = StackProgressTracker(plan(), output)
    tracker.advance(1)
    tracker.advance(79)
    assert output.qsize() == 1
    assert output.get_nowait().completed == 80


def test_timepoint_completion_is_visible_before_a_pause_even_when_throttled(
    monkeypatch,
):
    monkeypatch.setattr("navigate.tools.stack_progress.monotonic", lambda: 0)
    output = Queue(1)
    tracker = StackProgressTracker(plan(), output)
    tracker.advance(39)
    assert output.get_nowait().completed == 39
    tracker.advance(1)
    end = output.get_nowait()
    assert (end.completed, end.plane, end.position, end.timepoint) == (40, 10, 2, 1)


def test_busy_multiprocessing_feeder_drops_snapshot_without_waiting():
    output = Mock()
    output.put_nowait.side_effect = Full
    output.get_nowait.side_effect = Empty
    StackProgressTracker(plan(), output).advance(1)
    output.put.assert_not_called()
    output.get.assert_not_called()
    assert output.put_nowait.call_count == 2


def test_snapshot_round_trips_through_real_multiprocessing_transport():
    output = get_context("spawn").Queue(1)
    try:
        p = plan()
        StackProgressTracker(p, output).advance(3)
        assert output.get(timeout=5) == p.snapshot(3)
    finally:
        output.close()
        output.join_thread()


@pytest.mark.parametrize("count", [0, -1, 81])
def test_unknown_or_out_of_range_frame_has_no_coordinate(count):
    with pytest.raises(ValueError):
        plan().snapshot(count)
