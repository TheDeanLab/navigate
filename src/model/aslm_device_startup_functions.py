# Standard Library Imports
import platform
import sys

# Third Party Imports

# Local Imports
from model.devices.zoom import DynamixelZoom, SyntheticZoom
from model.devices.filter_wheels import SutterFilterWheel, SyntheticFilterWheel
from model.devices.laser_shutters import ThorlabsShutter, SyntheticShutter
from model.devices.laser_triggers import LaserTriggers, SyntheticLaserTriggers
from model.devices.cameras import HamamatsuOrca, SyntheticCamera


def start_camera(configuration, experiment, verbose):
    """
    # Initializes the camera as a sub-process using concurrency tools.
    """
    camera_id = 0 # Becomes important when a second camera must be dealth with.
    if configuration.Devices['camera'] == 'HamamatsuOrca' and platform.system() == 'Windows':
        return HamamatsuOrca(camera_id, configuration, experiment, verbose)
    elif configuration.Devices['camera'] == 'SyntheticCamera':
        return SyntheticCamera(camera_id, configuration, experiment, verbose)
    else:
        device_not_found(configuration.Devices['camera'])


def start_stages(configuration, verbose):
    """
    # Initializes the Stage.
    """
    # Physik Instrumente Stage
    if configuration.Devices['stage'] == 'PI' and platform.system() == 'Windows':
        from model.devices.stages.PI.PIStage import Stage as StageModel
        stage = StageModel(configuration, verbose)
        stage.report_position()
    # Synthetic Stage
    elif configuration.Devices['stage'] == 'SyntheticStage':
        from model.devices.stages.SyntheticStage import Stage as StageModel
        stage = StageModel(configuration, verbose)
    else:
        print("Stage Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    if verbose:
        print("Initialized ", configuration.Devices['stage'])
    return stage


def start_zoom_servo(configuration, verbose):
    """
    # Initializes the Zoom Servo Motor. DynamixelZoom of SyntheticZoom
    """
    if configuration.Devices['zoom'] == 'DynamixelZoom':
        return DynamixelZoom(configuration, verbose)
    elif configuration.Devices['zoom'] == 'SyntheticZoom':
        return SyntheticZoom(configuration, verbose)
    else:
        device_not_found(configuration.Devices['zoom'])


def start_filter_wheel(configuration, verbose):
    """
    # Initializes the Filter Wheel. Sutter or SyntheticFilterWheel
    """
    if configuration.Devices['filter_wheel'] == 'SutterFilterWheel':
        return SutterFilterWheel(configuration, verbose)
    elif configuration.Devices['filter_wheel'] == 'SyntheticFilterWheel':
        return SyntheticFilterWheel(configuration, verbose)
    else:
        device_not_found(configuration.Devices['filter_wheel'])


def start_lasers(configuration, verbose):
    '''
    # Start the lasers: Lasers or SyntheticLasers
    '''
    if configuration.Devices['lasers'] == 'Omicron':
        # This is the Omicron LightHUB Ultra Launch - consists of both Obis and Luxx lasers.
        from model.devices.lasers.coherent.ObisLaser import ObisLaser as obis
        from model.devices.lasers.omicron.LuxxLaser import LuxxLaser as luxx

        # Iteratively go through the configuration file and turn on each of the lasers,
        # and make sure that they are in appropriate external control mode.
        laser = {}
        for laser_idx in range(configuration.LaserParameters['number_of_lasers']):
            if laser_idx == 0:
                # 488 nm LuxX laser
                print("Initializing 488 nm LuxX Laser")
                comport = 'COM19'
                laser[laser_idx] = luxx(comport, verbose)
                laser[laser_idx].initialize_laser()

            elif laser_idx == 1:
                # 561 nm Obis laser
                print("Initializing 561 nm Obis Laser")
                comport = 'COM4'
                laser[laser_idx] = obis(comport, verbose)
                laser[laser_idx].set_laser_operating_mode('mixed')

            elif laser_idx == 2:
                # 642 nm LuxX laser
                print("Initializing 642 nm LuxX Laser")
                comport = 'COM17'
                laser[laser_idx] = luxx(comport, verbose)
                laser[laser_idx].initialize_laser()

            else:
                print("Laser index not recognized")
                sys.exit()

    elif configuration.Devices['lasers'] == 'SyntheticLasers':
        from model.devices.lasers.SyntheticLaser import SyntheticLaser
        laser = SyntheticLaser(configuration, verbose)

    else:
        print("Laser Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()

    if verbose:
        print("Initialized ", configuration.Devices['lasers'])

    return laser


def start_daq(configuration, experiment, etl_constants, verbose):
    """
    # Start the data acquisition device (DAQ):  NI or SyntheticDAQ
    """
    if configuration.Devices['daq'] == 'NI':
        from model.devices.daq.NI.NIDAQ import DAQ as DAQModel
        return DAQModel(configuration, experiment, etl_constants, verbose)
    elif configuration.Devices['daq'] == 'SyntheticDAQ':
        from model.devices.daq.SyntheticDAQ import DAQ as DAQModel
        return DAQModel(configuration, experiment, etl_constants, verbose)
    else:
        device_not_found(configuration.Devices['daq'])


def start_shutters(configuration, experiment, verbose):
    """
    # Initializes the shutters: ThorlabsShutter or SyntheticShutter
    # Shutters are triggered via digital outputs on the NI DAQ Card
    # Thus, requires both to be enabled.
    """
    if configuration.Devices['shutters'] == 'ThorlabsShutter' and configuration.Devices['daq'] == 'NI':
        return ThorlabsShutter(configuration, experiment, verbose)
    elif configuration.Devices['shutters'] == 'SyntheticShutter':
        return SyntheticShutter(configuration, experiment, verbose)
    else:
        device_not_found(configuration.Devices['shutters'])


def start_laser_triggers(configuration, experiment, verbose):
    """
    # Initializes the Laser Switching DAQ Output:
    """
    if configuration.Devices['daq'] == 'NI':
        return LaserTriggers(configuration, experiment, verbose)
    elif configuration.Devices['daq'] == 'SyntheticDAQ':
        return SyntheticLaserTriggers(configuration, experiment, verbose)
    else:
        device_not_found(configuration.Devices['daq'])


def device_not_found(args):
    print("Device Not Found in Configuration.YML:", args)
    sys.exit()