# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Focused tests for cancellable resolution-change stage motion."""

import threading


class RecordingStage:
    """Small stage double that records physical movement and stop attempts."""

    def __init__(
        self,
        name,
        calls,
        *,
        cancel_event_on_move=None,
        stop_error=None,
    ):
        self.name = name
        self.calls = calls
        self.cancel_event_on_move = cancel_event_on_move
        self.stop_error = stop_error

    def move_absolute(self, position, wait_until_done=False):
        self.calls.append(("move", self.name, position, wait_until_done))
        if self.cancel_event_on_move is not None:
            self.cancel_event_on_move.set()
        return True

    def stop(self):
        self.calls.append(("stop", self.name))
        if self.stop_error is not None:
            raise self.stop_error


def make_microscope_with_stages(*stage_axes):
    """Build a real Microscope instance without starting hardware."""
    from navigate.model.microscope import Microscope

    microscope = Microscope.__new__(Microscope)
    microscope.stages_list = list(stage_axes)
    microscope.stages = {axis: stage for stage, axes in stage_axes for axis in axes}
    microscope.cache_stage_positions = False
    microscope.ask_stage_for_position = True
    microscope.central_focus = 0.0
    microscope.get_stage_position = lambda: {"f_pos": 0.0}
    return microscope


def test_move_stage_stops_before_second_device_after_cancellation():
    cancel_event = threading.Event()
    calls = []
    first = RecordingStage("first", calls, cancel_event_on_move=cancel_event)
    second = RecordingStage("second", calls)
    microscope = make_microscope_with_stages((first, ["x"]), (second, ["z"]))

    result = microscope.move_stage(
        {"x_abs": 10.0, "z_abs": 20.0},
        wait_until_done=True,
        cancel_event=cancel_event,
    )

    assert result is False
    assert calls == [("move", "first", {"x_abs": 10.0}, True)]


def test_move_stage_offset_stops_before_second_device_after_cancellation():
    cancel_event = threading.Event()
    calls = []
    first = RecordingStage("first", calls, cancel_event_on_move=cancel_event)
    second = RecordingStage("second", calls)
    microscope = make_microscope_with_stages((first, ["x"]), (second, ["z"]))
    microscope.microscope_name = "target"
    microscope.configuration = {
        "configuration": {
            "microscopes": {
                "former": {"stage": {"x_offset": 0, "z_offset": 0}},
                "target": {"stage": {"x_offset": 5, "z_offset": -2}},
            }
        }
    }
    microscope.get_stage_position = lambda: {
        "x_pos": 10.0,
        "z_pos": 20.0,
        "f_pos": 0.0,
    }

    result = microscope.move_stage_offset("former", cancel_event=cancel_event)

    assert result is False
    assert calls == [("move", "first", {"x_abs": 15.0}, True)]


def test_stop_stage_attempts_each_unique_device_after_error():
    calls = []
    shared = RecordingStage("shared", calls, stop_error=RuntimeError("stop failed"))
    other = RecordingStage("other", calls)
    microscope = make_microscope_with_stages(
        (shared, ["x"]), (shared, ["y"]), (other, ["z"])
    )

    errors = microscope.stop_stage()

    assert calls == [("stop", "shared"), ("stop", "other")]
    assert len(errors) == 1
    assert "stop failed" in errors[0]
