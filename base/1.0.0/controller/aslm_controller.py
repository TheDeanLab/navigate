"""
This is the controller in an MVC-scheme for mediating the interaction between the View (GUI) and the model (./model/aslm_model.py).
Use: https://www.python-course.eu/tkinter_events_binds.php
"""
# Import Standard Python Packages
import numpy as np

# Local Imports
from view.main_application_window import Main_App as view
from controller.aslm_controller_functions import *

class ASLM_controller():
    def __init__(self, root, configuration_path, verbose):
        if verbose:
            print("Starting ASLM_controller")

        # Initialize the Model
        self.configuration_path = configuration_path
        self.model = start_model(self.configuration_path, verbose)

        # Initialize Camera
        self.camera_id = 0
        self.cam = start_camera(self.model, self.camera_id, verbose)

        # Initialize Stages
        self.stages = start_stages(self.model, verbose)
        self.stages.report_position()
        self.stages.create_internal_position_dict()

        # Initialize Filter Wheel
        self.filter_wheel = start_filter_wheel(self.model, verbose)

        # Initialize DAQ
        #self.daq = start_daq(self.model, verbose)

        # Initialize View
        self.view = view(root)

        #TODO: camera_view_tab, maximum intensity tab, waveform_tab
        # still need to be changed so that they are populated here.

        # Populate the View with the Model

        # Channels Tab, Channel Settings
        # Select only a single channel by default.
        self.view.notebook_1.channels_tab.channel_1_frame.on_off.set(True)
        self.view.notebook_1.channels_tab.channel_2_frame.on_off.set(False)
        self.view.notebook_1.channels_tab.channel_3_frame.on_off.set(False)
        self.view.notebook_1.channels_tab.channel_4_frame.on_off.set(False)
        self.view.notebook_1.channels_tab.channel_5_frame.on_off.set(False)

        # Populate the lasers in the GUI
        self.view.notebook_1.channels_tab.channel_1_frame.laser_pull_down['values'] = populate_lasers(self, verbose)
        self.view.notebook_1.channels_tab.channel_2_frame.laser_pull_down['values'] = populate_lasers(self)
        self.view.notebook_1.channels_tab.channel_3_frame.laser_pull_down['values'] = populate_lasers(self)
        self.view.notebook_1.channels_tab.channel_4_frame.laser_pull_down['values'] = populate_lasers(self)
        self.view.notebook_1.channels_tab.channel_5_frame.laser_pull_down['values'] = populate_lasers(self)

        # Populate the filters in the GUI
        self.view.notebook_1.channels_tab.channel_1_frame.filterwheel_pull_down['values'] = \
            list(self.model.FilterWheelParameters['available_filters'].keys())
        self.view.notebook_1.channels_tab.channel_2_frame.filterwheel_pull_down['values'] = \
            list(self.model.FilterWheelParameters['available_filters'].keys())
        self.view.notebook_1.channels_tab.channel_3_frame.filterwheel_pull_down['values'] = \
            list(self.model.FilterWheelParameters['available_filters'].keys())
        self.view.notebook_1.channels_tab.channel_4_frame.filterwheel_pull_down['values'] = \
            list(self.model.FilterWheelParameters['available_filters'].keys())
        self.view.notebook_1.channels_tab.channel_5_frame.filterwheel_pull_down['values'] = \
            list(self.model.FilterWheelParameters['available_filters'].keys())

        # Populate the exposure times in the GUI
        self.view.notebook_1.channels_tab.channel_1_frame.exp_time_spinval.set(self.model.CameraParameters['camera_exposure_time'])
        self.view.notebook_1.channels_tab.channel_2_frame.exp_time_spinval.set(self.model.CameraParameters['camera_exposure_time'])
        self.view.notebook_1.channels_tab.channel_3_frame.exp_time_spinval.set(self.model.CameraParameters['camera_exposure_time'])
        self.view.notebook_1.channels_tab.channel_4_frame.exp_time_spinval.set(self.model.CameraParameters['camera_exposure_time'])
        self.view.notebook_1.channels_tab.channel_5_frame.exp_time_spinval.set(self.model.CameraParameters['camera_exposure_time'])

        # Define all of the callbacks/events.
        # Acquire bar
        self.view.acqbar.acquire_btn.config(command=lambda: launch_popup_window(self, root, verbose))
        self.view.acqbar.exit_btn.config(command=lambda: exit_program(verbose))
        self.view.acqbar.pull_down.bind('<<ComboboxSelected>>', lambda *args: update_microscope_mode(self, verbose))

        # Channels Tab, Stack Acquisition Settings
        self.view.notebook_1.channels_tab.stack_acq_frame.start_pos_spinval.trace_add('write', lambda *args: update_z_steps(self, verbose))
        self.view.notebook_1.channels_tab.stack_acq_frame.step_size_spinval.trace_add('write', lambda *args: update_z_steps(self, verbose))
        self.view.notebook_1.channels_tab.stack_acq_frame.end_pos_spinval.trace_add('write', lambda *args: update_z_steps(self, verbose))

        # Channels Tab, Laser Cycling Settings
        self.view.notebook_1.channels_tab.stack_cycling_frame.cycling_options.trace_add('write', lambda *args: update_cycling_settings(self, verbose))

        # Channels Tab, Timepoint Settings
        self.view.notebook_1.channels_tab.stack_timepoint_frame.exp_time_spinval.trace_add('write', lambda *args: update_time_points(self, verbose))
        #TODO: Automatically calculate the stack acquisition time based on the number of timepoints, channels, and exposure time.

        # Channels Tab, Multi-position Acquisition Settings

        # Camera Tab, Camera Settings

        # Advanced Tab

        # Stage Notebook
        # Prepopulate the stage positions.
        self.view.notebook_3.stage_control_tab.position_frame.x_val.set(self.stages.x_pos)
        self.view.notebook_3.stage_control_tab.position_frame.y_val.set(self.stages.y_pos)
        self.view.notebook_3.stage_control_tab.position_frame.z_val.set(self.stages.z_pos)
        self.view.notebook_3.stage_control_tab.position_frame.theta_val.set(self.stages.theta_pos)
        self.view.notebook_3.stage_control_tab.position_frame.focus_val.set(self.stages.f_pos)

        # Prepopulate the stage step size.
        self.view.notebook_3.stage_control_tab.x_y_frame.increment_box.set(self.model.StageParameters['xy_step'])
        self.view.notebook_3.stage_control_tab.z_frame.increment_box.set(self.model.StageParameters['z_step'])
        self.view.notebook_3.stage_control_tab.theta_frame.increment_box.set(self.model.StageParameters['theta_step'])
        self.view.notebook_3.stage_control_tab.focus_frame.increment_box.set(self.model.StageParameters['f_step'])

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

        #self.view.notebook_3.goto_frame.goto_btn.config(command=lambda: self.stages.goto_position(self.view.notebook_3.goto_frame.goto_entry.get()))
        #x_y_frame.x_pos_spinval.trace_add('write', lambda *args: self.stages.update_x_position(verbose))
            #.stage_frame.stage_x_spinval.trace_add('write', lambda *args: update_stage_position(self, verbose))


    def launch_acquisition(self, popup_window, verbose=False):
        # Need to create the save path, and update the model from the entries.
        save_directory = create_save_path(self, popup_window, verbose)

        #TODO: Acquire data according to the operating mode.

        # Close the window
        popup_window.dismiss(verbose)



if __name__ == '__main__':
    # Testing section.

    print("done")
