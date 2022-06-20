"""
Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

#  Standard Library Imports
import tkinter
import multiprocessing as mp
import time
import threading

# Third Party Imports

# Local View Imports
from tkinter import filedialog
from view.main_application_window import Main_App as view
from view.remote_focus_popup import remote_popup
from view.autofocus_setting_popup import autofocus_popup

# Local Sub-Controller Imports
from controller.sub_controllers.stage_gui_controller import Stage_GUI_Controller
from controller.sub_controllers.acquire_bar_controller import Acquire_Bar_Controller
from controller.sub_controllers.channels_tab_controller import Channels_Tab_Controller
from controller.sub_controllers.camera_view_controller import Camera_View_Controller
from controller.sub_controllers.camera_setting_controller import Camera_Setting_Controller
from controller.aslm_configuration_controller import ASLM_Configuration_Controller
from controller.sub_controllers.waveform_tab_controller import Waveform_Tab_Controller
from controller.sub_controllers.etl_popup_controller import Etl_Popup_Controller
from controller.sub_controllers.autofocus_popup_controller import Autofocus_Popup_Controller
from controller.aslm_controller_functions import *
from controller.thread_pool import SynchronizedThreadPool

# Local Model Imports
from model.aslm_model import Model
from model.aslm_model_config import Session as session
from model.concurrency.concurrency_tools import ObjectInSubprocess, SharedNDArray

# debug
from controller.aslm_debug import Debug_Module

import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)

class ASLM_controller:
    """ ASLM Controller

    Parameters
    ----------
    root : Tk top-level widget.
        Tk.tk GUI instance.
    configuration_path : string
        Path to the configuration yaml file. Provides global microscope configuration parameters.
    experiment_path : string
        Path to the experiment yaml file. Provides experiment-specific microscope configuration.
    etl_constants_path : string
        Path to the etl constants yaml file. Provides magnification and wavelength-specific parameters.
    USE_GPU : Boolean
        Flag for utilizing CUDA functionality.
    *args :
        Command line input arguments for non-default file paths or using synthetic hardware modes.
    """

    def __init__(
            self,
            root,
            configuration_path,
            experiment_path,
            etl_constants_path,
            USE_GPU,
            args):
        
        logger.info("Spec - Controller controlling")
        logger.info("Performance - Controller performing")

        # Verbosity and debugging menu
        self.verbose = args.verbose
        self.debug = args.debug

        # Create a thread pool
        self.threads_pool = SynchronizedThreadPool()

        self.event_queue = mp.Queue()  # pass events from the model to the view via controller
                                       # accepts tuples, ('event_name', value)

        # Initialize the Model
        self.model = ObjectInSubprocess(Model,
                                        USE_GPU,
                                        args,
                                        configuration_path=configuration_path,
                                        experiment_path=experiment_path,
                                        etl_constants_path=etl_constants_path,
                                        event_queue=self.event_queue)
        logger.debug(f"Spec - Configuration Path: {configuration_path}")
        logger.debug(f"Spec - Experiment Path: {experiment_path}")
        logger.debug(f"Spec - ETL Constants Path: {etl_constants_path}")

        # save default experiment file
        self.default_experiment_file = experiment_path

        # Load the Configuration to Populate the GUI
        self.configuration = session(configuration_path, self.verbose)

        # Initialize view based on model.configuration
        configuration_controller = ASLM_Configuration_Controller(self.configuration)

        # etl setting file
        self.etl_constants_path = etl_constants_path
        self.etl_setting = session(self.etl_constants_path, self.verbose)

        # Initialize the View
        self.view = view(root)

        # Sub Gui Controllers
        # Acquire bar
        self.acquire_bar_controller = Acquire_Bar_Controller(self.view.acqbar,
                                                             self,
                                                             self.verbose)

        # Channels Controller
        self.channels_tab_controller = Channels_Tab_Controller(self.view.settings.channels_tab,
                                                               self,
                                                               self.verbose,
                                                               configuration_controller)

        # Camera View Controller
        self.camera_view_controller = Camera_View_Controller(self.view.camera_waveform.camera_tab,
                                                             self,
                                                             self.verbose)
        self.camera_view_controller.populate_view()

        # Camera Settings Controller
        self.camera_setting_controller = Camera_Setting_Controller(self.view.settings.camera_settings_tab,
                                                                   self,
                                                                   self.verbose,
                                                                   configuration_controller)

        # Stage Controller
        self.stage_gui_controller = Stage_GUI_Controller(self.view.stage_control.stage_control_tab,
                                                         self,
                                                         self.verbose,
                                                         configuration_controller)

        # Waveform Controller
        self.waveform_tab_controller = Waveform_Tab_Controller(self.view.camera_waveform.waveform_tab,
                                                               self,
                                                               self.verbose)
        t = threading.Thread(target=self.update_event)
        t.start()

        # initialize menu bar
        self.initialize_menus()

        # Set view based on model.experiment
        self.experiment = session(experiment_path, args.verbose)
        self.populate_experiment_setting()

        # Camera Settings Tab
        # self.initialize_cam_settings(configuration_controller)

        # Camera View Tab
        self.initialize_cam_view(configuration_controller)

        #  TODO: camera_view_tab, maximum intensity tab, waveform_tab

        # Camera Tab, Camera Settings

        # Advanced Tab

        # Wire up show image pipe
        self.show_img_pipe_parent, self.show_img_pipe_child = mp.Pipe()
        self.model.set_show_img_pipe(self.show_img_pipe_child)

        # Setting up Pipe for Autofocus Plot
        self.plot_pipe_controller, self.plot_pipe_model = mp.Pipe(duplex=True)
        self.model.set_autofocus_plot_pipe(self.plot_pipe_model)

        # Create default data buffer
        self.img_width = 0
        self.img_height = 0
        self.update_buffer()

    def update_buffer(self):
        """ Update the buffer size according to the camera dimensions listed in the experimental parameters.

        Returns
        -------
        self.img_width : int
            Number of x_pixels from microscope configuration file.
        self.image_height : int
            Number of y_pixels from microscope configuration file.
        self.data_buffer : SharedNDArray
            Pre-allocated shared memory array. Size dictated by x_pixels, y_pixels, an number_of_frames in
            configuration file.
        """
        img_width = int(self.experiment.CameraParameters['x_pixels'])
        img_height = int(self.experiment.CameraParameters['y_pixels'])
        if img_width == self.img_width and img_height == self.img_height:
            return

        self.data_buffer = [SharedNDArray(shape=(img_height, img_width),
                                          dtype='uint16') for i in range(self.configuration.SharedNDArray['number_of_frames'])]
        self.model.set_data_buffer(self.data_buffer, img_width, img_height)
        self.img_width = img_width
        self.img_height = img_height

    def initialize_cam_view(self, configuration_controller):
        """ Populate view tab.
        Populate widgets with necessary data from config file via config controller. For the entire view tab.

        Parameters
        -------
        configuration_controller : class
            Camera view sub-controller.
        """
        # Populating Min and Max Counts
        minmax_values = [110, 5000]
        self.camera_view_controller.initialize('minmax', minmax_values)
        image_metrics = [1, 0, 0]
        self.camera_view_controller.initialize('image', image_metrics)

    def initialize_menus(self):
        """ Initialize menus
        This function defines all the menus in the menubar

        Returns
        -------
        configuration_controller : class
            Camera view sub-controller.

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
                tkinter.messagebox.showerror(title='Warning',
                                             message='Incorrect/missing settings. Cannot save current experiment file.')
                return
            filename = filedialog.asksaveasfilename(defaultextension='.yml',
                                                    filetypes=[('Yaml file', '*.yml')])
            if not filename:
                return
            save_yaml_file('', self.experiment.serialize(), filename)

        def popup_etl_setting():
            if hasattr(self, 'etl_controller'):
                self.etl_controller.showup()
                return
            etl_setting_popup = remote_popup(self.view)  # TODO: can we rename remote_popup to etl_popup?
            self.etl_controller = Etl_Popup_Controller(etl_setting_popup,
                                                       self,
                                                       self.verbose,
                                                       self.etl_setting,
                                                       self.etl_constants_path,
                                                       self.experiment.GalvoParameters)
            self.etl_controller.set_experiment_values(self.resolution_value.get())
            self.etl_controller.set_mode(self.acquire_bar_controller.mode)

        def popup_autofocus_setting():
            if hasattr(self, 'af_popup_controller'):
                self.af_popup_controller.showup()
                return
            af_popup = autofocus_popup(self.view)
            self.af_popup_controller = Autofocus_Popup_Controller(af_popup,
                                                                  self,
                                                                  self.verbose,
                                                                  self.experiment.AutoFocusParameters)

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
            }
        }
        for menu in menus_dict:
            menu_items = menus_dict[menu]
            for label in menu_items:
                menu.add_command(label=label, command=menu_items[label])

        # add resolution menu
        self.resolution_value = tkinter.StringVar()
        self.view.menubar.menu_resolution.add_radiobutton(label='Nanoscale',
                                                          variable=self.resolution_value,
                                                          value='high')

        # low resolution sub menu
        # Should only be one checkbox selected, depending on what mode we are initialized in.
        # In order to make sure only one checkbox would be selected, they need
        # to share one variable: resolution_value
        meso_res_sub_menu = tkinter.Menu(self.view.menubar.menu_resolution)
        self.view.menubar.menu_resolution.add_cascade(menu=meso_res_sub_menu,label='Mesoscale')

        for res in self.etl_setting.ETLConstants['low'].keys():
            meso_res_sub_menu.add_radiobutton(label=res,
                                              variable=self.resolution_value,
                                              value=res)
        # event binding
        self.resolution_value.trace_add('write', lambda *args: self.execute('resolution', self.resolution_value.get()))

        # add separator
        self.view.menubar.menu_resolution.add_separator()

        # etl popup
        self.view.menubar.menu_resolution.add_command(label='ETL Parameters', command=popup_etl_setting)

        # autofocus menu
        self.view.menubar.menu_autofocus.add_command(label='Autofocus', command=lambda: self.execute('autofocus'))
        self.view.menubar.menu_autofocus.add_command(label='setting', command=popup_autofocus_setting)

        # debug menu
        if self.debug:
            Debug_Module(self, self.view.menubar.menu_debug, self.verbose)

    def populate_experiment_setting(self, file_name=None):
        """
        # if file_name is specified and exists, this function will load an experiment file to model.experiment
        # populate model.experiment to view
        """
        # model will load the specified experiment file
        if file_name:
            file_path = Path(file_name)
            if file_path.exists():
                # Loads experiment file within the model, then the controller.
                self.model.load_experiment_file(file_path)

                # Create experiment instance here.
                self.experiment = session(file_path, self.verbose)

        # set mode according to model.experiment
        mode = self.experiment.MicroscopeState['image_mode']
        self.acquire_bar_controller.set_mode(mode)
        self.acquire_bar_controller.set_saving_settings(self.experiment.Saving)

        # populate StageParameters
        self.stage_gui_controller.set_experiment_values(
            self.experiment.StageParameters)

        # channels tab
        self.channels_tab_controller.set_experiment_values(self.experiment.MicroscopeState)

        # camera setting tab
        self.camera_setting_controller.set_experiment_values(self.experiment)

        # resolution/zoom menu
        resolution_mode = self.experiment.MicroscopeState['resolution_mode']
        if resolution_mode == 'high':
            self.resolution_value.set('high')
        else:
            self.resolution_value.set(self.experiment.MicroscopeState['zoom'])

    def update_experiment_setting(self):
        """
        # This function will update model.experiment according values in the View(GUI)
        """
        # acquire_bar_controller - update image mode
        self.experiment.MicroscopeState['image_mode'] = self.acquire_bar_controller.get_mode()
        # camera_view_controller
        # channel_setting_controller
        # etl_popup_controller
        # gui_controller
        # waveform_tab_controller
        # widget_functions
        # get zoom and resolution info from resolution menu
        if self.resolution_value.get() == 'high':
            self.experiment.MicroscopeState['resolution_mode'] = 'high'
            self.experiment.MicroscopeState['zoom'] = 'N/A'
        else:
            self.experiment.MicroscopeState['resolution_mode'] = 'low'
            self.experiment.MicroscopeState['zoom'] = self.resolution_value.get()

        # collect settings from sub-controllers
        # sub-controllers will validate the value, if something wrong, it will
        # return False

        return self.channels_tab_controller.update_experiment_values(self.experiment.MicroscopeState) and \
               self.stage_gui_controller.update_experiment_values(self.experiment.StageParameters) and \
               self.camera_setting_controller.update_experiment_values(self.experiment.CameraParameters)

    def prepare_acquire_data(self):
        """
        # this function does preparations before acquiring data
        # first, update model.experiment
        # second, set sub-controllers' mode to 'live' when 'continuous' was selected, or 'stop'
        """
        if not self.update_experiment_setting():
            tkinter.messagebox.showerror(
                title='Warning',
                message='There are some missing/wrong settings! Cannot start acquisition!')
            return False

        self.set_mode_of_sub(self.acquire_bar_controller.mode)
        self.update_buffer()
            
        return True

    def set_mode_of_sub(self, mode):
        """
        # set mode to sub-controllers.
        """
        self.channels_tab_controller.set_mode(mode)
        self.camera_view_controller.set_mode(mode)
        self.camera_setting_controller.set_mode(mode)
        if hasattr(self, 'etl_controller') and self.etl_controller:
            self.etl_controller.set_mode(mode)

    def update_camera_view(self):
        """
        # Function aims to update the real-time parameters in the camera view, including the
        # channel number, the max counts, the image, etc.
        """
        create_threads = False
        if create_threads:
            self.threads_pool.createThread(
                'camera_display',
                self.camera_view_controller.display_image(
                    self.model.data))
            self.threads_pool.createThread(
                'update_GUI', self.camera_view_controller.update_channel_idx(
                    self.model.current_channel))
        else:
            self.camera_view_controller.display_image(self.model.data)
            self.camera_view_controller.update_channel_idx(
                self.model.current_channel)

    def execute(self, command, *args):
        """
        # This function listens to sub_gui_controllers
        # In general, the controller.experiment is passed as an argument to the model, which then overwrites
        # the model.experiment.  Workaround due to model being in a sub-process.
        """
        if command == 'stage':
            """
            # Creates a thread and uses it to call the model to move stage
            """
            self.threads_pool.createThread('stage', self.move_stage, args=({args[1] + '_abs': args[0]},))

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

        elif command == 'resolution':
            """
            #  Changes the resolution mode and zoom position.
            #  one Argument = self.resolution_value
            #  values: 'high', '0.63x', '1x', '2x'...'6x'
            """
            self.model.change_resolution(args)

            # tell camera setting tab to recalculate FOV_X and FOV_Y
            self.camera_setting_controller.calculate_physical_dimensions(args[0])

            # tell etl popup if there is one opened
            if hasattr(self, 'etl_controller') and self.etl_controller:
                self.etl_controller.set_experiment_values(args[0])

        elif command == 'set_save':
            self.acquire_bar_controller.set_save_option(args[0])

        elif command == 'update_setting':
            """
            Called by ETL_Popup_Controller.  
            Passes the string 'resolution' and a dictionary
            consisting of the resolution_mode, the zoom, and the laser_info.
            e.g., self.resolution_info.ETLConstants[self.resolution][self.mag]
            """
            self.threads_pool.createThread('model', lambda: self.model.run_command('update_setting', *args))

        elif command == 'autofocus':
            self.threads_pool.createThread('camera', self.capture_autofocus_image)
            
        elif command == 'acquire_and_save':
            if not self.prepare_acquire_data():
                self.acquire_bar_controller.stop_acquire()
                return

            # create file directory
            # TODO: create_save_path unresolved.
            file_directory = create_save_path(args[0], self.verbose)

            # save experiment file
            save_yaml_file(file_directory, self.experiment.serialize())

            self.execute('acquire')

        elif command == 'acquire':
            """
            # Acquisition Button Triggered by User.
            # Acquisition modes can be: 'continuous', 'z-stack', 'single', 'projection'
            """
            if not self.prepare_acquire_data():
                self.acquire_bar_controller.stop_acquire()
                return

            if self.acquire_bar_controller.mode == 'single':
                self.threads_pool.createThread('camera', self.capture_single_image)

            elif self.acquire_bar_controller.mode == 'live':
                self.threads_pool.createThread('camera', self.capture_live_image)

            elif self.acquire_bar_controller.mode == 'z-stack':
                is_multi_position = self.channels_tab_controller.is_multiposition_val.get()
                self.model.open_shutter()
                self.model.run_z_stack_acquisition(is_multi_position, self.update_camera_view())
                self.model.close_shutter()

            elif self.acquire_bar_controller.mode == 'projection':
                pass

            else:
                print("Wrong acquisition mode.  Not recognized.")
                logger.info("Wrong acquisition mode. Not recognized.")
                pass

        elif command == 'stop_acquire':
            self.model.run_command('stop')
            self.set_mode_of_sub('stop')

        elif command == 'exit':
            self.model.run_command('stop')
            if hasattr(self, 'etl_controller'):
                self.etl_controller.save_etl_info()
            self.model.terminate()
            self.model = None
            self.event_queue.put(('stop', ''))
            # self.threads_pool.clear()

        if self.verbose:
            print(
                'In central controller: command passed from child',
                command,
                args)
        logger.debug(f"In central controller: command passed from child, {command}, {args}")

    def capture_single_image(self):
        """
        # Trigger model to capture a single image
        """
        self.camera_view_controller.image_count = 0
        self.model.run_command('single',
                               microscope_info=self.experiment.MicroscopeState,
                               camera_info=self.experiment.CameraParameters,
                               saving_info=self.experiment.Saving)

        image_id = self.show_img_pipe_parent.recv()
        self.camera_view_controller.display_image(self.data_buffer[image_id])
        # get 'stop' from the pipe
        self.show_img_pipe_parent.recv()
        self.set_mode_of_sub('stop')

    def capture_live_image(self):
        """
        Trigger model to capture a live image stream
        """
        self.camera_view_controller.image_count = 0
        self.model.run_command('live',
                               microscope_info=self.experiment.MicroscopeState,
                               camera_info=self.experiment.CameraParameters)

        while True:
            image_id = self.show_img_pipe_parent.recv()
            if self.verbose:
                print('receive', image_id)
            logger.debug(f"recieve, {image_id}")
            if image_id == 'stop':
                break
            if not isinstance(image_id, int):
                print('some thing wrong happened, stop the model!', image_id)
                logger.debug(f"some thing wrong happened, stop the model!, {image_id}")
                self.execute('stop_acquire')
            self.camera_view_controller.display_image(
                self.data_buffer[image_id])

        if self.verbose:
            print("Captured", self.camera_view_controller.image_count, "Live Images")
        logger.debug(f"Captured {self.camera_view_controller.image_count}, Live Images")

    def capture_autofocus_image(self):
        """
        # Trigger model to capture a single image
        """
        if not self.prepare_acquire_data():
            return
        pos = self.experiment.StageParameters['f']
        self.camera_view_controller.image_count = 0
        self.model.run_command(
            'autofocus',
            self.experiment.MicroscopeState,
            self.experiment.AutoFocusParameters,
            pos
            )
        while True:
            image_id = self.show_img_pipe_parent.recv()
            if image_id == 'stop':
                break
            self.camera_view_controller.display_image(self.data_buffer[image_id])
            # get focus position and update it in GUI

        # Rec plot data from model and send to sub controller to display plot
        plot_data = self.plot_pipe_controller.recv()
        if self.verbose:
            print("Controller received plot data: ", plot_data)
        logger.debug(f"Controller recieved plot data: {plot_data}")
        if hasattr(self, 'af_popup_controller'):
            self.af_popup_controller.display_plot(plot_data)
        
        self.set_mode_of_sub('stop')
    
    def move_stage(self, args):
        self.model.move_stage(args)

    def update_event(self):
        while True:
            event, value = self.event_queue.get()
            if event == 'waveform':
                self.waveform_tab_controller.plot_waveforms2(value, self.configuration.DAQParameters['sample_rate'])
            elif event == 'stop':
                break


if __name__ == '__main__':
    # Testing section.

    print("done")
    logger.info("done")
