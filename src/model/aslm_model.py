
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

        # Initialize all Hardware
        if args.synthetic_hardware:
            # If command line entry provided, overwrites the model parameters with synthetic hardware
            self.configuration.Devices['daq'] = 'SyntheticDAQ'
            self.configuration.Devices['camera'] = 'SyntheticCamera'
            self.configuration.Devices['etl'] = 'SyntheticETL'
            self.configuration.Devices['filter_wheel'] = 'SyntheticFilterWheel'
            self.configuration.Devices['stage'] = 'SyntheticStage'
            self.configuration.Devices['zoom'] = 'SyntheticZoom'
            self.configuration.Devices['lasers'] = 'SyntheticLasers'

        self.cam = start_camera(self.configuration, 0, self.verbose)
        self.stages = start_stages(self.configuration, self.verbose)
        self.filter_wheel = start_filter_wheel(self.configuration, self.verbose)
        self.zoom = start_zoom_servo(self.configuration, self.verbose)
        self.daq = start_daq(self.configuration, etl_constants_path, self.verbose)
        self.laser = start_lasers(self.configuration, self.verbose)
        #self.etl = start_etl(self.configuration, self.verbose)

    def continuous_acquisition_mode(channel_settings):
        """
        FOR ANNIE: We control different hardware elements using different mechanisms.  The laser is controlled by
        The laser is turned on/off by sending a digital signal.  This is either 0V or 5V.  This signal is sent by the
        daq card.  You can see in the configuration file where these signals are physically connected.
        Likewise, the intensity is controlled by an analog signal.  0V is the lowest intensity and 5V is the highest.
        We need to make sure that we do not send signals that are negative, or greater than 5V.  This is also specified
        in the configuration file.

        For example, the wavelength, laser_0_wavelength, is 488 nm.
        The digital output channel for laser_0 is PXI6733/port0/line2
        The analog output channel for laser_0 is PXI6733/line5.


        Continuous acquisition mode.
        channel_settings[ch] = [laser, filter, exposure, laser_power, interval]

        Get the channel properties (laser, filter wheel, exposure time).
        Set laser
        Set the filter wheel
        Set the exposure time
        Prepare the data acquisition card (sends and receives voltages)
        Once everything has prepared itself, send out the voltage that triggers the camera.


        """
        # Determine the number of channels to image
        number_of_channels = len(channel_settings)

        # Set the laser.  Controlled by the DAQ card.  Delivered as  a digital signal for on/off, analog for intensity.

        # Set the filter wheel
        self.filter_wheel.set_filter(channel_settings[0]['filter'])

        # Set the exposure time - Need to make sure that the units are correct (milliseconds, microseconds, etc.)
        self.camera.set_exposure(channel_settings[0]['exposure'])

        # Prepare the data acquisition card (sends and receives voltages)
        # self.daq.calculate_samples() # calculates how many data points
        # self.daq.create_waveforms() # calculates the waveforms. Many of these values are stored in the View.
        # self.daq.start_tasks() # starts the tasks.

        # Grab the image and send it to the view.

    def load_experiment_file(self, experiment_path):
        # Loads the YAML file for all of the experiment parameters
        self.experiment = session(experiment_path, self.verbose)

if __name__ == '__main__':
    """ Testing Section """
    pass