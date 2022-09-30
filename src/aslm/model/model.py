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
from aslm.model.aslm_model_config import Configurator
from aslm.model.concurrency.concurrency_tools import ResultThread, SharedNDArray
from aslm.model.model_features.autofocus import Autofocus
from aslm.model.model_features.aslm_image_writer import ImageWriter
from aslm.model.model_features.dummy_detective import Dummy_Detective
from aslm.model.model_features.aslm_common_features import *
from aslm.model.model_features.aslm_feature_container import load_features
from aslm.model.model_features.aslm_restful_features import IlastikSegmentation
from aslm.log_files.log_functions import log_setup
from aslm.tools.common_dict_tools import update_settings_common, update_stage_dict
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
    def __init__(self,
                 USE_GPU,
                 args,
                 configuration=None,
                 event_queue=None):

        log_setup('model_logging.yml')
        self.logger = logging.getLogger(p)

        # Loads the YAML file for all of the microscope parameters
        # self.configuration = Configurator(configuration_path)
        self.configuration = configuration

        devices_dict = load_devices(configuration, args.synthetic_hardware)
        self.microscopes = {}
        for microscope_name in configuration['configuration']['microscopes'].keys():
            self.microscopes[microscope_name] = Microscope(microscope_name, configuration, devices_dict, args.synthetic_hardware)
        self.active_microscope = None
        self.active_microscope_name = None
        self.get_active_microscope()

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
        self.img_width = int(self.configuration['configuration']['microscopes'][self.active_microscope_name]['camera']['x_pixels'])
        self.img_height = int(self.configuration['configuration']['microscopes'][self.active_microscope_name]['camera']['y_pixels'])
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
        self.stop_acquisition = False # stop signal and data threads
        self.stop_send_signal = False # stop signal thread

        self.pause_data_event = threading.Event()
        self.pause_data_ready_lock = threading.Lock()
        self.ask_to_pause_data_thread = False

        # data buffer for image frames
        self.number_of_frames = self.configuration['experiment']['CameraParameters']['databuffer_size']
        self.update_data_buffer(self.img_width, self.img_height)

        # Image Writer/Save functionality
        self.image_writer = None

        # feature list
        # TODO: put it here now
        self.feature_list = []
        # automatically switch resolution
        self.feature_list.append([[{'name': ChangeResolution, 'args': ('1x',)}, {'name': Snap}], [{'name': ChangeResolution, 'args': ('high',)}, {'name': Snap}]])
        # z stack acquisition
        self.feature_list.append([[{'name': ZStackAcquisition}]])
        # threshold and tile
        self.feature_list.append([[{'name': FindTissueSimple2D}]])
        # Ilastik segmentation
        self.feature_list.append([[{'name': IlastikSegmentation}]])

    def update_data_buffer(self, img_width=512, img_height=512):
        r"""Update the Data Buffer

        Parameters
        ----------
        img_width : int
            Number of active pixels in the x-dimension.
        img_height : int
            Number of active pixels in the y-dimension.
        """
        self.data_buffer = [SharedNDArray(shape=(img_height, img_width),
                                          dtype='uint16') for i in range(self.number_of_frames)]
        self.img_width = img_width
        self.img_height = img_height
        self.data_buffer_positions = SharedNDArray(shape=(self.number_of_frames, 5), dtype=float)  # z-index, x, y, z, theta, f
        for microscope_name in self.microscopes:
            self.microscopes[microscope_name].update_data_buffer(img_width, img_height, self.data_buffer, self.number_of_frames)

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

    def get_active_microscope(self):
        self.active_microscope_name = self.configuration['experiment']['MicroscopeState']['resolution_mode']
        self.active_microscope = self.microscopes[self.active_microscope_name]
        return self.active_microscope

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
        logging.info('ASLM Model - Received command from controller:', command, args)
        if not self.data_buffer:
            logging.debug('ASLM Model - Shared Memory Buffer Not Set Up.')
            return

        if command == 'acquire':
            self.is_acquiring = True
            self.imaging_mode = self.configuration['experiment']['MicroscopeState']['image_mode']
            self.is_save = self.configuration['experiment']['MicroscopeState']['is_save']
            self.prepare_acquisition()
            # load features
            # TODO: put it here now.
            if self.imaging_mode == 'z-stack':
                self.signal_container, self.data_container = load_features(self, [[{'name': ZStackAcquisition}]])
            
            if self.imaging_mode == 'single':
                self.configuration['experiment']['MicroscopeState']['stack_cycling_mode'] = 'per_z'

            if self.imaging_mode == 'live':
                self.signal_thread = threading.Thread(target=self.run_live_acquisition)
            else:
                self.signal_thread = threading.Thread(target=self.run_acquisition)
            
            self.signal_thread.name = self.imaging_mode + " signal"
            if self.is_save and self.imaging_mode != 'live':
                self.configuration['experiment']['Saving'] = kwargs['saving_info']
                self.image_writer = ImageWriter(self)
                self.data_thread = threading.Thread(target=self.run_data_process, kwargs={'data_func': self.image_writer.save_image})
            else:
                self.is_save = False
                self.data_thread = threading.Thread(target=self.run_data_process)
            self.data_thread.name = self.imaging_mode + " Data"
            self.signal_thread.start()
            self.data_thread.start()

        elif command == 'update_setting':
            """
            Called by the controller
            Passes the string 'resolution' and a dictionary
            consisting of the resolution_mode, the zoom, and the laser_info.
            e.g., self.resolution_info['ETLConstants'][self.resolution][self.mag]
            """
            reboot = False
            if self.is_acquiring:
                # We called this while in the middle of an acquisition
                # stop live thread
                self.stop_send_signal = True
                self.signal_thread.join()
                if args[0] == 'resolution' and args[1] != self.active_microscope_name:
                    self.pause_data_thread()
                    self.active_microscope.end_acquisition()
                    reboot = True
                self.current_channel = 0

            if args[0] == 'resolution':
                self.change_resolution(args[1])
                if reboot:
                    # prepare active microscope
                    waveform_dict = self.active_microscope.prepare_acquisition()
                    self.resume_data_thread()

            if not reboot:
                waveform_dict = self.active_microscope.calculate_all_waveform()
            self.event_queue.put(('waveform', waveform_dict))

            if self.is_acquiring:
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

        elif command == 'load_feature':
            """
            args[0]: int, args[0]-1 is the id of features
                   : 0 no features
            """
            if hasattr(self, 'signal_container'):
                delattr(self, 'signal_container')
                delattr(self, 'data_container')
            
            if args[0] != 0:
                self.signal_container, self.data_container = load_features(self, self.feature_list[args[0]-1])
            
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

    def move_stage(self, pos_dict, wait_until_done=False):
        r"""Moves the stages.

        Updates the stage dictionary, moves to the desired position, and reports the position.

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
        r"""Get the position of the stage.

        Returns
        -------
        ret_pos_dict : dict
            Dictionary of stage positions.
        """
        return self.active_microscope.get_stage_position()

    def stop_stage(self):
        r"""Stop the stages.

        """
        self.active_microscope.stop_stage()

        ret_pos_dict = self.get_stage_position()
        update_stage_dict(self, ret_pos_dict)

    def end_acquisition(self):
        r"""End the acquisition.

        Sets the current channel to 0, clears the signal and data containers, disconnects buffer in live mode
        and closes the shutters.
        #
        """
        self.current_channel = 0
        self.is_acquiring = False
        if hasattr(self, 'signal_container'):
            self.signal_container.cleanup()
            delattr(self, 'signal_container')
        if hasattr(self, 'data_container'):
            self.data_container.cleanup()
            delattr(self, 'data_container')
        if self.image_writer is not None:
            self.image_writer.close()
        
        self.active_microscope.end_acquisition()

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
            if self.ask_to_pause_data_thread:
                self.pause_data_ready_lock.release()
                self.pause_data_event.clear()
                self.pause_data_event.wait()
            frame_ids = self.active_microscope.camera.get_new_frame()  # This is the 500 ms wait for Hamamatsu
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
                if self.data_container.is_closed:
                    self.stop_acquisition = True
                    break
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
        
        # release the lock when data thread ends
        if self.pause_data_ready_lock.locked():
            self.pause_data_ready_lock.release()

        self.end_acquisition()  # Need this to turn off the lasers/close the shutters

    def pause_data_thread(self):
        self.pause_data_ready_lock.acquire()
        self.ask_to_pause_data_thread = True
        self.pause_data_ready_lock.acquire()

    def resume_data_thread(self):
        self.ask_to_pause_data_thread = False
        self.pause_data_event.set()
        self.pause_data_ready_lock.release()

    def prepare_acquisition(self, turn_off_flags=True):
        r"""Prepare the acquisition.

        Sets flags, calculates all of the waveforms.
        Sets the Camera Sensor Mode, initializes the data buffer, starts camera, and opens shutters
        Sets flags.
        Calculates all of the waveforms.
        Sets the Camera Sensor Mode
        Initializes the data buffer and starts camera.
        Opens Shutters
        """
        # turn off flags
        if turn_off_flags:
            self.stop_acquisition = False
            self.stop_send_signal = False
            self.autofocus_on = False
            self.is_live = False

        # prepare active microscope
        waveform_dict = self.active_microscope.prepare_acquisition()

        self.event_queue.put(('waveform', waveform_dict))

        
        self.frame_id = 0


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
        microscope_state = self.configuration['experiment']['MicroscopeState']
        channels = microscope_state['channels']
        if target_channel != self.current_channel:
            if channel_key not in channels \
                    or not channels[channel_key]['is_selected']:
                # if self.imaging_mode != 'z-stack':
                #     self.stop_acquisition = True
                return

            # Update Microscope State Dictionary
            channel = channels[channel_key]
            self.current_channel = target_channel

            self.active_microscope.prepare_channel(channel_key)

            # Defocus Settings
            curr_focus = self.configuration['experiment']['StageParameters']['f']
            self.move_stage({'f_abs': curr_focus + float(channel['defocus'])}, wait_until_done=True)
            self.configuration['experiment']['StageParameters']['f'] = curr_focus  # do something very hacky so we keep using the same focus reference

        # Take the image
        self.snap_image(channel_key)

    def run_single_acquisition(self):
        r"""Run a single acquisition.

        Called by model.run_command().
        target_channel called only during the autofocus routine.
        """

        #  Get the Experiment Settings
        microscope_state = self.configuration['experiment']['MicroscopeState']
        prefix_len = len('channel_')
        for channel_key in microscope_state['channels'].keys():
            if self.stop_acquisition or self.stop_send_signal:
                break
            channel_idx = int(channel_key[prefix_len:])
            self.run_single_channel_acquisition_with_features(channel_idx)

            if self.imaging_mode == 'z-stack':
                break

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

        # Camera Settings - Exposure Time in Milliseconds
        # only set exposure time after the previous trigger has been done.
        if self.pre_exposure_time != self.current_exposure_time:
            # In order to change exposure time, we need to stop the camera
            # if self.camera.camera_controller.is_acquiring:
            #     self.camera.close_image_series()
            self.active_microscope.camera.set_exposure_time(self.current_exposure_time)
            # cam_exposure_time = self.camera.camera_controller.get_property_value('exposure_time')
            self.pre_exposure_time = self.current_exposure_time
            # And then re-set it
            # self.camera.initialize_image_series(self.data_buffer, self.number_of_frames)

        # get time when send out the trigger
        # self.pre_trigger_time = time.perf_counter()

        #  Initialize, run, and stop the acquisition.
        #  Consider putting below to not block thread.
        self.active_microscope.daq.prepare_acquisition(channel_key, self.current_exposure_time)

        # Stash current position, channel, timepoint
        # Do this here, because signal container functions can inject changes to the stage
        self.data_buffer_positions[self.frame_id][0] = self.configuration['experiment']['StageParameters']['x']
        self.data_buffer_positions[self.frame_id][1] = self.configuration['experiment']['StageParameters']['y']
        self.data_buffer_positions[self.frame_id][2] = self.configuration['experiment']['StageParameters']['z']
        self.data_buffer_positions[self.frame_id][3] = self.configuration['experiment']['StageParameters']['theta']
        self.data_buffer_positions[self.frame_id][4] = self.configuration['experiment']['StageParameters']['f']

        # Run the acquisition
        self.active_microscope.daq.run_acquisition()
        self.active_microscope.daq.stop_acquisition()

        if hasattr(self, 'signal_container'):
            self.signal_container.run(wait_response=True)

        self.frame_id = (self.frame_id + 1) % self.number_of_frames

    def run_live_acquisition(self):
        r"""Stream live image to the GUI.

         Recalculates the waveforms for each image, thereby allowing people to adjust
         acquisition parameters in real-time.
        """
        self.stop_acquisition = False
        while self.stop_acquisition is False and self.stop_send_signal is False:
            self.run_single_acquisition()

    def run_acquisition(self):
        r"""Run acquisition along with a feature list one time.
        """
        self.run_single_acquisition()
        # wait a very short time to the data thread to get the last frame
        # TODO: maybe need to adjust
        # time.sleep(0.005)
        self.stop_acquisition = True

    def run_single_channel_acquisition_with_features(self, target_channel=1):
        r"""Acquire data with ...

        Parameters
        ----------
        target_channel : int
            Desired channel to acquire.

        """
        if not hasattr(self, 'signal_container'):
            self.run_single_channel_acquisition(target_channel)
            return
        
        self.signal_container.reset()
        self.target_channel = target_channel

        while not self.signal_container.end_flag and not self.stop_send_signal and not self.stop_acquisition:
            self.run_single_channel_acquisition(self.target_channel)
            if not hasattr(self, 'signal_container'):
                return
            if self.signal_container.is_closed:
                self.stop_acquisition = True
                return
    
    def change_resolution(self, resolution_value):
        r"""Switch resolution mode of the microscope.

        Parameters
        ----------
        resolution_value : str
            'high' for high-resolution mode, and 'low' for low-resolution mode.
        """
        if resolution_value != self.active_microscope_name:
            former_microscope = self.active_microscope_name
            self.get_active_microscope()
            self.active_microscope.move_stage_offset(former_microscope)

    def load_images(self, filenames=None):
        r"""Load/Unload images to the Synthetic Camera
        """
        self.active_microscope.camera.initialize_image_series(self.data_buffer,
                                            self.number_of_frames)
        self.active_microscope.camera.load_images(filenames)
        self.active_microscope.camera.close_image_series()

    def update_ilastik_setting(self, display_segmentation=False, mark_position=True, target_labels=[1]):
        self.display_ilastik_segmentation = display_segmentation
        self.mark_ilastik_position = mark_position
        self.ilastik_target_labels = target_labels
