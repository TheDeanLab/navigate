# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import pytest
import tkinter as tk
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call
import numpy as np
import yaml

AXES = ["x", "y", "z", "theta", "f"]
CAXES = ["xy", "z", "theta", "f"]


def pos_dict(v, axes=AXES):
    return {k: v for k in axes}


def hover_button():
    return SimpleNamespace(hover=SimpleNamespace(setdescription=MagicMock()))


@pytest.fixture
def initialize_controller():
    """Build an isolated controller without creating a Tk window."""
    from navigate.controller.sub_controllers.stages import StageController

    def build(axes, gui_settings, saved_steps=None, limits=(-100, 200)):
        config = SimpleNamespace(
            stage_axes=axes,
            all_stage_axes=axes,
            microscope_name="scope",
            gui_setting=gui_settings,
            stage_flip_flags={},
            stage_home_position={},
            get_stage_position_limits=lambda suffix: dict.fromkeys(
                axes, limits[0] if suffix == "_min" else limits[1]
            ),
        )
        widgets = {axis: MagicMock() for axis in axes}
        widgets.update(
            {
                f"{'xy' if axis in ('x', 'y') else axis}_step": MagicMock()
                for axis in axes
            }
        )
        controller = object.__new__(StageController)
        controller.parent_controller = SimpleNamespace(
            configuration_controller=config,
            configuration={"configuration": {"microscopes": {"scope": {"stage": {}}}}},
        )
        controller.stage_setting_dict = {"scope": saved_steps or {}}
        controller.joystick_axes = []
        controller.disable_synthetic_stages = MagicMock()
        controller.view = MagicMock()
        controller.view.get_widgets.return_value = widgets
        return controller, widgets

    return build


@pytest.mark.parametrize("axis", [*AXES, "aux"])
def test_initialize_uses_axis_gui_step_settings(initialize_controller, axis):
    step_key = f"{'xy' if axis in ('x', 'y') else axis}_step"
    controller, widgets = initialize_controller(
        [axis],
        {"stage_movement": {step_key: {"step": 0.125, "min": 0.025}}},
        {step_key: 50},
    )

    controller.initialize()

    widgets[step_key].widget.configure.assert_any_call(increment=0.125)
    widgets[step_key].widget.configure.assert_any_call(from_=0.025)
    widgets[step_key].set.assert_called_once_with(50)


@pytest.mark.parametrize(
    "gui_settings, saved_steps, expected_min, expected_increment, expected_value",
    [
        ({}, {"z_step": 50}, 0.01, 5, 50),
        ({"stage_movement": {}}, {"z_step": 50}, 0.01, 5, 50),
        (
            {"stage_movement": {"xy_step": {"step": 0.25, "min": 0.1}}},
            {"z_step": 50},
            0.01,
            5,
            50,
        ),
        ({"stage_movement": {"z_step": {}}}, {}, 0.01, 1, 10),
        ({}, {"z_step": 0.5}, 0.01, 1, 0.5),
        (
            {"stage_movement": {"z_step": {"step": 0.25}}},
            {"z_step": 50},
            0.01,
            0.25,
            50,
        ),
        (
            {"stage_movement": {"z_step": {"min": 0.05}}},
            {"z_step": 50},
            0.05,
            5,
            50,
        ),
    ],
    ids=[
        "missing-section",
        "missing-axis",
        "other-axis-only",
        "empty-axis",
        "small-saved-step",
        "increment-only",
        "minimum-only",
    ],
)
def test_initialize_step_settings_fallbacks(
    initialize_controller,
    gui_settings,
    saved_steps,
    expected_min,
    expected_increment,
    expected_value,
):
    controller, widgets = initialize_controller(["z"], gui_settings, saved_steps)

    controller.initialize()

    widgets["z_step"].widget.configure.assert_any_call(from_=expected_min)
    widgets["z_step"].widget.configure.assert_any_call(increment=expected_increment)
    widgets["z_step"].set.assert_called_once_with(expected_value)


@pytest.mark.parametrize("limits", [(-100, 200), (100, 300), (-300, -100), (0, 200)])
def test_initialize_step_maximum_uses_full_travel_range(initialize_controller, limits):
    controller, widgets = initialize_controller(["z"], {}, limits=limits)

    controller.initialize()

    widgets["z_step"].widget.configure.assert_any_call(to=limits[1] - limits[0])
    assert widgets["z"].widget.min == limits[0]
    assert widgets["z"].widget.max == limits[1]


def test_initialize_refreshes_independent_axis_settings(initialize_controller):
    settings = {
        "stage_movement": {
            "xy_step": {"step": 0.25, "min": 0.05},
            "z_step": {"step": 0.5, "min": 0.1},
        }
    }
    controller, widgets = initialize_controller(["x", "y", "z"], settings)
    controller.initialize()
    widgets["xy_step"].widget.configure.assert_any_call(increment=0.25)
    widgets["z_step"].widget.configure.assert_any_call(increment=0.5)

    settings["stage_movement"]["xy_step"] = {"step": 0.125, "min": 0.025}
    widgets["xy_step"].reset_mock()
    widgets["z_step"].reset_mock()
    controller.initialize()

    widgets["xy_step"].widget.configure.assert_any_call(increment=0.125)
    widgets["xy_step"].widget.configure.assert_any_call(from_=0.025)
    widgets["z_step"].widget.configure.assert_any_call(increment=0.5)
    widgets["z_step"].widget.configure.assert_any_call(from_=0.1)


def test_initialize_uses_shipped_gui_step_defaults(initialize_controller):
    import navigate

    config_path = Path(navigate.__file__).parent / "config" / "gui_configuration.yml"
    with config_path.open() as config_file:
        settings = yaml.safe_load(config_file)
    for axis in CAXES:
        assert settings["stage_movement"][f"{axis}_step"] == {"step": 1, "min": 0.01}
    controller, widgets = initialize_controller(
        AXES, settings, {f"{axis}_step": 50 for axis in CAXES}
    )

    controller.initialize()

    for axis in CAXES:
        widgets[f"{axis}_step"].widget.configure.assert_any_call(increment=1)
        widgets[f"{axis}_step"].widget.configure.assert_any_call(from_=0.01)
        widgets[f"{axis}_step"].set.assert_called_with(50)


@pytest.mark.parametrize("axis", [*CAXES, "aux"])
@pytest.mark.parametrize("value", [0.01, 0.25, 1.75, 10])
def test_update_step_size_preserves_fractional_values(
    initialize_controller, axis, value
):
    controller, _ = initialize_controller(["z"], {})
    controller.parent_controller.configuration["experiment"] = {
        "MicroscopeState": {"microscope_name": "scope"}
    }
    controller.stage_setting_dict["other_scope"] = {f"{axis}_step": 20}
    controller.widget_vals = {
        f"{axis}_step": MagicMock(get=MagicMock(return_value=value))
    }
    controller.set_hover_descriptions = MagicMock()

    controller.update_step_size_handler(axis)("variable", "", "write")

    assert controller.stage_setting_dict["scope"][f"{axis}_step"] == value
    assert controller.stage_setting_dict["other_scope"][f"{axis}_step"] == 20
    controller.set_hover_descriptions.assert_called_once_with()


@pytest.mark.parametrize("error", [ValueError("invalid"), tk.TclError("empty")])
def test_update_step_size_ignores_invalid_input(initialize_controller, error):
    controller, _ = initialize_controller(["z"], {}, {"z_step": 0.25})
    controller.parent_controller.configuration["experiment"] = {
        "MicroscopeState": {"microscope_name": "scope"}
    }
    controller.widget_vals = {"z_step": MagicMock(get=MagicMock(side_effect=error))}
    controller.set_hover_descriptions = MagicMock()

    controller.update_step_size_handler("z")()

    assert controller.stage_setting_dict["scope"]["z_step"] == 0.25
    controller.set_hover_descriptions.assert_not_called()


def test_fractional_step_survives_reinitialization(stage_controller):
    controller = stage_controller
    controller.widget_vals["z_step"].set(0.25)
    microscope_name = controller.parent_controller.configuration["experiment"][
        "MicroscopeState"
    ]["microscope_name"]
    assert controller.stage_setting_dict[microscope_name]["z_step"] == 0.25

    controller.initialize()

    assert controller.widget_vals["z_step"].get() == 0.25
    controller.widget_vals["z"].set(0)
    controller.position_callback = MagicMock(return_value=MagicMock())
    controller.flip_flags["z"] = False
    controller.up_btn_handler("z")()
    assert float(controller.widget_vals["z"].get()) == 0.25
    controller.down_btn_handler("z", large_step=True)()
    assert float(controller.widget_vals["z"].get()) == -1.0


def test_set_hover_descriptions_without_exec():
    from navigate.controller.sub_controllers.stages import StageController

    controller = object.__new__(StageController)
    controller.stage_axes = AXES
    controller.widget_vals = {
        "xy_step": MagicMock(get=MagicMock(return_value=10.0)),
        "z_step": MagicMock(get=MagicMock(return_value=20.0)),
        "theta_step": MagicMock(get=MagicMock(return_value=30.0)),
        "f_step": MagicMock(get=MagicMock(return_value=40.0)),
    }
    controller.view = SimpleNamespace(
        xy_frame=SimpleNamespace(
            large_up_x_btn=hover_button(),
            large_down_x_btn=hover_button(),
            up_x_btn=hover_button(),
            down_x_btn=hover_button(),
            large_up_y_btn=hover_button(),
            large_down_y_btn=hover_button(),
            up_y_btn=hover_button(),
            down_y_btn=hover_button(),
        ),
        z_frame=SimpleNamespace(
            large_up_btn=hover_button(),
            large_down_btn=hover_button(),
            up_btn=hover_button(),
            down_btn=hover_button(),
        ),
        theta_frame=SimpleNamespace(
            large_up_btn=hover_button(),
            large_down_btn=hover_button(),
            up_btn=hover_button(),
            down_btn=hover_button(),
        ),
        f_frame=SimpleNamespace(
            large_up_btn=hover_button(),
            large_down_btn=hover_button(),
            up_btn=hover_button(),
            down_btn=hover_button(),
        ),
        position_frame=SimpleNamespace(
            inputs={
                axis: SimpleNamespace(
                    widget=SimpleNamespace(
                        hover=SimpleNamespace(setdescription=MagicMock())
                    )
                )
                for axis in AXES
            }
        ),
        stack_shortcuts=SimpleNamespace(
            set_start_button=hover_button(),
            set_end_button=hover_button(),
        ),
        stop_frame=SimpleNamespace(joystick_btn=hover_button()),
    )

    controller.set_hover_descriptions()

    controller.view.xy_frame.large_up_x_btn.hover.setdescription.assert_called_once()


@pytest.fixture
def stage_controller(dummy_controller):
    from navigate.controller.sub_controllers.stages import StageController

    dummy_controller.camera_view_controller = MagicMock()

    stage_controller = StageController(
        dummy_controller.view.settings.stage_control_tab,
        dummy_controller,
    )

    dummy_controller.view.settings.stage_control_tab.focus_get = MagicMock(
        return_value=True
    )

    return stage_controller


# test before set position variables to MagicMock()
def test_set_position(stage_controller):

    widgets = stage_controller.view.get_widgets()
    vals = {}
    for axis in AXES:
        widgets[axis].widget.trigger_focusout_validation = MagicMock()
        vals[axis] = np.random.randint(0, 9)

    stage_controller.view.get_widgets = MagicMock(return_value=widgets)
    stage_controller.show_verbose_info = MagicMock()
    position = {
        "x": np.random.random(),
        "y": np.random.random(),
        "z": np.random.random(),
    }
    stage_controller.set_position(position)
    for axis in position.keys():
        assert float(stage_controller.widget_vals[axis].get()) == position[axis]
        assert widgets[axis].widget.trigger_focusout_validation.called
        assert stage_controller.stage_setting_dict[axis] == position.get(axis, 0)
    stage_controller.show_verbose_info.assert_has_calls(
        [call("Stage position changed"), call("Set stage position")]
    )


def test_set_position_silent(stage_controller):

    widgets = stage_controller.view.get_widgets()
    vals = {}
    for axis in AXES:
        widgets[axis].widget.trigger_focusout_validation = MagicMock()
        vals[axis] = np.random.randint(0, 9)

    stage_controller.view.get_widgets = MagicMock(return_value=widgets)
    stage_controller.show_verbose_info = MagicMock()
    position = {
        "x": np.random.random(),
        "y": np.random.random(),
        "z": np.random.random(),
    }
    stage_controller.set_position_silent(position)
    for axis in position.keys():
        assert float(stage_controller.widget_vals[axis].get()) == position[axis]
        widgets[axis].widget.trigger_focusout_validation.assert_called_once()
        assert stage_controller.stage_setting_dict[axis] == position.get(axis, 0)
    stage_controller.show_verbose_info.assert_has_calls([call("Set stage position")])
    assert (
        call("Stage position changed")
        not in stage_controller.show_verbose_info.mock_calls
    )


@pytest.mark.parametrize(
    "flip_x, flip_y",
    [(False, False), (True, False), (True, True), (False, True), (True, True)],
)
def test_stage_key_press(stage_controller, flip_x, flip_y):
    microscope_name = (
        stage_controller.parent_controller.configuration_controller.microscope_name
    )
    stage_config = stage_controller.parent_controller.configuration["configuration"][
        "microscopes"
    ][microscope_name]["stage"]
    stage_config["flip_x"] = flip_x
    stage_config["flip_y"] = flip_y
    stage_controller.initialize()
    x = round(np.random.random(), 1)
    y = round(np.random.random(), 1)
    increment = round(np.random.random() + 1, 1)
    stage_controller.widget_vals["xy_step"].get = MagicMock(return_value=increment)
    stage_controller.widget_vals["x"].get = MagicMock(return_value=x)
    stage_controller.widget_vals["x"].set = MagicMock()
    stage_controller.widget_vals["y"].get = MagicMock(return_value=y)
    stage_controller.widget_vals["y"].set = MagicMock()
    event = MagicMock()

    axes_map = {"w": "y", "a": "x", "s": "y", "d": "x"}

    for char, xs, ys in zip(
        ["w", "a", "s", "d"],
        [0, -increment, 0, increment],
        [increment, 0, -increment, 0],
    ):
        event.char = char
        # <a> instead of <Control+a>
        event.state = 0
        axis = axes_map[char]
        if axis == "x":
            temp = x + xs * (-1 if flip_x else 1)
        else:
            temp = y + ys * (-1 if flip_y else 1)
        stage_controller.stage_key_press(event)
        stage_controller.widget_vals[axis].set.assert_called_once_with(temp)
        stage_controller.widget_vals[axis].set.reset_mock()
        stage_controller.widget_vals[axis].get.reset_mock()
        stage_controller.widget_vals["xy_step"].get.reset_mock()

    stage_config["flip_x"] = False
    stage_config["flip_y"] = False


def test_get_position(stage_controller):
    import tkinter as tk

    vals = {}
    for axis in AXES:
        vals[axis] = np.random.randint(0, 9)
        stage_controller.widget_vals[axis].get = MagicMock(return_value=vals[axis])

    step_vals = {}
    for axis in CAXES:
        step_vals[axis] = np.random.randint(1, 9)
        stage_controller.widget_vals[axis + "_step"].get = MagicMock(
            return_value=step_vals[axis]
        )

    stage_controller.position_min = pos_dict(0)
    stage_controller.position_max = pos_dict(10)
    position = stage_controller.get_position()
    assert position == {k: vals[k] for k in AXES}

    stage_controller.position_min = pos_dict(2)

    vals = {}
    for axis in AXES:
        vals[axis] = np.random.choice(
            np.concatenate((np.arange(-9, 0), np.arange(10, 20)))
        )
        stage_controller.widget_vals[axis].get = MagicMock(return_value=vals[axis])

    position = stage_controller.get_position()
    assert position is None

    stage_controller.widget_vals["x"].get.side_effect = tk.TclError
    position = stage_controller.get_position()
    assert position is None


@pytest.mark.parametrize(
    "flip_x, flip_y, flip_z",
    [
        (False, False, False),
        (True, False, False),
        (True, True, False),
        (False, True, True),
        (True, True, True),
    ],
)
def test_up_btn_handler(stage_controller, flip_x, flip_y, flip_z):
    microscope_name = (
        stage_controller.parent_controller.configuration_controller.microscope_name
    )
    stage_config = stage_controller.parent_controller.configuration["configuration"][
        "microscopes"
    ][microscope_name]["stage"]
    stage_config["flip_x"] = flip_x
    stage_config["flip_y"] = flip_y
    stage_config["flip_z"] = flip_z
    stage_controller.initialize()
    flip_flags = (
        stage_controller.parent_controller.configuration_controller.stage_flip_flags
    )

    vals = {}
    for axis in AXES:
        vals[axis] = np.random.randint(1, 9)
        stage_controller.widget_vals[axis].get = MagicMock(return_value=vals[axis])
        stage_controller.widget_vals[axis].set = MagicMock()

    step_vals = {}
    for axis in CAXES:
        step_vals[axis] = np.random.randint(1, 9)
        stage_controller.widget_vals[axis + "_step"].get = MagicMock(
            return_value=step_vals[axis]
        )

    stage_controller.position_max = pos_dict(10)

    # Test for each axis
    for axis in AXES:
        pos = stage_controller.widget_vals[axis].get()
        if axis == "x" or axis == "y":
            step = stage_controller.widget_vals["xy_step"].get()
        else:
            step = stage_controller.widget_vals[axis + "_step"].get()
        temp = pos + step * (-1 if flip_flags[axis] else 1)
        if temp > stage_controller.position_max[axis]:
            temp = stage_controller.position_max[axis]
        stage_controller.up_btn_handler(axis)()
        stage_controller.widget_vals[axis].set.assert_called_once_with(temp)

    # Test for out of limit condition
    for axis in AXES:
        stage_controller.widget_vals[axis].set.reset_mock()
        stage_controller.widget_vals[axis].get.return_value = 10
        stage_controller.up_btn_handler(axis)()
        if flip_flags[axis] is False:
            stage_controller.widget_vals[axis].set.assert_not_called()

    stage_config["flip_x"] = False
    stage_config["flip_y"] = False
    stage_config["flip_z"] = False


@pytest.mark.parametrize(
    "flip_x, flip_y, flip_z",
    [
        (False, False, False),
        (True, False, False),
        (True, True, False),
        (False, True, True),
        (True, True, True),
    ],
)
def test_down_btn_handler(stage_controller, flip_x, flip_y, flip_z):
    microscope_name = (
        stage_controller.parent_controller.configuration_controller.microscope_name
    )
    stage_config = stage_controller.parent_controller.configuration["configuration"][
        "microscopes"
    ][microscope_name]["stage"]
    stage_config["flip_x"] = flip_x
    stage_config["flip_y"] = flip_y
    stage_config["flip_z"] = flip_z
    stage_controller.initialize()
    flip_flags = (
        stage_controller.parent_controller.configuration_controller.stage_flip_flags
    )
    vals = {}
    for axis in AXES:
        vals[axis] = np.random.randint(1, 9)
        stage_controller.widget_vals[axis].get = MagicMock(return_value=vals[axis])
        stage_controller.widget_vals[axis].set = MagicMock()

    step_vals = {}
    for axis in CAXES:
        step_vals[axis] = np.random.randint(1, 9)
        stage_controller.widget_vals[axis + "_step"].get = MagicMock(
            return_value=step_vals[axis]
        )

    stage_controller.position_min = pos_dict(0)

    # Test for each axis
    for axis in AXES:
        pos = stage_controller.widget_vals[axis].get()
        if axis == "x" or axis == "y":
            step = stage_controller.widget_vals["xy_step"].get()
        else:
            step = stage_controller.widget_vals[axis + "_step"].get()
        temp = pos - step * (-1 if flip_flags[axis] else 1)
        if temp < stage_controller.position_min[axis]:
            temp = stage_controller.position_min[axis]
        stage_controller.down_btn_handler(axis)()
        stage_controller.widget_vals[axis].set.assert_called_once_with(temp)

    # Test for out of limit condition
    for axis in ["x", "y", "z", "theta", "f"]:
        stage_controller.widget_vals[axis].set.reset_mock()
        stage_controller.widget_vals[axis].get.return_value = 0
        stage_controller.down_btn_handler(axis)()
        if flip_flags[axis] is False:
            stage_controller.widget_vals[axis].set.assert_not_called()

    stage_config["flip_x"] = False
    stage_config["flip_y"] = False
    stage_config["flip_z"] = False


def test_stop_button_handler_dispatches_immediately():
    from navigate.controller.sub_controllers.stages import StageController

    parent_controller = MagicMock()
    stage_controller = SimpleNamespace(parent_controller=parent_controller)

    StageController.stop_button_handler(stage_controller)

    parent_controller.execute.assert_called_once_with("stop_stage")


def test_position_callback(stage_controller):

    stage_controller.show_verbose_info = MagicMock()

    stage_controller.view.after = MagicMock()

    vals = {}
    widgets = stage_controller.view.get_widgets()
    for axis in AXES:
        vals[axis] = np.random.randint(1, 9)
        stage_controller.widget_vals[axis].get = MagicMock(return_value=vals[axis])
        stage_controller.widget_vals[axis].set = MagicMock()
        widgets[axis].widget.set(vals[axis])
        widgets[axis].widget.trigger_focusout_validation = MagicMock()

    stage_controller.position_min = pos_dict(0)
    stage_controller.position_max = pos_dict(10)
    stage_controller.stage_setting_dict = {}

    for axis in AXES:

        callback = stage_controller.position_callback(axis)

        # Test case 1: Position variable is within limits
        widgets[axis].widget.get = MagicMock(return_value=vals[axis])
        callback()
        stage_controller.view.after.assert_called()
        stage_controller.view.after.reset_mock()
        assert stage_controller.stage_setting_dict[axis] == vals[axis]

        # Test case 2: Position variable is outside limits
        widgets[axis].widget.get = MagicMock(return_value=11)
        callback()
        stage_controller.view.after.assert_called_once()
        stage_controller.view.after.reset_mock()
