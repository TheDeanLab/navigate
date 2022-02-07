# Standard Library Imports
import os
import time

# Third Party Imports
from tifffile import imsave
import numpy as np

# Local Imports
from .aslm_model_functions import *
from .aslm_model_config import Session as session
# from model.concurrency.concurrency_tools import ObjectInSubprocess

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
        self.laser = start_lasers(self.configuration, self.verbose)
        self.shutter = start_shutters(self.configuration, self.experiment, self.verbose)
        #self.etl = start_etl(self.configuration, self.verbose)

        # Acquisition Housekeeping
        self.stop_flag = False
        self.image_count = 0
        self.acquisition_count = 0
        self.total_acquisition_count = None
        self.total_image_count = None
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
        self.daq.create_tasks()
        self.daq.write_waveforms_to_tasks()
        self.daq.start_tasks()
        self.daq.run_tasks()
        self.data = self.camera.get_image()
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

    def live(self):
        """
        #  Stream live image to the GUI.
        #  Recalculates the waveforms for each image, thereby allowing people to adjust
        #  acquisition parameters in real-time.
        """
        self.stop_flag = False
        self.open_shutter()
        while self.stop_flag is False:
            self.snap_image()
        self.close_shutters()

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

    def run_acquisition(self, acq):
        """
        # Acquire all of the image volumes in the acquisition list.
        # Meant more to be an example of how it was performed in the mesoSPIM software
        """
        self.prepare_acquisition_list()
        self.open_shutter()

        # for i in range(self.total_image_count):
        #     if self.stopflag is True:
        #         self.close_image_series()
        #         break
        #     else:
        #         self.snap_image_in_series()
        #         # move_dict = acq.get_delta_dict()
        #         # f_step = self.f_step_generator.__next__()
        #         if f_step != 0:
        #             move_dict.update({'f_rel': f_step})
        #
        #         self.move_relative(move_dict)
        #         self.image_count += 1
        #
        #         ''' Keep track of passed time and predict remaining time '''
        #         time_passed = time.time() - self.start_time
        #         # time_remaining = self.state['predicted_acq_list_time'] - time_passed
        #
        #         ''' If the time to set up everything is longer than the predicted
        #         acq time, the remaining time turns negative - here a different
        #         calculation should be employed here: '''
        #         if time_remaining < 0:
        #             time_passed = time.time() - self.image_acq_start_time
        #             time_remaining = self.state['predicted_acq_list_time'] - time_passed
        #
        #         self.state['remaining_acq_list_time'] = time_remaining
        #         framerate = self.image_count / time_passed
        #
        #         ''' Every 100 images, update the predicted acquisition time '''
        #         if self.image_count % 100 == 0:
        #             framerate = self.image_count / time_passed
        #             self.state['predicted_acq_list_time'] = self.total_image_count / framerate
        #
        #
        #         self.send_progress(self.acquisition_count,
        #                            self.total_acquisition_count,
        #                            i,
        #                            self.total_image_count,
        #                            self.total_image_count,
        #                            self.image_count,
        #                            convert_seconds_to_string(time_passed),
        #                            convert_seconds_to_string(time_remaining))
        #
        # self.image_acq_end_time = time.time()
        # self.image_acq_end_time_string = time.strftime("%Y%m%d-%H%M%S")

        self.close_shutters()

    def acquire_z_stack(self):
        microscope_state = self.experiment.MicroscopeState
        pass

        self.camera.initialize_image_series()

        for time_idx in range(microscope_state['timepoints']):
            #  TODO: Should evaluate if the multiposition checkbox is selected.
            for position_idx in range(len(microscope_state['stage_positions'])):
                if self.verbose:
                    print("Position :", position_idx)
                microscope_position = microscope_state['stage_positions'][position_idx]
                self.stages.move_absolute(microscope_position)

                if microscope_state['stack_cycling_mode'] == 'per_stack':
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
                elif microscope_state['stack_cycling_mode']  == 'per_z':
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
                else:
                    raise UserWarning('Stack Cycling Mode Not Recognized')
                    break

        self.camera.close_image_series()

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
        self.camera.set_exposure_time(self.experiment.MicroscopeState['channels']['channel_1']['camera_exposure_time']/1000)
        self.camera.initialize_image_series()
        #  self.filter_wheel.set_filter(self.experiment.MicroscopeState['channels']['channel_1']['filter'])
        self.daq.identify_laser_idx(self.experiment.MicroscopeState['channels']['channel_1']['laser'])
        self.open_shutter()
        self.daq.create_waveforms()
        self.daq.start_tasks()
        self.daq.run_tasks()
        self.daq.stop_tasks()
        image = self.camera.get_image()
        #  self.save_test_image(image)
        self.close_shutter()
        self.camera.close_image_series()

    def save_test_image(self, image):
        save_path = os.path.join('E:', 'PLEASE', 'test.tif')
        imsave(save_path, image)
        if self.verbose:
            print("Image saved")

    def load_experiment_file(self, experiment_path):
        # Loads the YAML file for all of the experiment parameters
        self.experiment = session(experiment_path, self.verbose)

if __name__ == '__main__':
    """ Testing Section """
    pass