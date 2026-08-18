from types import SimpleNamespace
from unittest.mock import MagicMock

from navigate.controller.sub_controllers.gui_settings_popup import (
    GuiSettingsPopupController,
)


def _controller_for_apply(entries):
    view = SimpleNamespace(
        entries=entries,
        boolean_variables={},
        set_status=MagicMock(),
        show_info=MagicMock(),
    )
    parent = SimpleNamespace(
        configuration={
            "gui": {
                "remote_focus_waveform": {"amplitude_step_size": 0.0001},
                "channel_settings": {"laser_power": {"max": 100}},
                "histogram": {"enabled": True},
                "mip_display": {"enabled": True},
            }
        },
        menu_controller=SimpleNamespace(
            popup_waveform_setting=MagicMock(),
            histogram_enabled=MagicMock(),
            mip_enabled=MagicMock(),
            toggle_histogram=MagicMock(),
            toggle_mip=MagicMock(),
        ),
    )
    controller = GuiSettingsPopupController.__new__(GuiSettingsPopupController)
    controller.view = view
    controller.parent_controller = parent
    return controller


def _entry(value):
    return (SimpleNamespace(get=lambda: value), MagicMock())


def test_apply_shows_restart_information_for_laser_power_changes():
    controller = _controller_for_apply(
        {("channel_settings", "laser_power", "max"): _entry("101")}
    )

    assert controller.apply_settings()
    assert (
        controller.parent_controller.configuration["gui"]["channel_settings"][
            "laser_power"
        ]["max"]
        == 101.0
    )
    controller.view.show_info.assert_called_once()


def test_apply_refreshes_an_open_waveform_popup_for_waveform_changes():
    controller = _controller_for_apply(
        {
            ("remote_focus_waveform", "amplitude_step_size"): _entry("0.001"),
        }
    )
    waveform_popup = MagicMock()
    controller.parent_controller.waveform_popup_controller = waveform_popup

    assert controller.apply_settings()
    controller.view.show_info.assert_called_once_with(
        "Settings Saved",
        "Waveform step-size settings were applied successfully.\n\n"
        "The Waveform Parameters window was reopened to take effect",
    )
    waveform_popup.close_window.assert_called_once()
    controller.parent_controller.menu_controller.popup_waveform_setting.assert_called_once()


def test_apply_combines_waveform_and_restart_information():
    controller = _controller_for_apply(
        {
            ("remote_focus_waveform", "amplitude_step_size"): _entry("0.001"),
            ("channel_settings", "laser_power", "max"): _entry("101"),
        }
    )

    assert controller.apply_settings()
    controller.view.show_info.assert_called_once_with(
        "Settings Saved",
        "Waveform step-size settings were applied successfully.\n\n"
        "Setting changes were saved. Restart Navigate for the changes to take "
        "effect.",
    )


def test_apply_updates_histogram_and_mip_displays_immediately():
    controller = _controller_for_apply({})
    controller.view.boolean_variables = {
        ("histogram", "enabled"): SimpleNamespace(get=lambda: False),
        ("mip_display", "enabled"): SimpleNamespace(get=lambda: False),
    }

    assert controller.apply_settings()

    assert controller.parent_controller.configuration["gui"]["histogram"][
        "enabled"
    ] is False
    assert controller.parent_controller.configuration["gui"]["mip_display"][
        "enabled"
    ] is False
    menu_controller = controller.parent_controller.menu_controller
    menu_controller.histogram_enabled.set.assert_called_once_with(False)
    menu_controller.toggle_histogram.assert_called_once()
    menu_controller.mip_enabled.set.assert_called_once_with(False)
    menu_controller.toggle_mip.assert_called_once()
    controller.view.show_info.assert_not_called()
