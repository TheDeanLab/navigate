import numpy as np
from view.gui_controller import GUI_Controller
from view.main_window_content.tabs.channels.channel_setting_controller import Channel_Setting_Controller

class Channels_Tab_Controller(GUI_Controller):
    def __init__(self, view, parent_controller=None):
        super().__init__(view, parent_controller)

        self.is_save = False

        self.channel_setting_controller = Channel_Setting_Controller(self.view.channel_widgets_frame, self)
        
        # stack acquisition variables
        self.stack_acq_vals = {
            'step_size': self.view.stack_acq_frame.step_size_spinval,
            'start_pos': self.view.stack_acq_frame.start_pos_spinval,
            'end_pos': self.view.stack_acq_frame.end_pos_spinval,
            'slice':  self.view.stack_acq_frame.slice_spinval
        }
        # stack acquisition event id
        self.stack_acq_event_id = None
        # stack acquisition event binds
        self.stack_acq_vals['step_size'].trace_add('write', self.update_z_steps)
        self.stack_acq_vals['start_pos'].trace_add('write', self.update_z_steps)
        self.stack_acq_vals['end_pos'].trace_add('write', self.update_z_steps)

        # laser cycling variable
        self.laser_cycling_val = self.view.stack_cycling_frame.cycling_options
        # laser cycling event binds
        self.laser_cycling_val.trace_add('write', self.update_cycling_setting)

        # timepoint setting variables
        self.timepoint_vals =  {
            'is_save': self.view.stack_timepoint_frame.save_data,
            'timepoint': self.view.stack_timepoint_frame.exp_time_spinval,
            'stack_acq_time': self.view.stack_timepoint_frame.stack_acq_spinval,
            'stack_pause': self.view.stack_timepoint_frame.stack_pause_spinval,
            'timepoint_interval': self.view.stack_timepoint_frame.timepoint_interval_spinval,
            'experiment_duration': self.view.stack_timepoint_frame.total_time_spinval
        }
        
        # save data event binds
        self.timepoint_vals['is_save'].trace_add('write', self.update_save_setting)

    def initialize(self, name, value):
        if name == 'channels':
            for col_name in value:
                self.channel_setting_controller.initialize(col_name, value[col_name])
        elif name == 'stack_acquisition':
            for col_name in value:
                if col_name not in self.stack_acq_vals:
                    continue
                self.stack_acq_vals[col_name].set(value[col_name])
        elif name == 'laser_cycling':
            self.view.stack_cycling_frame.cycling_pull_down['values'] = value

    def update_z_steps(self, *args):
        '''
        # Recalculates the number of slices that will be acquired in a z-stack whenever the GUI
        # has the start position, end position, or step size changed.
        # Sets the number of slices in the model and the GUI.
        '''
        # Calculate the number of slices and set GUI
        start_position = np.float(self.stack_acq_vals['start_pos'].get())
        end_position = np.float(self.stack_acq_vals['end_pos'].get())
        step_size = np.float(self.stack_acq_vals['step_size'].get())
        number_z_steps = np.floor((end_position - start_position)/step_size)
        self.stack_acq_vals['slice'].set(number_z_steps)

        # tell central controller that stack acquisition setting is changed
        if self.stack_acq_event_id:
            self.view.after_cancel(self.stack_acq_event_id)
        self.stack_acq_event_id = self.view.after(1000, \
            lambda: self.parent_controller.execute('stack_acquisition', self.get_stack_acq_info()))

    def update_cycling_setting(self, *args):
        '''
        # Updates the cycling settings in the model and the GUI.
        # You can collect different channels in different formats.
        # In the perZ format: Slice 0/Ch0, Slice0/Ch1, Slice1/Ch0, Slice1/Ch1, etc
        # in the perStack format: Slice 0/Ch0, Slice1/Ch0... SliceN/Ch0.  Then it repeats with Ch1
        '''
        # tell the central/parent controller that laser cycling setting is changed
        self.parent_controller.execute('laser_cycling', self.laser_cycling_val.get())

    def update_save_setting(self, *args):
        self.is_save = self.timepoint_vals['is_save'].get()
        self.parent_controller.execute('save', self.is_save)

    def get_stack_acq_info(self):
        stack_acq_info = {}
        for name in self.stack_acq_vals:
            stack_acq_info[name] = self.stack_acq_vals[name].get()
        return stack_acq_info
