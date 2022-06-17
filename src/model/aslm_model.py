"""
ASLM Model.

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

# Standard Library Imports
import time
import os
import threading
import platform
import logging
from pathlib import Path

# Third Party Imports
import numpy as np
from queue import Queue
import multiprocessing as mp

# Local Imports
import model.aslm_device_startup_functions as startup_functions
from .aslm_model_config import Session as session
from controller.thread_pool import SynchronizedThreadPool
from model.concurrency.concurrency_tools import ResultThread, SharedNDArray, ObjectInSubprocess
from model.model_features.autofocus import Autofocus
from model.model_features.aslm_image_writer import ImageWriter

# debug
from model.aslm_debug_model import Debug_Module



class Model:
    def __init__(
            self,
            USE_GPU,
            args,
            configuration_path=None,
            experiment_path=None,
            etl_constants_path=None,
            event_queue=None):
        
        # Logger Setup
        from log_files.log_functions import log_setup
        log_setup('model_logging.yml')
        p = __name__.split(".")[0]
        self.logger = logging.getLogger(p)
        
        self.logger.info("Performance - Testing if it works")
        self.logger.debug("Spec - Testing if spec works too")
        self.logger.info("Made it to model")
        
        # Specify verbosity
        self.verbose = args.verbose

        # Loads the YAML file for all of the microscope parameters
        self.configuration = session(configuration_path, args.verbose)

        # Loads the YAML file for all of the experiment parameters
        self.experiment = session(experiment_path, args.verbose)

        # Loads the YAML file for all of the ETL constants
        self.etl_constants = session(etl_constants_path, args.verbose)

        # Initialize all Hardware
        if args.synthetic_hardware or args.sh:
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
        '''
        Each of the below represents self.camera or the respective device
        '''
        threads_dict = {
            'filter_wheel': ResultThread(target=startup_functions.start_filter_wheel,
                                         args=(self.configuration,self.verbose,)).start(),

            'zoom': ResultThread(target=startup_functions.start_zoom_servo,
                                 args=(self.configuration, self.verbose,)).start(),

            'camera': ResultThread(target=startup_functions.start_camera,
                                   args=(self.configuration, self.experiment, self.verbose,)).start(),

            'stages': ResultThread(target=startup_functions.start_stages,
                                   args=(self.configuration,self.verbose,)).start(),

            'shutter': ResultThread(target=startup_functions.start_shutters,
                                    args=(self.configuration, self.experiment, self.verbose,)).start(),

            'daq': ResultThread(target=startup_functions.start_daq,
                                args=(self.configuration, self.experiment, self.etl_constants, self.verbose,)).start(),

            'laser_triggers': ResultThread(target=startup_functions.start_laser_triggers,
                                           args=(self.configuration, self.experiment, self.verbose,)).start(),
        }

        for k in threads_dict:
            setattr(self, k, threads_dict[k].get_result())

        # in synthetic_hardware mode, we need to wire up camera to daq
        if args.synthetic_hardware or args.sh:
            self.daq.set_camera(self.camera)

        # analysis class
        self.analysis = startup_functions.start_analysis(self.configuration, self.experiment, USE_GPU, self.verbose)

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
        self.trigger_waiting_time = 10
        self.pre_trigger_time = 0

        # data buffer for image frames
        self.number_of_frames = self.configuration.SharedNDArray['number_of_frames']
        self.update_data_buffer(int(self.experiment.CameraParameters['x_pixels']),
                                int(self.experiment.CameraParameters['y_pixels']))

        # debug
        self.debug = Debug_Module(self, self.verbose)

    def update_data_buffer(self, img_width=512, img_height=512):
        if self.camera.is_acquiring:
            self.camera.close_image_series()
        self.camera.set_ROI(img_width, img_height)
        self.data_buffer = [SharedNDArray(shape=(img_height, img_width),
                                          dtype='uint16') for i in range(self.number_of_frames)]
        self.img_width = img_width
        self.img_height = img_height

    def get_data_buffer(self, img_width=512, img_height=512):
        if img_width != self.img_width or img_height != self.img_height:
            self.update_data_buffer(img_width, img_height)
        return self.data_buffer

    def create_pipe(self, pipe_name):
        self.release_pipe(pipe_name)
        end1, end2 = mp.Pipe()
        setattr(self, pipe_name, end2)
        return end1

    def release_pipe(self, pipe_name):
        if hasattr(self, pipe_name):
            pipe = getattr(self, pipe_name)
            if pipe:
                pipe.close()
            delattr(self, pipe_name)


    #  Basic Image Acquisition Functions
    #  - These functions are used to acquire images from the camera
    #  - Tasks for delivering analog and digital outputs are already initiated by the DAQ object
    #  - daq.create_waveforms() calculates the waveforms and writes them to tasks.
    #  - daq.start_tasks() starts the tasks, which then wait for an external trigger.
    #  - daq.run_tasks() delivers the external trigger which synchronously starts the tasks and waits for completion.
    #  - daq.stop_tasks() stops the tasks and cleans up.

    def run_command(self, command, *args, **kwargs):
        """
        Receives commands from the controller.
        """
        if self.verbose:
            print('in the model(get the command from controller):', command, args)
        if not self.data_buffer:
            if self.verbose:
                print("Error: The Shared Memory Buffer Has Not Been Set Up.")
            return

        if command == 'single':
            """
            # Acquire a single image.
            # First overwrites the model instance of the MicroscopeState
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
                image_writer = ImageWriter(self)
                # self.run_data_process(channel_num, data_func=image_writer.write_tiff)
                self.run_data_process(channel_num, data_func=image_writer.write_zarr)
            else:
                self.run_data_process(channel_num)
            self.end_acquisition()

        elif command == 'live':
            """
            Live Acquisition Mode
            """
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
            pass

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
            # stop live thread
            self.stop_send_signal = True
            self.signal_thread.join()
            if args[0] == 'channel':
                self.experiment.MicroscopeState['channels'] = args[1]

            if args[0] == 'resolution':
                """
                args[1] is a dictionary that includes 'resolution_mode': 'low', 'zoom': '1x', 'laser_info': ...
                ETL popup window updating the self.etl_constants.
                Passes new self.etl_constants to the self.model.daq
                TODO: Make sure the daq knows which etl data to use based upon wavelength, zoom, resolution mode, etc.
                """
                updated_settings = args[1]
                resolution_mode = updated_settings['resolution_mode']
                zoom = updated_settings['zoom']
                laser_info = updated_settings['laser_info']

                if resolution_mode == 'low':
                    self.etl_constants.ETLConstants['low'][zoom] = laser_info
                else:
                    self.etl_constants.ETLConstants['high'][zoom] = laser_info
                if self.verbose:
                    print(self.etl_constants.ETLConstants['low'][zoom])

                # Modify DAQ to pull the initial values from the etl_constants.yml file, or be passed it from the model.
                # Pass to the self.model.daq to
                #             value = self.resolution_info.ETLConstants[self.resolution][self.mag][laser][etl_name]
                # print(args[1])

            if args[0] == 'galvo':
                (param, value), = args[1].items()
                self.experiment.GalvoParameters[param] = value

            self.daq.calculate_all_waveforms(self.experiment.MicroscopeState, self.etl_constants, self.experiment.GalvoParameters)
            self.event_queue.put(('waveform', self.daq.waveform_dict))

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
            '''
            Debug Operation Mode
            '''
            self.debug.debug(*args, **kwargs)

    def move_stage(self, pos_dict, wait_until_done=False):
        """
        Moves the stages.
        Checks "on target state" after command and waits until done.
        """
        self.stages.move_absolute(pos_dict, wait_until_done)
        self.stages.report_position()


    def end_acquisition(self):
        """
        #
        """
        # dettach buffer in live mode in order to clear unread frames
        if self.camera.camera_controller.is_acquiring:
            self.camera.close_image_series()

        # close shutter
        self.shutter.close_shutters()

    # functions related to send out signals

    # functions related to frame data
    def run_data_process(self, num_of_frames=0, pre_func=None, data_func=None, callback=None):
        """
        # this function is the structure of data thread
        """

        wait_num = 10 # this will let this thread wait 10 * 500 ms before it ends
        acquired_frame_num = 0

        # whether acquire specific number of frames.
        count_frame = num_of_frames > 0

        if pre_func:
            pre_func()

        while not self.stop_acquisition:
            frame_ids = self.camera.get_new_frame()
            self.logger.debug(f'running data process, get frames {frame_ids}')
            # if there is at least one frame available
            if not frame_ids:
                wait_num -= 1
                if wait_num <= 0:
                    # it has waited for wait_num * 500 ms, it's sure there won't be any frame coming
                    break
                continue

            wait_num = 10

            # May need a separate save_func as saving is done before display and other analysis may be after display
            if data_func:
                data_func(frame_ids)

            # show image
            self.logger.debug(f'sent through pipe{frame_ids[0]}')
            self.show_img_pipe.send(frame_ids[0])


            acquired_frame_num += len(frame_ids)
            if count_frame and acquired_frame_num >= num_of_frames:
                self.stop_acquisition = True

        if callback:
            callback()
        
        self.show_img_pipe.send('stop')

        self.logger.debug('data thread is stop')
        self.logger.debug(f'received frames in total:{acquired_frame_num}')


    def prepare_image_series(self):
        """
        #  Prepares an image series without waveform update
        """
        pass
        # self.daq.create_tasks()
        # self.daq.write_waveforms_to_tasks()

    def snap_image_in_series(self):
        """
        # Snaps and image from a series without waveform update
        """
        pass
        # self.daq.start_tasks()
        # self.daq.run_tasks()
        # self.data = self.camera.get_image()
        # self.daq.stop_tasks()

    def close_image_series(self):
        """
        #  Cleans up after series without waveform update
        """
        pass  # self.daq.close_tasks()

    def calculate_number_of_channels(self):
        """
        #  Calculates the total number of channels that are selected.
        """
        return len(self.experiment.MicroscopeState['channels'])

    def prepare_acquisition_list(self):
        """
        #  Calculates the total number of acquisitions, images, etc.  Initializes the counters.
        """
        number_of_channels = self.calculate_number_of_channels()
        number_of_positions = len(
            self.experiment.MicroscopeState['stage_positions'])
        number_of_slices = self.experiment.MicroscopeState['number_z_steps']
        number_of_time_points = self.experiment.MicroscopeState['timepoints']

        self.image_count = 0
        self.acquisition_count = 0
        self.total_acquisition_count = number_of_channels * \
            number_of_positions * number_of_time_points
        self.total_image_count = self.total_acquisition_count * number_of_slices
        self.start_time = time.time()

    def load_experiment_file(self, experiment_path):
        # Loads the YAML file for all of the experiment parameters
        self.experiment = session(experiment_path, self.verbose)

    def prepare_acquisition(self):
        """
        Sets flags.
        Calculates all of the waveforms.
        Sets the Camera Sensor Mode
        Initializes the data buffer and starts camera.
        Opens Shutters
        """
        if self.camera.camera_controller.is_acquiring:
            self.camera.close_image_series()
        # turn off flags
        self.stop_acquisition = False
        self.stop_send_signal = False
        self.autofocus_on = False
        self.is_live = False

        # Calculate Waveforms for all channels. Plot in the view.
        waveform_dict = self.daq.calculate_all_waveforms(self.experiment.MicroscopeState, self.etl_constants, self.experiment.GalvoParameters)
        self.event_queue.put(('waveform', waveform_dict))

        # Set Camera Sensor Mode - Must be done before camera is initialized.
        self.camera.set_sensor_mode(self.experiment.CameraParameters['sensor_mode'])
        if self.experiment.CameraParameters['sensor_mode'] == 'Light-Sheet':
            self.camera.set_readout_direction(self.experiment.CameraParameters['readout_direction'])

        self.frame_id = 0

        # Initialize Image Series - Attaches camera buffer and start imaging
        self.camera.initialize_image_series(self.data_buffer, self.number_of_frames)

        self.open_shutter()

    def run_single_acquisition(self,
                               target_channel=None,
                               snap_func=None):
        """
        # Called by model.run_command().
        target_channel called only during the autofocus routine.
        """

        #  Get the Experiment Settings
        microscope_state = self.experiment.MicroscopeState
        prefix_len = len('channel_')
        for channel_key in microscope_state['channels']:
            if self.stop_acquisition or self.stop_send_signal:
                break
            channel_idx = int(channel_key[prefix_len:])
            if target_channel and channel_idx != target_channel:
                continue
            channel = microscope_state['channels'][channel_key]

            # Iterate through the selected channels.
            if channel['is_selected'] is True:
                # Move the Filter Wheel - Rate-Limiting Step - Perform First.
                self.filter_wheel.set_filter(channel['filter'])

                # Get and set the parameters for Waveform Generation, triggering, etc.
                self.current_channel = channel_idx

                # Calculate duration of time necessary between camera triggers.
                self.trigger_waiting_time = self.current_exposure_time/1000 + self.camera_minimum_waiting_time

                # Update Camera Exposure Time
                self.current_exposure_time = channel['camera_exposure_time']
                if self.experiment.CameraParameters['sensor_mode'] == 'Light-Sheet':
                    self.current_exposure_time, self.camera_line_interval = self.camera.calculate_light_sheet_exposure_time(
                        self.current_exposure_time,
                        int(self.experiment.CameraParameters['number_of_pixels']))
                    self.camera.camera_controller.set_property_value("internal_line_interval", self.camera_line_interval)

                # self.camera.set_exposure_time(exposure_time)

                # Laser Settings
                self.current_laser_index = channel['laser_index']
                self.laser_triggers.trigger_digital_laser(self.current_laser_index)
                self.laser_triggers.set_laser_analog_voltage(channel['laser_index'], channel['laser_power'])

                # # Update Laser Data Acquisition Sweep Time according to exposure and delay parameters.
                # self.daq.sweep_time = (self.current_exposure_time / 1000) * \
                #                       ((self.configuration.CameraParameters['delay_percent'] +
                #                         self.configuration.RemoteFocusParameters['remote_focus_l_ramp_falling_percent']) / 100 + 1)

                # Update ETL Settings
                self.daq.update_etl_parameters(microscope_state, channel, self.experiment.GalvoParameters)

                # Acquire an Image
                if snap_func:
                    snap_func()
                else:
                    self.snap_image(channel_key)


    def snap_image(self, channel_key):
        """
        # Snaps a single image after updating the waveforms.
        # Can be used in acquisitions where changing waveforms are required,
        # but there is additional overhead due to the need to write the
        # waveforms into the buffers of the NI cards.
        #
        """
        #  Initialize, run, and stop the acquisition.
        #  Consider putting below to not block thread.
        self.daq.prepare_acquisition(channel_key, self.current_exposure_time, self.camera_line_interval)

        # calculate how long has been since last trigger
        time_spent = time.perf_counter() - self.pre_trigger_time

        if time_spent < self.trigger_waiting_time:
            if self.verbose:
                print('Need to wait!!!! Camera is not ready to be triggered!!!!')
            #TODO: we may remove additional 0.001 waiting time
            time.sleep(self.trigger_waiting_time - time_spent + 0.001)

        # Camera Settings - Exposure Time in Milliseconds
        # only set exposure time after the previous trigger has been done.
        if self.pre_exposure_time != self.current_exposure_time:
            self.camera.set_exposure_time(self.current_exposure_time)
            self.pre_exposure_time = self.current_exposure_time

        # get time when send out the trigger
        self.pre_trigger_time = time.perf_counter()

        # Run the acquisition
        self.daq.run_acquisition()
        self.daq.stop_acquisition()

        self.frame_id = (self.frame_id + 1) % self.number_of_frames

    def run_live_acquisition(self):
        """
        #  Stream live image to the GUI.
        #  Recalculates the waveforms for each image, thereby allowing people to adjust
        #  acquisition parameters in real-time.
        """
        self.stop_acquisition = False
        while self.stop_acquisition is False and self.stop_send_signal is False:
            self.run_single_acquisition()

    def change_resolution(self, args):
        resolution_value = args[0]
        if resolution_value == 'high':
            print("High Resolution Mode")
            self.experiment.MicroscopeState['resolution_mode'] = 'high'
            self.laser_triggers.enable_high_resolution_laser()
        else:
            # Can be 0.63, 1, 2, 3, 4, 5, and 6x.
            print("Low Resolution Mode, Zoom:", resolution_value)
            self.experiment.MicroscopeState['resolution_mode'] = 'low'
            self.experiment.MicroscopeState['zoom'] = resolution_value
            self.zoom.set_zoom(resolution_value)
            self.laser_triggers.enable_low_resolution_laser()

    def open_shutter(self):
        """
        # Evaluates the experiment parameters and opens the proper shutter.
        # 'low' is the low-resolution mode of the microscope, or the left shutter.
        # 'high' is the high-resolution mode of the microscope, or the right shutter.
        """
        resolution_mode = self.experiment.MicroscopeState['resolution_mode']
        if resolution_mode == 'low':
            self.shutter.open_left()
        elif resolution_mode == 'high':
            self.shutter.open_right()
        else:
            print("Shutter Command Invalid")

    def return_channel_index(self):
        return self.current_channel

if __name__ == '__main__':
    """ Testing Section """
    pass
