import pytest
import random
from types import SimpleNamespace
from unittest.mock import MagicMock


@pytest.fixture(scope="module")
def waveform_popup_controller(dummy_view, dummy_controller):
    from navigate.controller.sub_controllers.waveform_popup import (
        WaveformPopupController,
    )
    from navigate.view.popups.waveform_parameter_popup_window import (
        WaveformParameterPopupWindow,
    )

    waveform_constants_popup = WaveformParameterPopupWindow(
        dummy_view, dummy_controller.configuration_controller
    )

    return WaveformPopupController(
        waveform_constants_popup,
        dummy_controller,
        dummy_controller.waveform_constants_path,
    )


def test_populate_experiment_values(waveform_popup_controller):
    exp_dict = waveform_popup_controller.parent_controller.configuration["experiment"][
        "MicroscopeState"
    ]
    resolution = exp_dict["microscope_name"]
    zoom = exp_dict["zoom"]
    waveform_constants = waveform_popup_controller.parent_controller.configuration[
        "waveform_constants"
    ]
    widgets = waveform_popup_controller.view.get_widgets()

    def assert_widget_values():
        resolution = exp_dict["microscope_name"]
        zoom = exp_dict["zoom"]
        assert widgets["Mode"].get() == resolution
        assert widgets["Mag"].get() == zoom

        # remote focus
        remote_focus_dict = waveform_constants["remote_focus_constants"][resolution][
            zoom
        ]
        for k in remote_focus_dict.keys():
            assert widgets[k + " Amp"].get() == remote_focus_dict[k]["amplitude"]
            assert widgets[k + " Off"].get() == remote_focus_dict[k]["offset"]

        # galvo
        galvo_dict = waveform_constants["galvo_constants"]
        for g in galvo_dict.keys():
            if resolution in [galvo_dict[g].keys()]:
                galvo_info = galvo_dict[g][resolution][zoom]
                assert widgets[g + " Amp"].get() == galvo_info["amplitude"]
                assert widgets[g + " Off"].get() == galvo_info["offset"]

        # delay, fly back time, settle duraation, smoothing
        assert widgets["Delay"].get() == str(
            waveform_constants["other_constants"]["remote_focus_delay"]
        )
        assert widgets["Ramp_falling"].get() == str(
            waveform_constants["other_constants"]["remote_focus_ramp_falling"]
        )
        assert widgets["Duty"].get() == str(
            waveform_constants["other_constants"]["remote_focus_settle_duration"]
        )
        assert widgets["Smoothing"].get() == str(
            waveform_constants["other_constants"]["percent_smoothing"]
        )

    # default values
    waveform_popup_controller.populate_experiment_values()
    assert_widget_values()

    # change resolution and/or zoom
    for microscope_name in waveform_constants["remote_focus_constants"].keys():
        for z in waveform_constants["remote_focus_constants"][microscope_name].keys():
            exp_dict["microscope_name"] = microscope_name
            exp_dict["zoom"] = z
            waveform_popup_controller.populate_experiment_values()
            assert_widget_values()

    exp_dict["microscope_name"] = resolution
    exp_dict["zoom"] = zoom
    waveform_popup_controller.populate_experiment_values()
    assert_widget_values()

    # update waveform_constants
    for k in waveform_constants["remote_focus_constants"][resolution][zoom].keys():
        amplitude = round(random.random() * 5, 2)
        offset = round(random.random() * 5, 2)
        temp = waveform_constants["remote_focus_constants"][resolution][zoom][k]
        temp["amplitude"] = amplitude
        temp["offset"] = offset

    # update galvo
    for g in waveform_constants["galvo_constants"].keys():
        amplitude = round(random.random() * 5, 2)
        offset = round(random.random() * 5, 2)
        temp = waveform_constants["galvo_constants"][g][resolution][zoom]
        temp["amplitude"] = amplitude
        temp["offset"] = offset

    for k in [
        "remote_focus_ramp_falling",
        "remote_focus_settle_duration",
        "percent_smoothing",
        "remote_focus_delay",
    ]:
        waveform_constants["other_constants"][k] = round(random.random() * 100, 2)

    waveform_popup_controller.populate_experiment_values(force_update=True)
    assert_widget_values()


def test_show_laser_info(waveform_popup_controller):
    waveform_popup_controller.show_laser_info()
    assert True


def test_configure_widget_range(waveform_popup_controller):
    waveform_popup_controller.configure_widget_range()
    assert True


def test_estimate_galvo_setting_empty_string(waveform_popup_controller):
    """Test if the function returns without calling the camera setting controller."""
    # Galvo name
    galvo_name = "galvo_0"

    # Mocked camera setting controller
    waveform_popup_controller.parent_controller.camera_setting_controller = MagicMock()
    waveform_popup_controller.parent_controller.camera_setting_controller.mode_widgets[
        "Pixels"
    ].get = MagicMock(return_value="")
    waveform_popup_controller.parent_controller.camera_setting_controller.framerate_widgets[
        "exposure_time"
    ].get = MagicMock()

    waveform_popup_controller.estimate_galvo_setting(galvo_name)
    waveform_popup_controller.parent_controller.camera_setting_controller.framerate_widgets[
        "exposure_time"
    ].get.assert_not_called()


def test_estimate_galvo_setting_with_string(waveform_popup_controller):
    """Test if the function calls the camera setting controller."""
    # Galvo name
    galvo_name = "galvo_0"
    number_of_pixels = 50

    # Mocked camera setting controller
    waveform_popup_controller.parent_controller.camera_setting_controller = MagicMock()
    waveform_popup_controller.parent_controller.camera_setting_controller.mode_widgets[
        "Pixels"
    ].get = MagicMock(return_value=str(number_of_pixels))
    waveform_popup_controller.parent_controller.camera_setting_controller.framerate_widgets[
        "exposure_time"
    ].get = MagicMock()

    # Mocked model
    waveform_popup_controller.parent_controller.model = MagicMock()
    mock_model = waveform_popup_controller.parent_controller.model
    mock_model.get_camera_line_interval_and_exposure_time = MagicMock(
        return_value=(0.05, 50, 500)
    )

    # Mocked view
    waveform_popup_controller.view = MagicMock()
    waveform_popup_controller.view.inputs[galvo_name].widget.set = MagicMock()

    # Call the function
    waveform_popup_controller.estimate_galvo_setting(galvo_name)

    # Check to see what the view was called with.
    waveform_popup_controller.view.inputs[galvo_name].widget.set.assert_called_once()


def _make_minimal_waveform_controller():
    from navigate.controller.sub_controllers.waveform_popup import WaveformPopupController

    controller = WaveformPopupController.__new__(WaveformPopupController)
    controller.resolution = "Mesoscale"
    controller.mag = "1x"
    controller.event_id = None
    controller.waveforms_enabled = True
    controller.lasers = ["Laser 1"]
    controller.galvos = ["Galvo 0"]
    controller.laser_min = -1.0
    controller.laser_max = 1.0
    controller.galvo_min = {"Galvo 0": -2.0}
    controller.galvo_max = {"Galvo 0": 2.0}
    controller.increment = 0.1
    controller.parent_controller = MagicMock()
    controller.view = MagicMock()
    controller.view.popup.after = MagicMock(return_value="after-id")
    controller.view.popup.after_cancel = MagicMock()
    controller.view.buttons = {"toggle_waveform_button": MagicMock()}
    controller.view.inputs = {
        "galvo_info": SimpleNamespace(widget=MagicMock()),
        "all_channels": MagicMock(),
    }
    controller.widgets = {
        "Delay": SimpleNamespace(widget=MagicMock()),
        "Duty": SimpleNamespace(widget=MagicMock()),
        "Smoothing": SimpleNamespace(widget=MagicMock()),
        "Ramp_falling": SimpleNamespace(widget=MagicMock()),
        "camera_delay": SimpleNamespace(widget=MagicMock()),
        "camera_settle_duration": SimpleNamespace(widget=MagicMock()),
        "Laser 1 Amp": SimpleNamespace(widget=MagicMock()),
        "Galvo 0 Amp": SimpleNamespace(widget=MagicMock()),
        "Galvo 0 Off": SimpleNamespace(widget=MagicMock()),
    }
    controller.variables = {
        "Laser 1 Amp": MagicMock(),
        "Galvo 0 Amp": MagicMock(),
        "Galvo 0 Off": MagicMock(),
    }
    controller.resolution_info = {
        "remote_focus_constants": {
            "Mesoscale": {
                "1x": {"Laser 1": {"amplitude": 0.2, "offset": 0.1}},
            }
        },
        "galvo_constants": {
            "Galvo 0": {
                "Mesoscale": {
                    "1x": {
                        "amplitude": 0.3,
                        "offset": -0.1,
                        "All": {"amplitude": 0.3, "offset": -0.1},
                    }
                }
            }
        },
        "other_constants": {
            "remote_focus_settle_duration": 1.0,
            "remote_focus_ramp_falling": 1.0,
            "remote_focus_delay": 1.0,
            "percent_smoothing": 1.0,
            "camera_delay": 1.0,
            "camera_settle_duration": 1.0,
            "galvo_factor": "none",
        },
    }
    controller.galvo_setting = controller.resolution_info["galvo_constants"]
    controller.update_waveform_parameters_flag = True
    controller.update_galvo_device_flag = True
    controller.amplitude_dict = None
    return controller


def test_close_window_invokes_cleanup(waveform_popup_controller):
    waveform_popup_controller.parent_controller.waveform_popup_controller = (
        waveform_popup_controller
    )
    waveform_popup_controller.restore_amplitude = MagicMock()
    waveform_popup_controller.save_waveform_constants = MagicMock()
    waveform_popup_controller.view.popup.dismiss = MagicMock()

    waveform_popup_controller.close_window()

    waveform_popup_controller.restore_amplitude.assert_called_once()
    waveform_popup_controller.save_waveform_constants.assert_called_once()
    waveform_popup_controller.view.popup.dismiss.assert_called_once()
    assert not hasattr(
        waveform_popup_controller.parent_controller, "waveform_popup_controller"
    )


def test_update_waveform_parameters_updates_and_schedules():
    controller = _make_minimal_waveform_controller()
    controller.widgets["Delay"].widget.get.return_value = "1.1"
    controller.widgets["Duty"].widget.get.return_value = "2.2"
    controller.widgets["Smoothing"].widget.get.return_value = "3.3"
    controller.widgets["Ramp_falling"].widget.get.return_value = "4.4"
    controller.widgets["camera_delay"].widget.get.return_value = "5.5"
    controller.widgets["camera_settle_duration"].widget.get.return_value = "6.6"
    controller.event_id = "old-id"

    controller.update_waveform_parameters()

    assert (
        controller.resolution_info["other_constants"]["remote_focus_settle_duration"]
        == 2.2
    )
    assert (
        controller.resolution_info["other_constants"]["camera_settle_duration"] == 6.6
    )
    controller.view.popup.after_cancel.assert_called_once_with("old-id")
    controller.view.popup.after.assert_called_once()


def test_update_waveform_parameters_invalid_value_returns():
    controller = _make_minimal_waveform_controller()
    controller.widgets["Delay"].widget.get.return_value = "invalid"
    controller.widgets["Duty"].widget.get.return_value = "2.2"
    controller.widgets["Smoothing"].widget.get.return_value = "3.3"
    controller.widgets["Ramp_falling"].widget.get.return_value = "4.4"
    controller.widgets["camera_delay"].widget.get.return_value = "5.5"
    controller.widgets["camera_settle_duration"].widget.get.return_value = "6.6"

    controller.update_waveform_parameters()

    controller.view.popup.after.assert_not_called()


def test_update_remote_focus_settings_callback_updates_constants():
    controller = _make_minimal_waveform_controller()
    controller.variables["Laser 1 Amp"].get.return_value = "0.4"
    callback = controller.update_remote_focus_settings("Laser 1 Amp", "Laser 1", "amplitude")

    callback()

    assert (
        controller.resolution_info["remote_focus_constants"]["Mesoscale"]["1x"]["Laser 1"][
            "amplitude"
        ]
        == "0.4"
    )
    controller.view.popup.after.assert_called_once()


def test_update_remote_focus_settings_callback_out_of_range():
    controller = _make_minimal_waveform_controller()
    controller.variables["Laser 1 Amp"].get.return_value = "5.0"
    callback = controller.update_remote_focus_settings("Laser 1 Amp", "Laser 1", "amplitude")

    callback()

    controller.view.popup.after.assert_not_called()


def test_update_galvo_setting_callback_updates_setting():
    controller = _make_minimal_waveform_controller()
    controller.variables["Galvo 0 Off"].get.return_value = "0.6"
    callback = controller.update_galvo_setting("Galvo 0", " Off", "offset")

    callback()

    assert (
        controller.galvo_setting["Galvo 0"]["Mesoscale"]["1x"]["offset"] == "0.6"
    )
    controller.view.popup.after.assert_called_once()


def test_toggle_waveform_state_transitions():
    controller = _make_minimal_waveform_controller()
    controller.variables["Laser 1 Amp"].set = MagicMock()
    controller.variables["Galvo 0 Amp"].set = MagicMock()

    controller.toggle_waveform_state()

    assert controller.waveforms_enabled is False
    assert controller.amplitude_dict is not None
    controller.variables["Laser 1 Amp"].set.assert_called_once_with(0)
    controller.variables["Galvo 0 Amp"].set.assert_called_once_with(0)

    controller.show_laser_info = MagicMock()
    controller.event_id = "old-id"
    controller.toggle_waveform_state()

    controller.show_laser_info.assert_called_once()
    controller.view.popup.after_cancel.assert_called_with("old-id")


def test_restore_amplitude_restores_saved_values():
    controller = _make_minimal_waveform_controller()
    controller.amplitude_dict = {"resolution": "Mesoscale", "mag": "1x", "Laser 1": 0.9, "Galvo 0": -0.4}

    controller.restore_amplitude()

    assert (
        controller.resolution_info["remote_focus_constants"]["Mesoscale"]["1x"]["Laser 1"][
            "amplitude"
        ]
        == 0.9
    )
    assert (
        controller.resolution_info["galvo_constants"]["Galvo 0"]["Mesoscale"]["1x"][
            "amplitude"
        ]
        == -0.4
    )
    assert controller.amplitude_dict is None


def test_set_galvo_factor_and_set_all_channels():
    controller = _make_minimal_waveform_controller()
    controller.widgets["Galvo 0 Amp"].widget = MagicMock()
    controller.widgets["Galvo 0 Off"].widget = MagicMock()

    controller.set_galvo_factor("channel")
    assert controller.resolution_info["other_constants"]["galvo_factor"] == "channel"
    controller.view.inputs["all_channels"].set.assert_called_with(False)

    controller.set_galvo_factor("none")
    assert controller.resolution_info["other_constants"]["galvo_factor"] == "none"
    controller.view.inputs["all_channels"].set.assert_called_with(True)

    controller.advanced_setting_popup = MagicMock()
    controller.set_galvo_to_all_channels()
    controller.advanced_setting_popup.variables["galvo_factor"].set.assert_called_with(
        "none"
    )


def test_update_galvo_advanced_setting_callback():
    controller = _make_minimal_waveform_controller()
    parameter = MagicMock()
    parameter.get.return_value = "0.75"
    controller.advanced_setting_popup = MagicMock()
    controller.advanced_setting_popup.parameters = {"galvo_0_0_amp": parameter}
    controller.event_id = "old-id"

    callback = controller.update_galvo_advanced_setting(0, 0, "All", "amp")
    callback()

    assert (
        controller.galvo_setting["Galvo 0"]["Mesoscale"]["1x"]["amplitude"] == 0.75
    )
    controller.view.popup.after_cancel.assert_called_once_with("old-id")
    controller.view.popup.after.assert_called()
