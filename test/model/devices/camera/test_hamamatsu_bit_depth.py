"""Transactional DCAM depth changes; no SDK or physical camera is required."""

import importlib
import sys
from types import ModuleType

import numpy as np
import pytest

from navigate.model.devices.camera.format import CameraImageFormat


class FakeDCAM:
    def __init__(self):
        self.values = {
            "bits_per_channel": 16.0,
            "image_pixel_type": 2.0,
            "internal_line_interval": 1e-5,
            "minimum_trigger_interval": 0.01,
        }
        self.choices = (8.0, 12.0, 16.0)
        self.writable = True
        self.writes = []
        self.reject = None
        self.bad_layout = False
        self.dev_close = lambda: None

    def get_property_value(self, name):
        return self.values.get(name, False)

    def get_property_values(self, name):
        return self.choices if name == "bits_per_channel" else (1.0, 2.0)

    def is_property_writable(self, name):
        return self.writable

    def get_property_range(self, name):
        return (1e-6, 10, 1e-6)

    def set_property_value(self, name, value):
        self.writes.append((name, value))
        if (name, value) == self.reject:
            return False
        self.values[name] = float(value)
        return True

    def get_frame_layout(self):
        from navigate.model.devices.APIs.hamamatsu.frame_layout import DCAMFrameLayout

        pixel_type = int(self.values["image_pixel_type"])
        if self.bad_layout and self.values["bits_per_channel"] == 8:
            pixel_type = 5
        return DCAMFrameLayout(3, 2, pixel_type, 6, 12)


@pytest.fixture
def camera(monkeypatch):
    api_name = "navigate.model.devices.APIs.hamamatsu.HamamatsuAPI"
    module_name = "navigate.model.devices.camera.hamamatsu"
    api = ModuleType(api_name)
    api.DCAM = object
    monkeypatch.setitem(sys.modules, api_name, api)
    monkeypatch.delitem(sys.modules, module_name, raising=False)
    module = importlib.import_module(module_name)
    camera = object.__new__(module.HamamatsuOrcaCamera)
    camera.camera_controller = FakeDCAM()
    camera.is_acquiring = False
    camera.camera_parameters = {}
    camera._image_format = CameraImageFormat()
    yield camera
    sys.modules.pop(module_name, None)


def test_capabilities_are_discovered_without_writes(camera):
    capability = camera.get_advanced_setting_capabilities()["bit_depth"]
    assert capability.choices == (8, 12, 16)
    assert capability.current_value == 16
    assert capability.writable
    assert camera.camera_controller.writes == []


@pytest.mark.parametrize(
    "choices,writable", [(None, True), ((16.0,), True), ((8.0, 16.0), False)]
)
def test_missing_fixed_and_readonly_are_disabled(camera, choices, writable):
    camera.camera_controller.choices = choices
    camera.camera_controller.writable = writable
    capability = camera.get_advanced_setting_capabilities()["bit_depth"]
    assert not capability.writable
    assert capability.reason


@pytest.mark.parametrize("depth", [8, 12, 16])
def test_exact_depth_application_refreshes_format_and_timing(camera, depth):
    assert camera.set_bit_depth(depth) == depth
    assert camera.get_image_format() == CameraImageFormat.for_bit_depth(depth)
    assert camera.get_bit_depth() == depth
    assert camera.minimum_exposure_time == 1e-6
    assert camera.camera_parameters["line_interval"] == 1e-5


def test_invalid_and_busy_requests_do_not_write(camera):
    with pytest.raises(ValueError):
        camera.set_bit_depth(10)
    camera.is_acquiring = True
    with pytest.raises(RuntimeError):
        camera.set_bit_depth(8)
    assert not camera.camera_controller.writes


def test_partial_change_rolls_back_and_restores_format(camera):
    camera.camera_controller.reject = ("image_pixel_type", 1)
    with pytest.raises(RuntimeError):
        camera.set_bit_depth(8)
    assert camera.camera_controller.values["bits_per_channel"] == 16
    assert camera.camera_controller.values["image_pixel_type"] == 2
    assert camera.get_image_format() == CameraImageFormat.for_bit_depth(16)


def test_unsupported_layout_rolls_back(camera):
    camera.camera_controller.bad_layout = True
    with pytest.raises(RuntimeError):
        camera.set_bit_depth(8)
    assert camera.camera_controller.values["bits_per_channel"] == 16
    assert ("bits_per_channel", 8) in camera.camera_controller.writes


def test_failed_rollback_blocks_acquisition(camera):
    def fail(name, value):
        camera.camera_controller.values[name] = 8.0
        return False

    camera.camera_controller.set_property_value = fail
    with pytest.raises(RuntimeError, match="restor|rollback"):
        camera.set_bit_depth(8)
    with pytest.raises(RuntimeError):
        camera.initialize_image_series([np.zeros((2, 3), np.uint16)], 1)


def test_lightning_stays_readonly_until_coupled_mode_is_implemented(camera):
    module = sys.modules["navigate.model.devices.camera.hamamatsu"]
    camera.__class__ = module.HamamatsuOrcaLightningCamera
    capability = camera.get_advanced_setting_capabilities()["bit_depth"]
    assert not capability.writable
    assert "full" in capability.reason.lower()


def test_unsupported_initial_layout_keeps_controls_available_for_diagnosis(camera):
    module = sys.modules["navigate.model.devices.camera.hamamatsu"]
    sdk = FakeDCAM()
    sdk.max_image_width, sdk.max_image_height = 3, 2
    sdk.min_image_width = sdk.min_image_height = 1
    sdk.step_image_width = sdk.step_image_height = 1

    def unsupported():
        raise ValueError("Unsupported packed layout")

    sdk.get_frame_layout = unsupported
    configuration = {
        "configuration": {
            "microscopes": {
                "scope": {
                    "camera": {
                        "hardware": {"serial_number": "fake"},
                        "defect_correct_mode": 1,
                    }
                }
            }
        },
        "experiment": {"CameraParameters": {"scope": {}}},
    }
    instance = module.HamamatsuOrcaCamera("scope", sdk, configuration)
    capability = instance.get_advanced_setting_capabilities()["bit_depth"]
    assert not capability.writable
    assert "packed" in capability.reason
    with pytest.raises(RuntimeError, match="packed"):
        instance.initialize_image_series([], 0)


def test_setter_rejects_depth_wider_than_readonly_native_container(camera):
    sdk = camera.camera_controller
    sdk.values.update(bits_per_channel=8.0, image_pixel_type=1.0)
    sdk.is_property_writable = lambda name: name != "image_pixel_type"
    with pytest.raises(RuntimeError):
        camera.set_bit_depth(16)
    assert sdk.values["bits_per_channel"] == 8


def test_failed_snapshot_never_leaves_changed_depth_as_restored(camera):
    sdk = camera.camera_controller
    original_read = sdk.get_property_value
    calls = 0

    def read(name):
        nonlocal calls
        if name == "bits_per_channel":
            calls += 1
            if calls == 3:
                return False
        return original_read(name)

    sdk.get_property_value = read
    sdk.reject = ("image_pixel_type", 1)
    with pytest.raises(RuntimeError):
        camera.set_bit_depth(8)
    assert sdk.values["bits_per_channel"] == 16


def test_sensor_mode_refreshes_cached_precision_before_buffer_negotiation(camera):
    sdk = camera.camera_controller
    sdk.values.update(bits_per_channel=8.0, image_pixel_type=1.0)
    camera._refresh_image_format()
    original_set = sdk.set_property_value

    def set_value(name, value):
        result = original_set(name, value)
        if name == "sensor_mode":
            sdk.values.update(bits_per_channel=16.0, image_pixel_type=2.0)
        return result

    sdk.set_property_value = set_value
    camera.set_sensor_mode("Normal")
    assert camera.get_image_format() == CameraImageFormat.for_bit_depth(16)


def test_failed_quest_restart_cannot_adopt_changed_depth_on_retry(camera):
    module = sys.modules["navigate.model.devices.camera.hamamatsu"]
    camera.__class__ = module.HamamatsuOrcaQuest2Camera
    camera.camera_parameters["reinitialize_on_restart"] = True
    camera._capture_started_before = True
    sdk = camera.camera_controller
    sdk.values["bits_per_channel"] = 12
    camera._refresh_image_format()
    calls = []

    def reinitialize():
        calls.append("restart")
        if len(calls) == 1:
            sdk.values["bits_per_channel"] = 16
            raise RuntimeError("Cannot restore DCAM property bits_per_channel.")
        return True

    sdk.reinitialize = reinitialize
    sdk.configure_frame_format = lambda image_format: None
    sdk.start_acquisition = lambda data, count: True
    with pytest.raises(RuntimeError):
        camera.initialize_image_series([np.zeros((2, 3), np.uint16)], 1)
    with pytest.raises(RuntimeError):
        camera.initialize_image_series([np.zeros((2, 3), np.uint16)], 1)
