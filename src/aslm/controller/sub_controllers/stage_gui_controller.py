"""
ASLM sub-controller for stage control from the GUI.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
from controller.sub_controllers.widget_functions import validate_wrapper
from controller.sub_controllers.gui_controller import GUI_Controller
import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)


class Stage_GUI_Controller(GUI_Controller):
    def __init__(self, view, parent_view, canvas, parent_controller, verbose=False, configuration_controller=None):
        super().__init__(view, parent_controller, verbose)

        self.event_id = {
            'x': None,
            'y': None,
            'z': None,
            'theta': None,
            'f': None
        }

        # stage movement limits
        # TODO: Should not be hard coded.
        self.position_min = {
            'x': 0,
            'y': 0,
            'z': 0,
            'theta': 0,
            'f': 0
        }

        # TODO: Should not be hard coded.
        self.position_max = {
            'x': 10000,
            'y': 10000,
            'z': 10000,
            'theta': 10000,
            'f': 10000
        }
        # variables
        self.widget_vals = self.view.get_variables()
                #binding mouse wheel event on camera viewcanvas")
                
        # gui event bind
        buttons = self.view.get_buttons()
        for k in buttons:
            if k[:2] == 'up':
                buttons[k].configure(command=self.up_btn_handler(k[3:-4]))
            elif k[:4] == 'down':
                buttons[k].configure(command=self.down_btn_handler(k[5:-4]))
            else:
                buttons[k].configure(
                    command=self.zero_btn_handler(k[5:-4])
                )

        for axis in ['x', 'y', 'z', 'theta', 'f']:
            # add event bind to position entry variables
            self.widget_vals[axis].trace_add('write', self.position_callback(axis))

        if configuration_controller:
            self.initialize(configuration_controller)
        self.count = 0
        self.mouse_scrolls = 0
        self.parent_view = parent_view
        self.canvas = canvas
        root = self.parent_view.root
        root.bind("<Key>", self.key_press)
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)
    #WASD key movement
    
    def on_enter(self, event):
        self.canvas.bind("<MouseWheel>", self.update_position)
        
    def on_leave(self, event):
        self.count = 0
        self.mouse_scrolls = 0

    def update_position(self, event):
        self.mouse_scrolls += 1
        if self.mouse_scrolls % 2 == 0:
            position_o = self.get_position()
            self.count += event.delta
            updated_position = position_o
            updated_position["f"] += self.count
            self.set_position(updated_position)

    def key_press(self, event):
      char = event.char
      position_o = self.get_position()
      current_position = position_o
      x_increment = self.widget_vals["x_step"].get()
      y_increment = self.widget_vals["y_step"].get()
      if char.lower() == "w":
          current_position['y'] += y_increment
      elif char.lower() == "a":
          current_position['x'] -= x_increment
      elif char.lower() == "s":
          current_position['y'] -= y_increment
      elif char.lower() == "d":
          current_position['x'] += x_increment
      self.set_position(current_position)  

    def initialize(self, config):
        """
        # initialize the limits of steps and postions
        """
        self.position_min = config.get_stage_position_limits('_min')
        self.position_max = config.get_stage_position_limits('_max')

        widgets = self.view.get_widgets()
        for axis in ['x', 'y', 'z', 'theta', 'f']:
            widgets[axis].widget.min = self.position_min[axis]
            widgets[axis].widget.max = self.position_max[axis]

        # set step limits
        for k in ['x_step', 'y_step', 'z_step', 'theta_step', 'f_step']:
            widgets[k].widget.configure(from_=config.configuration.GUIParameters['stage'][k]['min'])
            widgets[k].widget.configure(to=config.configuration.GUIParameters['stage'][k]['max'])
            widgets[k].widget.configure(increment=config.configuration.GUIParameters['stage'][k]['step'])

    def set_experiment_values(self, setting_dict):
        """
        # This function set all the position and step value
        # setting_dict = { 'x': value, 'y': value, 'z': value, 'theta': value, 'f': value
                           'xy_step': value, 'z_step': value, 'theta_step': value, 'f_step': value}
        # }
        """
        widgets = self.view.get_widgets()
        for k in widgets:
            self.widget_vals[k].set(setting_dict.get(k, 0))
            widgets[k].widget.trigger_focusout_validation()

    def update_experiment_values(self, setting_dict):
        """
        # This function collects position and step value
        # it will update setting_dict directly
        # return value: bool - True: all the values are valid
        #                      False: any value is invalid
        """
        position = self.get_position()
        if position is None:
            return False
        for axis in ['x', 'y', 'z', 'theta', 'f']:
            setting_dict[axis] = position[axis]
        
        # get step value
        try:
            for axis in ['x', 'y', 'z', 'theta', 'f']:
                setting_dict[axis+'_step'] = self.widget_vals[axis+'_step'].get()
        except:
            return False
        
        return True
    
    def set_position(self, position):
        """
        # This function is to populate(set) position
        # position should be a dict
        # {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}
        """
        widgets = self.view.get_widgets()
        for axis in ['x', 'y', 'z', 'theta', 'f']:
            self.widget_vals[axis].set(position.get(axis, 0))
            # validate position value if set through variable
            widgets[axis].widget.trigger_focusout_validation()
        
        self.show_verbose_info('set stage position')

    def get_position(self):
        """
        # This function returns current position
        """
        position = {}
        try:
            for axis in ['x', 'y', 'z', 'theta', 'f']:
                position[axis] = self.widget_vals[axis].get()
                if position[axis] < self.position_min[axis] or position[axis] > self.position_max[axis]:
                    return None
        except:
            # Tkinter will raise error when the variable is DoubleVar and the value is empty
            return None
        return position

    def up_btn_handler(self, axis):
        """
        # This function generates command functions according to axis
        # axis should be one of 'x', 'y', 'z', 'theta', 'f'
        # position_axis += step_axis
        """
        position_val = self.widget_vals[axis]
        step_val = self.widget_vals[axis+'_step']

        def handler():
            # guarantee stage won't move out of limits
            if position_val.get() == self.position_max[axis]:
                return
            try:
                temp = position_val.get() + step_val.get()
            except:
                return
            if temp > self.position_max[axis]:
                temp = self.position_max[axis]
            position_val.set(temp)
        return handler

    def down_btn_handler(self, axis):
        """
        # This function generates command functions according to axis
        # axis should be one of 'x', 'y', 'z', 'theta', 'f'
        # position_axis -= step_axis
        """
        position_val = self.widget_vals[axis]
        step_val = self.widget_vals[axis+'_step']

        def handler():
            # guarantee stage won't move out of limits
            if position_val.get() == self.position_min[axis]:
                return
            try:
                temp = position_val.get() - step_val.get()
            except:
                return
            if temp < self.position_min[axis]:
                temp = self.position_min[axis]
            position_val.set(temp)
        return handler

    def zero_btn_handler(self, axis):
        """
        # This function generates command functions according to axis
        # axis should be one of 'z', 'theta', 'f'
        # position_axis = 0
        """
        position_val = self.widget_vals[axis]

        def handler():
            position_val.set(0)
        return handler

    def xy_zero_btn_handler(self):
        """
        # This function generates command functions to set xy position to zero
        """
        x_val = self.widget_vals['x']
        y_val = self.widget_vals['y']

        def handler():
            x_val.set(0)
            y_val.set(0)
        return handler

    def position_callback(self, axis, **kwargs):
        """
        # callback functions bind to position variables
        # axis can be 'x', 'y', 'z', 'theta', 'f'
        # this function considers debouncing user inputs(or click buttons)
        # to reduce time costs of moving stage device
        """
        position_var = self.widget_vals[axis]
        temp = self.view.get_widgets()
        widget = temp[axis].widget

        def handler(*args):
            if self.event_id[axis]:
                self.view.after_cancel(self.event_id[axis])
            # if position is not a number, then do not move stage
            try:
                widget.trigger_focusout_validation()
                position = position_var.get()
                # if position is not inside limits do not move stage
                if position < self.position_min[axis] or position > self.position_max[axis]:
                    if self.event_id[axis]:
                        self.view.after_cancel(self.event_id[axis])
                    return
            except:
                if self.event_id[axis]:
                    self.view.after_cancel(self.event_id[axis])
                return

            # Debouncing wait duration - Duration of time to integrate the number of clicks that a user provides.
            # If 1000 ms, if user hits button 10x within 1s, only moves to the final value.
            self.event_id[axis] = self.view.after(250, lambda: self.parent_controller.execute('stage', position_var.get(), axis))
            # self.event_id[axis] = self.view.after(250, self.parent_controller.execute, 'stage', position_var.get(), axis)

            self.show_verbose_info('stage position is changed')
        
        return handler
