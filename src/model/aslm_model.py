
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

        self.cam = start_camera(self.configuration, 0, self.verbose)
        self.stages = start_stages(self.configuration, self.verbose)
        self.filter_wheel = start_filter_wheel(self.configuration, self.verbose)
        self.zoom = start_zoom_servo(self.configuration, self.verbose)
        self.daq = start_daq(self.configuration, self.experiment, self.etl_constants, self.verbose)
        self.laser = start_lasers(self.configuration, self.verbose)
        #self.etl = start_etl(self.configuration, self.verbose)

    def continuous_acquisition_mode(self, args):
        """
        Runs the continuous acquisition mode.
        """

        #  TODO: Automatically cycle through each of the channels (channel_1, channel_2, channel_3) if 'is_selected'
        # number_of_channels = len(channel_settings)
        # for channel_idx in range(number_of_channnels):
        #     pass

        # Single Channel
        # Set the filter wheel
        # TODO: Generate method that knows how long it will take for the filter wheel to move.
        self.filter_wheel.set_filter(self.Experiment.MicroscopeState['channel_1']['filter'])

        #  Set the camera exposure time.
        #  TODO: Need to make sure that the units are correct (milliseconds, microseconds, etc.)
        self.camera.set_exposure(self.Experiment['MicroscopeState']['channel_1']['camera_exposure_time'])

        # Set the laser and laser intensity
        self.daq.identify_laser_idx(self.Experiment['MicroscopeState']['channel_1']['laser'])

        #  Prepare the data acquisition card (sends and receives voltages)
        #  TODO: Seems to be a disconnect between waveform generation and the camera exposure time.
        self.daq.create_tasks()
        self.daq.write_waveforms_to_tasks()
        self.daq.start_tasks()
        self.daq.run_tasks()

        #TODO: if the one of the args is 'save to device' then you could save it to device.
        #image = self.camera.read_camera()

        # Send the image to the GUI

    def load_experiment_file(self, experiment_path):
        # Loads the YAML file for all of the experiment parameters
        self.experiment = session(experiment_path, self.verbose)

if __name__ == '__main__':
    """ Testing Section """
    pass