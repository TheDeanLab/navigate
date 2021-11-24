"""
    UUTrack.Model.Cameras.SyntheticCamera.py
    ====================================
    Dummy camera class for testing GUI and other functionalities. Based on the skeleton.

    .. sectionauthor: Aquiles Carattino <aquiles@aquicarattino.com>
"""

import time
import numpy as np
from .CameraBase import CameraBase

class Camera(CameraBase):
    MODE_CONTINUOUS = 1
    MODE_SINGLE_SHOT = 0
    def __init__(self, camera):
        self.camera = camera
        self.running = False
        self.xsize = 600
        self.ysize = 250
        self.maxX = 600
        self.maxY = 250
        self.exposure = 0

    def initialize_camera(self):
        """Initializes the camera.
        """
        print('Initializing camera')
        self.maxWidth = self.get_ccd_width()
        self.maxHeight = self.get_ccd_height()
        return True

    def trigger_camera(self):
        """Triggers the camera.
        """
        return True

    def set_acquisition_mode(self, mode):
        """
        Set the readout mode of the camera: Single or continuous.

        :param: int mode: One of self.MODE_CONTINUOUS, self.MODE_SINGLE_SHOT
        """
        print('Setting acquisition mode')
        return self.get_acquisition_mode()

    def get_acquisition_mode(self):
        """Returns the acquisition mode, either continuous or single shot.
        """
        return self.MODE_CONTINUOUS

    def acquisition_ready(self):
        """Checks if the acquisition in the camera is over.
        """
        return True

    def set_exposure(self, exposure):
        """Sets the exposure of the camera.
        """
        self.exposure = exposure
        return exposure

    def get_exposure(self):
        """Gets the exposure time of the camera.
        """
        return self.exposure

    def read_camera(self):
        X,Y = self.get_size()
        moment = time.time()
        sample = np.random.normal(size=(self.xsize, self.ysize))*100
        sample = np.around(data).astype('uint16')
        elapsed = time.time() - moment
        try:
            # to simulate exposure time corrected for data generation delay
            time.sleep(self.exposure.magnitude/1000-elapsed)
        except:
            time.sleep(0)
        return sample

    def set_ROI(self,X,Y):
        """
        Sets up the ROI. Not all cameras are 0-indexed, so this is an important
        place to define the proper ROI.

        :param X: array type with the coordinates for the ROI X[0], X[1]
        :param Y: array type with the coordinates for the ROI Y[0], Y[1]
        :return:
        """
        self.xsize = abs(X[1]-X[0])
        self.ysize = abs(Y[1]-Y[0])
        self.sb.resizeView((self.xsize, self.ysize))
        return self.get_size()

    def get_size(self):
        """
        :return: Returns the size in pixels of the image being acquired. This is useful for checking the ROI settings.
        """

        return self.xsize, self.ysize

    def get_serial_number(self):
        """Returns the serial number of the camera.
        """
        return "Serial Number"

    def get_ccd_width(self):
        """
        :return: The CCD width in pixels
        """
        return self.maxX


    def get_ccd_height(self):
        """
        :return: The CCD height in pixels
        """
        return self.maxY

    def set_binning(self, xbin, ybin):
        """Sets the binning of the camera if supported. Has to check if binning in X/Y can be different or not, etc.

        :param: xbin: binning in x
        :param: ybin: binning in y
        """
        self.xbin = xbin
        self.ybin = ybin
        pass

    def stop_acq(self):
        """ Stops the acquisition

        :return: bool True: returns true
        """
        return True

    def stop_camera(self):
        """Stops the acquisition and closes the connection with the camera.
        """
        try:
            #Closing the camera
            return True
        except:
            #Monitor failed to close
            return False