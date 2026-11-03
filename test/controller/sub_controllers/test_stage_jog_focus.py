"""Explicit jogs must reach the model even when Tk has no keyboard focus."""

from types import SimpleNamespace
from unittest.mock import MagicMock
import tkinter as tk

import pytest

from navigate.controller.sub_controllers.stages import StageController


@pytest.fixture
def jog_controller():
    interpreter = tk.Tcl()
    controller = object.__new__(StageController)
    controller.widget_vals = {
        "f": tk.StringVar(master=interpreter, value="75"),
        "f_step": tk.DoubleVar(master=interpreter, value=4),
    }
    controller.flip_flags = {"f": False}
    controller.stage_limits = True
    controller.position_min = {"f": -75}
    controller.position_max = {"f": 75}
    controller.event_id = {"f": None}
    controller.stage_setting_dict = {}
    controller.view = MagicMock()
    controller.view.focus_get.return_value = None
    commands = []
    controller.parent_controller = SimpleNamespace(
        execute=lambda *args: commands.append(args)
    )
    return controller, commands


@pytest.mark.parametrize(
    "direction,large,start,expected",
    [
        ("down", False, 75, 71),
        ("up", False, 71, 75),
        ("down", True, 75, 55),
        ("up", True, 55, 75),
    ],
)
def test_jog_without_keyboard_focus_dispatches_displayed_target(
    jog_controller, direction, large, start, expected
):
    controller, commands = jog_controller
    controller.widget_vals["f"].set(start)

    getattr(controller, f"{direction}_btn_handler")("f", large_step=large)()

    assert float(controller.widget_vals["f"].get()) == expected
    assert controller.view.after.call_count == 1
    assert commands == []  # Still debounce explicit jogs.
    _, callback = controller.view.after.call_args.args
    callback()
    assert commands == [("stage", expected, "f")]


def test_unfocused_focusout_does_not_schedule_a_move(jog_controller):
    controller, commands = jog_controller

    controller.position_callback("f")()

    controller.view.after.assert_not_called()
    assert commands == []


@pytest.mark.parametrize("direction,start", [("down", -75), ("up", 75)])
def test_unfocused_jog_at_limit_does_not_schedule_a_move(
    jog_controller, direction, start
):
    controller, commands = jog_controller
    controller.widget_vals["f"].set(start)

    getattr(controller, f"{direction}_btn_handler")("f")()

    assert float(controller.widget_vals["f"].get()) == start
    controller.view.after.assert_not_called()
    assert commands == []
