# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
from unittest.mock import MagicMock, call
import numpy as np

AXES = ["x", "y", "z", "theta", "f"]
CAXES = ["xy", "z", "theta", "f"]


def pos_dict(v, axes=AXES):
    return {k: v for k in axes}


@pytest.fixture
def stage_controller(dummy_controller):
    from navigate.controller.sub_controllers.stage_controller import StageController

    dummy_controller.camera_view_controller = MagicMock()

    return StageController(
        dummy_controller.view.settings.stage_control_tab,
        dummy_controller.view,
        dummy_controller.camera_view_controller.canvas,
        dummy_controller,
    )

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
        assert stage_controller.widget_vals[axis].get() == position[axis]
        assert widgets[axis].widget.trigger_focusout_validation.called
        assert stage_controller.stage_setting_dict[axis] == position.get(axis, 0)
    stage_controller.show_verbose_info.assert_has_calls([call("Stage position changed"), call("Set stage position")])

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
        assert stage_controller.widget_vals[axis].get() == position[axis]
        widgets[axis].widget.trigger_focusout_validation.assert_called_once()
        assert stage_controller.stage_setting_dict[axis] == position.get(axis, 0)
    stage_controller.show_verbose_info.assert_has_calls([call("Set stage position")])
    assert call("Stage position changed") not in stage_controller.show_verbose_info.mock_calls


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


def test_zero_btn_handler(stage_controller):

    vals = {}
    for axis in AXES:
        vals[axis] = np.random.randint(1, 9)
        stage_controller.widget_vals[axis].get = MagicMock(return_value=vals[axis])
        stage_controller.widget_vals[axis].set = MagicMock()
        stage_controller.widget_vals[axis].get()
        stage_controller.zero_btn_handler(axis)()
        stage_controller.widget_vals[axis].set.assert_called_once_with(0)


def test_stop_button_handler(stage_controller):

    stage_controller.view.after = MagicMock()

    stage_controller.stop_button_handler()

    stage_controller.view.after.assert_called_once()


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
