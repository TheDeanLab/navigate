"""Idle readbacks cannot overwrite acquisition state or a pending GUI target."""

from queue import Queue
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from navigate.controller.controller import Controller
from navigate.controller.sub_controllers.stages import StageController


def snapshot(**kwargs):
    return dict(
        microscope_name="scope",
        sample_started=100.0,
        positions={"x_pos": 12.0, "y_pos": 13.0},
        unavailable_axes=[],
        **kwargs,
    )


@pytest.fixture
def controller(monkeypatch):
    monkeypatch.setattr("navigate.controller.controller.time.monotonic", lambda: 101.0)
    controller = Controller.__new__(Controller)
    controller.acquire_bar_controller = SimpleNamespace(is_acquiring=False)
    controller.is_autofocusing = False
    controller.configuration_controller = SimpleNamespace(
        microscope_name="scope", microscope_config={"stage": {}}
    )
    controller._stage_position_valid_after = 99.0
    controller.stage_controller = Mock()
    return controller


def test_recent_idle_snapshot_is_applied(controller):
    result = snapshot()
    controller._update_idle_stage_position(result)
    controller.stage_controller.update_position_telemetry.assert_called_once_with(
        result
    )


@pytest.mark.parametrize(
    "reason",
    ["acquiring", "autofocus", "scope", "old", "command", "pending", "disabled"],
)
def test_stale_or_ineligible_snapshot_is_discarded(controller, reason):
    result = snapshot()
    if reason == "acquiring":
        controller.acquire_bar_controller.is_acquiring = True
    elif reason == "autofocus":
        controller.is_autofocusing = True
    elif reason == "scope":
        result["microscope_name"] = "other"
    elif reason == "old":
        result["sample_started"] = 80
    elif reason == "command":
        controller._stage_position_valid_after = 100.5
    elif reason == "disabled":
        controller.configuration_controller.microscope_config["stage"][
            "position_polling"
        ] = False
    else:
        controller._stage_position_moves_pending = 1
    controller._update_idle_stage_position(result)
    controller.stage_controller.update_position_telemetry.assert_not_called()


@pytest.mark.parametrize("entry_state", ["normal", "disabled"])
def test_telemetry_preserves_focused_and_debounced_targets(entry_state):
    stage = StageController.__new__(StageController)
    widgets = {axis: SimpleNamespace(widget=Mock()) for axis in ("x", "y", "z")}
    widgets["x"].widget.cget.return_value = entry_state
    stage.view = SimpleNamespace(
        get_widgets=lambda: widgets,
        focus_get=lambda: widgets["x"].widget,
    )
    stage.stage_axes = ["x", "y", "z"]
    stage.event_id = {"x": None, "y": "pending", "z": None}
    stage.widget_vals = {axis: Mock() for axis in stage.stage_axes}
    stage.stage_setting_dict = {"x": 1, "y": 2, "z": 3}
    stage.refresh_position_telemetry_status = Mock()
    result = snapshot()
    result["positions"]["z_pos"] = 42
    stage.update_position_telemetry(result)
    if entry_state == "normal":
        stage.widget_vals["x"].set.assert_not_called()
    else:
        # A joystick-disabled entry may retain Tk focus; it is not being edited.
        stage.widget_vals["x"].set.assert_called_once_with(12)
    stage.widget_vals["y"].set.assert_not_called()
    stage.widget_vals["z"].set.assert_called_once_with(42)
    assert stage.stage_setting_dict == {
        "x": 1 if entry_state == "normal" else 12,
        "y": 2,
        "z": 42,
    }
    for widget in widgets.values():
        widget.widget.trigger_focusout_validation.assert_not_called()


def test_pending_move_clears_on_failure_and_invalidates_old_readbacks(controller):
    controller.threads_pool = SimpleNamespace(createThread=Mock())
    controller.move_stage = Mock(side_effect=OSError("move failed"))
    controller._run_on_main_thread = lambda fn: fn()
    controller.execute("stage", 10, "x")
    assert controller._stage_position_moves_pending == 1
    work = controller.threads_pool.createThread.call_args.kwargs["target"]
    with pytest.raises(OSError):
        work()
    assert controller._stage_position_moves_pending == 0
    assert controller._stage_position_valid_after == 101


def test_status_marks_old_positions_stale_and_acquisition_paused(monkeypatch):
    monkeypatch.setattr(
        "navigate.controller.sub_controllers.stages.time.monotonic", lambda: 110
    )
    stage = StageController.__new__(StageController)
    stage.parent_controller = SimpleNamespace(
        acquire_bar_controller=SimpleNamespace(is_acquiring=False),
        configuration_controller=SimpleNamespace(microscope_config={"stage": {}}),
    )
    label = Mock()
    stage.view = SimpleNamespace(
        position_frame=SimpleNamespace(set_polling_indicator=label)
    )
    stage._last_position_telemetry = snapshot()
    stage.refresh_position_telemetry_status()
    label.assert_called_with(False, "Stage position polling: last readback is stale")
    stage.parent_controller.acquire_bar_controller.is_acquiring = True
    stage.refresh_position_telemetry_status()
    label.assert_called_with(
        False, "Stage position polling: paused during acquisition or movement"
    )


def test_control_events_invalidate_queued_telemetry_before_it_is_displayed(controller):
    controller._event_pump_running = True
    controller.event_queue = Queue()
    controller.autofocus_progress_queue = Queue()
    controller.stage_position_queue = Queue(1)
    controller.event_listeners = {}
    controller.update_stage_controller_silent = Mock()
    controller.event_queue.put(("update_stage", {"x_pos": 22}))
    controller.stage_position_queue.put(snapshot())
    controller.update_event()
    controller.update_stage_controller_silent.assert_called_once_with({"x_pos": 22})
    controller.stage_controller.update_position_telemetry.assert_not_called()


def test_indicator_pulses_after_refresh_and_turns_dark_when_disabled(monkeypatch):
    now = [100.1]
    monkeypatch.setattr(
        "navigate.controller.sub_controllers.stages.time.monotonic", lambda: now[0]
    )
    stage = StageController.__new__(StageController)
    stage_config = {}
    stage.parent_controller = SimpleNamespace(
        acquire_bar_controller=SimpleNamespace(is_acquiring=False),
        configuration_controller=SimpleNamespace(
            microscope_config={"stage": stage_config}
        ),
    )
    indicator = Mock()
    stage.view = SimpleNamespace(
        position_frame=SimpleNamespace(set_polling_indicator=indicator)
    )
    stage._last_position_telemetry = snapshot()
    stage._position_refresh_received_at = 100.0
    stage.refresh_position_telemetry_status()
    assert indicator.call_args.args[0] is True
    now[0] = 100.3
    stage.refresh_position_telemetry_status()
    assert indicator.call_args.args[0] is False
    now[0] = 100.1
    stage_config["position_polling"] = False
    stage.refresh_position_telemetry_status()
    indicator.assert_called_with(False, "Stage position polling: disabled")
