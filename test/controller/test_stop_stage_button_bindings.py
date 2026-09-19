# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Headless regression tests for both visible Stop Stage buttons."""

from types import SimpleNamespace
from unittest.mock import patch

from navigate.controller.controller import Controller
from navigate.controller.sub_controllers.stages import StageController


class _InvokableButton:
    """Store and invoke a configured callback without constructing a Tk widget."""

    def __init__(self):
        self.command = None

    def configure(self, *, command=None, **_options):
        self.command = command

    config = configure

    def invoke(self):
        if self.command is None:
            raise RuntimeError("button has no configured command")
        self.command()


def _build_headless_controller():
    stage_stop_button = _InvokableButton()
    stage_view = SimpleNamespace(
        add_additional_stage=lambda _axis: None,
        after=lambda _delay, callback: callback(),
        get_buttons=lambda: {
            "stop": stage_stop_button,
            "joystick": _InvokableButton(),
        },
        get_variables=lambda: {},
        stack_shortcuts=SimpleNamespace(
            set_start_button=_InvokableButton(),
            set_end_button=_InvokableButton(),
        ),
    )
    acquisition_stop_button = _InvokableButton()
    executed_commands = []
    controller = SimpleNamespace(
        channels_tab_controller=SimpleNamespace(
            update_start_position=lambda: None,
            update_end_position=lambda: None,
        ),
        configuration={
            "configuration": {
                "microscopes": {"scope": {"stage": {"joystick_axes": []}}}
            },
            "experiment": {"StageParameters": {}},
        },
        configuration_controller=SimpleNamespace(
            microscope_name="scope",
            stage_axes=[],
            all_stage_axes=[],
        ),
        execute=executed_commands.append,
        view=SimpleNamespace(
            acquire_bar=SimpleNamespace(stop_stage=acquisition_stop_button)
        ),
    )

    # These callbacks initialize unrelated stage state and require full GUI widgets.
    with patch.multiple(
        StageController,
        bind_position_callbacks=lambda _self: None,
        initialize=lambda _self: None,
        set_hover_descriptions=lambda _self: None,
    ):
        controller.stage_controller = StageController(stage_view, controller)
    Controller.update_acquire_control(controller)

    return controller, stage_stop_button, acquisition_stop_button, executed_commands


def test_stage_control_stop_button_click_dispatches_stop_stage():
    _, stage_stop_button, _, executed_commands = _build_headless_controller()

    stage_stop_button.invoke()

    assert executed_commands == ["stop_stage"]


def test_acquisition_bar_stop_button_click_dispatches_stop_stage():
    _, _, acquisition_stop_button, executed_commands = _build_headless_controller()

    acquisition_stop_button.invoke()

    assert executed_commands == ["stop_stage"]
