# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


#  Standard Library Imports
from multiprocessing import Manager
import tkinter
from tkinter import messagebox
import multiprocessing as mp
import threading
import sys
import os
import time

# Third Party Imports

# Local View Imports
from aslm.view.main_application_window import MainApp as view
from aslm.view.popups.camera_view_popup_window import CameraViewPopupWindow
from aslm.view.popups.feature_list_popup import FeatureListPopup

# Local Sub-Controller Imports
from aslm.controller.configuration_controller import ConfigurationController
from aslm.controller.sub_controllers import (
    KeystrokeController,
    WaveformTabController,
    StageController,
    CameraSettingController,
    CameraViewController,
    MultiPositionController,
    ChannelsTabController,
    AcquireBarController,
    FeaturePopupController,
    MenuController,
)

from aslm.controller.thread_pool import SynchronizedThreadPool

# Local Model Imports
from aslm.model.model import Model
from aslm.model.concurrency.concurrency_tools import ObjectInSubprocess

# Misc. Local Imports
from aslm.config.config import (
    load_configs,
    update_config_dict,
    verify_experiment_config,
    verify_waveform_constants,
    get_aslm_path,
)
from aslm.tools.file_functions import create_save_path, save_yaml_file
from aslm.tools.common_dict_tools import update_stage_dict
from aslm.tools.multipos_table_tools import update_table
from aslm.tools.common_functions import combine_funcs

# Logger Setup
import logging

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Controller:
    """ASLM Controller"""

    def __init__(
        self,
        root,
        splash_screen,
        configuration_path,
        experiment_path,
        waveform_constants_path,
        rest_api_path,
        waveform_templates_path,
        args,
    ):
        """Initialize the ASLM Controller.

        Parameters
        ----------
        root : Tk top-level widget.
            Tk.tk GUI instance.
        splash_screen : Tk top-level widget.
            Tk.tk GUI instance.
        configuration_path : string
            Path to the configuration yaml file.
            Provides global microscope configuration parameters.
        experiment_path : string
            Path to the experiment yaml file.
            Provides experiment-specific microscope configuration.
        waveform_constants_path : string
            Path to the waveform constants yaml file.
            Provides magnification and wavelength-specific parameters.
        rest_api_path : string
            Path to the REST API yaml file.
            Provides REST API configuration parameters.
        waveform_templates_path : string
            Path to the waveform templates yaml file.
            Provides waveform templates for each channel.
        *args :
            Command line input arguments for non-default
            file paths or using synthetic hardware modes.
        """

        #: Object: Thread pool for the controller.
        self.threads_pool = SynchronizedThreadPool()

        #: mp.Queue: Queue for retrieving events ('event_name', value) from model
        self.event_queue = mp.Queue(100)

        #: Manager: A shared memory manager
        self.manager = Manager()
        #: dict: Configuration dictionary
        self.configuration = load_configs(
            self.manager,
            configuration=configuration_path,
            experiment=experiment_path,
            waveform_constants=waveform_constants_path,
            rest_api_config=rest_api_path,
            waveform_templates=waveform_templates_path,
        )

        verify_experiment_config(self.manager, self.configuration)
        verify_waveform_constants(self.manager, self.configuration)

        # Initialize the Model
        #: ObjectInSubprocess: Model object in MVC architecture.
        self.model = ObjectInSubprocess(
            Model, args, self.configuration, event_queue=self.event_queue
        )

        logger.info(f"Spec - Configuration Path: {configuration_path}")
        logger.info(f"Spec - Experiment Path: {experiment_path}")
        logger.info(f"Spec - Waveform Constants Path: {waveform_constants_path}")
        logger.info(f"Spec - Rest API Path: {rest_api_path}")

        # Wire up pipes
        #: mp.Pipe: Pipe for sending images from model to view.
        self.show_img_pipe = self.model.create_pipe("show_img_pipe")

        # save default experiment file
        #: string: Path to the default experiment yaml file.
        self.default_experiment_file = experiment_path

        # waveform setting file
        #: string: Path to the waveform constants yaml file.
        self.waveform_constants_path = waveform_constants_path

        # Configuration Reader
        #: ConfigurationController: Configuration Controller object.
        self.configuration_controller = ConfigurationController(self.configuration)

        # Initialize the View
        #: View: View object in MVC architecture.
        self.view = view(root=root, configuration=self.configuration)

        # Sub Gui Controllers
        #: AcquireBarController: Acquire Bar Sub-Controller.
        self.acquire_bar_controller = AcquireBarController(
            self.view.acqbar, self.view.settings.channels_tab, self
        )
        #: ChannelsTabController: Channels Tab Sub-Controller.
        self.channels_tab_controller = ChannelsTabController(
            self.view.settings.channels_tab, self
        )
        #: MultiPositionController: Multi-Position Tab Sub-Controller.
        self.multiposition_tab_controller = MultiPositionController(
            self.view.settings.multiposition_tab.multipoint_list, self
        )
        #: CameraViewController: Camera View Tab Sub-Controller.
        self.camera_view_controller = CameraViewController(
            self.view.camera_waveform.camera_tab, self
        )
        #: CameraSettingController: Camera Settings Tab Sub-Controller.
        self.camera_setting_controller = CameraSettingController(
            self.view.settings.camera_settings_tab, self
        )
        #: StageController: Stage Sub-Controller.
        self.stage_controller = StageController(
            self.view.settings.stage_control_tab,
            self.view,
            self.camera_view_controller.canvas,
            self,
        )
        #: WaveformTabController: Waveform Display Sub-Controller.
        self.waveform_tab_controller = WaveformTabController(
            self.view.camera_waveform.waveform_tab, self
        )
        #: KeystrokeController: Keystroke Sub-Controller.
        self.keystroke_controller = KeystrokeController(self.view, self)

        # Exit
        self.view.root.protocol(
            "WM_DELETE_WINDOW", self.acquire_bar_controller.exit_program
        )

        # Bonus config
        self.update_acquire_control()

        t = threading.Thread(target=self.update_event)
        t.start()

        # self.microscope = self.configuration['configuration']
        # ['microscopes'].keys()[0]  # Default to the first microscope

        # Initialize the menus
        #: MenuController: Menu Sub-Controller.
        self.menu_controller = MenuController(view=self.view, parent_controller=self)
        self.menu_controller.initialize_menus()

        # Create default data buffer
        #: int: Number of x_pixels from microscope configuration file.
        self.img_width = 0
        #: int: Number of y_pixels from microscope configuration file.
        self.img_height = 0
        #: SharedNDArray: Pre-allocated shared memory array.
        self.data_buffer = None
        #: dict: Additional microscopes.
        self.additional_microscopes = {}
        #: dict: Additional microscope configurations.
        self.additional_microscopes_configs = {}
        #: bool: Flag for stopping acquisition.
        self.stop_acquisition_flag = False

        # Set view based on model.experiment
        self.populate_experiment_setting(in_initialize=True)

        # Camera View Tab
        self.initialize_cam_view()

        # destroy splash screen and show main screen
        splash_screen.destroy()
        root.deiconify()
        #: event: Event for resizing the GUI.
        self.resizie_event_id = None
        self.view.root.bind("<Configure>", self.resize)

    def update_buffer(self):
        """Update the buffer size according to the camera
        dimensions listed in the experimental parameters.

        Returns
        -------
        self.img_width : int
            Number of x_pixels from microscope configuration file.
        self.image_height : int
            Number of y_pixels from microscope configuration file.
        self.data_buffer : SharedNDArray
            Pre-allocated shared memory array.
            Size dictated by x_pixels, y_pixels, an number_of_frames in
            configuration file.
        """
        img_width = int(
            self.configuration["experiment"]["CameraParameters"]["img_x_pixels"]
        )
        img_height = int(
            self.configuration["experiment"]["CameraParameters"]["img_y_pixels"]
        )
        if img_width == self.img_width and img_height == self.img_height:
            return

        self.data_buffer = self.model.get_data_buffer(img_width, img_height)
        self.img_width = img_width
        self.img_height = img_height

    def update_acquire_control(self):
        """Update the acquire control based on the current experiment parameters."""
        self.view.acqbar.stop_stage.config(
            command=self.stage_controller.stop_button_handler
        )

    def change_microscope(self, microscope_name):
        """Change the microscope configuration.

        Parameters
        ----------
        microscope_name : string
            Name of the microscope to change to.
        """
        self.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ] = microscope_name
        if self.configuration_controller.change_microscope():
            # update widgets
            self.stage_controller.initialize()
            self.channels_tab_controller.initialize()
            self.camera_setting_controller.update_camera_device_related_setting()
            self.camera_setting_controller.calculate_physical_dimensions()
            if (
                hasattr(self, "waveform_popup_controller")
                and self.waveform_popup_controller
            ):
                self.waveform_popup_controller.populate_experiment_values()
            self.camera_view_controller.update_snr()

    def initialize_cam_view(self):
        """Populate view tab.

        Populate widgets with necessary data from
        config file via config controller. For the entire view tab.
        Sets the minimum and maximum counts
        for when the data is not being autoscaled.
        """
        # Populating Min and Max Counts
        minmax_values = [0, 2**16 - 1]
        self.camera_view_controller.initialize("minmax", minmax_values)
        image_metrics = [1, 0, 0]
        self.camera_view_controller.initialize("image", image_metrics)

    def populate_experiment_setting(self, file_name=None, in_initialize=False):
        """Load experiment file and populate model.experiment and configure view.

        Confirms that the experiment file exists.
        Sends the experiment file to the model and the controller.
        Populates the GUI with these settings.

        Parameters
        __________
        file_name : string
            file_name = path to the non-default experiment yaml file.

        """
        # read the new file and update info of the configuration dict
        if not in_initialize:
            update_config_dict(
                self.manager, self.configuration, "experiment", file_name
            )
            verify_experiment_config(self.manager, self.configuration)

        # update buffer
        self.update_buffer()

        # Configure GUI
        microscope_name = self.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ]
        self.configuration_controller.change_microscope()
        self.menu_controller.resolution_value.set(
            f"{microscope_name} "
            f"{self.configuration['experiment']['MicroscopeState']['zoom']}"
        )
        self.menu_controller.disable_stage_limits.set(
            0 if self.configuration["experiment"]["StageParameters"]["limits"] else 1
        )
        self.execute(
            "stage_limits",
            self.configuration["experiment"]["StageParameters"]["limits"],
        )

        self.acquire_bar_controller.populate_experiment_values()
        # self.stage_controller.populate_experiment_values()
        self.multiposition_tab_controller.set_positions(
            self.configuration["experiment"]["MultiPositions"]
        )
        self.channels_tab_controller.populate_experiment_values()
        self.camera_setting_controller.populate_experiment_values()

        # autofocus popup
        if hasattr(self, "af_popup_controller"):
            self.af_popup_controller.populate_experiment_values()

        # set widget modes
        self.set_mode_of_sub("stop")
        self.stage_controller.initialize()

    def update_experiment_setting(self):
        """Update model.experiment according to values in the GUI

        Collect settings from sub-controllers will validate the value, if something
        is wrong, it will return False

        Returns
        -------
        bool
            True if all settings are valid, False otherwise.

        """
        # acquire_bar_controller - update image mode
        self.configuration["experiment"]["MicroscopeState"][
            "image_mode"
        ] = self.acquire_bar_controller.get_mode()
        self.camera_setting_controller.update_experiment_values()
        # update multi-positions
        positions = self.multiposition_tab_controller.get_positions()
        update_config_dict(
            self.manager,
            self.configuration["experiment"],
            "MultiPositions",
            positions,
        )
        self.configuration["experiment"]["MicroscopeState"][
            "multiposition_count"
        ] = len(positions)

        # TODO: validate experiment dict
        if self.configuration["experiment"]["MicroscopeState"]["scanrange"] == 0:
            return False
        if self.configuration["experiment"]["MicroscopeState"]["number_z_steps"] < 1:
            return False
        return True

    def resize(self, event):
        """Resize the GUI.

        Parameters
        __________
        event : event
            event = <Configure x=0 y=0 width=1200 height=600>
        """

        def refresh(width, height):
            if width < 1200 or height < 600:
                return
            self.view.camera_waveform["width"] = (
                width - self.view.frame_left.winfo_width() - 81
            )
            self.view.camera_waveform["height"] = height - 110

        if event.widget != self.view.scroll_frame:
            return
        if self.resizie_event_id:
            self.view.after_cancel(self.resizie_event_id)
        self.resizie_event_id = self.view.after(
            1000, lambda: refresh(event.width, event.height)
        )

    def prepare_acquire_data(self):
        """Prepare the acquisition data.

        Updates model.experiment.
        Sets sub-controller's mode to 'live' when 'continuous is selected, or 'stop'.

        Returns
        -------
        bool
            True if all settings are valid, False otherwise.
        """
        if not self.update_experiment_setting():
            messagebox.showerror(
                title="Warning",
                message="There are some missing/wrong settings! "
                "Cannot start acquisition!",
            )
            return False

        # set waveform template
        if self.acquire_bar_controller.mode == "confocal-projection":
            self.configuration["experiment"]["MicroscopeState"][
                "waveform_template"
            ] = "Confocal-Projection"
        else:
            self.configuration["experiment"]["MicroscopeState"][
                "waveform_template"
            ] = "Default"

        # update real image width and height
        self.set_mode_of_sub(self.acquire_bar_controller.mode)
        self.update_buffer()
        return True

    def set_mode_of_sub(self, mode):
        """Communicates imaging mode to sub-controllers.

        Parameters
        __________
        mode : string
            string = 'live', 'stop'
        """
        self.channels_tab_controller.set_mode(mode)
        self.camera_view_controller.set_mode(mode)
        self.camera_setting_controller.set_mode(mode)
        self.waveform_tab_controller.set_mode(mode)
        if mode == "stop":
            # GUI Failsafe
            self.acquire_bar_controller.stop_acquire()
            # self.menu_controller.feature_id_val.set(0)

    def execute(self, command, *args):
        """Functions listens to the Sub_Gui_Controllers.

        The controller.experiment is passed as an argument to the model, which then
        overwrites the model.experiment. Workaround due to model being in a sub-process.

        Parameters
        __________
        command : string
            string = 'stage', 'stop_stage', 'move_stage_and_update_info',
        args* : function-specific passes.
        """

        if command == "joystick_toggle":
            """Toggles the joystick mode on/off."""
            if self.stage_controller.joystick_is_on:
                self.execute("stop_stage")

        elif command == "stage":
            """Creates a thread and uses it to call the model to move stage

            Parameters
            __________
            args[0] : dict
                dict = {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}
            """
            self.threads_pool.createThread(
                "model", self.move_stage, args=({args[1] + "_abs": args[0]},)
            )

        elif command == "stop_stage":
            """Creates a thread and uses it to call the model to stop stage"""
            self.threads_pool.createThread("stop_stage", self.stop_stage)

        elif command == "move_stage_and_update_info":
            """update stage view to show the position

            Parameters
            __________
            args[0] : dict
                dict = {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}
            """
            self.stage_controller.set_position(args[0])

        elif command == "move_stage_and_acquire_image":
            """update stage and acquire an image

            Parameters
            __________
            args[0] : dict
                dict = {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}
            """
            stage_pos = dict(map(lambda axis: (axis + "_abs", args[0][axis]), args[0]))
            self.move_stage(stage_pos)
            self.update_stage_controller_silent(stage_pos)
            self.acquire_bar_controller.set_mode("single")
            self.execute("acquire")

        elif command == "get_stage_position":
            """Returns the current stage position

            Returns
            -------
                dict = {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}
            """
            return self.stage_controller.get_position()

        elif command == "mark_position":
            """Appends a position to the multi-position list.

            Parameters
            __________
            args[0] : dict
                dict = {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}
                values are in float64
            """
            self.multiposition_tab_controller.append_position(args[0])

        elif command == "resolution":
            """Changes the resolution mode and zoom position.

            Recalculates FOV_X and FOV_Y
            If Waveform Popup is open, communicates changes to it.

            Parameters
            ----------
            args : dict
                dict = {'resolution_mode': self.resolution,
                'zoom': self.mag,
                'laser_info': self.resolution_info[
                'remote_focus_constants'][self.resolution][self.mag]
                }
            """
            microscope_name, zoom = self.menu_controller.resolution_value.get().split()
            self.configuration["experiment"]["MicroscopeState"]["zoom"] = zoom
            if (
                microscope_name
                != self.configuration["experiment"]["MicroscopeState"][
                    "microscope_name"
                ]
            ):
                self.change_microscope(microscope_name)
            work_thread = self.threads_pool.createThread(
                "model", lambda: self.model.run_command("update_setting", "resolution")
            )
            work_thread.join()

        elif command == "set_save":
            """Set whether the image will be saved.

            Parameters
            __________
            args : Boolean
                is_save = True/False
            """
            self.acquire_bar_controller.set_save_option(args[0])

        elif command == "update_setting":
            """Called by the Waveform Constants Popup Controller
            to update the Waveform constants settings in memory.

            Parameters
            __________
            args[0] : string
                string = 'resolution' or 'waveform' or 'galvo'...
            args[1] : dict
                dict = {
                'resolution_mode': self.resolution,
                'zoom': self.mag,
                'laser_info': self.resolution_info[
                'remote_focus_constants'][self.resolution][self.mag]
                }
            """
            self.threads_pool.createThread(
                "model", lambda: self.model.run_command("update_setting", *args)
            )

        elif command == "stage_limits":
            self.stage_controller.stage_limits = args[0]
            self.threads_pool.createThread(
                "model", lambda: self.model.run_command("stage_limits", *args)
            )

        elif command == "autofocus":
            """Execute autofocus routine."""
            self.threads_pool.createThread(
                "camera",
                self.capture_image,
                args=("autofocus", "live", *args),
            )

        elif command == "load_feature":
            """Tell model to load/unload features."""
            self.threads_pool.createThread(
                "model", lambda: self.model.run_command("load_feature", *args)
            )

        elif command == "acquire_and_save":
            """Acquire data and save it.

            Prepares the acquisition data.
            Creates the file directory for saving the data.
            Saves the experiment file to that directory.
            Acquires the data.

            Parameters
            __________
            args[0] : dict
                dict = self.save_settings from the experiment.yaml file.

            """
            if not self.prepare_acquire_data():
                self.acquire_bar_controller.stop_acquire()
                return
            saving_settings = self.configuration["experiment"]["Saving"]
            file_directory = create_save_path(saving_settings)
            save_yaml_file(
                file_directory,
                self.configuration["experiment"],
                filename="experiment.yml",
            )
            self.camera_setting_controller.solvent = self.configuration["experiment"][
                "Saving"
            ]["solvent"]
            self.camera_setting_controller.calculate_physical_dimensions()
            self.execute("acquire")

        elif command == "acquire":
            """Acquire data.

            Triggered when the Acquire button is hit by the user in the GUI.

            Prepares the acquisition data.

            Parameters
            __________
            args[0] : string
                string = 'continuous', 'z-stack', 'single', or 'projection'
            """
            # Prepare data
            if not self.prepare_acquire_data():
                self.acquire_bar_controller.stop_acquire()
                return

            # ask user to verify feature list parameters if in "customized" mode
            if self.acquire_bar_controller.mode == "customized":
                feature_id = self.menu_controller.feature_id_val.get()
                if feature_id > 0:
                    if hasattr(self, "features_popup_controller"):
                        self.features_popup_controller.exit_func()
                    feature_list_popup = FeatureListPopup(
                        self.view, title="Feature List Configuration"
                    )
                    self.features_popup_controller = FeaturePopupController(
                        feature_list_popup, self
                    )
                    self.features_popup_controller.populate_feature_list(feature_id)
                    # wait until close the popup windows
                    self.view.wait_window(feature_list_popup.popup)
                    # do not run acquisition if "cancel" is selected
                    temp = self.features_popup_controller.start_acquisiton_flag
                    delattr(self, "features_popup_controller")
                    if not temp:
                        self.set_mode_of_sub("stop")
                        return

            # if select 'ilastik segmentation',
            # 'show segmentation',
            # and in 'single acquisition'
            self.camera_view_controller.display_mask_flag = (
                self.acquire_bar_controller.mode == "single"
                and self.menu_controller.feature_id_val.get() == 4
                and self.ilastik_controller.show_segmentation_flag
            )

            self.stop_acquisition_flag = False
            self.launch_additional_microscopes()

            self.threads_pool.createThread(
                "camera",
                self.capture_image,
                args=(
                    "acquire",
                    self.acquire_bar_controller.mode,
                ),
            )

        elif command == "stop_acquire":
            """Stop the acquisition."""
            self.stop_acquisition_flag = True

            # self.model.run_command('stop')
            self.sloppy_stop()
            self.menu_controller.feature_id_val.set(0)

            # clear show_img_pipe
            while self.show_img_pipe.poll():
                # TODO: image_id never called.
                self.show_img_pipe.recv()
                # image_id = self.show_img_pipe.recv()

        elif command == "exit":
            """Exit the program."""
            # Save current GUI settings to .ASLM/config/experiment.yml file.
            self.sloppy_stop()
            # self.menu_controller.feature_id_val.set(0)

            self.update_experiment_setting()
            file_directory = os.path.join(get_aslm_path(), "config")
            save_yaml_file(
                file_directory=file_directory,
                content_dict=self.configuration["experiment"],
                filename="experiment.yml",
            )
            if hasattr(self, "waveform_popup_controller"):
                self.waveform_popup_controller.save_waveform_constants()

            self.model.run_command("terminate")
            self.model = None
            self.event_queue.put(("stop", ""))
            self.threads_pool.clear()
            sys.exit()

        logger.info(f"ASLM Controller - command passed from child, {command}, {args}")

    def sloppy_stop(self):
        """Keep trying to stop the model until successful.

        TODO: Delete this function!!!

        This is set up to get around the conflict between
        self.threads_pool.createThread('model', target)
        commands and the need to stop as abruptly as
        possible when the user hits stop. Here we leverage
        ObjectInSubprocess's refusal to let us access
        the model from two threads to our advantage, and just
        try repeatedly until we get a command in front
        of the next command in the model threads_pool resource.
        We should instead pause the model thread pool
        and interject our stop command, or clear the queue
        in threads_pool.
        """
        e = RuntimeError
        while e == RuntimeError:
            try:
                self.model.run_command("stop")
                e = None
            except RuntimeError:
                e = RuntimeError

    def capture_image(self, command, mode, *args):
        """Trigger the model to capture images.

        Parameters
        ----------
        command : string
            string = 'acquire' or 'autofocus'
        mode : string
            string = 'continuous', 'z-stack', 'single', or 'projection'
        args : function-specific passes.
        """
        self.camera_view_controller.image_count = 0

        # Start up Progress Bars
        images_received = 0
        self.acquire_bar_controller.progress_bar(
            images_received=images_received,
            microscope_state=self.configuration["experiment"]["MicroscopeState"],
            mode=mode,
            stop=False,
        )
        try:
            self.model.run_command(command, *args)
        except Exception as e:
            messagebox.showerror(
                title="Error:",
                message=f"WARNING:\n{e}",
            )
            self.set_mode_of_sub("stop")
            return
        self.acquire_bar_controller.view.acquire_btn.configure(text="Stop")
        self.acquire_bar_controller.view.acquire_btn.configure(state="normal")

        self.camera_view_controller.initialize_non_live_display(
            self.data_buffer,
            self.configuration["experiment"]["MicroscopeState"],
            self.configuration["experiment"]["CameraParameters"],
        )

        self.stop_acquisition_flag = False

        while True:
            if self.stop_acquisition_flag:
                break
            # Receive the Image and log it.
            image_id = self.show_img_pipe.recv()
            logger.info(f"ASLM Controller - Received Image: {image_id}")

            if image_id == "stop":
                break
            if not isinstance(image_id, int):
                logger.debug(
                    f"ASLM Controller - Something wrong happened, stop the model!, "
                    f"{image_id}"
                )
                self.execute("stop_acquire")

            # Display the Image in the View
            self.camera_view_controller.try_to_display_image(image_id=image_id)
            images_received += 1

            # Update progress bar.
            self.acquire_bar_controller.progress_bar(
                images_received=images_received,
                microscope_state=self.configuration["experiment"]["MicroscopeState"],
                mode=mode,
                stop=False,
            )

        logger.info(f"ASLM Controller - Captured {images_received}, " f"{mode} Images")

        # Stop Progress Bars
        self.acquire_bar_controller.progress_bar(
            images_received=images_received,
            microscope_state=self.configuration["experiment"]["MicroscopeState"],
            mode=mode,
            stop=True,
        )
        self.set_mode_of_sub("stop")

    def launch_additional_microscopes(self):
        """Launch additional microscopes."""

        def display_images(camera_view_controller, show_img_pipe, data_buffer):
            """Display images from additional microscopes.

            Parameters
            ----------
            camera_view_controller : CameraViewController
                Camera View Controller object.
            show_img_pipe : multiprocessing.Pipe
                Pipe for showing images.
            data_buffer : SharedNDArray
                Pre-allocated shared memory array.
                Size dictated by x_pixels, y_pixels, an number_of_frames in
                configuration file.
            """
            camera_view_controller.initialize_non_live_display(
                data_buffer,
                self.configuration["experiment"]["MicroscopeState"],
                self.configuration["experiment"]["CameraParameters"],
            )
            images_received = 0
            while True:
                if self.stop_acquisition_flag:
                    break
                # Receive the Image and log it.
                image_id = show_img_pipe.recv()
                logger.info(f"ASLM Controller - Received Image: {image_id}")

                if image_id == "stop":
                    break
                if not isinstance(image_id, int):
                    logger.debug(
                        f"ASLM Controller - Something wrong happened in additional "
                        f"microscope!, {image_id}"
                    )
                    break

                # Display the Image in the View
                try:
                    camera_view_controller.try_to_display_image(
                        image_id=image_id,
                    )
                except tkinter._tkinter.TclError:
                    print("Can't show images for the additional microscope!")
                    break
                images_received += 1

        # destroy unnecessary additional microscopes
        temp = []
        for microscope_name in self.additional_microscopes:
            if microscope_name not in self.additional_microscopes_configs:
                temp.append(microscope_name)
        for microscope_name in temp:
            del self.additional_microscopes[microscope_name]
            self.model.destroy_virtual_microscope(microscope_name)

        # show additional camera view popup
        for microscope_name in self.additional_microscopes_configs:
            if microscope_name not in self.additional_microscopes:
                show_img_pipe = self.model.create_pipe(
                    f"{microscope_name}_show_img_pipe"
                )
                data_buffer = self.model.launch_virtual_microscope(
                    microscope_name,
                    self.additional_microscopes_configs[microscope_name],
                )

                self.additional_microscopes[microscope_name] = {
                    "show_img_pipe": show_img_pipe,
                    "data_buffer": data_buffer,
                }
            if (
                self.additional_microscopes[microscope_name].get(
                    "camera_view_controller", None
                )
                is None
            ):
                popup_window = CameraViewPopupWindow(self.view, microscope_name)
                camera_view_controller = CameraViewController(
                    popup_window.camera_view, self
                )
                camera_view_controller.data_buffer = self.additional_microscopes[
                    microscope_name
                ]["data_buffer"]
                popup_window.popup.bind("<Configure>", camera_view_controller.resize)
                self.additional_microscopes[microscope_name][
                    "camera_view_controller"
                ] = camera_view_controller
                popup_window.popup.protocol(
                    "WM_DELETE_WINDOW",
                    combine_funcs(
                        popup_window.popup.dismiss,
                        lambda: self.additional_microscopes[microscope_name].pop(
                            "camera_view_controller"
                        ),
                    ),
                )

            # clear show_img_pipe
            show_img_pipe = self.additional_microscopes[microscope_name][
                "show_img_pipe"
            ]
            while show_img_pipe.poll():
                image_id = show_img_pipe.recv()
                if image_id == "stop":
                    break

            # start thread
            capture_img_thread = threading.Thread(
                target=display_images,
                args=(
                    self.additional_microscopes[microscope_name][
                        "camera_view_controller"
                    ],
                    show_img_pipe,
                    self.additional_microscopes[microscope_name]["data_buffer"],
                ),
            )
            capture_img_thread.start()

    def move_stage(self, pos_dict):
        """Trigger the model to move the stage.

        Parameters
        ----------
        pos_dict : dict
            Dictionary of axis positions
        """
        # Update our local stage dictionary
        update_stage_dict(self, pos_dict)

        # Pass to model
        self.model.move_stage(pos_dict)

    def stop_stage(self):
        """Stop the stage.

        Grab the stopped position from the stage
        and update the GUI control values accordingly.
        """
        self.model.stop_stage()

    def update_stage_controller_silent(self, ret_pos_dict):
        """Send updates to the stage GUI

        Parameters
        ----------
        ret_pos_dict : dict
            Dictionary of axis positions
        """
        stage_gui_dict = {}
        for axis, val in ret_pos_dict.items():
            ax = axis.split("_")[0]
            stage_gui_dict[ax] = val
        self.stage_controller.set_position_silent(stage_gui_dict)

    def update_event(self):
        """Update the View/Controller based on events from the Model."""
        while True:
            event, value = self.event_queue.get()

            if event == "warning":
                # Display a warning that arises from the model as a top-level GUI popup
                messagebox.showwarning(title="ASLM", message=value)

            elif event == "waveform":
                # Update the waveform plot.
                self.waveform_tab_controller.update_waveforms(
                    waveform_dict=value,
                    sample_rate=self.configuration_controller.daq_sample_rate,
                )
            elif event == "multiposition":
                # Update the multi-position tab without appending to the list
                update_table(
                    table=self.view.settings.multiposition_tab.multipoint_list.get_table(),
                    pos=value,
                )
                self.channels_tab_controller.is_multiposition_val.set(True)
                self.channels_tab_controller.toggle_multiposition()

            elif event == "ilastik_mask":
                # Display the ilastik mask
                self.camera_view_controller.display_mask(mask=value)

            elif event == "autofocus":
                # Display the autofocus plot
                if hasattr(self, "af_popup_controller"):
                    self.af_popup_controller.display_plot(
                        data=value[0], line_plot=value[1], clear_data=value[2]
                    )

            elif event == "stop":
                # Stop the software
                break

            elif event == "update_stage":
                # ZM: I am so sorry for this.
                for _ in range(10):
                    try:
                        self.update_stage_controller_silent(value)
                        break
                    except RuntimeError:
                        time.sleep(0.001)
                        pass

            elif event == "framerate":
                self.camera_setting_controller.framerate_widgets["max_framerate"].set(
                    value
                )
            elif event == "remove_positions":
                self.multiposition_tab_controller.remove_positions(value)

    # def exit_program(self):
    #     """Exit the program.

    #     This function is called when the user clicks the exit button in the GUI.
    #     """
    #     if messagebox.askyesno("Exit", "Are you sure?"):
    #         logger.info("Exiting Program")
    #         self.execute("exit")
    #         sys.exit()
