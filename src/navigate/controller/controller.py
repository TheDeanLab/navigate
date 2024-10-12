# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
import platform

# Third Party Imports

# Local View Imports
from navigate.view.main_application_window import MainApp as view
from navigate.view.popups.camera_view_popup_window import CameraViewPopupWindow
from navigate.view.popups.feature_list_popup import FeatureListPopup

# Local Sub-Controller Imports
from navigate.controller.configuration_controller import ConfigurationController
from navigate.controller.sub_controllers import (
    KeystrokeController,
    WaveformTabController,
    StageController,
    CameraSettingController,
    CameraViewController,
    MIPViewController,
    MultiPositionController,
    ChannelsTabController,
    AcquireBarController,
    FeaturePopupController,
    MenuController,
    PluginsController,
    HistogramController,
    # MicroscopePopupController,
    # AdaptiveOpticsPopupController,
)

from navigate.controller.thread_pool import SynchronizedThreadPool

# Local Model Imports
from navigate.model.model import Model
from navigate.model.concurrency.concurrency_tools import ObjectInSubprocess

# Misc. Local Imports
from navigate.config.config import (
    load_configs,
    update_config_dict,
    verify_experiment_config,
    verify_waveform_constants,
    verify_configuration,
    get_navigate_path,
)
from navigate.tools.file_functions import create_save_path, save_yaml_file, get_ram_info
from navigate.tools.common_dict_tools import update_stage_dict
from navigate.tools.multipos_table_tools import update_table
from navigate.tools.common_functions import combine_funcs

# Logger Setup
import logging

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Controller:
    """Navigate Controller"""

    def __init__(
        self,
        root,
        splash_screen,
        configuration_path,
        experiment_path,
        waveform_constants_path,
        rest_api_path,
        waveform_templates_path,
        gui_configuration_path,
        args,
    ):
        """Initialize the Navigate Controller.

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
        gui_configuration_path : string
            Path to the GUI configuration yaml file.
            Provides GUI configuration parameters.
        *args :
            Command line input arguments for non-default
            file paths or using synthetic hardware modes.
        """
        #: Tk top-level widget: Tk.tk GUI instance.
        self.root = root

        #: Tk top-level widget: Tk.tk GUI instance.
        self.splash_screen = splash_screen

        #: string: Path to the configuration yaml file.
        self.configuration_path = configuration_path
        logger.info(f"Configuration Path: {self.configuration_path}")

        #: string: Path to the experiment yaml file.
        self.experiment_path = experiment_path
        logger.info(f"Experiment Path: {self.experiment_path}")

        #: string: Path to the waveform constants yaml file.
        self.waveform_constants_path = waveform_constants_path
        logger.info(f"Waveform Constants Path: {self.waveform_constants_path}")

        #: string: Path to the REST API yaml file.
        self.rest_api_path = rest_api_path
        logger.info(f"REST API Path: {self.rest_api_path}")

        #: string: Path to the waveform templates yaml file.
        self.waveform_templates_path = waveform_templates_path
        logger.info(f"Waveform Templates Path: {self.waveform_templates_path}")

        #: string: Path to the GUI configuration yaml file.
        self.gui_configuration_path = gui_configuration_path
        logger.info(f"GUI Configuration Path: {self.gui_configuration_path}")

        #: iterable: Non-default command line input arguments for
        self.args = args
        logger.info(f"Variable Input Arguments: {self.args}")

        #: Object: Thread pool for the controller.
        self.threads_pool = SynchronizedThreadPool()

        #: mp.Queue: Queue for retrieving events ('event_name', value) from model
        self.event_queue = mp.Queue(100)

        #: Manager: A shared memory manager
        self.manager = Manager()

        #: dict: Configuration dictionary
        self.configuration = load_configs(
            self.manager,
            configuration=self.configuration_path,
            experiment=self.experiment_path,
            waveform_constants=self.waveform_constants_path,
            rest_api_config=self.rest_api_path,
            waveform_templates=self.waveform_templates_path,
            gui=self.gui_configuration_path,
        )

        verify_configuration(self.manager, self.configuration)
        verify_experiment_config(self.manager, self.configuration)
        verify_waveform_constants(self.manager, self.configuration)

        total_ram, available_ram = get_ram_info()
        logger.info(
            f"Total RAM: {total_ram / 1024**3:.2f} GB. "
            f"Available RAM: {available_ram / 1024**3:.2f} GB."
        )

        #: ObjectInSubprocess: Model object in MVC architecture.
        self.model = ObjectInSubprocess(
            Model, args, self.configuration, event_queue=self.event_queue
        )

        #: mp.Pipe: Pipe for sending images from model to view.
        self.show_img_pipe = self.model.create_pipe("show_img_pipe")

        #: string: Path to the default experiment yaml file.
        self.default_experiment_file = self.experiment_path

        #: string: Path to the waveform constants yaml file.
        self.waveform_constants_path = waveform_constants_path

        #: ConfigurationController: Configuration Controller object.
        self.configuration_controller = ConfigurationController(self.configuration)

        #: View: View object in MVC architecture.
        self.view = view(self.root)

        #: dict: Event listeners for the controller.
        self.event_listeners = {}

        #: AcquireBarController: Acquire Bar Sub-Controller.
        self.acquire_bar_controller = AcquireBarController(self.view.acquire_bar, self)

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

        self.histogram_controller = HistogramController(
            self.view.camera_waveform.camera_tab.histogram, self
        )

        #: MIPSettingController: MIP Settings Tab Sub-Controller.
        self.mip_setting_controller = MIPViewController(
            self.view.camera_waveform.mip_tab, self
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

        # Exit the program when the window is closed
        self.view.root.protocol(
            "WM_DELETE_WINDOW", self.acquire_bar_controller.exit_program
        )

        # Bonus config
        self.update_acquire_control()

        t = threading.Thread(target=self.update_event)
        t.start()

        #: MenuController: Menu Sub-Controller.
        self.menu_controller = MenuController(view=self.view, parent_controller=self)
        self.menu_controller.initialize_menus()

        #: dict: acquisition modes from plugins
        self.plugin_acquisition_modes = {}

        #: PluginsController: Plugin Sub-Controller
        self.plugin_controller = PluginsController(
            view=self.view, parent_controller=self
        )
        self.plugin_controller.load_plugins()

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

        #: int: current image id in the buffer
        self.current_image_id = -1

        # Set view based on model.experiment
        self.populate_experiment_setting(in_initialize=True)

        # Camera View Tab
        self.initialize_cam_view()

        # destroy splash screen and show main screen
        self.splash_screen.destroy()
        self.root.deiconify()

        #: int: ID for the resize event.Only works on Windows OS.
        self.resize_event_id = None
        if platform.system() == "Windows":
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
        microscope_name = self.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ]
        img_width = int(
            self.configuration["experiment"]["CameraParameters"][microscope_name][
                "img_x_pixels"
            ]
        )
        img_height = int(
            self.configuration["experiment"]["CameraParameters"][microscope_name][
                "img_y_pixels"
            ]
        )
        if img_width == self.img_width and img_height == self.img_height:
            return

        self.data_buffer = self.model.get_data_buffer(img_width, img_height)
        self.img_width = img_width
        self.img_height = img_height

    def update_acquire_control(self):
        """Update the acquire control based on the current experiment parameters."""
        self.view.acquire_bar.stop_stage.config(
            command=self.stage_controller.stop_button_handler
        )

    def change_microscope(self, microscope_name, zoom=None):
        """Change the microscope configuration.

        Parameters
        ----------
        microscope_name : string
            Name of the microscope to change to.
        zoom : string
            Name of the zoom value to change to.
        """
        self.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ] = microscope_name
        if zoom:
            self.configuration["experiment"]["MicroscopeState"]["zoom"] = zoom
        if self.configuration_controller.change_microscope():
            # update widgets
            self.stage_controller.initialize()
            self.channels_tab_controller.initialize()
            self.camera_setting_controller.update_camera_device_related_setting()
            self.camera_setting_controller.populate_experiment_values()
            self.camera_setting_controller.calculate_physical_dimensions()
            self.camera_view_controller.update_snr()

        if (
            hasattr(self, "waveform_popup_controller")
            and self.waveform_popup_controller
        ):
            self.waveform_popup_controller.populate_experiment_values()

    def initialize_cam_view(self):
        """Populate view and maximum intensity projection tabs.

        Communicates with the camera view controller and mip setting controller to
        set the minimum and maximum counts, as well as the default channel settings.
        """
        # Populating Min and Max Counts
        self.camera_view_controller.initialize("minmax", [0, 2**16 - 1])
        self.mip_setting_controller.initialize("minmax", [0, 2**16 - 1])
        self.camera_view_controller.initialize("image", [1, 0, 0])

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
        self.waveform_tab_controller.set_waveform_template(
            self.configuration["experiment"]["MicroscopeState"]["waveform_template"]
        )

        # autofocus popup
        if hasattr(self, "af_popup_controller"):
            self.af_popup_controller.populate_experiment_values()

        if file_name:
            self.plugin_controller.populate_experiment_setting()

        # set widget modes
        self.set_mode_of_sub("stop")
        self.stage_controller.initialize()

    def update_experiment_setting(self):
        """Update model.experiment according to values in the GUI

        Collect settings from sub-controllers will validate the value, if something
        is wrong, it will return False

        Returns
        -------
        string
            Warning info if any

        """
        warning_message = self.camera_setting_controller.update_experiment_values()
        microscope_name = self.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ]

        # set waveform template
        if self.acquire_bar_controller.mode in ["live", "single", "z-stack"]:
            camera_setting = self.configuration["experiment"]["CameraParameters"][
                microscope_name
            ]
            if camera_setting["sensor_mode"] == "Light-Sheet" and camera_setting[
                "readout_direction"
            ] in ["Bidirectional", "Rev. Bidirectional"]:
                self.waveform_tab_controller.set_waveform_template("Bidirectional")
            else:
                self.waveform_tab_controller.set_waveform_template("Default")

        # update multi-positions
        positions = self.multiposition_tab_controller.get_positions()
        self.configuration["experiment"]["MultiPositions"] = positions
        self.configuration["experiment"]["MicroscopeState"][
            "multiposition_count"
        ] = len(positions)

        if (
            self.configuration["experiment"]["MicroscopeState"]["is_multiposition"]
            and len(positions) == 0
        ):
            # Update the view and override the settings.
            self.configuration["experiment"]["MicroscopeState"][
                "is_multiposition"
            ] = False
            self.channels_tab_controller.is_multiposition_val.set(False)

        # TODO: validate experiment dict

        warning_message += self.channels_tab_controller.verify_experiment_values()

        # additional microscopes
        for microscope_name in self.additional_microscopes_configs:
            if hasattr(self, f"{microscope_name.lower()}_camera_setting_controller"):
                getattr(
                    self, f"{microscope_name.lower()}_camera_setting_controller"
                ).update_experiment_values()
        if warning_message:
            return warning_message
        return ""

    def resize(self, event):
        """Resize the GUI.

        Parameters
        __________
        event : event
            event = <Configure x=0 y=0 width=1200 height=600>
        """

        def refresh(width, height):
            """Refresh the GUI.

            Parameters
            __________
            width : int
                Width of the GUI.
            height : int
                Height of the GUI.
            """
            if width < 1300 or height < 800:
                return
            self.view.camera_waveform["width"] = (
                width - self.view.left_frame.winfo_width() - 35
            )  #
            self.view.camera_waveform["height"] = height - 117

            print("camera_waveform height", self.view.camera_waveform["height"])

        if event.widget != self.view.scroll_frame:
            return
        if self.resize_event_id:
            self.view.after_cancel(self.resize_event_id)
        self.resize_event_id = self.view.after(
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
        warning_info = self.update_experiment_setting()
        if warning_info:
            messagebox.showerror(
                title="Warning",
                message=f"Cannot start acquisition!\n{warning_info}",
            )
            return False

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
        self.mip_setting_controller.set_mode(mode)
        self.waveform_tab_controller.set_mode(mode)

        # additional microscopes
        for microscope_name in self.additional_microscopes_configs:
            if hasattr(self, f"{microscope_name.lower()}_camera_setting_controller"):
                getattr(
                    self, f"{microscope_name.lower()}_camera_setting_controller"
                ).set_mode(mode)

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
            args : str
                "microscope_name zoom_value", "microscope_name", or "zoom_value"
            """
            # get microscope name and zoom value from args[0]
            temp = args[0].split()
            if len(temp) == 1:
                # microscope name is given
                if temp[0] in self.configuration_controller.microscope_list:
                    temp.append(
                        self.configuration_controller.get_zoom_value_list(temp[0])[0]
                    )
                elif temp[0] in self.configuration_controller.get_zoom_value_list(
                    self.configuration_controller.microscope_name
                ):
                    temp = [self.configuration_controller.microscope_name, temp[0]]
                else:
                    return
            resolution_value = " ".join(temp)
            if resolution_value != self.menu_controller.resolution_value.get():
                self.menu_controller.resolution_value.set(resolution_value)
                return
            self.change_microscope(temp[0], temp[1])
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
            if not self.acquire_bar_controller.is_acquiring:
                self.threads_pool.createThread(
                    "camera",
                    self.capture_image,
                    args=("autofocus", "live", *args),
                )
            elif self.acquire_bar_controller.mode == "live":
                self.threads_pool.createThread(
                    "model", lambda: self.model.run_command("autofocus", *args)
                )

        elif command == "eliminate_tiles":
            """Execute eliminate tiles routine."""

            self.acquire_bar_controller.set_mode(mode="customized")
            feature_list = self.menu_controller.feature_list_names
            feature_name = "Remove Empty Tiles"
            try:
                # feature_id_val has a trace, and setting the menu item triggers it.
                feature_id = feature_list.index(feature_name)
                self.menu_controller.feature_id_val.set(feature_id)
            except ValueError:
                logger.debug("No feature named 'Remove Empty Tiles' found.")
                messagebox.showwarning(
                    title="Navigate", message="Feature 'Remove Empty Tiles' not found."
                )
                return
            self.execute("acquire")

        elif command == "load_feature":
            """Tell model to load/unload features."""

            work_thread = self.threads_pool.createThread(
                "model", lambda: self.model.run_command("load_feature", *args)
            )
            work_thread.join()

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

            # Save the experiment.yaml file.
            save_yaml_file(
                file_directory=file_directory,
                content_dict=self.configuration["experiment"],
                filename="experiment.yml",
            )

            # Save the waveform_constants.yaml file.
            save_yaml_file(
                file_directory=file_directory,
                content_dict=self.configuration["waveform_constants"],
                filename="waveform_constants.yml",
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
            # acquisition mode from plugin
            plugin_obj = self.plugin_acquisition_modes.get(
                self.acquire_bar_controller.mode, None
            )

            if plugin_obj and hasattr(plugin_obj, "prepare_acquisition_controller"):
                getattr(plugin_obj, "prepare_acquisition_controller")(self)

            # Prepare data
            if not self.prepare_acquire_data():
                self.acquire_bar_controller.stop_acquire()
                return

            # set the display segmentation flag to False
            self.camera_view_controller.display_mask_flag = False

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

                    # if select 'ilastik segmentation' and 'show segmentation',
                    # TODO: update id if the feature id is changed
                    self.camera_view_controller.display_mask_flag = (
                        self.menu_controller.feature_id_val.get() == 4
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
                self.show_img_pipe.recv()

            self.current_image_id = -1

        elif command == "exit":
            """Exit the program.

            Saves the current GUI settings to .navigate/config/experiment.yml file.
            """
            self.sloppy_stop()
            self.update_experiment_setting()
            file_directory = os.path.join(get_navigate_path(), "config")
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

        # mirror commands:
        elif command in [
            "flatten_mirror",
            "zero_mirror",
            "set_mirror",
            "set_mirror_from_wcs",
        ]:
            self.threads_pool.createThread(
                "model", lambda: self.model.run_command(command, *args)
            )
        elif command == "tony_wilson":
            self.threads_pool.createThread(
                "camera",
                self.capture_image,
                args=(
                    "tony_wilson",
                    "live",
                ),
            )
        else:
            self.threads_pool.createThread(
                "model", lambda: self.model.run_command(command, *args)
            )

        # elif command == "change_camera":
        #     self.model.run_command("change_camera", *args)

        logger.info(
            f"Navigate Controller - command passed from child, {command}, {args}"
        )

    def sloppy_stop(self):
        """Keep trying to stop the model until successful.

        TODO: Delete this function!!!

        This is set up to get around the conflict between
        self.threads_pool.createThread('model', target)
        commands and the need to stop as abruptly as
        possible when the user hits stop. Here we leverage
        ObjectInSubprocess' refusal to let us access
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
            'acquire' or 'autofocus'
        mode : string
            'continuous', 'z-stack', 'single', or 'projection'
        args : function-specific passes.
        """
        self.camera_view_controller.image_count = 0
        self.mip_setting_controller.image_count = 0

        # Start up Progress Bars
        images_received = 0
        self.acquire_bar_controller.progress_bar(
            images_received=images_received,
            microscope_state=self.configuration["experiment"]["MicroscopeState"],
            mode=mode,
            stop=False,
        )
        try:
            work_thread = self.threads_pool.createThread(
                "model", lambda: self.model.run_command(command, *args)
            )
            work_thread.join()
        except Exception as e:
            messagebox.showerror(
                title="Error:",
                message=f"WARNING:\n{e}",
            )
            self.set_mode_of_sub("stop")
            return
        self.acquire_bar_controller.view.acquire_btn.configure(text="Stop")
        self.acquire_bar_controller.view.acquire_btn.configure(state="normal")
        microscope_name = self.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ]

        self.camera_view_controller.initialize_non_live_display(
            self.configuration["experiment"]["MicroscopeState"],
            self.configuration["experiment"]["CameraParameters"][microscope_name],
        )

        self.mip_setting_controller.initialize_non_live_display(
            self.configuration["experiment"]["MicroscopeState"],
            self.configuration["experiment"]["CameraParameters"][microscope_name],
        )

        self.stop_acquisition_flag = False
        start_time = time.time()
        self.camera_setting_controller.update_readout_time()

        while True:
            if self.stop_acquisition_flag:
                break
            # Receive the Image and log it.
            image_id = self.show_img_pipe.recv()
            logger.info(f"Navigate Controller - Received Image: {image_id}")

            if image_id == "stop":
                self.current_image_id = -1
                break

            self.current_image_id = image_id

            if not isinstance(image_id, int):
                logger.debug(
                    f"Navigate Controller - Something wrong happened, stop the model!, "
                    f"{image_id}"
                )
                self.execute("stop_acquire")

            # Display the image and update the histogram
            self.camera_view_controller.try_to_display_image(
                image=self.data_buffer[image_id]
            )
            self.mip_setting_controller.try_to_display_image(
                image=self.data_buffer[image_id]
            )
            self.histogram_controller.populate_histogram(
                image=self.data_buffer[image_id]
            )
            images_received += 1

            # Update progress bar.
            self.acquire_bar_controller.progress_bar(
                images_received=images_received,
                microscope_state=self.configuration["experiment"]["MicroscopeState"],
                mode=mode,
                stop=False,
            )
            # update framerate
            stop_time = time.time()
            try:
                frames_per_second = images_received / (stop_time - start_time)
            except ZeroDivisionError:
                frames_per_second = 1 / (
                    self.configuration["experiment"]["MicroscopeState"]["channels"][
                        "channel_1"
                    ].get("camera_exposure_time", 200)
                    / 1000
                )

            # Update the Framerate in the Camera Settings Tab
            self.camera_setting_controller.framerate_widgets["max_framerate"].set(
                frames_per_second
            )

            # Update the Framerate in the Acquire Bar to provide an estimate of
            # the duration of time remaining.
            self.acquire_bar_controller.framerate = frames_per_second

        logger.info(
            f"Navigate Controller - Captured {images_received}, " f"{mode} Images"
        )

        # acquisition mode from plugin
        plugin_obj = self.plugin_acquisition_modes.get(mode, None)
        if plugin_obj and hasattr(plugin_obj, "end_acquisition_controller"):
            getattr(plugin_obj, "end_acquisition_controller")(self)

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

        def display_images(
            microscope_name, camera_view_controller, show_img_pipe, data_buffer
        ):
            """Display images from additional microscopes.

            Parameters
            ----------
            microscope_name : str
                Microscope name
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
                self.configuration["experiment"]["MicroscopeState"],
                self.configuration["experiment"]["CameraParameters"][microscope_name],
            )
            images_received = 0
            while True:
                if self.stop_acquisition_flag:
                    break
                # Receive the Image and log it.
                image_id = show_img_pipe.recv()
                logger.info(f"Navigate Controller - Received Image: {image_id}")

                if image_id == "stop":
                    break
                if not isinstance(image_id, int):
                    logger.debug(
                        f"Navigate Controller - Something wrong happened in additional "
                        f"microscope!, {image_id}"
                    )
                    break

                # Display the Image in the View
                try:
                    camera_view_controller.try_to_display_image(
                        image=data_buffer[image_id],
                    )
                except tkinter._tkinter.TclError:
                    print("Can't show images for the additional microscope!")
                    break
                images_received += 1

        # destroy all additional microscopes
        for microscope_name in list(self.additional_microscopes.keys()):
            destroy_window = False
            if microscope_name not in self.additional_microscopes_configs:
                destroy_window = True
            self.destroy_virtual_microscope(microscope_name, destroy_window)

        # show additional camera view popup
        for microscope_name in self.additional_microscopes_configs:
            show_img_pipe = self.model.create_pipe(f"{microscope_name}_show_img_pipe")
            data_buffer = self.model.launch_virtual_microscope(
                microscope_name,
                self.additional_microscopes_configs[microscope_name],
            )

            if microscope_name not in self.additional_microscopes:
                self.additional_microscopes[microscope_name] = {}

                popup_window = CameraViewPopupWindow(self.view, microscope_name)
                camera_view_controller = CameraViewController(
                    popup_window.camera_view, self
                )
                camera_view_controller.microscope_name = microscope_name
                popup_window.popup.bind("<Configure>", camera_view_controller.resize)
                self.additional_microscopes[microscope_name][
                    "popup_window"
                ] = popup_window
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

            self.additional_microscopes[microscope_name][
                "show_img_pipe"
            ] = show_img_pipe
            self.additional_microscopes[microscope_name]["data_buffer"] = data_buffer

            # start thread
            capture_img_thread = threading.Thread(
                target=display_images,
                args=(
                    microscope_name,
                    self.additional_microscopes[microscope_name][
                        "camera_view_controller"
                    ],
                    show_img_pipe,
                    self.additional_microscopes[microscope_name]["data_buffer"],
                ),
            )
            capture_img_thread.start()

    def destroy_virtual_microscope(self, microscope_name, destroy_window=True):
        """Destroy virtual microscopes.

        Parameters
        ----------
        microscope_name : str
            The microscope name
        destroy_window : bool
            The flag to dismiss window.
        """
        if microscope_name not in self.additional_microscopes:
            return
        del self.additional_microscopes[microscope_name]["data_buffer"]
        self.model.destroy_virtual_microscope(microscope_name)
        # release pipe
        self.model.release_pipe(f"{microscope_name}_show_img_pipe")
        del self.additional_microscopes[microscope_name]["show_img_pipe"]
        # destroy the popup window
        if destroy_window:
            self.additional_microscopes[microscope_name]["popup_window"].popup.dismiss()
            self.additional_microscopes[microscope_name][
                "camera_view_controller"
            ] = None
            del self.additional_microscopes[microscope_name]

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
                messagebox.showwarning(title="Navigate", message=value)

            elif event == "multiposition":
                # Update the multi-position tab without appending to the list
                update_table(
                    table=self.multiposition_tab_controller.table,
                    pos=value,
                )
                self.channels_tab_controller.is_multiposition_val.set(True)

            elif event == "stop":
                # Stop the software
                break

            elif event == "update_stage":
                for _ in range(10):
                    try:
                        self.update_stage_controller_silent(value)
                        break
                    except RuntimeError:
                        time.sleep(0.001)
                        pass

            elif event in self.event_listeners.keys():
                try:
                    self.event_listeners[event](value)
                except Exception:
                    print(f"*** unhandled event: {event}, {value}")

    def add_acquisition_mode(self, name, acquisition_obj):
        """Add and Acquisition Mode.

        Parameters
        ----------
        name : string
            Name of the acquisition mode.
        acquisition_obj : object
            Object of the acquisition mode.
        """
        if name in self.plugin_acquisition_modes:
            print(f"*** plugin acquisition mode {name} exists, can't add another one!")
            return
        self.plugin_acquisition_modes[name] = acquisition_obj(name)
        self.acquire_bar_controller.add_mode(name)

    def register_event_listener(self, event_name, event_handler):
        """Register an event listener.

        Parameters
        ----------
        event_name : string
            Name of the event.
        event_handler : function
            Function to handle the event.
        """
        self.event_listeners[event_name] = event_handler

    def register_event_listeners(self, events):
        """Register multiple event listeners.

        Parameters
        ----------
        events : dict
            Dictionary of event names and handlers.
        """
        for event_name, event_handler in events.items():
            self.register_event_listener(event_name, event_handler)
