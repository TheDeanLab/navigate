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
from model.camera.Hamamatsu.API.HamamatsuAPI import HamamatsuCamera as HamamatsuController
from model.camera.CameraBase import CameraBase


class Camera(CameraBase):
    MODE_CONTINUOUS = 1
    MODE_SINGLE_SHOT = 0
    MODE_EXTERNAL = 2

    def __init__(self, camera_id, session, verbose):
        # Monitor ID
        self.cam_id = camera_id
        self.camera_controller = HamamatsuController(camera_id)
        self.running = False
        self.mode = self.MODE_SINGLE_SHOT
        if verbose:
            print("Camera initialized")

    def initialize_camera(self):
        """
        Initializes the camera.
        :return:
        """

        self.camera_controller.initCamera()
        self.max_width = self.get_ccd_width()
        self.max_height = self.get_ccd_height()
        #This is important to not have shufled patches of the CCD.
        #Have to check documentation!!
        self.camera_controller.setPropertyValue("readout_speed", 1)
        self.camera_controller.setPropertyValue("defect_correct_mode", 1)

    def trigger_camera(self):
        """
        Triggers the camera.
        """
        if self.get_acquisition_mode() == self.MODE_CONTINUOUS:
            self.camera_controller.startAcquisition()
        elif self.get_acquisition_mode() == self.MODE_SINGLE_SHOT:
            self.camera_controller.startAcquisition()
            self.camera_controller.stopAcquisition()

    def set_acquisition_mode(self, mode):
        """
        Set the readout mode of the camera: Single or continuous.
        Parameters
        mode : int
        One of self.MODE_CONTINUOUS, self.MODE_SINGLE_SHOT
        """
        self.mode = mode
        if mode == self.MODE_CONTINUOUS:
            #self.camera_controller.setPropertyValue("trigger_source", 1)
            self.camera_controller.settrigger(1)
            self.camera_controller.setmode(self.camera_controller.CAPTUREMODE_SEQUENCE)
        elif mode == self.MODE_SINGLE_SHOT:
            #self.camera_controller.setPropertyValue("trigger_source", 3)
            self.camera_controller.settrigger(1)
            self.camera_controller.setmode(self.camera_controller.CAPTUREMODE_SNAP)
        elif mode == self.MODE_EXTERNAL:
            #self.camera_controller.setPropertyValue("trigger_source", 2)
            self.camera_controller.settrigger(2)
        return self.getAcquisitionMode()

    def get_acquisition_mode(self):
        """
        Returns the acquisition mode, either continuous or single shot.
        """
        return self.mode

    def acquisition_ready(self):
        """
        Checks if the acquisition in the camera is over.
        """
        return True

    def set_exposure(self, exposure):
        """
        Sets the exposure of the camera.
        """
        self.camera_controller.setPropertyValue("exposure_time", exposure/1000)
        return self.get_exposure()

    def get_exposure(self):
        """
        Gets the exposure time of the camera.
        """
        return self.camera_controller.getPropertyValue("exposure_time")[0]*1000

    def read_camera(self):
        """
        Reads the camera
        """
        [frames, dims] = self.camera_controller.getFrames()
        img = []
        for f in frames:
            d = f.getData()
            d = np.reshape(d, (dims[1], dims[0]))
            d = d.T
            img.append(d)
#        img = frames[-1].getData()
#        img = np.reshape(img,(dims[0],dims[1]))
        return img

    def set_ROI(self, X ,Y):
        """
        Sets up the ROI. Not all cameras are 0-indexed, so this is an important
        place to define the proper ROI.
        X -- array type with the coordinates for the ROI X[0], X[1]
        Y -- array type with the coordinates for the ROI Y[0], Y[1]
        """
        # First needs to go full frame, if not, throws an error of subframe not valid
        self.camera_controller.setPropertyValue("subarray_vpos", 0)
        self.camera_controller.setPropertyValue("subarray_hpos", 0)
        self.camera_controller.setPropertyValue("subarray_vsize", self.camera_controller.max_height)
        self.camera_controller.setPropertyValue("subarray_hsize", self.camera_controller.max_width)
        self.camera_controller.setSubArrayMode()

        X-=1
        Y-=1
        # Because of how Orca Flash 4 works, all the ROI parameters have to be multiple of 4.
        hsize = int(abs(X[0]-X[1])/4)*4
        hpos = int(X[0]/4)*4
        vsize = int(abs(Y[0]-Y[1])/4)*4
        vpos = int(Y[0]/4)*4
        self.camera_controller.setPropertyValue("subarray_vpos", vpos)
        self.camera_controller.setPropertyValue("subarray_hpos", hpos)
        self.camera_controller.setPropertyValue("subarray_vsize", vsize)
        self.camera_controller.setPropertyValue("subarray_hsize", hsize)
        self.camera_controller.setSubArrayMode()
        return self.getSize()

    def get_size(self):
        """Returns the size in pixels of the image being acquired. This is useful for checking the ROI settings.
        """
        X = self.camera_controller.getPropertyValue("subarray_hsize")
        Y = self.camera_controller.getPropertyValue("subarray_vsize")
        return X[0], Y[0]

    def get_serial_number(self):
        """Returns the serial number of the camera.
        """
        return self.camera_controller.getModelInfo(self.cam_id)

    def get_ccd_width(self):
        """
        Returns
        The CCD width in pixels

        """
        return self.camera_controller.max_width

    def get_ccd_height(self):
        """
        Returns
        The CCD height in pixels

        """
        return self.camera_controller.max_height

    def stop_acq(self):
        self.camera_controller.stopAcquisition()

    def stop_camera(self):
        """Stops the acquisition and closes the connection with the camera.
        """
        try:
            #Closing the camera
            self.camera_controller.stopAcquisition()
            self.camera_controller.shutdown()
            return True
        except:
            #Monitor failed to close
            return False