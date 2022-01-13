"""
This is the controller in an MVC-scheme for mediating the interaction between the View (GUI) and the model (./model/aslm_model.py).
Use: https://www.python-course.eu/tkinter_events_binds.php
"""

# Local View Imports
from view.main_application_window import Main_App as view

# Local Sub-Controller Imports
from view.main_window_content.stage_control.stage_gui_controller import Stage_GUI_Controller
from view.main_window_content.acquire_bar_frame.acquire_bar_controller import Acquire_Bar_Controller
from view.main_window_content.tabs.channels.channel_setting_controller import Channel_Setting_Controller
from controller.aslm_controller_functions import *
from controller.aslm_configuration_controller import ASLM_Configuration_Controller

# Local Model Imports
from model.aslm_model import Model


class ASLM_controller():
    def __init__(self, root, configuration_path, experiment_path, etl_constants_path, args):
        self.verbose = args.verbose

        # Initialize the Model
        global model
        self.model = Model(args, configuration_path, experiment_path, etl_constants_path)

        # Initialize the View
        self.view = view(root)

        # sub gui controllers
        # Acquire bar
        self.acquire_bar_controller = Acquire_Bar_Controller(self.view.acqbar, self)

        # Channels Controller
        self.channel_setting_controller = Channel_Setting_Controller(self.view.notebook_1.channels_tab.channel_widgets_frame, self)

        # Stage Controller
        self.stage_gui_controller = Stage_GUI_Controller(self.view.notebook_3.stage_control_tab, self)

        # Initialize view based on model.configuration
        configuration_controller = ASLM_Configuration_Controller(self.model.configuration)

        # Channels Tab, Channel Settings
        self.initialize_channels(configuration_controller)

        # Stage Control Tab
        self.initialize_stage(configuration_controller)

        # Set view based on model.experiment
        # todo
        # Select only a single channel by default.
        # todo: other channel settings? like laser, filter.....
        self.channel_setting_controller.set_values(0, {
            'is_selected': True
        })

        #TODO: camera_view_tab, maximum intensity tab, waveform_tab
        # still need to be changed so that they are populated here.


        # Moved to the acquisition bar sub-controller...  Not functional yet.
        # self.view.acqbar.acquire_btn.config(command=lambda: launch_popup_window(self, root, self.verbose))
        # self.view.acqbar.exit_btn.config(command=lambda: exit_program(self.verbose))
        # self.view.acqbar.pull_down.bind('<<ComboboxSelected>>', lambda *args: update_microscope_mode(self, self.verbose))

        # Channels Tab, Stack Acquisition Settings
        #TODO: Move to a sub-controller.
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

        # Configure event control for the buttons
        #TODO: Move to a sub-controller.
        self.view.menu_zoom.bind("<<MenuSelect>>", lambda *args: print("Zoom Selected", *args))


    def launch_acquisition(self, popup_window):
        '''
        # Once the popup window has been filled out, we first create the save path using the create_save_path function.
        # This automatically removes spaces and replaces them with underscores.
        # Then it makes the directory.
        # Thereafter, the experiment is ready to go.
        '''
        # Need to create the save path, and update the model from the entries.
        save_directory = create_save_path(self, popup_window, self.verbose)

        #TODO: Acquire data according to the operating mode.

        # Close the window
        popup_window.dismiss(self.verbose)

    def initialize_channels(self, configuration_controller):
        # populate the lasers in the GUI
        self.channel_setting_controller.initialize('laser', configuration_controller.get_lasers_info())
        
        # populate the filters in the GUI
        self.channel_setting_controller.initialize('filter', configuration_controller.get_filters_info())

        # todo: camera_exposure_time is a configuration or experiment?
        self.channel_setting_controller.initialize('camera_exposure_time', configuration_controller.get_exposure_time())

    def initialize_stage(self, configuration_controller):
        # Prepopulate the stage positions.
        self.stage_gui_controller.set_position(configuration_controller.get_stage_position())

        # Prepopulate the stage step size.
        self.stage_gui_controller.set_step_size(configuration_controller.get_stage_step())

    def execute(self, command, *args):
        '''
        This function listens to sub_gui_controllers
        '''
        print('command passed from child', command, args)
        if command == 'stage':
            # todo: call the model to move stage
            print('stage should move to', args[0], 'on', args[1])



if __name__ == '__main__':
    # Testing section.

    print("done")
