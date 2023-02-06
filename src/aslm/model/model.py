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

# Third Party Imports

# Local Imports
from aslm.model.concurrency.concurrency_tools import SharedNDArray
from aslm.model.features.autofocus import Autofocus
from aslm.model.features.image_writer import ImageWriter
from aslm.model.features.common_features import (
    ChangeResolution,
    Snap,
    ZStackAcquisition,
    FindTissueSimple2D,
    PrepareNextChannel,
    LoopByCount,
    ConProAcquisition,
)
from aslm.model.features.feature_container import load_features
from aslm.model.features.restful_features import IlastikSegmentation
from aslm.model.features.volume_search import VolumeSearch
from aslm.log_files.log_functions import log_setup
from aslm.tools.common_dict_tools import update_stage_dict
from aslm.model.device_startup_functions import load_devices
from aslm.model.microscope import Microscope


# Logger Setup
p = __name__.split(".")[1]


class Model:
    """ASLM Model Class

    Model for Model-View-Controller Software Architecture.

    Attributes
    ----------
    USE_GPU : bool
        Flag for whether or not to leverage CUDA analysis engine.
    args : str
        ...
    configuration_path : str
        File path for the global configuration of the microscope
    experiment_path : str
        File path for the experiment configuration of the microscope
    event_queue : ...
        ...

    Methods
    -------
    update_data_buffer()
    get_data_buffer()
    create_pipe()
    release_pipe()
    run_command()
    move_stage()
    end_acquisition()
    run_data_process()
    get_readout_time()
    prepare_acquisition()
    run_single_channel_acquisition()
    run_single_acquisition()
    snap_image()
    run_live_acquisition()
    run_z_stack_acquisition()
    run_single_channel_acquisition_with_features()
    """

    def __init__(self, USE_GPU, args, configuration=None, event_queue=None):

        log_setup("model_logging.yml")
        self.logger = logging.getLogger(p)

        # Loads the YAML file for all of the microscope parameters
        self.configuration = configuration

        devices_dict = load_devices(configuration, args.synthetic_hardware)
        self.virtual_microscopes = {}
        self.microscopes = {}
        for microscope_name in configuration["configuration"]["microscopes"].keys():
            self.microscopes[microscope_name] = Microscope(
                microscope_name, configuration, devices_dict, args.synthetic_hardware
            )
        self.active_microscope = None
        self.active_microscope_name = None
        self.get_active_microscope()

        # Acquisition Housekeeping
        self.imaging_mode = None
        self.image_count = 0
        self.acquisition_count = 0
        self.total_acquisition_count = None
        self.total_image_count = None
        self.current_filter = "Empty"
        self.current_laser = "488nm"
        self.current_laser_index = 1
        self.current_exposure_time = 0  # milliseconds
        self.pre_exposure_time = 0  # milliseconds
        self.camera_line_interval = 9.7e-6  # s
        self.start_time = None
        self.data_buffer = None
        self.img_width = int(
            self.configuration["configuration"]["microscopes"][
                self.active_microscope_name
            ]["camera"]["x_pixels"]
        )
        self.img_height = int(
            self.configuration["configuration"]["microscopes"][
                self.active_microscope_name
            ]["camera"]["y_pixels"]
        )
        self.data_buffer_positions = None
        self.is_acquiring = False

        # Autofocusing
        self.f_position = None
        self.max_entropy = None
        self.focus_pos = None

        # Threads
        self.signal_thread = None
        self.data_thread = None

        # show image function/pipe handler
        self.show_img_pipe = None

        # Plot Pipe handler
        self.plot_pipe = None

        # waveform queue
        self.event_queue = event_queue

        # frame signal id
        self.frame_id = 0

        # flags
        self.autofocus_on = False  # autofocus
        self.is_live = False  # need to clear up data buffer after acquisition
        self.is_save = False  # save data
        self.stop_acquisition = False  # stop signal and data threads
        self.stop_send_signal = False  # stop signal thread

        self.pause_data_event = threading.Event()
        self.pause_data_ready_lock = threading.Lock()
        self.ask_to_pause_data_thread = False

        # data buffer for image frames
        self.number_of_frames = self.configuration["experiment"]["CameraParameters"][
            "databuffer_size"
        ]
        self.update_data_buffer(self.img_width, self.img_height)

        # Image Writer/Save functionality
        self.image_writer = None

        # feature list
        # TODO: put it here now
        self.feature_list = []
        # automatically switch resolution
        self.feature_list.append(
            [
                [{"name": ChangeResolution, "args": ("1x",)}, {"name": Snap}],
                [{"name": ChangeResolution, "args": ("high",)}, {"name": Snap}],
            ]
        )
        # z stack acquisition
        self.feature_list.append([{"name": ZStackAcquisition}])
        # threshold and tile
        self.feature_list.append([{"name": FindTissueSimple2D}])
        # Ilastik segmentation
        self.feature_list.append([{"name": IlastikSegmentation}])
        # volume search
        self.feature_list.append([{"name": VolumeSearch}])

        self.acquisition_modes_feature_setting = {
            "single": [{"name": PrepareNextChannel}],
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
                    {
                        "name": LoopByCount,
                        "args": ("experiment.MicroscopeState.timepoints",),
                    },
                )
            ],
            "projection": [{"name": PrepareNextChannel}],
            "confocal-projection": [
                {"name": PrepareNextChannel},
                {"name": ConProAcquisition},
            ],
            "customized": [],
        }

    def update_data_buffer(self, img_width=512, img_height=512):
        """Update the Data Buffer

        Parameters
        ----------
        img_width : int
            Number of active pixels in the x-dimension.
        img_height : int
            Number of active pixels in the y-dimension.
        """
        self.data_buffer = [
            SharedNDArray(shape=(img_height, img_width), dtype="uint16")
            for i in range(self.number_of_frames)
        ]
        self.img_width = img_width
        self.img_height = img_height
        self.data_buffer_positions = SharedNDArray(
            shape=(self.number_of_frames, 5), dtype=float
        )  # z-index, x, y, z, theta, f
        for microscope_name in self.microscopes:
            self.microscopes[microscope_name].update_data_buffer(
                img_width, img_height, self.data_buffer, self.number_of_frames
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
        if img_width != self.img_width or img_height != self.img_height:
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
        logging.info("ASLM Model - Received command from controller:", command, args)
        if not self.data_buffer:
            logging.debug("ASLM Model - Shared Memory Buffer Not Set Up.")
            return

        if command == "acquire":
            self.is_acquiring = True
            self.imaging_mode = self.configuration["experiment"]["MicroscopeState"][
                "image_mode"
            ]
            self.is_save = self.configuration["experiment"]["MicroscopeState"][
                "is_save"
            ]
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
            else:
                self.signal_container, self.data_container = load_features(
                    self, self.acquisition_modes_feature_setting[self.imaging_mode]
                )

            if self.imaging_mode == "single":
                self.configuration["experiment"]["MicroscopeState"][
                    "stack_cycling_mode"
                ] = "per_z"

            if self.imaging_mode == "projection":
                self.move_stage({"z_abs": 0})

            if self.imaging_mode == "live" or self.imaging_mode == "projection":
                self.signal_thread = threading.Thread(target=self.run_live_acquisition)
            else:
                self.signal_thread = threading.Thread(target=self.run_acquisition)

            self.signal_thread.name = f"{self.imaging_mode} signal"
            if self.is_save and self.imaging_mode != "live":
                # self.configuration['experiment']['Saving'] = kwargs['saving_info']
                self.image_writer = ImageWriter(self)
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
                        self, self.virtual_microscopes[m].data_buffer, m
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
            """
            Autofocus Routine
            Args[0] is a dictionary of the microscope state (resolution, zoom, ...)
            Args[1] is a dictionary of the user-defined autofocus parameters:
            {'coarse_range': 500,
            'coarse_step_size': 50,
            'coarse_selected': True,
            'fine_range': 50,
            'fine_step_size': 5,
            'fine_selected': True}
            """
            autofocus = Autofocus(self)
            autofocus.run(*args)

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
                    self.addon_feature = self.feature_list[args[0] - 1]
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

        elif command == "stop":
            """
            Called when user halts the acquisition
            """
            self.logger.info("ASLM Model - Stopping with stop command.")
            self.stop_acquisition = True
            if self.signal_thread:
                self.signal_thread.join()
            if self.data_thread:
                self.data_thread.join()
            self.end_acquisition()

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
        return self.active_microscope.move_stage(pos_dict, wait_until_done)

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

    def end_acquisition(self):
        """End the acquisition.

        Sets the current channel to 0, clears the signal and data containers,
        disconnects buffer in live mode and closes the shutters.
        #
        """
        self.is_acquiring = False

        self.active_microscope.end_acquisition()
        for microscope_name in self.virtual_microscopes:
            self.virtual_microscopes[microscope_name].end_acquisition()

        if hasattr(self, "signal_container"):
            self.signal_container.cleanup()
            delattr(self, "signal_container")
        if hasattr(self, "data_container"):
            self.data_container.cleanup()
            delattr(self, "data_container")
        if self.image_writer is not None:
            self.image_writer.close()

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

        wait_num = 10  # this will let this thread wait 10 * 500 ms before it ends
        acquired_frame_num = 0

        # whether acquire specific number of frames.
        count_frame = num_of_frames > 0

        while not self.stop_acquisition:
            if self.ask_to_pause_data_thread:
                self.pause_data_ready_lock.release()
                self.pause_data_event.clear()
                self.pause_data_event.wait()
            frame_ids = (
                self.active_microscope.camera.get_new_frame()
            )  # This is the 500 ms wait for Hamamatsu
            self.logger.info(
                f"ASLM Model - Running data process, get frames {frame_ids}"
            )
            # if there is at least one frame available
            if not frame_ids:
                self.logger.info(f"ASLM Model - Waiting {wait_num}")
                wait_num -= 1
                if wait_num <= 0:
                    # it has waited for wait_num * 500 ms, it's sure there won't be any
                    # frame coming
                    break
                continue

            wait_num = 10

            # Leave it here for now to work with current ImageWriter workflow
            # Will move it feature container later
            if data_func:
                data_func(frame_ids)

            if hasattr(self, "data_container"):
                if self.data_container.is_closed:
                    self.logger.info("ASLM Model - Data container is closed.")
                    self.stop_acquisition = True
                    break
                self.data_container.run(frame_ids)

            # show image
            self.logger.info(f"ASLM Model - Sent through pipe{frame_ids[0]}")
            self.show_img_pipe.send(frame_ids[0])

            acquired_frame_num += len(frame_ids)
            if count_frame and acquired_frame_num >= num_of_frames:
                self.logger.info("ASLM Model - Loop stop condition met.")
                self.stop_acquisition = True

        self.show_img_pipe.send("stop")
        self.logger.info("ASLM Model - Data thread stopped.")
        self.logger.info(f"ASLM Model - Received frames in total: {acquired_frame_num}")

        # release the lock when data thread ends
        if self.pause_data_ready_lock.locked():
            self.pause_data_ready_lock.release()

        self.end_acquisition()  # Need this to turn off the lasers/close the shutters

    def pause_data_thread(self):
        """Pause the data thread.

        This function is called when user pauses the acquisition.
        """

        self.pause_data_ready_lock.acquire()
        self.ask_to_pause_data_thread = True
        self.pause_data_ready_lock.acquire()

    def resume_data_thread(self):
        """Resume the data thread.

        This function is called when user resumes the acquisition.
        """

        self.ask_to_pause_data_thread = False
        self.pause_data_event.set()
        if self.pause_data_ready_lock.locked():
            self.pause_data_ready_lock.release()

    def simplified_data_process(self, microscope, show_img_pipe, data_func=None):
        wait_num = 10  # this will let this thread wait 10 * 500 ms before it ends
        acquired_frame_num = 0

        while not self.stop_acquisition:
            frame_ids = (
                microscope.camera.get_new_frame()
            )  # This is the 500 ms wait for Hamamatsu
            self.logger.info(
                f"ASLM Model - Running data process, get frames {frame_ids} from "
                f"{microscope.microscope_name}"
            )
            # if there is at least one frame available
            if not frame_ids:
                self.logger.info(f"ASLM Model - Waiting {wait_num}")
                wait_num -= 1
                if wait_num <= 0:
                    # it has waited for wait_num * 500 ms, it's sure there won't be any
                    # frame coming
                    break
                continue

            wait_num = 10

            # Leave it here for now to work with current ImageWriter workflow
            # Will move it feature container later
            if data_func:
                data_func(frame_ids)

            # show image
            self.logger.info(
                f"ASLM Model - Sent through pipe{frame_ids[0]} -- "
                f"{microscope.microscope_name}"
            )
            show_img_pipe.send(frame_ids[0])

            acquired_frame_num += len(frame_ids)

        show_img_pipe.send("stop")
        self.logger.info("ASLM Model - Data thread stopped.")
        self.logger.info(f"ASLM Model - Received frames in total: {acquired_frame_num}")

    def prepare_acquisition(self, turn_off_flags=True):
        """Prepare the acquisition.

        This function is called when user starts the acquisition.
        Sets flags, calculates all of the waveforms.
        Sets the Camera Sensor Mode, initializes the data buffer, starts camera,
        and opens shutters
        Sets flags.
        Calculates all of the waveforms.
        Sets the Camera Sensor Mode
        Initializes the data buffer and starts camera.
        Opens Shutters

        Parameters
        ----------
        turn_off_flags : bool
            Turn off the flags.
        """
        # turn off flags
        if turn_off_flags:
            self.stop_acquisition = False
            self.stop_send_signal = False
            self.autofocus_on = False
            self.is_live = False

        for m in self.virtual_microscopes:
            self.virtual_microscopes[m].prepare_acquisition()

        # prepare active microscope
        waveform_dict = self.active_microscope.prepare_acquisition()

        self.event_queue.put(("waveform", waveform_dict))

        self.frame_id = 0

    def snap_image(self):
        """Acquire an image after updating the waveforms.

        Can be used in acquisitions where changing waveforms are required,
        but there is additional overhead due to the need to write the
        waveforms into the buffers of the DAQ cards.

        TODO: Cleanup.
        """
        if hasattr(self, "signal_container"):
            self.signal_container.run()

        #  Initialize, run, and stop the acquisition.
        #  Consider putting below to not block thread.
        # self.active_microscope.daq.prepare_acquisition(
        #     channel_key, self.current_exposure_time
        # )

        # Stash current position, channel, timepoint
        # Do this here, because signal container functions can inject changes
        # to the stage
        self.data_buffer_positions[self.frame_id][0] = self.configuration["experiment"][
            "StageParameters"
        ]["x"]
        self.data_buffer_positions[self.frame_id][1] = self.configuration["experiment"][
            "StageParameters"
        ]["y"]
        self.data_buffer_positions[self.frame_id][2] = self.configuration["experiment"][
            "StageParameters"
        ]["z"]
        self.data_buffer_positions[self.frame_id][3] = self.configuration["experiment"][
            "StageParameters"
        ]["theta"]
        self.data_buffer_positions[self.frame_id][4] = self.configuration["experiment"][
            "StageParameters"
        ]["f"]

        # Run the acquisition
        self.active_microscope.daq.run_acquisition()
        # self.active_microscope.daq.stop_acquisition()

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

    def run_acquisition(self):
        """Run acquisition along with a feature list one time."""
        if not hasattr(self, "signal_container"):
            self.snap_image()
            return

        self.signal_container.reset()

        while (
            not self.signal_container.end_flag
            and not self.stop_send_signal
            and not self.stop_acquisition
        ):
            self.snap_image()
            if not hasattr(self, "signal_container"):
                return
            if self.signal_container.is_closed:
                self.logger.info("ASLM Model - Signal container is closed.")
                self.stop_acquisition = True
                return
        if self.imaging_mode != "live":
            self.stop_acquisition = True

    def change_resolution(self, resolution_value):
        """Switch resolution mode of the microscope.

        Parameters
        ----------
        resolution_value : str
            Resolution mode.
        """
        if resolution_value != self.active_microscope_name:
            former_microscope = self.active_microscope_name
            self.get_active_microscope()
            self.active_microscope.move_stage_offset(former_microscope)

        # update zoom if possible
        try:
            zoom_value = self.configuration["experiment"]["MicroscopeState"]["zoom"]
            self.active_microscope.zoom.set_zoom(zoom_value)
            self.logger.debug(
                f"Change zoom of {self.active_microscope_name} to {zoom_value}"
            )
        except ValueError as e:
            self.logger.debug(f"{self.active_microscope_name}: {e}")

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
        self.display_ilastik_segmentation = display_segmentation
        self.mark_ilastik_position = mark_position
        self.ilastik_target_labels = target_labels

    def get_microscope_info(self):
        """Return Microscopes device information"""
        microscope_info = {}
        for microscope_name in self.microscopes:
            microscope_info[microscope_name] = self.microscopes[microscope_name].info
        return microscope_info

    def launch_virtual_microscope(self, microscope_name, microscope_config):
        # create databuffer
        data_buffer = [
            SharedNDArray(shape=(self.img_height, self.img_width), dtype="uint16")
            for i in range(self.number_of_frames)
        ]

        # create virtual microscope
        from aslm.model.devices import (
            SyntheticDAQ,
            SyntheticCamera,  # noqa: F401
            SyntheticGalvo,
            SyntheticFilterWheel,  # noqa: F401
            SyntheticShutter,  # noqa: F401
            SyntheticRemoteFocus,  # noqa: F401
            SyntheticStage,
            SyntheticZoom,  # noqa: F401
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
        data_buffer = self.virtual_microscopes[microscope_name].data_buffer
        del self.virtual_microscopes[microscope_name]
        # delete shared_buffer
        for i in range(self.number_of_frames):
            data_buffer[i].shared_memory.close()
            data_buffer[i].shared_memory.unlink()
        del data_buffer
