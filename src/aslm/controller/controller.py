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
from tkinter import filedialog, messagebox
import multiprocessing as mp
import threading
import sys

# Third Party Imports

# Local View Imports
from aslm.view.main_application_window import MainApp as view
from aslm.view.menus.waveform_parameter_popup_window import WaveformParameterPopupWindow
from aslm.view.menus.camera_view_popup_window import CameraViewPopupWindow
from aslm.view.menus.autofocus_setting_popup import AutofocusPopup
from aslm.view.menus.ilastik_setting_popup import ilastik_setting_popup
from aslm.view.menus.help_popup import HelpPopup
from aslm.view.menus.camera_map_setting_popup import CameraMapSettingPopup

# Local Sub-Controller Imports
from aslm.controller.sub_controllers.help_popup_controller import HelpPopupController
from aslm.controller.configuration_controller import ConfigurationController
from aslm.controller.sub_controllers import (
    IlastikPopupController,
    CameraMapSettingPopupController,
    AutofocusPopupController,
    WaveformPopupController,
    KeystrokeController,
    WaveformTabController,
    StageController,
    CameraSettingController,
    CameraViewController,
    MultiPositionController,
    ChannelsTabController,
    AcquireBarController,
    MicroscopePopupController,
)
from aslm.controller.thread_pool import SynchronizedThreadPool

# Local Model Imports
from aslm.model.model import Model
from aslm.model.concurrency.concurrency_tools import ObjectInSubprocess

# Misc. Local Imports
from aslm.config.config import load_configs, update_config_dict
from aslm.tools.file_functions import create_save_path, save_yaml_file
from aslm.tools.common_dict_tools import update_stage_dict
from aslm.tools.multipos_table_tools import update_table
from aslm.tools.common_functions import combine_funcs

# Logger Setup
import logging

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Controller:
    """ASLM Controller

    Parameters
    ----------
    root : Tk top-level widget.
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
    use_gpu : Boolean
        Flag for utilizing CUDA functionality.
    *args :
        Command line input arguments for non-default
        file paths or using synthetic hardware modes.
    """

    def __init__(
        self,
        root,
        splash_screen,
        configuration_path,
        experiment_path,
        waveform_constants_path,
        rest_api_path,
        use_gpu,
        args,
    ):

        # Create a thread pool
        self.threads_pool = SynchronizedThreadPool()
        self.event_queue = mp.Queue(
            100
        )  # pass events from the model to the view via controller
        # accepts tuples, ('event_name', value)

        # Create a shared memory manager
        self.manager = Manager()
        self.configuration = load_configs(
            self.manager,
            configuration=configuration_path,
            experiment=experiment_path,
            waveform_constants=waveform_constants_path,
            rest_api_config=rest_api_path,
        )

        # Initialize the Model
        self.model = ObjectInSubprocess(
            Model, use_gpu, args, self.configuration, event_queue=self.event_queue
        )

        logger.info(f"Spec - Configuration Path: {configuration_path}")
        logger.info(f"Spec - Experiment Path: {experiment_path}")
        logger.info(f"Spec - Waveform Constants Path: {waveform_constants_path}")
        logger.info(f"Spec - Rest API Path: {rest_api_path}")

        # Wire up pipes
        self.show_img_pipe = self.model.create_pipe("show_img_pipe")

        # save default experiment file
        self.default_experiment_file = experiment_path

        # waveform setting file
        self.waveform_constants_path = waveform_constants_path

        # Configuration Reader
        self.configuration_controller = ConfigurationController(self.configuration)

        # Initialize the View
        self.view = view(root)
        self.view.root.protocol("WM_DELETE_WINDOW", self.exit_program)

        # Sub Gui Controllers
        # Acquire bar, channels controller,
        # camera view, camera settings,
        # stage, waveforms, menus.
        self.acquire_bar_controller = AcquireBarController(
            self.view.acqbar, self.view.settings.channels_tab, self
        )

        self.channels_tab_controller = ChannelsTabController(
            self.view.settings.channels_tab, self
        )

        self.multiposition_tab_controller = MultiPositionController(
            self.view.settings.multiposition_tab.multipoint_list, self
        )

        self.camera_view_controller = CameraViewController(
            self.view.camera_waveform.camera_tab, self
        )

        self.camera_setting_controller = CameraSettingController(
            self.view.settings.camera_settings_tab, self
        )

        # Stage Controller
        self.stage_controller = StageController(
            self.view.settings.stage_control_tab,
            self.view,
            self.camera_view_controller.canvas,
            self,
        )

        # Waveform Controller
        self.waveform_tab_controller = WaveformTabController(
            self.view.camera_waveform.waveform_tab, self
        )

        # Keystroke Controller
        self.keystroke_controller = KeystrokeController(self.view, self)

        # Bonus config
        self.update_acquire_control()

        t = threading.Thread(target=self.update_event)
        t.start()

        # self.microscope = self.configuration['configuration']
        # ['microscopes'].keys()[0]  # Default to the first microscope

        self.initialize_menus(args.synthetic_hardware)

        # Create default data buffer
        self.img_width = 0
        self.img_height = 0
        self.data_buffer = None
        self.additional_microscopes = {}
        self.additional_microscopes_configs = {}

        # Set view based on model.experiment
        self.populate_experiment_setting(in_initialize=True)

        # Camera View Tab
        self.initialize_cam_view()

        # destroy splash screen and show main screen
        splash_screen.destroy()
        root.deiconify()

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
            self.configuration["experiment"]["CameraParameters"]["x_pixels"]
        )
        img_height = int(
            self.configuration["experiment"]["CameraParameters"]["y_pixels"]
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

    def initialize_cam_view(self):
        """Populate view tab.

        Populate widgets with necessary data from
        config file via config controller. For the entire view tab.
        Sets the minimum and maximum counts
        for when the data is not being autoscaled.

        Returns
        -------
        None
        """
        # Populating Min and Max Counts
        minmax_values = [0, 2**16 - 1]
        self.camera_view_controller.initialize("minmax", minmax_values)
        image_metrics = [1, 0, 0]
        self.camera_view_controller.initialize("image", image_metrics)

    def initialize_menus(self, is_synthetic_hardware=False):
        """Initialize menus
        This function defines all the menus in the menubar

        Parameters
        ----------
        is_synthetic_hardware : bool
            If True, then the hardware is simulated.
            If False, then the hardware is real.

        Returns
        -------
        configuration_controller : class
            Camera view sub-controller.

        """

        def new_experiment():
            """Create a new experiment file."""
            self.populate_experiment_setting(self.default_experiment_file)

        def load_experiment():
            """Load an experiment file."""
            filename = filedialog.askopenfilename(
                defaultextension=".yml", filetypes=[("Yaml files", "*.yml *.yaml")]
            )
            if not filename:
                return
            self.populate_experiment_setting(filename)

        def save_experiment():
            """Save an experiment file.

            Updates model.experiment and saves it to file.
            """
            if not self.update_experiment_setting():
                tkinter.messagebox.showerror(
                    title="Warning",
                    message="Incorrect/missing settings. "
                    "Cannot save current experiment file.",
                )
                return
            filename = filedialog.asksaveasfilename(
                defaultextension=".yml", filetypes=[("Yaml file", "*.yml *.yaml")]
            )
            if not filename:
                return
            save_yaml_file("", self.configuration["experiment"], filename)

        def load_images():
            """Load images from a file."""
            filenames = filedialog.askopenfilenames(
                defaultextension=".tif", filetypes=[("tiff files", "*.tif *.tiff")]
            )
            if not filenames:
                return
            self.model.load_images(filenames)

        def popup_waveform_setting():
            if hasattr(self, "waveform_popup_controller"):
                self.waveform_popup_controller.showup()
                return
            waveform_constants_popup = WaveformParameterPopupWindow(
                self.view, self.configuration_controller
            )
            self.waveform_popup_controller = WaveformPopupController(
                waveform_constants_popup, self, self.waveform_constants_path
            )

            self.waveform_popup_controller.populate_experiment_values()

        def popup_microscope_setting():
            """Pop up the microscope setting window.

            Parameters
            ----------
            None

            Returns
            -------
            None
            """
            if hasattr(self, "microscope_popup_controller"):
                self.microscope_popup_controller.showup()
                return
            microscope_info = self.model.get_microscope_info()
            self.microscope_popup_controller = MicroscopePopupController(
                self.view, self, microscope_info
            )

        def popup_autofocus_setting():
            """Pop up the Autofocus setting window."""
            if hasattr(self, "af_popup_controller"):
                self.af_popup_controller.showup()
                return
            af_popup = AutofocusPopup(self.view)
            self.af_popup_controller = AutofocusPopupController(af_popup, self)

        def popup_camera_map_setting():
            """Pop up the Camera Map setting window."""
            if hasattr(self, "camera_map_popup_controller"):
                self.camera_map_popup_controller.showup()
                return
            map_popup = CameraMapSettingPopup(self.view)
            self.camera_map_popup_controller = CameraMapSettingPopupController(
                map_popup, self
            )

        def popup_ilastik_setting():
            """Pop up the Ilastik setting window."""
            ilastik_popup_window = ilastik_setting_popup(self.view)
            ilastik_url = self.configuration["rest_api_config"]["Ilastik"]["url"]
            if hasattr(self, "ilastik_controller"):
                self.ilastik_controller.showup(ilastik_popup_window)
            else:
                self.ilastik_controller = IlastikPopupController(
                    ilastik_popup_window, self, ilastik_url
                )

        def popup_help():
            """Pop up the help window."""
            if hasattr(self, "help_controller"):
                self.help_controller.showup()
                return
            help_pop = HelpPopup(self.view)
            self.help_controller = HelpPopupController(help_pop, self)

        menus_dict = {
            self.view.menubar.menu_file: {
                "New Experiment": new_experiment,
                "Load Experiment": load_experiment,
                "Save Experiment": save_experiment,
            },
            self.view.menubar.menu_multi_positions: {
                "Load Positions": (self.multiposition_tab_controller.load_positions),
                "Export Positions": (
                    self.multiposition_tab_controller.export_positions
                ),
                "Append Current Position": (
                    self.multiposition_tab_controller.add_stage_position
                ),
                "Generate Positions": (
                    self.multiposition_tab_controller.generate_positions
                ),
                "Move to Selected Position": (
                    self.multiposition_tab_controller.move_to_position
                ),
                # 'Sort Positions': ,
            },
        }
        for menu in menus_dict:
            menu_items = menus_dict[menu]
            for label in menu_items:
                menu.add_command(label=label, command=menu_items[label])

        # load images from disk in synthetic hardware
        if is_synthetic_hardware:
            self.view.menubar.menu_file.add_separator()
            self.view.menubar.menu_file.add_command(
                label="Load Images", command=load_images
            )
            self.view.menubar.menu_file.add_command(
                label="Unload Images", command=lambda: self.model.load_images(None)
            )

        # add resolution menu
        self.resolution_value = tkinter.StringVar()
        for microscope_name in self.configuration["configuration"][
            "microscopes"
        ].keys():
            zoom_positions = self.configuration["configuration"]["microscopes"][
                microscope_name
            ]["zoom"]["position"]
            if len(zoom_positions) > 1:
                sub_menu = tkinter.Menu(self.view.menubar.menu_resolution)
                self.view.menubar.menu_resolution.add_cascade(
                    menu=sub_menu, label=microscope_name
                )
                for res in zoom_positions.keys():
                    sub_menu.add_radiobutton(
                        label=res,
                        variable=self.resolution_value,
                        value=f"{microscope_name} {res}",
                    )
            else:
                self.view.menubar.menu_resolution.add_radiobutton(
                    label=microscope_name,
                    variable=self.resolution_value,
                    value=f"{microscope_name} {zoom_positions.keys()[0]}",
                )

        # event binding
        self.resolution_value.trace_add(
            "write",
            lambda *args: self.execute("resolution", self.resolution_value.get()),
        )

        # add separator
        self.view.menubar.menu_resolution.add_separator()

        # waveform popup
        self.view.menubar.menu_resolution.add_command(
            label="Waveform Parameters", command=popup_waveform_setting
        )
        # microscope setting popup
        self.view.menubar.menu_resolution.add_command(
            label="Configure Microscopes", command=popup_microscope_setting
        )

        # autofocus menu
        self.view.menubar.menu_autofocus.add_command(
            label="Autofocus", command=lambda: self.execute("autofocus")
        )
        self.view.menubar.menu_autofocus.add_command(
            label="setting", command=popup_autofocus_setting
        )

        # Help menu
        self.view.menubar.menu_help.add_command(label="Help", command=popup_help)

        # add-on features
        feature_list = [
            "None",
            "Switch Resolution",
            "Z Stack Acquisition",
            "Threshold",
            "Ilastik Segmentation",
            "Volume Search",
            "Time Series",
        ]
        self.feature_id_val = tkinter.IntVar(0)
        for i in range(len(feature_list)):
            self.view.menubar.menu_features.add_radiobutton(
                label=feature_list[i], variable=self.feature_id_val, value=i
            )
        self.feature_id_val.trace_add(
            "write",
            lambda *args: self.execute("load_feature", self.feature_id_val.get()),
        )
        self.view.menubar.menu_features.add_separator()
        self.view.menubar.menu_features.add_command(
            label="ilastik setting", command=popup_ilastik_setting
        )
        # disable ilastik menu
        self.view.menubar.menu_features.entryconfig(
            "Ilastik Segmentation", state="disabled"
        )
        self.view.menubar.menu_features.add_command(
            label="Camera offset and variance maps", command=popup_camera_map_setting
        )

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
        update_config_dict(self.manager, self.configuration, "experiment", file_name)

        # update buffer
        self.update_buffer()

        # Configure GUI
        microscope_name = self.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ]
        self.resolution_value.set(
            f"{microscope_name} "
            f"{self.configuration['experiment']['MicroscopeState']['zoom']}"
        )

        if in_initialize:
            # Force stage update (should have happened in self.resolution_value.set())
            ret_pos_dict = self.model.get_stage_position()
            update_stage_dict(self, ret_pos_dict)

        self.acquire_bar_controller.populate_experiment_values()
        self.stage_controller.populate_experiment_values()
        self.multiposition_tab_controller.set_positions(
            self.configuration["experiment"]["MultiPositions"]["stage_positions"]
        )
        self.channels_tab_controller.populate_experiment_values()
        self.camera_setting_controller.populate_experiment_values()

        # set widget modes
        self.set_mode_of_sub("stop")

    def update_experiment_setting(self):
        """Update model.experiment according to values in the GUI

        Collect settings from sub-controllers
        sub-controllers will validate the value, if something is wrong, it will
        return False

        """
        # acquire_bar_controller - update image mode
        self.configuration["experiment"]["MicroscopeState"][
            "image_mode"
        ] = self.acquire_bar_controller.get_mode()
        self.camera_setting_controller.update_experiment_values()

        # TODO: validate experiment dict
        return True

    def prepare_acquire_data(self):
        """Prepare the acquisition data.

        Updates model.experiment.
        Sets sub-controller's mode to 'live' when 'continuous is selected, or 'stop'.
        """
        if not self.update_experiment_setting():
            tkinter.messagebox.showerror(
                title="Warning",
                message="There are some missing/wrong settings! "
                "Cannot start acquisition!",
            )
            return False
        # update multi-positions
        positions = self.multiposition_tab_controller.get_positions()
        update_config_dict(
            self.manager,
            self.configuration["experiment"]["MultiPositions"],
            "stage_positions",
            positions,
        )

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
        if mode == "stop":
            # GUI Failsafe
            self.acquire_bar_controller.stop_acquire()
            self.feature_id_val.set(0)

    def execute(self, command, *args):
        """Functions listens to the Sub_Gui_Controllers.

        The controller.experiment is passed as
        an argument to the model, which then overwrites
        the model.experiment.
        Workaround due to model being in a sub-process.

        Parameters
        __________
        args* : function-specific passes.
        """
        if command == "stage":
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
            microscope_name, zoom = self.resolution_value.get().split()
            if (
                microscope_name
                != self.configuration["experiment"]["MicroscopeState"][
                    "microscope_name"
                ]
            ):
                self.change_microscope(microscope_name)
            self.configuration["experiment"]["MicroscopeState"]["zoom"] = zoom
            work_thread = self.threads_pool.createThread(
                "model", lambda: self.model.run_command("update_setting", "resolution")
            )
            work_thread.join()
            self.camera_setting_controller.calculate_physical_dimensions()
            if (
                hasattr(self, "waveform_popup_controller")
                and self.waveform_popup_controller
            ):
                self.waveform_popup_controller.populate_experiment_values()
            ret_pos_dict = self.model.get_stage_position()
            update_stage_dict(self, ret_pos_dict)
            self.update_stage_controller_silent(ret_pos_dict)
            self.camera_view_controller.update_snr()

        elif command == "set_save":
            """Set whether the image will be saved.

            Parameters
            __________
            args : Boolean
                is_save = True/False
            """
            self.acquire_bar_controller.set_save_option(args[0])

        elif command == "update_setting":
            r"""Called by the Waveform Constants Popup Controller
            to update the Waveform constants settings in memory.

            Parameters
            __________
            args[0] : string
                string = 'resolution'
            args[1] : dict
                dict = {
                'resolution_mode': self.resolution,
                'zoom': self.mag,
                'laser_info': self.resolution_info[
                'remote_focus_constants'][self.resolution][self.mag
                ]
                }
            """
            # update_settings_common(self, args)
            self.threads_pool.createThread(
                "model", lambda: self.model.run_command("update_setting", *args)
            )

        elif command == "autofocus":
            """Execute autofocus routine."""
            self.threads_pool.createThread(
                "camera",
                self.capture_image,
                args=(
                    "autofocus",
                    "live",
                ),
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

            # if select 'ilastik segmentation',
            # 'show segmentation',
            # and in 'single acquisition'
            self.camera_view_controller.display_mask_flag = (
                self.acquire_bar_controller.mode == "single"
                and self.feature_id_val.get() == 4
                and self.ilastik_controller.show_segmentation_flag
            )

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

            # self.model.run_command('stop')
            self.sloppy_stop()
            self.set_mode_of_sub("stop")
            self.acquire_bar_controller.stop_progress_bar()
            self.acquire_bar_controller.view.acquire_btn.configure(state="normal")

        elif command == "exit":
            """Exit the program."""

            # self.model.run_command('stop')
            self.sloppy_stop()
            if hasattr(self, "waveform_popup_controller"):
                self.waveform_popup_controller.save_waveform_constants()
            self.model.terminate()
            self.model = None
            self.event_queue.put(("stop", ""))
            # self.threads_pool.clear()

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

    def capture_image(self, command, mode):
        """Trigger the model to capture images.

        Parameters
        ----------
        command : string
            string = 'acquire' or 'autofocus'
        mode : string
            string = 'continuous', 'z-stack', 'single', or 'projection'
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

        self.model.run_command(command)
        self.acquire_bar_controller.view.acquire_btn.configure(state="normal")

        self.camera_view_controller.initialize_non_live_display(
            self.data_buffer,
            self.configuration["experiment"]["MicroscopeState"],
            self.configuration["experiment"]["CameraParameters"],
        )

        while True:
            # Receive the Image and log it.
            image_id = self.show_img_pipe.recv()
            logger.info(f"ASLM Controller - Received Image: {image_id}")

            if image_id == "stop":
                self.set_mode_of_sub("stop")
                break
            if not isinstance(image_id, int):
                logger.debug(
                    f"ASLM Controller - Something wrong happened, stop the model!, "
                    f"{image_id}"
                )
                self.execute("stop_acquire")

            # Display the Image in the View
            self.camera_view_controller.display_image(
                image=self.data_buffer[image_id],
                microscope_state=self.configuration["experiment"]["MicroscopeState"],
                images_received=images_received,
            )
            images_received += 1

            # Update progress bar.
            self.acquire_bar_controller.progress_bar(
                images_received=images_received,
                microscope_state=self.configuration["experiment"]["MicroscopeState"],
                mode=mode,
                stop=False,
            )

        logger.info(
            f"ASLM Controller - Captured {self.camera_view_controller.image_count}, "
            f"{mode} Images"
        )
        self.set_mode_of_sub("stop")

        # Stop Progress Bars
        self.acquire_bar_controller.progress_bar(
            images_received=images_received,
            microscope_state=self.configuration["experiment"]["MicroscopeState"],
            mode=mode,
            stop=True,
        )

    def launch_additional_microscopes(self):
        def display_images(camera_view_controller, show_img_pipe, data_buffer):
            images_received = 0
            while True:
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
                    camera_view_controller.display_image(
                        image=data_buffer[image_id],
                        microscope_state=self.configuration["experiment"][
                            "MicroscopeState"
                        ],
                        images_received=images_received,
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

            # start thread
            capture_img_thread = threading.Thread(
                target=display_images,
                args=(
                    self.additional_microscopes[microscope_name][
                        "camera_view_controller"
                    ],
                    self.additional_microscopes[microscope_name]["show_img_pipe"],
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
        ret_pos_dict = self.model.get_stage_position()
        update_stage_dict(self, ret_pos_dict)
        self.update_stage_controller_silent(ret_pos_dict)

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
        """Update the waveforms in the View."""
        while True:
            event, value = self.event_queue.get()
            if event == "waveform":
                self.waveform_tab_controller.update_waveforms(
                    value, self.configuration_controller.daq_sample_rate
                )
            elif event == "multiposition":
                # Updates the multi-position tab without appending to the list
                update_table(
                    self.view.settings.multiposition_tab.multipoint_list.get_table(),
                    value,
                )
                self.view.settings.channels_tab.multipoint_frame.on_off.set(True)
            elif event == "ilastik_mask":
                self.camera_view_controller.display_mask(value)

            elif event == "autofocus":
                if hasattr(self, "af_popup_controller"):
                    self.af_popup_controller.display_plot(value)

            elif event == "stop":
                break

            elif event == "update_stage":
                self.update_stage_controller_silent(value)

            elif event == "framerate":
                self.camera_setting_controller.framerate_widgets["max_framerate"].set(
                    value
                )
                # (value)

    def exit_program(self):
        """Exit the program.

        This function is called when the user clicks the exit button in the GUI.
        """
        if messagebox.askyesno("Exit", "Are you sure?"):
            logger.info("Exiting Program")
            self.execute("exit")
            sys.exit()
