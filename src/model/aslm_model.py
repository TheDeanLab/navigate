# Standard Library Imports
import time
import os
import threading
import ctypes

# Third Party Imports
import numpy as np

# Local Imports
from .aslm_model_functions import *
from .aslm_model_config import Session as session
from controller.thread_pool import SynchronizedThreadPool
from tifffile import imsave

from model.concurrency.concurrency_tools import ResultThread, SharedNDArray, ObjectInSubprocess

NUM_OF_FRAMES = 100

class Model:
    def __init__(self, args, configuration_path=None, experiment_path=None, etl_constants_path=None):
        # Retrieve the initial configuration from the yaml file
        self.verbose = args.verbose

        # Loads the YAML file for all of the microscope parameters
        self.configuration = session(configuration_path, args.verbose)

        # Loads the YAML file for all of the experiment parameters
        self.experiment = session(experiment_path, args.verbose)

        # Loads the YAML file for all of the ETL constants
        self.etl_constants = session(etl_constants_path, args.verbose)

        # Initialize all Hardware
        if args.synthetic_hardware:
            # If command line entry provided, overwrites the model parameters with synthetic hardware
            self.configuration.Devices['daq'] = 'SyntheticDAQ'
            self.configuration.Devices['camera'] = 'SyntheticCamera'
            self.configuration.Devices['etl'] = 'SyntheticETL'
            self.configuration.Devices['filter_wheel'] = 'SyntheticFilterWheel'
            self.configuration.Devices['stage'] = 'SyntheticStage'
            self.configuration.Devices['zoom'] = 'SyntheticZoom'
            self.configuration.Devices['shutters'] = 'SyntheticShutter'
            self.configuration.Devices['lasers'] = 'SyntheticLasers'

        # Move device initialization steps to multiple threads
        # we start serial devices in function self.start_serial_devices()
        # TODO: make sure all serial devices connected to the same computer serial port moved to self.start_serial_device()
        threads_dict = {
            'serial_devices': ResultThread(target=self.start_serial_devices).start(),
            'camera': ResultThread(target=start_camera, args=(self.configuration, self.experiment, self.verbose,)).start(),
            'stages': ResultThread(target=start_stages, args=(self.configuration, self.verbose,)).start(),
            'shutter': ResultThread(target=start_shutters, args=(self.configuration, self.experiment, self.verbose,)).start(),
            'daq': ResultThread(target=start_daq, args=(self.configuration, self.experiment, self.etl_constants, self.verbose,)).start(),
            # 'etl': ResultThread(target=start_etl, args=(self.configuration, self.verbose,)).start()
        }
        for k in threads_dict:
            if k != 'serial_devices':
                setattr(self, k, threads_dict[k].get_result())
            else:
                threads_dict[k].get_result()

        # in synthetic_hardware mode, we need to wire up camera to daq
        if args.synthetic_hardware:
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
        self.data = np.zeros(np.shape((self.camera.y_pixels, self.camera.x_pixels)))
        # data buffer
        self.data_buffer = None
        # self.data_buffer = [SharedNDArray(shape=(self.camera.y_pixels, self.camera.x_pixels), dtype='uint16') for i in range(NUM_OF_FRAMES)]
        # frame buffer pointer array: used to link camera with the data buffer
        self.data_ptr = None
        # self.data_ptr = [np_array.ctypes.data for np_array in self.data_buffer]
        # show image function/pipe handler
        self.show_img_pipe = None

    def start_serial_devices(self):
        """
        # This function used to start serial devices
        # TODO:If other devices connect to the same computer serial port, we could add it here
        """
        self.filter_wheel = start_filter_wheel(self.configuration, self.verbose)
        self.zoom = start_zoom_servo(self.configuration, self.verbose)
        # self.laser=start_lasers(self.configuration, self.verbose)

    def set_show_img_pipe(self, handler):
        """
        # wire up show image function/pipe
        """
        self.show_img_pipe = handler

    def set_data_buffer(self, data_buffer):
        self.data_buffer = data_buffer
        ptr_array= ctypes.c_void_p * NUM_OF_FRAMES
        self.data_ptr = ptr_array()
        for i in range(NUM_OF_FRAMES):
            np_array = self.data_buffer[i]
            self.data_ptr[i] = np_array.ctypes.data
    
    #  Basic Image Acquisition Functions
    #  - These functions are used to acquire images from the camera
    #  - Tasks for delivering analog and digital outputs are already initiated by the DAQ object
    #  - daq.create_waveforms() calculates the waveforms and writes them to tasks.
    #  - daq.start_tasks() starts the tasks, which then wait for an external trigger.
    #  - daq.run_tasks() delivers the external trigger which synchronously starts the tasks and waits for completion.
    #  - daq.stop_tasks() stops the tasks and cleans up.
    
    def run_command(self, command, *args, **kwargs):
        if self.verbose:
            print('in the model(get the command from controller):', command, args)
        if not self.data_buffer:
            if self.verbose:
                print('Error: have not set up data buffer!')
            return
        if command == 'single':
            self.experiment.MicroscopeState = args[0]
            self.is_save = self.experiment.MicroscopeState['is_save']
            self.stop_acquisition = False
            self.prepare_acquisition()
            self.run_single_acquisition()
            self.stop_acquisition = True
            self.run_data_process(1)
            self.end_acquisition()
        elif command == 'live':
            self.is_save = False
            self.stop_acquisition = False
            self.stop_send_signal = False
            self.prepare_acquisition()
            self.live_thread = threading.Thread(target=self.run_live_acquisition)
            self.data_thread = threading.Thread(target=self.run_data_process)
            self.live_thread.start()
            self.data_thread.start()
        elif command == 'series':
            pass
        elif command == 'update setting':
            # stop live thread
            self.stop_send_signal = True
            self.live_thread.join()
            if args[0] == 'channel':
                self.experiment.MicroscopeState['channels'] = kwargs['channels']
            # prepare devices based on updated info
            self.stop_send_signal = False
            self.prepare_acquisition()
            self.live_thread = threading.Thread(target=self.run_live_acquisition)
            self.live_thread.start()
        elif command == 'stop':
            # stop live thread
            self.stop_acquisition = True
            self.live_thread.join()
            self.data_thread.join()
            self.end_acquisition()

    def move_stage(self, pos_dict):
        self.stages.move_absolute(pos_dict)

    def open_shutter(self):
        """
        # Evaluates the experiment parameters and opens the proper shutter.
        # 'low' is the low-resolution mode of the microscope, or the left shutter.
        # 'high' is the high-resolution mode of the microscope, or the right shutter.
        """
        resolution_mode = self.experiment.MicroscopeState['resolution_mode']
        if resolution_mode == 'low':
            self.shutter.open_left()
        else:  # High Resolution Mode = Right
            self.shutter.open_right()

    def close_shutter(self):
        """
        # Automatically closes both shutters
        """
        self.shutter.close_shutters()

    def prepare_acquisition(self):
        """
        # 
        """
        self.open_shutter()
        # attach buffer to camera
        self.camera.initialize_image_series(self.data_ptr)

    def end_acquisition(self):
        """
        # 
        """
        # dettach buffer
        self.camera.close_image_series()
        
        # close shutter
        self.close_shutter()

    def run_data_process(self, num_of_frames=0):
        """
        # This function will listen to camera, when there is a frame ready, it will call next steps to handle the frame data
        """
        count_frame = num_of_frames > 0
        while True:
            frame_ids = self.camera.get_new_frame()
            if self.verbose:
                print('running data process, get frames', frame_ids)
            # if there is at least one frame available
            if frame_ids:
                # analyse image

                # show image
                if self.show_img_pipe:
                    print('sent through pipe', frame_ids[0])
                    self.show_img_pipe.send(frame_ids[0])
                # save image
                if self.is_save:
                    for idx in frame_ids:
                        image_name = self.generate_image_name()
                        imsave(os.path.join(self.experiment.Saving['save_directory'], image_name), self.data_buffer[idx])

            if count_frame:
                num_of_frames -= 1
                if num_of_frames == 0:
                    break
            if self.stop_acquisition:
                self.show_img_pipe.send('stop')
                if self.verbose:
                    print('data thread is stopped, send stop to parent pipe')
                break


    def end_acquisition(self):
        """
        """

    def snap_image(self):
        """
        # Snaps a single image after updating the waveforms.
        #
        # Can be used in acquisitions where changing waveforms are required,
        # but there is additional overhead due to the need to write the
        # waveforms into the buffers of the NI cards.
        #
        """
        #  Initialize the DAQ Tasks and the Camera.
        self.daq.initialize_tasks()        

        #  Prepare the DAQ for Waveform Delivery
        self.daq.create_tasks()
        self.daq.create_waveforms()
        self.daq.start_tasks()

        #  Trigger everything and grab the image.
        self.daq.run_tasks()

        #  Close everything.
        self.daq.stop_tasks()
        self.daq.close_tasks()


    def prepare_image_series(self):
        """
        #  Prepares an image series without waveform update
        """
        self.daq.create_tasks()
        self.daq.write_waveforms_to_tasks()

    def snap_image_in_series(self):
        """
        # Snaps and image from a series without waveform update
        """
        self.daq.start_tasks()
        self.daq.run_tasks()
        self.data = self.camera.get_image()
        self.daq.stop_tasks()

    def close_image_series(self):
        """
        #  Cleans up after series without waveform update
        """
        self.daq.close_tasks()

    def calculate_number_of_channels(self):
        """
        #  Calculates the total number of channels that are selected.
        """
        return len(self.experiment.MicroscopeState['channels'].keys())

    def prepare_acquisition_list(self):
        """
        #  Calculates the total number of acquisitions, images, etc.  Initializes the counters.
        """

        number_of_channels = self.calculate_number_of_channels()
        number_of_positions = len(self.experiment.MicroscopeState['stage_positions'])
        number_of_slices = self.experiment.MicroscopeState['number_z_steps']
        number_of_time_points = self.experiment.MicroscopeState['timepoints']

        self.image_count = 0
        self.acquisition_count = 0
        self.total_acquisition_count = number_of_channels * number_of_positions * number_of_time_points
        self.total_image_count = self.total_acquisition_count * number_of_slices
        self.start_time = time.time()

    def acquire_with_waveform_update(self):
        """
        # Sets the camera in a state where it can be triggered.
        # Changes the Filter Wheel to the correct position
        # Specifies the laser
        # Open the shutter as specified by the experiment parameters.
        # The NIDAQ tasks are initialized during the daq __init__ function.
        # Not sure if we have to self.daq.close_tasks() them in order to load a fresh waveform.
        # if so, self.daq.initialize_tasks() need to be called after.

        # Grab the image from the camera and save it.
        # Closes the shutter
        # Disables the camera
        """
        self.camera.set_exposure_time(self.experiment.MicroscopeState['channels']
                                      ['channel_1']['camera_exposure_time']/1000)
        self.camera.initialize_image_series(self.data_ptr)
        self.daq.initialize_tasks()

        self.filter_wheel.set_filter(self.experiment.MicroscopeState['channels']['channel_1']['filter'])
        self.daq.identify_laser_idx(self.experiment.MicroscopeState['channels']['channel_1']['laser'])
        self.open_shutter()
        self.daq.start_tasks()
        self.daq.create_waveforms()
        self.daq.run_tasks()
        self.daq.stop_tasks()
        image = self.camera.get_image()
        #  self.save_test_image(image)
        self.close_shutter()
        self.camera.close_image_series()

    def load_experiment_file(self, experiment_path):
        # Loads the YAML file for all of the experiment parameters
        self.experiment = session(experiment_path, self.verbose)

    def run_single_acquisition(self):
        """
        This function retrieves the state of the microscope from the GUI, iterates through each selected channel,
        and snaps an image for each channel setting.  In each iteration, the camera is initialized and closed.
        TODO:  Make sure that there is no disconnect between the waveform generation and the exposure time.
        TODO:  Add ability to save the data.
        """

        #  Interrogate the Experiment Settings
        microscope_state = self.experiment.MicroscopeState
        prefix_len = len('channel_')
        for channel_key in microscope_state['channels']:
            if self.stop_acquisition or self.stop_send_signal:
                break
            channel_idx = int(channel_key[prefix_len:])
            channel = microscope_state['channels'][channel_key]
            if channel['is_selected'] is True:

                #  Get the parameters
                self.current_channel = channel_idx
                self.current_exposure_time = channel['camera_exposure_time']
                self.current_filter = channel['filter']
                self.current_laser = channel['laser']
                self.current_laser_index = channel['laser_index']

                #  Set the parameters
                self.camera.set_exposure_time(self.current_exposure_time)
                self.filter_wheel.set_filter(self.current_filter)
                self.daq.laser_idx = self.current_laser_index
                if self.verbose:
                    print("Channel:", self.current_channel)
                    print("Camera Exposure Time:", self.current_exposure_time)
                    print("Filter Wheel:", self.current_filter)

                self.snap_image()
                # may need to add some wait time
                # if (readout time + exposure time) > (time to move filter_wheel + daq), then add a wait time


    def run_live_acquisition(self):
        """
        #  Stream live image to the GUI.
        #  Recalculates the waveforms for each image, thereby allowing people to adjust
        #  acquisition parameters in real-time.
        """
        self.stop_acquisition = False
        while self.stop_acquisition is False and self.stop_send_signal is False:
            self.run_single_acquisition()

    def run_z_stack_acquisition(self, is_multi_position, update_view):
        self.camera.initialize_image_series(self.data_ptr)

        microscope_state = self.experiment.MicroscopeState
        for time_idx in range(microscope_state['timepoints']):
            if is_multi_position is True:
                for position_idx in range(len(microscope_state['stage_positions'])):
                    if self.verbose:
                        print("Position :", position_idx)
                    microscope_position = microscope_state['stage_positions'][position_idx]
                    self.stages.move_absolute(microscope_position)
                    if microscope_state['stack_cycling_mode'] == 'per_stack':
                        #  self.per_stack_acquisition(microscope_state, microscope_position)
                        pass
                    elif microscope_state['stack_cycling_mode'] == 'per_z':
                        #  self.per_z_acquisition(microscope_state, microscope_position)
                        pass
            elif is_multi_position is False:
                self.stages.create_position_dict()
                microscope_position = self.stages.position_dict
                print(microscope_position)
                if microscope_state['stack_cycling_mode'] == 'per_stack':
                    #  self.per_stack_acquisition(microscope_state, microscope_position)
                    pass
                elif microscope_state['stack_cycling_mode'] == 'per_z':
                    #  self.per_z_acquisition(microscope_state, microscope_position)
                    pass
        self.camera.close_image_series()

    def per_stack_acquisition(self, microscope_state, microscope_position):
        prefix_len = len('channel_')
        for channel_key in microscope_state['channels']:
            channel_idx = int(channel_key[prefix_len:])
            channel = microscope_state['channels'][channel_key]
            if channel['is_selected'] is True:
                if self.verbose:
                    print("Channel :", channel_idx)

                self.current_channel = channel_idx
                self.current_exposure_time = channel['camera_exposure_time']
                self.current_filter = channel['filter']
                self.current_laser = channel['laser']

                #  Set the parameters
                self.camera.set_exposure_time(self.current_exposure_time)
                self.filter_wheel.set_filter(self.current_filter)
                self.daq.identify_laser_idx(self.current_laser)

                self.open_shutter()
                self.daq.create_waveforms()
                self.daq.start_tasks()

                for z_idx in range(int(microscope_state['number_z_steps'])):
                    print("Z slice :", z_idx)
                    self.daq.run_tasks()
                    image = self.camera.get_image()
                    if microscope_state['is_save']:
                        # Save the data.
                        pass
                    microscope_position['Z'] = microscope_position['Z'] + microscope_state['step_size']
                    self.stages.move_absolute(microscope_position)
            self.close_shutter()

    def per_z_acquisition(self, microscope_state, microscope_position):
        for z_idx in range(int(microscope_state['number_z_steps'])):
            for channel_idx in range(len(microscope_state['channels'])):
                # Check if it is selected.
                if microscope_state['channels']['is_selected']:
                    print("Channel :", channel_idx)
                    self.camera.set_exposure_time(microscope_state['channels']
                                                  ['channel_' + str(channel_idx + 1)]
                                                  ['camera_exposure_time']/1000)
                    self.filter_wheel.set_filter(microscope_state['channels']
                                                 ['channel_' + str(channel_idx + 1)]
                                                 ['filter'])
                    self.daq.identify_laser_idx(self.experiment.MicroscopeState['channels']
                                                ['channel_' + str(channel_idx + 1)]
                                                ['laser'])
                    self.open_shutter()
                    self.daq.create_waveforms()
                    self.daq.start_tasks()
                    self.daq.run_tasks()
                    image = self.camera.get_image()
                    if microscope_state['is_save']:
                        # Save the data.
                        pass
                    microscope_position['Z'] = microscope_position['Z'] + microscope_state['step_size']
                    self.stages.move_absolute(microscope_position)

    def generate_image_name(self):
        """
        #  Generates a string for the filename
        #  e.g., CH00_000000.tif
        """
        image_name = "CH0" + str(self.current_channel) + "_" + str(self.current_time_point).zfill(6) + ".tif"
        self.current_time_point += 1
        return image_name

if __name__ == '__main__':
    """ Testing Section """
    pass