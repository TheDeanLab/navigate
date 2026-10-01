# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

import importlib
import sys
import types
from unittest.mock import MagicMock

import numpy as np
import pytest


def build_configuration():
    return {
        "configuration": {
            "microscopes": {
                "test_scope": {
                    "camera": {
                        "hardware": {"serial_number": "PM-123"},
                        "readout_port": 3,
                        "speed_table_index": 2,
                        "gain": 4,
                        "unitforlinedelay": 2,
                    }
                }
            }
        }
    }


def disable_camera_maps(self):
    self._offset = None
    self._variance = None
    return None, None


class FakePhotometricsController:
    def __init__(self):
        self.sensor_size = (3200, 3200)
        self.serial_no = "PM-123"
        self.readout_time = 8000
        self.binning = None
        self.exp_mode = None
        self.prog_scan_dir = None
        self.readout_port = None
        self.speed_table_index = None
        self.gain = None
        self.prog_scan_mode = 0
        self.prog_scan_line_delay = None
        self.exp_out_mode = None
        self.trig_mode = None
        self.exp_time = None
        self.close_calls = 0
        self.finish_calls = 0
        self.start_live_calls = []
        self.last_roi = None
        self.roi_shape = self.sensor_size
        self.poll_exception = None
        self.poll_payload = np.array([[1, 2], [3, 4]], dtype=np.uint16)
        self.poll_timeout_ms = None

    def close(self):
        self.close_calls += 1

    def start_live(self, exposure_time=None):
        self.start_live_calls.append(exposure_time)

    def set_roi(self, roi_left, roi_top, roi_width, roi_height):
        self.last_roi = (roi_left, roi_top, roi_width, roi_height)
        self.roi_shape = (roi_width, roi_height)

    def shape(self):
        return self.roi_shape

    def poll_frame(self, timeout_ms=10000):
        self.poll_timeout_ms = timeout_ms
        if self.poll_exception is not None:
            raise self.poll_exception
        frame = {"pixel_data": self.poll_payload.copy()}
        return frame, 10.0, 1

    def finish(self):
        self.finish_calls += 1


@pytest.fixture
def photometrics_module(monkeypatch):
    fake_pvc = types.SimpleNamespace(init_pvcam=MagicMock())
    fake_pyvcam = types.ModuleType("pyvcam")
    fake_pyvcam.pvc = fake_pvc

    class FakeSDKCamera:
        select_camera = MagicMock()

    fake_pyvcam_camera = types.ModuleType("pyvcam.camera")
    fake_pyvcam_camera.Camera = FakeSDKCamera

    monkeypatch.setitem(sys.modules, "pyvcam", fake_pyvcam)
    monkeypatch.setitem(sys.modules, "pyvcam.camera", fake_pyvcam_camera)
    sys.modules.pop("navigate.model.devices.camera.photometrics", None)

    module = importlib.import_module("navigate.model.devices.camera.photometrics")
    monkeypatch.setattr(
        module.CameraBase, "get_offset_variance_maps", disable_camera_maps
    )
    return module


@pytest.fixture
def photometrics_camera(photometrics_module):
    controller = FakePhotometricsController()
    camera = photometrics_module.PhotometricsCamera(
        "test_scope", controller, build_configuration()
    )
    return camera, controller


def test_connect_success(photometrics_module):
    fake_opened_camera = MagicMock()
    photometrics_module.PyvcamCamera.select_camera.return_value = fake_opened_camera

    result = photometrics_module.PhotometricsCamera.connect("PCIe-0")

    photometrics_module.pvc.init_pvcam.assert_called_once_with()
    photometrics_module.PyvcamCamera.select_camera.assert_called_once_with("PCIe-0")
    fake_opened_camera.open.assert_called_once_with()
    assert result is fake_opened_camera


def test_connect_failure_raises_userwarning(photometrics_module):
    photometrics_module.pvc.init_pvcam.side_effect = RuntimeError("no sdk")

    with pytest.raises(UserWarning, match="Could not establish connection with camera"):
        photometrics_module.PhotometricsCamera.connect("PCIe-1")


def test_init_applies_configuration_values(photometrics_camera):
    camera, controller = photometrics_camera

    assert camera.camera_parameters["x_pixels"] == 3200
    assert camera.camera_parameters["y_pixels"] == 3200
    assert controller.readout_port == 3
    assert controller.speed_table_index == 2
    assert controller.gain == 4
    assert controller.exp_mode == "Edge Trigger"
    assert controller.prog_scan_dir == 0


def test_set_sensor_mode_branches(photometrics_camera):
    camera, controller = photometrics_camera

    camera.set_sensor_mode("Light-Sheet")
    assert camera._scan_mode == 1
    assert controller.prog_scan_mode == 1

    with pytest.raises(KeyError):
        camera.set_sensor_mode("Unsupported")


def test_trigger_and_readout_direction_branches(photometrics_camera):
    camera, controller = photometrics_camera

    camera.set_trigger_mode("External")
    assert controller.exp_mode == "Edge Trigger"
    camera.set_trigger_mode("Internal")
    assert controller.exp_mode == "Internal Trigger"
    camera.set_trigger_mode("Unknown")
    assert controller.exp_mode == "Internal Trigger"
    camera.set_trigger_mode("Software")
    assert controller.exp_mode == "Software Trigger Edge"

    camera.set_readout_direction("Top-to-Bottom")
    assert controller.prog_scan_dir == 0
    camera.set_readout_direction("Bottom-to-Top")
    assert controller.prog_scan_dir == 1
    camera.set_readout_direction("Alternate")
    assert controller.prog_scan_dir == 2
    camera.set_readout_direction("Invalid")
    assert controller.prog_scan_dir == 2


def test_readout_exposure_line_interval_and_aslm_math(photometrics_camera):
    camera, controller = photometrics_camera

    assert camera.calculate_readout_time() == pytest.approx(0.008, rel=1e-6)

    assert camera.set_exposure_time(0.012) is True
    assert camera._exposure_time == 12
    assert controller.exp_time == 12
    assert controller.start_live_calls[-1] == 12

    assert camera.set_line_interval(17) is True
    assert camera._scan_delay == 17
    assert controller.prog_scan_line_delay == 17

    exposure_time, line_delay, acquisition_time = (
        camera.calculate_light_sheet_exposure_time(0.2, 100)
    )
    assert exposure_time == pytest.approx(0.01, rel=1e-6)
    assert line_delay == 46
    assert acquisition_time == pytest.approx(0.202606, rel=1e-6)
    assert camera.camera_parameters["line_interval"] == 10


def test_set_binning_valid_and_invalid(photometrics_camera):
    camera, controller = photometrics_camera

    assert camera.set_binning("3x3") is False

    assert camera.set_binning("2x2") is True
    assert controller.binning == 2
    assert camera.x_binning == 2
    assert camera.y_binning == 2
    assert camera.x_pixels == 1024
    assert camera.y_pixels == 1024


def test_set_roi_validation_and_success(photometrics_camera):
    camera, controller = photometrics_camera

    assert camera.set_ROI(roi_width=3210, roi_height=3200) is False
    assert camera.set_ROI(roi_width=101, roi_height=100) is False
    assert camera.set_ROI(roi_width=100, roi_height=100, center_y=1601) is False

    assert camera.set_ROI(roi_width=200, roi_height=200, center_x=1600, center_y=1600)
    assert controller.last_roi == (1500, 1500, 200, 200)
    assert camera.x_pixels == 200
    assert camera.y_pixels == 200


def test_initialize_image_series_in_both_modes_and_close(photometrics_camera):
    camera, controller = photometrics_camera
    data_buffer = [np.zeros((2, 2), dtype=np.uint16) for _ in range(2)]

    controller.prog_scan_mode = 0
    camera.initialize_image_series(data_buffer, number_of_frames=2)
    assert controller.exp_out_mode == "Any Row"
    assert controller.exp_mode == "Edge Trigger"
    assert camera.is_acquiring is True
    assert camera._frames_received == 0
    assert camera._frame_ids == []
    assert controller.start_live_calls[-1] is None

    camera._scan_delay = 11
    controller.prog_scan_mode = 1
    camera.initialize_image_series(data_buffer, number_of_frames=2)
    assert controller.exp_mode == "Edge Trigger"
    assert controller.prog_scan_line_delay == 11
    assert controller.exp_out_mode == 4

    camera.close_image_series()
    assert controller.finish_calls == 1
    assert camera.is_acquiring is False


def test_receive_images_success_wraparound_and_error_path(photometrics_camera):
    camera, controller = photometrics_camera
    data_buffer = [np.zeros((2, 2), dtype=np.uint16) for _ in range(2)]
    camera.initialize_image_series(data_buffer, number_of_frames=2)

    camera._frames_received = 1
    frame_ids = camera.get_new_frame()
    assert frame_ids == [1]
    assert controller.poll_timeout_ms == 10000
    assert np.array_equal(data_buffer[1], controller.poll_payload)
    assert camera._frames_received == 0

    controller.poll_exception = RuntimeError("poll failed")
    assert camera.get_new_frame() == []


def test_destructor_closes_controller(photometrics_camera):
    camera, controller = photometrics_camera

    camera.__del__()
    assert controller.close_calls == 1
