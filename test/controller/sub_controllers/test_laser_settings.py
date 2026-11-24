"""Real Tk widgets exercise popup state without accessing physical hardware."""

from types import SimpleNamespace
from unittest.mock import Mock
from multiprocessing import Manager

import pytest

from navigate.config.config import update_config_dict
from navigate.controller.sub_controllers.laser_settings import (
    AdvancedLaserSettingController,
)
from navigate.controller.sub_controllers.menus import MenuController
from navigate.view.popups.laser_setting_popup import AdvancedLaserSettingPopup
from test.model.devices.lasers.test_laser_software import make_laser


@pytest.fixture
def popup(tk_root):
    parent = SimpleNamespace(
        configuration={
            "configuration": {
                "microscopes": {
                    "scope": {"laser": [{"wavelength": 488}, {"wavelength": 640}]},
                    "empty": {},
                }
            },
            "experiment": {"MicroscopeState": {"microscope_name": "scope"}},
        },
        acquire_bar_controller=SimpleNamespace(is_acquiring=False),
        execute=Mock(),
    )
    view = AdvancedLaserSettingPopup(tk_root)
    controller = AdvancedLaserSettingController(view, parent)
    parent.advanced_laser_setting_controller = controller
    yield controller
    controller.close_popup()


def reply(popup, **kwargs):
    _, request, callback = popup.parent_controller.execute.call_args.args
    snapshot = make_laser().advanced_settings_snapshot()
    result = {
        **request,
        **snapshot,
        "error": None,
        "identity": "connection-token",
        **kwargs,
    }
    callback(result)
    return result


def test_open_queries_async_and_shows_unknown_simulated_readbacks(popup):
    view = popup.view
    assert str(view.buttons["apply"]["state"]) == "disabled"
    assert (
        popup.parent_controller.execute.call_args.args[0] == "laser_advanced_settings"
    )
    assert view.variables["measured"].get() == "Unknown"
    reply(popup)
    assert view.variables["connection"].get() == "Simulated"
    assert view.variables["mode"].get() == "Digital"
    assert view.inputs["mode"]["values"] == ("CW", "Digital")
    assert view.variables["limits"].get() == "0–100 mW"
    assert view.variables["setpoint"].get() == "0 mW (peak pulse)"
    assert view.variables["measured"].get() == "Unknown"
    assert view.variables["emission"].get() == "Unknown"


def test_popup_populates_selectors_from_nested_shared_configuration(tk_root):
    with Manager() as manager:
        configuration = manager.dict()
        update_config_dict(
            manager,
            configuration,
            "configuration",
            {
                "microscopes": {
                    "ORCA-Quest2": {"laser": [{"wavelength": 488}]},
                    "other": {"laser": [{"wavelength": 640}]},
                }
            },
        )
        update_config_dict(
            manager,
            configuration,
            "experiment",
            {"MicroscopeState": {"microscope_name": "ORCA-Quest2"}},
        )
        parent = SimpleNamespace(
            configuration=configuration,
            acquire_bar_controller=SimpleNamespace(is_acquiring=False),
            execute=Mock(),
        )
        view = AdvancedLaserSettingPopup(tk_root)
        controller = None
        try:
            controller = AdvancedLaserSettingController(view, parent)
            assert view.inputs["microscope"]["values"] == ("ORCA-Quest2", "other")
            assert view.variables["microscope"].get() == "ORCA-Quest2"
            assert view.inputs["laser"]["values"] == ("488 nm",)
            assert view.variables["laser"].get() == "488 nm"
            request = parent.execute.call_args.args[1]
            assert request["microscope"] == "ORCA-Quest2"
            assert request["laser"] == "488"
            reply(controller, mode="cw", bench_mode=True, power_kind="cw_setpoint")
            assert view.inputs["mode"]["values"] == ("CW", "Digital")
            assert view.variables["mode"].get() == "CW"
            view.variables["microscope"].set("other")
            controller.update_microscope()
            assert view.inputs["laser"]["values"] == ("640 nm",)
            assert parent.execute.call_args.args[1]["laser"] == "640"
        finally:
            if controller is not None:
                controller.close_popup()
            else:
                view.popup.destroy()


def test_serial_bench_display_explains_ungated_illumination(popup):
    reply(popup, bench_mode=True)
    assert popup.view.variables["power_source"].get() == "Serial (bench; no gating)"
    assert "does not gate illumination" in popup.view.variables["status"].get()


def test_mode_selection_is_explicit_and_locked_until_response(popup):
    reply(popup)
    popup.view.variables["mode"].set("CW")
    assert popup.parent_controller.execute.call_count == 1
    popup.view.buttons["apply"].invoke()
    request = popup.parent_controller.execute.call_args.args[1]
    assert request["mode"] == "cw"
    assert request["identity"] == "connection-token"
    assert str(popup.view.inputs["microscope"]["state"]) == "disabled"
    assert str(popup.view.buttons["apply"]["state"]) == "disabled"
    popup.apply_mode()
    assert popup.parent_controller.execute.call_count == 2
    reply(popup, mode="cw", acquisition_mode="cw", power_kind="cw_setpoint")
    assert popup.view.variables["current_mode"].get() == "CW"
    assert popup.view.variables["acquisition_mode"].get() == "CW"


def test_old_or_different_device_responses_are_ignored(popup):
    result = reply(popup)
    popup.view.variables["laser"].set("640 nm")
    popup.refresh()
    assert popup.view.variables["setpoint"].get() == "Unknown"
    popup._receive(result)
    assert popup._pending
    assert popup.view.variables["setpoint"].get() == "Unknown"
    popup._receive({**result, "request_id": popup._request_id})
    assert popup._pending
    reply(popup)
    assert not popup._pending


def test_close_while_pending_ignores_late_completion(popup):
    _, request, callback = popup.parent_controller.execute.call_args.args
    popup.close_popup()
    callback(request)  # Would raise TclError if any destroyed widget was touched.
    assert not hasattr(popup.parent_controller, "advanced_laser_setting_controller")


def test_busy_popup_does_not_send_requests_and_refreshes_after_stop(popup):
    reply(popup)
    popup.set_acquisition_state(True)
    popup.refresh()
    popup.apply_mode()
    assert popup.parent_controller.execute.call_count == 1
    assert str(popup.view.buttons["refresh"]["state"]) == "disabled"
    assert popup.view.variables["measured"].get() == "Unknown"
    popup.set_acquisition_state(False)
    assert popup.parent_controller.execute.call_count == 2


def test_response_after_capture_starts_does_not_restore_idle_readbacks(popup):
    popup.set_acquisition_state(True)
    reply(popup)
    assert not popup._pending
    assert popup.view.variables["setpoint"].get() == "Unknown"
    assert str(popup.view.buttons["apply"]["state"]) == "disabled"


def test_error_removes_old_readbacks_and_allows_refresh(popup):
    reply(popup)
    popup.refresh()
    reply(popup, connection="unavailable", error="Serial disconnected")
    assert popup.view.variables["setpoint"].get() == "Unknown"
    assert popup.view.variables["connection"].get() == "Unavailable"
    assert popup.view.variables["status"].get() == "Serial disconnected"
    assert str(popup.view.buttons["apply"]["state"]) == "disabled"
    assert str(popup.view.buttons["refresh"]["state"]) == "normal"


def test_legacy_and_empty_configurations_do_not_require_new_fields(popup):
    reply(popup, connection="not_configured")
    assert popup.view.variables["connection"].get() == "Software control not configured"
    assert str(popup.view.buttons["apply"]["state"]) == "disabled"
    popup.view.variables["microscope"].set("empty")
    popup.update_microscope()
    assert popup.parent_controller.execute.call_count == 1
    assert (
        popup.view.variables["status"].get()
        == "No lasers configured for this microscope."
    )


def test_external_analog_readbacks_do_not_claim_internal_output(popup):
    reply(
        popup,
        power_source="hardware",
        mode="analog",
        available_modes=["cw", "digital", "analog", "mixed"],
        setpoint_mw=None,
    )
    assert popup.view.inputs["mode"]["values"] == ("CW", "Digital", "Analog", "Mixed")
    assert popup.view.variables["setpoint"].get() == "External analog control"
    assert popup.view.variables["reference"].get() == "External hardware scale"


def test_menu_reuses_existing_popup(popup):
    menu = MenuController.__new__(MenuController)
    menu.parent_controller = popup.parent_controller
    popup.showup = Mock()
    menu.popup_advanced_laser_setting()
    popup.showup.assert_called_once()


@pytest.mark.parametrize(
    "backend,labels",
    [("OBIS", ("CW", "Digital", "Analog", "Mixed")), ("LuxX", ("CW", "Analog"))],
)
def test_popup_uses_adapter_capabilities_and_readbacks(popup, backend, labels):
    from test.model.devices.lasers.test_obis_luxx_settings import adapter
    from test.model.devices.lasers.test_laser_software import configuration

    laser = make_laser(configuration(source="hardware"))
    laser.settings, _ = adapter(backend)
    reply(popup, **laser.advanced_settings_snapshot())
    assert popup.view.inputs["mode"]["values"] == labels
    assert popup.view.variables["connection"].get() == "Connected"
    assert popup.view.variables["limits"].get() == "0–200 mW"
    assert popup.view.variables["measured"].get() == "7.25 mW"


def test_connected_standby_state_allows_selecting_a_supported_mode(popup):
    reply(
        popup,
        connection="connected",
        available_modes=["cw"],
        mode=None,
        setpoint_mw=None,
        mode_warning="LuxX is in Standby; select CW.",
    )
    assert popup.view.variables["connection"].get() == "Connected"
    assert popup.view.variables["setpoint"].get() == "Unknown"
    assert "Standby" in popup.view.variables["status"].get()
    popup.view.variables["mode"].set("CW")
    popup.apply_mode()
    assert popup.parent_controller.execute.call_args.args[1]["mode"] == "cw"
