"""Laser requests use model workers; completions and Tk state stay on main."""

from queue import Queue
from threading import Thread, get_ident
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from navigate.controller.controller import Controller


@pytest.fixture
def controller():
    controller = Controller.__new__(Controller)
    controller.model = Mock()
    controller.acquire_bar_controller = SimpleNamespace(
        is_acquiring=False, stop_acquire=Mock()
    )
    controller.threads_pool = Mock()
    controller._run_on_main_thread = Mock()
    return controller


@pytest.mark.parametrize("writing", [False, True])
def test_dispatch_keeps_model_io_off_main_thread(controller, writing):
    c = controller
    main = get_ident()

    def on_result(result):
        assert get_ident() == main

    callback = Mock(side_effect=on_result)
    completed = Queue()
    c._run_on_main_thread.side_effect = lambda fn, *args, **kwargs: completed.put(
        (fn, args)
    )

    def model_call(request):
        assert get_ident() != main
        return {**request, "connection": "simulated"}

    c.model.laser_advanced_settings.side_effect = model_call
    request = dict(microscope="scope", laser="488", request_id=1)
    if writing:
        request.update(mode="cw", identity="token")
    c.execute("laser_advanced_settings", request, callback)
    assert c._laser_settings_pending == 1
    c.model.laser_advanced_settings.assert_not_called()
    resource, worker = c.threads_pool.createThread.call_args.args
    assert resource == "model"
    thread = Thread(target=worker)
    thread.start()
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert c._laser_settings_pending == 1
    callback.assert_not_called()
    fn, args = completed.get_nowait()
    fn(*args)
    assert c._laser_settings_pending == 0
    callback.assert_called_once()
    assert c._run_on_main_thread.call_args.kwargs["wait"] is True


@pytest.mark.parametrize("busy", [False, True])
def test_errors_and_busy_dispatch_release_pending_on_main(controller, busy):
    c = controller
    c.acquire_bar_controller.is_acquiring = busy
    c.model.laser_advanced_settings.side_effect = RuntimeError("disconnected")
    c._run_on_main_thread.side_effect = lambda fn, *args, **kwargs: fn(*args)
    callback = Mock()
    c.dispatch_laser_advanced_settings({"request_id": 1}, callback)
    c.acquire_bar_controller.is_acquiring = False
    c.threads_pool.createThread.call_args.args[1]()
    assert c._laser_settings_pending == 0
    assert callback.call_args.args[0]["error"]
    if busy:
        c.model.laser_advanced_settings.assert_not_called()


@pytest.mark.parametrize(
    "command", ["acquire", "acquire_and_save", "autofocus", "tony_wilson"]
)
def test_acquisition_cannot_overtake_pending_laser_request(
    controller, monkeypatch, command
):
    controller._laser_settings_pending = 1
    message = Mock()
    monkeypatch.setattr("navigate.controller.controller.messagebox.showinfo", message)
    controller.execute(command)
    message.assert_called_once()
    controller.threads_pool.createThread.assert_not_called()
    controller.model.assert_not_called()


def test_dispatch_failure_does_not_permanently_block_acquisition(controller):
    controller.threads_pool.createThread.side_effect = RuntimeError("pool closed")
    with pytest.raises(RuntimeError, match="pool closed"):
        controller.dispatch_laser_advanced_settings({}, Mock())
    assert controller._laser_settings_pending == 0


def test_stop_clears_acquisition_flag_before_popup_refresh(controller):
    c = controller
    c.acquire_bar_controller.is_acquiring = True
    c.acquire_bar_controller.stop_acquire.side_effect = lambda: setattr(
        c.acquire_bar_controller, "is_acquiring", False
    )
    c.additional_microscopes_configs = {}
    for name in (
        "channels_tab_controller",
        "camera_view_controller",
        "camera_setting_controller",
        "mip_setting_controller",
        "waveform_tab_controller",
    ):
        setattr(c, name, Mock())
    c.advanced_laser_setting_controller = Mock()

    def refresh(acquiring):
        assert acquiring is False
        assert c.acquire_bar_controller.is_acquiring is False

    c.advanced_laser_setting_controller.set_acquisition_state.side_effect = refresh
    c.set_mode_of_sub("stop")
