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
from tools.decorators import function_timer

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
        
        # Plot Pipe handler
        self.plot_pipe = None

        # frame signal id
        self.frame_id = 0
        # Queue
        self.autofocus_frame_queue = Queue()
        self.autofocus_pos_queue = Queue()
        
        # flags
        self.autofocus_on = False # autofocus 
        self.is_live = False  # need to clear up data buffer after acquisition
        self.is_save = False  # save data
        self.stop_acquisition = False # stop signal and data threads
        self.stop_send_signal = False # stop signal thread

        # timing
        self.camera_minimum_waiting_time = self.camera.get_minimum_waiting_time()
        self.trigger_waiting_time = 0
        self.pre_trigger_time = 0

        # debug
        self.debug = Debug_Module(self, self.verbose)

    def set_show_img_pipe(self, handler):
        """
        # wire up show image function/pipe
        """
        self.show_img_pipe = handler
        
    def set_autofocus_plot_pipe(self, handler):
        """
        # wire up autofocus plot pipe
        """
        self.plot_pipe = handler

    def set_data_buffer(self, data_buffer, img_width=512, img_height=512):
        self.camera.close_image_series()
        self.camera.set_ROI(img_width, img_height)
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

    @function_timer
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
            """
            Live Acquisition Mode
            """
            self.experiment.MicroscopeState = args[0]
            self.is_save = False
            self.before_acquisition()
            self.is_live = True
            self.signal_thread = threading.Thread(target=self.run_live_acquisition)
            self.signal_thread.name = "Live Mode Signal"
            self.data_thread = threading.Thread(target=self.run_data_process)
            self.data_thread.name = "Live Mode Data"
            self.signal_thread.start()
            self.data_thread.start()

        elif command == 'z-stack':
            pass

        elif command == 'projection':
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
                    self.etl_constants.low[zoom] = laser_info
                else:
                    self.etl_constants.high[zoom] = laser_info
                if self.verbose:
                    print(self.etl_constants.low[zoom])

                # Modify DAQ to pull the initial values from the etl_constants.yml file, or be passed it from the model.
                # Pass to the self.model.daq to
                #             value = self.resolution_info.ETLConstants[self.resolution][self.mag][laser][etl_name]
                # print(args[1])

            # prepare devices based on updated info
            self.stop_send_signal = False
            self.signal_thread = threading.Thread(
                target=self.run_live_acquisition)
            self.signal_thread.name = "ETL Popup Signal"
            self.signal_thread.start()

        elif command == 'autofocus':
            self.experiment.MicroscopeState = args[0]
            self.experiment.AutoFocusParameters = args[1]
            frame_num = self.get_autofocus_frame_num() + 1  # What does adding one here again doing?
            if frame_num < 1:
                return
            self.before_acquisition() # Opens correct shutter and puts all signals to false
            self.autofocus_on = True
            self.is_save = False
            self.f_position = args[2] # Current position
            self.signal_thread = threading.Thread(target=self.run_single_acquisition, kwargs={'target_channel': 1})
            self.signal_thread.name = "Autofocus Signal"
            self.data_thread = threading.Thread(target=self.run_data_process, args=(frame_num,))
            self.data_thread.name = "Autofocus Data"
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
        # trun off flags
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

        wait_num = 10 # this will let this thread wait 10 * 500 ms before it ends
        acquired_frame_num = 0
        
        # Plot Data list
        plot_data = [] # Going to be a List of [focus, entropy]

        while not self.stop_acquisition:
            frame_ids = self.camera.get_new_frame()
            # frame_ids = self.camera.buf_getlastframedata()
            if self.verbose:
                print('running data process, get frames', frame_ids)
            # if there is at least one frame available
            if not frame_ids:
                wait_num -= 1
                if wait_num <= 0:
                    # it has waited for wait_num * 500 ms, it's sure there won't be any frame coming
                    break
                continue

            wait_num = 10
            acquired_frame_num += len(frame_ids)

            # show image
            if self.verbose:
                print('sent through pipe', frame_ids[0])
            self.show_img_pipe.send(frame_ids[0])

            # autofocuse analyse
            while self.autofocus_on:
                try:
                    if f_frame_id < 0:
                        f_frame_id, frame_num, f_pos = self.autofocus_frame_queue.get_nowait()
                    if f_frame_id not in frame_ids:
                        break
                except:
                    break
                entropy = self.analysis.normalized_dct_shannon_entropy(self.data_buffer[f_frame_id], 3) # How is this getting called without self.analysis existing in the model?
                # TODO Pipe f_pos and entropy to controller to pass to popup plot
                if self.verbose:
                    print("Appending plot data focus, entropy: ", f_pos, entropy)
                    plot_data.append([f_pos, entropy[0]])
                    print("Testing plot data print: ", len(plot_data))
                else:
                    plot_data.append([f_pos, entropy[0]])
                # Need to initialize entropy above for the first iteration of the autofocus routine.
                # Need to initialize entropy_vector above for the first iteration of the autofocus routine.
                # Then need to append each measurement to the entropy_vector.  First column will be the focus position, 
                # second column would be the DCT entropy value.
                # 
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

        # Turning plot_data into numpy array and sending
        # we could send plot_data here or we could send it in function snap_image_with_autofocus
        if self.autofocus_on:
            if self.verbose:
                print("Model sending plot data: ", plot_data)
            plot_data = np.asarray(plot_data)
            self.plot_pipe.send(plot_data) # Sending controller plot data
        
        self.show_img_pipe.send('stop')

        if self.verbose:
            print('data thread is stop')
            print('received frames in total:', acquired_frame_num)

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

    @function_timer
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
                self.current_exposure_time = channel['camera_exposure_time']

                # update trigger waiting time when exposure time changed
                self.trigger_waiting_time = self.current_exposure_time/1000 + self.camera_minimum_waiting_time

                # Laser Settings
                self.laser_triggers.trigger_digital_laser(self.current_laser_index)
                self.laser_triggers.set_laser_analog_voltage(channel['laser_index'], channel['laser_power'])

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


    @function_timer
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

        # calculate how long has been since last trigger
        time_spent = time.perf_counter() - self.pre_trigger_time

        if time_spent < self.trigger_waiting_time:
            if self.verbose:
                print('Need to wait!!!! Too much signals!!!!')
            # add 0.1 here, there are lost signals if I don't add another short time,
            # but we might could add time short than 0.1
            time.sleep(self.trigger_waiting_time - time_spent + 0.1)
        
        self.daq.run_acquisition()

        # get time when send out the trigger
        self.pre_trigger_time = time.perf_counter()

        self.daq.stop_acquisition()

        self.frame_id = (self.frame_id + 1) % self.number_of_frames

    def snap_image_with_autofocus(self):
        # get autofocus setting according to channel
        settings = self.experiment.AutoFocusParameters
        pos = self.f_position

        if settings['coarse_selected']:
            pos = self.send_autofocus_signals(self.f_position, int(settings['coarse_range']), int(settings['coarse_step_size']))

        if settings['fine_selected']:
            pos = self.send_autofocus_signals(pos, int(settings['fine_range']), int(settings['fine_step_size']))

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

            self.move_stage({'f': pos})
            self.autofocus_frame_queue.put((self.frame_id, steps - i, pos))
            # add a wait time here to let the stage move to where we want
            # TODO:we may change to 'on_target' function later when figure it out
            time.sleep(0.1)
            self.snap_image()
            pos += step_size

        # wait to get the focus postion
        pos = self.autofocus_pos_queue.get(timeout=steps*3)
        return pos

    def get_autofocus_frame_num(self):
        settings = self.experiment.AutoFocusParameters
        frames = 0
        if settings['coarse_selected']:
            frames = int(settings['coarse_range']) // int(settings['coarse_step_size']) + 1
        if settings['fine_selected']:
            frames += int(settings['fine_range']) // int(settings['fine_step_size']) + 1
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
