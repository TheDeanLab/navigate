# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Callback tests for the resolution-change recovery popup."""

from unittest.mock import MagicMock


def test_popup_uses_approved_choices_and_disables_unavailable_return():
    from unittest.mock import call, patch

    from navigate.view.popups.resolution_change_popup import (
        ResolutionChangeCancelledPopup,
    )

    popup_shell = MagicMock()
    popup_shell.get_frame.return_value = MagicMock()
    buttons = [MagicMock(), MagicMock()]
    with (
        patch(
            "navigate.view.popups.resolution_change_popup.PopUp",
            return_value=popup_shell,
        ) as popup_class,
        patch("navigate.view.popups.resolution_change_popup.ttk.Label"),
        patch(
            "navigate.view.popups.resolution_change_popup.ttk.Button",
            side_effect=buttons,
        ) as button_class,
    ):
        ResolutionChangeCancelledPopup(
            root=MagicMock(),
            keep_command=MagicMock(),
            return_command=MagicMock(),
            return_enabled=False,
        )

    assert popup_class.call_args.args[1] == "Resolution Change Cancelled"
    assert button_class.call_args_list == [
        call(
            popup_shell.get_frame.return_value,
            text="Keep Current Position",
            command=button_class.call_args_list[0].kwargs["command"],
        ),
        call(
            popup_shell.get_frame.return_value,
            text="Return to Previous Position",
            command=button_class.call_args_list[1].kwargs["command"],
            state="disabled",
        ),
    ]
    popup_shell.protocol.assert_called_once()
    assert popup_shell.protocol.call_args.args[0] == "WM_DELETE_WINDOW"
    popup_shell.bind.assert_called_once()
    assert popup_shell.bind.call_args.args[0] == "<Escape>"


def test_popup_close_keeps_current_position():
    from navigate.view.popups.resolution_change_popup import (
        ResolutionChangeCancelledPopup,
    )

    popup = ResolutionChangeCancelledPopup.__new__(ResolutionChangeCancelledPopup)
    popup.popup = MagicMock()
    popup._keep_command = MagicMock()

    popup._keep()

    popup.popup.dismiss.assert_called_once_with()
    popup._keep_command.assert_called_once_with()


def test_popup_return_dismisses_before_starting_motion():
    from navigate.view.popups.resolution_change_popup import (
        ResolutionChangeCancelledPopup,
    )

    order = []
    popup = ResolutionChangeCancelledPopup.__new__(ResolutionChangeCancelledPopup)
    popup.popup = MagicMock(dismiss=lambda: order.append("dismiss"))
    popup._return_command = lambda: order.append("return")

    popup._return()

    assert order == ["dismiss", "return"]
