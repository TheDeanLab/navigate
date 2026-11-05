"""Bounded, non-hardware regressions from the PR5 independent review."""
import queue
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np

from navigate.controller.controller import Controller
from navigate.controller.thread_pool import SynchronizedThreadPool
from navigate.model.devices.camera.format import CameraSettingCapability


def make_controller():
    c = Controller.__new__(Controller)
    c.configuration = {"experiment": {"MicroscopeState": {"microscope_name": "scope"}}}
    c.additional_microscopes_configs = {}
    c.acquire_bar_controller = SimpleNamespace(is_acquiring=False)
    c.model = Mock()
    c.threads_pool = SynchronizedThreadPool()
    c._main_thread_dispatch_queue = queue.Queue()
    c._event_pump_running = True
    c.launch_additional_microscopes = Mock()
    c.stop_acquisition_flag = False
    return c


def test_camera_reply_does_not_deadlock_feature_selection_on_tk():
    c = make_controller()
    c.model.camera_advanced_settings.return_value = {
        "microscope": "scope",
        "request_id": 1,
        "identity": (1,),
        "capability": CameraSettingCapability(16),
        "data_buffer": None,
    }
    c.dispatch_camera_advanced_settings(
        {"microscope": "scope", "request_id": 1}, Mock()
    )
    # Hold the queued Tk completion, reproducing a user feature selection arriving
    # before the next 20-ms event-pump tick.
    pending_completion = c._main_thread_dispatch_queue.get(timeout=1)
    returned = threading.Event()
    blocked = []

    def bounded_rescue():
        if not returned.wait(0.3):
            blocked.append(True)
        # Test-only rescue releases the waiter, so this regression never hangs pytest.
        fn, args, kwargs, done, result = pending_completion
        try:
            result["value"] = fn(*args, **kwargs)
        except Exception as exc:
            result["error"] = exc
        finally:
            done.set()

    rescue = threading.Thread(target=bounded_rescue)
    rescue.start()
    c.execute("load_feature", 1)
    returned.set()
    rescue.join(2)
    assert not blocked, "Tk feature selection blocks behind a model worker awaiting Tk"


def test_stop_during_pre_capture_handshake_does_not_start_camera_afterwards():
    c = make_controller()
    c._set_autofocus_acquisition_state = Mock()
    c.menu_controller = SimpleNamespace(feature_id_val=Mock())
    c.show_img_pipe = Mock()
    c.show_img_pipe.poll.return_value = False
    c.model.prepare_camera_buffers.return_value = {
        "microscope": "scope",
        "data_buffer": [np.zeros((2, 3), dtype=np.uint8)],
    }
    stopped = False

    def dispatch_on_tk(fn, *args, **kwargs):
        nonlocal stopped
        # The prepare RPC has returned, and the worker is waiting for its first
        # Tk callback. This is a legitimate point for the Stop button to run.
        if not stopped:
            stopped = True
            c.execute("stop_acquire")
        return fn(*args)

    c._run_on_main_thread = dispatch_on_tk
    c._start_model_capture("acquire")
    commands = [call.args[0] for call in c.model.run_command.call_args_list]
    assert commands == ["stop"], f"Camera restarted after stop: {commands}"


def test_autofocus_retires_changed_additional_camera_buffers():
    from navigate.model.model import Model
    from navigate.model.microscope import Microscope
    from navigate.model.devices.camera.format import CameraImageFormat

    class Camera:
        def __init__(self):
            self.depth = 16
            self.is_acquiring = False

        def get_image_format(self):
            return CameraImageFormat.for_bit_depth(self.depth)

        def get_advanced_setting_capabilities(self):
            return {
                "bit_depth": CameraSettingCapability(
                    self.depth, (8, 12, 16), True, reason=""
                )
            }

        def set_bit_depth(self, value):
            self.depth = value
            return value

    m = Model.__new__(Model)
    m.configuration = {
        "experiment": {
            "MicroscopeState": {"microscope_name": "main"},
            "CameraParameters": {
                name: {"img_x_pixels": 3, "img_y_pixels": 2, "binning": "1x1"}
                for name in ("main", "aux")
            },
        }
    }

    def microscope(name, camera):
        scope = Microscope.__new__(Microscope)
        scope.configuration = m.configuration
        scope.microscope_name = name
        scope.camera = camera
        scope.data_buffer = [np.zeros((2, 3), dtype=np.uint16)]
        scope._buffer_image_format = CameraImageFormat.for_bit_depth(16)
        scope.set_camera_trigger_mode = Mock()
        scope.set_camera_sensor_mode = Mock()
        scope.set_camera_roi_and_binning = Mock(return_value=True)
        scope.get_available_channels = Mock()
        scope.update_data_buffer = Mock()
        return scope

    m.active_microscope_name = "main"
    m.active_microscope = microscope("main", Camera())
    auxiliary = microscope("aux", Camera())
    m.microscopes = {"main": m.active_microscope, "aux": auxiliary}
    # A prior ordinary acquisition leaves its virtual scope and ring in place.
    m.virtual_microscopes = {"aux": microscope("aux", auxiliary.camera)}
    from navigate.model.concurrency.concurrency_tools import SharedNDArray

    m.virtual_microscopes["aux"].data_buffer = [SharedNDArray((2, 3), dtype="uint16")]
    m.is_acquiring = False
    m.data_buffer = m.active_microscope.data_buffer
    m.number_of_frames = 1
    m.img_width, m.img_height = 3, 2
    m.binning = "1x1"
    m.imaging_mode = "autofocus"
    m.plugin_acquisition_modes = {}
    read = m.camera_advanced_settings({"microscope": "aux", "request_id": 1})
    applied = m.camera_advanced_settings(
        {
            "microscope": "aux",
            "request_id": 2,
            "identity": read["identity"],
            "bit_depth": 8,
        }
    )
    assert applied["error"] is None
    # _start_model_capture('autofocus') passes no additional microscopes and
    # does not relaunch them. Autofocus.run then calls Model.prepare_acquisition.
    prepared = m.prepare_camera_buffers("main")
    assert prepared["retired"] == ["aux"]
    assert not m.virtual_microscopes  # Autofocus will only prepare the main scope.


def test_failed_hamamatsu_rollback_blocks_same_physical_camera_alias(monkeypatch):
    import importlib
    import sys
    from types import ModuleType
    from navigate.model.model import Model
    from navigate.model.devices.camera.format import CameraImageFormat
    from test.model.devices.camera.test_hamamatsu_bit_depth import FakeDCAM

    api_name = "navigate.model.devices.APIs.hamamatsu.HamamatsuAPI"
    module_name = "navigate.model.devices.camera.hamamatsu"
    api = ModuleType(api_name)
    api.DCAM = object
    monkeypatch.setitem(sys.modules, api_name, api)
    monkeypatch.delitem(sys.modules, module_name, raising=False)
    module = importlib.import_module(module_name)
    sdk = FakeDCAM()
    cameras = []
    for _ in range(2):
        cam = object.__new__(module.HamamatsuOrcaCamera)
        cam.camera_controller = sdk
        cam.is_acquiring = False
        cam.camera_parameters = {}
        cam._image_format = CameraImageFormat()
        cameras.append(cam)
    m = Model.__new__(Model)
    m.is_acquiring = False
    m.microscopes = {
        name: SimpleNamespace(camera=cam)
        for name, cam in zip(("scope", "alias"), cameras)
    }
    first = m.camera_advanced_settings({"microscope": "scope", "request_id": 1})

    def failed_write_and_restore(name, value):
        if name == "bits_per_channel":
            sdk.values[name] = 8.0
            return False
        return True

    sdk.set_property_value = failed_write_and_restore
    failure = m.camera_advanced_settings(
        {
            "microscope": "scope",
            "request_id": 2,
            "identity": first["identity"],
            "bit_depth": 8,
        }
    )
    assert "restor" in failure["error"]
    assert cameras[0]._bit_depth_error
    alias = m.camera_advanced_settings({"microscope": "alias", "request_id": 3})
    assert alias["identity"] == first["identity"]
    sys.modules.pop(module_name, None)
    assert not alias[
        "capability"
    ].writable, "Same physical camera remains writable after failed rollback"
