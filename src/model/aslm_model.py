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

# Third Party Imports
import numpy as np
from tifffile import imsave
from queue import Queue

# Local Imports
import model.aslm_device_startup_functions as startup_functions
from .aslm_model_config import Session as session
from controller.thread_pool import SynchronizedThreadPool
from model.concurrency.concurrency_tools import ResultThread, SharedNDArray, ObjectInSubprocess

# debug
from model.aslm_debug_model import Debug_Module

class Model:
    def __init__(
            self,
            args,
            configuration_path=None,
            experiment_path=None,
            etl_constants_path=None):
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
            # If command line entry provided, overwrites the model parameters
            # with synthetic hardware.
            print("Synthetic Zoom!")
            self.configuration.Devices['daq'] = 'SyntheticDAQ'
            self.configuration.Devices['camera'] = 'SyntheticCamera'
            self.configuration.Devices['etl'] = 'SyntheticETL'
            self.configuration.Devices['filter_wheel'] = 'SyntheticFilterWheel'
            self.configuration.Devices['stage'] = 'SyntheticStage'
            self.configuration.Devices['zoom'] = 'SyntheticZoom'
            self.configuration.Devices['shutters'] = 'SyntheticShutter'
            self.configuration.Devices['lasers'] = 'SyntheticLasers'

        # Move device initialization steps to multiple threads
        threads_dict = {
            'analysis': ResultThread(
                target=startup_functions.start_analysis,
                args=(
                    self.configuration,
                    self.experiment,
                    self.verbose,
                )).start(),
            'image_writer': ResultThread(
                target=startup_functions.start_image_writer,
                args=(
                    self.configuration,
                    self.experiment,
                    self.verbose,
                )).start(),
            'filter_wheel': ResultThread(
                target=startup_functions.start_filter_wheel,
                args=(
                    self.configuration,
                    self.verbose)).start(),
            'zoom': ResultThread(
                target=startup_functions.start_zoom_servo,
                args=(
                    self.configuration,
                    self.verbose)).start(),
            'camera': ResultThread(
                        target=startup_functions.start_camera,
                        args=(
                            self.configuration,
                            self.experiment,
                            self.verbose,
                        )).start(),
            'stages': ResultThread(
                target=startup_functions.start_stages,
                args=(
                    self.configuration,
                    self.verbose,
                )).start(),
            'shutter': ResultThread(
                target=startup_functions.start_shutters,
                args=(
                    self.configuration,
                    self.experiment,
                    self.verbose,
                )).start(),
            'daq': ResultThread(
                target=startup_functions.start_daq,
                args=(
                    self.configuration,
                    self.experiment,
                    self.etl_constants,
                    self.verbose,
                )).start(),
            'laser_triggers': ResultThread(
                target=startup_functions.start_laser_triggers,
                args=(
                    self.configuration,
                    self.experiment,
                    self.verbose,
                )).start(),
        }

        for k in threads_dict:
            setattr(self, k, threads_dict[k].get_result())

        # in synthetic_hardware mode, we need to wire up camera to daq
        if args.synthetic_hardware or args.sh:
            self.daq.set_camera(self.camera)

        # Acquisition Housekeeping
        self.threads_pool = SynchronizedThreadPool()
        self.stop_acquisition = False
        self.stop_send_signal = False
        self.image_count = 0
        self.acquisition_count = 0
        self.total_acquisition_count = None
        self.total_image_count = None
        self.current_time_point = 0
        self.current_channel = 0
        self.current_filter = 'Empty'
        self.current_laser = '488nm'
        self.current_laser_index = 1
        self.current_exposure_time = 200  # milliseconds
        self.start_time = None
        self.image_acq_start_time_string = time.strftime("%Y%m%d-%H%M%S")

        # data buffer
        self.data_buffer = None
        self.number_of_frames = 0

        # show image function/pipe handler
        self.show_img_pipe = None

        # frame signal id
        self.frame_id = 0
        # Queue
        self.autofocus_frame_queue = Queue()
        self.autofocus_pos_queue = Queue()
        self.autofocus_on = False

        # debug
        self.debug = Debug_Module(self, self.verbose)
        # add here for now for debug
        self.trigger_waitingtime = 0
        self.pre_trigger_time = 0

    def set_show_img_pipe(self, handler):
        """
        # wire up show image function/pipe
        """
        self.show_img_pipe = handler

    def set_data_buffer(self, data_buffer):
        # 05/16 Debugging
        self.camera.close_image_series()
        self.camera.set_ROI(512, 512)
        # print('image width, height:', width, height)
        self.data_buffer = data_buffer
        self.number_of_frames = self.configuration.SharedNDArray['number_of_frames']
        self.camera.initialize_image_series(self.data_buffer, self.number_of_frames)
        self.frame_id = 0

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
            self.experiment.MicroscopeState = args[0]
            self.is_save = self.experiment.MicroscopeState['is_save']
            if self.is_save:
                self.experiment.Saving = kwargs['saving_info']
            self.before_acquisition()
            self.run_single_acquisition()
            self.run_data_process(1)
            self.end_acquisition()

        elif command == 'live':
            self.experiment.MicroscopeState = args[0]
            self.is_save = False
            self.before_acquisition()
            self.is_live = True
            self.signal_thread = threading.Thread(
                target=self.run_live_acquisition)
            self.data_thread = threading.Thread(target=self.run_data_process)
            self.signal_thread.start()
            self.data_thread.start()

        elif command == 'series':
            self.experiment.MicroscopeState = args[0]

            pass

        elif command == 'update_setting':
            # stop live thread
            self.stop_send_signal = True
            self.signal_thread.join()
            if args[0] == 'channel':
                self.experiment.MicroscopeState['channels'] = args[1]
            # prepare devices based on updated info
            self.stop_send_signal = False
            self.signal_thread = threading.Thread(
                target=self.run_live_acquisition)
            self.signal_thread.start()

        elif command == 'autofocus':
            self.experiment.MicroscopeState = args[0]
            self.experiment.AutoFocusParameters = args[1]
            frame_num = self.get_autofocus_frame_num() + 1 # Produces 22
            print("Frame Number: ", frame_num)
            if frame_num < 1:
                return
            # frame_num = 11
            self.before_acquisition()
            self.autofocus_on = True
            self.is_save = False
            self.f_position = args[2]

            self.signal_thread = threading.Thread(target=self.run_single_acquisition, kwargs={'target_channel': 1})
            self.data_thread = threading.Thread(target=self.run_data_process, args=(frame_num,))
            self.signal_thread.start()
            self.data_thread.start()
            
        elif command == 'stop':
            # stop live thread
            self.stop_acquisition = True
            if hasattr(self, 'signal_thread'):
                self.signal_thread.join()
                self.data_thread.join()
            self.end_acquisition()
        elif command == 'debug':
            self.debug.debug(*args, **kwargs)

    def move_stage(self, pos_dict):
        self.stages.move_absolute(pos_dict)

    def before_acquisition(self):
        self.stop_acquisition = False
        self.stop_send_signal = False
        self.autofocus_on = False
        self.is_live = False
        self.open_shutter()

    def end_acquisition(self):
        """
        #
        """
        # dettach buffer in live mode in order to clear unread frames
        if self.is_live:
            self.camera.close_image_series()
            self.camera.initialize_image_series(self.data_buffer, self.number_of_frames)
            self.is_live = False
            self.frame_id = 0

        # close shutter
        self.shutter.close_shutters()

    def run_data_process(self, num_of_frames=0):
        """
        # This function will listen to camera, when there is a frame ready, it will call next steps to handle the frame data
        """
        count_frame = num_of_frames > 0
        if self.autofocus_on:
            f_frame_id = -1  # to indicate if there is one frame need to calculate shannon value, but the image frame isn't ready
            frame_num = 10  # any value but not 1

        wait_num = 20
        acquired_frame_num = 0

        while not self.stop_acquisition:
            frame_ids = self.camera.get_new_frame()
            # frame_ids = self.camera.buf_getlastframedata()
            if self.verbose:
                print('running data process, get frames', frame_ids)
            # if there is at least one frame available
            if not frame_ids:
                wait_num -= 1
                if wait_num <= 0:
                    break
                continue

            wait_num = 20
            acquired_frame_num += len(frame_ids)

            # show image
            if self.verbose:
                print('sent through pipe', frame_ids[0])
            self.show_img_pipe.send(frame_ids[0])

            # autofocuse analyse
            # debug: change something here!!!!!
            while self.autofocus_on:
                try:
                    if f_frame_id < 0:
                        f_frame_id, frame_num, f_pos = self.autofocus_frame_queue.get_nowait()
                    if f_frame_id not in frame_ids:
                        break
                except:
                    break
                entropy = self.analysis.normalized_dct_shannon_entropy(self.data_buffer[f_frame_id], 3)
                print('*******calculate entropy ', frame_num)
                f_frame_id = -1
                if entropy > self.max_entropy:
                    self.max_entropy = entropy
                    self.focus_pos = f_pos
                if frame_num == 1:
                    frame_num = 10  # any value but not 1
                    print('***********max shannon entropy:', self.max_entropy, self.focus_pos)
                    # find out the focus
                    self.autofocus_pos_queue.put(self.focus_pos)
                    break

            if count_frame:
                num_of_frames -= len(frame_ids)
                self.stop_acquisition = (num_of_frames <= 0) or self.stop_acquisition

        self.show_img_pipe.send('stop')
        # self.show_img_pipe.send(acquired_frame_num)
        print('received frames in total:', acquired_frame_num)
        if self.verbose:
            print('data thread is stop')

        # count_frame = num_of_frames > 0
        # while True:
        #     frame_ids = self.camera.get_new_frame()
        #     # frame_ids = self.camera.buf_getlastframedata()
        #     if self.verbose:
        #         print('running data process, get frames', frame_ids)
        #     # if there is at least one frame available
        #     if frame_ids:
        #         # show image
        #         if self.show_img_pipe:
        #             if self.verbose:
        #                 print('sent through pipe', frame_ids[0])
        #             self.show_img_pipe.send(frame_ids[0])
        #         else:
        #             if self.verbose:
        #                 print('get image frames:', frame_ids)
        #         # autofocus analyse
        #         while not self.autofocus_frame_queue.empty():
        #             try:
        #                 print("Made it to Queue!!!!!!!!!!!!!!!!")
        #                 f_frame_id, frame_num, f_pos = self.autofocus_frame_queue.get_nowait()
        #                 print('get from the queue:', f_frame_id, frame_num)
        #                 self.autofocus_pos_queue.put(1)
        #                 break
        #             except:
        #                 print("Did not make it to queue/autofocus_on")
        #                 break
        #
        #             # entropy = self.analysis.normalized_dct_shannon_entropy(self.data_buffer[f_frame_id], 3)
        #             entropy = f_frame_id
        #             if entropy > self.max_entropy:
        #                 self.max_entropy = entropy
        #                 self.focus_pos = f_pos
        #             if frame_num == 1:
        #                 print('max shannon entropy:', self.max_entropy, self.focus_pos)
        #                 # find out the focus
        #                 self.autofocus_pos_queue.put(self.focus_pos)
        #                 break
        #
        #         # save image
        #         if self.is_save:
        #             for idx in frame_ids:
        #                 threading.Thread(target=self.image_writer.write_tiff,
        #                                 args=(frame_ids,
        #                                             self.data_buffer[idx],
        #                                             self.current_channel,
        #                                             self.current_time_point,
        #                                             self.experiment.Saving['save_directory'])).start()
        #                 self.current_time_point += 1
        #
        #     if count_frame:
        #         num_of_frames -= len(frame_ids)
        #         self.stop_acquisition = (num_of_frames <= 0) or self.stop_acquisition
        #
        #     if self.stop_acquisition:
        #         if self.show_img_pipe:
        #             self.show_img_pipe.send('stop')
        #         if self.verbose:
        #             print('data thread is stopped, send stop to parent pipe')
        #         break

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

    def run_single_acquisition(self, target_channel=None):
        """
        # Called by model.run_command().
        """

        #  Interrogate the Experiment Settings
        microscope_state = self.experiment.MicroscopeState
        prefix_len = len('channel_')
        for channel_key in microscope_state['channels']:
            if self.stop_acquisition or self.stop_send_signal:
                break
            channel_idx = int(channel_key[prefix_len:])
            if target_channel and channel_idx != target_channel:
                continue
            channel = microscope_state['channels'][channel_key]
            if channel['is_selected'] is True:

                # Get and set the parameters for Waveform Generation,
                # Triggering, etc.
                self.current_channel = channel_idx

                # Camera Settings - Exposure Time in Milliseconds
                self.camera.set_exposure_time(channel['camera_exposure_time'])

                # Laser Settings
                self.laser_triggers.trigger_digital_laser(
                    self.current_laser_index)
                self.laser_triggers.set_laser_analog_voltage(
                    channel['laser_index'], channel['laser_power'])

                # Filter Wheel Settings
                self.filter_wheel.set_filter(channel['filter'])

                # Update Laser Scanning Waveforms - Exposure Time in Seconds
                self.daq.sweep_time = self.current_exposure_time / 1000

                # Update ETL Settings
                self.daq.update_etl_parameters(microscope_state, channel)

                # Acquire an Image
                if self.autofocus_on:
                    self.snap_image_with_autofocus()
                else:
                    self.snap_image()


    def snap_image(self):
        """
        # Snaps a single image after updating the waveforms.
        # Can be used in acquisitions where changing waveforms are required,
        # but there is additional overhead due to the need to write the
        # waveforms into the buffers of the NI cards.
        #
        """
        #  Initialize, run, and stop the acquisition.
        self.daq.prepare_acquisition()
        time_spent = time.perf_counter() - self.pre_trigger_time
        print('*Timing!', time_spent, self.trigger_waitingtime)
        if time_spent < self.trigger_waitingtime:
            print('Need to wait!!!! Too much signals!!!!')
            time.sleep(self.trigger_waitingtime - time_spent + 0.1)
        self.trigger_waitingtime = self.current_exposure_time/1000 + 0.054
        self.daq.run_acquisition()
        self.pre_trigger_time = time.perf_counter()
        self.daq.stop_acquisition()

        self.frame_id = (self.frame_id + 1) % self.number_of_frames

    def snap_image_with_autofocus(self):
        # get autofocus setting according to channel
        settings = self.experiment.AutoFocusParameters
        pos = self.f_position
        if settings['stage1_selected']:
            pos = self.send_autofocus_signals(self.f_position, int(settings['stage1_range']), int(settings['stage1_step_size']))

        if settings['stage2_selected']:
            pos = self.send_autofocus_signals(pos, int(settings['stage2_range']), int(settings['stage2_step_size']))

        # move stage to the focus position
        self.move_stage({'f': pos})
        
        # self.autofocus_on = False

        self.snap_image()
        

    def send_autofocus_signals(self, f_position, ranges, step_size):
        steps = ranges // step_size + 1
        pos = f_position - (steps // 2) * step_size

        self.max_entropy = 0
        self.focus_pos = f_position

        for i in range(steps):
            # move focus device
            # low resolution move device
            print("Frame ID: ", self.frame_id, " Position: ", pos, "frame in queue", steps-i)
            self.move_stage({'f': pos})
            self.autofocus_frame_queue.put((self.frame_id, steps - i, pos))
            time.sleep(0.1)
            self.snap_image()
            pos += step_size



        # wait to get the focus postion
        pos = self.autofocus_pos_queue.get(timeout=steps*3)
        return pos

    def get_autofocus_frame_num(self):
        settings = self.experiment.AutoFocusParameters
        frames = 0
        if settings['stage1_selected']:
            frames = int(settings['stage1_range']) // int(settings['stage1_step_size']) + 1
        if settings['stage2_selected']:
            frames += int(settings['stage2_range']) // int(settings['stage2_step_size']) + 1
        return frames

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
