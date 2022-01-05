def start_camera(model, camera_id, verbose):
    """
    Initializes the camera.
    self.cam = start_camera(self.model, self.camera_id, verbose)
    """
    # Hamamatsu Camera
    if model.CameraParameters['type'] == 'HamamatsuOrca':
        from model.devices.camera.Hamamatsu.HamamatsuCamera import Camera as CameraModel
        cam = CameraModel(camera_id, verbose)
        cam.initialize_camera()
        cam.set_exposure(model.CameraParameters['camera_exposure_time'])
    # Synthetic Camera
    elif model.CameraParameters['type'] == 'SyntheticCamera':
        from model.devices.camera.SyntheticCamera import Camera as CameraModel
        cam = CameraModel(0, verbose)
        cam.initialize_camera()
        cam.set_exposure(1000*model.CameraParameters['camera_exposure_time'])
    else:
        print("Camera Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    if verbose:
        print("Initialized ", model.CameraParameters['type'])
    return cam

def start_stages(model, verbose):
    """
    Initializes the Stage.
    """
    # Physik Instrumente Stage
    if model.StageParameters['type'] == 'PI':
        from model.devices.stages.PI.PIStage import Stage as StageModel
        stage = StageModel(model, verbose)
        stage.report_position()
    # Synthetic Stage
    elif model.StageParameters['type'] == 'SyntheticStage':
        from model.devices.stages.SyntheticStage import Stage as StageModel
        stage = StageModel(model, verbose)
    else:
        print("Stage Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    if verbose:
        print("Initialized ", model.StageParameters['type'])
    return stage

def start_zoom_servo(model, verbose):
    """
    Initializes the Zoom Servo Motor. Dynamixel of SyntheticZoom
    """
    if model.ZoomParameters['type'] == 'Dynamixel':
        from model.devices.zoom.Dynamixel.DynamixelZoom import Zoom as ZoomModel
        zoom = ZoomModel(self.model, verbose)
    elif self.model.ZoomParameters['type'] == 'SyntheticZoom':
        from model.devices.zoom.SyntheticZoom import Zoom as ZoomModel
        zoom = ZoomModel(self.model, verbose)
    else:
        print("Zoom Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    if verbose:
        print("Initialized ", self.model.ZoomParameters['type'])
        print("Zoom Position", zoom.read_position())
    return zoom

def start_filter_wheel(model, verbose):
    """
    Initializes the Filter Wheel. Sutter or SyntheticFilterWheel
    """
    if model.FilterWheelParameters['type'] == 'Sutter':
        from model.devices.filter_wheel.Sutter.Lambda10B import FilterWheel as FilterWheelModel
        filter_wheel = FilterWheelModel(model, verbose)
    elif model.FilterWheelParameters['type'] == 'SyntheticFilterWheel':
        from model.devices.filter_wheel.SyntheticFilterWheel import SyntheticFilterWheel as FilterWheelModel
        filter_wheel = FilterWheelModel(model, verbose)
    else:
        print("Filter Wheel Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    if verbose:
        print("Initialized ", model.FilterWheelParameters['type'])
    return filter_wheel

def start_lasers(model, verbose):
    '''
    Start the lasers: Lasers or SyntheticLasers
    '''
    if model.LaserParameters['laser_type'] == 'Lasers':
        from model.devices.lasers.Lasers.Lasers import Lasers as LasersModel
        lasers = LasersModel(model, verbose)
    elif model.LaserParameters['laser_type'] == 'SyntheticLasers':
        from model.devices.lasers.SyntheticLasers.SyntheticLasers import SyntheticLasers as SyntheticLasersModel
        lasers = SyntheticLasersModel(model, verbose)
    else:
        print("Laser Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    if verbose:
        print("Initialized ", self.model.LaserParameters['laser_type'])
    return lasers

def start_daq(model, verbose):
    """
    Start the data acquisition device (DAQ):  NI or SyntheticDAQ
    """
    if model.DAQParameters['hardware_type'] == 'NI':
        from model.devices.daq.NI.NIDAQ import DAQ as DAQModel
        daq = DAQModel(model, verbose)
    elif model.DAQParameters['hardware_type'] == 'SyntheticDAQ':
        from model.devices.daq.SyntheticDAQ import DAQ as DAQModel
        daq = DAQModel(model, verbose)
    else:
        print("DAQ Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    if verbose:
        print("Initialized ", self.model.DAQParameters['hardware_type'])
    return daq