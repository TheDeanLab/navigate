# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Focused tests for cancellable resolution-change stage motion."""

import threading
from queue import SimpleQueue
from types import SimpleNamespace


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


class RecordingMicroscope:
    """Microscope double that observes model cancellation before hardware stop."""

    def __init__(self, name, task, calls):
        self.name = name
        self.task = task
        self.calls = calls

    def stop_stage(self, stopped_stage_ids=None):
        self.calls.append((self.name, self.task.cancel_event.is_set()))
        return []


def make_model_for_stop():
    """Build a real Model instance around deterministic microscope doubles."""
    from navigate.model.model import Model

    task = SimpleNamespace(
        cancel_event=threading.Event(),
        state="changing",
        former_microscope_name="former",
        target_microscope_name="target",
        stopped_position=None,
        stop_errors=[],
    )
    calls = []
    model = Model.__new__(Model)
    model.logger = SimpleNamespace(exception=lambda *_args: None)
    model._resolution_change_task = task
    model._resolution_change_lock = threading.Lock()
    model.microscopes = {
        name: RecordingMicroscope(name, task, calls) for name in ("former", "target")
    }
    model.active_microscope_name = "target"
    model.active_microscope = model.microscopes["target"]
    model.get_stage_position = lambda: {"x_pos": 7.0, "f_pos": 1.0}
    model.configuration = {"experiment": {"StageParameters": {"x": 0.0, "f": 0.0}}}
    model.event_queue = SimpleQueue()
    return model, task, calls


def test_model_stop_records_cancellation_before_each_hardware_stop():
    model, task, calls = make_model_for_stop()

    model.stop_stage()

    assert task.state == "cancel_requested"
    assert calls == [("former", True), ("target", True)]


def test_model_stop_publishes_actual_stopped_position():
    model, task, _ = make_model_for_stop()

    model.stop_stage()

    assert task.stopped_position == {"x_pos": 7.0, "f_pos": 1.0}
    assert model.event_queue.get_nowait() == (
        "update_stage",
        {"x_pos": 7.0, "f_pos": 1.0},
    )


def test_model_stop_attempts_target_after_former_microscope_error():
    model, task, calls = make_model_for_stop()

    def fail_after_stop(_stopped_stage_ids=None):
        calls.append(("former", task.cancel_event.is_set()))
        raise RuntimeError("former position read failed")

    model.microscopes["former"].stop_stage = fail_after_stop

    model.stop_stage()

    assert calls == [("former", True), ("target", True)]
    assert any("former position read failed" in error for error in task.stop_errors)


def test_model_stop_reports_position_readback_error_after_stop_attempts():
    model, task, calls = make_model_for_stop()

    def fail_readback():
        raise RuntimeError("position readback failed")

    model.get_stage_position = fail_readback

    model.stop_stage()

    assert calls == [("former", True), ("target", True)]
    assert task.stopped_position is None
    assert any("position readback failed" in error for error in task.stop_errors)
    event, message = model.event_queue.get_nowait()
    assert event == "warning"
    assert "position readback failed" in message


def test_model_move_stage_forwards_cancellation_event():
    from unittest.mock import MagicMock

    from navigate.model.model import Model

    cancel_event = threading.Event()
    model = Model.__new__(Model)
    model.logger = MagicMock()
    model.active_microscope = MagicMock()
    model.active_microscope.move_stage.return_value = False

    result = model.move_stage(
        {"x_abs": 4.0}, wait_until_done=True, cancel_event=cancel_event
    )

    assert result is False
    model.active_microscope.move_stage.assert_called_once_with(
        {"x_abs": 4.0}, True, cancel_event=cancel_event
    )


def test_manual_resolution_command_returns_while_model_worker_is_active():
    from unittest.mock import MagicMock

    from navigate.model.model import Model

    move_started = threading.Event()
    release_move = threading.Event()
    command_returned = threading.Event()

    def blocking_resolution_change(*_args):
        move_started.set()
        release_move.wait(1.0)
        return True

    model = Model.__new__(Model)
    model.logger = MagicMock()
    model.configuration = {
        "experiment": {"MicroscopeState": {"microscope_name": "target", "zoom": "1x"}}
    }
    model.active_microscope_name = "former"
    model.active_microscope = MagicMock()
    model.active_microscope.calculate_all_waveform.return_value = {}
    model.is_acquiring = False
    model.data_buffer = [object()]
    model.event_queue = SimpleQueue()
    model._resolution_change_lock = threading.Lock()
    model._resolution_change_task = None
    model._resolution_change_counter = 0
    model.change_resolution = blocking_resolution_change
    model._perform_resolution_change = blocking_resolution_change

    def run_command():
        model.run_command("update_setting", "resolution")
        command_returned.set()

    caller = threading.Thread(target=run_command)
    caller.start()
    try:
        assert move_started.wait(1.0)
        assert command_returned.wait(0.1)
    finally:
        release_move.set()
        caller.join(1.0)


def test_resolution_task_stops_after_cancelled_offset_move():
    from unittest.mock import MagicMock

    from navigate.model.model import Model
    from navigate.model.resolution_change import _ResolutionChangeTask

    cancel_event = threading.Event()
    former = MagicMock()
    target = MagicMock()
    target.central_focus = 0.0
    target.ask_stage_for_position = False
    target.zoom.zoomvalue = "1x"
    target.zoom.stage_offsets = None

    def cancel_during_offset(_former_name, *, cancel_event=None):
        assert cancel_event is not None
        cancel_event.set()
        return False

    target.move_stage_offset.side_effect = cancel_during_offset

    model = Model.__new__(Model)
    model.logger = MagicMock()
    model.configuration = {
        "configuration": {"microscopes": {"former": {}, "target": {}}},
        "experiment": {
            "MicroscopeState": {"microscope_name": "target", "zoom": "2x"},
            "Saving": {"solvent": "water"},
            "StageParameters": {"x": 0.0, "f": 0.0},
        },
    }
    model.microscopes = {"former": former, "target": target}
    model.active_microscope_name = "former"
    model.active_microscope = former
    model.get_stage_position = lambda: {"x_pos": 12.0, "f_pos": 3.0}
    model.stop_stage = MagicMock()
    task = _ResolutionChangeTask(
        task_id=1,
        resolution_value="target",
        former_microscope_name="former",
        target_microscope_name="target",
        cancel_event=cancel_event,
    )

    result = model._perform_resolution_change(task)

    assert result is False
    assert task.previous_position == {"x_abs": 12.0, "f_abs": 3.0}
    target.zoom.set_zoom.assert_not_called()
    model.stop_stage.assert_not_called()


def test_terminate_stops_and_joins_active_resolution_worker():
    from unittest.mock import MagicMock

    from navigate.model.model import Model
    from navigate.model.resolution_change import _ResolutionChangeTask

    model = Model.__new__(Model)
    model.active_microscope = MagicMock()
    model.virtual_microscopes = {}
    task = _ResolutionChangeTask(
        task_id=1,
        resolution_value="target",
        former_microscope_name="former",
        target_microscope_name="target",
    )
    worker = threading.Thread(target=task.cancel_event.wait)
    task.worker = worker
    model._resolution_change_task = task

    stop_calls = []

    def stop_stage():
        stop_calls.append("stop")
        task.cancel_event.set()

    model.stop_stage = stop_stage
    worker.start()
    try:
        model.terminate()
        assert stop_calls == ["stop"]
        assert worker.is_alive() is False
    finally:
        task.cancel_event.set()
        worker.join(1.0)


def test_failed_resolution_move_does_not_calculate_waveforms():
    from unittest.mock import MagicMock

    from navigate.model.model import Model
    from navigate.model.resolution_change import _ResolutionChangeTask

    model = Model.__new__(Model)
    model.configuration = {
        "experiment": {"MicroscopeState": {"microscope_name": "target", "zoom": "1x"}}
    }
    model.active_microscope_name = "former"
    model.active_microscope = MagicMock()
    model.is_acquiring = False
    model.stop_acquisition = False
    model.stop_send_signal = False
    model.event_queue = SimpleQueue()
    model._perform_resolution_change = MagicMock(return_value=False)
    model._finish_resolution_change = MagicMock()
    task = _ResolutionChangeTask(
        task_id=1,
        resolution_value="target",
        former_microscope_name="former",
        target_microscope_name="target",
    )

    model._update_setting("resolution", task)

    model.active_microscope.calculate_all_waveform.assert_not_called()
    assert model.stop_acquisition is True
    assert model.stop_send_signal is True
    model._finish_resolution_change.assert_called_once_with(task, False)


class ValidatingStage:
    """Stage double that applies strict literal limit validation."""

    def __init__(self, valid=True):
        self.valid = valid

    def verify_abs_position(self, position, is_strict=False):
        assert is_strict is True
        if not self.valid:
            return {}
        return {key.removesuffix("_abs"): value for key, value in position.items()}


def test_resolution_return_is_disabled_when_limit_validation_fails():
    from unittest.mock import MagicMock

    from navigate.model.model import Model
    from navigate.model.resolution_change import _ResolutionChangeTask

    stage = ValidatingStage()
    stage.verify_abs_position = MagicMock(side_effect=RuntimeError("validation failed"))
    model = Model.__new__(Model)
    model.active_microscope = SimpleNamespace(stages_list=[(stage, ["x"])])
    model.logger = MagicMock()
    task = _ResolutionChangeTask(
        task_id=7,
        resolution_value="target",
        former_microscope_name="former",
        target_microscope_name="target",
        previous_position={"x_abs": 12.0},
        stopped_position={"x_pos": 15.0},
    )

    assert model._is_resolution_return_position_valid(task) is False
    model.logger.exception.assert_called_once()


def test_cancelled_resolution_stores_validated_recovery_snapshot():
    from unittest.mock import MagicMock

    from navigate.model.model import Model
    from navigate.model.resolution_change import _ResolutionChangeTask

    model = Model.__new__(Model)
    model._resolution_change_lock = threading.Lock()
    model._resolution_change_task = None
    model._resolution_recovery = None
    model.active_microscope_name = "target"
    model.active_microscope = SimpleNamespace(
        stages_list=[(ValidatingStage(), ["x", "f"])]
    )
    model.configuration = {"experiment": {"MicroscopeState": {"zoom": "2x"}}}
    model.event_queue = SimpleQueue()
    model.logger = MagicMock()
    task = _ResolutionChangeTask(
        task_id=7,
        resolution_value="target",
        former_microscope_name="former",
        target_microscope_name="target",
        previous_position={"x_abs": 12.0, "f_abs": 3.0},
        stopped_position={"x_pos": 15.0, "f_pos": 4.0},
    )
    task.cancel_event.set()
    model._resolution_change_task = task

    model._finish_resolution_change(task, False)

    assert model._resolution_recovery.task_id == 7
    assert model._resolution_recovery.previous_position == {
        "x_abs": 12.0,
        "f_abs": 3.0,
    }
    event, payload = model.event_queue.get_nowait()
    assert event == "resolution_change_cancelled"
    assert payload["return_allowed"] is True


def make_model_with_recovery(*, return_allowed=True):
    """Build a real Model with one pending recovery decision."""
    from unittest.mock import MagicMock

    from navigate.model.model import Model
    from navigate.model.resolution_change import _ResolutionRecovery

    model = Model.__new__(Model)
    model.data_buffer = [object()]
    model.logger = MagicMock()
    model.event_queue = SimpleQueue()
    model._resolution_change_lock = threading.Lock()
    model._resolution_change_counter = 7
    model._resolution_change_task = None
    model._resolution_recovery = _ResolutionRecovery(
        task_id=7,
        microscope_name="target",
        previous_position={"x_abs": 12.0, "f_abs": 3.0},
        return_allowed=return_allowed,
    )
    model.active_microscope_name = "target"
    model.active_microscope = MagicMock()
    model.configuration = {
        "experiment": {"MicroscopeState": {"microscope_name": "target", "zoom": "2x"}}
    }
    return model


def test_keep_resolution_position_discards_snapshot_without_motion():
    model = make_model_with_recovery()

    model.run_command("resolution_recovery", 7, "keep")

    assert model._resolution_recovery is None
    model.active_microscope.move_stage.assert_not_called()


def test_rejected_resolution_return_emits_terminal_event():
    model = make_model_with_recovery()
    model.active_microscope_name = "different-scope"

    assert model._start_resolution_return(7) is False

    events = []
    while not model.event_queue.empty():
        events.append(model.event_queue.get_nowait())
    assert events == [
        ("warning", "The saved resolution-change position is unavailable."),
        (
            "resolution_return_complete",
            {"task_id": 7, "succeeded": False, "cancelled": False},
        ),
    ]
    model.active_microscope.move_stage.assert_not_called()


def test_successful_resolution_return_stops_and_reports_completion():
    from unittest.mock import MagicMock

    model = make_model_with_recovery()
    move_started = threading.Event()
    release_move = threading.Event()

    def blocking_move(_position, wait_until_done=False, cancel_event=None):
        assert wait_until_done is True
        assert cancel_event is not None
        move_started.set()
        release_move.wait(1.0)
        return True

    model.move_stage = blocking_move
    model.stop_stage = MagicMock()

    assert model._start_resolution_return(7) is True
    assert move_started.wait(1.0)
    worker = model._resolution_change_task.worker
    release_move.set()
    worker.join(1.0)

    model.stop_stage.assert_called_once_with(cancel_resolution_change=False)
    assert model._resolution_change_task is None
    assert model.event_queue.get_nowait() == (
        "resolution_return_complete",
        {"task_id": 7, "succeeded": True, "cancelled": False},
    )


def test_return_moves_to_literal_snapshot_and_stop_cancels_it():
    model = make_model_with_recovery()
    move_started = threading.Event()
    release_move = threading.Event()
    move_arguments = []

    def blocking_move(position, wait_until_done=False, cancel_event=None):
        move_arguments.append((position, wait_until_done, cancel_event))
        move_started.set()
        release_move.wait(1.0)
        return cancel_event is None or not cancel_event.is_set()

    model.move_stage = blocking_move
    model.microscopes = {"target": model.active_microscope}
    model.active_microscope.stop_stage.return_value = []
    model.get_stage_position = lambda: {"x_pos": 14.0, "f_pos": 4.0}
    model.configuration["experiment"]["StageParameters"] = {"x": 0.0, "f": 0.0}

    model.run_command("resolution_recovery", 7, "return")
    assert move_started.wait(1.0)
    worker = model._resolution_change_task.worker
    try:
        model.stop_stage()
    finally:
        release_move.set()
        worker.join(1.0)

    assert move_arguments[0][:2] == (
        {"x_abs": 12.0, "f_abs": 3.0},
        True,
    )
    assert move_arguments[0][2].is_set()
    assert model._resolution_change_task is None
    events = []
    while not model.event_queue.empty():
        events.append(model.event_queue.get_nowait())
    return_event = next(
        payload for event, payload in events if event == "resolution_return_complete"
    )
    assert return_event == {"task_id": 7, "succeeded": False, "cancelled": True}
