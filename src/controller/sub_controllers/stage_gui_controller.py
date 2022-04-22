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


class Stage_GUI_Controller(GUI_Controller):
    def __init__(self, view, parent_controller, verbose=False, configuration_controller=None):
        super().__init__(view, parent_controller, verbose)
        
        # Get Widgets
        self.pos_widgets = self.view.position_frame.get_widgets() # Keys ['X', 'Y', 'Z', "Theta", 'Focus']

        self.event_id = {
            'X': None,
            'Y': None,
            'Z': None,
            'Theta': None,
            'Focus': None
        }

        # state movement limits
        self.position_min = {
            'X': 0,
            'Y': 0,
            'Z': 0,
            'Theta': 0,
            'Focus': 0
        }
        self.position_max = {
            'X': 10000,
            'Y': 10000,
            'Z': 10000,
            'Theta': 10000,
            'Focus': 10000
        }

        # position variables
        self.position_val = {
            'X': self.pos_widgets['X'].get_variable(),
            'Y': self.pos_widgets['Y'].get_variable(),
            'Z': self.pos_widgets['Z'].get_variable(),
            'Theta': self.pos_widgets['Theta'].get_variable(),
            'Focus': self.pos_widgets['Focus'].get_variable()
        }

        # add validations to widgets
        validate_wrapper(self.view.x_y_frame.increment_box)
        validate_wrapper(self.view.z_frame.increment_box)
        validate_wrapper(self.view.theta_frame.increment_box)
        validate_wrapper(self.view.focus_frame.increment_box)
        # TODO add validation widgets from pos frame and can remove this after
        # validate_wrapper(self.pos_widgets['X'].widget, is_entry=True)
        # validate_wrapper(self.pos_widgets['Y'].widget, is_entry=True)
        # validate_wrapper(self.pos_widgets['Z'].widget, is_entry=True)
        # validate_wrapper(self.pos_widgets['Theta'].widget, is_entry=True)
        # validate_wrapper(self.pos_widgets['Focus'].widget, is_entry=True)

        
        # gui event bind
        self.view.x_y_frame.positive_x_btn.configure(
            command=self.up_btn_handler('X')
        )
        self.view.x_y_frame.negative_x_btn.configure(
            command=self.down_btn_handler('X')
        )
        self.view.x_y_frame.positive_y_btn.configure(
            command=self.up_btn_handler('Y')
        )
        self.view.x_y_frame.negative_y_btn.configure(
            command=self.down_btn_handler('Y')
        )
        self.view.x_y_frame.zero_x_y_btn.configure(
            command=self.xy_zero_btn_handler()
        )
        self.view.z_frame.up_btn.configure(
            command=self.up_btn_handler('Z')
        )
        self.view.z_frame.down_btn.configure(
            command=self.down_btn_handler('Z')
        )
        self.view.z_frame.zero_btn.configure(
            command=self.zero_btn_handler('Z')
        )
        self.view.theta_frame.up_btn.configure(
            command=self.up_btn_handler('Theta')
        )
        self.view.theta_frame.down_btn.configure(
            command=self.down_btn_handler('Theta')
        )
        self.view.theta_frame.zero_btn.configure(
            command=self.zero_btn_handler('Theta')
        )
        self.view.focus_frame.up_btn.configure(
            command=self.up_btn_handler('Focus')
        )
        self.view.focus_frame.down_btn.configure(
            command=self.down_btn_handler('Focus')
        )
        self.view.focus_frame.zero_btn.configure(
            command=self.zero_btn_handler('Focus')
        )

        for axis in ['X', 'Y', 'Z', 'Theta', 'Focus']:
            # add event bind to position entry variables
            self.position_val[axis].trace_add('write', self.position_callback(axis))

        if configuration_controller:
            self.initialize(configuration_controller)


    def initialize(self, config):
        """
        # initialize the limits of steps and postions
        """
        self.position_min = config.get_stage_position_limits('_min')
        self.position_max = config.get_stage_position_limits('_max')

        # TODO test
        for axis in ['X', 'Y', 'Z', 'Theta', 'Focus']:
            # exec('self.view.position_frame.{}_entry.from_={}'.format(axis, self.position_min[axis]))
            # exec('self.view.position_frame.{}_entry.to={}'.format(axis, self.position_max[axis]))
            self.pos_widgets[axis].widget.min = self.position_min[axis]
            self.pos_widgets[axis].widget.max = self.position_max[axis]
            

        # set step limits
        temp_dict = {
            'x_y_step': self.view.x_y_frame.increment_box,
            'z_step': self.view.z_frame.increment_box,
            'theta_step': self.view.theta_frame.increment_box,
            'f_step': self.view.focus_frame.increment_box
        }
        for k in temp_dict:
            temp_dict[k].configure(from_=config.configuration.GUIParameters['stage'][k]['min'])
            temp_dict[k].configure(to=config.configuration.GUIParameters['stage'][k]['max'])
            temp_dict[k].configure(increment=config.configuration.GUIParameters['stage'][k]['step'])

    def set_experiment_values(self, setting_dict):
        """
        # This function set all the position and step value
        # setting_dict = { 'x': value, 'y': value, 'z': value, 'theta': value, 'f': value
                           'xy_step': value, 'z_step': value, 'theta_step': value, 'f_step': value}
        # }
        """
        self.set_position(setting_dict)
        self.set_step_size(setting_dict)

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
        for axis in ['X', 'Y', 'Z', 'Theta', 'Focus']:
            setting_dict[axis] = position[axis]
        
        # get step value
        try:
            for axis in ['X', 'Y', 'Z', 'Theta', 'Focus']:
                setting_dict[axis+'_step'] = self.get_step_val(axis).get()
        except:
            return False
        
        return True
    
    def set_position(self, position):
        """
        # This function is to populate(set) position
        # position should be a dict
        # {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}
        """
        for axis in ['X', 'Y', 'Z', 'Theta', 'Focus']:
            self.position_val[axis].set(position.get(axis, 0))
            # validate position value if set through variable
            # exec('self.view.position_frame.{}_entry.validate()'.format(axis))
            self.pos_widgets[axis].widget.trigger_focusout_validation() # TODO test
        
        self.show_verbose_info('set stage position')

    def get_position(self):
        """
        # This function returns current position
        """
        position = {}
        try:
            for axis in ['X', 'Y', 'Z', 'Theta', 'Focus']:
                position[axis] = self.position_val[axis].get()
                if position[axis] < self.position_min[axis] or position[axis] > self.position_max[axis]:
                    return None
        except:
            # Tkinter will raise error when the variable is DoubleVar and the value is empty
            return None
        return position

    def set_step_size(self, steps):
        """
        # This function is to populate(set) step sizes
        # steps should be a dict
        # {'xy': value, 'z': value, 'theta': value, 'f': value}
        """
        for axis in ['xy', 'Z', 'Theta', 'Focus']: # TODO this may cause errors because of XY conjoined
            val = self.get_step_val(axis)
            if val:
                val.set(steps[axis+'_step'])
        # validate
        self.view.x_y_frame.increment_box.validate()
        self.view.z_frame.increment_box.validate()
        self.view.focus_frame.increment_box.validate()
        self.view.theta_frame.increment_box.validate()

        self.show_verbose_info('set step size')

    def up_btn_handler(self, axis):
        """
        # This function generates command functions according to axis
        # axis should be one of 'x', 'y', 'z', 'theta', 'f'
        # position_axis += step_axis
        """
        position_val = self.position_val[axis]
        step_val = self.get_step_val(axis)

        def handler():
            # guarantee stage won't move out of limits
            if position_val.get() == self.position_max[axis]:
                return
            try:
                temp = position_val.get() + step_val.get()
            except:
                #TODO: maybe a popup
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
        position_val = self.position_val[axis]
        step_val = self.get_step_val(axis)

        def handler():
            # guarantee stage won't move out of limits
            if position_val.get() == self.position_min[axis]:
                return
            try:
                temp = position_val.get() - step_val.get()
            except:
                #TODO: maybe a popup
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
        position_val = self.position_val[axis]

        def handler():
            position_val.set(0)
        return handler

    def xy_zero_btn_handler(self):
        """
        # This function generates command functions to set xy position to zero
        """
        x_val = self.position_val['X']
        y_val = self.position_val['Y']

        def handler():
            x_val.set(0)
            y_val.set(0)
        return handler

    def position_callback(self, axis):
        """
        # callback functions bind to position variables
        # axis can be 'x', 'y', 'z', 'theta', 'f'
        # this function considers debouncing user inputs(or click buttons)
        # to reduce time costs of moving stage device
        """
        position_var = self.position_val[axis]

        def handler(*args):
            if self.event_id[axis]:
                self.view.after_cancel(self.event_id[axis])
            # if position is not a number, then do not move stage
            try:
                exec('self.view.position_frame.{}_entry.validate()'.format(axis))
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
            self.event_id[axis] = self.view.after(1000, lambda: self.parent_controller.execute('stage',
                                                                                               position_var.get(),
                                                                                               axis))

            self.show_verbose_info('stage position is changed')
        
        return handler

    def get_step_val(self, axis):
        """
        # get increment step variable according to axis name
        # axis can be: 'x', 'y', 'z', 'theta', 'f'
        """
        if axis == 'Z':
            return self.view.z_frame.spinval
        elif axis == 'Theta':
            return self.view.theta_frame.spinval
        elif axis == 'Focus':
            return self.view.focus_frame.spinval
        else:
            return self.view.x_y_frame.spinval
