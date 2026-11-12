"""Real controls display SDK labels and send only idle identity-tagged requests."""

from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from navigate.controller.sub_controllers.camera_settings import (
    AdvancedCameraSettingController,
)
from navigate.model.devices.camera.format import CameraSettingCapability
from navigate.view.popups.camera_setting_popup import AdvancedCameraSettingPopup


@pytest.fixture
def popup(tk_root):
    view = AdvancedCameraSettingPopup(tk_root)
    view.populate_view({"x": False, "y": False})
    c = AdvancedCameraSettingController.__new__(AdvancedCameraSettingController)
    c.view = view
    c.current_microscope = "scope"
    c.camera_setting_dict = {"sensor_mode": "Normal"}
    c.parent_controller = SimpleNamespace(
        execute=Mock(), acquire_bar_controller=SimpleNamespace(is_acquiring=False)
    )
    c._depth_request_id = 0
    c._depth_identity = None
    c._depth_pending = False
    c._depth_closed = False
    c._depth_close_requested = False
    c._depth_capability = CameraSettingCapability()
    yield c
    view.popup.destroy()


def response(c):
    depth = CameraSettingCapability(16, (8, 12, 16), True, reason="")
    return dict(
        microscope="scope",
        request_id=c._depth_request_id,
        identity=(1,),
        error=None,
        capability=depth,
        capabilities={
            "bit_depth": depth,
            "scan_speed": CameraSettingCapability(
                1,
                (1, 2),
                True,
                reason="",
                value_labels=((1, "Ultra quiet"), (2, "Standard")),
            ),
            "defect_correction": CameraSettingCapability(2, (1, 2), True, reason=""),
            "hot_pixel_correction": CameraSettingCapability(
                1, (1,), False, reason="Fixed in current mode"
            ),
            "sensor_mode": CameraSettingCapability(1, (1, 12), True, reason=""),
        },
    )


def test_real_controls_use_labels_and_lock_all_while_request_pending(popup):
    c = popup
    c._receive_bit_depth(response(c))
    assert c.view.inputs["scan_speed"].get() == "Ultra quiet"
    assert tuple(c.view.inputs["scan_speed"]["values"]) == ("Ultra quiet", "Standard")
    assert str(c.view.inputs["hot_pixel_correction"]["state"]) == "disabled"
    c.view.inputs["scan_speed"].set("Standard")
    c.set_advanced_setting("scan_speed")
    request = c.parent_controller.execute.call_args.args[1]
    assert request == dict(
        microscope="scope", request_id=1, identity=(1,), setting="scan_speed", value=2
    )
    assert c._depth_pending
    for name in (
        "bit_depth",
        "scan_speed",
        "defect_correction",
        "hot_pixel_correction",
    ):
        assert str(c.view.inputs[name]["state"]) == "disabled"
    c._receive_bit_depth({**response(c), "error": "Rejected"})
    assert c.view.inputs["scan_speed"].get() == "Ultra quiet"
    assert "Rejected" in c.view.variables["scan_speed_status"].get()


def test_mode_mismatch_requires_explicit_apply_and_refreshes_choices(popup):
    c = popup
    c.camera_setting_dict["sensor_mode"] = "Light-Sheet"
    c._receive_bit_depth(response(c))
    assert str(c.view.inputs["scan_speed"]["state"]) == "disabled"
    assert str(c.view.buttons["apply_sensor_mode"]["state"]) == "normal"
    c.apply_sensor_mode()
    request = c.parent_controller.execute.call_args.args[1]
    assert request["setting"] == "sensor_mode" and request["value"] == 12
    result = response(c)
    result["capabilities"]["sensor_mode"] = CameraSettingCapability(
        12, (1, 12), True, reason=""
    )
    result["capabilities"]["scan_speed"] = CameraSettingCapability(
        2, (2,), False, reason="Fixed"
    )
    c._receive_bit_depth(result)
    assert c.view.inputs["scan_speed"].get() == "2"
    assert str(c.view.buttons["apply_sensor_mode"]["state"]) == "disabled"


def test_late_result_cannot_enable_controls_during_acquisition(popup):
    c = popup
    c.parent_controller.acquire_bar_controller.is_acquiring = True
    c._receive_bit_depth(response(c))
    for name in ("scan_speed", "defect_correction", "hot_pixel_correction"):
        assert str(c.view.inputs[name]["state"]) == "disabled"


def test_main_sensor_selection_updates_pending_mode_and_refreshes_popup():
    from unittest.mock import MagicMock
    from navigate.controller.sub_controllers.camera_settings import (
        CameraSettingController,
    )

    c = CameraSettingController.__new__(CameraSettingController)
    c.mode_widgets = {key: MagicMock() for key in ("Sensor", "Readout", "Pixels")}
    c.mode_widgets["Sensor"].widget.get.return_value = "Normal"
    c.camera_setting_dict = {"sensor_mode": "Light-Sheet"}
    c.in_initialization = False
    c.microscope_name = "scope"
    advanced = SimpleNamespace(current_microscope="scope", refresh_bit_depth=Mock())
    c.parent_controller = SimpleNamespace(advanced_camera_setting_controller=advanced)
    c.show_verbose_info = Mock()
    c.update_readout_time = Mock()
    c.update_sensor_mode()
    assert c.camera_setting_dict["sensor_mode"] == "Normal"
    advanced.refresh_bit_depth.assert_called_once()
