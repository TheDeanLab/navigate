# Standard Library Imports
import time
import os

# Third Party Imports
import numpy as np

# Local Imports
from .aslm_model_functions import *
from .aslm_model_config import Session as session
from controller.thread_pool import SynchronizedThreadPool
from tifffile import imsave


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

        self.camera = start_camera(self.configuration, self.experiment, self.verbose)
        self.stages = start_stages(self.configuration, self.verbose)
        self.filter_wheel = start_filter_wheel(self.configuration, self.verbose)
        self.zoom = start_zoom_servo(self.configuration, self.verbose)
        self.daq = start_daq(self.configuration, self.experiment, self.etl_constants, self.verbose)
        # self.laser = start_lasers(self.configuration, self.verbose)
        self.shutter = start_shutters(self.configuration, self.experiment, self.verbose)
        #self.etl = start_etl(self.configuration, self.verbose)

        # Acquisition Housekeeping
        self.threads_pool = SynchronizedThreadPool()
        self.stop_acquisition = False
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

    #  Basic Image Acquisition Functions
    #  - These functions are used to acquire images from the camera
    #  - Tasks for delivering analog and digital outputs are already initiated by the DAQ object
    #  - daq.create_waveforms() calculates the waveforms and writes them to tasks.
    #  - daq.start_tasks() starts the tasks, which then wait for an external trigger.
    #  - daq.run_tasks() delivers the external trigger which synchronously starts the tasks and waits for completion.
    #  - daq.stop_tasks() stops the tasks and cleans up.

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
        self.camera.initialize_image_series()

        #  Prepare the DAQ for Waveform Delivery
        self.daq.create_tasks()
        self.daq.create_waveforms()
        self.daq.start_tasks()

        #  Trigger everything and grab the image.
        self.daq.run_tasks()
        self.data = self.camera.get_image()

        #  Close everything.
        self.daq.stop_tasks()
        self.daq.close_tasks()
        self.camera.close_image_series()

        return self.data

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
        number_of_channels = 0
        for channel_idx in range(len(self.experiment.MicroscopeState['channels'])):
            # Check if it is selected.
            if self.experiment.MicroscopeState['channels']['is_selected']:
                number_of_channels = number_of_channels + 1
        return number_of_channels

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
        self.camera.initialize_image_series()
        self.daq.initialize_tasks()

        self.filter_wheel.set_filter(self.experiment.MicroscopeState['channels']['channel_1']['filter'])
        self.daq.identify_laser_idx(self.experiment.MicroscopeState['channels']['channel_1']['laser'])
        self.open_shutter()
        self.daq.start_tasks()
        self.daq.create_waveforms()
        self.daq.run_tasks()
        self.daq.stop_tasks()
        image = self.camera.get_image()
        self.close_shutter()
        self.camera.close_image_series()

    def load_experiment_file(self, experiment_path):
        # Loads the YAML file for all of the experiment parameters
        self.experiment = session(experiment_path, self.verbose)

    def run_single_acquisition(self, update_view=None):
        """
        This function retrieves the state of the microscope from the GUI, iterates through each selected channel,
        and snaps an image for each channel setting.  In each iteration, the camera is initialized and closed.
        """

        #  Interrogate the Experiment Settings
        microscope_state = self.experiment.MicroscopeState
        prefix_len = len('channel_')
        for channel_key in microscope_state['channels']:
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
                self.daq.sweep_time = self.current_exposure_time

                # self.daq.identify_laser_idx(self.current_laser)
                if self.verbose:
                    print("Channel:", self.current_channel)
                    print("Camera Exposure Time:", self.current_exposure_time)
                    print("Filter Wheel:", self.current_filter)
                    print("Waveform Sweeptime:", self.daq.sweep_time)

                #  Acquire the Image
                image_data = self.snap_image()

                #  Update the View
                if update_view is not None:
                    update_view()
                    if self.verbose:
                        print("Updated the Camera View Panel")

            #  Save the Data
            if microscope_state['is_save']:
                image_name = self.generate_image_name()
                imsave(os.path.join(self.experiment.Saving['save_directory'], image_name), image_data)

    def run_live_acquisition(self, update_view):
        """
        #  Stream live image to the GUI.
        #  Recalculates the waveforms for each image, thereby allowing people to adjust
        #  acquisition parameters in real-time.
        """
        self.stop_acquisition = False
        while self.stop_acquisition is False:
            self.run_single_acquisition(update_view)

    def run_z_stack_acquisition(self, is_multi_position, update_view):
        self.camera.initialize_image_series()

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
        return image_name

if __name__ == '__main__':
    """ Testing Section """
    pass