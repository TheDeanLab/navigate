from controller.sub_controllers.gui_controller import GUI_Controller


class Stage_GUI_Controller(GUI_Controller):
    def __init__(self, view, parent_controller, verbose=False):
        super().__init__(view, parent_controller, verbose)

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
        self.view.position_frame.x_val.trace_add('write', self.position_callback('x'))
        self.view.position_frame.y_val.trace_add('write', self.position_callback('y'))
        self.view.position_frame.z_val.trace_add('write', self.position_callback('z'))
        self.view.position_frame.theta_val.trace_add('write', self.position_callback('theta'))
        self.view.position_frame.focus_val.trace_add('write', self.position_callback('f'))

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

    def set_position_limits(self, position_min, position_max):
        """
        # this function sets position limits
        """
        self.position_min = position_min
        self.position_max = position_max

    def set_position(self, position):
        """
        # This function is to populate(set) position
        # position should be a dict
        # {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}
        """
        for axis in position:
            val = self.get_position_val(axis)
            if val:
                val.set(position[axis])
        
        self.show_verbose_info('set stage position')

    def get_position(self):
        """
        # This function returns current position
        """
        position = {
            'x': self.get_position_val('x').get(),
            'y': self.get_position_val('y').get(),
            'z': self.get_position_val('z').get(),
            'theta': self.get_position_val('theta').get(),
            'f': self.get_position_val('f').get()
        }
        return position

    def set_step_size(self, steps):
        """
        # This function is to populate(set) step sizes
        # steps should be a dict
        # {'xy': value, 'z': value, 'theta': value, 'f': value}
        """
        for axis in steps:
            val = self.get_step_val(axis)
            if val:
                val.set(steps[axis])

        self.show_verbose_info('set step size')

    def get_step_size(self):
        """
        # This function returns step sizes as a dictionary
        # {
        #    'xy': ,
        #    'z': ,
        #    'theta': ,
        #    'f': 
        # }
        """
        step_size = {}
        for axis in ['xy', 'z', 'theta', 'f']:
            step_size[axis] = self.get_step_val(axis).get()
        return step_size

    def up_btn_handler(self, axis):
        """
        # This function generates command functions according to axis
        # axis should be one of 'x', 'y', 'z', 'theta', 'f'
        # position_axis += step_axis
        """
        position_val = self.get_position_val(axis)
        step_val = self.get_step_val(axis)

        def handler():
            # guarantee stage won't move out of limits
            if position_val.get() == self.position_max[axis]:
                return
            temp = position_val.get() + step_val.get()
            if temp >= self.position_max[axis]:
                temp = self.position_max[axis]
            position_val.set(temp)
        return handler

    def down_btn_handler(self, axis):
        """
        # This function generates command functions according to axis
        # axis should be one of 'x', 'y', 'z', 'theta', 'f'
        # position_axis -= step_axis
        """
        position_val = self.get_position_val(axis)
        step_val = self.get_step_val(axis)

        def handler():
            # guarantee stage won't move out of limits
            if position_val.get() == self.position_min[axis]:
                return
            temp = position_val.get() - step_val.get()
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
        position_val = self.get_position_val(axis)

        def handler():
            position_val.set(0)
        return handler

    def xy_zero_btn_handler(self):
        """
        # This function generates command functions to set xy position to zero
        """
        x_val = self.get_position_val('x')
        y_val = self.get_position_val('y')

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
        position_var = self.get_position_val(axis)

        def handler(*args):
            if self.event_id[axis]:
                self.view.after_cancel(self.event_id[axis])
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

    def get_position_val(self, axis):
        """
        # get position variable according to axis name
        # axis can be 'x', 'y', 'z', 'theta', 'f'
        """
        if axis == 'x':
            return self.view.position_frame.x_val
        elif axis == 'y':
            return self.view.position_frame.y_val
        elif axis == 'z':
            return self.view.position_frame.z_val
        elif axis == 'theta':
            return self.view.position_frame.theta_val
        elif axis == 'f':
            return self.view.position_frame.focus_val
