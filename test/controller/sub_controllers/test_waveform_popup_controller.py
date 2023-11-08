import pytest


@pytest.fixture(scope="module")
def waveform_popup_controller(dummy_view, dummy_controller):
    from aslm.controller.sub_controllers.waveform_popup_controller import (
        WaveformPopupController,
    )
    from aslm.view.popups.waveform_parameter_popup_window import (
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
    waveform_popup_controller.populate_experiment_values()
    assert True


def test_show_laser_info(waveform_popup_controller):
    waveform_popup_controller.show_laser_info()
    assert True


def test_configure_widget_range(waveform_popup_controller):
    waveform_popup_controller.configure_widget_range()
    assert True
