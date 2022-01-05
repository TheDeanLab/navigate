
# Local Imports
from .aslm_model_functions import *
from .aslm_model_config import Session as session

class Model:
    def __init__(self, args, file_path=None):
        # Retrieve the initial configuration from the yaml file
        self.verbose = args.verbose

        # Loads the YAML file for all of the microscope parameters
        self.session = session(file_path, args.verbose)

        # Initialize all Hardware
        if args.synthetic_hardware:
            # If command line entry provided, overwrites the model parameters with synthetic hardware
            self.session.DAQParameters['hardware_type'] = 'SyntheticDAQ'
            self.session.CameraParameters['type'] = 'SyntheticCamera'
            self.session.ETLParameters['type'] = 'SyntheticETL'
            self.session.FilterWheelParameters['type'] = 'SyntheticFilterWheel'
            self.session.StageParameters['type'] = 'SyntheticStage'
            self.session.ZoomParameters['type'] = 'SyntheticZoom'

        # self.daq = start_daq(self.session, self.verbose)
        self.cam = start_camera(self.session, 0, self.verbose)
        self.stages = start_stages(self.session, self.verbose)
        self.filter_wheel = start_filter_wheel(self.session, self.verbose)


    def continuous_acquisition_mode(channel_settings):
        """
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
        #set.d

        # Set the filter wheel
        self.filter_wheel.set_filter(channel_settings[0]['filter'])

if __name__ == '__main__':
    """ Testing Section """
    pass