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
import tkinter as tk


from aslm.controller.sub_controllers.gui_controller import GUIController
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class StageController(GUIController):
    """StageController

    This class is the controller for the stage GUI. It handles the stage movement
    and the stage limits. It also handles the stage movement buttons and the
    stage movement limits.

    Parameters
    ----------
    view : aslm.view.stage_view.StageView
        The stage view
    main_view : tkinter.Tk
        The main view of the microscope
    canvas : tkinter.Canvas
        The canvas of the microscope
    parent_controller : aslm.controller.microscope_controller.MicroscopeController
        The parent controller of the stage controller

    Attributes
    ----------
    main_view : tkinter.Tk
        The main view of the microscope
    canvas : tkinter.Canvas
        The canvas of the microscope
    stage_setting_dict : dict
        The stage settings dictionary
    event_id : dict
        The event id dictionary
    position_min : dict
        The minimum position dictionary
    position_max : dict
        The maximum position dictionary
    widget_vals : dict
        The widget values dictionary
    position_callback_traces : dict
        The position callback traces dictionary
    position_callbacks_bound : bool
        The position callbacks bound boolean
    joystick_is_on : bool
        The joystick on/off boolean
    joystick_axes : list
        The joystick axes

    Methods
    -------
    bind_position_callbacks()
        Bind the position callbacks
    down_btn_handler(axis)
        The down button handler
    get_position()
        Get the position
    initialize()
        Initialize the stage limits of steps and positions
    populate_experiment_values()
        Populate the experiment values
    position_callback(axis, position)
        The position callback
    set_position(position)
        Set the position
    set_position_silent(position)
        Set the position silently
    stage_key_press(event)
        The stage key press
    stop_button_handler()
        The stop button handler
    joystick_button_handler()
        The enable/disable joystick button
    unbind_position_callbacks()
        Unbind the position callbacks
    up_btn_handler(axis)
        The up button handler
    xy_zero_btn_handler()
        The xy zero button handler
    zero_btn_handler(axis)
        The zero button handler
    """

    def __init__(self, view, main_view, canvas, parent_controller):
        super().__init__(view, parent_controller)

        self.default_microscope = (
            f"{self.parent_controller.configuration_controller.microscope_name}"
        )
        self.joystick_is_on = False
        self.joystick_axes = self.parent_controller.configuration["configuration"][
            "microscopes"
        ][self.default_microscope]["stage"].get("joystick_axes", [])

        self.main_view = main_view
        self.canvas = canvas

        self.stage_setting_dict = self.parent_controller.configuration["experiment"][
            "StageParameters"
        ]

        self.event_id = {"x": None, "y": None, "z": None, "theta": None, "f": None}

        # stage movement limits
        self.position_min = {}
        self.position_max = {}

        # variables
        self.widget_vals = self.view.get_variables()

        # gui event bind
        buttons = self.view.get_buttons()
        for k in buttons:
            if k[:2] == "up":
                buttons[k].configure(command=self.up_btn_handler(k[3:-4]))
            elif k[:4] == "down":
                buttons[k].configure(command=self.down_btn_handler(k[5:-4]))
            elif k[5:-4] == "xy":
                buttons[k].configure(command=self.xy_zero_btn_handler())
            elif k.startswith("zero"):
                buttons[k].configure(command=self.zero_btn_handler(k[5:-4]))

        buttons["stop"].configure(command=self.stop_button_handler)
        buttons["joystick"].configure(command=self.joystick_button_handler)
        self.position_callback_traces = {}
        self.position_callbacks_bound = False
        self.bind_position_callbacks()
        self.stage_limits = True
        self.initialize()

   
    def initialize(self):
        """Initialize the Stage limits of steps and positions

        Returns
        -------
        None

        """
        config = self.parent_controller.configuration_controller
        self.position_min = config.get_stage_position_limits("_min")
        self.position_max = config.get_stage_position_limits("_max")

        widgets = self.view.get_widgets()
        step_dict = config.stage_step
        for axis in ["x", "y", "z", "theta", "f"]:
            widgets[axis].widget.min = self.position_min[axis]
            widgets[axis].widget.max = self.position_max[axis]
            if axis == "x" or axis == "y":
                step_axis = "xy"
            else:
                step_axis = axis
            # the minimum step should be non-zero and non-negative.
            widgets[step_axis + "_step"].widget.configure(from_=1)
            widgets[step_axis + "_step"].widget.configure(to=self.position_max[axis])
            step_increment = step_dict[axis] // 10
            if step_increment == 0:
                step_increment = 1
            widgets[step_axis + "_step"].widget.configure(increment=step_increment)
            widgets[step_axis + "_step"].set(step_dict[axis])
            
        # Joystick
        microscope_name = config.microscope_name

        self.new_joystick_axes = self.parent_controller.configuration["configuration"][
            "microscopes"
        ][f"{microscope_name}"]["stage"].get("joystick_axes", [])

        if self.view.stop_frame.joystick_btn.winfo_ismapped():
            if self.new_joystick_axes is None or list(self.new_joystick_axes) == []:
                self.view.stop_frame.joystick_btn.grid_forget()
            else:
                self.view.stop_frame.joystick_btn.grid()
        else:
            if (
                self.new_joystick_axes is not None
                and list(self.new_joystick_axes) != []
            ):
                self.view.stop_frame.joystick_btn.grid()
            else:
                self.view.stop_frame.joystick_btn.grid_forget()

        if list(self.joystick_axes) != list(self.new_joystick_axes):
            self.force_enable_all_axes()
            self.joystick_is_on = False
            self.new_joystick_axes

        self.joystick_axes = self.new_joystick_axes
   
    def stage_key_press(self, event):
        """The stage key press

        Parameters
        ----------
        event : tkinter.Event
            The tkinter event

        Returns
        -------
        None
        """
        if event.state != 0:
            return
        char = event.char.lower()
        current_position = {}
        #current_position = self.get_position()
        #if current_position is None:
        #    return
       
        xy_increment = self.widget_vals["xy_step"].get()
        
        for axis in ["x", "y", "z", "theta", "f"]:
            current_position[axis] = self.widget_vals[axis].get() 
        
        config = self.parent_controller.configuration_controller
        self.position_min = config.get_stage_position_limits("_min")
        self.position_max = config.get_stage_position_limits("_max")

        self.position_min_x = self.position_min['x']
        self.position_max_x = self.position_max['x']
        self.position_min_y = self.position_min['y']
        self.position_max_y = self.position_max['y']
        
        
        if self.stage_limits is True:
                if current_position["y"] < self.position_max['y'] and current_position['y'] > self.position_min['y']:
                        if char == "w":
                            current_position["y"] += xy_increment
                        elif char == "s":
                            current_position["y"] -= xy_increment
                        #print("inside stage bounds y")
                elif current_position['y'] >= self.position_max_y:
                    current_position['y'] = self.position_max_y - xy_increment
                    #print('Upper Y Stage Limit keystroke')
                elif current_position['y'] <= self.position_min_y:
                    #print('Lower Y Stage Limit keystroke')
                    current_position['y'] = self.position_min_y + xy_increment
        if self.stage_limits is True:
                if current_position["x"] < self.position_max['x'] and current_position['x'] > self.position_min['x']:
                        if char == "a":
                            current_position["x"] -= xy_increment
                        elif char == "d":
                            current_position["x"] += xy_increment
                        #print("inside stage bounds x")
                elif current_position['x'] >= self.position_max_x:
                    #print('Upper X Stage Limit keystroke')
                    current_position['x'] = self.position_max_x - xy_increment
                elif current_position['x'] <= self.position_min_x:
                    #print('Lower X Stage Limit keystroke')
                    current_position['x'] = self.position_min_x + xy_increment
        if self.stage_limits is False:
                if char == "w":
                    current_position["y"] += xy_increment
                elif char == "a":
                    current_position["x"] -= xy_increment
                elif char == "s":
                    current_position["y"] -= xy_increment
                elif char == "d":
                    current_position["x"] += xy_increment
                #print("STAGE LIMITS OFF")
        self.set_position(current_position)
        # if char == "w":
        #     current_position["y"] += xy_increment/2
        # elif char == "a":
        #     current_position["x"] -= xy_increment/2
        # elif char == "s":
        #     current_position["y"] -= xy_increment/2
        # elif char == "d":
        #     current_position["x"] += xy_increment/2
        # print(current_position)
        # self.set_position(current_position)
        #return handler
        
    def bind_position_callbacks(self):
        """Binds position_callback() to each axis, records the trace name so we can
        unbind later.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if not self.position_callbacks_bound:
            for axis in ["x", "y", "z", "theta", "f"]:
                # add event bind to position entry variables
                cbname = self.widget_vals[axis].trace_add(
                    "write", self.position_callback(axis)
                )
                self.position_callback_traces[axis] = cbname
            self.position_callbacks_bound = True

    def unbind_position_callbacks(self):
        """Unbinds position callbacks.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if self.position_callbacks_bound:
            for axis, cbname in self.position_callback_traces.items():
                self.widget_vals[axis].trace_remove("write", cbname)
            self.position_callbacks_bound = False

    def populate_experiment_values(self):
        """This function set all the position and step values

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.stage_setting_dict = self.parent_controller.configuration["experiment"][
            "StageParameters"
        ]
        widgets = self.view.get_widgets()
        for k in widgets:
            self.widget_vals[k].set(self.stage_setting_dict.get(k, 0))
            widgets[k].widget.trigger_focusout_validation()

    def set_position(self, position):
        """This function is to populate(set) position in the View

        Parameters
        ----------
        position : dict
            {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}

        Returns
        -------
        None
        """
        widgets = self.view.get_widgets()
        for axis in ["x", "y", "z", "theta", "f"]:
            self.widget_vals[axis].set(position.get(axis, 0))
            # validate position value if set through variable
            if self.stage_limits:
                widgets[axis].widget.trigger_focusout_validation()
            self.stage_setting_dict[axis] = position.get(axis, 0)
        self.show_verbose_info("Set stage position")

    def set_position_silent(self, position):
        """This function is to populate(set) position in the View without a trace.

        Parameters
        ----------
        position : dict
            {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}

        Returns
        -------
        None
        """
        self.unbind_position_callbacks()

        self.set_position(position)

        self.bind_position_callbacks()

    def get_position(self):
        """This function returns current position from the view.

        Parameters
        ----------
        None

        Returns
        -------
        position : dict
            Dictionary of x, y, z, theta, and f values.

        """
        position = {}
        try:
            for axis in ["x", "y", "z", "theta", "f"]:
                position[axis] = self.widget_vals[axis].get()
                if self.stage_limits is True:
                    if (
                        position[axis] < self.position_min[axis]
                        or position[axis] > self.position_max[axis]
                    ):
                        return None
        except tk.TclError:
            # Tkinter will raise error when the variable is DoubleVar and the value
            # is empty
            return None
        return position

    def up_btn_handler(self, axis):
        """This function generates command functions according to the desired axis
        to move.

        Parameters
        ----------
        axis : str
            Should be one of 'x', 'y', 'z', 'theta', 'f'
            position_axis += step_axis

        Returns
        -------
        handler : object
            Function for setting desired stage positions in the View.
        """
        position_val = self.widget_vals[axis]
        if axis == "x" or axis == "y":
            step_val = self.widget_vals["xy_step"]
        else:
            step_val = self.widget_vals[axis + "_step"]

        def handler():

            try:
                temp = position_val.get() + step_val.get()
            except AttributeError:
                return
            if self.stage_limits is True:
                if temp >= self.position_max[axis]:
                    temp = position_val.get()
                    #temp = self.position_max[axis] + step_val.get()
                    #print('Upper Stage Limit Up')
                elif temp <= self.position_min[axis]:
                    temp = position_val.get()
                    #temp = self.position_min[axis] - step_val.get()
                    #print('Lower Stage Limit Up')
            # guarantee stage won't move out of limits
            if position_val.get() != temp:
                position_val.set(temp)

        return handler

    def down_btn_handler(self, axis):
        """This function generates command functions according to the desired axis
        to move.

        Parameters
        ----------
   
        Returns
        -------
        handler : object
            Function for setting desired stage positions in the View.
        """
        position_val = self.widget_vals[axis]
        if axis == "x" or axis == "y":
            step_val = self.widget_vals["xy_step"]
        else:
            step_val = self.widget_vals[axis + "_step"]

        def handler():

            try:
                temp = position_val.get() - step_val.get()
            except AttributeError:
                return
            if self.stage_limits is True:
                if temp <= self.position_min[axis]:
                    temp = self.position_min[axis] + step_val.get()
                    #print('Lower Stage Limit down') 
                elif temp >= self.position_max[axis]:
                    temp = self.position_max[axis] - step_val.get()
                    #print('Upper Stage Limit down') 
                
            # guarantee stage won't move out of limits
            if position_val.get() != temp:
                position_val.set(temp)

        return handler

    def zero_btn_handler(self, axis):
        """This function generates command functions according to the desired axis
        to move.

        Parameters
        ----------
        axis : str
            Should be one of 'z', 'theta', 'f'
            position_axis = 0

        Returns
        -------
        handler : object
            Function for setting desired stage positions in the View.
        """
        position_val = self.widget_vals[axis]

        def handler():
            position_val.set(0)

        return handler

    def xy_zero_btn_handler(self):
        """This function generates command functions to set xy position to zero

        Parameters
        ----------
        None

        Returns
        -------
        handler : object
            Function for setting desired stage positions in the View.
        """
        x_val = self.widget_vals["x"]
        y_val = self.widget_vals["y"]

        def handler():
            x_val.set(0)
            y_val.set(0)

        return handler

    def stop_button_handler(self, *args):
        """This function stops the stage after a 250 ms debouncing period of time.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.view.after(250, lambda *args: self.parent_controller.execute("stop_stage"))

    def joystick_button_handler(self, event=None, *args):
        """Toggle the joystick operation mode.

        Parameters
        ----------
        event : tkinter.Event
            The tkinter event

        Returns
        -------
        None

        """
        if self.joystick_is_on:
            self.joystick_is_on = False
        else:
            self.joystick_is_on = True
        self.view.after(
            250, lambda *args: self.parent_controller.execute("joystick_toggle")
        )
        self.view.toggle_button_states(self.joystick_is_on, self.joystick_axes)

    def force_enable_all_axes(self, event=None, *args):
        """Enables all buttons and entries on the stage tab.

        Parameters
        ----------
        event : tkinter.Event
            The tkinter event (currently unused)

        Returns
        -------
        None

        """
        self.view.force_enable_all_axes()

    def position_callback(self, axis, *args, **kwargs):
        """Callback functions bind to position variables.

        Implements debounce functionality for user inputs (or click buttons) to reduce
        time costs of moving stage.

        Parameters
        ----------
        axis : str
            axis can be 'x', 'y', 'z', 'theta', 'f'
        kwargs : ...
            ...

        Returns
        -------
        handler : object
            Function for moving stage to the desired position with debounce
            functionality.

        """
        position_var = self.widget_vals[axis]
        temp = self.view.get_widgets()
        widget = temp[axis].widget

        def handler(*args):
            if self.event_id[axis]:
                self.view.after_cancel(self.event_id[axis])
            # if position is not a number, then do not move stage
            try:
                position = position_var.get()
                #print(position)
                if self.stage_limits:
                    widget.trigger_focusout_validation()
                    # if position is not inside limits do not move stage
                    if (
                        position < self.position_min[axis]
                        or position > self.position_max[axis]
                    ):
                        return
            except tk._tkinter.TclError:
                print("tk error")
                if self.event_id[axis]:
                    self.view.after_cancel(self.event_id[axis])
                return
            except AttributeError:
                print("attribute error")
                logger.error(f"Attribute Error Caught: trying to set position {axis}")
                return

            # update stage position
            self.stage_setting_dict[axis] = position
            # Debouncing wait duration - Duration of time to integrate the number of
            # clicks that a user provides. If 1000 ms, if user hits button 10x within
            # 1s, only moves to the final value.
            self.event_id[axis] = self.view.after(
                250,
                lambda *args: self.parent_controller.execute("stage", position, axis),
            )

            self.show_verbose_info("Stage position changed")

        return handler
