# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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
#

# Standard Library Imports
import threading
import logging
import multiprocessing as mp
import time
import os

# Third Party Imports

# Local Imports
from navigate.model.concurrency.concurrency_tools import SharedNDArray
from navigate.model.features.autofocus import Autofocus
from navigate.model.features.cva_conpro import ConstantVelocityAcquisition
from navigate.model.features.adaptive_optics import TonyWilson
from navigate.model.features.image_writer import ImageWriter
from navigate.model.features.auto_tile_scan import CalculateFocusRange  # noqa
from navigate.model.features.common_features import (
    ChangeResolution,
    Snap,
    ZStackAcquisition,
    FindTissueSimple2D,
    PrepareNextChannel,
    LoopByCount,
    StackPause,
    MoveToNextPositionInMultiPositionTable,
    WaitToContinue,
)
from navigate.model.features.remove_empty_tiles import (
    DetectTissueInStackAndRecord,
    RemoveEmptyPositions,
)
from navigate.model.features.feature_container import load_features
from navigate.model.features.restful_features import IlastikSegmentation
from navigate.model.features.volume_search import VolumeSearch
from navigate.model.features.feature_related_functions import (
    convert_str_to_feature_list,
    convert_feature_list_to_str,
    SharedList,
    load_dynamic_parameter_functions,
)
from navigate.log_files.log_functions import log_setup
from navigate.tools.common_dict_tools import update_stage_dict
from navigate.tools.common_functions import load_module_from_file, VariableWithLock
from navigate.tools.file_functions import load_yaml_file, save_yaml_file
from navigate.model.device_startup_functions import load_devices
from navigate.model.microscope import Microscope
from navigate.config.config import get_navigate_path
from navigate.model.plugins_model import PluginsModel


# Logger Setup
p = __name__.split(".")[1]


class Model:
    """Navigate Model Class

    Model for Model-View-Controller Software Architecture."""

    def __init__(self, args, configuration=None, event_queue=None):
        """Initialize the Model.

        Parameters
        ----------
        args : argparse.Namespace
            Command line arguments.
        configuration : dict
            Configuration dictionary.
        event_queue : multiprocessing.Queue
            Queue for events.
        """

        log_setup("model_logging.yml")
        #: object: Logger object.
        self.logger = logging.getLogger(p)

        # Loads the YAML file for all of the microscope parameters
        #: dict: Configuration dictionary.
        self.configuration = configuration

        plugins = PluginsModel()
        # load plugin feature and devices
        plugin_devices, plugin_acquisition_modes = plugins.load_plugins()
        devices_dict = load_devices(
            configuration, args.synthetic_hardware, plugin_devices
        )
        devices_dict["__plugins__"] = plugin_devices

        #: dict: Dictionary of plugin acquisition modes
        self.plugin_acquisition_modes = plugin_acquisition_modes

        #: dict: Dictionary of virtual microscopes.
        self.virtual_microscopes = {}
        #: dict: Dictionary of physical microscopes.
        self.microscopes = {}
        for microscope_name in configuration["configuration"]["microscopes"].keys():
            self.microscopes[microscope_name] = Microscope(
                microscope_name, configuration, devices_dict, args.synthetic_hardware
            )
            self.microscopes[microscope_name].output_event_queue = event_queue
        # register device commands if there is any.

        #: str: Name of the active microscope.
        self.active_microscope = None
        #: str: Name of the active microscope.
        self.active_microscope_name = None
        self.get_active_microscope()

        # Acquisition Housekeeping
        #: str: Imaging mode.
        self.imaging_mode = None
        #: int: Number of images acquired.
        self.image_count = 0
        #: int: Number of acquisitions.
        self.acquisition_count = 0
        #: int: Total number of acquisitions.
        self.total_acquisition_count = None
        #: int: Total number of images.
        self.total_image_count = None
        #: float: Current exposure time in milliseconds
        self.current_exposure_time = 0  # milliseconds
        #: float: Pre-exposure time in milliseconds
        self.pre_exposure_time = 0  # milliseconds
        #: int: Number of timeouts before aborting acquisition.
        self.camera_wait_iterations = 20  # Thread waits this * 500 ms before it ends
        #: float: Time before acquisition.
        self.start_time = None
        #: object: Data buffer.
        self.data_buffer = None
        #: int: Number of active pixels in the x-dimension.
        self.img_width = int(
            self.configuration["experiment"]["CameraParameters"]["img_x_pixels"]
        )
        #: int: Number of active pixels in the y-dimension.
        self.img_height = int(
            self.configuration["experiment"]["CameraParameters"]["img_y_pixels"]
        )
        #: str: Binning mode.
        self.binning = "1x1"
        #: array: stage positions.
        self.data_buffer_positions = None
        #: array: saving flags for a frame
        self.data_buffer_saving_flags = None
        #: bool: Is the model acquiring?
        self.is_acquiring = False

        # Autofocusing
        #: float: Current focus position.
        self.f_position = None
        #: float: Autofocus maximum entropy.
        self.max_entropy = None
        #: float: Autofocus maximum entropy position.
        self.focus_pos = None

        # Threads
        #: threading.Thread: Signal thread.
        self.signal_thread = None
        #: threading.Thread: Data thread.
        self.data_thread = None

        # show image function/pipe handler
        #: multiprocessing.connection.Connection: Show image pipe.
        self.show_img_pipe = None

        # Plot Pipe handler
        #: multiprocessing.connection.Connection: Plot pipe.
        self.plot_pipe = None

        # waveform queue
        #: multiprocessing.Queue: Waveform queue.
        self.event_queue = event_queue

        # frame signal id
        #: int: Frame ID.
        self.frame_id = 0

        # flags
        #: bool: Inject a feature list?
        self.injected_flag = VariableWithLock(bool)  # autofocus
        #: bool: Is the model live?
        self.is_live = False  # need to clear up data buffer after acquisition
        #: bool: Is the model saving the data?
        self.is_save = False  # save data
        #: bool: Stop signal and data threads?
        self.stop_acquisition = False  # stop signal and data threads
        #: bool: Stop signal thread?
        self.stop_send_signal = False  # stop signal thread
        #: event: Pause data event.
        self.pause_data_event = threading.Event()
        #: threading.Lock: Pause data ready lock.
        self.pause_data_ready_lock = threading.Lock()
        #: bool: Ask to pause data thread?
        self.ask_to_pause_data_thread = False

        # data buffer for image frames
        #: int: Number of frames in the data buffer.
        self.number_of_frames = self.configuration["experiment"]["CameraParameters"][
            "databuffer_size"
        ]
        self.update_data_buffer(self.img_width, self.img_height)

        # Image Writer/Save functionality
        #: ImageWriter: Image writer.
        self.image_writer = None

        # feature list
        #: list: add on feature in customized mode
        self.addon_feature = None
        #: list: List of features.
        self.feature_list = []
        # automatically switch resolution
        self.feature_list.append(
            [
                {"name": ChangeResolution, "args": ("Mesoscale", "1x")},
                {"name": Snap},
            ]
        )
        # z stack acquisition
        self.feature_list.append([{"name": ZStackAcquisition}])
        # threshold and tile
        self.feature_list.append([{"name": FindTissueSimple2D}])
        # Ilastik segmentation
        self.feature_list.append([{"name": IlastikSegmentation}])
        # volume search
        self.feature_list.append(
            [
                {
                    "name": VolumeSearch,
                    "args": ("Nanoscale", "N/A", True, False, 0.1),
                }
            ]
        )
        self.feature_list.append(
            [
                (
                    (
                        {"name": PrepareNextChannel},
                        {
                            "name": LoopByCount,
                            "args": ("experiment.MicroscopeState.selected_channels",),
                        },
                    ),
                    {
                        "name": LoopByCount,
                        "args": ("experiment.MicroscopeState.timepoints",),
                    },
                )
            ]
        )

        self.feature_list.append(
            [
                # {"name": MoveToNextPositionInMultiPositionTable},
                # {"name": CalculateFocusRange},
                {"name": PrepareNextChannel},
                (
                    {"name": MoveToNextPositionInMultiPositionTable},
                    {"name": Autofocus},
                    {
                        "name": ZStackAcquisition,
                        "args": (
                            True,
                            True,
                        ),
                    },
                    {"name": WaitToContinue},
                    {
                        "name": LoopByCount,
                        "args": ("experiment.MicroscopeState.multiposition_count",),
                    },
                ),
            ]
        )

        records = SharedList([], "records")
        self.feature_list.append(
            [
                {"name": PrepareNextChannel},
                (
                    {"name": MoveToNextPositionInMultiPositionTable},
                    # {"name": CalculateFocusRange},
                    {
                        "name": DetectTissueInStackAndRecord,
                        "args": (
                            5,
                            0.75,
                            records,
                        ),
                    },
                    {
                        "name": LoopByCount,
                        "args": ("experiment.MicroscopeState.multiposition_count",),
                    },
                ),
                {"name": RemoveEmptyPositions, "args": (records,)},
            ]
        )

        self.acquisition_modes_feature_setting = {
            "single": [
                (
                    {"name": PrepareNextChannel},
                    {
                        "name": LoopByCount,
                        "args": ("experiment.MicroscopeState.selected_channels",),
                    },
                )
            ],
            "live": [
                (
                    {"name": PrepareNextChannel},
                    {
                        "name": LoopByCount,
                        "args": ("experiment.MicroscopeState.selected_channels",),
                    },
                )
            ],
            "z-stack": [
                (
                    {"name": ZStackAcquisition},
                    {"name": StackPause},
                    {
                        "name": LoopByCount,
                        "args": ("experiment.MicroscopeState.timepoints",),
                    },
                )
            ],
            "ConstantVelocityAcquisition": [{"name": ConstantVelocityAcquisition}],
            "customized": [],
        }
        # append plugin acquisition mode
        for mode in self.plugin_acquisition_modes:
            self.acquisition_modes_feature_setting[
                mode
            ] = self.plugin_acquisition_modes[mode].feature_list

        self.load_feature_records()

    def update_data_buffer(self, img_width=512, img_height=512):
        """Update the Data Buffer

        Parameters
        ----------
        img_width : int
            Number of active pixels in the x-dimension.
        img_height : int
            Number of active pixels in the y-dimension.
        """
        self.img_width = img_width
        self.img_height = img_height
        self.data_buffer = [
            SharedNDArray(shape=(img_height, img_width), dtype="uint16")
            for i in range(self.number_of_frames)
        ]
        self.data_buffer_positions = SharedNDArray(
            shape=(self.number_of_frames, 5), dtype=float
        )  # z-index, x, y, z, theta, f
        for microscope_name in self.microscopes:
            self.microscopes[microscope_name].update_data_buffer(
                self.configuration["experiment"]["CameraParameters"]["x_pixels"],
                self.configuration["experiment"]["CameraParameters"]["y_pixels"],
                self.data_buffer,
                self.number_of_frames,
            )

    def get_data_buffer(self, img_width=512, img_height=512):
        """Get the data buffer.

        If the number of active pixels in x and y changes, updates the data buffer and
        returns newly-sized buffer.

        Parameters
        ----------
        img_height : int
            Number of active pixels in the x-dimension.
        img_width : int
            Number of active pixels in the y-dimension.

        Returns
        -------
        data_buffer : SharedNDArray
            Shared memory object.
        """
        if (
            img_width != self.img_width
            or img_height != self.img_height
            or self.configuration["experiment"]["CameraParameters"]["binning"]
            != self.binning
        ):
            self.update_data_buffer(img_width, img_height)
        return self.data_buffer

    def create_pipe(self, pipe_name):
        """Create a data pipe.

        Creates a pair of connection objects connected by a pipe which by default is
        duplex (two-way)

        Parameters
        ----------
        pipe_name : str
            Name of pipe to create.

        Returns
        -------
        end1 : object
            Connection object.
        """
        self.release_pipe(pipe_name)
        end1, end2 = mp.Pipe()
        setattr(self, pipe_name, end2)
        return end1

    def release_pipe(self, pipe_name):
        """Close a data pipe.

        Parameters
        ----------
        pipe_name : str
            Name of pipe to close.
        """
        if hasattr(self, pipe_name):
            pipe = getattr(self, pipe_name)
            if pipe:
                pipe.close()
            delattr(self, pipe_name)

    def get_active_microscope(self):
        """Get the active microscope.

        Returns
        -------
        microscope : Microscope
            Active microscope.
        """

        self.active_microscope_name = self.configuration["experiment"][
            "MicroscopeState"
        ]["microscope_name"]
        self.active_microscope = self.microscopes[self.active_microscope_name]
        return self.active_microscope

    def get_offset_variance_maps(self):
        """Get the offset variance maps.

        Returns
        -------
        offset_variance_maps : dict
            Offset variance maps.
        """

        return self.active_microscope.camera.get_offset_variance_maps()

    def run_command(self, command, *args, **kwargs):
        """Receives commands from the controller.

        Parameters
        ----------
        command : str
            Type of command to run.
        *args : list
            List of arguments to pass to the command.
        **kwargs : dict
            Dictionary of keyword arguments to pass to the command.
        """
        logging.info(
            "Navigate Model - Received command from controller:", command, args
        )
        if not self.data_buffer:
            logging.debug("Navigate Model - Shared Memory Buffer Not Set Up.")
            return

        if command == "acquire":
            self.is_acquiring = True
            self.imaging_mode = self.configuration["experiment"]["MicroscopeState"][
                "image_mode"
            ]
            self.is_save = self.configuration["experiment"]["MicroscopeState"][
                "is_save"
            ]

            # If multiposition is selected, verify that it is not empty.
            if self.configuration["experiment"]["MicroscopeState"]["is_multiposition"]:
                if len(self.configuration["experiment"]["MultiPositions"]) == 0:
                    # Update the view and override the settings.
                    self.event_queue.put(("disable_multiposition", None))
                    self.configuration["experiment"]["MicroscopeState"][
                        "is_multiposition"
                    ] = False

            # Calculate waveforms, turn on lasers, etc.
            self.prepare_acquisition()

            # load features
            if self.imaging_mode == "customized":
                if self.addon_feature is None:
                    self.addon_feature = self.acquisition_modes_feature_setting[
                        "single"
                    ]
                self.signal_container, self.data_container = load_features(
                    self, self.addon_feature
                )
                self.data_buffer_saving_flags = [False] * self.number_of_frames
            else:
                self.signal_container, self.data_container = load_features(
                    self, self.acquisition_modes_feature_setting[self.imaging_mode]
                )
                self.data_buffer_saving_flags = None

            if self.imaging_mode == "live":
                self.signal_thread = threading.Thread(target=self.run_live_acquisition)
            else:
                self.signal_thread = threading.Thread(target=self.run_acquisition)

            self.signal_thread.name = f"{self.imaging_mode} signal"
            if self.is_save and self.imaging_mode != "live":
                saving_config = {}
                plugin_obj = self.plugin_acquisition_modes.get(self.imaging_mode, None)
                if plugin_obj and hasattr(plugin_obj, "update_saving_config"):
                    saving_config = getattr(plugin_obj, "update_saving_config")(self)
                self.image_writer = ImageWriter(
                    self,
                    saving_flags=self.data_buffer_saving_flags,
                    saving_config=saving_config,
                )
                self.data_thread = threading.Thread(
                    target=self.run_data_process,
                    kwargs={"data_func": self.image_writer.save_image},
                )
            else:
                self.is_save = False
                self.data_thread = threading.Thread(target=self.run_data_process)
            self.data_thread.name = f"{self.imaging_mode} Data"
            self.signal_thread.start()
            self.data_thread.start()
            for m in self.virtual_microscopes:
                image_writer = (
                    ImageWriter(
                        self,
                        self.virtual_microscopes[m].data_buffer,
                        m,
                        saving_flags=self.data_buffer_saving_flags,
                        saving_config=saving_config,
                    ).save_image
                    if self.is_save
                    else None
                )
                threading.Thread(
                    target=self.simplified_data_process,
                    args=(
                        self.virtual_microscopes[m],
                        getattr(self, f"{m}_show_img_pipe"),
                        image_writer,
                    ),
                ).start()

        elif command == "update_setting":
            """
            Called by the controller
            Passes the string 'resolution' and a dictionary
            consisting of the resolution_mode, the zoom, and the laser_info.
            e.g., self.resolution_info['waveform_constants'][self.resolution][self.mag]
            """
            reboot = False
            microscope_name = self.configuration["experiment"]["MicroscopeState"][
                "microscope_name"
            ]
            if self.is_acquiring:
                # We called this while in the middle of an acquisition
                # stop live thread
                self.stop_send_signal = True
                self.signal_thread.join()
                if microscope_name != self.active_microscope_name:
                    self.pause_data_thread()
                    self.active_microscope.end_acquisition()
                    reboot = True
                self.active_microscope.current_channel = 0

            if args[0] == "resolution":
                self.change_resolution(
                    self.configuration["experiment"]["MicroscopeState"][
                        "microscope_name"
                    ]
                )

            if reboot:
                # prepare active microscope
                waveform_dict = self.active_microscope.prepare_acquisition()
                self.resume_data_thread()
            else:
                waveform_dict = self.active_microscope.calculate_all_waveform()

            self.event_queue.put(("waveform", waveform_dict))

            if self.is_acquiring:
                # prepare devices based on updated info
                # load features
                self.signal_container, self.data_container = load_features(
                    self, self.acquisition_modes_feature_setting[self.imaging_mode]
                )
                self.stop_send_signal = False
                self.signal_thread = threading.Thread(target=self.run_live_acquisition)
                self.signal_thread.name = "Waveform Popup Signal"
                self.signal_thread.start()

        elif command == "autofocus":
            """Autofocus Routine

            Parameters
            ----------
            Args[0]: device name
            Args[1]: device reference
            """
            if self.is_acquiring and self.imaging_mode == "live":
                with self.injected_flag as injected_flag:
                    if hasattr(self, "signal_container"):
                        self.signal_container.cleanup()
                    if hasattr(self, "data_container"):
                        self.data_container.cleanup()
                    self.signal_container, self.data_container = load_features(
                        self,
                        [{"name": Autofocus}],
                    )
                    injected_flag.value = True

            elif not self.is_acquiring:
                self.is_acquiring = True
                self.imaging_mode = "autofocus"
                autofocus = Autofocus(self, *args)
                autofocus.run()

        elif command == "flatten_mirror":
            self.update_mirror(coef=[], flatten=True)
        elif command == "zero_mirror":
            self.active_microscope.mirror.zero_flatness()
        elif command == "set_mirror":
            coef = list(
                self.configuration["experiment"]["MirrorParameters"]["modes"].values()
            )
            self.update_mirror(coef=coef)
        elif command == "save_wcs_file":
            self.active_microscope.mirror.save_wcs_file(path=args[0])
        elif command == "set_mirror_from_wcs":
            coef = self.active_microscope.mirror.set_from_wcs_file(path=args[0])
            self.update_mirror(coef=coef)
        elif command == "tony_wilson":
            tony_wilson = TonyWilson(self)
            tony_wilson.run(*args)

        elif command == "load_feature":
            """
            args[0]: int, args[0]-1 is the id of features
                   : 0 no features
                   : str, name of feature, case sensitive
            """
            if hasattr(self, "signal_container"):
                delattr(self, "signal_container")
                delattr(self, "data_container")

            if type(args[0]) == int:
                self.addon_feature = None
                if args[0] != 0:
                    if len(args) == 2:
                        self.feature_list[args[0] - 1] = convert_str_to_feature_list(
                            args[1]
                        )

                    self.addon_feature = self.feature_list[args[0] - 1]
                    load_dynamic_parameter_functions(
                        self.addon_feature,
                        f"{get_navigate_path()}/feature_lists/feature_parameter_setting",
                    )
                    self.signal_container, self.data_container = load_features(
                        self, self.addon_feature
                    )
            elif type(args[0]) == str:
                try:
                    if len(args) > 1:
                        self.addon_feature = [
                            {"name": globals()[args[0]], "args": (args[1],)}
                        ]
                        self.signal_container, self.data_container = load_features(
                            self, self.addon_feature
                        )
                    else:
                        self.addon_feature = [{"name": globals()[args[0]]}]
                        self.signal_container, self.data_container = load_features(
                            self, self.addon_feature
                        )
                except KeyError:
                    self.logger.debug(
                        f"run_command - load_feature - Unknown feature {args[0]}."
                    )
        elif command == "stage_limits":
            for microscope_name in self.microscopes:
                self.microscopes[microscope_name].update_stage_limits(args[0])
        elif command == "stop":
            """
            Called when user halts the acquisition
            """
            self.logger.info("Navigate Model - Stopping with stop command.")
            self.stop_acquisition = True

            if hasattr(self, "signal_container"):
                self.signal_container.end_flag = True
            if self.imaging_mode == "ConstantVelocityAcquisition":
                self.active_microscope.stages["z"].stop()
            if self.signal_thread:
                self.signal_thread.join()
            if self.data_thread:
                self.data_thread.join()

            self.end_acquisition()
            self.stop_stage()

        elif command == "terminate":
            self.terminate()

        # elif command == "change_camera":
        #     new_camera = list(self.active_microscope.cameras.values())[args[0]]
        #     print(f"Using new camera >> {new_camera.camera_controller._serial_number}")
        #     self.active_microscope.camera = new_camera

        elif command == "exit":
            for camera in self.active_microscope.cameras.values():
                camera.camera_controller.dev_close()
        else:
            self.active_microscope.run_command(command, args)

    # main function to update mirror/set experiment mode values
    def update_mirror(self, coef=[], flatten=False):
        """Update the mirror.

        Parameters
        ----------
        coef : list
            List of coefficients.
        flatten : bool
            Flatten the mirror?
        """
        if coef:
            self.active_microscope.mirror.display_modes(coef)
        elif flatten:
            self.active_microscope.mirror.flat()

        mirror_img = self.active_microscope.mirror.mirror_controller.get_wavefront_pix()

        self.event_queue.put(
            ("mirror_update", {"mirror_img": mirror_img, "coefs": coef})
        )

        # print(self.configuration['experiment']['MirrorParameters']['modes'])

    def move_stage(self, pos_dict, wait_until_done=False):
        """Moves the stages.

        Updates the stage dictionary, moves to the desired position, and reports
        the position.

        Parameters
        ----------
        pos_dict : dict
            Dictionary of stage positions.
        wait_until_done : bool
            Checks "on target state" after command and waits until done.

        Returns
        -------
        success : bool
            Was the move successful?
        """
        try:
            r = self.active_microscope.move_stage(pos_dict, wait_until_done)
        except Exception as e:
            self.logger.debug(f"*** stage move failed: {e}")
            return False
        return r

    def get_stage_position(self):
        """Get the position of the stage.

        Returns
        -------
        ret_pos_dict : dict
            Dictionary of stage positions.
        """
        return self.active_microscope.get_stage_position()

    def stop_stage(self):
        """Stop the stages."""
        self.active_microscope.stop_stage()
        ret_pos_dict = self.get_stage_position()
        update_stage_dict(self, ret_pos_dict)
        self.event_queue.put(("update_stage", ret_pos_dict))

    def end_acquisition(self):
        """End the acquisition.

        Sets the current channel to 0, clears the signal and data containers,
        disconnects buffer in live mode and closes the shutters."""
        self.is_acquiring = False

        self.active_microscope.end_acquisition()
        for microscope_name in self.virtual_microscopes:
            self.virtual_microscopes[microscope_name].end_acquisition()

        plugin_obj = self.plugin_acquisition_modes.get(self.imaging_mode, None)
        if plugin_obj and hasattr(plugin_obj, "end_acquisition_model"):
            getattr(plugin_obj, "end_acquisition_model")(self)

        if hasattr(self, "signal_container"):
            self.signal_container.cleanup()
            delattr(self, "signal_container")
        if hasattr(self, "data_container"):
            self.data_container.cleanup()
            delattr(self, "data_container")
        if self.image_writer is not None:
            self.image_writer.close()
        #: obj: Add on feature.
        self.addon_feature = None

    def run_data_process(self, num_of_frames=0, data_func=None):
        """Run the data process.

        This function is the structure of data thread.

        Parameters
        ----------
        num_of_frames : int
            Number of frames to acquire.
        data_func : object
            Function to run on the acquired data.
        """
        wait_num = self.camera_wait_iterations
        acquired_frame_num = 0

        # whether acquire specific number of frames.
        count_frame = num_of_frames > 0
        start_time = time.time()

        while not self.stop_acquisition:
            if self.ask_to_pause_data_thread:
                self.pause_data_ready_lock.release()
                self.pause_data_event.clear()
                self.pause_data_event.wait()
            frame_ids = self.active_microscope.camera.get_new_frame()
            self.logger.info(
                f"Navigate Model - Running data process, get frames {frame_ids}"
            )
            # if there is at least one frame available
            if not frame_ids:
                self.logger.info(f"Navigate Model - Waiting {wait_num}")
                wait_num -= 1
                if wait_num <= 0:
                    # Camera timeout, abort acquisition.
                    break
                continue

            acquired_frame_num += len(frame_ids)
            stop_time = time.time()
            frames_per_second = acquired_frame_num / (stop_time - start_time)
            self.event_queue.put(("framerate", frames_per_second))

            wait_num = self.camera_wait_iterations

            if hasattr(self, "data_container") and not self.data_container.end_flag:
                if self.data_container.is_closed:
                    self.logger.info("Navigate Model - Data container is closed.")
                    self.stop_acquisition = True
                    break

                self.data_container.run(frame_ids)

            # ImageWriter to save images
            if data_func:
                data_func(frame_ids)

            # show image
            self.logger.info(f"Navigate Model - Sent through pipe{frame_ids[0]}")
            self.show_img_pipe.send(frame_ids[-1])

            if count_frame and acquired_frame_num >= num_of_frames:
                self.logger.info("Navigate Model - Loop stop condition met.")
                self.stop_acquisition = True

        self.show_img_pipe.send("stop")
        self.logger.info("Navigate Model - Data thread stopped.")
        self.logger.info(
            f"Navigate Model - Received frames in total: {acquired_frame_num}"
        )

        # release the lock when data thread ends
        if self.pause_data_ready_lock.locked():
            self.pause_data_ready_lock.release()

        self.end_acquisition()  # Need this to turn off the lasers/close the shutters

    def pause_data_thread(self):
        """Pause the data thread.

        Function is called when user pauses the acquisition.
        """

        self.pause_data_ready_lock.acquire()
        self.ask_to_pause_data_thread = True
        self.pause_data_ready_lock.acquire()

    def resume_data_thread(self):
        """Resume the data thread.

        Function is called when user resumes the acquisition.
        """

        self.ask_to_pause_data_thread = False
        self.pause_data_event.set()
        if self.pause_data_ready_lock.locked():
            self.pause_data_ready_lock.release()

    def simplified_data_process(self, microscope, show_img_pipe, data_func=None):
        """Run the data process.

        Parameters
        ----------
        microscope : Microscope
            Microscope object.
        show_img_pipe : multiprocessing.connection.Connection
            Pipe for showing images.
        data_func : object
            Function to run on the acquired data.
        """

        wait_num = self.camera_wait_iterations
        acquired_frame_num = 0

        while not self.stop_acquisition:
            frame_ids = (
                microscope.camera.get_new_frame()
            )  # This is the 500 ms wait for Hamamatsu
            self.logger.info(
                f"Navigate Model - Running data process, get frames {frame_ids} from "
                f"{microscope.microscope_name}"
            )
            # if there is at least one frame available
            if not frame_ids:
                self.logger.info(f"Navigate Model - Waiting {wait_num}")
                wait_num -= 1
                if wait_num <= 0:
                    # Camera timeout, abort acquisition.
                    break
                continue

            wait_num = self.camera_wait_iterations

            # Leave it here for now to work with current ImageWriter workflow
            # Will move it feature container later
            if data_func:
                data_func(frame_ids)

            # show image
            self.logger.info(
                f"Navigate Model - Sent through pipe{frame_ids[0]} -- "
                f"{microscope.microscope_name}"
            )
            show_img_pipe.send(frame_ids[-1])
            acquired_frame_num += len(frame_ids)

        show_img_pipe.send("stop")
        self.logger.info("Navigate Model - Data thread stopped.")
        self.logger.info(
            f"Navigate Model - Received frames in total: {acquired_frame_num}"
        )

    def prepare_acquisition(self, turn_off_flags=True):
        """Prepare the acquisition.

        This function is called when user starts the acquisition.
        Sets flags. Calculates all of the waveforms. Sets the Camera Sensor Mode
        Initializes the data buffer and starts camera. Opens Shutters

        Parameters
        ----------
        turn_off_flags : bool
            Turn off the flags.
        """
        # turn off flags
        if turn_off_flags:
            self.stop_acquisition = False
            self.stop_send_signal = False
            self.injected_flag.value = False
            self.is_live = False

        plugin_obj = self.plugin_acquisition_modes.get(self.imaging_mode, None)
        if plugin_obj and hasattr(plugin_obj, "prepare_acquisition_model"):
            getattr(plugin_obj, "prepare_acquisition_model")(self)

        for m in self.virtual_microscopes:
            self.virtual_microscopes[m].prepare_acquisition()

        # Confirm stage position and software are in agreement.
        self.stop_stage()

        # prepare active microscope
        waveform_dict = self.active_microscope.prepare_acquisition()
        self.event_queue.put(("waveform", waveform_dict))

        self.frame_id = 0

    def snap_image(self):
        """Acquire an image after updating the waveforms.

        Can be used in acquisitions where changing waveforms are required,
        but there is additional overhead due to the need to write the
        waveforms into the buffers of the DAQ cards.
        """
        if hasattr(self, "signal_container"):
            self.signal_container.run()

        # Stash current position, channel, timepoint. Do this here, because signal
        # container functions can inject changes to the stage. NOTE: This line is
        # wildly expensive when get_stage_position() does not cache results.
        stage_pos = self.get_stage_position()
        self.data_buffer_positions[self.frame_id][0] = stage_pos.get("x_pos", 0)
        self.data_buffer_positions[self.frame_id][1] = stage_pos.get("y_pos", 0)
        self.data_buffer_positions[self.frame_id][2] = stage_pos.get("z_pos", 0)
        self.data_buffer_positions[self.frame_id][3] = stage_pos.get("theta_pos", 0)
        self.data_buffer_positions[self.frame_id][4] = stage_pos.get("f_pos", 0)

        # Run the acquisition
        try:
            self.active_microscope.turn_on_laser()
            self.active_microscope.daq.run_acquisition()
        except:  # noqa
            self.active_microscope.daq.stop_acquisition()
            if self.active_microscope.current_channel == 0:
                self.stop_acquisition = True
                self.event_queue.put(
                    (
                        "warning",
                        "There is an error happened. Please read the log files for details!",
                    )
                )
                return
            self.active_microscope.daq.prepare_acquisition(
                f"channel_{self.active_microscope.current_channel}"
            )
            self.active_microscope.daq.run_acquisition()
        finally:
            # Ensure the laser is turned off
            self.active_microscope.turn_off_lasers()

        if hasattr(self, "signal_container"):
            self.signal_container.run(wait_response=True)

        self.frame_id = (self.frame_id + 1) % self.number_of_frames

    def run_live_acquisition(self):
        """Stream live image to the GUI.

        Recalculates the waveforms for each image, thereby allowing people to adjust
        acquisition parameters in real-time.
        """
        self.stop_acquisition = False
        while self.stop_acquisition is False and self.stop_send_signal is False:
            self.run_acquisition()
            if not self.injected_flag.value:
                self.signal_container.reset()
            else:
                self.reset_feature_list()
        # Update the stage position.
        # Allows the user to externally move the stage in the continuous mode.
        self.get_stage_position()

    def run_acquisition(self):
        """Run acquisition along with a feature list one time."""
        if not hasattr(self, "signal_container"):
            self.snap_image()
            return

        while (
            not self.signal_container.end_flag
            and not self.stop_send_signal
            and not self.stop_acquisition
        ):
            self.snap_image()
            if not hasattr(self, "signal_container"):
                return
            if self.signal_container.is_closed:
                self.logger.info("Navigate Model - Signal container is closed.")
                self.stop_acquisition = True
                return
        if self.imaging_mode != "live":
            self.stop_acquisition = True

    def reset_feature_list(self):
        """Reset live mode feature list."""
        with self.injected_flag as injected_flag:
            # wait for datathread ends
            waiting_num = 30
            while (
                hasattr(self, "data_container")
                and not self.data_container.end_flag
                and waiting_num > 0
            ):
                if self.stop_acquisition:
                    return
                time.sleep(0.01)
                waiting_num -= 1
            if hasattr(self, "signal_container"):
                self.signal_container.cleanup()
            if hasattr(self, "data_container"):
                self.data_container.cleanup()
            self.signal_container, self.data_container = load_features(
                self,
                [
                    (
                        {"name": PrepareNextChannel},
                        {
                            "name": LoopByCount,
                            "args": ("experiment.MicroscopeState.selected_channels",),
                        },
                    )
                ],
            )
            injected_flag.value = False


    def change_resolution(self, resolution_value):
        """Switch resolution mode of the microscope.

        Parameters
        ----------
        resolution_value : str
            Resolution mode.
        """
        self.active_microscope.central_focus = None

        former_microscope = self.active_microscope_name
        if resolution_value != self.active_microscope_name:
            self.get_active_microscope()
            self.active_microscope.move_stage_offset(former_microscope)

        # update zoom if possible
        try:
            curr_zoom = self.active_microscope.zoom.zoomvalue
            zoom_value = self.configuration["experiment"]["MicroscopeState"]["zoom"]
            self.active_microscope.zoom.set_zoom(zoom_value)
            self.logger.debug(
                f"Change zoom of {self.active_microscope_name} to {zoom_value}"
            )

            offsets = self.active_microscope.zoom.stage_offsets
            solvent = self.configuration["experiment"]["Saving"]["solvent"]
            if (
                offsets is not None
                and curr_zoom is not None
                and self.active_microscope_name == former_microscope
                and solvent in offsets.keys()
            ):
                # stop stages
                self.active_microscope.stop_stage()
                curr_pos = self.get_stage_position()
                shift_pos = {}
                for axis, mags in offsets[solvent].items():
                    shift_pos[f"{axis}_abs"] = curr_pos[f"{axis}_pos"] + float(
                        mags[curr_zoom][zoom_value]
                    )
                self.move_stage(shift_pos, wait_until_done=True)
            # stop stages and update GUI
            self.stop_stage()

        except ValueError as e:
            self.logger.debug(f"{self.active_microscope_name} - {e}")

        self.active_microscope.ask_stage_for_position = True

    def get_camera_line_interval_and_exposure_time(
        self, exposure_time, number_of_pixel
    ):
        """Get camera line interval time and light sheet exposure time

        Parameters
        ----------
        exposure_time : float
            camera global exposure time
        number_of_pixel: int
            number of pixel in light sheet mode

        Returns
        -------
        exposure_time : float
            Light-sheet mode exposure time (ms).
        camera_line_interval : float
            line interval duration (s).

        """
        return self.active_microscope.camera.calculate_light_sheet_exposure_time(
            exposure_time, number_of_pixel
        )

    def load_images(self, filenames=None):
        """Load/Unload images to the Synthetic Camera

        Parameters
        ----------
        filenames : list
            List of filenames to load.
        """
        self.active_microscope.camera.initialize_image_series(
            self.data_buffer, self.number_of_frames
        )
        self.active_microscope.camera.load_images(filenames)
        self.active_microscope.camera.close_image_series()

    def update_ilastik_setting(
        self, display_segmentation=False, mark_position=True, target_labels=[1]
    ):
        """Update the ilastik setting.

        Parameters
        ----------
        display_segmentation : bool
            Display segmentation.
        mark_position : bool
            Mark position.
        target_labels : list
            Target labels.
        """
        #: bool: Display segmentation.
        self.display_ilastik_segmentation = display_segmentation
        #: bool: Mark position.
        self.mark_ilastik_position = mark_position
        #: list: Target labels.
        self.ilastik_target_labels = target_labels

    def get_microscope_info(self):
        """Return Microscopes device information.

        Returns
        -------
        microscope_info : dict
            Microscope device information.
        """
        microscope_info = {}
        for microscope_name in self.microscopes:
            microscope_info[microscope_name] = self.microscopes[microscope_name].info
        return microscope_info

    def launch_virtual_microscope(self, microscope_name, microscope_config):
        """Launch a virtual microscope.

        Parameters
        ----------
        microscope_name : str
            Name of microscope.
        microscope_config : dict
            Configuration of microscope.

        Returns
        -------
        data_buffer : list
            List of data buffer.
        """

        # create databuffer
        data_buffer = [
            SharedNDArray(shape=(self.img_height, self.img_width), dtype="uint16")
            for i in range(self.number_of_frames)
        ]

        # create virtual microscope
        from navigate.model.devices import (
            SyntheticDAQ,
            SyntheticCamera,  # noqa: F401
            SyntheticGalvo,
            SyntheticFilterWheel,  # noqa: F401
            SyntheticShutter,  # noqa: F401
            SyntheticRemoteFocus,  # noqa: F401
            SyntheticStage,
            SyntheticZoom,  # noqa: F401
            SyntheticMirror,  # noqa: F401
        )

        microscope = Microscope(
            microscope_name, self.configuration, {}, False, is_virtual=True
        )
        microscope.daq = SyntheticDAQ(self.configuration)
        microscope.laser_wavelength = self.microscopes[microscope_name].laser_wavelength
        microscope.lasers = self.microscopes[microscope_name].lasers
        microscope.camera = self.microscopes[microscope_name].camera

        # TODO: lasers
        temp = {
            "zoom": "SyntheticZoom",
            "filter_wheel": "SyntheticFilterWheel",
            "shutter": "SyntheticShutter",
            "remote_focus_device": "SyntheticRemoteFocus",
            "mirror": "SyntheticMirror",
        }

        for k in microscope_config:
            if k.startswith("stage"):
                axis = k[len("stage_") :]
                if microscope_config[k] == "":
                    microscope.stages[axis] = SyntheticStage(
                        microscope_name, None, self.configuration
                    )
                else:
                    microscope.stages[axis] = self.microscopes[microscope_name].stages[
                        axis
                    ]
            elif k.startswith("galvo"):
                if microscope_config[k] == "":
                    microscope.galvo[k] = SyntheticGalvo(
                        microscope_name, None, self.configuration
                    )
                else:
                    microscope.galvo[k] = self.microscopes[microscope_name].galvo[k]
            else:
                if microscope_config[k] == "":
                    exec(
                        f"microscope.{k} = {temp[k]}('{microscope_name}', None, "
                        f"self.configuration)"
                    )
                else:
                    setattr(
                        microscope, k, getattr(self.microscopes[microscope_name], k)
                    )

        # connect virtual microscope with data_buffer
        microscope.update_data_buffer(
            self.img_width, self.img_height, data_buffer, self.number_of_frames
        )

        # add microscope to self.virtual_microscopes
        self.virtual_microscopes[microscope_name] = microscope
        return data_buffer

    def destroy_virtual_microscope(self, microscope_name):
        """Destroy a virtual microscope.

        Parameters
        ----------
        microscope_name : str
            Name of microscope.
        """
        data_buffer = self.virtual_microscopes[microscope_name].data_buffer
        del self.virtual_microscopes[microscope_name]
        # delete shared_buffer
        for i in range(self.number_of_frames):
            data_buffer[i].shared_memory.close()
            data_buffer[i].shared_memory.unlink()
        del data_buffer

    def terminate(self):
        """Terminate the model."""
        self.active_microscope.terminate()
        for microscope_name in self.virtual_microscopes:
            self.virtual_microscopes[microscope_name].terminate()

    def load_feature_list_from_file(self, filename, features):
        """Append feature list from file

        Parameters
        ----------
        filename: str
            filename of the feature list
        features: list
            list of feature names
        """
        module = load_module_from_file(filename[filename.rindex("/") + 1 :], filename)
        for name in features:
            feature = getattr(module, name)
            self.feature_list.append(feature())

    def load_feature_list_from_str(self, feature_list_str):
        """Append feature list from feature_list_str

        Parameters
        ----------
        feature_list_str: str
            str of a feature list
        """
        self.feature_list.append(convert_str_to_feature_list(feature_list_str))

    def load_feature_records(self):
        """Load installed feature lists from system folder

        Note
        ----
            System folcer can be found at '..../.navigate/feature_lists'
        """
        feature_lists_path = get_navigate_path() + "/feature_lists"
        if not os.path.exists(feature_lists_path):
            os.makedirs(feature_lists_path)
            return
        # get __sequence.yml
        if not os.path.exists(f"{feature_lists_path}/__sequence.yml"):
            feature_records = []
        else:
            feature_records = load_yaml_file(f"{feature_lists_path}/__sequence.yml")

        # add non added feature lists
        feature_list_files = [
            temp
            for temp in os.listdir(feature_lists_path)
            if (temp.endswith(".yml") or temp.endswith(".yaml"))
            and os.path.isfile(os.path.join(feature_lists_path, temp))
        ]
        for item in feature_list_files:
            if item == "__sequence.yml":
                continue
            temp = load_yaml_file(f"{feature_lists_path}/{item}")
            add_flag = True
            for feature in feature_records:
                if feature["feature_list_name"] == temp["feature_list_name"]:
                    add_flag = False
                    break
            if add_flag:
                feature_records.append(
                    {
                        "feature_list_name": temp["feature_list_name"],
                        "yaml_file_name": item,
                    }
                )

        i = 0
        while i < len(feature_records):
            temp = feature_records[i]
            if not os.path.exists(f"{feature_lists_path}/{temp['yaml_file_name']}"):
                del feature_records[i]
                continue
            item = load_yaml_file(f"{feature_lists_path}/{temp['yaml_file_name']}")

            if item["module_name"]:
                try:
                    module = load_module_from_file(
                        item["module_name"], item["filename"]
                    )
                    feature = getattr(module, item["module_name"])
                except FileNotFoundError:
                    del feature_records[i]
                    continue
                self.feature_list.append(feature())
            elif item["feature_list"]:
                feature = convert_str_to_feature_list(item["feature_list"])
                self.feature_list.append(feature)
            else:
                del feature_records[i]
                continue
            i += 1
        save_yaml_file(feature_lists_path, feature_records, "__sequence.yml")

    def get_feature_list(self, idx):
        """Get feature list str by index

        Parameters
        ----------
        idx: int
            index of feature list

        Returns
        -------
        feature_list_str: str
            "" if not exist
            string of the feature list
        """
        if idx > 0 and idx <= len(self.feature_list):
            return convert_feature_list_to_str(self.feature_list[idx - 1])
        return ""

    def mark_saving_flags(self, frame_ids):
        """Mark saving flags for the ImageWriter

        Parameters
        ----------
        frame_ids: array
            a list of frame ids
        """
        if not self.data_buffer_saving_flags:
            return
        for id in frame_ids:
            self.data_buffer_saving_flags[id] = True
