"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Standard Library Imports
import time
import threading
import logging
import multiprocessing as mp

# Third Party Imports
import numpy as np

# Local Imports
import aslm.model.aslm_device_startup_functions as startup_functions
from aslm.model.aslm_model_config import Session as session
from aslm.model.concurrency.concurrency_tools import ResultThread, SharedNDArray
from aslm.model.model_features.autofocus import Autofocus
from aslm.model.model_features.aslm_image_writer import ImageWriter
from aslm.log_files.log_functions import log_setup
from aslm.tools.common_dict_tools import update_settings_common, update_stage_dict

# debug
from aslm.model.aslm_debug_model import Debug_Module

# Logger Setup
log_setup('model_logging.yml')
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
    get_camera()
    update_data_buffer()
    get_data_buffer()
    create_pipe()
    release_pipe()
    run_command()
    move_stage()
    end_acquisition()
    run_data_process()
    calculate_number_of_channels()
    load_experiment_file()
    get_readout_time()
    prepare_acquisition()
    run_single_channel_acquisition()
    run_single_acquisition()
    snap_image()
    run_live_acquisition()
    run_z_stack_acquisition()
    run_single_channel_acquisition_with_features()
    open_shutter()
    return_channel_index()
    """
    def __init__(self,
                 USE_GPU,
                 args,
                 configuration_path=None,
                 experiment_path=None,
                 etl_constants_path=None,
                 event_queue=None):

        self.logger = logging.getLogger(p)

        # Specify verbosity
        self.verbose = args.verbose

        # Loads the YAML file for all of the microscope parameters
        self.configuration = session(configuration_path, args.verbose)

        # Loads the YAML file for all of the experiment parameters
        self.experiment = session(experiment_path, args.verbose)

        # Loads the YAML file for all of the ETL constants
        self.etl_constants = session(etl_constants_path, args.verbose)

        # Initialize all Hardware
        if args.synthetic_hardware:
            # If command line entry provided, overwrites the model parameters with synthetic hardware.
            self.configuration.Devices['daq'] = 'SyntheticDAQ'
            self.configuration.Devices['camera'] = 'SyntheticCamera'
            self.configuration.Devices['etl'] = 'SyntheticETL'
            self.configuration.Devices['filter_wheel'] = 'SyntheticFilterWheel'
            self.configuration.Devices['stage'] = 'SyntheticStage'
            self.configuration.Devices['zoom'] = 'SyntheticZoom'
            self.configuration.Devices['shutters'] = 'SyntheticShutter'
            self.configuration.Devices['lasers'] = 'SyntheticLasers'

        # Move device initialization steps to multiple threads
        """
        Each of the below represents self.camera or the respective device
        """
        threads_dict = {
            'filter_wheel': ResultThread(target=startup_functions.start_filter_wheel,
                                         args=(self.configuration, self.verbose,)).start(),

            'zoom': ResultThread(target=startup_functions.start_zoom_servo,
                                 args=(self.configuration, self.verbose,)).start(),

            'stages': ResultThread(target=startup_functions.start_stages,
                                   args=(self.configuration, self.verbose,)).start(),

            'shutter': ResultThread(target=startup_functions.start_shutters,
                                    args=(self.configuration, self.experiment, self.verbose,)).start(),

            'daq': ResultThread(target=startup_functions.start_daq,
                                args=(self.configuration, self.experiment, self.etl_constants, self.verbose,)).start(),

            'laser_triggers': ResultThread(target=startup_functions.start_laser_triggers,
                                           args=(self.configuration, self.experiment, self.verbose,)).start(),
        }

        # Optionally start up multiple cameras
        # TODO: In the event two cameras are on, but we've only requested one, make sure it's the one with the
        #       serial number we want.
        for i in range(int(self.configuration.CameraParameters['number_of_cameras'])):
            threads_dict[f'camera{i}'] = ResultThread(target=startup_functions.start_camera,
                                                      args=(self.configuration,
                                                            self.experiment,
                                                            self.verbose,
                                                            i)).start()
            time.sleep(1.0)

        for k in threads_dict:
            setattr(self, k, threads_dict[k].get_result())

        self.camera = self.get_camera()  # make sure we grab the correct camera for this resolution mode

        # in synthetic_hardware mode, we need to wire up camera to daq
        if args.synthetic_hardware:
            self.daq.set_camera(self.camera)

        # analysis class
        self.analysis = startup_functions.start_analysis(self.configuration,
                                                         self.experiment,
                                                         USE_GPU,
                                                         self.verbose)

        # Acquisition Housekeeping
        self.imaging_mode = None
        self.image_count = 0
        self.acquisition_count = 0
        self.total_acquisition_count = None
        self.total_image_count = None
        self.current_channel = 0
        self.current_filter = 'Empty'
        self.current_laser = '488nm'
        self.current_laser_index = 1
        self.current_exposure_time = 0  # milliseconds
        self.pre_exposure_time = 0  # milliseconds
        self.camera_line_interval = 9.7e-6  # s
        self.start_time = None
        self.data_buffer = None
        self.img_width = int(self.configuration.CameraParameters['x-pixels'])
        self.img_height = int(self.configuration.CameraParameters['y-pixels'])

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
        self.stop_acquisition = False # stop signal and data threads
        self.stop_send_signal = False # stop signal thread

        # timing - Units in milliseconds.
        self.camera_minimum_waiting_time = self.camera.get_minimum_waiting_time()
        # self.trigger_waiting_time = 10
        # self.pre_trigger_time = 0

        # data buffer for image frames
        self.number_of_frames = self.configuration.SharedNDArray['number_of_frames']
        self.update_data_buffer(self.img_width, self.img_height)

        # debug
        self.debug = Debug_Module(self, self.verbose)

        # Image Writer/Save functionality
        self.image_writer = ImageWriter(self)

    def get_camera(self):
        r"""Select active camera.

        Get the currently-used camera, in the event there are multiple cameras.
        Find the camera with the matching serial number for the current resolution mode.

        Returns
        -------
        object
            Camera object for current resolution mode.
        """

        # Default to the zeroth camera
        cam = self.camera

        # TODO: In the event two cameras are on, but we've only requested one, make sure it's the one with the
        #       serial number we want.
        # If we have multiple cameras, loop through them all and check their serial numbers
        n_cams = int(self.configuration.CameraParameters['number_of_cameras'])
        if n_cams > 1:
            # Grab the camera with the serial number that matches for the current resolution mode, as specified in
            # configuration.yaml
            sn = self.configuration.CameraParameters[f"{self.experiment.MicroscopeState['resolution_mode']}_serial_number"]
            for i in range(n_cams):
                curr_cam = getattr(self, f'camera{i}')
                if str(sn) == str(curr_cam.serial_number):
                    cam = curr_cam
                    break

        return cam

    def update_data_buffer(self, img_width=512, img_height=512):
        r"""Update the Data Buffer

        Parameters
        ----------
        img_width : int
            Number of active pixels in the x-dimension.
        img_height : int
            Number of active pixels in the y-dimension.
        """
        if self.camera.is_acquiring:
            self.camera.close_image_series()
        self.camera.set_ROI(img_width, img_height)
        self.data_buffer = [SharedNDArray(shape=(img_height, img_width),
                                          dtype='uint16') for i in range(self.number_of_frames)]
        self.img_width = img_width
        self.img_height = img_height

    def get_data_buffer(self, img_width=512, img_height=512):
        r"""Get the data buffer.

        If the number of active pixels in x and y changes, updates the data buffer and returns in.

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
        r"""Create a data pipe.

        Creates a pair of connection objects connected by a pipe which by default is duplex (two-way)

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
        r"""Close a data pipe.

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

    def run_command(self, command, *args, **kwargs):
        r"""Receives commands from the controller.

        Parameters
        ----------
        command : str
            Type of command to run.  Can be 'single', 'live', 'z-stack', 'projection', 'update_setting'
            'autofocus', 'stop', and 'debug'.
        *args : str
            ...
        **kwargs : str
            ...
        """
        logging.info(f"ASLM Model - Received command from controller: {command}, {args}")
        if not self.data_buffer:
            logging.debug("ASLM Model Error: The Shared Memory Buffer Has Not Been Set Up.")
            return

        if command == 'single':
            r"""Acquire a single image.
            
            First overwrites the model instance of the MicroscopeState
            """
            self.imaging_mode = 'single'
            self.experiment.MicroscopeState = kwargs['microscope_info']
            self.experiment.CameraParameters = kwargs['camera_info']
            self.is_save = self.experiment.MicroscopeState['is_save']
            self.prepare_acquisition()
            self.run_single_acquisition()
            channel_num = len(self.experiment.MicroscopeState['channels'].keys())

            if self.is_save:
                self.experiment.Saving = kwargs['saving_info']
                self.run_data_process(channel_num, data_func=self.image_writer.save_image)

            else:
                self.run_data_process(channel_num)
            self.end_acquisition()

        elif command == 'live':
            r"""Live Acquisition Mode"""
            self.imaging_mode = 'live'
            self.experiment.MicroscopeState = kwargs['microscope_info']
            self.experiment.CameraParameters = kwargs['camera_info']
            self.is_save = False
            self.prepare_acquisition()
            self.is_live = True
            self.signal_thread = threading.Thread(target=self.run_live_acquisition)
            self.signal_thread.name = "Live Mode Signal"
            self.data_thread = threading.Thread(target=self.run_data_process)
            self.data_thread.name = "Live Mode Data"
            self.signal_thread.start()
            self.data_thread.start()

        elif command == 'z-stack':
            self.imaging_mode = 'z-stack'
            self.experiment.MicroscopeState = kwargs['microscope_info']
            self.experiment.CameraParameters = kwargs['camera_info']
            self.is_save = self.experiment.MicroscopeState['is_save']
            self.prepare_acquisition()
            self.signal_thread = threading.Thread(target=self.run_z_stack_acquisition)
            self.signal_thread.name = "Z-Stack Signal"
            n_frames = len(self.experiment.MicroscopeState['channels'].keys()) \
                       * int(self.experiment.MicroscopeState['number_z_steps']) \
                       * int(self.experiment.MicroscopeState['timepoints'])

            if self.is_save:
                self.experiment.Saving = kwargs['saving_info']
                self.data_thread = threading.Thread(target=self.run_data_process, kwargs={'num_of_frames': n_frames,
                                                                                          'data_func': self.image_writer.save_image})
            else:
                self.data_thread = threading.Thread(target=self.run_data_process, kwargs={'num_of_frames': n_frames})
            self.data_thread.name = "Z-Stack Data"
            self.signal_thread.start()
            self.data_thread.start()
            # self.end_acquisition()

        elif command == 'projection':
            self.imaging_mode = 'projection'
            pass

        elif command == 'update_setting':
            """
            Called by the controller
            Passes the string 'resolution' and a dictionary
            consisting of the resolution_mode, the zoom, and the laser_info.
            e.g., self.resolution_info.ETLConstants[self.resolution][self.mag]
            """
            reboot = False
            if self.camera.is_acquiring:
                # We called this while in the middle of an acquisition
                # stop live thread
                self.stop_send_signal = True
                self.signal_thread.join()
                self.current_channel = 0
                reboot = True

            update_settings_common(self, args)

            self.daq.calculate_all_waveforms(self.experiment.MicroscopeState, self.etl_constants,
                                             self.experiment.GalvoParameters, self.get_readout_time())
            self.event_queue.put(('waveform', self.daq.waveform_dict))

            if reboot:
                # prepare devices based on updated info
                self.stop_send_signal = False
                self.signal_thread = threading.Thread(target=self.run_live_acquisition)
                self.signal_thread.name = "ETL Popup Signal"
                self.signal_thread.start()

        elif command == 'autofocus':
            """
            Autofocus Routine
            Args[0] is a dictionary of the microscope state (resolution, mode, zoom, ...)
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
            
        elif command == 'stop':
            """
            Called when user halts the acquisition
            """
            self.stop_acquisition = True
            if self.signal_thread:
                self.signal_thread.join()
            if self.data_thread:
                self.data_thread.join()
            self.end_acquisition()

        elif command == 'debug':
            """
            Debug Operation Mode
            """
            self.debug.debug(*args, **kwargs)

    def move_stage(self, pos_dict, wait_until_done=False):
        r"""Moves the stages.

        Updates the stage dictionary, moves to the desired position, and reports the position.

        Parameters
        ----------
        pos_dict : dict
            Dictionary of stage positions.
        wait_until_done : bool
            Checks "on target state" after command and waits until done.
        """
        # Update our local experiment parameters
        update_stage_dict(self, pos_dict)
        self.stages.move_absolute(pos_dict, wait_until_done)
        self.stages.report_position()

        # TODO: This atrribute records current focus position
        # TODO: put it here right now
        self.focus_pos = self.stages.int_position_dict['f_pos']

    def end_acquisition(self):
        r"""End the acquisition.

        Sets the current channel to 0, clears the signal and data containers, disconnects buffer in live mode
        and closes the shutters.
        #
        """
        self.current_channel = 0
        if hasattr(self, 'signal_container'):
            delattr(self, 'signal_container')
        if hasattr(self, 'data_container'):
            delattr(self, 'data_container')
        if self.camera.is_acquiring:
            self.camera.close_image_series()
        self.shutter.close_shutters()

    def run_data_process(self, num_of_frames=0, data_func=None):
        r"""Run the data process.

        This function is the structure of data thread.

        Parameters
        ----------
        num_of_frames : int
            ...
        data_func : object
            Function to run on the acquired data.
        """

        wait_num = 10  # this will let this thread wait 10 * 500 ms before it ends
        acquired_frame_num = 0

        # whether acquire specific number of frames.
        count_frame = num_of_frames > 0

        while not self.stop_acquisition:
            frame_ids = self.camera.get_new_frame()  # This is the 500 ms wait for Hamamatsu
            self.logger.info(f'ASLM Model - Running data process, get frames {frame_ids}')
            # if there is at least one frame available
            if not frame_ids:
                wait_num -= 1
                if wait_num <= 0:
                    # it has waited for wait_num * 500 ms, it's sure there won't be any frame coming
                    break
                continue

            wait_num = 10

            # Leave it here for now to work with current ImageWriter workflow
            # Will move it feature container later
            if data_func:
                data_func(frame_ids)
            
            if hasattr(self, 'data_container'):
                self.data_container.run(frame_ids)

            # show image
            self.logger.info(f'ASLM Model - Sent through pipe{frame_ids[0]}')
            self.show_img_pipe.send(frame_ids[0])

            acquired_frame_num += len(frame_ids)
            if count_frame and acquired_frame_num >= num_of_frames:
                self.stop_acquisition = True
        
        self.show_img_pipe.send('stop')
        self.logger.info('ASLM Model - Data thread stopped.')
        self.logger.info(f'ASLM Model - Received frames in total: {acquired_frame_num}')

    def calculate_number_of_channels(self):
        r"""Calculates the total number of channels selected."""
        return len(self.experiment.MicroscopeState['channels'])

    def load_experiment_file(self, experiment_path):
        r"""Load the experiment YAML file.

        Loads the YAML file for all of the experiment parameters

        Parameters
        ----------
        experiment_path : str
            File path to non-default experiment file.
        """
        self.experiment = session(experiment_path, self.verbose)

    def get_readout_time(self):
        r"""Get readout time from caamera.

        Get the camera readout time if we are in normal mode.
        Return a -1 to indicate when we are not in normal mode.
        This is needed in daq.calculate_all_waveforms()

        Returns
        -------
        readout_time : float
            Camera readout time in seconds or -1 if not in Normal mode.
        """
        readout_time = 0
        if self.experiment.CameraParameters['sensor_mode'] == 'Normal':
            readout_time = self.camera.camera_controller.get_property_value("readout_time")
        return readout_time

    def prepare_acquisition(self):
        r"""Prepare the acquisition.

        Sets flags, calculates all of the waveforms.
        Sets the Camera Sensor Mode, initializes the data buffer, starts camera, and opens shutters
        """
        if self.camera.is_acquiring:
            self.camera.close_image_series()

        # turn off flags
        self.stop_acquisition = False
        self.stop_send_signal = False
        self.autofocus_on = False
        self.is_live = False
        self.frame_id = 0

        # Calculate Waveforms for all channels. Plot in the view.
        waveform_dict = self.daq.calculate_all_waveforms(self.experiment.MicroscopeState,
                                                         self.etl_constants,
                                                         self.experiment.GalvoParameters,
                                                         self.get_readout_time())
        self.event_queue.put(('waveform', waveform_dict))

        # Set Camera Sensor Mode - Must be done before camera is initialized.
        self.camera.set_sensor_mode(self.experiment.CameraParameters['sensor_mode'])
        if self.experiment.CameraParameters['sensor_mode'] == 'Light-Sheet':
            self.camera.set_readout_direction(self.experiment.CameraParameters['readout_direction'])

        # Initialize Image Series - Attaches camera buffer and start imaging
        self.camera.initialize_image_series(self.data_buffer,
                                            self.number_of_frames)
        self.open_shutter()

    def run_single_channel_acquisition(self, target_channel=None):
        r"""Acquire a single channel.

        Updates MicroscopeState dictionary.
        Changes the filter wheel position.
        Configures the camera mode and exposure time.
        Mixed modulation control of laser intensity.

        Parameters
        ----------
        target_channel : int
            Index of channel to acquire.

        """
        # stop acquisition if no channel specified
        if target_channel is None:
            self.stop_acquisition = True
            return

        # Confirm that target channel exists
        channel_key = 'channel_' + str(target_channel)
        if target_channel != self.current_channel:
            microscope_state = self.experiment.MicroscopeState
            if channel_key not in microscope_state['channels'] \
                    or not microscope_state['channels'][channel_key]['is_selected']:
                if self.imaging_mode != 'z-stack':
                    self.stop_acquisition = True
                return

            # Update Microscope State Dictionary
            channel = microscope_state['channels'][channel_key]
            self.current_channel = target_channel

            # Filter Wheel Settings.
            self.filter_wheel.set_filter(channel['filter'])

            # Camera Settings
            self.current_exposure_time = channel['camera_exposure_time']
            if self.experiment.CameraParameters['sensor_mode'] == 'Light-Sheet':
                self.current_exposure_time, self.camera_line_interval = self.camera.calculate_light_sheet_exposure_time(
                    self.current_exposure_time,
                    int(self.experiment.CameraParameters['number_of_pixels']))
                self.camera.camera_controller.set_property_value("internal_line_interval", self.camera_line_interval)

            # Laser Settings
            self.current_laser_index = channel['laser_index']
            self.laser_triggers.trigger_digital_laser(self.current_laser_index)
            self.laser_triggers.set_laser_analog_voltage(channel['laser_index'], channel['laser_power'])

            # ETL Settings
            self.daq.update_etl_parameters(microscope_state,
                                           channel,
                                           self.experiment.GalvoParameters,
                                           self.get_readout_time())

            # Defocus Settings
            curr_focus = self.experiment.StageParameters['f']
            self.move_stage({'f_abs': curr_focus + float(channel['defocus'])}, wait_until_done=True)
            self.experiment.StageParameters['f'] = curr_focus  # do something very hacky so we keep using the same focus reference

        self.snap_image(channel_key)

    def run_single_acquisition(self):
        r"""Run a single acquisition.

        Called by model.run_command().
        target_channel called only during the autofocus routine.
        """

        #  Get the Experiment Settings
        microscope_state = self.experiment.MicroscopeState
        prefix_len = len('channel_')
        for channel_key in microscope_state['channels']:
            if self.stop_acquisition or self.stop_send_signal:
                break
            channel_idx = int(channel_key[prefix_len:])
            self.run_single_channel_acquisition(channel_idx)

    def snap_image(self, channel_key):
        r"""Acquire an image after updating the waveforms.

        Can be used in acquisitions where changing waveforms are required,
        but there is additional overhead due to the need to write the
        waveforms into the buffers of the DAQ cards.

        TODO: Cleanup.

        Parameters
        ----------
        channel_key : int
            Channel index to acquire.

        """
        if hasattr(self, 'signal_container'):
            self.signal_container.run()

        # calculate how long has been since last trigger
        # time_spent = time.perf_counter() - self.pre_trigger_time

        # if time_spent < self.trigger_waiting_time:
        #     if self.verbose:
        #         print('Need to wait!!!! Camera is not ready to be triggered!!!!')
        #     #TODO: we may remove additional 0.001 waiting time
        #     time.sleep(self.trigger_waiting_time - time_spent + 0.001)

        # Camera Settings - Exposure Time in Milliseconds
        # only set exposure time after the previous trigger has been done.
        if self.pre_exposure_time != self.current_exposure_time:
            # In order to change exposure time, we need to stop the camera
            # if self.camera.camera_controller.is_acquiring:
            #     self.camera.close_image_series()
            self.camera.set_exposure_time(self.current_exposure_time)
            # cam_exposure_time = self.camera.camera_controller.get_property_value('exposure_time')
            self.pre_exposure_time = self.current_exposure_time
            # And then re-set it
            # self.camera.initialize_image_series(self.data_buffer, self.number_of_frames)

        # get time when send out the trigger
        # self.pre_trigger_time = time.perf_counter()

        #  Initialize, run, and stop the acquisition.
        #  Consider putting below to not block thread.
        self.daq.prepare_acquisition(channel_key,
                                     self.current_exposure_time)

        # Run the acquisition
        self.daq.run_acquisition()
        self.daq.stop_acquisition()

        self.frame_id = (self.frame_id + 1) % self.number_of_frames

        if hasattr(self, 'signal_container'):
            self.signal_container.run(wait_response=True)

    def run_live_acquisition(self):
        r"""Stream live image to the GUI.

         Recalculates the waveforms for each image, thereby allowing people to adjust
         acquisition parameters in real-time.
        """
        self.stop_acquisition = False
        while self.stop_acquisition is False and self.stop_send_signal is False:
            self.run_single_acquisition()

    def run_z_stack_acquisition(self):
        r"""Acquire a z-stack."""

        microscope_state = self.experiment.MicroscopeState
        stack_cycling_mode = microscope_state['stack_cycling_mode']

        # TODO: Make relative to stage coordinates.
        self.stages.report_position()  # Update current position
        restore_z = self.stages.z_pos

        # z-positions
        stack_z_origin = float(microscope_state.get('stack_z_origin', self.experiment.StageParameters['z']))
        z_pos = np.linspace(float(microscope_state['start_position']) + stack_z_origin,
                            float(microscope_state['end_position']) + stack_z_origin,
                            int(microscope_state['number_z_steps']))

        # corresponding focus positions
        stack_focus_origin = float(microscope_state.get('stack_focus_origin', self.experiment.StageParameters['f']))
        f_pos = np.linspace(float(microscope_state['start_focus']) + stack_focus_origin,
                            float(microscope_state['end_focus']) + stack_focus_origin,
                            int(microscope_state['number_z_steps']))

        if stack_cycling_mode == 'per_stack':
            # Only change the channel we're looking at once per z-stack
            chans = microscope_state['channels']
            active_channels = [k for k in chans if chans[k]['is_selected'] is True]
        elif stack_cycling_mode == 'per_z':
            # Regular, pass nonsense
            active_channels = ['sdasdasd']
        else:
            logging.debug(f"ASLM Model - Unknown stack cycling mode: {stack_cycling_mode}.")
            return

        # For each moment in time...
        for t in range(int(microscope_state['timepoints'])):
            if self.stop_acquisition:
                break
            # Make sure all the right channels are active...
            for ch in active_channels:
                if self.stop_acquisition:
                    break
                try:
                    # If we have readable active chans (we're in per_stack mode) we turn
                    # on one channel at a time.
                    for ch2 in active_channels:
                        if ch2 != ch:
                            self.experiment.MicroscopeState['channels'][ch2]['is_selected'] = False
                    self.experiment.MicroscopeState['channels'][ch]['is_selected'] = True
                except KeyError:
                    pass

                # And step through z-space...
                for z, f in zip(z_pos, f_pos):
                    if self.stop_acquisition:
                        break
                    self.move_stage({'z_abs': z}, wait_until_done=True)  # Update positions
                    self.move_stage({'f_abs': f}, wait_until_done=True)
                    self.run_single_acquisition()  # This will take pics of all active channels

        # Restore active channels. TODO: Is this necessary?
        for ch in active_channels:
            try:
                self.experiment.MicroscopeState['channels'][ch]['is_selected'] = True
            except KeyError:
                pass

        # Restore stage position
        self.move_stage({'z_abs': restore_z}, wait_until_done=True)  # Update position

    def run_single_channel_acquisition_with_features(self, target_channel=1):
        r"""Acquire data with ...

        Parameters
        ----------
        target_channel : int
            Desired channel to acquire.

        """
        # if not hasattr(self, 'signal_container'):
        #     self.run_single_channel_acquisition(target_channel)
        #     return
        
        self.signal_container.reset()
        while not self.signal_container.end_flag:
            self.run_single_channel_acquisition(target_channel)
    
    def change_resolution(self, resolution_value):
        r"""Switch resolution mode of the microscope.

        Parameters
        ----------
        resolution_value : str
            'high' for high-resolution mode, and 'low' for low-resolution mode.
        """

        if (self.experiment.MicroscopeState['resolution_mode'] == "low" and resolution_value == 'high')\
           or (self.experiment.MicroscopeState['resolution_mode'] == "high" and resolution_value != 'high'):
            # We're switching cameras

            # We need to set this first for get_camera()
            if resolution_value == 'high':
                self.experiment.MicroscopeState['resolution_mode'] = 'high'
            else:
                self.experiment.MicroscopeState['resolution_mode'] = 'low'

            # We can't keep acquiring if we're switching cameras. For now, simply turn the camera off.
            if self.camera.is_acquiring:
                self.run_command('stop')

            self.camera = self.get_camera()

        if resolution_value == 'high':
            logging.info("ASLM Model - Switching into High-Resolution Mode")
            self.experiment.MicroscopeState['resolution_mode'] = 'high'
            self.laser_triggers.enable_high_resolution_laser()
        else:
            # Can be 0.63, 1, 2, 3, 4, 5, and 6x.
            logging.info(f"ASLM Model - Switching into Low-Resolution Mode. Magnification = {resolution_value}.")
            self.experiment.MicroscopeState['resolution_mode'] = 'low'
            self.experiment.MicroscopeState['zoom'] = resolution_value
            self.zoom.set_zoom(resolution_value)
            self.laser_triggers.enable_low_resolution_laser()

    def open_shutter(self):
        r"""Open the shutter according to the resolution mode.

        Evaluates the experiment parameters and opens the proper shutter.
        'low' is the low-resolution mode of the microscope, or the left shutter.
        'high' is the high-resolution mode of the microscope, or the right shutter.
        """
        resolution_mode = self.experiment.MicroscopeState['resolution_mode']
        if resolution_mode == 'low':
            self.shutter.open_left()
        elif resolution_mode == 'high':
            self.shutter.open_right()
        else:
            logging.debug(f"ASLM Model - Invalid Shutter Command: {resolution_mode}")

    def return_channel_index(self):
        r"""Provide the current channel index.

        Returns
        -------
        current_channel : int
            Index for active channel.
        """
        return self.current_channel

