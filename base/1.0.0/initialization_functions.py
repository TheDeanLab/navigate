__all__ = ['start_camera', 'start_stages']

def start_camera(session, camera_id, verbose):
    """
    Initializes the camera.
    """
    # Hamamatsu Camera
    if session.CameraParameters['type'] == 'HamamatsuOrca':
        from model.camera.Hamamatsu.HamamatsuCamera import Camera as CameraModel
        cam = CameraModel(camera_id, session, verbose)
        cam.initialize_camera()
        cam.set_exposure(session.CameraParameters['camera_exposure_time'])
        if verbose:
            print("Initialized ", session.CameraParameters['type'])

    # Synthetic Camera
    elif session.CameraParameters['type'] == 'SyntheticCamera':
        from model.camera.SyntheticCamera import Camera as CameraModel
        cam = CameraModel(0)
        cam.initialize_camera()
        cam.set_exposure(session.CameraParameters['camera_exposure_time'])
        if verbose:
            print("Initialized ", session.CameraParameters['type'])

    # Failed to Initialize
    else:
        print("Camera Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    return cam

def start_stages(session, verbose):
    """
    Initializes the Stage.
    """
    # Physik Instrumente Stage
    if session.StageParameters['stage_type'] == 'PI':
        from model.stages.PI.PIStage import Stage as StageModel
        stage = StageModel(session, verbose)
        if verbose:
            print("Initialized ", session.StageParameters['stage_type'])
        stage.report_position()

    # Synthetic Stage
    elif session.StageParameters['stage_type'] == 'SyntheticStage':
        from model.stages.SyntheticStage import Stage as StageModel
        if verbose:
            print("Initialized ", session.StageParameters['stage_type'])

    # Failed to Initialize
    else:
        print("Stage Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    return stage

def start_zoom_servo(session, verbose):
    pass

def start_filter_wheel(session, verbose):
    pass

def start_lasers(session, verbose):
    pass


