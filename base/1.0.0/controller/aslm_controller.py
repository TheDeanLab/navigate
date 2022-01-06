"""
This is the controller in an MVC-scheme for mediating the interaction between the View (GUI) and the model (./model/aslm_model.py).
Use: https://www.python-course.eu/tkinter_events_binds.php
"""
# Import Standard Python Packages
import numpy as np

# Local Imports
from view.main_application_window import Main_App as view
from controller.aslm_controller_functions import *
from model.aslm_model import Model

class ASLM_controller():
    def __init__(self, root, configuration_path, args):
        self.verbose = args.verbose

        # Initialize the Model
        global model
        self.model = Model(args, configuration_path)

        # Initialize the View
        self.view = view(root)

        #TODO: camera_view_tab, maximum intensity tab, waveform_tab
        # still need to be changed so that they are populated here.

        # Populate the View with the Model

        # Channels Tab, Channel Settings
        # Select only a single channel by default.
        self.view.notebook_1.channels_tab.channel_widgets_frame.channel_variables[0].set(True)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.channel_variables[1].set(False)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.channel_variables[2].set(False)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.channel_variables[3].set(False)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.channel_variables[4].set(False)

        '''
        Loop to populate the channel settings******************************
        Code above and below that is commented out is no longer needed
        '''
        
        for x in range(5):
            self.view.notebook_1.channels_tab.channel_widgets_frame.laser_pulldowns[x]['values'] = populate_lasers(self, self.verbose)
            self.view.notebook_1.channels_tab.channel_widgets_frame.filterwheel_pulldowns[x]['values'] = \
                list(self.model.session.FilterWheelParameters['available_filters'].keys())
            self.view.notebook_1.channels_tab.channel_widgets_frame.exptime_variables[x].set(self.model.session.CameraParameters['camera_exposure_time'])

        '''
        End of loop
        '''

        # Populate the lasers in the GUI
        # self.view.notebook_1.channels_tab.channel_widgets_frame.laser_pulldowns[0]['values'] = populate_lasers(self, self.verbose)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.laser_pulldowns[1]['values'] = populate_lasers(self)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.laser_pulldowns[2]['values'] = populate_lasers(self)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.laser_pulldowns[3]['values'] = populate_lasers(self)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.laser_pulldowns[4]['values'] = populate_lasers(self)
        
            
        # Populate the filters in the GUI
        # self.view.notebook_1.channels_tab.channel_widgets_frame.filterwheel_pulldowns[0]['values'] = \
        #     list(self.model.session.FilterWheelParameters['available_filters'].keys())
        # self.view.notebook_1.channels_tab.channel_widgets_frame.filterwheel_pulldowns[1]['values'] = \
        #     list(self.model.session.FilterWheelParameters['available_filters'].keys())
        # self.view.notebook_1.channels_tab.channel_widgets_frame.filterwheel_pulldowns[2]['values'] = \
        #     list(self.model.session.FilterWheelParameters['available_filters'].keys())
        # self.view.notebook_1.channels_tab.channel_widgets_frame.filterwheel_pulldowns[3]['values'] = \
        #     list(self.model.session.FilterWheelParameters['available_filters'].keys())
        # self.view.notebook_1.channels_tab.channel_widgets_frame.filterwheel_pulldowns[4]['values'] = \
        #     list(self.model.session.FilterWheelParameters['available_filters'].keys())

        # Populate the exposure times in the GUI
        # self.view.notebook_1.channels_tab.channel_widgets_frame.exptime_variables[0].set(self.model.session.CameraParameters['camera_exposure_time'])
        # self.view.notebook_1.channels_tab.channel_widgets_frame.exptime_variables[1].set(self.model.session.CameraParameters['camera_exposure_time'])
        # self.view.notebook_1.channels_tab.channel_widgets_frame.exptime_variables[2].set(self.model.session.CameraParameters['camera_exposure_time'])
        # self.view.notebook_1.channels_tab.channel_widgets_frame.exptime_variables[3].set(self.model.session.CameraParameters['camera_exposure_time'])
        # self.view.notebook_1.channels_tab.channel_widgets_frame.exptime_variables[4].set(self.model.session.CameraParameters['camera_exposure_time'])

        # Define all of the callbacks/events.
        # Acquire bar
        self.view.acqbar.acquire_btn.config(command=lambda: launch_popup_window(self, root, self.verbose))
        self.view.acqbar.exit_btn.config(command=lambda: exit_program(self.verbose))
        self.view.acqbar.pull_down.bind('<<ComboboxSelected>>', lambda *args: update_microscope_mode(self, self.verbose))

        # Channels Tab, Stack Acquisition Settings
        self.view.notebook_1.channels_tab.stack_acq_frame.start_pos_spinval.trace_add('write', lambda *args: update_z_steps(self, self.verbose))
        self.view.notebook_1.channels_tab.stack_acq_frame.step_size_spinval.trace_add('write', lambda *args: update_z_steps(self, self.verbose))
        self.view.notebook_1.channels_tab.stack_acq_frame.end_pos_spinval.trace_add('write', lambda *args: update_z_steps(self, self.verbose))

        # Channels Tab, Laser Cycling Settings
        self.view.notebook_1.channels_tab.stack_cycling_frame.cycling_options.trace_add('write', lambda *args: update_cycling_settings(self, self.verbose))

        # Channels Tab, Timepoint Settings
        self.view.notebook_1.channels_tab.stack_timepoint_frame.exp_time_spinval.trace_add('write', lambda *args: update_time_points(self, self.verbose))
        #TODO: Automatically calculate the stack acquisition time based on the number of timepoints, channels, and exposure time.

        # Channels Tab, Multi-position Acquisition Settings

        # Camera Tab, Camera Settings

        # Advanced Tab

        # Stage Notebook
        # Prepopulate the stage positions.
        self.view.notebook_3.stage_control_tab.position_frame.x_val.set(self.model.stages.x_pos)
        self.view.notebook_3.stage_control_tab.position_frame.y_val.set(self.model.stages.y_pos)
        self.view.notebook_3.stage_control_tab.position_frame.z_val.set(self.model.stages.z_pos)
        self.view.notebook_3.stage_control_tab.position_frame.theta_val.set(self.model.stages.theta_pos)
        self.view.notebook_3.stage_control_tab.position_frame.focus_val.set(self.model.stages.f_pos)

        # Prepopulate the stage step size.
        self.view.notebook_3.stage_control_tab.x_y_frame.increment_box.set(self.model.session.StageParameters['xy_step'])
        self.view.notebook_3.stage_control_tab.z_frame.increment_box.set(self.model.session.StageParameters['z_step'])
        self.view.notebook_3.stage_control_tab.theta_frame.increment_box.set(self.model.session.StageParameters['theta_step'])
        self.view.notebook_3.stage_control_tab.focus_frame.increment_box.set(self.model.session.StageParameters['f_step'])

        # Configure event control for the buttons
        self.view.menu_zoom.bind("<<MenuSelect>>", lambda *args: print("Zoom Selected", *args))

        #TODO: Replace print functions with calls to the stage controller.
        self.view.notebook_3.stage_control_tab.x_y_frame.negative_x_btn.config(command=lambda: print("x-"))
        self.view.notebook_3.stage_control_tab.x_y_frame.positive_x_btn.config(command=lambda: print("x+"))
        self.view.notebook_3.stage_control_tab.x_y_frame.negative_y_btn.config(command=lambda: print("y-"))
        self.view.notebook_3.stage_control_tab.x_y_frame.positive_y_btn.config(command=lambda: print("y+"))
        self.view.notebook_3.stage_control_tab.x_y_frame.zero_x_y_btn.config(command=lambda: print("Zero x-y"))

        self.view.notebook_3.stage_control_tab.z_frame.down_btn.config(command=lambda: print("z-"))
        self.view.notebook_3.stage_control_tab.z_frame.up_btn.config(command=lambda: print("z+"))
        self.view.notebook_3.stage_control_tab.z_frame.zero_z_btn.config(command=lambda: print("Zero z"))

        self.view.notebook_3.stage_control_tab.theta_frame.up_btn.config(command=lambda: print("theta-"))
        self.view.notebook_3.stage_control_tab.theta_frame.down_btn.config(command=lambda: print("theta+"))
        self.view.notebook_3.stage_control_tab.theta_frame.zero_theta_btn.config(command=lambda: print("Zero theta"))

        self.view.notebook_3.stage_control_tab.focus_frame.up_btn.config(command=lambda: print("focus-"))
        self.view.notebook_3.stage_control_tab.focus_frame.down_btn.config(command=lambda: print("focus+"))
        self.view.notebook_3.stage_control_tab.focus_frame.zero_focus_btn.config(command=lambda: print("Zero Focus"))

        #self.view.notebook_3.goto_frame.goto_btn.config(command=lambda: self.model.stages.goto_position(self.view.notebook_3.goto_frame.goto_entry.get()))
        #x_y_frame.x_pos_spinval.trace_add('write', lambda *args: self.model.stages.update_x_position(self.verbose))
            #.stage_frame.stage_x_spinval.trace_add('write', lambda *args: update_stage_position(self, self.verbose))


    def launch_acquisition(self, popup_window):
        # Need to create the save path, and update the model from the entries.
        save_directory = create_save_path(self, popup_window, self.verbose)

        #TODO: Acquire data according to the operating mode.

        # Close the window
        popup_window.dismiss(self.verbose)



if __name__ == '__main__':
    # Testing section.

    print("done")
