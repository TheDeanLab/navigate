__all__ = ['start_camera', 'start_stages', 'start_zoom_servo',
           'start_filter_wheel', 'start_lasers', 'start_model']
import sys

from model.aslm_model import Model

def start_camera(model, camera_id, verbose):
    """
    Initializes the camera.
    """
    # Hamamatsu Camera
    if model.CameraParameters['type']== 'HamamatsuOrca':
        from model.camera.Hamamatsu.HamamatsuCamera import Camera as CameraModel
        cam = CameraModel(camera_id, model, verbose)
        cam.initialize_camera()
        cam.set_exposure(model.CameraParameters['camera_exposure_time'])
        if verbose:
            print("Initialized ", model.CameraParameters['type'])

    # Synthetic Camera
    elif model.CameraParameters['type'] == 'SyntheticCamera':
        from model.camera.SyntheticCamera import Camera as CameraModel
        cam = CameraModel(0, model, verbose)
        cam.initialize_camera()
        cam.set_exposure(model.CameraParameters['camera_exposure_time'])
        if verbose:
            print("Initialized ", model.CameraParameters['type'])

    # Failed to Initialize
    else:
        print("Camera Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    return cam

def start_stages(model, verbose):
    """
    Initializes the Stage.
    """
    # Physik Instrumente Stage
    if model.StageParameters['stage_type'] == 'PI':
        from model.stages.PI.PIStage import Stage as StageModel
        stage = StageModel(model, verbose)
        if verbose:
            print("Initialized ", model.StageParameters['stage_type'])
        stage.report_position()

    # Synthetic Stage
    elif model.StageParameters['stage_type'] == 'SyntheticStage':
        from model.stages.SyntheticStage import Stage as StageModel
        if verbose:
            print("Initialized ", model.StageParameters['stage_type'])

    # Failed to Initialize
    else:
        print("Stage Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    return stage

def start_zoom_servo(model, verbose):
    """
    Initializes the Zoom Servo Motor
    """

    # Dynamixel Servo
    if model.ZoomParameters['zoom_type'] == 'Dynamixel':
        from model.zoom.Dynamixel.DynamixelZoom import Zoom as ZoomModel
        zoom = ZoomModel(model, verbose)
        if verbose:
            print("Initialized ", model.ZoomParameters['zoom_type'])
        print("Zoom Position", zoom.read_position())

    # Synthetic Servo
    #TODO: Make the synthetic servo class.
    elif model.ZoomParameters['zoom_type'] == 'SyntheticZoom':
        from model.zoom.SyntheticZoom import Zoom as ZoomModel
        zoom = ZoomModel(model, verbose)
        if verbose:
            print("Initialized ", model.ZoomParameters['zoom_type'])
        print("Zoom Position", zoom.read_position())
    else :
        print("Zoom Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    return zoom

def start_filter_wheel(model, verbose):
    pass

def start_lasers(model, verbose):
    pass

def start_model(configuration_path, verbose):
    global model
    model = Model(configuration_path, verbose)
    return model
