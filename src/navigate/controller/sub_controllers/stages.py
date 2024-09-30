# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

# Standard Library Imports
import tkinter as tk
from multiprocessing.managers import ListProxy, DictProxy
import logging

# Third Party Imports

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class StageController(GUIController):
    """StageController

    This class is the controller for the stage GUI. It handles the stage movement
    and the stage limits. It also handles the stage movement buttons and the
    stage movement limits.
    """

    def __init__(self, view, main_view, canvas, parent_controller):
        """Initializes the StageController

        Parameters
         ----------
         view : navigate.view.stage_view.StageView
             The stage view
         main_view : tkinter.Tk
             The main view of the microscope
         canvas : tkinter.Canvas
             The canvas of the microscope
         parent_controller : navigate.controller.Controller
             The parent controller of the stage controller
        """
        super().__init__(view, parent_controller)

        #: str: The default microscope
        self.default_microscope = (
            f"{self.parent_controller.configuration_controller.microscope_name}"
        )

        #: bool: The joystick mode is on.
        self.joystick_is_on = False

        #: list: The joystick axes
        self.joystick_axes = self.parent_controller.configuration["configuration"][
            "microscopes"
        ][self.default_microscope]["stage"].get("joystick_axes", [])

        #: tkinter.Tk: The main view of the microscope
        self.main_view = main_view

        #: tkinter.Canvas: The canvas of the microscope
        self.canvas = canvas

        #: dict: The stage setting dictionary
        self.stage_setting_dict = self.parent_controller.configuration["experiment"][
            "StageParameters"
        ]

        #: dict: The event id
        self.event_id = {"x": None, "y": None, "z": None, "theta": None, "f": None}

        # stage movement limits
        #: dict: The minimum stage position.
        self.position_min = {}

        #: dict: The maximum stage position.
        self.position_max = {}

        # variables
        #: dict: The widget values
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

        for k in ["xy", "z", "f", "theta"]:
            self.widget_vals[k + "_step"].trace_add(
                "write", self.update_step_size_handler(k)
            )

        buttons["stop"].configure(command=self.stop_button_handler)

        buttons["joystick"].configure(command=self.joystick_button_handler)

        #: dict: The position callback traces
        self.position_callback_traces = {}

        #: bool: The position callbacks are bound
        self.position_callbacks_bound = False

        self.bind_position_callbacks()

        #: bool: The stage limits are on
        self.stage_limits = True

        #: list: The stage flip flags
        self.flip_flags = None

        self.initialize()

    def stage_key_press(self, event):
        """The stage key press.

        This function is called when a W, A, S, or D is
        pressed and initializes a stage movement..

        Parameters
        ----------
        event : tkinter.Event
            The tkinter event

        """
        if event.state != 0:
            return
        if not self.joystick_is_on:
            char = event.char.lower()
            if char == "w":
                self.up_btn_handler("y")()
            elif char == "a":
                self.down_btn_handler("x")()
            elif char == "s":
                self.down_btn_handler("y")()
            elif char == "d":
                self.up_btn_handler("x")()

    def initialize(self):
        """Initialize the Stage limits of steps and positions."""
        config = self.parent_controller.configuration_controller
        self.disable_synthetic_stages(config)

        # Get the minimum and maximum stage limits.
        self.position_min = config.get_stage_position_limits("_min")
        self.position_max = config.get_stage_position_limits("_max")

        widgets = self.view.get_widgets()
        step_dict = self.stage_setting_dict[config.microscope_name]
        for axis in ["x", "y", "z", "theta", "f"]:
            # Set Stage Limits
            widgets[axis].widget.min = self.position_min[axis]
            widgets[axis].widget.max = self.position_max[axis]
            if axis == "x" or axis == "y":
                step_axis = "xy"
            else:
                step_axis = axis

            # Set step size.
            # the minimum step should be non-zero and non-negative.
            widgets[step_axis + "_step"].widget.configure(from_=0.01)
            widgets[step_axis + "_step"].widget.configure(to=self.position_max[axis])
            step_increment = step_dict[step_axis + "_step"] // 10
            if step_increment == 0:
                step_increment = 1
            widgets[step_axis + "_step"].widget.configure(increment=step_increment)
            widgets[step_axis + "_step"].set(step_dict[step_axis + "_step"])

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
        self.flip_flags = config.stage_flip_flags

    def disable_synthetic_stages(self, config):
        """Disable synthetic stages.

        Parameters
        ----------
        config : ConfigurationController
            The configuration controller
        """
        microscope_configuration = config.get_microscope_configuration_dict()
        stages = microscope_configuration["stage"]["hardware"]

        if type(stages) is ListProxy:
            stages = list(stages)
        elif type(stages) is DictProxy:
            stages = [dict(stages)]

        for stage in stages:
            if type(stage) is DictProxy:
                stage_dict = dict(stage)
            elif type(stage) is dict:
                stage_dict = stage

            for axis in stage_dict["axes"]:
                if (stage_dict["type"].lower() == "synthetic") or (
                    stage_dict["type"].lower() == "syntheticstage"
                ):
                    state = "disabled"
                else:
                    state = "normal"

                if axis == "x":
                    self.view.xy_frame.up_x_btn.config(state=state)
                    self.view.xy_frame.down_x_btn.config(state=state)

                elif axis == "y":
                    self.view.xy_frame.up_y_btn.config(state=state)
                    self.view.xy_frame.down_y_btn.config(state=state)

                elif axis == "z":
                    self.view.z_frame.down_btn.config(state=state)
                    self.view.z_frame.up_btn.config(state=state)

                elif axis == "theta":
                    self.view.theta_frame.down_btn.config(state=state)
                    self.view.theta_frame.up_btn.config(state=state)

                elif axis == "f":
                    self.view.f_frame.down_btn.config(state=state)
                    self.view.f_frame.up_btn.config(state=state)
            else:
                pass

    def bind_position_callbacks(self):
        """Binds position_callback() to each axis, records the trace name so we can
        unbind later."""
        widgets = self.view.get_widgets()
        if not self.position_callbacks_bound:
            for axis in ["x", "y", "z", "theta", "f"]:
                # add event bind to position entry variables
                widgets[axis].widget.bind("<FocusOut>", self.position_callback(axis))
                # cbname = self.widget_vals[axis].trace_add(
                #     "write", self.position_callback(axis)
                # )
                # self.position_callback_traces[axis] = cbname
            self.position_callbacks_bound = True

    def unbind_position_callbacks(self):
        """Unbinds position callbacks."""
        if self.position_callbacks_bound:
            for axis, cbname in self.position_callback_traces.items():
                self.widget_vals[axis].trace_remove("write", cbname)
            self.position_callbacks_bound = False

    def populate_experiment_values(self):
        """This function sets all the position and step values"""
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
        """
        for axis in ["x", "y", "z", "theta", "f"]:
            if axis not in position:
                continue
            self.widget_vals[axis].set(position[axis])
            self.position_callback(axis)()
        self.show_verbose_info("Set stage position")

    def set_position_silent(self, position):
        """This function is to populate(set) position in the View without a trace.

        Parameters
        ----------
        position : dict
            {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}
        """
        widgets = self.view.get_widgets()
        for axis in ["x", "y", "z", "theta", "f"]:
            if axis not in position:
                continue
            self.widget_vals[axis].set(position[axis])
            # validate position value if set through variable
            if self.stage_limits:
                widgets[axis].widget.trigger_focusout_validation()
            self.stage_setting_dict[axis] = position.get(axis, 0)
        self.show_verbose_info("Set stage position")

    def get_position(self):
        """This function returns current position from the view.

        Returns
        -------
        position : dict
            Dictionary of x, y, z, theta, and f values.

        """
        position = {}
        try:
            for axis in ["x", "y", "z", "theta", "f"]:
                position[axis] = float(self.widget_vals[axis].get())
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
            """This function generates command functions according to the desired axis
            to move."""
            stage_direction = -1 if self.flip_flags[axis] else 1
            try:
                temp = float(position_val.get()) + step_val.get() * stage_direction
            except tk._tkinter.TclError:
                return
            if self.stage_limits is True:
                if temp > self.position_max[axis]:
                    temp = self.position_max[axis]
                elif temp < self.position_min[axis]:
                    temp = self.position_min[axis]
            # guarantee stage won't move out of limits
            if float(position_val.get()) != temp:
                position_val.set(temp)
                self.position_callback(axis)()

        return handler

    def down_btn_handler(self, axis):
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
            """This function generates command functions according to the desired axis
            to move."""
            stage_direction = -1 if self.flip_flags[axis] else 1
            try:
                temp = float(position_val.get()) - step_val.get() * stage_direction
            except tk._tkinter.TclError:
                return
            if self.stage_limits is True:
                if temp < self.position_min[axis]:
                    temp = self.position_min[axis]
                elif temp > self.position_max[axis]:
                    temp = self.position_max[axis]
            # guarantee stage won't move out of limits
            if float(position_val.get()) != temp:
                position_val.set(temp)
                self.position_callback(axis)()

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
            self.position_callback(axis)()

        return handler

    def xy_zero_btn_handler(self):
        """This function generates command functions to set xy position to zero

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
            self.position_callback("x")()
            self.position_callback("y")()

        return handler

    def stop_button_handler(self, *args):
        """This function stops the stage after a 250 ms debouncing period of time."""
        self.view.after(250, lambda *args: self.parent_controller.execute("stop_stage"))

    def joystick_button_handler(self, event=None, *args):
        """Toggle the joystick operation mode.

        Parameters
        ----------
        event : tkinter.Event
            The tkinter event
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
        *args : ...
            ...
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
            """Callback functions bind to position variables."""
            # check if focus on another window
            if not self.view.focus_get():
                return
            if self.event_id[axis]:
                self.view.after_cancel(self.event_id[axis])
            # if position is not a number, then do not move stage
            try:
                position = float(position_var.get())
                if self.stage_limits:
                    widget.trigger_focusout_validation()
                    # if position is not inside limits do not move stage
                    if position < float(self.position_min[axis]) or position > float(
                        self.position_max[axis]
                    ):
                        return
            except tk._tkinter.TclError:
                if self.event_id[axis]:
                    self.view.after_cancel(self.event_id[axis])
                return
            except AttributeError:
                logger.error(f"Attribute Error Caught: trying to set position {axis}")
                return

            # update stage position
            self.stage_setting_dict[axis] = position
            # Debouncing wait duration - Duration of time to integrate the number of
            # clicks that a user provides. If 1000 ms, if user hits button 10x within
            # 1s, only moves to the final value.
            self.event_id[axis] = self.view.after(
                500,
                lambda *args: self.parent_controller.execute("stage", position, axis),
            )

            self.show_verbose_info("Stage position changed")

        return handler

    def update_step_size_handler(self, axis):
        """Callback functions bind to step size variables

        Parameters
        ----------
        axis : str
            axis can be 'xy', 'z', 'theta', 'f'

        Returns
        -------
        handler : object
            Function to update step size in experiment.yml.
        """

        def func(*args):
            """Callback functions bind to step size variables."""
            microscope_name = self.parent_controller.configuration["experiment"][
                "MicroscopeState"
            ]["microscope_name"]
            try:
                step_size = int(self.widget_vals[axis + "_step"].get())
            except (ValueError, tk._tkinter.TclError):
                return
            self.stage_setting_dict[microscope_name][axis + "_step"] = step_size

        return func
