from controller.sub_controllers.widget_functions import validate_wrapper
from controller.sub_controllers.gui_controller import GUI_Controller


class Stage_GUI_Controller(GUI_Controller):
    def __init__(self, view, parent_controller, verbose=False, configuration_controller=None):
        super().__init__(view, parent_controller, verbose)

        self.event_id = {
            'x': None,
            'y': None,
            'z': None,
            'theta': None,
            'f': None
        }

        # state movement limits
        self.position_min = {
            'x': 0,
            'y': 0,
            'z': 0,
            'theta': 0,
            'f': 0
        }
        self.position_max = {
            'x': 10000,
            'y': 10000,
            'z': 10000,
            'theta': 10000,
            'f': 10000
        }

        # position variables
        self.position_val = {
            'x': self.view.position_frame.x_val,
            'y': self.view.position_frame.y_val,
            'z': self.view.position_frame.z_val,
            'theta': self.view.position_frame.theta_val,
            'f': self.view.position_frame.focus_val
        }

        # add validations to widgets
        validate_wrapper(self.view.x_y_frame.increment_box)
        validate_wrapper(self.view.z_frame.increment_box)
        validate_wrapper(self.view.theta_frame.increment_box)
        validate_wrapper(self.view.focus_frame.increment_box)
        validate_wrapper(self.view.position_frame.x_entry, is_entry=True)
        validate_wrapper(self.view.position_frame.y_entry, is_entry=True)
        validate_wrapper(self.view.position_frame.z_entry, is_entry=True)
        validate_wrapper(self.view.position_frame.theta_entry, is_entry=True)
        validate_wrapper(self.view.position_frame.f_entry, is_entry=True)

        
        # gui event bind
        self.view.x_y_frame.positive_x_btn.configure(
            command=self.up_btn_handler('x')
        )
        self.view.x_y_frame.negative_x_btn.configure(
            command=self.down_btn_handler('x')
        )
        self.view.x_y_frame.positive_y_btn.configure(
            command=self.up_btn_handler('y')
        )
        self.view.x_y_frame.negative_y_btn.configure(
            command=self.down_btn_handler('y')
        )
        self.view.x_y_frame.zero_x_y_btn.configure(
            command=self.xy_zero_btn_handler()
        )
        self.view.z_frame.up_btn.configure(
            command=self.up_btn_handler('z')
        )
        self.view.z_frame.down_btn.configure(
            command=self.down_btn_handler('z')
        )
        self.view.z_frame.zero_btn.configure(
            command=self.zero_btn_handler('z')
        )
        self.view.theta_frame.up_btn.configure(
            command=self.up_btn_handler('theta')
        )
        self.view.theta_frame.down_btn.configure(
            command=self.down_btn_handler('theta')
        )
        self.view.theta_frame.zero_btn.configure(
            command=self.zero_btn_handler('theta')
        )
        self.view.focus_frame.up_btn.configure(
            command=self.up_btn_handler('f')
        )
        self.view.focus_frame.down_btn.configure(
            command=self.down_btn_handler('f')
        )
        self.view.focus_frame.zero_btn.configure(
            command=self.zero_btn_handler('f')
        )

        for axis in ['x', 'y', 'z', 'theta', 'f']:
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


        for axis in ['x', 'y', 'z', 'theta', 'f']:
            exec('self.view.position_frame.{}_entry.from_={}'.format(axis, self.position_min[axis]))
            exec('self.view.position_frame.{}_entry.to={}'.format(axis, self.position_max[axis]))

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
        for axis in ['x', 'y', 'z', 'theta', 'f']:
            setting_dict[axis] = position[axis]
        
        # get step value
        try:
            for axis in ['xy', 'z', 'theta', 'f']:
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
        for axis in ['x', 'y', 'z', 'theta', 'f']:
            self.position_val[axis].set(position.get(axis, 0))
            # validate position value if set through variable
            exec('self.view.position_frame.{}_entry.validate()'.format(axis))
        
        self.show_verbose_info('set stage position')

    def get_position(self):
        """
        # This function returns current position
        """
        position = {}
        try:
            for axis in ['x', 'y', 'z', 'theta', 'f']:
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
        for axis in ['xy', 'z', 'theta', 'f']:
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
        x_val = self.position_val['x']
        y_val = self.position_val['y']

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
        if axis == 'z':
            return self.view.z_frame.spinval
        elif axis == 'theta':
            return self.view.theta_frame.spinval
        elif axis == 'f':
            return self.view.focus_frame.spinval
        else:
            return self.view.x_y_frame.spinval
