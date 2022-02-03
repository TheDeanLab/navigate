"""
Hamamatsu Camera Class

Model class for controlling Hamamatsu cameras via the DCAM-API. At the time of writing this class,
little documentation on the DCAM-API was available. Hamamatsu has a different time schedule regarding support of
their own API. However, Zhuang's lab Github repository had a python driver for the Orca camera and with a bit of
tinkering things worked out.

DCAM-API relies mostly on setting parameters into the camera. The correct data type of each parameter is not well
documented; however it is possible to print all the available properties and work from there.
The properties are stored in a filed named params.txt next to the Hamamatsu Driver located in Controller.

note:: When setting the ROI, Hamamatsu only allows to set multiples of 4 for every setting (X,Y and vsize,
hsize). This is checked in the function. Changing the ROI cannot be done directly, one first needs to disable it
and then re-enable.

Adopted and modified from UUTrack
"""
# External Dependencies
import numpy as np

# Internal Dependencies
# from model.devices.camera.Hamamatsu.API.HamamatsuAPI import HamamatsuCamera as HamamatsuController
from model.devices.camera.Hamamatsu.API.HamamatsuAPI import HamamatsuCameraMR as HamamatsuController
from model.devices.camera.CameraBase import CameraBase


# CameraBase - Test without the base class.
class Camera:
    MODE_CONTINUOUS = 1
    MODE_SINGLE_SHOT = 0
    MODE_EXTERNAL = 2

    def __init__(self, camera_id, model, experiment, verbose=False):
        self.model = model
        self.experiment = experiment
        self.camera_id = camera_id
        self.verbose = verbose
        self.stop_flag = False

        # Initialize Pixel Information
        self.x_pixel_size_in_microns = self.model.CameraParameters['x_pixel_size_in_microns']
        self.y_pixel_size_in_microns = self.model.CameraParameters['y_pixel_size_in_microns']
        self.binning_string = self.model.CameraParameters['binning']
        self.x_binning = int(self.binning_string[0])
        self.y_binning = int(self.binning_string[2])
        self.x_pixels = self.model.CameraParameters['x_pixels']
        self.y_pixels = self.model.CameraParameters['y_pixels']
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)

        # Initialize Exposure and Display Information
        self.camera_line_interval = self.model.CameraParameters['line_interval']
        self.camera_exposure_time = self.model.CameraParameters['exposure_time']
        self.camera_display_live_subsampling = self.model.CameraParameters['display_live_subsampling']
        self.camera_display_acquisition_subsampling = self.model.CameraParameters['display_acquisition_subsampling']

        # Initialize Camera Controller
        self.camera_controller = HamamatsuController(self.camera_id)
        self.camera_controller.setPropertyValue("sensor_mode", self.model.CameraParameters['sensor_mode'])
        self.camera_controller.setPropertyValue("defect_correct_mode",
                                                self.model.CameraParameters['defect_correct_mode'])
        self.camera_controller.setPropertyValue("exposure_time", self.camera_exposure_time/1E6)  # ms -> s or us?
        self.camera_controller.setPropertyValue("binning", self.x_binning)
        self.camera_controller.setPropertyValue("readout_speed", self.model.CameraParameters['readout_speed'])
        self.camera_controller.setPropertyValue("trigger_active", self.model.CameraParameters['trigger_active'])
        self.camera_controller.setPropertyValue("trigger_mode", self.model.CameraParameters['trigger_mode'])
        self.camera_controller.setPropertyValue("trigger_polarity", self.model.CameraParameters['trigger_polarity'])
        self.camera_controller.setPropertyValue("trigger_source", self.model.CameraParameters['trigger_source'])
        self.camera_controller.setPropertyValue("internal_line_interval", self.camera_line_interval)
        self.camera_controller.setPropertyValue("image_height", self.y_pixels)
        self.camera_controller.setPropertyValue("image_width", self.x_pixels)

        if self.verbose:
            print("Hamamatsu Camera Class Initialized")

    def __del__(self):
        self.camera_controller.shutdown()
        if self.verbose:
            print("Hamamatsu Camera Shutdown")

    def stop(self):
        self.stop_flag = True

    def report_camera_settings(self):
        params = ["defect_correct_mode",
                  "sensor_mode",
                  "binning",
                  "readout_speed",
                  "trigger_active",
                  "trigger_mode",
                  "trigger_polarity",
                  "trigger_source",
                  "internal_line_interval",
                  "image_height",
                  "image_width"]
        for param in params:
            print(param, self.camera_controller.getPropertyValue(param))

    def close_camera(self):
        self.camera_controller.shutdown()

    def set_camera_sensor_mode(self, mode):
        if mode == 'Area':
            self.camera_controller.setPropertyValue("sensor_mode", 1)
        elif mode == 'ASLM':
            self.camera_controller.setPropertyValue("sensor_mode", 12)
        else:
            print('Camera mode not supported')

    def set_exposure_time(self, time):
        time = time/1000
        self.camera_controller.setPropertyValue("exposure_time", time)

    def set_line_interval(self, time):
        self.camera_controller.setPropertyValue("internal_line_interval", self.camera_line_interval)

    def set_binning(self, binningstring):
        self.camera_controller.setPropertyValue("binning", binningstring)
        self.x_binning = int(binning_string[0])
        self.y_binning = int(binning_string[2])
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)
        self.experiment.CameraParameters['camera_binning'] = str(self.x_binning) + 'x' + str(self.y_binning)

    def initialize_image_series(self):
        self.camera_controller.startAcquisition()

    def get_images_in_series(self):
        [frames, _] = self.camera_controller.getFrames()
        images = [np.reshape(aframe.getData(), (-1, self.x_pixels)) for aframe in frames]
        return images

    def close_image_series(self):
        self.camera_controller.stopAcquisition()

    def get_image(self):
        [frames, _] = self.camera_controller.getFrames()
        images = [np.reshape(aframe.getData(), (-1, self.x_pixels)) for aframe in frames]
        return images[0]

    def initialize_live_mode(self):
        self.camera_controller.setACQMode(mode="run_till_abort")
        self.camera_controller.startAcquisition()

    def get_live_image(self):
        [frames, _] = self.camera_controller.getFrames()
        images = [np.reshape(aframe.getData(), (-1, self.x_pixels)) for aframe in frames]
        return images

    def close_live_mode(self):
        self.camera_controller.stopAcquisition()

        # self.running = False
        # self.mode = self.MODE_SINGLE_SHOT

