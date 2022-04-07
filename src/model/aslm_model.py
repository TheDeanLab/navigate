# Standard Library Imports
import time
import os
import threading
import ctypes

# Third Party Imports
import numpy as np

# Local Imports
from .aslm_device_startup_functions import *
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
        if args.synthetic_hardware or args.sh:
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
        threads_dict = {
            'filter_wheel':     ResultThread(target=start_filter_wheel,
                                             args=(self.configuration, self.verbose)).start(),
            'zoom':             ResultThread(target=start_zoom_servo,
                                             args=(self.configuration, self.verbose)).start(),
            'camera':           ResultThread(target=start_camera,
                                             args=(self.configuration, self.experiment, self.verbose,)).start(),
            'stages':           ResultThread(target=start_stages,
                                             args=(self.configuration, self.verbose,)).start(),
            'shutter':          ResultThread(target=start_shutters,
                                             args=(self.configuration, self.experiment, self.verbose,)).start(),
            'daq':              ResultThread(target=start_daq,
                                             args=(self.configuration, self.experiment, self.etl_constants, self.verbose,)).start(),
            'laser_triggers':   ResultThread(target=start_laser_triggers,
                                             args=(self.configuration, self.experiment, self.verbose,)).start(),
            # 'etl': ResultThread(target=start_etl, args=(self.configuration, self.verbose,)).start()
        }
        for k in threads_dict:
            if k != 'serial_devices':
                setattr(self, k, threads_dict[k].get_result())
            else:
                threads_dict[k].get_result()

        # in synthetic_hardware mode, we need to wire up camera to daq
        # TODO: Confirm that I did not mess this up.
        if args.synthetic_hardware:
            self.daq.set_camera(self.camera)

        # Set Default Camera Settings
        # self.camera.dev_open(0)
        # # self.camera.dcam_set_default_light_sheet_mode_parameters()
        # self.camera.dcam_set_default_area_mode_parameters()

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
        # self.data_buffer = [SharedNDArray(shape=(self.camera.y_pixels, self.camera.x_pixels), dtype='uint16') for i in range(NUM_OF_FRAMES)]
        # show image function/pipe handler
        self.show_img_pipe = None

    def set_show_img_pipe(self, handler):
        """
        # wire up show image function/pipe
        """
        self.show_img_pipe = handler

    def set_data_buffer(self, data_buffer):
        self.data_buffer = data_buffer
        self.camera.initialize_image_series(self.data_buffer)
    
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
                print('Error: have not set up data buffer!')
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
            self.stop_acquisition = False
            self.stop_send_signal = False
            self.open_shutter()
            self.run_single_acquisition()
            self.stop_acquisition = True
            self.run_data_process(1)
            self.close_shutter()

        elif command == 'live':
            self.is_save = False
            self.stop_acquisition = False
            self.stop_send_signal = False
            self.open_shutter()
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
            self.live_thread = threading.Thread(target=self.run_live_acquisition)
            self.live_thread.start()

        elif command == 'stop':
            # stop live thread
            self.stop_acquisition = True
            self.live_thread.join()
            self.data_thread.join()
            self.close_shutter()

    def move_stage(self, pos_dict):
        self.stages.move_absolute(pos_dict)

    def close_shutter(self):
        """
        # Automatically closes both shutters
        """
        self.shutter.close_shutters()

    def end_acquisition(self):
        """
        # 
        """
        # dettach buffer
        # self.camera.close_image_series()
        
        # close shutter
        self.close_shutter()

    def run_data_process(self, num_of_frames=0):
        """
        # This function will listen to camera, when there is a frame ready, it will call next steps to handle the frame data
        """
        count_frame = num_of_frames > 0
        while True:
            frame_ids = self.camera.get_new_frame()
            # frame_ids = self.camera.buf_getlastframedata()
            if self.verbose:
                print('running data process, get frames', frame_ids)
            # if there is at least one frame available
            if frame_ids:
                # analyse image

                # show image
                if self.show_img_pipe:
                    if self.verbose:
                        print('sent through pipe', frame_ids[0])
                    self.show_img_pipe.send(frame_ids[0])
                else:
                    if self.verbose:
                        print('get image frames:', frame_ids)
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
                if self.show_img_pipe:
                    self.show_img_pipe.send('stop')
                if self.verbose:
                    print('data thread is stopped, send stop to parent pipe')
                break


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
        pass #        self.daq.close_tasks()

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
        number_of_positions = len(self.experiment.MicroscopeState['stage_positions'])
        number_of_slices = self.experiment.MicroscopeState['number_z_steps']
        number_of_time_points = self.experiment.MicroscopeState['timepoints']

        self.image_count = 0
        self.acquisition_count = 0
        self.total_acquisition_count = number_of_channels * number_of_positions * number_of_time_points
        self.total_image_count = self.total_acquisition_count * number_of_slices
        self.start_time = time.time()

    def load_experiment_file(self, experiment_path):
        # Loads the YAML file for all of the experiment parameters
        self.experiment = session(experiment_path, self.verbose)

    def run_single_acquisition(self):
        """
        # Called by model.run_command().
        """
        print("in fun_single_acquisition")
        #  Interrogate the Experiment Settings
        microscope_state = self.experiment.MicroscopeState
        prefix_len = len('channel_')
        for channel_key in microscope_state['channels']:
            if self.stop_acquisition or self.stop_send_signal:
                break
            channel_idx = int(channel_key[prefix_len:])
            channel = microscope_state['channels'][channel_key]
            if channel['is_selected'] is True:

                #  Get and set the parameters for Waveform Generation, Triggering, etc.
                self.current_channel = channel_idx

                # Camera Settings - Exposure Time in Milliseconds
                self.camera.set_exposure_time(channel['camera_exposure_time'])

                # Laser Settings
                self.laser_triggers.trigger_digital_laser(self.current_laser_index)
                self.laser_triggers.set_laser_analog_voltage(channel['laser_index'], channel['laser_power'])

                # Filter Wheel Settings
                self.filter_wheel.set_filter(channel['filter'])

                # Update Laser Scanning Waveforms - Exposure Time in Seconds
                self.daq.sweep_time = self.current_exposure_time/1000
                # self.galvo_l_frequency
                # self.galvo_l_amplitude
                # self.galvo_l_offset
                # self.etl_l_amplitude

                # TODO: Add ability to save the data.
                # Save Data

                # Acquire an Image
                self.snap_image()

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

    def run_live_acquisition(self):
        """
        #  Stream live image to the GUI.
        #  Recalculates the waveforms for each image, thereby allowing people to adjust
        #  acquisition parameters in real-time.
        """
        self.stop_acquisition = False
        while self.stop_acquisition is False and self.stop_send_signal is False:
            self.run_single_acquisition()

    def generate_image_name(self):
        """
        #  Generates a string for the filename
        #  e.g., CH00_000000.tif
        """
        image_name = "CH0" + str(self.current_channel) + "_" + str(self.current_time_point).zfill(6) + ".tif"
        self.current_time_point += 1
        return image_name

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

if __name__ == '__main__':
    """ Testing Section """
    pass