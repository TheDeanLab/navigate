# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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
import multiprocessing
import time
import os
from typing import Tuple, Any, Dict, List, Optional, Union
import argparse
import json

# Third Party Imports
import numpy as np

# Local Imports
from navigate.model.concurrency.concurrency_tools import SharedNDArray
from navigate.model.features.autofocus import Autofocus
from navigate.model.features.adaptive_optics import TonyWilson
from navigate.model.features.image_writer import ImageWriter
from navigate.model.features.auto_tile_scan import CalculateFocusRange  # noqa
from navigate.model.features.common_features import (
    Snap,  # noqa
    ZStackAcquisition,
    ASIZStackAcquisition,
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
from navigate.model.utils.threads import ThreadWithWarning
from navigate.log_files.log_functions import log_setup
from navigate.tools.common_dict_tools import update_stage_dict
from navigate.tools.common_functions import load_module_from_file, VariableWithLock
from navigate.tools.file_functions import load_yaml_file, save_yaml_file
from navigate.model.microscope import Microscope
from navigate.config.config import get_navigate_path
from navigate.model.plugins_model import PluginsModel


# Logger Setup
p = __name__.split(".")[1]


class Model:
    """Navigate Model Class

    Model for Model-View-Controller Software Architecture."""

    def __init__(
        self,
        args: argparse.Namespace,
        configuration: Optional[Dict[str, Any]] = None,
        event_queue: multiprocessing.Queue = None,
        log_queue: Optional[multiprocessing.Queue] = None,
    ) -> None:
        """Initialize the Model.

        Parameters
        ----------
        args : argparse.Namespace
            Command line arguments.
        configuration : Optional[Dict[str, Any]]
            Configuration dictionary. Defaults to None.
        event_queue : multiprocessing.Queue
            Event queue. Receives events from the controller.
        log_queue : Optional[multiprocessing.Queue]
            Log queue. Receives log messages from the controller.
        """
        # Set up logging
        log_setup("logging.yml", queue=log_queue)

        #: object: Logger object.
        self.logger = logging.getLogger(p)

        #: dict: Configuration dictionary.
        self.configuration = configuration

        # Plugins
        plugins = PluginsModel()
        plugin_devices, plugin_acquisition_modes = plugins.load_plugins()

        #: dict: Dictionary of plugin acquisition modes
        self.plugin_acquisition_modes = plugin_acquisition_modes

        # Devices
        devices_dict = {"__plugins__": plugin_devices}

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

        #: List[SharedNDArray]: Data buffer for image frames.
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

        #: bool: Submit a request to pause the data thread?
        self.ask_to_pause_data_thread = False

        #: bool: Is there a data thread?
        self.is_data_thread_on = False

        #: int: Available image frames
        self.available_image_count = 0

        #: int: Number of frames in the data buffer.
        self.number_of_frames = self.configuration["experiment"]["CameraParameters"][
            "databuffer_size"
        ]
        self.update_data_buffer(self.img_width, self.img_height)

        self.data_buffer_positions = SharedNDArray(
            shape=(self.number_of_frames, 5), dtype=float
        )  # x, y, z, theta, f

        #: ImageWriter: Image writer.
        self.image_writer = None

        #: list: add on feature in customized mode
        self.addon_feature = None

        #: list: List of features.
        self.feature_list = []

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
                            "args": ("channels",),
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
                        "args": ("positions",),
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
                        "args": ("positions",),
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
                        "args": ("channels",),
                    },
                )
            ],
            "live": [
                (
                    {"name": PrepareNextChannel},
                    {
                        "name": LoopByCount,
                        "args": ("channels",),
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
            "customized": [],
        }
        # append plugin acquisition mode
        for mode in self.plugin_acquisition_modes:
            self.acquisition_modes_feature_setting[mode] = (
                self.plugin_acquisition_modes[mode].feature_list
            )

        self.load_feature_records()

    def update_data_buffer(self, img_width: int = 512, img_height: int = 512) -> None:
        """Update the Data Buffer

        Parameters
        ----------
        img_width : int
            Number of active pixels in the x-dimension.
        img_height : int
            Number of active pixels in the y-dimension.

        Returns
        -------
        None
            Completes after the data buffer is resized and reinitialized.
        """
        self.img_width = img_width
        self.img_height = img_height
        if self.data_buffer is not None:
            for i in range(self.number_of_frames):
                self.data_buffer[i].shared_memory.close()
                self.data_buffer[i].shared_memory.unlink()

        self.data_buffer = [
            SharedNDArray(shape=(img_height, img_width), dtype="uint16")
            for _ in range(self.number_of_frames)
        ]

        for microscope_name in self.microscopes:
            self.microscopes[microscope_name].update_data_buffer(
                self.data_buffer,
                self.number_of_frames,
            )

    def get_data_buffer(
        self, img_width: int = 512, img_height: int = 512
    ) -> List[SharedNDArray]:
        """Get the data buffer.

        If the number of active pixels in x and y changes, updates the data buffer and
        returns newly sized buffer.

        Parameters
        ----------
        img_height : int
            Number of active pixels in the x-dimension.
        img_width : int
            Number of active pixels in the y-dimension.

        Returns
        -------
        data_buffer : List[SharedNDArray]
            Shared memory object.
        """
        if (
            img_width != self.img_width
            or img_height != self.img_height
            or self.configuration["experiment"]["CameraParameters"][
                self.active_microscope_name
            ]["binning"]
            != self.binning
        ):
            self.update_data_buffer(img_width, img_height)
        return self.data_buffer

    def create_pipe(self, pipe_name: str) -> multiprocessing.Pipe:
        """Create a data pipe.

        Creates a pair of connection objects connected by a pipe which by default is
        duplex (two-way)

        Parameters
        ----------
        pipe_name : str
            Name of pipe to create.

        Returns
        -------
        multiprocessing.Pipe
            The writable end of the newly created duplex pipe.
        """
        self.release_pipe(pipe_name)
        end1, end2 = multiprocessing.Pipe()
        setattr(self, pipe_name, end2)
        return end1

    def release_pipe(self, pipe_name: str) -> None:
        """Close a data pipe.

        Parameters
        ----------
        pipe_name : str
            Name of pipe to close.

        Returns
        -------
        None
            Always returns None.
        """
        if hasattr(self, pipe_name):
            pipe = getattr(self, pipe_name)
            if pipe:
                pipe.close()
            delattr(self, pipe_name)

    def get_active_microscope(self) -> Microscope:
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

    def get_offset_variance_maps(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get the offset variance maps.

        Returns
        -------
        offset_variance_maps : Tuple[np.ndarray, np.ndarray]
            Offset variance maps.
        """

        return self.active_microscope.camera.get_offset_variance_maps()

    def run_command(
        self, command: str, *args: List[Union[str, int]], **kwargs: Dict[str, Any]
    ) -> None:
        """Receives commands from the controller.

        Parameters
        ----------
        command : str
            Type of command to run.
        *args : List[Union[str, int]]
            List of arguments to pass to the command.
        **kwargs : Dict[str, Any]
            Dictionary of keyword arguments to pass to the command.

        Returns
        -------
        None
            This method always returns None.
        """
        logging.info(f"Received command: {command}, {args}, {kwargs}")
        if not self.data_buffer:
            logging.debug("Shared Memory Not Set Up.")
            return

        if command == "acquire":
            """Begin an acquisition."""
            self.is_acquiring = True
            self.imaging_mode = self.configuration["experiment"]["MicroscopeState"][
                "image_mode"
            ]
            self.is_save = self.configuration["experiment"]["MicroscopeState"][
                "is_save"
            ]
            if len(self.configuration["multi_positions"]) < 2:
                self.configuration["experiment"]["MicroscopeState"][
                    "is_multiposition"
                ] = False

            # Calculate waveforms, turn on lasers, etc.
            r = self.prepare_acquisition()
            if not r:
                self.show_img_pipe.send("stop")
                self.event_queue.put(
                    (
                        "warning",
                        "Acquisition aborted because of camera ROI setting failed.\n"
                        "Please do not use center ROI for the Ximea Camera.",
                    )
                )
                return

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

                # Retrieve dictionary of features and then initialize the signal and data containers.
                self.signal_container, self.data_container = load_features(
                    self, self.acquisition_modes_feature_setting[self.imaging_mode]
                )
                self.data_buffer_saving_flags = None

            if self.imaging_mode == "live":
                self.signal_thread = ThreadWithWarning(
                    target=self.run_live_acquisition,
                    warning_queue=self.event_queue,
                    logger=self.logger,
                )
            else:
                if self.imaging_mode == "z-stack":
                    speed_mode = self.configuration["experiment"][
                        "MicroscopeState"
                    ].get("speed", "Auto")
                    self.is_data_thread_on = speed_mode == "Auto"
                self.signal_thread = ThreadWithWarning(
                    target=self.run_acquisition,
                    warning_queue=self.event_queue,
                    logger=self.logger,
                )

            self.signal_thread.name = f"{self.imaging_mode} signal"

            # Z-stack will be in here.
            if self.is_save and self.imaging_mode != "live":
                saving_config = {}
                plugin_obj = self.plugin_acquisition_modes.get(self.imaging_mode, None)
                if plugin_obj and hasattr(plugin_obj, "update_saving_config"):
                    saving_config = getattr(plugin_obj, "update_saving_config")(self)

                self.image_writer = ImageWriter(
                    model=self,
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
            if self.is_data_thread_on:
                self.data_thread.start()

            # TODO: virtual microscopes only work with data thread on currently.
            for m in self.virtual_microscopes:
                image_writer = (
                    ImageWriter(
                        model=self,
                        data_buffer=self.virtual_microscopes[m].data_buffer,
                        microscope_name=m,
                        sub_dir=m,
                        saving_flags=self.data_buffer_saving_flags,
                        saving_config=saving_config,
                    )
                    if self.is_save
                    else None
                )
                if image_writer:
                    self.virtual_microscopes[m].image_writer = image_writer

                threading.Thread(
                    target=self.simplified_data_process,
                    args=(
                        self.virtual_microscopes[m],
                        getattr(self, f"{m}_show_img_pipe"),
                        image_writer.save_image if image_writer else None,
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
                self.signal_thread = ThreadWithWarning(
                    target=self.run_live_acquisition,
                    warning_queue=self.event_queue,
                    logger=self.logger,
                )
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
            coefficients = list(
                self.configuration["experiment"]["MirrorParameters"]["modes"].values()
            )
            self.update_mirror(coef=coefficients)
        elif command == "save_wcs_file":
            self.active_microscope.mirror.save_wcs_file(path=args[0])
        elif command == "set_mirror_from_wcs":
            coefficients = self.active_microscope.mirror.set_from_wcs_file(path=args[0])
            self.update_mirror(coef=coefficients)
        elif command == "tony_wilson":
            # tony_wilson = TonyWilson(self)
            # tony_wilson.run(*args)
            self.configuration["experiment"]["MicroscopeState"][
                "image_mode"
            ] = "customized"
            self.addon_feature = [{"name": PrepareNextChannel}, {"name": TonyWilson}]
            self.run_command("acquire")

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
                    self.logger.debug(f"Attempted to load an unknown feature: {args}.")
        elif command == "stage_limits":
            for microscope_name in self.microscopes:
                self.microscopes[microscope_name].update_stage_limits(args[0])
        elif command == "stop":
            """
            Called when user halts the acquisition
            """
            self.stop_acquisition = True

            if hasattr(self, "signal_container"):
                self.signal_container.end_flag = True
            if self.signal_thread:
                self.signal_thread.join()
            if self.is_data_thread_on and self.data_thread:
                self.data_thread.join()

            self.end_acquisition()
            self.stop_stage()

        elif command == "terminate":
            self.terminate()

        # elif command == "change_camera":
        #     new_camera = list(self.active_microscope.cameras.values())[args[0]]
        #     print(f"Using new camera >> {
        #     new_camera.camera_controller._serial_number}")
        #     self.active_microscope.camera = new_camera

        elif command == "exit":
            for camera in self.active_microscope.cameras.values():
                camera.camera_controller.dev_close()
        else:
            self.active_microscope.run_command(command, *args)

    # main function to update mirror/set experiment mode values
    def update_mirror(self, coef: list = [], flatten: bool = False) -> None:
        """Update the mirror.

        Parameters
        ----------
        coef : list
            The list of coefficients. Default is [].
        flatten : bool
            Flatten the mirror? Default is False.
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

    def move_stage(self, pos_dict: Dict[str, Any], wait_until_done=False) -> bool:
        """Moves the stages.

        Updates the stage dictionary, moves to the desired position, and reports
        the position.

        Parameters
        ----------
        pos_dict : Dict[str, Any]
            Dictionary of stage positions.
        wait_until_done : bool
            Checks "on target state" after command and waits until done.

        Returns
        -------
        success : bool
            Was the move successful?
        """
        self.logger.debug("****** moving stage to: %s", pos_dict)
        try:
            r = self.active_microscope.move_stage(pos_dict, wait_until_done)
            self.logger.info(
                f"Stage moved to:, {pos_dict}, " f"Wait until done: {wait_until_done}"
            )
        except Exception as e:
            self.logger.debug(f"Stage move failed: {e}")
            return False
        return r

    def get_stage_position(self) -> Dict[str, Any]:
        """Get the position of the stage.

        Returns
        -------
        ret_pos_dict : dict
            Dictionary of stage positions.
        """
        return self.active_microscope.get_stage_position()

    def query_select_microscope(self, *args: List[Any]) -> Dict[str, Any]:
        """Query the selected stage."""
        microscope_name = args[0]
        self.microscopes[microscope_name].stop_stage()
        ret_pos_dict = self.microscopes[microscope_name].get_stage_position()
        return ret_pos_dict

    def update_stage_limits(self, microscope_name: str) -> None:
        """Update stage limits

        Parameters
        ----------
        microscope_name : str
            Microscope name
        """
        microscope = self.microscopes[microscope_name]
        microscope.update_stage_limits()

    def stop_stage(self) -> None:
        """Stop the stages."""
        self.active_microscope.stop_stage()
        ret_pos_dict = self.get_stage_position()
        update_stage_dict(self, ret_pos_dict)
        self.event_queue.put(("update_stage", ret_pos_dict))

    def end_acquisition(self) -> None:
        """End the acquisition.

        Sets the current channel to 0, clears the signal and data containers,
        disconnects buffer in live mode and closes the shutters."""
        self.is_acquiring = False

        self.active_microscope.end_acquisition()
        for microscope_name in self.virtual_microscopes:
            self.virtual_microscopes[microscope_name].end_acquisition()
            if hasattr(self.virtual_microscopes[microscope_name], "image_writer"):
                self.virtual_microscopes[microscope_name].image_writer.close()

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

    def run_data_process(
        self, num_of_frames: Optional[int] = 0, data_func: Optional[callable] = None
    ) -> None:
        """Run the data process.

        This function is the structure of the data thread.

        So long as the acquisition is not stopped, it will keep acquiring frames. If
        it expects a frame, but does not receive one, it will wait for a certain number
        of iterations before aborting the acquisition. If it receives a frame,
        it will count it, send it to the controller for display, and run the data_func
        function on the acquired data. If the data_func is not provided, it will
        simply display the image. If the number of frames to acquire is specified, it
        will stop acquiring frames when the specified number is reached.

        Parameters
        ----------
        num_of_frames : Optional[int]
            Number of frames to acquire. Default is 0.
        data_func : Optional[callable]
            Function to run on the acquired data. Default is None.
        Returns
        -------
        None
            Terminates when acquisition ends or errors occur.
        """
        wait_num = self.camera_wait_iterations
        acquired_frame_num = 0

        # whether acquire a specific number of frames.
        count_frame = num_of_frames > 0

        # Frame rate tracking for GUI update (~10 Hz max)
        frame_rate_update_interval_ns = 100_000_000  # 100ms = 10 Hz
        last_frame_rate_update_ns = time.perf_counter_ns()
        accumulated_durations_ns = []

        while not self.stop_acquisition:
            if self.ask_to_pause_data_thread:
                self.pause_data_ready_lock.release()
                self.pause_data_event.clear()
                self.pause_data_event.wait()
            start_time = time.perf_counter_ns()
            frame_ids = self.active_microscope.camera.get_new_frame()
            # if there is at least one frame available
            if not frame_ids:
                self.logger.debug(
                    f"Frame not received. Waiting {wait_num}"
                    f"/{self.camera_wait_iterations} iterations"
                )
                wait_num -= 1
                if wait_num <= 0:
                    error_statement = (
                        "Acquisition aborted due to camera time out "
                        "error. Please verify that the external "
                        "trigger is connected and configured properly."
                    )

                    self.logger.debug(error_statement)
                    print(error_statement)
                    break
                continue

            duration = time.perf_counter_ns() - start_time
            self.logger.performance(
                json.dumps(
                    {
                        "kind": "Acquire Image",
                        "duration_ns": duration,
                        "timestamp": time.time(),
                    }
                )
            )

            # Accumulate duration for frame rate calculation
            accumulated_durations_ns.append(duration)

            # Send frame rate to GUI at ~10 Hz max
            current_time_ns = time.perf_counter_ns()
            if current_time_ns - last_frame_rate_update_ns >= frame_rate_update_interval_ns:
                if accumulated_durations_ns:
                    avg_duration_ns = sum(accumulated_durations_ns) / len(accumulated_durations_ns)
                    if avg_duration_ns > 0:
                        frame_rate = 1e9 / avg_duration_ns
                        self.event_queue.put(("frame_rate", frame_rate))
                    accumulated_durations_ns.clear()
                last_frame_rate_update_ns = current_time_ns

            acquired_frame_num += len(frame_ids)

            wait_num = self.camera_wait_iterations

            # ImageWriter to save images
            if data_func:
                data_func(frame_ids)

            if hasattr(self, "data_container") and not self.data_container.end_flag:
                if self.data_container.is_closed:
                    self.logger.info("Data container is closed.")
                    self.stop_acquisition = True
                    break

                self.data_container.run(frame_ids)

            # show image
            self.logger.info(f"Sending image to the controller: {frame_ids[-1]}")
            self.show_img_pipe.send(frame_ids[-1])

            if count_frame and acquired_frame_num >= num_of_frames:
                self.logger.info("Loop stop condition met.")
                self.stop_acquisition = True

        self.show_img_pipe.send("stop")
        self.logger.info("Data thread stopped.")
        self.logger.info(f"Received frames in total: {acquired_frame_num}")

        # release the lock when the data thread ends
        if self.pause_data_ready_lock.locked():
            self.pause_data_ready_lock.release()

        self.end_acquisition()  # Need this to turn off the lasers/close the shutters

    def pause_data_thread(self) -> None:
        """Pause the data thread.

        Function is called when user pauses the acquisition.

        Returns
        -------
        None
            Execution pauses until resume_data_thread() is called.
        """
        if not self.is_data_thread_on:
            return
        self.pause_data_ready_lock.acquire()
        self.ask_to_pause_data_thread = True
        self.pause_data_ready_lock.acquire()

    def resume_data_thread(self) -> None:
        """Resume the data thread.

        Function is called when the user resumes the acquisition.

        Returns
        -------
        None
            Execution continues after pause.
        """
        if not self.is_data_thread_on:
            return
        self.ask_to_pause_data_thread = False
        self.pause_data_event.set()
        if self.pause_data_ready_lock.locked():
            self.pause_data_ready_lock.release()

    def simplified_data_process(
        self,
        microscope: Microscope,
        show_img_pipe: multiprocessing.Pipe,
        data_func: callable = None,
    ) -> None:
        """Run the data process.

        Parameters
        ----------
        microscope : Microscope
            Instance of the Microscope object.
        show_img_pipe : multiprocessing.Pipe
            The pipe for delivering images to the Controller.
        data_func : callable
            Function to run on the acquired data.

        Returns
        -------
        None
            Terminates when acquisition stops.
        """

        acquired_frame_num = 0

        while not self.stop_acquisition:
            frame_ids = (
                microscope.camera.get_new_frame()
            )  # This is the 500 ms wait for Hamamatsu
            self.logger.info(
                f"Running data process, getting frames {frame_ids} from "
                f"{microscope.microscope_name}"
            )
            # if there is at least one frame available
            if not frame_ids:
                continue

            # Leave it here for now to work with the current ImageWriter workflow
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
        self.logger.info("Data thread stopped.")
        self.logger.info(f"Received frames in total: {acquired_frame_num}")

    def prepare_acquisition(self, turn_off_flags: bool = True) -> bool:
        """Prepare the acquisition.

        This function is called when the user starts the acquisition, sets flags,
        calculates all the waveforms, sets the Camera Sensor Mode, initializes the
        data buffer and starts the cameras, and opens Shutters.

        Parameters
        ----------
        turn_off_flags : bool
            Turn off the flags.

        Returns
        -------
        bool
            Was the preparation successful?
        """
        # turn off flags
        if turn_off_flags:
            self.stop_acquisition = False
            self.stop_send_signal = False
            self.injected_flag.value = False
            self.is_live = False
            self.available_image_count = 0
            self.is_data_thread_on = True

        plugin_obj = self.plugin_acquisition_modes.get(self.imaging_mode, None)
        if plugin_obj and hasattr(plugin_obj, "prepare_acquisition_model"):
            getattr(plugin_obj, "prepare_acquisition_model")(self)

        for m in self.virtual_microscopes:
            self.virtual_microscopes[m].prepare_acquisition()

        # Confirm stage position and software are in agreement.
        self.stop_stage()

        # prepare active microscope
        waveform_dict = self.active_microscope.prepare_acquisition()
        if waveform_dict is None:
            return False

        self.event_queue.put(("waveform", waveform_dict))

        self.frame_id = 0
        return True

    def snap_image(self) -> None:
        """Acquire an image after updating the waveforms.

        Can be used in acquisitions where changing waveforms are required,
        but there is additional overhead due to the need to write the
        waveforms into the buffers of the DAQ cards.

        Returns
        -------
        None
            Completes after the image is captured and buffered.
        """
        if hasattr(self, "signal_container"):
            self.signal_container.run()

        # Stash current position, channel, timepoint. Do this here, because signal
        # container functions can inject changes to the stage. NOTE: This line is
        # wildly expensive when get_stage_position() does not cache results.
        start_time = time.perf_counter_ns()
        stage_pos = self.get_stage_position()
        self.data_buffer_positions[self.frame_id][0] = stage_pos.get("x_pos", 0)
        self.data_buffer_positions[self.frame_id][1] = stage_pos.get("y_pos", 0)
        self.data_buffer_positions[self.frame_id][2] = stage_pos.get("z_pos", 0)
        self.data_buffer_positions[self.frame_id][3] = stage_pos.get("theta_pos", 0)
        self.data_buffer_positions[self.frame_id][4] = stage_pos.get("f_pos", 0)
        self.logger.performance(
            json.dumps(
                {
                    "kind": "Stage Position",
                    "duration_ns": time.perf_counter_ns() - start_time,
                    "timestamp": time.time(),
                }
            )
        )

        # Run the acquisition
        start_time = time.perf_counter_ns()
        try:
            self.active_microscope.turn_on_laser()
            self.active_microscope.daq.run_acquisition(
                wait_until_done=self.is_data_thread_on
            )
            if not self.is_data_thread_on:
                if self.available_image_count > 0:
                    self.grab_image(getattr(self.image_writer, "save_image", None))
                self.active_microscope.daq.wait_acquisition_done()
        except:  # noqa
            self.active_microscope.daq.stop_acquisition()
            if self.active_microscope.current_channel == 0:
                self.stop_acquisition = True
                self.event_queue.put(
                    (
                        "warning",
                        "An error happened. Please read the log files for details!",
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

        self.logger.performance(
            json.dumps(
                {
                    "kind": "DAQ Triggers",
                    "duration_ns": time.perf_counter_ns() - start_time,
                    "timestamp": time.time(),
                }
            )
        )

        self.available_image_count += 1

        if hasattr(self, "signal_container"):
            self.signal_container.run(wait_response=True)

        self.frame_id = (self.frame_id + 1) % self.number_of_frames

    def grab_image(self, data_func: Optional[callable] = None) -> None:
        """Grab one image from the camera.

        Parameters
        ----------
        data_func : Optional[callable]
            Function to run on the acquired data. Default is None.
        """
        wait_num = self.camera_wait_iterations

        while not self.stop_acquisition:
            frame_ids = self.active_microscope.camera.get_new_frame()
            self.logger.info(f"Running data process, getting frames {frame_ids}")
            # if there is at least one frame available
            if not frame_ids:
                self.logger.debug(
                    f"Frame not received. Waiting {wait_num}"
                    f"/{self.camera_wait_iterations} iterations"
                )
                wait_num -= 1
                if wait_num <= 0:
                    error_statement = (
                        "Acquisition aborted due to camera time out "
                        "error. Please verify that the external "
                        "trigger is connected and configured properly."
                    )

                    self.logger.debug(error_statement)
                    print(error_statement)
                    break
                continue

            wait_num = self.camera_wait_iterations

            # ImageWriter to save images
            if data_func:
                data_func(frame_ids)

            if hasattr(self, "data_container") and not self.data_container.end_flag:
                if self.data_container.is_closed:
                    self.logger.info("Data container is closed.")
                    self.stop_acquisition = True
                    break

                self.data_container.run(frame_ids)

            # show image
            self.logger.info(f"Image delivered to controller: {frame_ids[0]}")
            self.show_img_pipe.send(frame_ids[-1])

            self.available_image_count -= len(frame_ids)

            break

    def run_live_acquisition(self) -> None:
        """Stream live image to the GUI.

        Recalculates the waveforms for each image, thereby allowing people to adjust
        acquisition parameters in real-time.

        Returns
        -------
        None
            Terminates when live acquisition is stopped.
        """
        self.stop_acquisition = False
        while not self.stop_acquisition and not self.stop_send_signal:
            self.run_acquisition()
            if self.injected_flag.value:
                self.reset_feature_list()
            elif hasattr(self, "signal_container"):
                self.signal_container.reset()

        # Update the stage position.
        # Allows the user to externally move the stage in the continuous mode.
        self.get_stage_position()

    def run_acquisition(self) -> None:
        """Run acquisition along with a feature list one time.

        Returns
        -------
        None
            Completes after acquisition pass ends.
        """
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
                self.logger.info("Signal container is closed.")
                self.stop_acquisition = True
                return
        if not self.is_data_thread_on:
            if self.available_image_count > 0:
                self.grab_image(getattr(self.image_writer, "save_image", None))
            self.show_img_pipe.send("stop")
        if self.imaging_mode != "live":
            self.stop_acquisition = True

        if not self.is_data_thread_on:
            self.end_acquisition()

    def reset_feature_list(self) -> None:
        """Reset live mode feature list."""
        with self.injected_flag as injected_flag:
            # wait for the data thread to end
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
                            "args": ("channels",),
                        },
                    )
                ],
            )
            injected_flag.value = False

    def change_resolution(self, resolution_value: str) -> None:
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
            self.logger.info(
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
            self.logger.debug(
                f"Error changing microscope resolution:"
                f".{self.active_microscope_name} - {e}"
            )

        self.active_microscope.ask_stage_for_position = True

    def get_camera_line_interval_and_exposure_time(
        self, exposure_time: float, number_of_pixel: int
    ) -> Tuple[float, float, float]:
        """Get camera line interval time, light sheet exposure, and full chip exposure
        times.

        Parameters
        ----------
        exposure_time : float
            camera global exposure time
        number_of_pixel: int
            number of pixel in light sheet mode

        Returns
        -------
        camera_times : Tuple[float, float, float]

            - camera_exposure_time : float
                camera exposure time (s)
            - camera_line_interval : float
                camera line interval (s)
            - full_chip_exposure_time : float
                Updated full chip exposure time (s).
        """
        return self.active_microscope.camera.calculate_light_sheet_exposure_time(
            exposure_time, number_of_pixel
        )

    def load_images(self, filenames: Optional[list[str]] = None) -> None:
        """Load/Unload images to the Synthetic Camera

        Parameters
        ----------
        filenames : Optional[list[str]]
            The list of filenames to load.
        """
        self.active_microscope.camera.initialize_image_series(
            self.data_buffer, self.number_of_frames
        )
        self.active_microscope.camera.load_images(filenames)
        self.active_microscope.camera.close_image_series()

    def update_ilastik_setting(
        self,
        display_segmentation: Optional[bool] = False,
        mark_position: Optional[bool] = True,
        target_labels: Optional[list[int]] = [1],
    ) -> None:
        """Update the ilastik setting.

        Parameters
        ----------
        display_segmentation : Optional[bool]
            Display segmentation. Default is False.
        mark_position : Optional[bool]
            Mark position. Default is True.
        target_labels : Optional[list[int]]
            Target labels. Default is [1].
        """
        #: bool: Display segmentation.
        self.display_ilastik_segmentation = display_segmentation

        #: bool: Mark position.
        self.mark_ilastik_position = mark_position

        #: list: Target labels.
        self.ilastik_target_labels = target_labels

    def get_microscope_info(self) -> Dict[str, Any]:
        """Return Microscopes device information.

        Returns
        -------
        microscope_info : Dict[str, Any]
            Microscope device information.
        """
        microscope_info = {}
        for microscope_name in self.microscopes:
            microscope_info[microscope_name] = self.microscopes[microscope_name].info
        return microscope_info

    def launch_virtual_microscope(
        self, microscope_name: str, microscope_config: Dict[str, Any]
    ) -> List[SharedNDArray]:
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
        img_height = self.configuration["experiment"]["CameraParameters"][
            microscope_name
        ]["img_y_pixels"]
        img_width = self.configuration["experiment"]["CameraParameters"][
            microscope_name
        ]["img_x_pixels"]

        # create data buffer
        data_buffer = [
            SharedNDArray(shape=(img_height, img_width), dtype="uint16")
            for _ in range(self.number_of_frames)
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
        microscope.laser = self.microscopes[microscope_name].laser
        microscope.camera = self.microscopes[microscope_name].camera

        # TODO: lasers
        temp = {
            "zoom": "SyntheticZoom",
            "shutter": "SyntheticShutter",
            "remote_focus": "SyntheticRemoteFocus",
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
            elif k.startswith("filter"):
                if microscope_config[k] == "":
                    idx = int(k[k.rfind("_") + 1 :])
                    microscope.filter_wheel[k] = SyntheticFilterWheel(
                        microscope_name, None, self.configuration, idx
                    )
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
        microscope.update_data_buffer(data_buffer, self.number_of_frames)

        # add microscope to self.virtual_microscopes
        self.virtual_microscopes[microscope_name] = microscope
        return data_buffer

    def destroy_virtual_microscope(self, microscope_name: str) -> None:
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

    def terminate(self) -> None:
        """Terminate the model."""
        self.active_microscope.terminate()
        for microscope_name in self.virtual_microscopes:
            self.virtual_microscopes[microscope_name].terminate()

    def load_feature_list_from_file(self, filename: str, features: list[str]) -> None:
        """Append feature list from the file

        Parameters
        ----------
        filename: str
            filename of the feature list.
        features: list[str]
            list of feature names to load from the file.
        """
        module = load_module_from_file(filename[filename.rindex("/") + 1 :], filename)
        for name in features:
            feature = getattr(module, name)
            self.feature_list.append(feature())

    def load_feature_list_from_str(self, feature_list_str: str) -> None:
        """Append feature list from feature_list_str

        Parameters
        ----------
        feature_list_str: str
            the str of a feature list
        """
        self.feature_list.append(convert_str_to_feature_list(feature_list_str))

    def load_feature_records(self) -> None:
        """Load installed feature lists from system folder

        Note
        ----
            System folder can be found at '..../.navigate/feature_lists'
        """
        feature_lists_path = get_navigate_path() + "/feature_lists"
        if not os.path.exists(feature_lists_path):
            os.makedirs(feature_lists_path)
            return
        # get __sequence.yml
        feature_records = load_yaml_file(f"{feature_lists_path}/__sequence.yml")
        if feature_records is None:
            feature_records = []
        # add non-added feature lists
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
            if temp is None:
                continue
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
            if item is None:
                del feature_records[i]
                continue

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

    def get_feature_list(self, idx: int) -> str:
        """Get feature list str by index

        Parameters
        ----------
        idx: int
            index of the feature list

        Returns
        -------
        feature_list_str: str

            - Any empty string if the feature is not found
            - The name of the feature if it is found
        """
        if 0 < idx <= len(self.feature_list):
            return convert_feature_list_to_str(self.feature_list[idx - 1])
        return ""

    def mark_saving_flags(self, frame_ids: list):
        """Mark saving flags for the ImageWriter

        Parameters
        ----------
        frame_ids: list
            a list of frame ids
        """
        if not self.data_buffer_saving_flags:
            return
        for id in frame_ids:
            self.data_buffer_saving_flags[id] = True


class ASIModel(Model):
    """ASI Model class.

    This class is used to control microscopes equipped with the Tiger Controller as
    the DAQ object. Assumes that only one microscope object will be enabled. Tiger
    Controller performs all hardware operations, such as galvos, voice coils,
    analog and digital triggering, etc. Requires a different software architecture
    for control than NI-based daq systems.

    """

    def __init__(
        self,
        args: argparse.Namespace,
        configuration: Optional[Dict[str, Any]] = None,
        event_queue: multiprocessing.Queue = None,
    ) -> None:
        """Initialize the ASI Model.

        Parameters
        ----------
        args : argparse.Namespace
            Command line arguments.
        configuration : Optional[Dict[str, Any]]
            Configuration dictionary. Default is None.
        event_queue : multiprocessing.Queue
            Event queue for communication with the controller. Default is None.

        """
        super().__init__(args, configuration, event_queue)

        self.acquisition_modes_feature_setting["z-stack"] = [
            (
                {"name": ASIZStackAcquisition},
                {"name": StackPause},
                {
                    "name": LoopByCount,
                    "args": ("experiment.MicroscopeState.timepoints",),
                },
            )
        ]

        self.logger.info("ASIModel initialized.")

    def prepare_acquisition(self, turn_off_flags: bool = True) -> bool:
        result = super().prepare_acquisition(turn_off_flags)
        self.active_microscope.daq.zstack = self.imaging_mode == "z-stack"
        self.active_microscope.daq.single = self.imaging_mode == "single"
        return result

    def run_live_acquisition(self) -> None:
        """Stream live image to the GUI.

        Recalculates the waveforms for each image, thereby allowing people to adjust
        acquisition parameters in real-time.

        Returns
        -------
        None
            Terminates when live acquisition is stopped.
        """
        self.stop_acquisition = False
        self.run_acquisition()
        while not self.stop_acquisition and not self.stop_send_signal:
            if self.injected_flag.value:
                self.reset_feature_list()
            elif hasattr(self, "signal_container"):
                self.signal_container.reset()

        # Update the stage position.
        # Allows the user to externally move the stage in the continuous mode.
        self.get_stage_position()

    def run_acquisition(self) -> None:
        """Run acquisition along with a feature list one time.

        Returns
        -------
        None
            Completes after acquisition pass ends.
        """
        if not hasattr(self, "signal_container"):
            self.snap_zstack()
            return

        # The data_thread is grabbing images from the camera.
        # We can initialize the data_thread to grab a certain number of images.
        # Data thread directly hands the images to the ImageWriter, which saves them
        # to disk.

        # Within the run_data_process, which is inside of the data_thread, we call
        # the data_container.

        # The signal thread is running this function iteratively.

        # Launch the signal and data containers, and let them terminate the
        # acquisition when we have received the right number of frames.

        while (
            not self.signal_container.end_flag
            and not self.stop_send_signal
            and not self.stop_acquisition
        ):
            self.logger.debug("in loop")
            self.snap_zstack()
            if not hasattr(self, "signal_container"):
                return
            if self.signal_container.is_closed:
                self.logger.info("Signal container is closed.")
                self.stop_acquisition = True
                return
        if self.imaging_mode != "live":
            self.stop_acquisition = True

    def snap_zstack(self) -> None:
        """Acquire a z-stack after updating the waveforms.

        Can be used in acquisitions where changing waveforms are required,
        but there is additional overhead due to the need to write the
        waveforms into the Tiger Controller.

        Returns
        -------
        None
            Completes after the image is captured and buffered.
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
            self.active_microscope.daq.run_acquisition()
            self.logger.info("ASIModel: Acquisition started.")
        except:  # noqa
            self.active_microscope.daq.stop_acquisition()
            if self.active_microscope.current_channel == 0:
                self.stop_acquisition = True
                self.event_queue.put(
                    (
                        "warning",
                        "An error happened. Please read the log files for details!",
                    )
                )
                return
            self.active_microscope.daq.prepare_acquisition(
                f"channel_{self.active_microscope.current_channel}"
            )
            self.active_microscope.daq.run_acquisition()

        if hasattr(self, "signal_container"):
            self.signal_container.run(wait_response=True)

        self.frame_id = (self.frame_id + 1) % self.number_of_frames
