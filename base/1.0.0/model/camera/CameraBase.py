"""
    UUTrack.Model.CameraBase.py
    ==================================
    Camera class with the skeleton functions. Important to keep track of the methods that are
    exposed to the View. The class cameraBase should be subclassed when developing new Models.
    This ensures that all the methods are automatically inherited and there is no breaks downstream.
    .. note:: **IMPORTANT** Whatever new function is implemented in a specific model,
    it should be first declared in the cameraBase class.
    In this way the other models will have access to the method and the
    program will keep running (perhaps with non intended behavior though).
    .. sectionauthor:: Aquiles Carattino <aquiles@aquicarattino.com>
"""

class CameraBase():
    MODE_CONTINUOUS = 1
    MODE_SINGLE_SHOT = 0
    def __init__(self, camera):
        self.camera = camera
        self.running = False
        self.maxWidth = 0
        self.maxHeight = 0
        self.exposure = 0

    def initialize_camera(self):
        """
        Initializes the camera.
        """
        self.maxWidth = self.get_CCD_width()
        self.maxHeight = self.get_CCD_height()
        return True

    def trigger_camera(self):
        """
        Triggers the camera.
        """
        print("Not Implemented")

    def set_acquisition_mode(self, mode):
        """
        Set the readout mode of the camera: Single or continuous.
        :param int mode: One of self.MODE_CONTINUOUS, self.MODE_SINGLE_SHOT
        :return:
        """
        self.mode = mode

    def get_acquisition_mode(self):
        """
        Returns the acquisition mode, either continuous or single shot.
        """
        return self.mode

    def acquisition_ready(self):
        """
        Checks if the acquisition in the camera is over.
        """
        print("Not Implemented")

    def set_exposure(self,exposure):
        """
        Sets the exposure of the camera.
        """
        self.exposure = exposure
        print("Not Implemented")

    def get_exposure(self):
        """
        Gets the exposure time of the camera.
        """
        print("Not Implemented")
        return self.exposure

    def read_camera(self):
        """
        Reads the camera
        """
        print("Not Implemented")

    def set_ROI(self,X,Y):
        """ Sets up the ROI. Not all cameras are 0-indexed, so this is an important
        place to define the proper ROI.
        :param array X: array type with the coordinates for the ROI X[0], X[1]
        :param array Y: array type with the coordinates for the ROI Y[0], Y[1]
        :return:
        """
        print("Not Implemented")

    def clear_ROI(self):
        """
        Clears the ROI from the camera.
        """
        self.set_ROI(self.maxWidth, self.maxHeight)

    def get_size(self):
        """Returns the size in pixels of the image being acquired. This is useful for checking the ROI settings.
        """
        print("Not Implemented")

    def get_serial_number(self):
        """Returns the serial number of the camera.
        """
        print("Not Implemented")

    def get_CCD_width(self):
        """
        Returns the CCD width in pixels
        """
        print("Not Implemented")

    def get_CCD_height(self):
        """
        Returns: the CCD height in pixels
        """
        print("Not Implemented")

    def stop_acq(self):
        """Stops the acquisition without closing the connection to the camera."""
        print("Not Implemented")

    def set_binning(self,xbin,ybin):
        """
        Sets the binning of the camera if supported. Has to check if binning in X/Y can be different or not, etc.
        :param xbin:
        :param ybin:
        :return:
        """
        print("Not Implemented")

    def stop_camera(self):
        """Stops the acquisition and closes the connection with the camera.
        """
        try:
            #Closing the camera
            print("Not Implemented")
        except:
            #Monitor failed to close
            print("Not Implemented")