"""Confirmed settings survive startup and never persist rejected UI requests."""

from types import MethodType, SimpleNamespace
from unittest.mock import Mock
import pytest

from test.model import test_camera_advanced_settings as model_tests
from test.model.devices.camera import test_synthetic_bit_depth as synthetic_tests

from navigate.model.microscope import Microscope

model = model_tests.model
request = model_tests.request
camera = synthetic_tests.camera


@pytest.fixture
def configured_model(model, camera):
    model.active_microscope.camera = camera
    return model


def test_new_request_persists_confirmed_value_and_returns_all_capabilities(
    configured_model,
):
    m = configured_model
    result = request(m, identity=request(m)["identity"], setting="scan_speed", value=2)
    assert result["error"] is None
    assert result["capabilities"]["scan_speed"].current_value == 2
    assert result["capability"].current_value == 16
    assert m.configuration["experiment"]["CameraParameters"]["scope"]["scan_speed"] == 2
    assert result["data_buffer"][0].dtype.name == "uint16"


@pytest.mark.parametrize("failure", ["busy", "stale", "bool", "unknown"])
def test_rejected_new_request_has_no_writes(configured_model, failure):
    m = configured_model
    values = dict(identity=request(m)["identity"], setting="scan_speed", value=2)
    if failure == "busy":
        m.is_acquiring = True
    elif failure == "stale":
        values["identity"] = (0,)
    elif failure == "bool":
        values["value"] = True
    else:
        values["setting"] = "other"
    result = request(m, **values)
    assert result["error"]
    assert m.active_microscope.camera.get_advanced_setting("scan_speed") == 1
    assert (
        "scan_speed" not in m.configuration["experiment"]["CameraParameters"]["scope"]
    )


def test_failed_allocation_restores_settings_and_failed_rollback_blocks_alias(
    configured_model,
):
    m = configured_model
    identity = request(m)["identity"]
    m.get_data_buffer = Mock(side_effect=MemoryError("no room"))
    assert request(m, identity=identity, setting="scan_speed", value=2)["error"]
    assert m.active_microscope.camera.get_advanced_setting("scan_speed") == 1
    m.active_microscope.camera.restore_advanced_settings = Mock(
        side_effect=RuntimeError("failed")
    )
    assert request(m, identity=identity, setting="scan_speed", value=2)["error"]
    m.microscopes["alias"] = SimpleNamespace(camera=m.active_microscope.camera)
    result = m.camera_advanced_settings(
        dict(
            microscope="alias",
            request_id=2,
            identity=identity,
            setting="defect_correction",
            value=1,
        )
    )
    assert result["error"]
    assert not result["capabilities"]["scan_speed"].writable
    with pytest.raises(RuntimeError):
        m.prepare_camera_buffers("scope")


def test_saved_scan_restored_before_depth_and_corrections_with_actual_metadata(
    configured_model,
):
    m = configured_model
    microscope = m.active_microscope
    microscope.configuration = m.configuration
    microscope.microscope_name = "scope"
    microscope.set_camera_trigger_mode = lambda: None
    microscope.set_camera_sensor_mode = lambda: None
    microscope.set_camera_roi_and_binning = (
        lambda: microscope.camera.get_advanced_setting("scan_speed") == 2
    )
    microscope.configure_camera = MethodType(Microscope.configure_camera, microscope)
    parameters = m.configuration["experiment"]["CameraParameters"]["scope"]
    parameters.update(
        scan_speed=2, bit_depth=8, defect_correction=1, hot_pixel_correction=3
    )
    frames = m.prepare_camera_buffers("scope")["data_buffer"]
    assert frames[0].dtype.name == "uint8"
    assert microscope.camera.get_advanced_setting("scan_speed") == 2
    assert m.get_camera_settings_metadata("scope") == {
        "scan_speed": 2,
        "defect_correction": 1,
        "hot_pixel_correction": 3,
    }
    parameters[
        "scan_speed"
    ] = 1  # unconfirmed UI request must never alter capture metadata
    assert m.get_camera_settings_metadata("scope")["scan_speed"] == 2


def test_scan_result_refreshes_confirmed_timing(configured_model):
    m = configured_model
    camera = m.active_microscope.camera
    camera.readout_time = 0.015
    camera.minimum_exposure_time = 0.0001
    camera.maximum_exposure_time = 2.0
    camera.exposure_time_step = 0.00001
    result = request(m, identity=request(m)["identity"], setting="scan_speed", value=2)
    assert result["timing"] == {
        "readout_time": 0.015,
        "minimum_exposure_time": 0.0001,
        "maximum_exposure_time": 2.0,
        "exposure_time_step": 0.00001,
    }
    assert (
        m.configuration["experiment"]["CameraParameters"]["scope"]["readout_time"] == 15
    )


def test_ambiguous_legacy_and_named_write_is_rejected(configured_model):
    m = configured_model
    result = request(
        m, identity=request(m)["identity"], setting="scan_speed", value=2, bit_depth=8
    )
    assert result["error"]
    assert m.active_microscope.camera.get_advanced_setting("scan_speed") == 1
    assert m.active_microscope.camera.get_bit_depth() == 16


def test_sensor_apply_preserves_newer_mode_intent_during_camera_write(configured_model):
    m = configured_model
    parameters = m.configuration["experiment"]["CameraParameters"]["scope"]
    parameters["sensor_mode"] = "Light-Sheet"
    camera = m.active_microscope.camera
    original = camera.set_advanced_setting

    def apply(name, value):
        confirmed = original(name, value)
        parameters["sensor_mode"] = "Normal"  # a newer main-tab selection
        return confirmed

    camera.set_advanced_setting = apply
    result = request(
        m, identity=request(m)["identity"], setting="sensor_mode", value=12
    )
    assert result["error"] is None
    assert result["capabilities"]["sensor_mode"].current_value == 12
    assert parameters["sensor_mode"] == "Normal"
