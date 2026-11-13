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


def test_pending_mode_apply_preserves_new_main_selection_and_displays_mismatch(popup):
    from navigate.model.model import Model
    from navigate.model.devices.camera.synthetic import SyntheticCamera

    c = popup
    c.camera_setting_dict.update(img_x_pixels=3, img_y_pixels=2, binning="1x1")
    configuration = {
        "experiment": {
            "MicroscopeState": {"microscope_name": "scope"},
            "CameraParameters": {"scope": c.camera_setting_dict},
        },
        "configuration": {
            "microscopes": {
                "scope": {
                    "camera": {
                        "hardware": {"serial_number": "mode-race"},
                        "x_pixels": 3,
                        "y_pixels": 2,
                    }
                }
            }
        },
    }
    c.parent_controller.configuration = configuration
    camera = SyntheticCamera("scope", None, configuration)
    model = Model.__new__(Model)
    model.configuration = configuration
    model.is_acquiring = False
    model.microscopes = {"scope": SimpleNamespace(camera=camera)}
    model.get_data_buffer = lambda *args: None
    c.camera_setting_dict["sensor_mode"] = "Light-Sheet"
    initial = model.camera_advanced_settings(dict(microscope="scope", request_id=0))
    c._receive_bit_depth(initial)
    c.apply_sensor_mode()
    pending_request = c.parent_controller.execute.call_args.args[1]
    assert c._depth_pending
    c.camera_setting_dict["sensor_mode"] = "Normal"
    c.refresh_bit_depth()  # the main-tab handler cannot query during the write
    completed = model.camera_advanced_settings(pending_request)
    c._receive_bit_depth(completed)
    assert c.camera_setting_dict["sensor_mode"] == "Normal"
    assert camera.get_advanced_setting("sensor_mode") == 12
    assert str(c.view.inputs["scan_speed"]["state"]) == "disabled"
    assert str(c.view.buttons["apply_sensor_mode"]["state"]) == "normal"


@pytest.mark.parametrize("initial_width,expected_initial_width", [(24, 24), (64, 48)])
@pytest.mark.parametrize("target_name", ["scope", "other"])
@pytest.mark.parametrize(
    "old_step,new_step,requested_width,expected_width", [(4, 8, 20, 16), (8, 4, 18, 16)]
)
def test_mode_geometry_reply_refreshes_real_roi_validation_without_repopulating(
    popup,
    tk_root,
    target_name,
    old_step,
    new_step,
    requested_width,
    expected_width,
    initial_width,
    expected_initial_width,
):
    from navigate.controller.sub_controllers.camera_settings import (
        CameraSettingController,
    )
    from navigate.view.main_window_content.camera_tab import CameraSettingsTab

    c = popup
    camera_configs = {
        name: {
            "x_pixels": 64,
            "y_pixels": 64,
            "x_pixels_min": old_step,
            "y_pixels_min": old_step,
            "x_pixels_step": old_step,
            "y_pixels_step": old_step,
            "pixel_size_in_microns": 1,
            "supported_sensor_modes": ["Normal", "Light-Sheet"],
            "supported_readout_directions": ["Top-to-Bottom"],
        }
        for name in ("scope", "other")
    }
    parameters = {
        name: {
            "sensor_mode": "Normal",
            "binning": "1x1",
            "pixel_size": 1,
            "readout_direction": "Top-to-Bottom",
            "number_of_pixels": 1,
        }
        for name in camera_configs
    }
    parent = c.parent_controller
    parent.configuration = {
        "configuration": {
            "microscopes": {
                name: {"camera": config, "zoom": {"pixel_size": {"1x": 1}}}
                for name, config in camera_configs.items()
            }
        },
        "experiment": {
            "MicroscopeState": {"microscope_name": "scope", "zoom": "1x"},
            "CameraParameters": parameters,
        },
    }
    parent.configuration_controller = SimpleNamespace(
        camera_config_dict=camera_configs["scope"]
    )
    views = [CameraSettingsTab(tk_root), CameraSettingsTab(tk_root)]
    try:
        main = CameraSettingController(views[0], parent)
        additional = CameraSettingController(views[1], parent, microscope_name="other")
        parent.camera_setting_controller = main
        parent.other_camera_setting_controller = additional
        target, untouched = (
            (main, additional) if target_name == "scope" else (additional, main)
        )
        c.current_microscope = target_name
        c.camera_setting_dict = parameters[target_name]
        target.mode_widgets["Sensor"].set("Normal")  # newer pending UI mode
        target.roi_widgets["Binning"].set("1x1")
        target.roi_widgets["is_centered"].set(True)
        target.roi_widgets["Width"].set(initial_width)
        target.roi_widgets["Height"].set(32)
        target.in_initialization = False
        geometry = {
            "x_pixels_min": new_step,
            "x_pixels_max": 48,
            "x_pixels_step": new_step,
            "y_pixels_min": new_step,
            "y_pixels_max": 48,
            "y_pixels_step": new_step,
        }
        camera_configs[target_name].update(geometry)
        result = response(c)
        result.update(microscope=target_name, geometry=geometry)
        result["capabilities"]["sensor_mode"] = CameraSettingCapability(
            12, (1, 12), True, reason=""
        )
        assert "timing" not in result
        c._receive_bit_depth(result)
        assert target.step_width == target.step_height == new_step
        assert target.min_width == target.min_height == new_step
        assert target.default_width == target.default_height == 64
        assert target.roi_widgets["Width"].widget.cget("to") == 48
        assert target.roi_widgets["Height"].widget.cget("to") == 48
        assert target.roi_widgets["Width"].widget.cget("increment") == new_step
        assert target.roi_widgets["Width"].get() == expected_initial_width
        assert target.roi_widgets["Height"].get() == 32
        assert (
            target.mode_widgets["Sensor"].get()
            == parameters[target_name]["sensor_mode"]
            == "Normal"
        )
        assert untouched.step_width == old_step
        target.roi_widgets["Width"].set(requested_width)
        assert target.update_experiment_values() == ""
        assert parameters[target_name]["x_pixels"] == expected_width
        assert parameters[target_name]["img_x_pixels"] == expected_width
    finally:
        for view in views:
            view.destroy()


@pytest.fixture(params=[None, "other"])
def roi_controller(tk_root, request):
    """Real main/additional camera controls with a 64-pixel physical sensor."""
    from navigate.controller.sub_controllers.camera_settings import (
        CameraSettingController,
    )
    from navigate.view.main_window_content.camera_tab import CameraSettingsTab

    config = {
        "x_pixels": 64,
        "y_pixels": 64,
        "x_pixels_min": 4,
        "y_pixels_min": 4,
        "x_pixels_step": 4,
        "y_pixels_step": 4,
        "pixel_size_in_microns": 1,
        "supported_sensor_modes": ["Normal", "Light-Sheet"],
        "supported_readout_directions": ["Top-to-Bottom"],
    }
    parameters = {
        name: {
            "sensor_mode": "Normal",
            "binning": "1x1",
            "x_pixels": 24,
            "y_pixels": 24,
            "readout_direction": "Top-to-Bottom",
            "number_of_pixels": 1,
            "is_centered": True,
            "pixel_size": 1,
        }
        for name in ("scope", "other")
    }
    parent = SimpleNamespace(
        configuration_controller=SimpleNamespace(camera_config_dict=config),
        configuration={
            "configuration": {
                "microscopes": {
                    name: {"camera": dict(config), "zoom": {"pixel_size": {"1x": 1}}}
                    for name in parameters
                }
            },
            "experiment": {
                "MicroscopeState": {
                    "microscope_name": "scope",
                    "zoom": "1x",
                    "channels": {"channel_1": {"camera_exposure_time": 10}},
                },
                "CameraParameters": parameters,
            },
        },
    )
    view = CameraSettingsTab(tk_root)
    c = CameraSettingController(view, parent, microscope_name=request.param)
    c.populate_experiment_values()
    yield c
    view.destroy()


def apply_roi_geometry(c, maximum=48, step=4):
    geometry = {
        f"{axis}_pixels_{key}": value
        for axis in ("x", "y")
        for key, value in (("min", step), ("max", maximum), ("step", step))
    }
    if c.microscope_name:
        config = c.parent_controller.configuration["configuration"]["microscopes"][
            c.microscope_name
        ]["camera"]
    else:
        config = c.parent_controller.configuration_controller.camera_config_dict
    config.update(geometry)
    c.update_camera_geometry(geometry)


def test_mode_roi_limit_preserves_physical_center_and_user_size(roi_controller):
    c = roi_controller
    apply_roi_geometry(c)
    assert c.update_experiment_values() == ""
    assert (c.camera_setting_dict["center_x"], c.camera_setting_dict["center_y"]) == (
        32,
        32,
    )
    assert (c.camera_setting_dict["x_pixels"], c.camera_setting_dict["y_pixels"]) == (
        24,
        24,
    )
    assert c.roi_widgets["Width"].widget.cget("to") == 48
    assert c.roi_widgets["Bottom_X"].widget.cget("to") == 64


def test_refresh_and_population_preserve_mode_roi_limits(roi_controller):
    c = roi_controller
    apply_roi_geometry(c, step=8)
    c.update_camera_device_related_setting()
    c.camera_setting_dict.update(x_pixels=64, y_pixels=64)
    c.populate_experiment_values()
    assert c.roi_widgets["Width"].widget.cget("to") == 48
    assert c.roi_widgets["Height"].widget.cget("to") == 48
    assert c.roi_widgets["Width"].get() == 48
    assert c.roi_widgets["Height"].get() == 48
    c.initialize()
    assert c.roi_widgets["Width"].widget.cget("from") == 8
    assert c.roi_widgets["Width"].widget.cget("increment") == 8


def test_roi_presets_respect_mode_maximum(roi_controller):
    c = roi_controller
    apply_roi_geometry(c)
    for preset in ("All", "512"):
        c.update_roi(preset)()
        assert c.roi_widgets["Width"].get() == 48
        assert c.roi_widgets["Height"].get() == 48
        assert c.update_experiment_values() == ""
        assert c.camera_setting_dict["center_x"] == 32


def test_offset_roi_uses_physical_coordinates_but_respects_mode_size(roi_controller):
    c = roi_controller
    apply_roi_geometry(c)
    c.roi_widgets["is_centered"].set(False)
    for key, value in (
        ("Top_X", 40),
        ("Bottom_X", 64),
        ("Top_Y", 40),
        ("Bottom_Y", 64),
    ):
        c.roi_widgets[key].set(value)
    assert c.update_experiment_values() == ""
    assert c.camera_setting_dict["x_pixels"] == 24
    assert c.camera_setting_dict["center_x"] == 52
    c.roi_widgets["Top_X"].set(0)
    assert c.update_experiment_values()  # Width64 exceeds mode maximum48.


def test_centered_roi_rejects_boundaries_invalid_after_step_change(roi_controller):
    c = roi_controller
    assert c.update_experiment_values() == ""
    before = dict(c.camera_setting_dict)
    apply_roi_geometry(c, maximum=64, step=8)
    warning = c.update_experiment_values()
    assert warning
    assert "center" in warning.lower() and "8" in warning
    assert c.camera_setting_dict == before
    assert c.roi_widgets["Width"].get() == 24
    c.roi_widgets["Width"].set(32)
    c.roi_widgets["Height"].set(32)
    assert c.update_experiment_values() == ""
    assert c.camera_setting_dict["center_x"] == 32


def test_centered_roi_size_validation_cannot_be_bypassed_by_variable(roi_controller):
    c = roi_controller
    apply_roi_geometry(c)
    # A variable/programmatic edit can bypass spinbox focus-out validation.
    c.roi_widgets["Width"].set(64)
    assert c.update_experiment_values()


@pytest.mark.parametrize(
    "size,binning,expected_size", [(24, "2x2", 16), (16, "4x4", None)]
)
def test_centered_roi_validates_final_binned_geometry(
    roi_controller, size, binning, expected_size
):
    c = roi_controller
    apply_roi_geometry(c, maximum=64, step=8)
    c.roi_widgets["Width"].set(size)
    c.roi_widgets["Height"].set(size)
    c.roi_widgets["Binning"].set(binning)
    warning = c.update_experiment_values()
    if expected_size is None:
        assert warning  # Binning and step rounding must not permit a zero-sized ROI.
    else:
        assert warning == ""
        assert c.camera_setting_dict["x_pixels"] == expected_size
        assert c.camera_setting_dict["y_pixels"] == expected_size
        assert c.camera_setting_dict["center_x"] == 32
