"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
from aslm.controller.sub_controllers.gui_controller import GUI_Controller
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Stage_GUI_Controller(GUI_Controller):
    """Stage GUI Controller

    Parameters
    ----------
    view : ttk widget
        ttk.Frame instance
    parent_controller
    verbose
    configuration_controller
    """
    def __init__(self,
                 view,
                 parent_view,
                 parent_controller,
                 verbose=False,
                 configuration_controller=None):

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
        self.parent_view = parent_view
     
        # gui event bind
        buttons = self.view.get_buttons()
        for k in buttons:
            if k[:2] == 'up':
                buttons[k].configure(command=self.up_btn_handler(k[3:-4]))
            elif k[:4] == 'down':
                buttons[k].configure(command=self.down_btn_handler(k[5:-4]))
            elif k[5:-4] == 'xy':
                buttons[k].configure(
                    command=self.xy_zero_btn_handler()
                )
            elif k.startswith('zero'):
                buttons[k].configure(
                    command=self.zero_btn_handler(k[5:-4])
                )
                
        min_buttons = self.parent_view.stage_control.minimized_control.get_buttons()
        for k in min_buttons:
            if k[:2] == 'up':
                min_buttons[k].configure(command=self.up_btn_handler(k[3:-4]))
            elif k[:4] == 'down':
                min_buttons[k].configure(command=self.down_btn_handler(k[5:-4]))
            elif k[5:-4] == 'xy':
                min_buttons[k].configure(
                    command=self.xy_zero_btn_handler()
                )
            else:
                min_buttons[k].configure(
                    command=self.zero_btn_handler(k[5:-4])
                )

        buttons['stop'].configure(command=self.stop_button_handler)
        self.position_callback_traces = {}
        self.position_callbacks_bound = False
        self.bind_position_callbacks()

        if configuration_controller:
            self.initialize(configuration_controller)

    def initialize(self, config):
        r"""Initialize the Stage limits of steps and positions

        Parameters
        ----------
        config : object
            ASLM_Configuration_Controller - config.configuration is Session instance of configuration.
        """
        self.position_min = config.get_stage_position_limits('_min')
        self.position_max = config.get_stage_position_limits('_max')

        widgets = self.view.get_widgets()
        for axis in ['x', 'y', 'z', 'theta', 'f']:
            widgets[axis].widget.min = self.position_min[axis]
            widgets[axis].widget.max = self.position_max[axis]

        # set step limits
        for k in ['xy_step', 'z_step', 'theta_step', 'f_step']:
            widgets[k].widget.configure(from_=config.configuration.GUIParameters['stage'][k]['min'])
            widgets[k].widget.configure(to=config.configuration.GUIParameters['stage'][k]['max'])
            widgets[k].widget.configure(increment=config.configuration.GUIParameters['stage'][k]['step'])

    def bind_position_callbacks(self):
        r"""Binds position_callback() to each axis, records the trace name so we can unbind later.
        """
        if not self.position_callbacks_bound:
            for axis in ['x', 'y', 'z', 'theta', 'f']:
                # add event bind to position entry variables
                cbname = self.widget_vals[axis].trace_add('write', self.position_callback(axis))
                self.position_callback_traces[axis] = cbname
            self.position_callbacks_bound = True

    def unbind_position_callbacks(self):
        r"""Unbinds position callbacks.
        """
        if self.position_callbacks_bound:
            for axis, cbname in self.position_callback_traces.items():
                self.widget_vals[axis].trace_remove('write', cbname)
            self.position_callbacks_bound = False

    def set_experiment_values(self, setting_dict):
        r"""This function set all the position and step values

        Parameters
        ----------
        setting_dict : dict
             setting_dict = { 'x': value, 'y': value, 'z': value, 'theta': value, 'f': value
                           'xy_step': value, 'z_step': value, 'theta_step': value, 'f_step': value}
        """
        widgets = self.view.get_widgets()
        for k in widgets:
            self.widget_vals[k].set(setting_dict.get(k, 0))
            widgets[k].widget.trigger_focusout_validation()

    def update_experiment_values(self, setting_dict):
        r"""This function collects position and step values

        Parameters
        ----------
        setting_dict : dict
            Dictionary of old stage locations.  Updated directly with new stage locations.

        Returns
        -------
            positions_valid : bool
                Returns True if all values are valid. Returns False if any value is invalid.
        """
        position = self.get_position()
        if position is None:
            return False
        for axis in ['x', 'y', 'z', 'theta', 'f']:
            setting_dict[axis] = position[axis]
        
        # get step value
        try:
            for axis in ['xy', 'z', 'theta', 'f']:
                setting_dict[axis+'_step'] = self.widget_vals[axis+'_step'].get()
        except:
            return False
        
        return True
    
    def set_position(self, position):
        r"""This function is to populate(set) position in the View

        Parameters
        ----------
        position : dict
            {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}
        """
        widgets = self.view.get_widgets()
        for axis in ['x', 'y', 'z', 'theta', 'f']:
            self.widget_vals[axis].set(position.get(axis, 0))
            # validate position value if set through variable
            widgets[axis].widget.trigger_focusout_validation()
        self.show_verbose_info('Set stage position')

    def set_position_silent(self, position):
        r"""This function is to populate(set) position in the View without a trace.

        Parameters
        ----------
        position : dict
            {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}
        """
        self.unbind_position_callbacks()

        widgets = self.view.get_widgets()
        for axis in ['x', 'y', 'z', 'theta', 'f']:
            self.widget_vals[axis].set(position.get(axis, 0))
            # validate position value if set through variable
            widgets[axis].widget.trigger_focusout_validation()

        self.bind_position_callbacks()

    def get_position(self):
        r"""This function returns current position from the view.

        Returns
        -------
        position : dict
            Dictionary of x, y, z, theta, and f values.
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
        r"""This function generates command functions according to the desired axis to move.

        Parameters
        ----------
        axis = str
            Should be one of 'x', 'y', 'z', 'theta', 'f'
            position_axis += step_axis

        Returns
        -------
        handler : object
            Function for setting desired stage positions in the View.
        """
        position_val = self.widget_vals[axis]
        if axis == 'x' or axis == 'y':
            step_val = self.widget_vals['xy_step']
        else:
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
        r"""This function generates command functions according to the desired axis to move.


        Parameters
        ----------
        axis = str
            Should be one of 'x', 'y', 'z', 'theta', 'f'
            position_axis += step_axis

        Returns
        -------
        handler : object
            Function for setting desired stage positions in the View.
        """
        position_val = self.widget_vals[axis]
        if axis == 'x' or axis == 'y':
            step_val = self.widget_vals['xy_step']
        else:
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
        r"""This function generates command functions according to the desired axis to move.


        Parameters
        ----------
        axis = str
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
        r"""This function generates command functions to set xy position to zero

        Returns
        -------
        handler : object
            Function for setting desired stage positions in the View.
        """
        x_val = self.widget_vals['x']
        y_val = self.widget_vals['y']

        def handler():
            x_val.set(0)
            y_val.set(0)
        return handler

    def stop_button_handler(self):
        r"""This function stops the stage after a 250 ms debouncing period of time."""
        self.view.after(250, lambda: self.parent_controller.execute('stop_stage'))

    def position_callback(self, axis, **kwargs):
        r"""Callback functions bind to position variables.

        Implements debounce functionality for user inputs (or click buttons) to reduce time costs of moving stage.

        Parameters
        ----------
        axis : str
            axis can be 'x', 'y', 'z', 'theta', 'f'
        kwargs : ...
            ...

        Returns
        -------
        handler : object
            Function for moving stage to the desired position with debounce functionality.

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
            self.event_id[axis] = self.view.after(250, lambda: self.parent_controller.execute('stage',
                                                                                              position_var.get(),
                                                                                              axis))

            # Acquire an image.
            self.parent_controller.execute('')
            self.show_verbose_info('Stage position changed')
        
        return handler
    