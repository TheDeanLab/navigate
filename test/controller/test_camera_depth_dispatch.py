"""Model workers negotiate formats before capture; only the main thread binds UI."""

from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from navigate.controller.controller import Controller
from navigate.model.devices.camera.format import CameraSettingCapability


@pytest.fixture
def controller():
    c = Controller.__new__(Controller)
    c.configuration = {"experiment": {"MicroscopeState": {"microscope_name": "scope"}}}
    c.additional_microscopes_configs = {}
    c.stop_acquisition_flag = False
    c.model = Mock()
    c.acquire_bar_controller = SimpleNamespace(is_acquiring=False)
    c.threads_pool = Mock()
    c._run_on_main_thread = Mock(side_effect=lambda fn, *a, **kw: fn(*a))
    c.launch_additional_microscopes = Mock()
    return c


def test_setting_dispatch_is_worker_only_and_clears_pending(controller):
    c = controller
    callback = Mock()
    request = dict(microscope="scope", request_id=1, bit_depth=8, identity=(1,))
    c.model.camera_advanced_settings.return_value = {
        **request,
        "error": None,
        "capability": CameraSettingCapability(8),
        "data_buffer": [np.zeros((2, 3), np.uint8)],
    }
    c.dispatch_camera_advanced_settings(request, callback)
    assert c._camera_settings_pending == 1
    c.model.camera_advanced_settings.assert_not_called()
    resource, worker = c.threads_pool.createThread.call_args.args
    assert resource == "model"
    worker()
    assert c._camera_settings_pending == 0
    assert c.data_buffer[0].dtype == np.uint8
    callback.assert_called_once()
    assert c._run_on_main_thread.call_args.kwargs["wait"] is True


def test_worker_failure_completes_pending_request(controller):
    c = controller
    c.model.camera_advanced_settings.side_effect = RuntimeError("disconnected")
    callback = Mock()
    c.dispatch_camera_advanced_settings(
        dict(microscope="scope", request_id=1, bit_depth=8), callback
    )
    c.threads_pool.createThread.call_args.args[1]()
    assert c._camera_settings_pending == 0
    assert callback.call_args.args[0]["error"] == "disconnected"


def test_capture_negotiates_then_binds_before_starting_model(controller):
    c = controller
    events = []
    data = [np.zeros((2, 3), np.uint8)]
    c.model.prepare_camera_buffers.side_effect = lambda *args: events.append(
        "prepare"
    ) or {"microscope": "scope", "data_buffer": data, "capture_token": (1, "scope")}
    c.launch_additional_microscopes.side_effect = lambda: events.append("launch")

    def run(*args):
        assert c.data_buffer is data
        events.append("capture")

    c.model.start_prepared_capture.side_effect = run
    c._start_model_capture("acquire")
    assert events == ["prepare", "launch", "capture"]


def test_capture_failure_never_starts_model(controller):
    c = controller
    c.model.prepare_camera_buffers.side_effect = ValueError("unsupported saved depth")
    with pytest.raises(ValueError):
        c._start_model_capture("acquire")
    c.model.run_command.assert_not_called()


def test_acquire_during_pending_write_resets_acquire_button(controller, monkeypatch):
    c = controller
    c._camera_settings_pending = 1
    c.acquire_bar_controller.is_acquiring = True
    c.acquire_bar_controller.stop_acquire = Mock()
    monkeypatch.setattr("navigate.controller.controller.messagebox.showinfo", Mock())
    c.execute("acquire")
    c.acquire_bar_controller.stop_acquire.assert_called_once()
    c.model.run_command.assert_not_called()


def test_capture_start_failure_cleans_up_partial_acquisition(controller):
    c = controller
    c.model.prepare_camera_buffers.return_value = {
        "microscope": "scope",
        "data_buffer": [np.zeros((2, 3), np.uint8)],
        "capture_token": (1, "scope"),
    }
    c.model.start_prepared_capture.side_effect = RuntimeError("capture failed")
    with pytest.raises(RuntimeError, match="capture failed"):
        c._start_model_capture("acquire")
    c.model.run_command.assert_called_once_with("stop")


def test_canceled_capture_never_reads_frames_or_clears_stop(controller):
    c = controller
    c._start_capture_ui = Mock()
    c._finish_capture_ui = Mock()
    c._on_capture_started = Mock()
    c.show_img_pipe = Mock()

    def cancel(*args):
        c.stop_acquisition_flag = True
        return False

    c._start_model_capture = Mock(side_effect=cancel)
    c.threads_pool.createThread.side_effect = lambda resource, worker: (
        worker(),
        Mock(),
    )[1]
    c.capture_image("acquire", "single")
    assert c.stop_acquisition_flag
    c.show_img_pipe.recv.assert_not_called()
    c._on_capture_started.assert_not_called()
    c._finish_capture_ui.assert_called_once_with("single", 0)


def test_retired_auxiliary_window_can_still_be_removed(controller):
    c = controller
    window = Mock()
    c.additional_microscopes = {"aux": {"popup_window": window}}
    c.destroy_virtual_microscope("aux", destroy_window=True)
    assert not c.additional_microscopes
    window.popup.dismiss.assert_called_once()
    c.model.destroy_virtual_microscope.assert_not_called()


def test_binding_retired_auxiliary_drops_old_buffer_but_keeps_window(controller):
    c = controller
    window = Mock()
    c.additional_microscopes = {
        "aux": {
            "popup_window": window,
            "data_buffer": object(),
            "show_img_pipe": object(),
        }
    }
    c._bind_camera_buffer(
        {"microscope": "scope", "data_buffer": None, "retired": ["aux"]}
    )
    assert c.additional_microscopes["aux"] == {"popup_window": window}


def test_scan_write_locks_capture_until_worker_confirms(controller):
    c = controller
    c.model.camera_advanced_settings.return_value = {
        "microscope": "scope",
        "data_buffer": None,
    }
    c.dispatch_camera_advanced_settings(
        dict(microscope="scope", request_id=1, setting="scan_speed", value=2), Mock()
    )
    assert c._camera_settings_pending == 1
    c.threads_pool.createThread.call_args.args[1]()
    assert c._camera_settings_pending == 0
