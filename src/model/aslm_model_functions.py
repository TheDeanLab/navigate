from model.concurrency.concurrency_tools import ObjectInSubprocess
import platform
import sys

def start_camera(session, camera_id, verbose):
    """
    Initializes the camera.
    self.cam = start_camera(self.session, self.camera_id, verbose)
    """
    # Hamamatsu Camera
    if session.CameraParameters['type'] == 'HamamatsuOrca' and platform.system() == 'Windows':
        from model.devices.camera.Hamamatsu.HamamatsuCamera import Camera as CameraModel
        cam = ObjectInSubprocess(CameraModel, camera_id, verbose)
        cam.initialize_camera()
        cam.set_exposure(session.StartupParameters['camera_exposure_time'])
    elif session.CameraParameters['type'] == 'HamamatsuOrca' and platform.system() != 'Windows':
        print("Hamamatsu Camera is only supported on Windows operating systems.")
        sys.exit()
    elif session.CameraParameters['type'] == 'SyntheticCamera':
        from model.devices.camera.SyntheticCamera import Camera as CameraModel
        cam = CameraModel(0, verbose)
        cam.initialize_camera()
        cam.set_exposure(1000*session.StartupParameters['camera_exposure_time'])
    else:
        print("Camera Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    if verbose:
        print("Initialized ", session.CameraParameters['type'])
    return cam

def start_stages(session, verbose):
    """
    Initializes the Stage.
    """
    # Physik Instrumente Stage
    if session.StageParameters['type'] == 'PI' and platform.system() == 'Windows':
        from model.devices.stages.PI.PIStage import Stage as StageModel
        stage = StageModel(session, verbose)
        stage.report_position()
    # Synthetic Stage
    elif session.StageParameters['type'] == 'SyntheticStage':
        from model.devices.stages.SyntheticStage import Stage as StageModel
        stage = StageModel(session, verbose)
    else:
        print("Stage Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    if verbose:
        print("Initialized ", session.StageParameters['type'])
    return stage

def start_zoom_servo(session, verbose):
    """
    Initializes the Zoom Servo Motor. Dynamixel of SyntheticZoom
    """
    if session.ZoomParameters['type'] == 'Dynamixel':
        from model.devices.zoom.dynamixel.DynamixelZoom import Zoom as ZoomModel
        zoom = ZoomModel(session, verbose)
    elif session.ZoomParameters['type'] == 'SyntheticZoom':
        from model.devices.zoom.SyntheticZoom import Zoom as ZoomModel
        zoom = ZoomModel(session, verbose)
    else:
        print("Zoom Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    if verbose:
        print("Initialized ", session.ZoomParameters['type'])
        print("Zoom Position", zoom.read_position())
    return zoom

def start_filter_wheel(session, verbose):
    """
    Initializes the Filter Wheel. Sutter or SyntheticFilterWheel
    """
    if session.FilterWheelParameters['type'] == 'Sutter':
        from model.devices.filter_wheel.Sutter.Lambda10B import FilterWheel as FilterWheelModel
        filter_wheel = FilterWheelModel(session, verbose)
    elif session.FilterWheelParameters['type'] == 'SyntheticFilterWheel':
        from model.devices.filter_wheel.SyntheticFilterWheel import SyntheticFilterWheel as FilterWheelModel
        filter_wheel = FilterWheelModel(session, verbose)
    else:
        print("Filter Wheel Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    if verbose:
        print("Initialized ", session.FilterWheelParameters['type'])
    return filter_wheel

def start_lasers(session, verbose):
    '''
    Start the lasers: Lasers or SyntheticLasers
    '''
    if session.LaserParameters['laser_type'] == 'Lasers':
        from model.devices.lasers.Lasers.Lasers import Lasers as LasersModel
        lasers = LasersModel(session, verbose)
    elif session.LaserParameters['laser_type'] == 'SyntheticLasers':
        from model.devices.lasers.SyntheticLasers.SyntheticLasers import SyntheticLasers as SyntheticLasersModel
        lasers = SyntheticLasersModel(session, verbose)
    else:
        print("Laser Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    if verbose:
        print("Initialized ", self.session.LaserParameters['laser_type'])
    return lasers

def start_daq(session, etl_constants_path, verbose):
    """
    Start the data acquisition device (DAQ):  NI or SyntheticDAQ
    """
    if session.DAQParameters['hardware_type'] == 'NI':
        from model.devices.daq.NI.NIDAQ import DAQ as DAQModel
        daq = DAQModel(session, etl_constants_path, verbose)
    elif session.DAQParameters['hardware_type'] == 'SyntheticDAQ':
        from model.devices.daq.SyntheticDAQ import DAQ as DAQModel
        daq = DAQModel(session, etl_constants_path, verbose)
    else:
        print("DAQ Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    if verbose:
        print("Initialized ", session.DAQParameters['hardware_type'])
    return daq