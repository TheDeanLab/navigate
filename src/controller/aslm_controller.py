"""
This is the controller in an MVC-scheme for mediating the interaction between the View (GUI) and the model (./model/aslm_model.py).
Use: https://www.python-course.eu/tkinter_events_binds.php
"""

# Local View Imports
from tabnanny import verbose
from view.main_application_window import Main_App as view

# Local Sub-Controller Imports
from controller.sub_controllers.stage_gui_controller import Stage_GUI_Controller
from controller.sub_controllers.acquire_bar_controller import Acquire_Bar_Controller
from controller.sub_controllers.channels_tab_controller import Channels_Tab_Controller
from controller.sub_controllers.camera_view_controller import Camera_View_Controller
from controller.aslm_configuration_controller import ASLM_Configuration_Controller
from controller.aslm_controller_functions import *
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
        self.acquire_bar_controller = Acquire_Bar_Controller(self.view.acqbar, self, self.verbose)

        # Channels Controller
        self.channels_tab_controller = Channels_Tab_Controller(self.view.notebook_1.channels_tab, self, self.verbose)

        # Camera View Controller
        self.camera_view_controller = Camera_View_Controller(self.view.notebook_2.camera_tab, self, self.verbose)

        # Stage Controller
        self.stage_gui_controller = Stage_GUI_Controller(self.view.notebook_3.stage_control_tab, self, self.verbose)

        # Initialize view based on model.configuration
        configuration_controller = ASLM_Configuration_Controller(self.model.configuration)

        # Channels Tab
        self.initialize_channels(configuration_controller)

        # Stage Control Tab
        self.initialize_stage(configuration_controller)

        # Set view based on model.experiment
        # TODO
        # Select only a single channel by default.
        # TODO: other channel settings? like laser, filter.....
        self.channels_tab_controller.set_values('channels', {
            'channel_1': {
                'is_selected': True
            }
        })

        # set mode according to model.experiment
        mode = self.model.experiment.MicroscopeState['image_mode']
        self.acquire_bar_controller.set_mode(mode)
        self.channels_tab_controller.set_mode(mode)

        # set saving settings to acquire bar
        for name in self.model.experiment.Saving:
            if self.model.experiment.Saving[name] is None:
                self.model.experiment.Saving[name] = ''
        self.acquire_bar_controller.set_saving_settings(self.model.experiment.Saving)

        #TODO: camera_view_tab, maximum intensity tab, waveform_tab

        # Camera Tab, Camera Settings

        # Advanced Tab

        # Configure event control for the buttons
        #TODO: Move to a sub-controller.
        self.view.menu_zoom.bind("<<MenuSelect>>", lambda *args: print("Zoom Selected", *args))

    def initialize_channels(self, configuration_controller):
        # set some other information needed by channels_tab_controller
        self.channels_tab_controller.settings_from_configuration = {
            'stage_velocity': self.model.configuration.StageParameters['velocity'],
            'filter_wheel_delay': self.model.configuration.FilterWheelParameters['filter_wheel_delay']
        }
        # populate channels in the GUI
        channels_setting = configuration_controller.get_channels_info(self.verbose)
        self.channels_tab_controller.initialize('channels', channels_setting)
        
        # populate stack acquisition
        # TODO: should those settings from configuration/experiments?
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
        # TODO: should those settings from configuration/experiments?
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
        if command == 'stage':
            # call the model to move stage
            abs_postion = {
                "{}_abs".format(args[1]) : args[0]
            }
            self.threads_pool.createThread('stage', self.model.stages.move_absolute, (abs_postion,))
            # self.model.stages.move_absolute(abs_postion)
        elif command == 'image_mode':
            # tell channel the mode is changed
            self.channels_tab_controller.set_mode('instant' if args[0] == 'continuous' else 'uninstant')
            # update model.experiment
            self.model.experiment.MicroscopeState['image_mode'] = args[0]
            # set camera view mode to change
            self.camera_view_controller.set_mode(args[0])
        elif command == 'set_save':
            self.acquire_bar_controller.set_save_option(args[0])
        elif command == 'acquisite_and_save':
            # TODO
<<<<<<< Updated upstream
            file_name = create_save_path(self.model.experiment.Saving, self.verbose)
            pass
        elif command == 'acquisite':
            # TODO
=======
            #This can be changed but this is just an if to catch all active functionality when in continuous mode and the acquire button is pressed
            if self.mode == 'continuous':
                #Create a thread for the camera to use to display live feed
                self.threads_pool.createThread('camera', self.camera_view_controller.live_feed)
        elif command == 'stop_acquire':
            # TODO: stop continuous acquire from camera
            if self.mode == 'continuous':
                # Do I need to lock the thread here or how do I stop the process with the thread pool? Or is it something with the ObjectSubProcess? Or both depending on if synthetic or real
                pass
>>>>>>> Stashed changes
            pass

        if self.verbose:
            print('In central controller: command passed from child', command, args)



if __name__ == '__main__':
    # Testing section.

    print("done")
