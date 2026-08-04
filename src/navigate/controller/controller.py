# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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
from __future__ import annotations
from multiprocessing import Manager
import tkinter
from tkinter import messagebox
import multiprocessing as mp
import threading
import queue
import sys
import os
import time
from typing import Any, Callable, TypeVar

# Third Party Imports

# Local View Imports
from navigate.view.main_application_window import MainApp as view
from navigate.view.popups.camera_view_popup_window import CameraViewPopupWindow
from navigate.view.popups.feature_list_popup import FeatureListPopup
from navigate.view.theme import apply_theme

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
)

from navigate.controller.thread_pool import SynchronizedThreadPool

# Local Model Imports
from navigate.model.model import Model, ASIModel
from navigate.model.concurrency.concurrency_tools import ObjectInSubprocess

# Misc. Local Imports
from navigate._commit import get_git_revision_hash, get_version_from_file
from navigate.config.config import (
    load_configs,
    update_config_dict,
    verify_experiment_config,
    verify_waveform_constants,
    verify_positions_config,
    verify_configuration,
    get_navigate_path,
)
from navigate.tools.file_functions import (
    load_yaml_file,
    save_yaml_file,
    get_ram_info,
)
from navigate.tools.common_dict_tools import update_stage_dict
from navigate.tools.multipos_table_tools import update_table
from navigate.tools.common_functions import combine_funcs
from navigate.tools.tk_thread_guard import install_tk_thread_guard

# Logger Setup
import logging

p = __name__.split(".")[1]
logger = logging.getLogger(p)

_T = TypeVar("_T")


class Controller:
    """Navigate Controller"""

    def __init__(
        self,
        root: tkinter.Tk,
        splash_screen: tkinter.Toplevel,
        configuration_path: str | os.PathLike[str],
        experiment_path: str | os.PathLike[str],
        waveform_constants_path: str | os.PathLike[str],
        rest_api_path: str | os.PathLike[str],
        waveform_templates_path: str | os.PathLike[str],
        gui_configuration_path: str | os.PathLike[str],
        multi_positions_path: str | os.PathLike[str],
        log_queue: mp.Queue | None,
        args: Any,
    ) -> None:
        """Initialize the Navigate Controller.

        Parameters
        ----------
        root : tkinter.Tk
            Tk root window.
        splash_screen : tkinter.Toplevel
            Splash window shown before the main window is initialized.
        configuration_path : str | os.PathLike[str]
            Path to the global configuration YAML file.
        experiment_path : str | os.PathLike[str]
            Path to the experiment YAML file.
        waveform_constants_path : str | os.PathLike[str]
            Path to the waveform constants YAML file.
        rest_api_path : str | os.PathLike[str]
            Path to the REST API configuration YAML file.
        waveform_templates_path : str | os.PathLike[str]
            Path to the waveform templates YAML file.
        gui_configuration_path : str | os.PathLike[str]
            Path to the GUI configuration YAML file.
        multi_positions_path : str | os.PathLike[str]
            Path to the multi-position YAML file.
        log_queue : multiprocessing.Queue | None
            Queue used for cross-process logging.
        args : Any
            Command-line arguments used for runtime options.

        Returns
        -------
        None
        """
        logger.info(f"Navigate GIT Hash: {get_git_revision_hash()}")
        logger.info(f"Navigate Version: {get_version_from_file()}")

        #: Tk top-level widget: Tk.tk GUI instance.
        self.root = root

        # Install thread guard to catch improper Tk calls from non-main threads
        install_tk_thread_guard(self.root, logger)

        #: bool: Flag to indicate if the GUI is ready for resizing.
        self.resize_ready_flag = False

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

        positions = load_yaml_file(multi_positions_path)
        positions = verify_positions_config(positions)
        self.configuration["multi_positions"] = positions

        total_ram, available_ram = get_ram_info()
        logger.info(
            f"Total RAM: {total_ram / 1024**3:.2f} GB. "
            f"Available RAM: {available_ram / 1024**3:.2f} GB."
        )

        #: ObjectInSubprocess: Model object in MVC architecture.
        if self.use_asi_model():
            logger.info("Using ASI model.")
            self.model = ObjectInSubprocess(
                ASIModel,
                args,
                self.configuration,
                event_queue=self.event_queue,
                log_queue=log_queue,
            )
        else:
            self.model = ObjectInSubprocess(
                Model,
                args,
                self.configuration,
                event_queue=self.event_queue,
                log_queue=log_queue,
            )

        #: mp.Pipe: Pipe for sending images from model to view.
        self.show_img_pipe = self.model.create_pipe("show_img_pipe")

        #: string: Path to the default experiment yaml file.
        self.default_experiment_file = self.experiment_path

        #: string: Path to the waveform constants yaml file.
        self.waveform_constants_path = waveform_constants_path

        #: ConfigurationController: Configuration Controller object.
        self.configuration_controller = ConfigurationController(self.configuration)

        # Apply global GUI theme before creating any view widgets.
        try:
            apply_theme(self.root, self.configuration.get("gui", {}))
        except Exception:
            logger.exception("Failed to apply GUI theme. Continuing with defaults.")

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

        #: bool: Whether the Tk main-loop event pump is running.
        self._event_pump_running = True

        #: Optional[str]: Tk after callback id for the event pump.
        self._event_pump_after_id = None

        #: queue.Queue: cross-thread call queue to execute work on Tk thread.
        self._main_thread_dispatch_queue = queue.Queue()
        self._schedule_event_pump()

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

        #: bool: Whether an autofocus routine is currently active.
        self.is_autofocusing = False

        #: str: Acquisition lifecycle state shown by the autofocus popup.
        self.autofocus_acquisition_state = "idle"

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
        self.window_width = 0
        self.window_height = 0
        self.view.root.after(5000, self.enable_resize)
        self.view.root.bind("<Configure>", self.resize)

    def use_asi_model(self) -> bool:
        """Check if the model uses ASI hardware.

        Returns
        -------
        bool
            True if the model uses ASI hardware, False if it uses NI hardware.

        Raises
        -------
        ValueError
            If the DAQ type is unknown.
        """
        microscope_name = self.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ]
        daq_type = self.configuration["configuration"]["microscopes"][microscope_name][
            "daq"
        ]["hardware"].get("type", "NI")
        daq_type = daq_type.lower()

        if daq_type in ("ni", "synthetic"):
            return False
        elif daq_type == "asi":
            return True
        else:
            raise ValueError(f"Unknown daq type: {daq_type}")

    def update_buffer(self) -> None:
        """Update the shared image buffer for the active camera geometry.

        Returns
        -------
        None
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

        if self.data_buffer is not None:
            for i in range(len(self.data_buffer)):
                self.data_buffer[i].shared_memory.close()
        self.data_buffer = self.model.get_data_buffer(img_width, img_height)
        self.img_width = img_width
        self.img_height = img_height

    def update_acquire_control(self) -> None:
        """Bind Acquire Bar controls to the current stage control handlers.

        Returns
        -------
        None
        """
        self.view.acquire_bar.stop_stage.config(
            command=self.stage_controller.stop_button_handler
        )

    def _run_on_main_thread(
        self, func: Callable[..., _T], *args: Any, wait: bool = False, **kwargs: Any
    ) -> _T | None:
        """Run a callable on the Tk main thread.

        Parameters
        ----------
        func : Callable[..., _T]
            Callable to execute on the Tk main thread.
        *args : Any
            Positional arguments passed to ``func``.
        wait : bool, optional
            If ``True``, block until ``func`` completes and return its result.
            If ``False``, enqueue the call and return immediately.
        **kwargs : Any
            Keyword arguments passed to ``func``.

        Returns
        -------
        _T | None
            Result from ``func`` when executed synchronously, otherwise ``None``.

        Raises
        ------
        RuntimeError
            Raised when synchronous execution is requested but the Tk dispatcher
            is unavailable.
        Exception
            Re-raises exceptions thrown by ``func`` during synchronous execution.
        """
        if threading.current_thread() is threading.main_thread():
            return func(*args, **kwargs)

        if not self._event_pump_running:
            message = "Tk main-thread dispatcher is not running."
            if wait:
                raise RuntimeError(message)
            logger.debug(message)
            return None

        done_event = threading.Event() if wait else None
        result = {"value": None, "error": None}
        self._main_thread_dispatch_queue.put((func, args, kwargs, done_event, result))

        if not wait:
            return None

        while not done_event.wait(timeout=0.1):
            if not self._event_pump_running:
                raise RuntimeError(
                    "Tk main-thread dispatcher stopped before callback ran."
                )
        if result["error"] is not None:
            raise result["error"]
        return result["value"]

    def _drain_main_thread_dispatch_queue(self) -> None:
        """Execute queued cross-thread callbacks on the Tk main thread.

        Returns
        -------
        None
        """
        while True:
            try:
                (
                    func,
                    args,
                    kwargs,
                    done_event,
                    result,
                ) = self._main_thread_dispatch_queue.get_nowait()
            except queue.Empty:
                return

            try:
                result["value"] = func(*args, **kwargs)
            except Exception as exc:
                result["error"] = exc
            finally:
                if done_event:
                    done_event.set()

    def _schedule_event_pump(self) -> None:
        """Schedule the next Tk event-pump iteration.

        Returns
        -------
        None
        """
        if not self._event_pump_running:
            return
        self._drain_main_thread_dispatch_queue()
        self.update_event()
        if self._event_pump_running:
            self._event_pump_after_id = self.view.root.after(
                20, self._schedule_event_pump
            )

    def _stop_event_pump(self) -> None:
        """Stop the Tk event queue polling loop.

        Returns
        -------
        None
        """
        self._event_pump_running = False
        self._drain_main_thread_dispatch_queue()
        if self._event_pump_after_id:
            try:
                self.view.root.after_cancel(self._event_pump_after_id)
            except Exception:
                pass
            self._event_pump_after_id = None

    def _start_capture_ui(self, mode: str) -> None:
        """Initialize capture-related widgets on the Tk thread.

        Parameters
        ----------
        mode : str
            Active acquisition mode.

        Returns
        -------
        None
        """
        self.camera_view_controller.image_count = 0
        self.mip_setting_controller.image_count = 0
        self.acquire_bar_controller.progress_bar(
            images_received=0,
            microscope_state=self.configuration["experiment"]["MicroscopeState"],
            mode=mode,
            stop=False,
        )

    def _set_autofocus_acquisition_state(self, state: str) -> None:
        """Synchronize an open autofocus popup with acquisition state."""
        self.autofocus_acquisition_state = state
        if hasattr(self, "af_popup_controller"):
            self.af_popup_controller.set_acquisition_state(state)

    def _set_autofocus_state(self, is_active: bool) -> None:
        """Synchronize an open autofocus popup with autofocus activity."""
        self.is_autofocusing = is_active
        if hasattr(self, "af_popup_controller"):
            self.af_popup_controller.set_autofocus_state(is_active)

    def _handle_capture_start_error(self, error: Exception) -> None:
        """Display capture startup errors on the Tk thread.

        Parameters
        ----------
        error : Exception
            Exception raised while starting capture.

        Returns
        -------
        None
        """
        messagebox.showerror(
            title="Error:",
            message=f"WARNING:\n{error}",
        )
        self.set_mode_of_sub("stop")
        self._set_autofocus_acquisition_state("idle")
        self._set_autofocus_state(False)

    def _on_capture_started(self, microscope_name: str) -> None:
        """Apply post-start capture UI updates on the Tk thread.

        Parameters
        ----------
        microscope_name : str
            Active microscope name for camera parameter lookup.

        Returns
        -------
        None
        """
        self.acquire_bar_controller.view.acquire_btn.configure(text="Stop")
        self.acquire_bar_controller.view.acquire_btn.configure(state="normal")
        self._set_autofocus_acquisition_state("running")
        self.camera_view_controller.initialize_non_live_display(
            self.configuration["experiment"]["MicroscopeState"],
            self.configuration["experiment"]["CameraParameters"][microscope_name],
        )
        self.mip_setting_controller.initialize_non_live_display(
            self.configuration["experiment"]["MicroscopeState"],
            self.configuration["experiment"]["CameraParameters"][microscope_name],
        )
        self.camera_setting_controller.update_readout_time()

    def _update_capture_display(
        self, image_id: int, mode: str, images_received: int
    ) -> None:
        """Display a captured frame and update related capture widgets.

        Parameters
        ----------
        image_id : int
            Index into ``self.data_buffer`` for the image to display.
        mode : str
            Active acquisition mode.
        images_received : int
            Number of frames processed so far.

        Returns
        -------
        None
        """
        image = self.data_buffer[image_id]
        self.camera_view_controller.try_to_display_image(image=image)
        self.mip_setting_controller.try_to_display_image(image=image)
        self.histogram_controller.populate_histogram(image=image)
        self.acquire_bar_controller.progress_bar(
            images_received=images_received,
            microscope_state=self.configuration["experiment"]["MicroscopeState"],
            mode=mode,
            stop=False,
        )

    def _finish_capture_ui(self, mode: str, images_received: int) -> None:
        """Finalize capture widgets on the Tk thread.

        Parameters
        ----------
        mode : str
            Active acquisition mode.
        images_received : int
            Total number of frames processed during capture.

        Returns
        -------
        None
        """
        self.acquire_bar_controller.progress_bar(
            images_received=images_received,
            microscope_state=self.configuration["experiment"]["MicroscopeState"],
            mode=mode,
            stop=True,
        )
        self.set_mode_of_sub("stop")
        self._set_autofocus_acquisition_state("idle")
        self._set_autofocus_state(False)

    def change_microscope(self, microscope_name: str, zoom: str | None = None) -> bool:
        """Change the microscope configuration.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope to switch to.
        zoom : str | None, optional
            Zoom value to set for the microscope. If ``None``, keep current zoom.

        Returns
        -------
        bool
            ``True`` when the microscope or zoom is updated successfully,
            otherwise ``False``.
        """
        if self.configuration_controller.change_microscope(microscope_name):
            supported_zoom = list(
                self.configuration_controller.get_zoom_value_list(microscope_name)
            )
            if not supported_zoom:
                messagebox.showwarning(
                    title="Navigate",
                    message=(
                        f"No zoom values are configured for microscope "
                        f"'{microscope_name}'. Please update the configuration YAML."
                    ),
                )
                return False
            if zoom not in supported_zoom:
                fallback_zoom = supported_zoom[0]
                messagebox.showwarning(
                    title="Navigate",
                    message=(
                        f"Zoom '{zoom}' is not available for microscope "
                        f"'{microscope_name}'. Using '{fallback_zoom}' instead."
                    ),
                )
                zoom = fallback_zoom

            # update microscope name
            self.configuration["experiment"]["MicroscopeState"][
                "microscope_name"
            ] = microscope_name
            # set zoom value
            self.configuration["experiment"]["MicroscopeState"]["zoom"] = zoom
            # update widgets
            self.stage_controller.initialize()
            self.channels_tab_controller.initialize()
            self.channels_tab_controller.populate_experiment_values()
            self.camera_setting_controller.update_camera_device_related_setting()
            self.camera_setting_controller.populate_experiment_values()
            r = self.camera_setting_controller.calculate_physical_dimensions()
            if not r:
                messagebox.showwarning(
                    title="Navigate",
                    message=(
                        f"Please make sure a valid pixel size is configured for zoom "
                        f"'{zoom}' on microscope '{microscope_name}' in the "
                        "configuration YAML."
                    ),
                )
            self.camera_view_controller.update_snr()
            result = True
        elif self.configuration_controller.microscope_name == microscope_name:
            # update zoom only if it's valid
            if zoom != self.configuration["experiment"]["MicroscopeState"][
                "zoom"
            ] and zoom in self.configuration_controller.get_zoom_value_list(
                microscope_name
            ):
                self.configuration["experiment"]["MicroscopeState"]["zoom"] = zoom
                r = self.camera_setting_controller.calculate_physical_dimensions()
                if not r:
                    messagebox.showwarning(
                        title="Navigate",
                        message=(
                            f"Please make sure a valid pixel size is configured for "
                            f"zoom '{zoom}' on microscope '{microscope_name}' in the "
                            "configuration YAML."
                        ),
                    )
                result = True
            else:
                result = False
        else:
            messagebox.showwarning(
                title="Navigate",
                message=(
                    f"Microscope '{microscope_name}' is not configured."
                    if not zoom
                    else (
                        f"Microscope '{microscope_name}' with zoom '{zoom}' "
                        "is not configured."
                    )
                ),
            )
            return False
        if (
            hasattr(self, "waveform_popup_controller")
            and self.waveform_popup_controller
        ):
            self.waveform_popup_controller.populate_experiment_values()
        return result

    def initialize_cam_view(self) -> None:
        """Populate view and maximum intensity projection tabs.

        Communicates with the camera view controller and mip setting controller to
        set the minimum and maximum counts, as well as the default channel settings.

        Returns
        -------
        None
        """
        # Populating Min and Max Counts
        self.camera_view_controller.initialize("minmax", [0, 2**16 - 1])
        self.mip_setting_controller.initialize("minmax", [0, 2**16 - 1])
        self.camera_view_controller.initialize("image", [1, 0, 0])

    def populate_experiment_setting(
        self,
        file_name: str | os.PathLike[str] | None = None,
        in_initialize: bool = False,
    ) -> None:
        """Load experiment file and populate model.experiment and configure view.

        Confirms that the experiment file exists.
        Sends the experiment file to the model and the controller.
        Populates the GUI with these settings.

        Parameters
        ----------
        file_name : str | os.PathLike[str] | None, optional
            Path to a non-default experiment YAML file to load.
        in_initialize : bool, optional
            ``True`` when called during controller initialization to skip reloading
            experiment YAML from disk.

        Returns
        -------
        None
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
        self.camera_setting_controller.populate_experiment_values()
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
            self.configuration["multi_positions"]
        )
        self.channels_tab_controller.populate_experiment_values()
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

    def update_experiment_setting(self) -> str:
        """Update experiment settings from GUI state.

        Collect settings from sub-controllers, validate values, and synchronize
        configuration data used by model commands.

        Returns
        -------
        str
            Concatenated warning message if validation fails, otherwise an empty
            string.
        """
        microscope_name = self.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ]
        zoom_value = self.configuration["experiment"]["MicroscopeState"]["zoom"]
        resolution_value = self.menu_controller.resolution_value.get()

        # set microscope and zoom value according to GUI
        if f"{microscope_name} {zoom_value}" != resolution_value:
            microscope_name, zoom_value = resolution_value.split()
            self.configuration["experiment"]["MicroscopeState"][
                "microscope_name"
            ] = microscope_name
            self.configuration["experiment"]["MicroscopeState"]["zoom"] = zoom_value
            self.execute("resolution", resolution_value)

        warning_message = self.camera_setting_controller.update_experiment_values()

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
        self.configuration["multi_positions"] = positions

        if (
            self.configuration["experiment"]["MicroscopeState"]["is_multiposition"]
            and len(positions) < 2
        ):
            # Update the view and override the settings.
            self.configuration["experiment"]["MicroscopeState"][
                "is_multiposition"
            ] = False
            self.channels_tab_controller.is_multiposition_val.set(False)

        self.channels_tab_controller.update_experiment_values()
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

    def enable_resize(self) -> None:
        """Enable window resize handling.

        Returns
        -------
        None
        """
        self.resize_ready_flag = True

    def resize(self, event: tkinter.Event) -> None:
        """Resize the GUI.

        Parameters
        ----------
        event : tkinter.Event
            Tk ``<Configure>`` event emitted during window size changes.

        Returns
        -------
        None
        """

        def refresh(width: int, height: int) -> None:
            """Refresh the GUI.

            Parameters
            ----------
            width : int
                Width of the GUI.
            height : int
                Height of the GUI.

            Returns
            -------
            None
            """
            self.view.scroll_frame.resize(width, height)
            self.view.update_idletasks()

        if not self.resize_ready_flag:
            return
        if event.widget != self.root:
            return
        if event.width == self.window_width and event.height == self.window_height:
            return

        if self.resize_event_id:
            self.view.after_cancel(self.resize_event_id)
        self.window_width = event.width
        self.window_height = event.height
        self.resize_event_id = self.view.after(
            300, lambda: refresh(event.width, event.height)
        )

    def prepare_acquire_data(self) -> bool:
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

    def set_mode_of_sub(self, mode: str) -> None:
        """Communicates imaging mode to sub-controllers.

        Parameters
        ----------
        mode : str
            Imaging mode such as ``"live"`` or ``"stop"``.

        Returns
        -------
        None
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

    def execute(self, command: str, *args: Any) -> Any:
        """Handle controller commands from sub-controllers and UI callbacks.

        The controller configuration is synchronized with model state and commands are
        dispatched to worker threads or executed locally based on command type.

        Parameters
        ----------
        command : str
            Command name routed to controller/model operations.
        *args : Any
            Command-specific positional arguments.

        Returns
        -------
        Any
            Command-dependent return value. Most commands return ``None``; some, such
            as ``"get_stage_position"``, return structured data.
        """

        if command == "stage":
            """Creates a thread and uses it to call the model to move stage

            Parameters
            __________
            args[0] : dict
                dict = {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}
            """
            self.threads_pool.createThread(
                resourceName="model",
                target=self.move_stage,
                args=({args[1] + "_abs": args[0]},),
            )

        elif command == "stop_stage":
            """Creates a thread and uses it to call the model to stop stage"""
            self.threads_pool.createThread(
                resourceName="stop_stage", target=self.stop_stage
            )

        elif command == "query_stages":
            """Query the stages for the active microscope's current position in a
            thread-blocking format."""
            query_thread = self.threads_pool.createThread(
                resourceName="model", target=self.stop_stage
            )

            while query_thread.is_alive():
                time.sleep(0.01)

        elif command == "query_select_microscope":
            """Query a specific microscope for its current positions in a
            thread-blocking format."""
            microscope_name = args[0]
            query_thread = self.threads_pool.createThread(
                resourceName="model",
                target=self.query_select_microscope,
                args=(microscope_name,),
            )

            while query_thread.is_alive():
                time.sleep(0.01)

        elif command == "update_stage_limits":
            microscope_name = args[0]
            if microscope_name == self.configuration_controller.microscope_name:
                self.stage_controller.initialize()
                self.channels_tab_controller.update_stack_position_limits()
            self.threads_pool.createThread(
                resourceName="model",
                target=self.update_stage_limits,
                args=(microscope_name,),
            )

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
            """Returns the current stage position from the widgets.

            Does not communicate with the stages, but rather takes the last known
            position.

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
            self.threads_pool.createThread(
                resourceName="model",
                target=lambda: self.model.run_command("update_setting", "resolution"),
            )

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
                resourceName="model",
                target=lambda: self.model.run_command("update_setting", *args),
            )

        elif command == "stage_limits":
            self.stage_controller.stage_limits = args[0]
            self.channels_tab_controller.update_stack_position_limits()
            self.threads_pool.createThread(
                resourceName="model",
                target=lambda: self.model.run_command("stage_limits", *args),
            )

        elif command == "autofocus":
            """Execute autofocus routine."""
            if not self.acquire_bar_controller.is_acquiring:
                self._set_autofocus_state(True)
                self._set_autofocus_acquisition_state("starting")
                self.acquire_bar_controller.is_acquiring = True
                self.acquire_bar_controller.view.acquire_btn.configure(state="disabled")
                self.threads_pool.createThread(
                    resourceName="camera",
                    target=self.capture_image,
                    args=("autofocus", "live", *args),
                )
            elif self.acquire_bar_controller.mode == "live":
                self._set_autofocus_state(True)
                self.threads_pool.createThread(
                    resourceName="model",
                    target=lambda: self.model.run_command("autofocus", *args),
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
                resourceName="model",
                target=lambda: self.model.run_command("load_feature", *args),
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
            # get saving file directory
            file_directory = args[0]

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

            # Save multi_positions.yml file
            save_yaml_file(
                file_directory=file_directory,
                content_dict=self.configuration["multi_positions"],
                filename="multi_positions.yml",
            )

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
            self._set_autofocus_acquisition_state("stopping")
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

            Saves the current settings to .navigate/config/*.yml files.
            """
            self.sloppy_stop()
            self.update_experiment_setting()
            file_directory = os.path.join(get_navigate_path(), "config")
            for config_name, filename in [
                ("experiment", "experiment.yml"),
                ("multi_positions", "multi_positions.yml"),
                ("gui", "gui_configuration.yml"),
                ("waveform_constants", "waveform_constants.yml"),
                ("rest_api_config", "rest_api_config.yml"),
                ("waveform_templates", "waveform_templates.yml"),
            ]:
                save_yaml_file(
                    file_directory=file_directory,
                    content_dict=self.configuration[config_name],
                    filename=filename,
                )

            self.model.run_command("terminate")
            self.model = None
            self.event_queue.put(("stop", ""))
            self._stop_event_pump()
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
        elif command in [
            "set_camera_cooling_state",
            "get_camera_temperature",
            "stop_refresh_camera_temperature",
        ]:
            self.threads_pool.createThread(
                "model", lambda: self.model.run_command(command, *args)
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

    def sloppy_stop(self) -> None:
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

        Returns
        -------
        None
        """
        e = RuntimeError
        while e is RuntimeError:
            try:
                self.model.run_command("stop")
                e = None
            except RuntimeError:
                e = RuntimeError

    def capture_image(self, command: str, mode: str, *args: Any) -> None:
        """Trigger the model to capture images.

        Parameters
        ----------
        command : str
            Capture command passed to the model (for example ``"acquire"``).
        mode : str
            Acquisition mode (for example ``"continuous"`` or ``"single"``).
        *args : Any
            Command-specific positional arguments.

        Returns
        -------
        None
        """
        self._run_on_main_thread(self._start_capture_ui, mode, wait=True)
        images_received = 0
        try:
            work_thread = self.threads_pool.createThread(
                "model", lambda: self.model.run_command(command, *args)
            )
            work_thread.join()
        except Exception as e:
            self._run_on_main_thread(self._handle_capture_start_error, e, wait=True)
            return
        microscope_name = self.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ]
        self._run_on_main_thread(self._on_capture_started, microscope_name, wait=True)
        self.stop_acquisition_flag = False

        while True:
            if self.stop_acquisition_flag:
                break
            # Receive the Image and log it.
            image_id = self.show_img_pipe.recv()
            dropped_frames = 0
            if mode == "live":
                # Drain queued frames so we only process the most recent one.
                # This prevents the pipe backlog from causing visible display lag.
                while self.show_img_pipe.poll():
                    image_id = self.show_img_pipe.recv()
                    if image_id == "stop" or not isinstance(image_id, int):
                        break
                    dropped_frames += 1

            logger.info(f"Received image from the controller: {image_id}")
            if dropped_frames:
                logger.debug(
                    "Live display dropping %d queued frames to keep up.",
                    dropped_frames,
                )

            if image_id == "stop":
                self.current_image_id = -1
                break

            self.current_image_id = image_id

            if not isinstance(image_id, int):
                logger.debug(
                    f"Navigate Controller - Something wrong happened, stop the model!, "
                    f"{image_id}"
                )
                self._run_on_main_thread(self.execute, "stop_acquire")
                continue

            images_received += 1 + dropped_frames
            self._run_on_main_thread(
                self._update_capture_display,
                image_id,
                mode,
                images_received,
                wait=True,
            )

        logger.info(
            f"Navigate Controller - Captured {images_received}, " f"{mode} Images"
        )

        # acquisition mode from plugin
        plugin_obj = self.plugin_acquisition_modes.get(mode, None)
        if plugin_obj and hasattr(plugin_obj, "end_acquisition_controller"):
            getattr(plugin_obj, "end_acquisition_controller")(self)

        self._run_on_main_thread(
            self._finish_capture_ui,
            mode,
            images_received,
            wait=True,
        )

    def launch_additional_microscopes(self) -> None:
        """Launch and wire up auxiliary microscope display windows.

        Returns
        -------
        None
        """

        def display_images(
            microscope_name: str,
            camera_view_controller: CameraViewController,
            show_img_pipe: Any,
            data_buffer: Any,
        ) -> None:
            """Display images from additional microscopes.

            Parameters
            ----------
            microscope_name : str
                Microscope name
            camera_view_controller : CameraViewController
                Camera View Controller object.
            show_img_pipe : multiprocessing.Pipe
                The pipe for showing images.
            data_buffer : SharedNDArray
                Pre-allocated shared memory array.
                Size dictated by x_pixels, y_pixels, and number_of_frames in
                configuration file.

            Returns
            -------
            None
            """
            self._run_on_main_thread(
                camera_view_controller.initialize_non_live_display,
                self.configuration["experiment"]["MicroscopeState"],
                self.configuration["experiment"]["CameraParameters"][microscope_name],
                wait=True,
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
                    self._run_on_main_thread(
                        camera_view_controller.try_to_display_image,
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

            if (
                "camera_view_controller"
                not in self.additional_microscopes[microscope_name]
            ):
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

    def destroy_virtual_microscope(
        self, microscope_name: str, destroy_window: bool = True
    ) -> None:
        """Destroy virtual microscopes.

        Parameters
        ----------
        microscope_name : str
            The microscope name
        destroy_window : bool
            The flag to dismiss window.

        Returns
        -------
        None
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

    def move_stage(self, pos_dict: dict[str, Any]) -> None:
        """Trigger the model to move the stage.

        Parameters
        ----------
        pos_dict : dict[str, Any]
            Dictionary of axis positions

        Returns
        -------
        None
        """
        # Update our local stage dictionary
        update_stage_dict(self, pos_dict)

        # Pass to model
        self.model.move_stage(pos_dict)

    def query_select_microscope(self, microscope_name: str) -> None:
        """Query a specific microscope for its current stage positions.

        Parameters
        ----------
        microscope_name : str
            Microscope name to query from the model.

        Returns
        -------
        None
        """
        stage_positions = self.model.query_select_microscope(microscope_name)

        # Inject updated positions back into the advanced stage parameters popup.
        if hasattr(self, "stage_limits_popup_controller"):
            self.stage_limits_popup_controller.positions = stage_positions

    def stop_stage(self) -> None:
        """Stop the stage.

        Grab the stopped position from the stage
        and update the GUI control values accordingly.

        Returns
        -------
        None
        """
        while True:
            try:
                self.model.stop_stage()
                return
            except RuntimeError as e:
                if "ObjectInSubprocess at the same time" not in str(e):
                    raise
                # ObjectInSubprocess rejects concurrent proxy calls. A safety stop
                # must be retried instead of disappearing in the thread pool.
                time.sleep(0.001)

    def update_stage_limits(self, microscope_name: str) -> None:
        """Update stage limits on the device side

        Parameters
        ----------
        microscope_name : str
            Microscope name.

        Returns
        -------
        None
        """
        self.model.update_stage_limits(microscope_name)

    def update_stage_controller_silent(self, ret_pos_dict: dict[str, Any]) -> None:
        """Send updates to the stage GUI

        Parameters
        ----------
        ret_pos_dict : dict[str, Any]
            Dictionary of axis positions

        Returns
        -------
        None
        """
        stage_gui_dict = {}
        for axis, val in ret_pos_dict.items():
            ax = axis.split("_")[0]
            stage_gui_dict[ax] = val
        self.stage_controller.set_position_silent(stage_gui_dict)

    def update_frame_rate(self, frame_rate: float) -> None:
        """Update the frame rate display in the GUI.

        Updates the frame rate in the camera settings tab and the acquire bar
        controller. This method receives the accurate frame rate calculated
        from the model's run_data_process method.

        Parameters
        ----------
        frame_rate : float
            The frame rate in frames per second (Hz).

        Returns
        -------
        None
        """
        # Round frame_rate to two decimal places for display
        frame_rate = round(frame_rate, 2)

        # Update the Framerate in the Camera Settings Tab
        self.camera_setting_controller.framerate_widgets["max_framerate"].set(
            frame_rate
        )

        # Update the Framerate in the Acquire Bar to provide an estimate of
        # the duration of time remaining.
        self.acquire_bar_controller.framerate = frame_rate

    def update_event(self) -> None:
        """Update the View/Controller based on events from the Model.

        This method runs on the Tk thread and drains all pending model events.

        Returns
        -------
        None
        """
        while self._event_pump_running:
            try:
                event, value = self.event_queue.get_nowait()
            except queue.Empty:
                break

            if event == "warning":
                # Display a warning that arises from the model as a top-level GUI popup
                messagebox.showwarning(title="Navigate", message=value)

            elif event == "multiposition":
                # Update the multi-position tab without appending to the list
                update_table(
                    table=self.multiposition_tab_controller.table,
                    pos=value[1:],
                    axes=value[0],
                )
                self.multiposition_tab_controller.clear_hidden_position_columns()
                self.channels_tab_controller.is_multiposition_val.set(True)

            elif event == "stop":
                # Stop the software
                self._stop_event_pump()
                break

            elif event == "update_stage":
                for _ in range(10):
                    try:
                        self.update_stage_controller_silent(value)
                        break
                    except RuntimeError:
                        time.sleep(0.001)
                        pass

            elif event == "frame_rate":
                # Update the GUI with the accurate frame rate from the model
                self.update_frame_rate(value)

            elif event == "autofocus_sequence_complete":
                self._set_autofocus_state(False)

            elif event in self.event_listeners.keys():
                try:
                    self.event_listeners[event](value)
                except Exception:
                    print(f"*** unhandled event: {event}, {value}")

    def add_acquisition_mode(
        self, name: str, acquisition_obj: Callable[[str], Any]
    ) -> None:
        """Add and Acquisition Mode.

        Parameters
        ----------
        name : str
            Name of the acquisition mode.
        acquisition_obj : Callable[[str], Any]
            Factory or class that produces an acquisition mode object.

        Returns
        -------
        None
        """
        if name in self.plugin_acquisition_modes:
            print(f"*** plugin acquisition mode {name} exists, can't add another one!")
            return
        self.plugin_acquisition_modes[name] = acquisition_obj(name)
        self.acquire_bar_controller.add_mode(name)

    def register_event_listener(
        self, event_name: str, event_handler: Callable[[Any], None]
    ) -> None:
        """Register an event listener.

        Parameters
        ----------
        event_name : str
            Name of the event.
        event_handler : Callable[[Any], None]
            The function to handle the event.

        Returns
        -------
        None
        """
        self.event_listeners[event_name] = event_handler

    def register_event_listeners(
        self, events: dict[str, Callable[[Any], None]]
    ) -> None:
        """Register multiple event listeners.

        Parameters
        ----------
        events : dict[str, Callable[[Any], None]]
            Dictionary of event names and handlers.

        Returns
        -------
        None
        """
        for event_name, event_handler in events.items():
            self.register_event_listener(event_name, event_handler)
