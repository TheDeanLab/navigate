import _tkinter
import numpy as np
from controller.sub_controllers.widget_functions import validate_float_wrapper
from controller.sub_controllers.gui_controller import GUI_Controller
from controller.sub_controllers.channel_setting_controller import Channel_Setting_Controller
from controller.sub_controllers.multi_position_controller import Multi_Position_Controller


class Channels_Tab_Controller(GUI_Controller):
    def __init__(self, view, parent_controller=None, verbose=False):
        super().__init__(view, parent_controller, verbose)

        self.is_save = False
        self.mode = 'stop'
        self.settings_from_configuration = {}
        self.channel_setting_controller = Channel_Setting_Controller(self.view.channel_widgets_frame, self,
                                                                     self.verbose)
        self.multi_position_controller = Multi_Position_Controller(self.view.multipoint_list, self, self.verbose)

        # add validation functions to spinbox
        # this function validate user's input (not from experiment file)
        # and will stop propagating errors to any 'parent' functions
        # the only thing is that when the user's input is smaller than the limits, 
        # it will show inputs in red, but still let the function know the inputs changed
        # I can not block it since the Tkinter's working strategy
        validate_float_wrapper(self.view.stack_acq_frame.step_size_spinbox)
        validate_float_wrapper(self.view.stack_acq_frame.start_pos_spinbox)
        validate_float_wrapper(self.view.stack_acq_frame.end_pos_spinbox)

        validate_float_wrapper(self.view.stack_timepoint_frame.stack_pause_spinbox)
        validate_float_wrapper(self.view.stack_timepoint_frame.exp_time_spinbox)

        # stack acquisition variables
        self.stack_acq_vals = {
            'step_size': self.view.stack_acq_frame.step_size_spinval,
            'start_position': self.view.stack_acq_frame.start_pos_spinval,
            'end_position': self.view.stack_acq_frame.end_pos_spinval,
            'number_z_steps': self.view.stack_acq_frame.slice_spinval
        }
        # stack acquisition event id
        self.stack_acq_event_id = None
        # stack acquisition event binds
        self.stack_acq_vals['step_size'].trace_add('write', self.update_z_steps)
        self.stack_acq_vals['start_position'].trace_add('write', self.update_z_steps)
        self.stack_acq_vals['end_position'].trace_add('write', self.update_z_steps)

        # laser cycling variable
        self.laser_cycling_val = self.view.stack_cycling_frame.cycling_options
        # laser cycling event binds
        self.laser_cycling_val.trace_add('write', self.update_cycling_setting)

        # timepoint setting variables
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
        self.timepoint_vals['timepoints'].trace_add('write', self.update_timepoint_setting)
        self.timepoint_vals['stack_pause'].trace_add('write', self.update_timepoint_setting)
        self.timepoint_vals['timepoints'].trace_add('write', self.timepoint_callback)
        self.timepoint_vals['stack_pause'].trace_add('write', self.timepoint_callback)

        # multiposition
        self.is_multiposition = False
        self.is_multiposition_val = self.view.multipoint_frame.on_off
        self.view.multipoint_frame.save_check.configure(command=self.toggle_multiposition)

    def initialize(self, name, value):
        if name == 'channel':
            for col_name in value:
                self.channel_setting_controller.initialize(col_name, value[col_name])
        elif name == 'laser_cycling':
            self.view.stack_cycling_frame.cycling_pull_down['values'] = value
        else:
            self.set_values(name, value)

        self.show_verbose_info(name, 'on channels tab has been initialized')

    def set_values(self, name, value):
        if name == 'stack_acquisition':
            self.set_info(self.stack_acq_vals, value)
            # validate
            self.view.stack_acq_frame.step_size_spinbox.validate()
            self.view.stack_acq_frame.start_pos_spinbox.validate()
            self.view.stack_acq_frame.end_pos_spinbox.validate()
        elif name == 'timepoint':
            self.set_info(self.timepoint_vals, value)
            # validate
            self.view.stack_timepoint_frame.stack_pause_spinbox.validate()
            self.view.stack_timepoint_frame.exp_time_spinbox.validate()
        elif name == 'laser_cycling':
            self.laser_cycling_val.set(value)
        elif name == 'channel':
            self.channel_setting_controller.set_values(value)

        self.show_verbose_info(name, 'on channels tab has been set new values')

    def get_values(self, name=None):
        settings = {}
        settings['stack_acquisition'] = self.get_info(self.stack_acq_vals)
        settings['stack_cycling_mode'] = 'per_stack' if self.laser_cycling_val.get() == 'Per Stack' else 'per_z'
        settings['timepoint'] = self.get_info(self.timepoint_vals)
        settings['channel'] = self.channel_setting_controller.get_values()
        if name in settings:
            return settings[name]
        return settings

    def set_channel_num(self, num):
        """
        # change the number of channels
        """
        self.channel_setting_controller.set_num(num)

        self.show_verbose_info('channel number is', num)

    def set_mode(self, mode):
        """
        # change acquisition mode
        """
        self.mode = mode
        self.channel_setting_controller.set_mode(mode)

        self.show_verbose_info('acquisition mode has been changed to', mode)

    def update_z_steps(self, *args):
        """
        # Recalculates the number of slices that will be acquired in a z-stack whenever the GUI
        # has the start position, end position, or step size changed.
        # Sets the number of slices in the model and the GUI.
        # send the current values to central/parent controller
        # the values is a dict as follows
        # {
            'step_size': ,
            'start_position': ,
            'end_possition': ,
            'number_z_steps':
        # }
        """
        # Calculate the number of slices and set GUI
        try:
            # validate the spinbox's value
            start_position = float(self.stack_acq_vals['start_position'].get())
            end_position = float(self.stack_acq_vals['end_position'].get())
            step_size = float(self.stack_acq_vals['step_size'].get())
            if step_size < 0.001:
                self.stack_acq_vals['number_z_steps'].set('')
                return
        except:
            self.stack_acq_vals['number_z_steps'].set('')
            if self.stack_acq_event_id:
                self.view.after_cancel(self.stack_acq_event_id)
            return
        # if step_size < 0.001:
        #     step_size = 0.001
        #     self.stack_acq_vals['step_size'].set(step_size)

        number_z_steps = np.floor((end_position - start_position) / step_size)
        self.stack_acq_vals['number_z_steps'].set(number_z_steps)

        self.update_timepoint_setting()

        # tell the central controller that stack acquisition setting is changed when mode is 'live'
        if self.mode == 'live':
            if self.stack_acq_event_id:
                self.view.after_cancel(self.stack_acq_event_id)
            self.stack_acq_event_id = self.view.after(1000, \
                lambda: self.parent_controller.execute('stack_acquisition', self.get_info(self.stack_acq_vals)))

        self.show_verbose_info('stack acquisition settings on channels tab have been changed and recalculated')

    def update_cycling_setting(self, *args):
        """
        # Updates the cycling settings in the model and the GUI.
        # You can collect different channels in different formats.
        # In the perZ format: Slice 0/Ch0, Slice0/Ch1, Slice1/Ch0, Slice1/Ch1, etc
        # in the perStack format: Slice 0/Ch0, Slice1/Ch0... SliceN/Ch0.  Then it repeats with Ch1
        """
        # recalculate timepoint settings
        self.update_timepoint_setting()

        # tell the central/parent controller that laser cycling setting is changed when mode is 'live'
        if self.mode == 'live':
            self.parent_controller.execute('laser_cycling', self.laser_cycling_val.get())

        self.show_verbose_info('cycling setting on channels tab has been changed')

    def update_save_setting(self, *args):
        self.is_save = self.timepoint_vals['is_save'].get()
        # tell the centrol/parent controller 'save_data' is selected
        self.parent_controller.execute('set_save', self.is_save)

        self.show_verbose_info('save data option has been changed to', self.is_save)

    def update_timepoint_setting(self, *args):
        """
        # Automatically calculate the stack acquisition time based on the number of timepoints,
        #  channels, and exposure time.  Add necessary computation for 'Stack Acq.Time',
        #  'Timepoint Interval', 'Experiment Duration'?
        """

        # Order of priority for perStack: timepoints > positions > channels > z-steps > delay
        # ORder of priority for perZ: timepoints > positions > z-steps > delays > channels

        channel_settings = self.channel_setting_controller.get_values()
        number_of_positions = self.multi_position_controller.get_position_num() if self.is_multiposition else 1
        stage_velocity = self.settings_from_configuration['stage_velocity']
        filter_wheel_delay = self.settings_from_configuration['filter_wheel_delay']
        channel_exposure_time = []
        # validate the spinbox's value
        try:
            number_of_timepoints = self.timepoint_vals['timepoints'].get()
            number_of_slices = int(self.stack_acq_vals['number_z_steps'].get())
            for channel_id in channel_settings:
                channel = channel_settings[channel_id]
                channel_exposure_time.append(float(channel['camera_exposure_time']))
            if len(channel_exposure_time) == 0:
                return
        except:
            self.timepoint_vals['experiment_duration'].set('')
            self.timepoint_vals['stack_acq_time'].set('')
            return

        perStack = self.laser_cycling_val.get() == 'Per Stack'

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

                stage_delay = 0  # distance[max_distance_idx]/stage_velocity #TODO False value.

                # If we were actually acquiring the data, we would call the function to move the stage here.
                experiment_duration = experiment_duration + stage_delay

                for channel_idx in range(len(channel_exposure_time)):
                    # Change the filter wheel here before the start of the acquisition.
                    if perStack:
                        # In the perStack mode, we only need to account for the time necessary for the filter wheel
                        # to change between each image stack.
                        experiment_duration = experiment_duration + filter_wheel_delay

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
                            experiment_duration = experiment_duration + filter_wheel_delay

                            if channel_idx == 0 and position_idx == 0 and timepoint_idx == 0:
                                stack_acquisition_duration = stack_acquisition_duration + channel_exposure_time[channel_idx] / 1000

        self.timepoint_vals['experiment_duration'].set(experiment_duration)
        self.timepoint_vals['stack_acq_time'].set(stack_acquisition_duration)

        self.show_verbose_info('timepoint settings on channels tab have been changed and recalculated')

    def timepoint_callback(self, *args):
        """
        # this function call central controller that timepoint setting has been changed
        """
        # tell the central controller that timepoint's setting has changed when mode is 'live'
        if self.mode == 'live':
            if self.timepoint_event_id:
                self.view.after_cancel(self.timepoint_event_id)
            temp = self.get_info(self.timepoint_vals)
            if not temp:
                return
            self.timepoint_event_id = self.view.after(1000, lambda: self.parent_controller.execute('timepoint', temp))

    def toggle_multiposition(self):
        self.is_multiposition = self.is_multiposition_val.get()
        # recalculate experiment time
        self.update_timepoint_setting()
        self.show_verbose_info('multi-position:', self.is_multiposition)

    def load_positions(self):
        self.multi_position_controller.load_csv_func()

    def export_positions(self):
        self.multi_position_controller.export_csv_func()

    def move_to_position(self):
        event = type('MyEvent', (object,), {})
        event.x, event.y = 0, 0
        self.multi_position_controller.handle_double_click(event)

    def append_current_position(self):
        self.multi_position_controller.add_stage_position_func()

    def generate_positions(self):
        self.multi_position_controller.generate_positions_func()

    def set_positions(self, positions):
        self.multi_position_controller.set_positions(positions)

    def get_positions(self):
        return self.multi_position_controller.get_positions()

    def set_info(self, vals, values):
        """
        # set values to a list of variables
        """
        for name in values:
            if name in vals:
                vals[name].set(values[name])

    def get_info(self, vals):
        """
        # get values from a list of variables
        """
        info = {}
        try:
            for name in vals:
                info[name] = vals[name].get()
        except _tkinter.TclError:
            print('invalid inputs')
            return None
        return info

    def execute(self, command, *args):
        if command == 'recalculate_timepoint':
            self.update_timepoint_setting()
        elif command == 'channel':
            self.parent_controller.execute(command, *args)
        elif command == 'move_stage_and_update_info':
            self.parent_controller.execute(command, *args)
        elif command == 'get_stage_position':
            return self.parent_controller.execute(command)

        self.show_verbose_info('get command from child', command, args)
