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

#
#     def initialize_camera(self):
#         """
#         Initializes the camera.
#         This is important to not have shuffled patches of the CCD.
#         :return:
#         """
#         self.camera_controller.initCamera()
#         self.max_width = self.get_ccd_width()
#         self.max_height = self.get_ccd_height()
#         self.camera_controller.setPropertyValue("readout_speed", 1)
#         self.camera_controller.setPropertyValue("defect_correct_mode", 1)
#         if self.verbose:
#             print("Camera Initialized")
#
#     def trigger_camera(self):
#         """
#         Triggers the camera.
#         """
#         if self.get_acquisition_mode() == self.MODE_CONTINUOUS:
#             self.camera_controller.startAcquisition()
#         elif self.get_acquisition_mode() == self.MODE_SINGLE_SHOT:
#             self.camera_controller.startAcquisition()
#             self.camera_controller.stopAcquisition()
#         if self.verbose:
#             print("Camera Triggered")
#
#     def set_acquisition_mode(self, mode):
#         """
#         Set the readout mode of the camera: Single or continuous.
#         Parameters
#         mode : int
#         One of self.MODE_CONTINUOUS, self.MODE_SINGLE_SHOT
#         """
#         self.mode = mode
#         if mode == self.MODE_CONTINUOUS:
#             #self.camera_controller.setPropertyValue("trigger_source", 1)
#             self.camera_controller.settrigger(1)
#             self.camera_controller.setmode(self.camera_controller.CAPTUREMODE_SEQUENCE)
#         elif mode == self.MODE_SINGLE_SHOT:
#             #self.camera_controller.setPropertyValue("trigger_source", 3)
#             self.camera_controller.settrigger(1)
#             self.camera_controller.setmode(self.camera_controller.CAPTUREMODE_SNAP)
#         elif mode == self.MODE_EXTERNAL:
#             #self.camera_controller.setPropertyValue("trigger_source", 2)
#             self.camera_controller.settrigger(2)
#         if self.verbose:
#             print("Camera Acquisition Mode Set:", mode)
#         return self.getAcquisitionMode()
#
#     def get_acquisition_mode(self):
#         """
#         Returns the acquisition mode, either continuous or single shot.
#         """
#         if self.verbose:
#             print("Camera Acquisition Mode:", self.mode)
#         return self.mode
#
#     def acquisition_ready(self):
#         """
#         Checks if the acquisition in the camera is over.
#         """
#         if self.verbose:
#             print("Camera Acquisition Ready")
#         return True
#
#     def set_exposure(self, exposure):
#         """
#         Sets the exposure of the camera.
#         """
#         self.camera_controller.setPropertyValue("exposure_time", exposure/1000)
#         if self.verbose:
#             print("Camera Exposure Set:", exposure)
#         return self.get_exposure()
#
#     def get_exposure(self):
#         """
#         Gets the exposure time of the camera.
#         """
#         exposure = self.camera_controller.getPropertyValue("exposure_time")[0]*1000
#         if self.verbose:
#             print("Camera Exposure:", exposure)
#         return exposure
#
#     def read_camera(self):
#         """
#         Reads the camera
#         """
#         [frames, dims] = self.camera_controller.getFrames()
#         img = []
#         for f in frames:
#             d = f.getData()
#             d = np.reshape(d, (dims[1], dims[0]))
#             d = d.T
#             img.append(d)
# #        img = frames[-1].getData()
# #        img = np.reshape(img,(dims[0],dims[1]))
#         if self.verbose:
#             print("Camera Read")
#         return img
#
#     def set_ROI(self, X ,Y):
#         """
#         Sets up the ROI. Not all cameras are 0-indexed, so this is an important
#         place to define the proper ROI.
#         X -- array type with the coordinates for the ROI X[0], X[1]
#         Y -- array type with the coordinates for the ROI Y[0], Y[1]
#         """
#         # First needs to go full frame, if not, throws an error of subframe not valid
#         self.camera_controller.setPropertyValue("subarray_vpos", 0)
#         self.camera_controller.setPropertyValue("subarray_hpos", 0)
#         self.camera_controller.setPropertyValue("subarray_vsize", self.camera_controller.max_height)
#         self.camera_controller.setPropertyValue("subarray_hsize", self.camera_controller.max_width)
#         self.camera_controller.setSubArrayMode()
#
#         X-=1
#         Y-=1
#         # Because of how Orca Flash 4 works, all the ROI parameters have to be multiple of 4.
#         hsize = int(abs(X[0]-X[1])/4)*4
#         hpos = int(X[0]/4)*4
#         vsize = int(abs(Y[0]-Y[1])/4)*4
#         vpos = int(Y[0]/4)*4
#         self.camera_controller.setPropertyValue("subarray_vpos", vpos)
#         self.camera_controller.setPropertyValue("subarray_hpos", hpos)
#         self.camera_controller.setPropertyValue("subarray_vsize", vsize)
#         self.camera_controller.setPropertyValue("subarray_hsize", hsize)
#         self.camera_controller.setSubArrayMode()
#         if self.verbose:
#             print("Camera ROI Set.")
#         return self.getSize()
#
#     def get_size(self):
#         """
#         Returns the size in pixels of the image being acquired.
#         This is useful for checking the ROI settings.
#         """
#         X = self.camera_controller.getPropertyValue("subarray_hsize")
#         Y = self.camera_controller.getPropertyValue("subarray_vsize")
#         return X[0], Y[0]
#
#     def get_serial_number(self):
#         """Returns the serial number of the camera.
#         """
#         serial_number = self.camera_controller.getModelInfo(self.camera_id)
#         if self.verbose:
#             print("Camera Serial Number:", serial_number)
#         return
#
#     def get_ccd_width(self):
#         """
#         The CCD width in pixels
#         """
#         ccd_width = self.camera_controller.max_width
#         if self.verbose:
#             print("Camera CCD Width:", ccd_width)
#         return ccd_width
#
#     def get_ccd_height(self):
#         """
#         The CCD height in pixels
#         """
#         ccd_height = self.camera_controller.max_height
#         if self.verbose:
#             print("Camera CCD Height:", ccd_height)
#         return ccd_height
#
#     def stop_acq(self):
#         if self.verbose:
#             print("Camera Acquisition Stopped.")
#         self.camera_controller.stopAcquisition()
#
#     def stop_camera(self):
#         """
#         Stops the acquisition and closes the connection with the camera.
#         """
#         try:
#             #Closing the camera
#             self.camera_controller.stopAcquisition()
#             self.camera_controller.shutdown()
#             if self.verbose:
#                 print("Camera Stopped.")
#             return True
#         except:
#             #Monitor failed to close
#             return False
