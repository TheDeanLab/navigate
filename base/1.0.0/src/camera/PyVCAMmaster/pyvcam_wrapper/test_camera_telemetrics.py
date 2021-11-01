from pyvcam import pvc
from pyvcam.camera import Camera
pvc.init_pvcam() # Initialize PVCAM
cam = next(Camera.detect_camera()) # Use generator to find first camera.
cam.open() # Open the camera.