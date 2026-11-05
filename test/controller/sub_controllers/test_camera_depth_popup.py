"""Asynchronous popup results never apply to a different camera or closed view."""

from types import SimpleNamespace
from unittest.mock import Mock, MagicMock

import pytest

from navigate.controller.sub_controllers.camera_settings import (
    AdvancedCameraSettingController,
)
from navigate.model.devices.camera.format import CameraSettingCapability


@pytest.fixture
def popup():
    c = AdvancedCameraSettingController.__new__(AdvancedCameraSettingController)
    c.parent_controller = SimpleNamespace(
        execute=Mock(), acquire_bar_controller=SimpleNamespace(is_acquiring=False)
    )
    c.current_microscope = "scope"
    c._depth_request_id = 0
    c._depth_identity = None
    c._depth_pending = False
    c._depth_closed = False
    c._depth_close_requested = False
    c._depth_capability = CameraSettingCapability()
    c.view = MagicMock()
    c.view.inputs = {"bit_depth": MagicMock()}
    c.view.variables = {"bit_depth_status": Mock()}
    c.save_camera_settings = Mock()
    return c


def response(popup, **values):
    result = dict(
        microscope="scope",
        request_id=popup._depth_request_id,
        identity=(1,),
        error=None,
        capability=CameraSettingCapability(16, (8, 12, 16), True, reason=""),
    )
    result.update(values)
    return result


def test_read_request_is_tagged_and_starts_disabled(popup):
    popup.refresh_bit_depth()
    command, request, callback = popup.parent_controller.execute.call_args.args
    assert command == "camera_advanced_settings"
    assert request == {"microscope": "scope", "request_id": 1}
    assert callback == popup._receive_bit_depth
    assert popup.view.inputs["bit_depth"].__setitem__.call_args.args == (
        "state",
        "disabled",
    )


@pytest.mark.parametrize("stale", ["request", "scope", "closed"])
def test_stale_results_do_not_touch_view(popup, stale):
    result = response(popup)
    if stale == "request":
        result["request_id"] = -1
    if stale == "scope":
        result["microscope"] = "other"
    if stale == "closed":
        popup._depth_closed = True
    popup._receive_bit_depth(result)
    popup.view.inputs["bit_depth"].set.assert_not_called()


@pytest.mark.parametrize(
    "capability",
    [
        CameraSettingCapability(),
        CameraSettingCapability(12, (12,), False, reason="Fixed"),
    ],
)
def test_unsupported_and_fixed_depth_are_disabled(popup, capability):
    popup._receive_bit_depth(response(popup, capability=capability))
    widget = popup.view.inputs["bit_depth"]
    widget.set.assert_called_with(
        "Unknown" if capability.current_value is None else "12"
    )
    assert widget.__setitem__.call_args.args == ("state", "disabled")


def test_selection_sends_identity_without_optimistic_persistence(popup):
    popup._receive_bit_depth(response(popup))
    popup.view.inputs["bit_depth"].get.return_value = "8"
    popup.set_bit_depth()
    command, request, callback = popup.parent_controller.execute.call_args.args
    assert request["identity"] == (1,)
    assert request["bit_depth"] == 8
    assert popup._depth_pending
    popup.save_camera_settings.assert_not_called()
    popup.close_popup()
    popup.view.popup.destroy.assert_not_called()
    popup._receive_bit_depth(
        response(
            popup, capability=CameraSettingCapability(8, (8, 12, 16), True, reason="")
        )
    )
    popup.view.popup.destroy.assert_called_once()


def test_failed_apply_restores_readback_and_reports_error(popup):
    popup._depth_pending = True
    popup._receive_bit_depth(response(popup, error="Camera rejected the value"))
    popup.view.inputs["bit_depth"].set.assert_called_with("16")
    assert "rejected" in popup.view.variables["bit_depth_status"].set.call_args.args[0]
    assert not popup._depth_pending


def test_acquisition_locks_popup_even_with_late_writable_reply(popup):
    popup.parent_controller.acquire_bar_controller.is_acquiring = True
    popup._receive_bit_depth(response(popup))
    assert popup.view.inputs["bit_depth"].__setitem__.call_args.args == (
        "state",
        "disabled",
    )


def test_real_popup_builds_depth_control_and_switches_microscope(
    dummy_controller, tk_root, monkeypatch
):
    from navigate.view.popups.camera_setting_popup import AdvancedCameraSettingPopup

    monkeypatch.setattr(dummy_controller, "execute", Mock())
    monkeypatch.setattr(
        dummy_controller, "register_event_listener", Mock(), raising=False
    )
    monkeypatch.setattr(
        dummy_controller,
        "acquire_bar_controller",
        SimpleNamespace(is_acquiring=False),
        raising=False,
    )
    view = AdvancedCameraSettingPopup(tk_root)
    c = AdvancedCameraSettingController(view, dummy_controller)
    monkeypatch.setattr(c, "save_camera_settings", Mock())
    try:
        tk_root.update_idletasks()
        assert str(view.inputs["bit_depth"]["state"]) == "disabled"
        c._receive_bit_depth(response(c, microscope=c.current_microscope))
        assert str(view.inputs["bit_depth"]["state"]) == "readonly"
        assert view.inputs["bit_depth"].get() == "16"
        assert view.inputs["bit_depth"].winfo_ismapped()
        choices = list(view.microscope.widget["values"])
        other = next((name for name in choices if name != c.current_microscope), None)
        if other:
            previous_request = c._depth_request_id
            view.microscope.set(other)
            assert c.current_microscope == other
            assert c._depth_request_id > previous_request
            assert str(view.inputs["bit_depth"]["state"]) == "disabled"
    finally:
        c.close_popup()
