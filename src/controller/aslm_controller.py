"""
This is the controller in an MVC-scheme for mediating the interaction between the View (GUI) and the model (./model/aslm_model.py).
Use: https://www.python-course.eu/tkinter_events_binds.php
"""

# Local View Imports
from view.main_application_window import Main_App as view

# Local Sub-Controller Imports
from view.main_window_content.stage_control.stage_gui_controller import Stage_GUI_Controller
from view.main_window_content.acquire_bar_frame.acquire_bar_controller import Acquire_Bar_Controller
from view.main_window_content.tabs.channels_tab_controller import Channels_Tab_Controller
from controller.aslm_controller_functions import *
from controller.aslm_configuration_controller import ASLM_Configuration_Controller
from controller.thread_pool import SynchronizedThreadPool

# Local Model Imports
from model.aslm_model import Model


class ASLM_controller():
    def __init__(self, root, configuration_path, experiment_path, etl_constants_path, args):
        self.verbose = args.verbose

        # Creat a thread pool
        self.threads_pool = SynchronizedThreadPool()
        # register resource
        self.threads_pool.registerResource('stage')

        # Initialize the Model
        global model
        self.model = Model(args, configuration_path, experiment_path, etl_constants_path)

        # Initialize the View
        self.view = view(root)

        # sub gui controllers
        # Acquire bar
        self.acquire_bar_controller = Acquire_Bar_Controller(self.view.acqbar, self)

        # Channels Controller
        self.channels_tab_controller = Channels_Tab_Controller(self.view.notebook_1.channels_tab, self)

        # Stage Controller
        self.stage_gui_controller = Stage_GUI_Controller(self.view.notebook_3.stage_control_tab, self)

        # Initialize view based on model.configuration
        configuration_controller = ASLM_Configuration_Controller(self.model.configuration)

        # Channels Tab
        self.initialize_channels(configuration_controller)

        # Stage Control Tab
        self.initialize_stage(configuration_controller)

        # Set view based on model.experiment
        # todo
        # Select only a single channel by default.
        # todo: other channel settings? like laser, filter.....
        self.channels_tab_controller.set_values('channels', {
            'channel_1': {
                'is_selected': True
            }
        })

        #TODO: camera_view_tab, maximum intensity tab, waveform_tab
        # still need to be changed so that they are populated here.


        # Moved to the acquisition bar sub-controller...  Not functional yet.
        # self.view.acqbar.acquire_btn.config(command=lambda: launch_popup_window(self, root, self.verbose))
        # self.view.acqbar.exit_btn.config(command=lambda: exit_program(self.verbose))
        # self.view.acqbar.pull_down.bind('<<ComboboxSelected>>', lambda *args: update_microscope_mode(self, self.verbose))

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
        # populate channels in the GUI
        channels_setting = configuration_controller.get_channels_info(self.verbose)
        self.channels_tab_controller.initialize('channels', channels_setting)
        
        # populate stack acquisition
        # todo: should those settings from configuration/experiments?
        stack_acq_setting = {
            'step_size': 0.160,
            'start_pos': 0,
            'end_pos': 200,
            # 'slice': 1250
        }
        self.channels_tab_controller.initialize('stack_acquisition', stack_acq_setting)

        # populate laser cycling settings
        laser_cycling_values = ['Per Z', 'Per Stack']
        self.channels_tab_controller.initialize('laser_cycling', laser_cycling_values)

        # populate timepoint settings
        # todo: should those settings from configuration/experiments?
        timepoint_setting = {
            'is_save': False,
            'timepoint': 1,
            'stack_acq_time': 200,
            'stack_pause': 0
        }
        self.channels_tab_controller.initialize('timepoint', timepoint_setting)
        

    def initialize_stage(self, configuration_controller):
        # Prepopulate the stage positions.
        self.stage_gui_controller.set_position(configuration_controller.get_stage_position())

        # Prepopulate the stage step size.
        self.stage_gui_controller.set_step_size(configuration_controller.get_stage_step())

        # Set stage movement limits
        position_min = configuration_controller.get_stage_position_limits('_min')
        position_max = configuration_controller.get_stage_position_limits('_max')
        self.stage_gui_controller.set_position_limits(position_min, position_max)

    def execute(self, command, *args):
        '''
        This function listens to sub_gui_controllers
        '''
        print('command passed from child', command, args)
        if command == 'stage':
            # call the model to move stage
            abs_postion = {
                "{}_abs".format(args[1]) : args[0]
            }
            self.threads_pool.createThread('stage', self.model.stages.move_absolute, (abs_postion,))
            # self.model.stages.move_absolute(abs_postion)



if __name__ == '__main__':
    # Testing section.

    print("done")
