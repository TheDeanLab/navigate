
# External Dependencies
import numpy as np

# Internal Dependencies
from model.devices.camera.Hamamatsu.API.HamamatsuAPI import DCAM as HamamatsuController
from model.devices.camera.CameraBase import CameraBase


# CameraBase - Test without the base class.
class Camera(CameraBase):
    def __init__(self, camera_id, model, experiment, verbose=False):
        super().__init__(camera_id, model, experiment, verbose)

        # Initialize Camera Controller
        self.camera_controller = HamamatsuController(camera_id)
        self.camera_controller.set_property_value("sensor_mode", self.model.CameraParameters['sensor_mode'])
        self.camera_controller.set_property_value("defect_correct_mode",
                                                self.model.CameraParameters['defect_correct_mode'])
        self.camera_controller.set_property_value("exposure_time", self.camera_exposure_time)
        self.camera_controller.set_property_value("binning", self.x_binning)
        self.camera_controller.set_property_value("readout_speed", self.model.CameraParameters['readout_speed'])
        self.camera_controller.set_property_value("trigger_active", self.model.CameraParameters['trigger_active'])
        self.camera_controller.set_property_value("trigger_mode", self.model.CameraParameters['trigger_mode'])
        self.camera_controller.set_property_value("trigger_polarity", self.model.CameraParameters['trigger_polarity'])
        self.camera_controller.set_property_value("trigger_source", self.model.CameraParameters['trigger_source'])
        self.camera_controller.set_property_value("internal_line_interval", self.camera_line_interval)
        self.camera_controller.set_property_value("image_height", self.y_pixels)
        self.camera_controller.set_property_value("image_width", self.x_pixels)

        if self.verbose:
            print("Hamamatsu Camera Class Initialized")

    def __del__(self):
        self.camera_controller.dev_close()
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
            self.camera_controller.set_property_value("sensor_mode", 1)
        elif mode == 'ASLM':
            self.camera_controller.set_property_value("sensor_mode", 12)
        else:
            print('Camera mode not supported')

    def set_exposure_time(self, time):
        """
        #  Units of the Hamamatsu API are in seconds.
        #  All of our units are in milliseconds.
        """
        self.camera_controller.set_property_value("exposure_time", time)

    def set_line_interval(self, time):
        self.camera_controller.set_property_value("internal_line_interval", self.camera_line_interval)

    def set_binning(self, binning_string):
        self.camera_controller.set_property_value("binning", binningstring)
        self.x_binning = int(binning_string[0])
        self.y_binning = int(binning_string[2])
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)
        self.experiment.CameraParameters['camera_binning'] = str(self.x_binning) + 'x' + str(self.y_binning)

    def initialize_image_series(self, data_buffer=None, number_of_frames=100):
        self.camera_controller.start_acquisition(data_buffer, number_of_frames)

    def close_image_series(self):
        self.camera_controller.stop_acquisition()

    def initialize_live_mode(self):
        # self.camera_controller.setACQMode(mode="run_till_abort")
        self.camera_controller.start_acquisition()

    def close_live_mode(self):
        self.camera_controller.stop_acquisition()

        # self.running = False
        # self.mode = self.MODE_SINGLE_SHOT

    def get_new_frame(self):
        return self.camera_controller.get_frames()