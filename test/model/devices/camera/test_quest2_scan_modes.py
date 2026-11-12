"""Quest 2 firmware reports a raw scan preference even in fixed Light-Sheet mode."""

import sys

import pytest

from test.model.devices.camera import test_hamamatsu_bit_depth as depth_tests
from test.model.devices.camera import test_scan_correction as scan_tests
from test.controller.sub_controllers import test_scan_correction_popup as popup_tests
from test.model import test_camera_advanced_settings as model_tests
from navigate.model.microscope import Microscope

camera = depth_tests.camera
scan_camera = scan_tests.scan_camera
popup = popup_tests.popup
transaction_model = model_tests.model


@pytest.fixture
def quest(scan_camera):
    module = sys.modules["navigate.model.devices.camera.hamamatsu"]
    scan_camera.__class__ = module.HamamatsuOrcaQuest2Camera
    sdk = scan_camera.camera_controller
    sdk.values["sensor_mode"] = 1.0
    sdk.options["sensor_mode"] = (1.0, 12.0, 18.0)
    sdk.get_property_value_text = lambda *args: None
    return scan_camera


def test_quest_area_scan_fallback_labels_are_model_specific(quest):
    cap = quest.get_advanced_setting_capabilities()["scan_speed"]
    assert cap.current_value == 1 and cap.writable
    assert cap.value_labels == ((1, "Ultra quiet"), (2, "Standard"))
    quest.__class__ = sys.modules[
        "navigate.model.devices.camera.hamamatsu"
    ].HamamatsuOrcaCamera
    assert quest.get_advanced_setting_capabilities()["scan_speed"].value_labels == (
        (1, "1"),
        (2, "2"),
    )
    assert quest.camera_controller.writes == []


def test_quest_scan_preserves_real_sdk_labels(quest):
    quest.camera_controller.get_property_value_text = (
        lambda name, value: "Vendor quiet" if value == 1 else "Vendor standard"
    )
    assert quest.get_advanced_setting_capabilities()["scan_speed"].value_labels == (
        (1, "Vendor quiet"),
        (2, "Vendor standard"),
    )


@pytest.mark.parametrize("raw", [1, 2])
def test_lightsheet_reports_fixed_effective_standard_without_sdk_writes(quest, raw):
    sdk = quest.camera_controller
    sdk.values.update(sensor_mode=12.0, readout_speed=float(raw))
    cap = quest.get_advanced_setting_capabilities()["scan_speed"]
    assert quest.get_advanced_setting("scan_speed") == cap.current_value == 2
    assert cap.choices == (2,) and not cap.writable
    assert cap.value_labels == ((2, "Standard"),)
    assert "Light-Sheet" in cap.reason
    with pytest.raises(ValueError):
        quest.set_advanced_setting("scan_speed", 1)
    assert quest.set_advanced_setting("scan_speed", 2) == 2
    assert sdk.values["readout_speed"] == raw and sdk.writes == []
    sdk.values["sensor_mode"] = 1
    assert quest.get_advanced_setting_capabilities()["scan_speed"].current_value == raw


@pytest.mark.parametrize(
    "mode,raw,choices",
    [
        (False, 1, (1, 2)),
        (18, 1, (1, 2)),
        (12, False, (1, 2)),
        (12, 1, None),
        (12, 1, (1, False)),
        (12, 1, (1,)),
    ],
)
def test_unconfirmed_quest_scan_does_not_invent_effective_standard(
    quest, mode, raw, choices
):
    sdk = quest.camera_controller
    sdk.values.update(sensor_mode=mode, readout_speed=raw)
    sdk.options["readout_speed"] = choices
    cap = quest.get_advanced_setting_capabilities()["scan_speed"]
    assert not cap.writable and cap.reason
    if mode in (False, 18) or raw is False:
        assert cap.current_value is None
    assert sdk.writes == []


def test_lightsheet_busy_and_failed_restoration_keep_controls_disabled(quest):
    quest.camera_controller.values["sensor_mode"] = 12
    quest.is_acquiring = True
    cap = quest.get_advanced_setting_capabilities()["scan_speed"]
    assert not cap.writable and "Stop" in cap.reason
    quest.is_acquiring = False
    quest.camera_controller._advanced_settings_error = "restoration failed"
    cap = quest.get_advanced_setting_capabilities()["scan_speed"]
    assert not cap.writable and cap.current_value is None
    assert "restoration" in cap.reason


def test_named_mode_change_persists_effective_scan_and_preserves_raw_preference(
    quest, transaction_model
):
    model = transaction_model
    model.active_microscope.camera = quest
    parameters = model.configuration["experiment"]["CameraParameters"]["scope"]
    parameters["scan_speed"] = 1
    for mode, effective in [(12, 2), (1, 1)]:
        result = model.camera_advanced_settings(
            dict(
                microscope="scope",
                request_id=mode,
                identity=(id(quest.camera_controller),),
                setting="sensor_mode",
                value=mode,
            )
        )
        assert result["error"] is None
        assert result["capabilities"]["scan_speed"].current_value == effective
        assert parameters["scan_speed"] == effective
        assert quest.camera_controller.values["readout_speed"] == 1


def test_saved_raw_lightsheet_scan_is_normalized_and_metadata_is_effective(quest):
    microscope = Microscope.__new__(Microscope)
    microscope.microscope_name = "scope"
    microscope.camera = quest
    parameters = {"scan_speed": 1}
    microscope.configuration = {
        "experiment": {"CameraParameters": {"scope": parameters}}
    }
    microscope.set_camera_trigger_mode = lambda: None
    microscope.set_camera_sensor_mode = lambda: quest.set_sensor_mode("Light-Sheet")
    microscope.set_camera_roi_and_binning = lambda: True
    microscope.configure_camera()
    assert parameters["scan_speed"] == 2
    assert microscope._camera_settings_metadata["scan_speed"] == 2
    assert quest.camera_controller.values["readout_speed"] == 1


def test_invalid_nonfixed_saved_scan_is_still_rejected(quest):
    microscope = Microscope.__new__(Microscope)
    microscope.microscope_name = "scope"
    microscope.camera = quest
    parameters = {"scan_speed": 99}
    microscope.configuration = {
        "experiment": {"CameraParameters": {"scope": parameters}}
    }
    microscope.set_camera_trigger_mode = lambda: None
    microscope.set_camera_sensor_mode = lambda: None
    microscope.set_camera_roi_and_binning = lambda: True
    with pytest.raises(ValueError):
        microscope.configure_camera()
    assert parameters["scan_speed"] == 99


def test_real_popup_displays_named_area_and_disabled_lightsheet_scan(quest, popup):
    result = popup_tests.response(popup)
    result["capabilities"] = quest.get_advanced_setting_capabilities()
    popup._receive_bit_depth(result)
    assert popup.view.inputs["scan_speed"].get() == "Ultra quiet"
    assert str(popup.view.inputs["scan_speed"]["state"]) == "readonly"
    quest.camera_controller.values["sensor_mode"] = 12
    popup.camera_setting_dict["sensor_mode"] = "Light-Sheet"
    result["capabilities"] = quest.get_advanced_setting_capabilities()
    popup._receive_bit_depth(result)
    assert popup.view.inputs["scan_speed"].get() == "Standard"
    assert str(popup.view.inputs["scan_speed"]["state"]) == "disabled"
    popup.set_advanced_setting("scan_speed")
    popup.parent_controller.execute.assert_not_called()
