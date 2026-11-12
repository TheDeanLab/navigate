"""Scan/correction discovery and transactions without opening a camera."""

import pytest

from test.model import test_camera_advanced_settings as model_tests
from test.model.devices.camera import test_hamamatsu_bit_depth as hamamatsu_tests
from test.model.devices.camera import test_synthetic_bit_depth as synthetic_tests

transaction_model = model_tests.model
camera = hamamatsu_tests.camera
synthetic_camera = synthetic_tests.camera


@pytest.fixture
def scan_camera(camera):
    sdk = camera.camera_controller
    sdk.is_property_writable = lambda name: name in sdk.values
    sdk.values.update(
        defect_correct_mode=2.0, hot_pixel_correct_level=1.0, readout_time=0.01
    )
    original = sdk.get_property_values
    sdk.options = {
        "readout_speed": (1.0, 2.0),
        "defect_correct_mode": (1.0, 2.0),
        "hot_pixel_correct_level": (1.0, 2.0, 3.0),
    }
    sdk.get_property_values = lambda name: sdk.options.get(name, original(name))
    sdk.get_property_value_text = lambda name, value: {
        ("readout_speed", 1): "Ultra quiet",
        ("readout_speed", 2): "Standard",
        ("hot_pixel_correct_level", 1): "STANDARD",
    }.get((name, value))
    return camera


def test_discovery_uses_complete_sdk_choices_and_text_without_writes(scan_camera):
    capabilities = scan_camera.get_advanced_setting_capabilities()
    scan = capabilities["scan_speed"]
    assert scan.current_value == 1
    assert scan.choices == (1, 2)
    assert scan.value_labels == ((1, "Ultra quiet"), (2, "Standard"))
    assert scan.writable
    assert capabilities["hot_pixel_correction"].choices == (1, 2, 3)
    assert dict(capabilities["hot_pixel_correction"].value_labels)[3] == "3"
    assert scan_camera.camera_controller.writes == []


@pytest.mark.parametrize(
    "current,choices",
    [(False, (0, 1)), (1, None), (1, (1,)), (1, (1, False)), (1, (1, 2.5))],
)
def test_unreliable_and_fixed_settings_cannot_write(scan_camera, current, choices):
    sdk = scan_camera.camera_controller
    sdk.values["readout_speed"] = current
    sdk.options["readout_speed"] = choices
    assert not scan_camera.get_advanced_setting_capabilities()["scan_speed"].writable
    with pytest.raises((ValueError, RuntimeError)):
        scan_camera.set_advanced_setting("scan_speed", 2)
    assert sdk.writes == []


def test_scan_refreshes_timing_precision_and_dependent_choices(scan_camera):
    sdk = scan_camera.camera_controller
    original = sdk.set_property_value

    def change(name, value):
        result = original(name, value)
        if name == "readout_speed":
            sdk.values.update(
                bits_per_channel=12.0, exposure_time=0.02, internal_line_interval=2e-5
            )
            sdk.options["hot_pixel_correct_level"] = (1.0,)
        return result

    sdk.set_property_value = change
    assert scan_camera.set_advanced_setting("scan_speed", 2) == 2
    assert scan_camera.get_image_format().bit_depth == 12
    assert scan_camera.camera_parameters["line_interval"] == 2e-5
    assert not scan_camera.get_advanced_setting_capabilities()[
        "hot_pixel_correction"
    ].writable


@pytest.mark.parametrize("reject", [True, False])
def test_scan_rejection_or_clamp_restores_all_dependencies(scan_camera, reject):
    sdk = scan_camera.camera_controller
    previous = dict(sdk.values)
    original = sdk.set_property_value

    def change(name, value):
        if name == "readout_speed" and value == 2:
            sdk.values.update(
                exposure_time=0.02, bits_per_channel=12.0, defect_correct_mode=1.0
            )
            return not reject
        return original(name, value)

    sdk.set_property_value = change
    with pytest.raises(RuntimeError):
        scan_camera.set_advanced_setting("scan_speed", 2)
    assert sdk.values == previous


def test_failed_restoration_blocks_another_adapter_for_same_camera(scan_camera):
    sdk = scan_camera.camera_controller
    original = sdk.set_property_value

    def change(name, value):
        if name == "readout_speed" and value == 2:
            sdk.values["exposure_time"] = 0.02
            return False
        if name == "exposure_time":
            return False
        return original(name, value)

    sdk.set_property_value = change
    with pytest.raises(RuntimeError, match="restoration"):
        scan_camera.set_advanced_setting("scan_speed", 2)
    alias = object.__new__(type(scan_camera))
    alias.camera_controller = sdk
    alias.is_acquiring = False
    alias.camera_parameters = {}
    assert not alias.get_advanced_setting_capabilities()["scan_speed"].writable
    with pytest.raises(RuntimeError):
        alias.set_bit_depth(8)


def test_busy_and_mode_constrained_scan_are_disabled(scan_camera):
    scan_camera.is_acquiring = True
    with pytest.raises(RuntimeError):
        scan_camera.set_advanced_setting("defect_correction", 1)
    scan_camera.is_acquiring = False
    scan_camera.camera_controller.options["readout_speed"] = (1.0,)
    assert not scan_camera.get_advanced_setting_capabilities()["scan_speed"].writable


def test_synthetic_settings_preserve_native_dtype_and_lock_while_acquiring(
    synthetic_camera,
):
    camera = synthetic_camera
    camera.set_bit_depth(8)
    for name, value in (
        ("scan_speed", 2),
        ("defect_correction", 1),
        ("hot_pixel_correction", 3),
    ):
        assert camera.set_advanced_setting(name, value) == value
        assert camera.get_advanced_setting(name) == value
    assert camera.get_image_format().dtype == "uint8"
    camera.is_acquiring = True
    with pytest.raises(RuntimeError):
        camera.set_advanced_setting("scan_speed", 1)


@pytest.mark.parametrize("fail", [False, True])
def test_explicit_sensor_apply_refreshes_scan_choices_and_restores_failed_mode(
    scan_camera, fail
):
    sdk = scan_camera.camera_controller
    sdk.values.update(sensor_mode=1.0, binning=1.0)
    sdk.options["sensor_mode"] = (1.0, 12.0)
    original = sdk.set_property_value

    def change(name, value):
        result = original(name, value)
        if name == "sensor_mode":
            sdk.options["readout_speed"] = (2.0,) if value == 12 else (1.0, 2.0)
            sdk.values["readout_speed"] = 2.0 if value == 12 else 1.0
            if fail and value == 12:
                return False
        return result

    sdk.set_property_value = change
    if fail:
        with pytest.raises(RuntimeError):
            scan_camera.set_advanced_setting("sensor_mode", 12)
        assert sdk.values["sensor_mode"] == 1
        assert sdk.values["readout_speed"] == 1
    else:
        assert scan_camera.set_advanced_setting("sensor_mode", 12) == 12
        capability = scan_camera.get_advanced_setting_capabilities()["scan_speed"]
        assert capability.current_value == 2
        assert capability.choices == (2,)
        assert not capability.writable


def test_failed_restoration_prevents_prepare_mode_writes_on_alias(scan_camera):
    sdk = scan_camera.camera_controller
    sdk._advanced_settings_error = "Camera restoration failed"
    with pytest.raises(RuntimeError, match="restoration"):
        scan_camera.set_sensor_mode("Normal")
    with pytest.raises(RuntimeError, match="restoration"):
        scan_camera.set_trigger_mode("Internal")
    assert sdk.writes == []


def test_zero_snapshot_cannot_be_confirmed_by_sdk_false(scan_camera):
    sdk = scan_camera.camera_controller
    sdk.values["internal_line_interval"] = 0.0
    previous = scan_camera.snapshot_advanced_settings()
    original = sdk.get_property_value
    sdk.get_property_value = (
        lambda name: False if name == "internal_line_interval" else original(name)
    )
    with pytest.raises(RuntimeError, match="restoration"):
        scan_camera.restore_advanced_settings(previous)


def test_saved_scan_prevents_fastest_initialization(scan_camera):
    sdk = scan_camera.camera_controller
    sdk.max_image_width, sdk.max_image_height = 3, 2
    sdk.min_image_width = sdk.min_image_height = 1
    sdk.step_image_width = sdk.step_image_height = 1
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
        "experiment": {"CameraParameters": {"scope": {"scan_speed": 1}}},
    }
    instance = type(scan_camera)("scope", sdk, configuration)
    assert not any(name == "readout_speed" for name, value in sdk.writes)
    assert instance.get_advanced_setting("scan_speed") == 1


def test_photon_number_mode_is_not_exposed(scan_camera):
    sdk = scan_camera.camera_controller
    sdk.values["sensor_mode"] = 1.0
    sdk.options["sensor_mode"] = (1.0, 3.0, 12.0)
    assert scan_camera.get_advanced_setting_capabilities()["sensor_mode"].choices == (
        1,
        12,
    )
    with pytest.raises(ValueError):
        scan_camera.set_advanced_setting("sensor_mode", 3)
    assert not sdk.writes


def test_synthetic_mode_change_refreshes_fixed_scan_choice(synthetic_camera):
    camera = synthetic_camera
    camera.set_advanced_setting("sensor_mode", 12)
    scan = camera.get_advanced_setting_capabilities()["scan_speed"]
    assert scan.current_value == 2
    assert scan.choices == (2,)
    assert not scan.writable
    with pytest.raises(ValueError):
        camera.set_advanced_setting("scan_speed", 1)


def test_explicit_sensor_mode_refreshes_roi_limits(scan_camera):
    sdk = scan_camera.camera_controller
    sdk.values["sensor_mode"] = 1.0
    sdk.options["sensor_mode"] = (1.0, 12.0)
    original = sdk.get_property_range
    sdk.get_property_range = (
        lambda name: (8, 2048, 8)
        if name in ("subarray_hsize", "subarray_vsize")
        else original(name)
    )
    scan_camera.set_advanced_setting("sensor_mode", 12)
    assert scan_camera.camera_parameters["x_pixels_min"] == 8
    assert scan_camera.camera_parameters["y_pixels_step"] == 8


def test_unknown_writable_dependency_prevents_sensor_mode_write(scan_camera):
    sdk = scan_camera.camera_controller
    sdk.values.update(sensor_mode=1.0, subarray_hsize=False)
    sdk.options["sensor_mode"] = (1.0, 12.0)
    with pytest.raises(RuntimeError, match="snapshot"):
        scan_camera.set_advanced_setting("sensor_mode", 12)
    assert sdk.writes == []


def test_unknown_native_layout_disables_settings_before_any_write(scan_camera):
    sdk = scan_camera.camera_controller

    def invalid_layout():
        raise ValueError("Unsupported layout")

    sdk.get_frame_layout = invalid_layout
    assert not scan_camera.get_advanced_setting_capabilities()["scan_speed"].writable
    with pytest.raises((ValueError, RuntimeError)):
        scan_camera.set_advanced_setting("scan_speed", 2)
    assert sdk.writes == []


def test_stale_request_does_not_trigger_legacy_precision_probe(
    scan_camera, transaction_model
):
    sdk = scan_camera.camera_controller
    sdk.values.update(bits_per_channel=8.0, image_pixel_type=1.0)
    transaction_model.active_microscope.camera = scan_camera
    result = transaction_model.camera_advanced_settings(
        {
            "microscope": "scope",
            "request_id": 1,
            "identity": (0,),
            "setting": "scan_speed",
            "value": 2,
        }
    )
    assert result["error"]
    assert sdk.writes == []


@pytest.mark.parametrize(
    "property_name",
    ["readout_time", "internal_line_interval", "minimum_trigger_interval"],
)
def test_scan_failed_supported_timing_refresh_rolls_back(scan_camera, property_name):
    sdk = scan_camera.camera_controller
    original = sdk.get_property_value
    sdk.get_property_value = (
        lambda name: False
        if name == property_name and sdk.values["readout_speed"] == 2
        else original(name)
    )
    with pytest.raises(RuntimeError, match="timing"):
        scan_camera.set_advanced_setting("scan_speed", 2)
    assert sdk.values["readout_speed"] == 1
    assert scan_camera.readout_time == 0.01
    assert scan_camera.camera_parameters["line_interval"] == 1e-5
    assert scan_camera.minimum_frame_interval == 0.01
    assert scan_camera._setting_error() is None


@pytest.mark.parametrize(
    "limits",
    [
        (None, 1, 1e-6),
        (1e-6, float("nan"), 1e-6),
        (1e-6, 1, float("nan")),
        (1e-6, 1, -1),
    ],
)
def test_scan_invalid_exposure_limits_roll_back(scan_camera, limits):
    sdk = scan_camera.camera_controller
    original = sdk.get_property_range
    sdk.get_property_range = (
        lambda name: limits
        if name == "exposure_time" and sdk.values["readout_speed"] == 2
        else original(name)
    )
    with pytest.raises(RuntimeError):
        scan_camera.set_advanced_setting("scan_speed", 2)
    assert sdk.values["readout_speed"] == 1
    assert scan_camera.minimum_exposure_time == 1e-6
    assert scan_camera.maximum_exposure_time == 10
    assert scan_camera.exposure_time_step == 1e-6


def test_scan_allows_genuinely_unsupported_optional_timing(scan_camera):
    sdk = scan_camera.camera_controller
    for name in ("internal_line_interval", "minimum_trigger_interval"):
        sdk.values.pop(name)
    original = sdk.get_property_range
    sdk.get_property_range = (
        lambda name: (None, None, None)
        if name in ("internal_line_interval", "minimum_trigger_interval")
        else original(name)
    )
    assert scan_camera.set_advanced_setting("scan_speed", 2) == 2
    assert scan_camera.readout_time == 0.01


def test_named_setting_rejects_unknown_required_timing_before_write(scan_camera):
    sdk = scan_camera.camera_controller
    sdk.values["readout_time"] = False
    with pytest.raises(RuntimeError, match="timing"):
        scan_camera.set_advanced_setting("scan_speed", 2)
    assert sdk.writes == []


def test_failed_scan_timing_never_persists_success_to_model(
    scan_camera, transaction_model
):
    sdk = scan_camera.camera_controller
    original = sdk.get_property_value
    sdk.get_property_value = (
        lambda name: False
        if name == "readout_time" and sdk.values["readout_speed"] == 2
        else original(name)
    )
    transaction_model.active_microscope.camera = scan_camera
    parameters = transaction_model.configuration["experiment"]["CameraParameters"][
        "scope"
    ]
    parameters.update(scan_speed=1, readout_time=10)
    result = transaction_model.camera_advanced_settings(
        {
            "microscope": "scope",
            "request_id": 1,
            "identity": (id(sdk),),
            "setting": "scan_speed",
            "value": 2,
        }
    )
    assert "timing" in result["error"]
    assert parameters["scan_speed"] == 1
    assert parameters["readout_time"] == 10
    assert result["data_buffer"] is None


def test_model_rechecks_timing_after_legacy_mono8_capability_probe(
    scan_camera, transaction_model
):
    sdk = scan_camera.camera_controller
    sdk.values.update(bits_per_channel=8.0, image_pixel_type=1.0)
    state = {"probe_after_scan": False}
    original_write, original_read = sdk.set_property_value, sdk.get_property_value

    def write(name, value):
        result = original_write(name, value)
        if (
            name == "image_pixel_type"
            and value == 2
            and sdk.values["readout_speed"] == 2
        ):
            state["probe_after_scan"] = True
        return result

    def read(name):
        if (
            name == "readout_time"
            and sdk.values["readout_speed"] == 2
            and state["probe_after_scan"]
        ):
            return False
        return original_read(name)

    sdk.set_property_value, sdk.get_property_value = write, read
    transaction_model.active_microscope.camera = scan_camera
    result = transaction_model.camera_advanced_settings(
        {
            "microscope": "scope",
            "request_id": 1,
            "identity": (id(sdk),),
            "setting": "scan_speed",
            "value": 2,
        }
    )
    assert result["error"] and "timing" in result["error"]
    assert sdk.values["readout_speed"] == 1
    assert (
        "scan_speed"
        not in transaction_model.configuration["experiment"]["CameraParameters"][
            "scope"
        ]
    )
