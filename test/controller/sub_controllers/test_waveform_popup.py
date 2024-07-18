import pytest
import random
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
