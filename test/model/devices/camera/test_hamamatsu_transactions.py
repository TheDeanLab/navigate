"""Coupled ROI and mode transaction regressions without a physical SDK."""

import sys

import pytest

from navigate.model.microscope import Microscope
from test.model.devices.camera import test_hamamatsu_bit_depth as depth_tests
from test.model.devices.camera import test_scan_correction as scan_tests

camera = depth_tests.camera
scan_camera = scan_tests.scan_camera


@pytest.fixture
def roi_camera(scan_camera):
    sdk = scan_camera.camera_controller
    sdk.values.update(
        sensor_mode=1.0,
        binning=1.0,
        subarray_hsize=2044.0,
        subarray_vsize=2044.0,
        subarray_hpos=4.0,
        subarray_vpos=4.0,
        subarray_mode=2.0,
    )
    sdk.options["sensor_mode"] = (1.0, 12.0)
    original = sdk.set_property_value

    def constrained_set(name, value):
        if name in ("subarray_hsize", "subarray_vsize"):
            offset = "subarray_hpos" if name == "subarray_hsize" else "subarray_vpos"
            if sdk.values["subarray_mode"] == 2 and value + sdk.values[offset] > 2048:
                return False
        return original(name, value)

    sdk.set_property_value = constrained_set
    return scan_camera


@pytest.mark.parametrize("mode", [1, 2])
def test_rollback_restores_offset_roi_and_exact_subarray_mode(roi_camera, mode):
    sdk = roi_camera.camera_controller
    sdk.values["subarray_mode"] = mode
    previous = roi_camera.snapshot_advanced_settings("sensor_mode")
    old = dict(sdk.values)
    sdk.values.update(
        subarray_hsize=2040.0,
        subarray_vsize=2040.0,
        subarray_hpos=8.0,
        subarray_vpos=8.0,
        subarray_mode=2.0,
    )
    roi_camera.restore_advanced_settings(previous)
    assert sdk.values == old
    assert roi_camera._setting_error() is None


def test_rollback_does_not_normalize_unchanged_roi(roi_camera):
    sdk = roi_camera.camera_controller
    previous = roi_camera.snapshot_advanced_settings("sensor_mode")
    roi_camera.restore_advanced_settings(previous)
    assert sdk.writes == []


def test_rollback_does_not_write_unsupported_roi_properties(scan_camera):
    sdk = scan_camera.camera_controller
    sdk.values["subarray_hsize"] = 1024.0
    previous = scan_camera.snapshot_advanced_settings()
    sdk.values["subarray_hsize"] = 512.0
    scan_camera.restore_advanced_settings(previous)
    assert sdk.values["subarray_hsize"] == 1024
    assert sdk.writes == [("subarray_hsize", 1024.0)]


def test_roi_normalization_failure_blocks_shared_connection(roi_camera):
    sdk = roi_camera.camera_controller
    previous = roi_camera.snapshot_advanced_settings("sensor_mode")
    sdk.values.update(subarray_hsize=2040.0, subarray_hpos=8.0)
    sdk.reject = ("subarray_mode", 1)
    with pytest.raises(RuntimeError, match="restoration"):
        roi_camera.restore_advanced_settings(previous)
    alias = object.__new__(type(roi_camera))
    alias.camera_controller = sdk
    alias.is_acquiring = False
    with pytest.raises(RuntimeError, match="restoration"):
        alias.set_advanced_setting("scan_speed", 1)


@pytest.mark.parametrize(
    "setting,prop,value",
    [
        ("scan_speed", "readout_speed", 1),
        ("defect_correction", "defect_correct_mode", 2),
        ("hot_pixel_correction", "hot_pixel_correct_level", 1),
    ],
)
def test_saved_unchanged_readonly_multichoice_allows_configuration(
    scan_camera, setting, prop, value
):
    sdk = scan_camera.camera_controller
    sdk.is_property_writable = lambda name: name in sdk.values and name != prop
    microscope = Microscope.__new__(Microscope)
    microscope.microscope_name = "scope"
    microscope.camera = scan_camera
    microscope.configuration = {
        "experiment": {"CameraParameters": {"scope": {setting: value}}}
    }
    microscope.set_camera_trigger_mode = lambda: None
    microscope.set_camera_sensor_mode = lambda: None
    microscope.set_camera_roi_and_binning = lambda: True
    microscope.configure_camera()
    assert sdk.writes == []
    assert microscope._camera_settings_metadata[setting] == value


@pytest.mark.parametrize("guard", ["busy", "error", "choices", "different"])
def test_readonly_noop_preserves_safety_guards(scan_camera, guard):
    sdk = scan_camera.camera_controller
    sdk.is_property_writable = lambda name: name != "defect_correct_mode"
    value = 2
    if guard == "busy":
        scan_camera.is_acquiring = True
    elif guard == "error":
        sdk._advanced_settings_error = "restoration failed"
    elif guard == "choices":
        sdk.options["defect_correct_mode"] = None
    else:
        value = 1
    with pytest.raises((ValueError, RuntimeError)):
        scan_camera.set_advanced_setting("defect_correction", value)
    assert sdk.writes == []


@pytest.fixture
def binned_quest(roi_camera):
    roi_camera.__class__ = sys.modules[
        "navigate.model.devices.camera.hamamatsu"
    ].HamamatsuOrcaQuest2Camera
    sdk = roi_camera.camera_controller
    sdk.values["binning"] = 2.0
    original = sdk.set_property_value

    def constrained_set(name, value):
        if name == "sensor_mode" and value == 12 and sdk.values["binning"] != 1:
            return False
        return original(name, value)

    sdk.set_property_value = constrained_set
    return roi_camera


def test_named_quest_mode_resets_binning_before_lightsheet(binned_quest):
    sdk = binned_quest.camera_controller
    assert binned_quest.set_advanced_setting("sensor_mode", 12) == 12
    assert sdk.values["binning"] == 1
    assert sdk.values["sensor_mode"] == 12


def test_legacy_quest_mode_retains_binning_prerequisite(binned_quest):
    sdk = binned_quest.camera_controller
    binned_quest.set_sensor_mode("Light-Sheet")
    assert sdk.values["binning"] == 1
    assert sdk.values["sensor_mode"] == 12


@pytest.mark.parametrize("failure", ["binning", "sensor_mode", "timing"])
def test_quest_prerequisite_failure_restores_original_binning_and_roi(
    binned_quest, failure
):
    sdk = binned_quest.camera_controller
    old = dict(sdk.values)
    original_set = sdk.set_property_value
    original_get = sdk.get_property_value
    attempts = []

    def write(name, value):
        attempts.append((name, value))
        result = original_set(name, value)
        if name == "binning" and value == 1:
            sdk.values.update(subarray_hsize=2040.0, subarray_hpos=8.0)
        if name == failure and value == (1 if failure == "binning" else 12):
            return False
        return result

    sdk.set_property_value = write
    sdk.get_property_value = lambda name: (
        False
        if failure == "timing"
        and name == "readout_time"
        and sdk.values["sensor_mode"] == 12
        else original_get(name)
    )
    with pytest.raises(RuntimeError, match="restored"):
        binned_quest.set_advanced_setting("sensor_mode", 12)
    assert ("binning", 1) in attempts
    if failure == "binning":
        assert ("sensor_mode", 12) not in attempts
    assert sdk.values == old
    assert binned_quest._setting_error() is None


def test_roi_mode_is_restored_before_dependent_exposure(roi_camera):
    sdk = roi_camera.camera_controller
    previous = roi_camera.snapshot_advanced_settings("sensor_mode")
    old = dict(sdk.values)
    sdk.values.update(subarray_hsize=2040.0, subarray_hpos=8.0)
    original = sdk.set_property_value

    def write(name, value):
        result = original(name, value)
        if name == "subarray_mode":
            sdk.values["exposure_time"] = 0.02
        return result

    sdk.set_property_value = write
    roi_camera.restore_advanced_settings(previous)
    assert sdk.values == old
    assert roi_camera._setting_error() is None


@pytest.mark.parametrize(
    "prop,value", [("subarray_mode", 1), ("subarray_hpos", 0), ("subarray_vpos", 0)]
)
def test_roi_normalization_does_not_write_already_neutral_property(
    roi_camera, prop, value
):
    sdk = roi_camera.camera_controller
    sdk.values.update(subarray_mode=1, subarray_hpos=0, subarray_vpos=0)
    previous = roi_camera.snapshot_advanced_settings("sensor_mode")
    old = dict(sdk.values)
    sdk.values["subarray_hsize"] = 2040
    # A supported neutral property can be read-only in the current mode.
    sdk.reject = (prop, value)
    roi_camera.restore_advanced_settings(previous)
    assert sdk.values == old
    assert (prop, value) not in sdk.writes
