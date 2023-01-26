# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

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

from aslm.controller.sub_controllers.stage_controller import StageController
import pytest
import random
from unittest.mock import MagicMock
import numpy as np


@pytest.fixture
def stage_controller(dummy_controller):

    dummy_controller.camera_view_controller = MagicMock()

    return StageController(dummy_controller.view.settings.stage_control_tab, dummy_controller.view, dummy_controller.camera_view_controller.canvas, dummy_controller)


def test_init(stage_controller):
    
    assert isinstance(stage_controller, StageController)


def test_stage_key_press(stage_controller):
    x = round(np.random.random(), 1)
    y = round(np.random.random(), 1)
    increment = round(np.random.random(), 1)
    stage_controller.get_position = MagicMock(return_value={"x": x, "y": y})
    stage_controller.set_position = MagicMock()
    stage_controller.widget_vals['xy_step'].get = MagicMock(return_value=increment)
    event = MagicMock()
    

    # Test 'w' key press
    event.char = 'w'
    stage_controller.stage_key_press(event)
    stage_controller.get_position.assert_called_once()
    y += increment
    stage_controller.set_position.assert_called_with({"x": x, "y": y})
    stage_controller.get_position.reset_mock()
    stage_controller.set_position.reset_mock()
    stage_controller.widget_vals['xy_step'].get.reset_mock()

    # Test 'a' key press
    event.char = 'a'
    stage_controller.stage_key_press(event)
    stage_controller.get_position.assert_called_once()
    x -= increment
    stage_controller.set_position.assert_called_with({"x": x, "y": y})
    stage_controller.get_position.reset_mock()
    stage_controller.set_position.reset_mock()
    stage_controller.widget_vals['xy_step'].get.reset_mock()

    # Test 's' key press
    event.char = 's'
    stage_controller.stage_key_press(event)
    stage_controller.get_position.assert_called_once()
    y -= increment
    stage_controller.set_position.assert_called_with({"x": x, "y": y})
    stage_controller.get_position.reset_mock()
    stage_controller.set_position.reset_mock()
    stage_controller.widget_vals['xy_step'].get.reset_mock()

    # Test 'd' key press
    event.char = 'd'
    stage_controller.stage_key_press(event)
    stage_controller.get_position.assert_called_once()
    x += increment
    stage_controller.set_position.assert_called_with({"x": x, "y": y})
    stage_controller.get_position.reset_mock()
    stage_controller.set_position.reset_mock()
    stage_controller.widget_vals['xy_step'].get.reset_mock()



def test_set_position(stage_controller):
    
    widgets = stage_controller.view.get_widgets()
    for axis in ["x", "y", "z", "theta", "f"]:
        widgets[axis].widget.trigger_focusout_validation = MagicMock()
        
    vals = {}
    for axis in ['x', 'y', 'z', 'theta', 'f']:
        vals[axis] = np.random.randint(0,9)
        stage_controller.widget_vals[axis].set = MagicMock()
    
    stage_controller.view.get_widgets = MagicMock(return_value=widgets)
    stage_controller.show_verbose_info = MagicMock()
    position = {
        "x": np.random.random(),
        "y": np.random.random(),
        "z": np.random.random()
    }
    stage_controller.set_position(position)
    for axis in ["x", "y", "z", "theta", "f"]:
        assert stage_controller.widget_vals[axis].set.called
        widgets[axis].widget.trigger_focusout_validation.assert_called_once()
        assert stage_controller.stage_setting_dict[axis] == position.get(axis, 0)
    stage_controller.show_verbose_info.assert_called_once_with("Set stage position")
    
    
    


def test_get_position(stage_controller):
    import tkinter as tk
    
    vals = {}
    for axis in ['x', 'y', 'z', 'theta', 'f']:
        vals[axis] = np.random.randint(0,9)
        stage_controller.widget_vals[axis].get = MagicMock(return_value=vals[axis])
        
    step_vals = {}
    for axis in ['xy', 'z', 'theta', 'f']:
        step_vals[axis] = np.random.randint(1,9)
        stage_controller.widget_vals[ axis + "_step" ].get = MagicMock(return_value=step_vals[axis])
    
    stage_controller.position_min = {
        "x": 0,
        "y": 0,
        "z": 0,
        "theta": 0,
        "f": 0
    }
    stage_controller.position_max = {
        "x": 10,
        "y": 10,
        "z": 10,
        "theta": 10,
        "f": 10
    }
    position = stage_controller.get_position()
    assert position == {
        "x": vals['x'],
        "y": vals['y'],
        "z": vals['z'],
        "theta": vals['theta'],
        "f": vals['f']
    }

    stage_controller.position_min = {
        "x": 2,
        "y": 2,
        "z": 2,
        "theta": 2,
        "f": 2
    }

    vals = {}
    for axis in ['x', 'y', 'z', 'theta', 'f']:
        vals[axis] = np.random.choice(np.concatenate((np.arange(-9, 0), np.arange(10,20))))
        stage_controller.widget_vals[axis].get = MagicMock(return_value=vals[axis])

    position = stage_controller.get_position()
    assert position is None

    stage_controller.widget_vals["x"].get.side_effect = tk.TclError
    position = stage_controller.get_position()
    assert position is None
    
    # for axis in ['x', 'y', 'z', 'theta', 'f']:
    #     stage_controller.widget_vals[axis].get.reset_mock()
    #     if axis == 'x' or axis == 'y':
    #         stage_controller.widget_vals[ "xy_step" ].get.reset_mock()
    #     else:
    #         stage_controller.widget_vals[ axis + "_step" ].get.reset_mock()


def test_up_btn_handler(stage_controller):

    vals = {}
    for axis in ['x', 'y', 'z', 'theta', 'f']:
        vals[axis] = np.random.randint(1,9)
        stage_controller.widget_vals[axis].get = MagicMock(return_value=vals[axis])
        stage_controller.widget_vals[axis].set = MagicMock()

    step_vals = {}
    for axis in ['xy', 'z', 'theta', 'f']:
        step_vals[axis] = np.random.randint(1,9)
        stage_controller.widget_vals[ axis + "_step" ].get = MagicMock(return_value=step_vals[axis])

    stage_controller.position_max = {
        "x": 10,
        "y": 10,
        "z": 10,
        "theta": 10,
        "f": 10
    }

    # Test for each axis
    for axis in ["x", "y", "z", "theta", "f"]:
        pos = stage_controller.widget_vals[axis].get()
        if axis == 'x' or axis == 'y':
            step = stage_controller.widget_vals["xy_step"].get()
        else:
            step = stage_controller.widget_vals[axis + "_step"].get()
        temp = pos + step
        if temp > stage_controller.position_max[axis]:
            temp = stage_controller.position_max[axis]
        up_btn_handler = stage_controller.up_btn_handler(axis)
        up_btn_handler()
        stage_controller.widget_vals[axis].set.assert_called_once_with(temp)



    # Test for out of limit condition
    for axis in ['x', 'y', 'z', 'theta', 'f']:
        stage_controller.widget_vals[axis].set.reset_mock()
        stage_controller.widget_vals[axis].get.return_value = 10
        up_btn_handler = stage_controller.up_btn_handler(axis)
        up_btn_handler()
        stage_controller.widget_vals[axis].set.assert_not_called()


def test_down_btn_handler(stage_controller):

    vals = {}
    for axis in ['x', 'y', 'z', 'theta', 'f']:
        vals[axis] = np.random.randint(1,9)
        stage_controller.widget_vals[axis].get = MagicMock(return_value=vals[axis])
        stage_controller.widget_vals[axis].set = MagicMock()

    step_vals = {}
    for axis in ['xy', 'z', 'theta', 'f']:
        step_vals[axis] = np.random.randint(1,9)
        stage_controller.widget_vals[ axis + "_step" ].get = MagicMock(return_value=step_vals[axis])

    stage_controller.position_min = {
        "x": 0,
        "y": 0,
        "z": 0,
        "theta": 0,
        "f": 0
    }

    # Test for each axis
    for axis in ["x", "y", "z", "theta", "f"]:
        pos = stage_controller.widget_vals[axis].get()
        if axis == 'x' or axis == 'y':
            step = stage_controller.widget_vals["xy_step"].get()
        else:
            step = stage_controller.widget_vals[axis + "_step"].get()
        temp = pos - step
        if temp < stage_controller.position_min[axis]:
            temp = stage_controller.position_min[axis]
        down_btn_handler = stage_controller.down_btn_handler(axis)
        down_btn_handler()
        stage_controller.widget_vals[axis].set.assert_called_once_with(temp)


    # Test for out of limit condition
    for axis in ['x', 'y', 'z', 'theta', 'f']:
        stage_controller.widget_vals[axis].set.reset_mock()
        stage_controller.widget_vals[axis].get.return_value = 0
        down_btn_handler = stage_controller.down_btn_handler(axis)
        down_btn_handler()
        stage_controller.widget_vals[axis].set.assert_not_called()


def test_zero_btn_handler(stage_controller):

    vals = {}
    for axis in ['x', 'y', 'z', 'theta', 'f']:
        vals[axis] = np.random.randint(1,9)
        stage_controller.widget_vals[axis].get = MagicMock(return_value=vals[axis])
        stage_controller.widget_vals[axis].set = MagicMock()

    # Test for each axis
    for axis in ["x", "y", "z", "theta", "f"]:
        pos = stage_controller.widget_vals[axis].get()
        zero_btn_handler = stage_controller.zero_btn_handler(axis)
        zero_btn_handler()
        stage_controller.widget_vals[axis].set.assert_called_once_with(0)


def test_position_callback(stage_controller):
    
    stage_controller.show_verbose_info = MagicMock()
    
    vals = {}
    widgets = stage_controller.view.get_widgets()
    for axis in ['x', 'y', 'z', 'theta', 'f']:
        vals[axis] = np.random.randint(1,9)
        stage_controller.widget_vals[axis].get = MagicMock(return_value=vals[axis])
        stage_controller.widget_vals[axis].set = MagicMock()
        widgets[axis].widget.set(vals[axis])
        widgets[axis].widget.trigger_focusout_validation = MagicMock()
        
    stage_controller.position_min = {
        "x": 0,
        "y": 0,
        "z": 0,
        "theta": 0,
        "f": 0
    }
    
    stage_controller.position_max = {
        "x": 10,
        "y": 10,
        "z": 10,
        "theta": 10,
        "f": 10
    }
    
    
    stage_controller.parent_controller.execute = MagicMock()
    stage_controller.stage_setting_dict = {}

    for axis in ['x', 'y', 'z', 'theta', 'f']:
        callback = stage_controller.position_callback(axis)

        # Test case 1: Position variable is not a number
        widgets[axis].widget.get = MagicMock(return_value='a')
        callback()
        assert not stage_controller.parent_controller.execute.called

        # Test case 2: Position variable is within limits
        widgets[axis].widget.get = MagicMock(return_value=vals[axis])
        callback()
        assert stage_controller.parent_controller.execute.called
        assert stage_controller.stage_setting_dict[axis] == vals[axis]
        stage_controller.parent_controller.execute.reset_mock()

        # Test case 3: Position variable is outside limits
        widgets[axis].widget.get = MagicMock(return_value=11)
        callback()
        assert not stage_controller.parent_controller.execute.called
   
        
    