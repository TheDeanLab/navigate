# Standard Library Imports
import os
import time

# Third Party Imports
from tifffile import imsave

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
            self.configuration.Devices['laser'] = 'SyntheticLaser'
            self.configuration.Devices['shutter'] = 'SyntheticShutter'

        self.camera = start_camera(self.configuration, self.experiment, self.verbose)
        self.stages = start_stages(self.configuration, self.verbose)
        self.filter_wheel = start_filter_wheel(self.configuration, self.verbose)
        self.zoom = start_zoom_servo(self.configuration, self.verbose)
        self.daq = start_daq(self.configuration, self.experiment, self.etl_constants, self.verbose)
        self.laser = start_lasers(self.configuration, self.verbose)
        self.shutter = start_shutters(self.configuration, self.experiment, self.verbose)
        #self.etl = start_etl(self.configuration, self.verbose)

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

    def acquire_with_waveform_update(self):
        """
        # Acquires an image without updating the waveforms.
        # Tasks are initialized during the daq __init__ function.
        """
        # Set the camera in a state where it can be triggered.
        self.camera.set_exposure_time(self.experiment.MicroscopeState['channel_1']['camera_exposure_time']/1000)
        self.camera.initialize_image_series()

        # Change the Filter Wheel to the correct position
        self.filter_wheel.set_filter(self.experiment.MicroscopeState['channel_1']['filter'])

        # Specify the laser
        self.daq.identify_laser_idx(self.experiment.MicroscopeState['channel_1']['laser'])

        # Open the shutter as specified by the experiment parameters.
        self.open_shutter()

        # The NIDAQ tasks are initialized during the daq __init__ function.
        # Not sure if we have to close them in order to get a fresh waveform.
        # if so, self.daq.close_tasks() and self.daq.initialize_tasks() need to be called.
        self.daq.create_waveforms()
        self.daq.start_tasks()
        self.daq.run_tasks()
        self.daq.stop_tasks()

        # Grab the image from the camera and save it.
        image = self.camera.get_image()
        self.save_test_image(image)

        # Close the shutter
        self.close_shutter()

        # Disable the camera
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