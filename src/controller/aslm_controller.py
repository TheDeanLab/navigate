"""
This is the controller in an MVC-scheme for mediating the interaction between the View (GUI) and the model
(./model/aslm_model.py). Use: https://www.python-course.eu/tkinter_events_binds.php
"""
#  Standard Library Imports
from pathlib import Path
import tkinter

#  External Library Imports
import numpy as np

# Local View Imports
from tabnanny import verbose
from tkinter import filedialog
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


class ASLM_controller:
    def __init__(self, root, configuration_path, experiment_path, etl_constants_path, args):
        self.verbose = args.verbose
        self.stop_acquisition = True

        # Creat a thread pool
        self.threads_pool = SynchronizedThreadPool()

        # register resource
        self.threads_pool.registerResource('stage')

        # Initialize the Model
        global model
        self.model = Model(args, configuration_path, experiment_path, etl_constants_path)

        # save default experiment file
        self.default_experiment_file = experiment_path

        # Initialize the View
        self.view = view(root)

        # Sub Gui Controllers
        # Acquire bar
        self.acquire_bar_controller = Acquire_Bar_Controller(self.view.acqbar, self, self.verbose)

        # Channels Controller
        self.channels_tab_controller = Channels_Tab_Controller(self.view.notebook_1.channels_tab, self, self.verbose)

        # Camera View Controller
        self.camera_view_controller = Camera_View_Controller(self.view.notebook_2.camera_tab, self.model.camera, self,
                                                             self.verbose)
        self.camera_view_controller.populate_view()

        # Stage Controller
        self.stage_gui_controller = Stage_GUI_Controller(self.view.notebook_3.stage_control_tab, self, self.verbose)

        # initialize menu bar
        self.initialize_menus()
        
        # Initialize view based on model.configuration
        configuration_controller = ASLM_Configuration_Controller(self.model.configuration)

        # Channels Tab
        self.initialize_channels(configuration_controller)

        # Stage Control Tab
        self.initialize_stage(configuration_controller)

        # Set view based on model.experiment
        self.populate_experiment_setting()

        #  TODO: camera_view_tab, maximum intensity tab, waveform_tab

        # Camera Tab, Camera Settings

        # Advanced Tab

    def initialize_channels(self, configuration_controller):
        """
        # set some other information needed by channels_tab_controller
        """
        self.channels_tab_controller.settings_from_configuration = {
            'stage_velocity': self.model.configuration.StageParameters['velocity'],
            'filter_wheel_delay': self.model.configuration.FilterWheelParameters['filter_wheel_delay']
        }
        # populate channels in the GUI
        channels_setting = configuration_controller.get_channels_info(self.verbose)
        self.channels_tab_controller.initialize('channel', channels_setting)

        # populate laser cycling settings
        laser_cycling_values = ['Per Z', 'Per Stack']
        self.channels_tab_controller.initialize('laser_cycling', laser_cycling_values)

    def initialize_stage(self, configuration_controller):
        """
        # Pre-populate the stage positions.
        """
        # Set stage movement limits
        position_min = configuration_controller.get_stage_position_limits('_min')
        position_max = configuration_controller.get_stage_position_limits('_max')
        self.stage_gui_controller.set_position_limits(position_min, position_max)

    def initialize_menus(self):
        """
        # this function defines all the menus in the menubar
        """
        def new_experiment():
            self.populate_experiment_setting(self.default_experiment_file)

        def load_experiment():
            filename = filedialog.askopenfilenames(defaultextension='.yml', filetypes=[('Yaml files', '*.yml')])
            if not filename:
                return
            self.populate_experiment_setting(filename[0])

        def save_experiment():
            # update model.experiment and save it to file
            if not self.update_experiment_setting():
                return
            filename = filedialog.asksaveasfilename(defaultextension='.yml', filetypes=[('Yaml file', '*.yml')])
            if not filename:
                return
            save_experiment_file('', self.model.experiment.serialize(), filename)

        menus_dict = {
            self.view.menubar.menu_file: {
                'New Experiment': new_experiment,
                'Load Experiment': load_experiment,
                'Save Experiment': save_experiment
            },
            self.view.menubar.menu_multi_positions: {
                'Load Positions': self.channels_tab_controller.load_positions,
                'Export Positions': self.channels_tab_controller.export_positions,
                'Append Current Position': self.channels_tab_controller.append_current_position,
                'Generate Positions': self.channels_tab_controller.generate_positions,
                'Move to Selected Position': self.channels_tab_controller.move_to_position,
                # 'Sort Positions': ,
            },
            self.view.menubar.menu_zoom: {
                '1x': lambda: self.execute('zoom', 1),
                '2x': lambda: self.execute('zoom', 2),
                '3x': lambda: self.execute('zoom', 3),
                '4x': lambda: self.execute('zoom', 4),
                '5x': lambda: self.execute('zoom', 5),
                '6x': lambda: self.execute('zoom', 6)
            },
            self.view.menubar.menu_resolution: {
                'Mesoscale Mode': lambda: self.execute('resolution', 'low-res'),
                'Nanoscale Mode': lambda: self.execute('resolution', 'high-res')
            }
        }
        for menu in menus_dict:
            menuitems = menus_dict[menu]
            for label in menuitems:
                menu.add_command(label=label, command=menuitems[label])

    def populate_experiment_setting(self, file_name=None):
        """
        # if file_name is specified and exists, this function will load an experiment file to model.experiment
        # populate model.experiment to view
        """
        # model will load the spcified experiment file
        if file_name:
            file_path = Path(file_name)
            if file_path.exists():
                self.model.load_experiment_file(file_path)

        # populate stack acquisition from model.experiment
        stack_acq_setting = {
            'step_size': self.model.experiment.MicroscopeState['step_size'],
            'start_position': self.model.experiment.MicroscopeState['start_position'],
            'end_position': self.model.experiment.MicroscopeState['end_position'],
            # 'number_z_steps': 1250
        }
        self.channels_tab_controller.set_values('stack_acquisition', stack_acq_setting)

        # populate laser cycling mode
        laser_cycling = 'Per Z' if self.model.experiment.MicroscopeState[
                                       'stack_cycling_mode'] == 'per_z' else 'Per Stack'
        self.channels_tab_controller.set_values('laser_cycling', laser_cycling)

        # populate timepoints settings
        timepoints_setting = {
            'is_save': self.model.experiment.MicroscopeState['is_save'],
            'timepoints': self.model.experiment.MicroscopeState['timepoints'],
            'stack_pause': self.model.experiment.MicroscopeState['stack_pause']
        }
        self.channels_tab_controller.set_values('timepoint', timepoints_setting)

        # populate channels
        self.channels_tab_controller.set_values('channel', self.model.experiment.MicroscopeState['channels'])

        # set mode according to model.experiment
        mode = self.model.experiment.MicroscopeState['image_mode']
        self.acquire_bar_controller.set_mode(mode)

        # set saving settings to acquire bar
        for name in self.model.experiment.Saving:
            if self.model.experiment.Saving[name] is None:
                self.model.experiment.Saving[name] = ''
        self.acquire_bar_controller.set_saving_settings(self.model.experiment.Saving)

        # populate StageParameters
        position = {}
        for axis in ['x', 'y', 'z', 'theta', 'f']:
            position[axis] = self.model.experiment.StageParameters[axis]
        self.stage_gui_controller.set_position(position)

        # Pre-populate the stage step size.
        step_size = {}
        for axis in ['xy', 'z', 'theta', 'f']:
            step_size[axis] = self.model.experiment.StageParameters[axis+'_step']
        self.stage_gui_controller.set_step_size(step_size)

        # populate multi_positions
        self.channels_tab_controller.set_positions(self.model.experiment.MicroscopeState['stage_positions'])

    def update_experiment_setting(self):
        """
        # This function will update model.experiment according values in the View(GUI)
        """
        # update image mode from acquire bar
        self.model.experiment.MicroscopeState['image_mode'] = self.acquire_bar_controller.get_mode()

        # get settings from channels tab
        settings = self.channels_tab_controller.get_values()
        # if there is something wrong, it will popup a window and return false
        for k in settings:
            if not settings[k]:
                #TODO: popup error window
                tkinter.messagebox.showerror(title='Warning', message='There is some missing/wrong settings!')
                return False
        self.model.experiment.MicroscopeState['stack_cycling_mode'] = settings['stack_cycling_mode']
        for k in settings['stack_acquisition']:
            self.model.experiment.MicroscopeState[k] = settings['stack_acquisition'][k]
        for k in settings['timepoint']:
            self.model.experiment.MicroscopeState[k] = settings['timepoint'][k]
        # channels
        self.model.experiment.MicroscopeState['channels'] = settings['channel']
        # get all positions
        self.model.experiment.MicroscopeState['stage_positions'] = self.channels_tab_controller.get_positions()

        # get position information from stage tab
        position = self.stage_gui_controller.get_position()
        for axis in position:
            self.model.experiment.StageParameters[axis] = position[axis]
        step_size = self.stage_gui_controller.get_step_size()
        for axis in step_size:
            self.model.experiment.StageParameters[axis+'_step'] = step_size[axis]
        
        return True

    def prepare_acquire_data(self):
        """
        # this function do preparations before acquiring data
        # first, update model.experiment
        # second, set sub-controllers' mode to 'live' when 'continuous' was selected, or 'stop'
        """
        if not self.update_experiment_setting():
            return False

        if self.model.experiment.MicroscopeState['image_mode'] == 'continuous':
            self.channels_tab_controller.set_mode('live')
            self.camera_view_controller.set_mode('live')
        else:
            self.channels_tab_controller.set_mode('stop')
            self.camera_view_controller.set_mode('stop')
        return True

    def update_camera_view(self):
        """
        # Function aims to update the real-time parameters in the camera view, including the
        # channel number, the max counts, the image, etc.
        """
        create_threads = False
        if create_threads:
            self.threads_pool.createThread('camera_display',
                                           self.camera_view_controller.display_image(self.model.data))
            self.threads_pool.createThread('update_GUI',
                                           self.camera_view_controller.update_channel_idx(self.model.current_channel))
        else:
            self.camera_view_controller.display_image(self.model.data)
            self.camera_view_controller.update_channel_idx(self.model.current_channel)

    def execute(self, command, *args):
        """
        # This function listens to sub_gui_controllers
        """
        if command == 'stage':
            """
            # call the model to move stage
            """
            axis_dict = {
                'x': 'X',
                'y': 'Y',
                'z': 'Z',
                'theta': 'R',
                'f': 'F'
            }
            abs_postion = {
                axis_dict[args[1]]: args[0]
            }
            self.threads_pool.createThread('stage', self.model.stages.move_absolute, (abs_postion,))

        elif command == 'move_stage_and_update_info':
            """
            # update stage view to show the position
            """
            self.stage_gui_controller.set_position(args[0])

        elif command == 'get_stage_position':
            """
            #  Returns the current stage position
            """
            return self.stage_gui_controller.get_position()

        elif command == 'zoom':
            """
            #  Changes the zoom position
            """
            self.model.zoom.set_zoom(args[0])
            if self.verbose:
                print("Zoom set to:", args[0])

        elif command == 'resolution':
            """
            # Upon switching modes, we will need to:
            #   - Initialize the second camera.
            #   - Change the focus axis.
            #   - Use a different remote focusing waveform.
            #   - Open a different shutter.
            """
            if self.verbose:
                print("Changing the Resolution Mode to:", args[0])

        elif command == 'set_save':
            self.acquire_bar_controller.set_save_option(args[0])

        elif command == 'stack_acquisition':
            settings = args[0]
            for k in settings:
                self.model.experiment.MicroscopeState[k] = settings[k]
            print('in continuous mode:the stack acquisition setting is changed')
            print('you could get the new setting from model.experiment')
            print('you could also get the changes from args')
            print(self.model.experiment.MicroscopeState)
            pass

        elif command == 'laser_cycling':
            self.model.experiment.MicroscopeState['stack_cycling_mode'] = args[0]
            print('in continuous mode:the laser cycling setting is changed')
            print('you could get the new setting from model.experiment')
            print('you could also get the changes from args')
            print(self.model.experiment.MicroscopeState['stack_cycling_mode'])
            pass

        elif command == 'channel':
            self.model.experiment.MicroscopeState['channels'] = self.channels_tab_controller.get_values('channel')
            print('in continuous mode:the channel setting is changed')
            print('you could get the new setting from model.experiment')
            print('you could also get the changes from args')
            print(self.model.experiment.MicroscopeState['channels'])
            pass

        elif command == 'timepoint':
            settings = args[0]
            for k in settings:
                self.model.experiment.MicroscopeState[k] = settings[k]
            print('timepoint is changed', args[0])

        elif command == 'acquire_and_save':
            if not self.prepare_acquire_data():
                self.acquire_bar_controller.stop_acquire()
                return
            # create file directory
            file_directory = create_save_path(args[0], self.verbose)
            # save experiment file
            save_experiment_file(file_directory, self.model.experiment.serialize())
            pass

        elif command == 'acquire':
            if not self.prepare_acquire_data():
                self.acquire_bar_controller.stop_acquire()
                return
            # Acquisition modes can be: 'continuous', 'z-stack', 'single', 'projection'
            if self.acquire_bar_controller.mode == 'single':
                """
                #  Acquires a single image at the current position for each chnanel configuration
                """
                if self.verbose:
                    print("Starting Single Acquisition")
                self.model.open_shutter()
                self.model.run_single_acquisition(self.update_camera_view)
                self.model.close_shutter()
                self.execute('stop_acquire')

            elif self.acquire_bar_controller.mode == 'continuous':
                if self.verbose:
                    print('Starting Continuous Acquisition')
                self.model.open_shutter()
                self.threads_pool.createThread(self.model.run_live_acquisition(self.update_camera_view))
                self.model.close_shutter()

            elif self.acquire_bar_controller.mode == 'z-stack':
                if self.verbose:
                    print("Starting Z-Stack Acquisition")
                is_multi_position = self.channels_tab_controller.is_multiposition_val.get()
                self.model.open_shutter()
                self.model.run_z_stack_acquisition(is_multi_position, self.update_camera_view())
                self.model.close_shutter()

            elif self.acquire_bar_controller.mode == 'projection':
                pass

            else:
                print("Wrong acquisition mode.  Not recognized.")
                pass

        elif command == 'stop_acquire':
            # stop continuous acquire from camera

            self.model.stop_acquisition = True
            self.camera_view_controller.set_mode('stop')  # Breaks live feed loop

            # TODO: stop continuous acquire from camera
            # Do I need to lock the thread here or how do I stop the process with the thread pool?
            # Or is it something with the ObjectSubProcess? Or both depending on if synthetic or real
            #  self.threads_pool.createThread('camera', self.model.acquire_with_waveform_update())

            # self.threads_pool.createThread('camera_display',
            #                                self.camera_view_controller.display_image(self.model.camera.image))
            #  self.threads_pool.createThread('camera', self.camera_view_controller.live_feed)

        if self.verbose:
            print('In central controller: command passed from child', command, args)


if __name__ == '__main__':
    # Testing section.

    print("done")
