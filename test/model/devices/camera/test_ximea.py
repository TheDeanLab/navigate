# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

import importlib
import sys
import types

import numpy as np
import pytest


def build_configuration(input_trigger_port=1):
    camera_config = {"hardware": {"serial_number": "XI-123"}}
    if input_trigger_port is not None:
        camera_config["input_trigger_port"] = input_trigger_port

    return {
        "configuration": {
            "microscopes": {
                "test_scope": {
                    "camera": camera_config,
                }
            }
        }
    }


def disable_camera_maps(self):
    self._offset = None
    self._variance = None
    return None, None


class FakeXiCam:
    def __init__(self, xi_error_cls):
        self.xi_error_cls = xi_error_cls
        self.params = {
            "width:max": 2048,
            "height:max": 2048,
            "width:min": 16,
            "height:min": 16,
            "width:inc": 8,
            "height:inc": 8,
            "offsetX:min": 0,
            "offsetX:inc": 8,
            "offsetY:min": 0,
            "offsetY:inc": 8,
            "exposure:min": 100,
            "downsampling": "XI_DWN_1x1",
            "width": 2048,
            "height": 2048,
            "device_sn": b"XI-123",
        }
        self.get_param_calls = []
        self.set_calls = []
        self.fail_on_set = set()
        self.start_calls = 0
        self.stop_calls = 0
        self.close_calls = 0
        self.get_image_exception = None

    def get_param(self, name):
        self.get_param_calls.append(name)
        return self.params[name]

    def set_param(self, name, value):
        if name in self.fail_on_set:
            raise self.xi_error_cls(f"failed to set {name}")
        self.set_calls.append((name, value))
        self.params[name] = value

    def start_acquisition(self):
        self.start_calls += 1

    def stop_acquisition(self):
        self.stop_calls += 1

    def close_device(self):
        self.close_calls += 1

    def get_image(self, image, timeout):
        del image
        del timeout
        if self.get_image_exception is not None:
            raise self.get_image_exception


@pytest.fixture
def ximea_module(monkeypatch):
    xiapi_module = types.ModuleType("ximea.xiapi")

    class Xi_error(Exception):
        pass

    class Camera:
        def __init__(self):
            self.opened_serial = None

        def open_device_by_SN(self, serial):
            self.opened_serial = serial

    class Image:
        def __init__(self):
            self.bp = None
            self.bp_size = 0

    xiapi_module.Xi_error = Xi_error
    xiapi_module.Camera = Camera
    xiapi_module.Image = Image

    ximea_package = types.ModuleType("ximea")
    ximea_package.xiapi = xiapi_module

    monkeypatch.setitem(sys.modules, "ximea", ximea_package)
    monkeypatch.setitem(sys.modules, "ximea.xiapi", xiapi_module)
    sys.modules.pop("navigate.model.devices.camera.ximea", None)

    module = importlib.import_module("navigate.model.devices.camera.ximea")
    monkeypatch.setattr(module.CameraBase, "get_offset_variance_maps", disable_camera_maps)
    return module


@pytest.fixture
def ximea_camera(ximea_module):
    cam = FakeXiCam(ximea_module.xiapi.Xi_error)
    camera = ximea_module.XimeaBase("test_scope", cam, build_configuration())
    return camera, cam


def test_connect_success(ximea_module):
    camera = ximea_module.XimeaBase.connect("XI-SN-42")

    assert isinstance(camera, ximea_module.xiapi.Camera)
    assert camera.opened_serial == "XI-SN-42"


def test_connect_failure_raises_userwarning(ximea_module, monkeypatch):
    class BrokenCamera:
        def open_device_by_SN(self, serial):
            raise RuntimeError(f"cannot open {serial}")

    monkeypatch.setattr(ximea_module.xiapi, "Camera", BrokenCamera)

    with pytest.raises(
        UserWarning, match="Could not establish connection with XIMEA camera"
    ):
        ximea_module.XimeaBase.connect("XI-SN-99")


def test_init_normalizes_trigger_port_and_supported_modes(ximea_module):
    cam = FakeXiCam(ximea_module.xiapi.Xi_error)
    camera = ximea_module.XimeaBase(
        "test_scope", cam, build_configuration(input_trigger_port=99)
    )

    assert cam.set_calls[0] == ("gpi_selector", "XI_GPI_PORT1")
    assert ("gpi_mode", "XI_GPI_TRIGGER") in cam.set_calls
    assert ("trigger_source", "XI_TRG_EDGE_RISING") in cam.set_calls
    assert camera.camera_parameters["supported_sensor_modes"] == ["Normal"]
    assert camera.camera_parameters["supported_readout_directions"] == ["Top-to-Bottom"]


def test_init_accepts_valid_trigger_port(ximea_module):
    cam = FakeXiCam(ximea_module.xiapi.Xi_error)
    ximea_module.XimeaBase("test_scope", cam, build_configuration(input_trigger_port=3))

    assert cam.set_calls[0] == ("gpi_selector", "XI_GPI_PORT3")


def test_sensor_mode_exposure_line_interval_and_binning_branches(ximea_camera):
    camera, cam = ximea_camera

    camera.set_sensor_mode("Normal")
    assert ("acq_timing_mode", "XI_ACQ_TIMING_MODE_FREE_RUN") in cam.set_calls
    assert ("shutter_type", "XI_SHUTTER_ROLLING") in cam.set_calls

    assert camera.set_exposure_time(0.005) is True
    assert cam.params["exposure"] == 5000.0

    assert camera.set_line_interval(0.001) is False

    assert camera.set_binning("11x11") is False
    assert camera.set_binning("4x4") is True
    assert ("downsampling_type", "XI_BINNING") in cam.set_calls
    assert ("downsampling", "XI_DWN_4x4") in cam.set_calls


def test_set_roi_rejects_invalid_geometry(ximea_camera):
    camera, _ = ximea_camera

    assert camera.set_ROI(roi_width=3000, roi_height=3000, center_x=200, center_y=200) is False


def test_set_roi_returns_false_on_sdk_error(ximea_camera):
    camera, cam = ximea_camera
    cam.fail_on_set.add("width")

    assert camera.set_ROI(roi_width=400, roi_height=200, center_x=1024, center_y=1024) is False


def test_set_roi_success_updates_dimensions(ximea_camera):
    camera, cam = ximea_camera

    assert camera.set_ROI(roi_width=400, roi_height=200, center_x=1024, center_y=1024)
    assert cam.params["width"] == 400
    assert cam.params["height"] == 200
    assert cam.params["offsetX"] == 824
    assert cam.params["offsetY"] == 920
    assert camera.x_pixels == 400
    assert camera.y_pixels == 200


def test_initialize_get_new_frame_wraparound_and_close(ximea_camera):
    camera, cam = ximea_camera
    data_buffer = [np.zeros((2, 2), dtype=np.uint16) for _ in range(2)]

    camera.initialize_image_series(data_buffer, number_of_frames=2)
    assert camera.is_acquiring is True
    assert cam.start_calls == 1
    assert camera._number_of_frames == 2

    assert camera.get_new_frame() == [0]
    assert camera.get_new_frame() == [1]
    assert camera.get_new_frame() == [0]

    camera.close_image_series()
    assert camera.is_acquiring is False
    assert cam.stop_calls == 1


def test_get_new_frame_error_path_returns_empty(ximea_camera):
    camera, cam = ximea_camera
    data_buffer = [np.zeros((2, 2), dtype=np.uint16)]
    camera.initialize_image_series(data_buffer, number_of_frames=1)
    cam.get_image_exception = camera.cam.xi_error_cls("acquisition failure")

    assert camera.get_new_frame() == []


def test_serial_number_property_current_behavior(ximea_camera):
    camera, cam = ximea_camera

    assert camera.serial_number is None
    assert "device_sn" in cam.get_param_calls


def test_mu196xr_overrides_trigger_port(ximea_module):
    cam = FakeXiCam(ximea_module.xiapi.Xi_error)
    camera = ximea_module.MU196XRCamera("test_scope", cam, build_configuration())

    assert str(camera) == "Ximea MU196XR Camera"
    assert cam.set_calls[-2] == ("gpi_selector", "XI_GPI_PORT2")
    assert cam.set_calls[-1] == ("gpi_mode", "XI_GPI_TRIGGER")
