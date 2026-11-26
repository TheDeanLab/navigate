"""Progress travels through the existing main-thread event pump, never model RPCs."""

import threading
from queue import Queue
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from navigate.controller.controller import Controller
from navigate.model.model import Model
from test.tools.test_stack_progress import plan


def test_event_pump_delivers_latest_progress_on_main_thread_without_hardware_calls():
    controller = Controller.__new__(Controller)
    controller._event_pump_running = True
    controller.autofocus_progress_queue = Queue()
    controller.event_queue = Queue()
    controller.stack_progress_queue = Queue()
    controller.stage_position_queue = Queue()
    controller.event_listeners = {}
    controller.model = Mock()
    seen = []
    controller.channels_tab_controller = SimpleNamespace(
        update_stack_progress=lambda p: seen.append((p, threading.current_thread()))
    )
    p = plan()
    for count in (1, 5, 10):
        controller.stack_progress_queue.put(p.snapshot(count))
    controller.update_event()
    assert seen == [(p.snapshot(10), threading.main_thread())]
    assert controller.model.mock_calls == []


def test_optional_display_failure_is_isolated():
    controller = Controller.__new__(Controller)
    controller._event_pump_running = True
    controller.stack_progress_queue = Queue()
    controller.stack_progress_queue.put(plan().snapshot(1))
    controller.channels_tab_controller = Mock()
    controller.channels_tab_controller.update_stack_progress.side_effect = RuntimeError(
        "destroyed widget"
    )
    controller._update_stack_progress()
    assert controller.stack_progress_queue.empty()


@pytest.mark.parametrize("canceled", [False, True])
def test_controller_binds_progress_before_start_using_existing_preparation_rpc(
    canceled,
):
    controller = Controller.__new__(Controller)
    controller.stop_acquisition_flag = False
    controller.additional_microscopes_configs = {}
    controller.configuration = {
        "experiment": {"MicroscopeState": {"microscope_name": "scope"}}
    }
    controller.model = Mock()
    token = (4, "scope")
    controller.model.prepare_camera_buffers.return_value = {"capture_token": token}
    controller.model.start_prepared_capture.return_value = True
    controller.launch_additional_microscopes = Mock()
    controller._run_on_main_thread = lambda f, **_: f()

    def bind(_):
        controller.stop_acquisition_flag = canceled

    controller._bind_camera_buffer = bind
    seen = []

    def begin(value):
        assert threading.current_thread() is threading.main_thread()
        controller.model.start_prepared_capture.assert_not_called()
        seen.append(value)

    controller.channels_tab_controller = SimpleNamespace(begin_stack_progress=begin)
    assert controller._start_model_capture("acquire") is not canceled
    assert seen == ([] if canceled else [token])
    assert controller.model.mock_calls == [
        call.prepare_camera_buffers("scope", ()),
        (
            call.cancel_prepared_capture()
            if canceled
            else call.start_prepared_capture(token, "acquire")
        ),
    ]


@pytest.mark.parametrize("outcome", ["success", "cancel", "error"])
def test_prepared_capture_token_is_bound_without_extra_model_commands(outcome):
    token = (4, "scope")
    seen = []
    model = SimpleNamespace(
        _prepared_camera_token=token if outcome != "cancel" else None,
        _stack_progress_token=None,
        configuration={"experiment": {"MicroscopeState": {"microscope_name": "scope"}}},
    )

    def run(command, *args):
        seen.append((command, args, model._stack_progress_token))
        if outcome == "error":
            raise RuntimeError("startup failed")

    model.run_command = run
    if outcome == "error":
        with pytest.raises(RuntimeError):
            Model.start_prepared_capture(model, token, "acquire")
        assert model._stack_progress_token is None
    else:
        assert Model.start_prepared_capture(model, token, "acquire") is (
            outcome == "success"
        )
    assert seen == ([] if outcome == "cancel" else [("acquire", (), token)])
