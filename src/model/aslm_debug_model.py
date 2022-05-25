"""
ASLM camera communication classes.

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

import threading
from queue import Empty
import random
import time
import logging
from pathlib import Path

from tifffile import imread
import numpy as np
from scipy.fftpack import dctn
import tensorflow as tf

from multiprocessing import Pool, Lock

from model.aslm_device_startup_functions import start_analysis
from model.concurrency.concurrency_tools import ObjectInSubprocess
from model.aslm_analysis import CPUAnalysis

# Logger Setup
p = Path(__file__).resolve().parts[7]
logger = logging.getLogger(p)

def calculate_entropy(dct_array, otf_support_x, otf_support_y):

    i = dct_array > 0
    image_entropy = np.sum(dct_array[i] * np.log(dct_array[i]))
    image_entropy = image_entropy + \
                    np.sum(-dct_array[~i] * np.log(-dct_array[~i]))
    image_entropy = -2 * image_entropy / (otf_support_x * otf_support_y)
    return image_entropy

def normalized_dct_shannon_entropy(input_array, psf_support_diameter_xy, verbose=False):
    '''
    # input_array : 2D or 3D image.  If 3D, will iterate through each 2D plane.
    # otf_support_x : Support for the OTF in the x-dimension.
    # otf_support_y : Support for the OTF in the y-dimension.
    # Returns the entropy value.
    '''
    # Get Image Attributes
    # input_array = np.double(input_array)
    image_dimensions = input_array.ndim

    if image_dimensions == 2:
        (image_height, image_width) = input_array.shape
        number_of_images = 1
    elif image_dimensions == 3:
        (number_of_images, image_height, image_width) = input_array.shape
    else:
        raise ValueError("Only 2D and 3D Images Supported.")

    otf_support_x = image_width / psf_support_diameter_xy
    otf_support_y = image_height / psf_support_diameter_xy

    #  Preallocate Array
    entropy = np.zeros(number_of_images)
    execution_time = np.zeros(number_of_images)
    for image_idx in range(int(number_of_images)):
        if verbose:
            start_time = time.time()
        if image_dimensions == 2:
            numpy_array = input_array
        else:
            numpy_array = np.array(input_array[image_idx, :, :])

        # Forward 2D DCT
        dct_array = dctn(numpy_array, type=2)

        # Normalize the DCT
        dct_array = np.divide(dct_array, np.linalg.norm(dct_array, ord=2))
        image_entropy = calculate_entropy(dct_array, otf_support_x, otf_support_y)

        if verbose:
            print("DCTS Entropy:", image_entropy)
            execution_time[image_idx] = time.time() - start_time
            print("Execution Time:", execution_time[image_idx])

        entropy[image_idx] = image_entropy
        input_array[0][0] = 0
    return entropy

class Debug_Module:
    def __init__(self, model, verbose=False):

        self.model = model
        self.verbose = verbose
        self.analysis_type = 'normal'

    def debug(self, command, *args, **kwargs):
        getattr(self, command)(*args, **kwargs)

    def update_analysis_type(self, analysis_type, *args, **kwargs):
        if analysis_type == self.analysis_type:
            return
        if self.analysis_type == 'subprocess':
            self.model.analysis.terminate()
        if analysis_type == 'normal':
            self.model.analysis = start_analysis(self.model.configuration, self.model.experiment, self.verbose)
        elif analysis_type == 'subprocess':
            self.model.analysis = ObjectInSubprocess(CPUAnalysis, verbose=self.verbose)
        else:
            self.start_autofocus(*args, **kwargs)
        if analysis_type != 'pool':
            self.analysis_type = analysis_type

    def get_timings(self, *args, **kwargs):
        cyclic_trigger = self.model.camera.camera_controller.get_property_value('cyclic_trigger_period')
        trigger_blank = self.model.camera.camera_controller.get_property_value('minimum_trigger_blank')
        trigger_interval = self.model.camera.camera_controller.get_property_value('minimum_trigger_interval')
        print('***cyclic_trigger:', cyclic_trigger, ',trigger_blank:', trigger_blank, 'trigger_interval:', trigger_interval)

    def update_image_size(self, *args, **kwargs):
        self.model.set_data_buffer(self.model.data_buffer)

    def start_autofocus(self, *args, **kwargs):
        print('start autofocus', *args)
        self.model.experiment.MicroscopeState = args[0]
        self.model.experiment.AutoFocusParameters = args[1]
        frame_num = self.model.get_autofocus_frame_num() + 1 # What does adding one here again doing?
        if frame_num <= 1:
            return
        self.model.before_acquisition() # Opens correct shutter and puts all signals to false
        self.model.autofocus_on = True
        self.model.is_save = False
        self.model.f_position = args[2] # Current position

        self.model.signal_thread = threading.Thread(target=self.model.run_single_acquisition, kwargs={'target_channel': 1})
        self.model.signal_thread.name = "Autofocus Signal"
        self.model.data_thread = threading.Thread(target=self.get_frames_analysis, args=(frame_num,))
        self.model.data_thread.name = "Autofocus Data"
        self.model.signal_thread.start()
        self.model.data_thread.start()

    def ignored_signals(self, command, *args, **kwargs):
        if command == 'live':
            print('live!!!!!!')
            self.model.experiment.MicroscopeState = args[0]
            self.model.is_save = False
            self.model.before_acquisition()
            self.model.trigger_waiting_time = 0
            self.model.pre_trigger_time = 0
            self.model.signal_thread = threading.Thread(
                target=self.send_signals(args[1]))
            self.model.data_thread = threading.Thread(target=self.get_frames, args=(args[1],))
            self.model.signal_thread.start()
            self.model.data_thread.start()
        elif command == 'autofocus':
            self.model.experiment.MicroscopeState = args[0]
            self.model.experiment.AutoFocusParameters = args[1]
            signal_num = args[3]
            # signal_num = self.model.get_autofocus_frame_num() + 1
            self.model.before_acquisition()
            self.model.autofocus_on = True
            self.model.is_save = False
            self.model.f_position = args[2]

            self.model.signal_thread = threading.Thread(target=self.send_autofocus_signals, args=(self.model.f_position, signal_num))
            self.model.data_thread = threading.Thread(target=self.get_frames, args=(signal_num,))
            self.model.signal_thread.start()
            self.model.data_thread.start()

    def blocked_queue(self, *args, **kwargs):

        signal_num = args[2] // 10

        def func():
            pos = args[1]
            for i in range(10):
                try:
                    pos = self.send_autofocus_signals(pos, signal_num)
                except Empty:
                    print('blocked queue happened!!!')
                    pos = args[1]
                    break

        self.model.experiment.MicroscopeState = args[0]
        self.model.before_acquisition()
        self.model.autofocus_on = True
        self.model.is_save = False
        self.model.signal_thread = threading.Thread(target=func)
        self.model.data_thread = threading.Thread(target=self.get_frames, args=(signal_num*10,))
        self.model.signal_thread.start()
        self.model.data_thread.start()
        

    def send_signals(self, signal_num):
        channel_num = len(self.model.experiment.MicroscopeState['channels'].keys())
        i = 0
        while i < signal_num and not self.model.stop_acquisition:
            self.model.run_single_acquisition()
            i += channel_num
            print('sent out', i, 'signals!!!!!')

    def send_autofocus_signals(self, f_position, signal_num):
        step_size = random.randint(5, 50)
        ranges = step_size * (signal_num-1)

        print('*************', f_position, ranges, step_size)

        pos = self.model.send_autofocus_signals(f_position, ranges, step_size)


        print('focus position', pos)
        return pos

        
    def get_frames(self, num_of_frames=0):
        """
        # This function will listen to camera, when there is a frame ready, it will call next steps to handle the frame data
        """
        count_frame = num_of_frames > 0
        if self.model.autofocus_on:
            f_frame_id = -1 # to indicate if there is one frame need to calculate shannon value, but the image frame isn't ready
            frame_num = 10 # any value but not 1

        wait_num = 20
        acquired_frame_num = 0

        # Plot Data list
        plot_data = [] # Going to be a List of [focus, entropy]
        start_time = time.perf_counter()

        while not self.model.stop_acquisition:
            frame_ids = self.model.camera.get_new_frame()
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
            self.model.show_img_pipe.send(frame_ids[0])

            # autofocuse analyse
            while self.model.autofocus_on:
                try:
                    if f_frame_id < 0:
                        f_frame_id, frame_num, f_pos = self.model.autofocus_frame_queue.get_nowait()
                    if f_frame_id not in frame_ids:
                        break
                except:
                    break
                entropy = self.model.analysis.normalized_dct_shannon_entropy(self.model.data_buffer[f_frame_id], 3)
                print('*******calculate entropy ', frame_num)
                if self.verbose:
                    print("Appending plot data focus, entropy: ", f_pos, entropy)
                    plot_data.append([f_pos, entropy[0]])
                    print("Testing plot data print: ", len(plot_data))
                else:
                    plot_data.append([f_pos, entropy[0]])

                f_frame_id = -1
                if entropy > self.model.max_entropy:
                    self.model.max_entropy = entropy
                    self.model.focus_pos = f_pos
                if frame_num == 1:
                    frame_num = 10 # any value but not 1
                    print('***********max shannon entropy:', self.model.max_entropy, self.model.focus_pos)
                    # find out the focus
                    self.model.autofocus_pos_queue.put(self.model.focus_pos)
                    break

            if count_frame:
                num_of_frames -= len(frame_ids)
                self.model.stop_acquisition = (num_of_frames <= 0) or self.model.stop_acquisition
        
        # Turning plot_data into numpy array and sending
        # we could send plot_data here or we could send it in function snap_image_with_autofocus
        if self.model.autofocus_on:
            if self.verbose:
                print("Model sending plot data: ", plot_data)
            plot_data = np.asarray(plot_data)
            self.model.plot_pipe.send(plot_data) # Sending controller plot data
        
        self.model.show_img_pipe.send('stop')
        self.model.show_img_pipe.send(acquired_frame_num)
        end_time = time.perf_counter()
        print('*******total time********', end_time - start_time)
        print('received frames in total:', acquired_frame_num)
        if self.verbose:
            print('data thread is stopped, send stop to parent pipe')

    def get_frames_analysis(self, num_of_frames=0):
        """
        # This function will listen to camera, when there is a frame ready, it will call next steps to handle the frame data
        """
        count_frame = num_of_frames > 0
        if self.model.autofocus_on:
            f_frame_id = -1 # to indicate if there is one frame need to calculate shannon value, but the image frame isn't ready
            frame_num = 10 # any value but not 1

        wait_num = 20
        acquired_frame_num = 0

        # Plot Data list
        plot_data = [] # Going to be a List of [focus, entropy]
        start_time = time.perf_counter()
        
        pool = Pool(processes=3)
        entropies = []
        end_lock = Lock()
        end_lock.acquire()
        autofocus_parameters = self.model.experiment.AutoFocusParameters

        end_length = 0
        if autofocus_parameters['coarse_selected']:
            end_length = int(autofocus_parameters['coarse_range']) // int(autofocus_parameters['coarse_step_size']) + 1
        end_length2 = 0
        if autofocus_parameters['fine_selected']:
            end_length2 = int(autofocus_parameters['fine_range']) // int(autofocus_parameters['fine_step_size']) + 1
        if end_length == 0:
            end_length = end_length2
            end_length2 = 0

        def callback_func(pos, frame_idx):
            def func(entropy):
                if entropy[0] > self.model.max_entropy:
                    self.model.max_entropy = entropy[0]
                    self.model.focus_pos = pos
                plot_data.append([pos, entropy[0]])
                if len(plot_data) == end_length:
                    end_lock.release()
            return func

        while not self.model.stop_acquisition:
            frame_ids = self.model.camera.get_new_frame()
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
            self.model.show_img_pipe.send(frame_ids[0])

            # autofocuse analyse
            while self.model.autofocus_on:
                try:
                    if f_frame_id < 0:
                        f_frame_id, frame_num, f_pos = self.model.autofocus_frame_queue.get_nowait()
                    if f_frame_id not in frame_ids:
                        break
                except:
                    break
                pool.apply_async(normalized_dct_shannon_entropy, (self.model.data_buffer[f_frame_id], 3,), callback = callback_func(f_pos, f_frame_id))
                # entropy = normalized_dct_shannon_entropy(self.model.data_buffer[f_frame_id], 3)
                print('*******calculate entropy ', frame_num)
                # if self.verbose:
                #     print("Appending plot data focus, entropy: ", f_pos, entropy)
                #     plot_data.append([f_pos, entropy[0]])
                #     print("Testing plot data print: ", len(plot_data))
                # else:
                #     plot_data.append([f_pos, entropy[0]])

                f_frame_id = -1
                # if entropy > self.model.max_entropy:
                #     self.model.max_entropy = entropy
                #     self.model.focus_pos = f_pos
                if frame_num == 1:
                    end_lock.acquire()
                    frame_num = 10 # any value but not 1
                    print('***********max shannon entropy:', self.model.max_entropy, self.model.focus_pos)
                    # find out the focus
                    self.model.autofocus_pos_queue.put(self.model.focus_pos)
                    end_length += end_length2
                    break

            if count_frame:
                num_of_frames -= len(frame_ids)
                self.model.stop_acquisition = (num_of_frames <= 0) or self.model.stop_acquisition
        
        print('entropy values:', plot_data)
        pool.close()
        self.model.show_img_pipe.send('stop')
        self.model.show_img_pipe.send(acquired_frame_num)

        # Turning plot_data into numpy array and sending
        # we could send plot_data here or we could send it in function snap_image_with_autofocus
        if self.model.autofocus_on:
            if self.verbose:
                print("Model sending plot data: ", plot_data)
            plot_data = np.asarray(plot_data)
            self.model.plot_pipe.send(plot_data) # Sending controller plot data
        end_time = time.perf_counter()
        print('*******total time********', end_time - start_time)
        print('received frames in total:', acquired_frame_num)
        if self.verbose:
            print('data thread is stopped, send stop to parent pipe')