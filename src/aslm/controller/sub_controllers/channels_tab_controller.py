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

# Standard Library Imports
import logging

# Third Party Imports
import numpy as np

# Local Imports
from aslm.controller.sub_controllers.widget_functions import validate_wrapper
from aslm.controller.sub_controllers.gui_controller import GUI_Controller
from aslm.controller.sub_controllers.channel_setting_controller import Channel_Setting_Controller
from aslm.controller.sub_controllers.multi_position_controller import Multi_Position_Controller
from aslm.controller.sub_controllers.tiling_wizard_controller import Tiling_Wizard_Controller

# View Imports that are not called on startup
from aslm.view.main_window_content.tabs.channels.tiling_wizard_popup import tiling_wizard_popup as tiling_wizard


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Channels_Tab_Controller(GUI_Controller):
    def __init__(self,
                 view,
                 parent_controller=None,
                 verbose=False,
                 configuration_controller=None):
        super().__init__(view, parent_controller, verbose)

        self.is_save = False
        self.mode = 'stop'
        self.in_initialization = True

        # sub-controllers
        self.channel_setting_controller = Channel_Setting_Controller(self.view.channel_widgets_frame,
                                                                     self,
                                                                     self.verbose)
        self.multi_position_controller = Multi_Position_Controller(self.view.multipoint_list,
                                                                   self,
                                                                   self.verbose)

        # add validation functions to spinbox
        # this function validate user's input (not from experiment file)
        # and will stop propagating errors to any 'parent' functions
        # the only thing is that when the user's input is smaller than the limits, 
        # it will show inputs in red, but still let the function know the inputs changed
        # I can not block it since the Tkinter's working strategy
        # validate_wrapper(self.view.stack_acq_frame.step_size_spinbox)
        # validate_wrapper(self.view.stack_acq_frame.start_pos_spinbox)
        # validate_wrapper(self.view.stack_acq_frame.end_pos_spinbox)

        validate_wrapper(self.view.stack_timepoint_frame.stack_pause_spinbox)
        validate_wrapper(self.view.stack_timepoint_frame.exp_time_spinbox, is_integer=True)

        # Get Widgets and Buttons from stack_acquisition_settings in view
        self.stack_acq_widgets = self.view.stack_acq_frame.get_widgets()
        self.stack_acq_vals = self.view.stack_acq_frame.get_variables()
        self.stack_acq_buttons = self.view.stack_acq_frame.get_buttons()

        # stack acquisition variables
        # self.stack_acq_vals = {
        #     'step_size': self.view.stack_acq_frame.step_size_spinval,
        #     'start_position': self.view.stack_acq_frame.start_pos_spinval,
        #     'end_position': self.view.stack_acq_frame.end_pos_spinval,
        #     'number_z_steps': self.view.stack_acq_frame.slice_spinval,
        #     'start_focus': self.view.stack_acq_frame.start_foc_spinval,
        #     'end_focus': self.view.stack_acq_frame.end_foc_spinval,
        #     'abs_z_start': self.view.stack_acq_frame.abs_z_start_spinval,
        #     'abs_z_end': self.view.stack_acq_frame.abs_z_end_spinval
        # }
        # stack acquisition event binds
        self.stack_acq_vals['step_size'].trace_add('write', self.update_z_steps)
        self.stack_acq_vals['start_position'].trace_add('write', self.update_z_steps)
        self.stack_acq_vals['end_position'].trace_add('write', self.update_z_steps)
        # self.view.stack_acq_frame.set_start_button.configure(command=self.update_start_position)
        # self.view.stack_acq_frame.set_end_button.configure(command=self.update_end_position)
        self.stack_acq_buttons['set_start'].configure(command=self.update_start_position)
        self.stack_acq_buttons['set_end'].configure(command=self.update_end_position)

        # stack acquisition_variables
        self.z_origin = 0
        self.focus_origin = 0

        # laser/stack cycling variable
        self.stack_cycling_val = self.view.stack_acq_frame.cycling_options
        # laser/stack cycling event binds
        self.stack_cycling_val.trace_add('write', self.update_cycling_setting)

        # time point setting variables
        self.timepoint_vals = {
            'is_save': self.view.stack_timepoint_frame.save_data,
            'timepoints': self.view.stack_timepoint_frame.exp_time_spinval,
            'stack_acq_time': self.view.stack_timepoint_frame.stack_acq_spinval,
            'stack_pause': self.view.stack_timepoint_frame.stack_pause_spinval,
            'timepoint_interval': self.view.stack_timepoint_frame.timepoint_interval_spinval,
            'experiment_duration': self.view.stack_timepoint_frame.total_time_spinval
        }
        # timepoint event id
        self.timepoint_event_id = None

        # timepoint event binds
        self.timepoint_vals['is_save'].trace_add('write', self.update_save_setting)
        self.timepoint_vals['timepoints'].trace_add('write', lambda *args: self.update_timepoint_setting(True))
        self.timepoint_vals['stack_pause'].trace_add('write', lambda *args: self.update_timepoint_setting(True))

        # multiposition
        self.is_multiposition = False
        self.is_multiposition_val = self.view.multipoint_frame.on_off
        self.view.multipoint_frame.save_check.configure(command=self.toggle_multiposition)
        self.view.multipoint_frame.buttons["tiling"].configure(command=self.launch_tiling_wizard)

        if configuration_controller:
            self.initialize(configuration_controller)
         

    def initialize(self,
                   config):
        r"""Function initializes widgets and gets other necessary configuration

        Parameters
        ----------
        config : object
            ASLM_Configuration_Controller.  config.configuration = Session object.
        """
        self.set_channel_num(config.configuration.GUIParameters['number_of_channels'])
        self.view.stack_acq_frame.inputs['cycling'].set_values(('Per Z', 'Per Stack'))
        self.view.stack_acq_frame.inputs['cycling'].set('Per Z')
        self.stage_velocity = config.configuration.StageParameters['velocity']
        self.filter_wheel_delay = config.configuration.FilterWheelParameters['filter_wheel_delay']
        self.channel_setting_controller.initialize(config)
        self.set_spinbox_range_limits(config.configuration.GUIParameters)
        self.show_verbose_info('channels tab has been initialized')

    def set_experiment_values(self,
                              microscope_state):
        """Distribute initial MicroscopeState values to this and sub-controllers and associated views.

        Parameters
        ----------
        microscope_state : dict
            experiment.MicroscopeState from aslm_controller
        """
        self.in_initialization = True
        self.set_info(self.stack_acq_vals, microscope_state)
        # validate
        # self.view.stack_acq_frame.step_size_spinbox.validate()
        # self.view.stack_acq_frame.start_pos_spinbox.validate()
        # self.view.stack_acq_frame.end_pos_spinbox.validate()

        self.set_info(self.timepoint_vals, microscope_state)
        # validate
        self.view.stack_timepoint_frame.stack_pause_spinbox.validate()
        self.view.stack_timepoint_frame.exp_time_spinbox.validate()

        self.stack_cycling_val.set('Per Z' if microscope_state['stack_cycling_mode'] == 'per_z' else 'Per Stack')
        self.channel_setting_controller.set_experiment_values(microscope_state['channels'])

        # positions
        self.multi_position_controller.set_positions(microscope_state['stage_positions'])
        
        # after initialization
        self.in_initialization = False
        self.channel_setting_controller.in_initialization = False
        self.update_z_steps()

        self.show_verbose_info('Channels tab has been set new values')

    def update_experiment_values(self,
                                 microscope_state):
        """Updates MicroscopeState in ASLM Controller.

        Parameters
        ----------
        microscope_state : dict
            experiment.MicroscopeState from aslm_controller

        Returns
        -------
        microscope_state : dict
            experiment.MicroscopeState from aslm_controller
        """

        # Not included in stack_acq_vals or timepoint_vals
        microscope_state['stage_positions'] = self.multi_position_controller.get_positions()
        microscope_state['channels'] = self.channel_setting_controller.get_values()
        microscope_state['stack_cycling_mode'] = 'per_stack' if self.stack_cycling_val.get() == 'Per Stack' else 'per_z'
        microscope_state['stack_z_origin'] = self.z_origin
        microscope_state['stack_focus_origin'] = self.focus_origin
        microscope_state['is_multiposition'] = self.is_multiposition_val.get()

        # TODO: get_info acts a setter here
        r1 = self.get_info(self.stack_acq_vals, microscope_state)  # update MicroscopeState with everything in stack_acq_vals
        r2 = self.get_info(self.timepoint_vals, microscope_state)  # update MicroscopeState with everything in timepoint_vals
        return microscope_state['channels'] is not None and r1 is not None and r2 is not None

    def set_channel_num(self,
                        num):
        r"""Change the number of channels.

        Parameters
        ----------
        num : int
            Number of channels. e.g. 5.
        """
        self.channel_setting_controller.set_num(num)
        self.show_verbose_info('Channel number is', num)

    def set_spinbox_range_limits(self,
                                 settings):
        r"""This function will set the spinbox widget's values of from_, to, step

        Parameters
        ----------
        settings :
        """
        temp_dict = {
            self.stack_acq_widgets['step_size']: settings['stack_acquisition']['step_size'],
            self.stack_acq_widgets['start_position']: settings['stack_acquisition']['start_pos'],
            self.stack_acq_widgets['end_position']: settings['stack_acquisition']['end_pos'],
            self.view.stack_timepoint_frame.stack_pause_spinbox: settings['timepoint']['stack_pause'],
            self.view.stack_timepoint_frame.exp_time_spinbox: settings['timepoint']['timepoints']
        }
        for idx, widget in enumerate(temp_dict):
            # Hacky Solution until stack time points are converted to LabelInput
            if idx < 3:
                widget.widget.configure(from_=temp_dict[widget]['min'])
                widget.widget.configure(to=temp_dict[widget]['max'])
                widget.widget.configure(increment=temp_dict[widget]['step'])
            else:
                widget.configure(from_=temp_dict[widget]['min'])
                widget.configure(to=temp_dict[widget]['max'])
                widget.configure(increment=temp_dict[widget]['step'])

        # channels setting
        self.channel_setting_controller.set_spinbox_range_limits(settings['channel'])
    
    def set_mode(self,
                 mode):
        r"""Change acquisition mode.

        Parameters
        ----------
        mode : str
            'stop'
        """
        self.mode = mode
        self.channel_setting_controller.set_mode(mode)

        stack_state = 'disabled' if mode == 'z-stack' else 'active'
        for key, widget in self.stack_acq_widgets.items():
            if key == 'abs_z_start' or key == 'abs_z_end' or key == 'number_z_steps':
                continue
            widget.widget.configure(state=stack_state)

        state = 'normal' if mode == 'stop' else 'disabled'
        self.view.stack_timepoint_frame.save_check['state'] = state
        self.view.stack_timepoint_frame.stack_pause_spinbox['state'] = state
        self.view.stack_timepoint_frame.exp_time_spinbox['state'] = state
        self.view.stack_acq_frame.inputs["cycling"]['state'] = 'readonly' if state == 'normal' else state
        self.show_verbose_info('acquisition mode has been changed to', mode)

    def update_z_steps(self,
                       *args):
        r"""Recalculates the number of slices that will be acquired in a z-stack.

        Requires GUI to have start position, end position, or step size changed.
        Sets the number of slices in the model and the GUI.
        Sends the current values to central/parent controller

        Parameters
        ----------
        args : dict
            Values is a dict as follows {'step_size':  'start_position': , 'end_position': ,'number_z_steps'}
        """

        # won't do any calculation when initialization
        if self.in_initialization:
            return

        # Calculate the number of slices and set GUI
        try:
            # validate the spinbox's value
            start_position = float(self.stack_acq_vals['start_position'].get())
            end_position = float(self.stack_acq_vals['end_position'].get())
            step_size = float(self.stack_acq_vals['step_size'].get())
            if step_size < 0.001:
                self.stack_acq_vals['number_z_steps'].set(0)
                self.stack_acq_vals['abs_z_start'].set(0)
                self.stack_acq_vals['abs_z_end'].set(0)
                return
        except:
            self.stack_acq_vals['number_z_steps'].set(0)
            self.stack_acq_vals['abs_z_start'].set(0)
            self.stack_acq_vals['abs_z_end'].set(0)
            # if self.stack_acq_event_id:
            #     self.view.after_cancel(self.stack_acq_event_id)
            return

        # if step_size < 0.001:
        #     step_size = 0.001
        #     self.stack_acq_vals['step_size'].set(step_size)

        number_z_steps = int(np.abs(np.floor((end_position - start_position) / step_size)))
        self.stack_acq_vals['number_z_steps'].set(number_z_steps)

        # Shift the start/stop positions by the relative position
        self.stack_acq_vals['abs_z_start'].set(self.z_origin + start_position)
        self.stack_acq_vals['abs_z_end'].set(self.z_origin + end_position)

        self.update_timepoint_setting()
        self.show_verbose_info('stack acquisition settings on channels tab have been changed and recalculated')

    def update_start_position(self, *args):
        r"""Get new z starting position from current stage parameters.

        Parameters
        ----------
        args : None
            ?
        """

        # We have a new origin
        self.z_origin = self.parent_controller.experiment.StageParameters['z']
        self.focus_origin = self.parent_controller.experiment.StageParameters['f']
        self.stack_acq_vals['start_position'].set(0)
        self.stack_acq_vals['start_focus'].set(0)

        # Propagate parameter changes to the GUI
        self.update_z_steps()

    def update_end_position(self, *args):
        r"""Get new z ending position from current stage parameters

        Parameters
        ----------
        args : ?
            ?
        """
        # Grab current values
        z_curr = self.parent_controller.experiment.StageParameters['z']
        focus_curr = self.parent_controller.experiment.StageParameters['f']

        # Propagate parameter changes to the GUI
        self.stack_acq_vals['end_position'].set(z_curr - self.z_origin)
        self.stack_acq_vals['end_focus'].set(focus_curr - self.focus_origin)
        self.update_z_steps()

    def update_cycling_setting(self,
                               *args):
        """Update the cycling settings in the model and the GUI.

        You can collect different channels in different formats.
        In the perZ format: Slice 0/Ch0, Slice0/Ch1, Slice1/Ch0, Slice1/Ch1, etc
        in the perStack format: Slice 0/Ch0, Slice1/Ch0... SliceN/Ch0.  Then it repeats with Ch1

        Parameters
        ----------
        args : ?
            ?
        """
        # won't do any calculation when initializing
        if self.in_initialization:
            return
        # recalculate time point settings
        self.update_timepoint_setting()

        # tell the central/parent controller that laser cycling setting is changed when mode is 'live'
        if self.mode == 'live':
            self.parent_controller.execute('update_setting', 'laser_cycling', self.stack_cycling_val.get())
        self.show_verbose_info('Cycling setting on channels tab has been changed')

    def update_save_setting(self,
                            *args):
        r"""Tell the centrol/parent controller 'save_data' is selected.

        Does not do any calculation when initializing the software.

        Parameters
        ----------
        args : ?
            ?
        """
        if self.in_initialization:
            return
        self.is_save = self.timepoint_vals['is_save'].get()
        self.parent_controller.execute('set_save', self.is_save)
        self.show_verbose_info('Save data option has been changed to', self.is_save)

    def update_timepoint_setting(self,
                                 call_parent=False):
        r"""Automatically calculates the stack acquisition time based on the number of time points,
        channels, and exposure time.

        TODO: Add necessary computation for 'Stack Acq.Time', 'Timepoint Interval', 'Experiment Duration'?

        Does not do any calculation when initializing the software.
        Order of priority for perStack: timepoints > positions > channels > z-steps > delay
        ORder of priority for perZ: timepoints > positions > z-steps > delays > channels

        Parameters
        ----------
        call_parent : bool
            Tell parent controller that time point setting has changed.
        """
        if self.in_initialization:
            return
        channel_settings = self.channel_setting_controller.get_values()
        number_of_positions = self.multi_position_controller.get_position_num() if self.is_multiposition else 1
        channel_exposure_time = []
        # validate the spinbox's value
        try:
            number_of_timepoints = int(float(self.timepoint_vals['timepoints'].get()))
            number_of_slices = int(self.stack_acq_vals['number_z_steps'].get())
            for channel_id in channel_settings:
                channel = channel_settings[channel_id]
                channel_exposure_time.append(float(channel['camera_exposure_time']))
            if len(channel_exposure_time) == 0:
                return
        except:
            self.timepoint_vals['experiment_duration'].set('')
            self.timepoint_vals['stack_acq_time'].set('')
            if call_parent and self.timepoint_event_id:
                self.view.after_cancel(self.timepoint_event_id)
            return

        perStack = self.stack_cycling_val.get() == 'Per Stack'

        # Initialize variable to keep track of how long the entire experiment will take.
        # Includes time, positions, channels...
        experiment_duration = 0

        # Initialize variable to calculate how long it takes to acquire a single volume for all of the channels.
        # Only calculate once at the beginning.
        stack_acquisition_duration = 0

        for timepoint_idx in range(number_of_timepoints):

            for position_idx in range(number_of_positions):
                # For multiple positions, need to account for the time necessary to move the stages that distance.
                # In theory, these positions would be populated in that 'pandastable' or some other data structure.

                # Determine the largest distance to travel between positions.  Assume all axes move the same velocity
                # This assumes that we are in a multi-position mode. Not yet implemented.
                # x1, y1, z1, theta1, f1, = position_start.values()
                # x2, y2, z1, theta2, f1 = position_end.values()
                # distance = [x2-x1, y2-y1, z2-z1, theta2-theta1, f2-f1]
                # max_distance_idx = np.argmax(distance)
                # Now if we are going to do this properly, we would need to do this for all of the positions
                # so that we can calculate the total experiment time.
                # Probably assemble a matrix of all the positions and then do the calculations.

                stage_delay = 0  # distance[max_distance_idx]/self.stage_velocity #TODO False value.

                # If we were actually acquiring the data, we would call the function to move the stage here.
                experiment_duration = experiment_duration + stage_delay

                for channel_idx in range(len(channel_exposure_time)):
                    # Change the filter wheel here before the start of the acquisition.
                    if perStack:
                        # In the perStack mode, we only need to account for the time necessary for the filter wheel
                        # to change between each image stack.
                        experiment_duration = experiment_duration + self.filter_wheel_delay

                    for slice_idx in range(number_of_slices):
                        # Now we need to know the exposure time of each channel.
                        # Assumes no delay between individual slices at this point.
                        # Convert from milliseconds to seconds.
                        experiment_duration = experiment_duration + channel_exposure_time[channel_idx] / 1000

                        if channel_idx == 0 and position_idx == 0 and timepoint_idx == 0:
                            stack_acquisition_duration = stack_acquisition_duration + channel_exposure_time[channel_idx] / 1000

                        if not perStack:
                            # In the perZ mode, we need to account for the time necessary to move the filter wheel
                            # at each slice
                            experiment_duration = experiment_duration + self.filter_wheel_delay

                            if channel_idx == 0 and position_idx == 0 and timepoint_idx == 0:
                                stack_acquisition_duration = stack_acquisition_duration + channel_exposure_time[channel_idx] / 1000

        self.timepoint_vals['experiment_duration'].set(experiment_duration)
        self.timepoint_vals['stack_acq_time'].set(stack_acquisition_duration)

        # call central controller
        if call_parent:
            self.timepoint_callback()

        self.show_verbose_info('timepoint settings on channels tab have been changed and recalculated')

    def timepoint_callback(self):
        r"""Tell central controller that time point setting has been changed when mode is 'live'.
        """
        if self.mode == 'live':
            if self.timepoint_event_id:
                self.view.after_cancel(self.timepoint_event_id)
            temp = self.get_info(self.timepoint_vals)
            if not temp:
                return
            self.timepoint_event_id = self.view.after(1000, lambda: self.parent_controller.execute('update_setting', 'timepoint', temp))

    def toggle_multiposition(self):
        r"""Toggle Multi-position Acquisition.

        Recalculates the experiment duration.
        """
        self.is_multiposition = self.is_multiposition_val.get()
        self.update_timepoint_setting()
        self.show_verbose_info('Multi-position:', self.is_multiposition)


    def launch_tiling_wizard(self):
        r"""Launches tiling wizard popup.

        Will only launch when button in GUI is pressed, and will not duplicate. Pressing button again brings popup to top
        """

        if hasattr(self, 'tiling_wizard_controller'):
            self.tiling_wizard_controller.showup()
            return
        tiling_wizard_popup = tiling_wizard(self.view)
        self.tiling_wizard_controller = Tiling_Wizard_Controller(tiling_wizard_popup,
                                                                 self,
                                                                 self.verbose)




    def load_positions(self):
        r"""Load Positions for Multi-Position Acquisition. """
        self.multi_position_controller.load_csv_func()

    def export_positions(self):
        r"""Export Positions for Multi-Position Acquisition. """
        self.multi_position_controller.export_csv_func()

    def move_to_position(self):
        r"""Move to a position within the Multi-Position Acquisition Interface."""
        event = type('MyEvent', (object,), {})
        event.x, event.y = 0, 0
        self.multi_position_controller.handle_double_click(event)

    def append_current_position(self):
        r"""Add current position to the Multi-Position Acquisition Interface."""
        self.multi_position_controller.add_stage_position_func()

    def generate_positions(self):
        r"""Generate a Multi-Position Acquisition."""
        self.multi_position_controller.generate_positions_func()

    def set_info(self,
                 vals,
                 values):
        r"""Set values to a list of variables."""
        for name in values:
            if name in vals:
                vals[name].set(values[name])

    def get_info(self,
                 vals,
                 value_dict={}):
        r"""Gets and assigns parameters in vals to corresponding parameter in value_dict.

        TODO: perhaps rename to map_values or the like?

        Parameters
        ----------
        vals : dict
            Dictionary of parameters (source)
        value_dict : dict
            Dictionary of parameters (target)

        Returns
        -------
        value_dict : dict
            Dictionary of values.
        """
        for name in vals:
            value_dict[name] = vals[name].get()
            if value_dict[name] == '':
                return None
        return value_dict

    def execute(self,
                command,
                *args):
        r"""Execute Command in the parent controller.

        Parameters
        ----------
        command : str
            recalculate_timepoint, channel, move_stage_and_update_info, get_stage_position

        Returns
        -------
        command : object
            Returns parent_controller.execute(command) if command = 'get_stage_position',
        """
        if command == 'recalculate_timepoint':
            self.update_timepoint_setting()
        elif (command == 'channel') or (command == 'move_stage_and_update_info') or (command == 'update_setting'):
            self.view.after(1000, lambda: self.parent_controller.execute(command, *args))
        elif command == 'get_stage_position':
            return self.view.after(1000, lambda: self.parent_controller.execute(command))
        self.show_verbose_info('Received command from child', command, args)
