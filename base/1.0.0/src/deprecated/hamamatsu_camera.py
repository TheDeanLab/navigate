from hamamatsu.dcam import Dcam as Dcam



# TODO: Import CameraParameter and set proper parameters below...  Hardcoded now.
# from ..constants import CameraParameters and camera_configuration
import numpy as np
import cv2


class HamamatsuCamera(Dcam):
    def __init__(self, camera_id=0):
        #Need to add getter methods to dcam to access methods or just use Dcam separately
        super().__init__(camera_id)
        #self.camera_id = camera_id
        #print("Initializing CameraID:", self.camera_id)

    def open_camera(self):
        if Dcamapi.init() is not False:
            if self.hcam.dev_open() is not False:
                self.hcam.prop_setvalue('SENSORMODE', 1)
                self.hcam.prop_setvalue('DEFECTCORRECT_MODE', 2)
                self.hcam.prop_setvalue('EXPOSURE TIME', 0.01)
                self.hcam.prop_setvalue('BINNING', 1)
                self.hcam.prop_setvalue('READOUTSPEED', 1)
                self.hcam.prop_setvalue('TRIGGERACTIVE', 1)
                self.hcam.prop_setvalue('TRIGGERMODE', 1)
                self.hcam.prop_setvalue('TRIGGERPOLARITY', 2)
                self.hcam.prop_setvalue('TRIGGERSOURCE', 2)
                self.hcam.prop_setvalue('INTERNAL LINE INTERVAL', 0.000075)
            else:
                print('-NG: hcam.dev_open() fails with error {}'.format(hcam.lasterr()))
        else:
            print('-NG: Dcamapi.init() fails with error {}'.format(Dcamapi.lasterr()))

    def open_camera_v2(self):
        hcam = Dcam(self.camera_id)
        self.hcam.dev_open()
        self.hcam.prop_setvalue('SENSOR MODE', 12)
        self.hcam.prop_setvalue('DEFECTCORRECT_MODE', 2)
        self.hcam.prop_setvalue('EXPOSURE TIME', 0.01)
        self.hcam.prop_setvalue('BINNING', 1)
        self.hcam.prop_setvalue('READOUTSPEED', 1)
        self.hcam.prop_setvalue('TRIGGERACTIVE', 1)
        self.hcam.prop_setvalue('TRIGGERMODE', 1)
        self.hcam.prop_setvalue('TRIGGERPOLARITY', 2)
        self.hcam.prop_setvalue('TRIGGERSOURCE', 2)
        self.hcam.prop_setvalue('INTERNAL LINE INTERVAL', 0.000075)
        # else:
        # print('-NG: hcam.dev_open() fails with error {}'.format(hcam.lasterr()))
        # else:
        # print('-NG: Dcamapi.init() fails with error {}'.format(Dcamapi.lasterr()))

    def close_camera(self):
        self.hcam.dev_close()
        # Dcamapi.uninit()

    def set_camera_sensor_mode(self, mode):
        if mode == 'Area':
            self.prop_setvalue('SENSORMODE', 1)
            print("Camera Mode:", mode)
        elif mode == 'ASLM':
            self.prop_setvalue('SENSORMODE', 12)
        else:
            print('Camera mode not supported')

    def get_camera_sensor_mode(self):
        # TODO: Not working.
        return str(self.prop_getvalue(DCAM_IDPROP.SENSORMODE))


    def set_exposure_time(self, time):
        print("Setting Exposure Time:", time)
        self.hcam.prop_setvalue('EXPOSURE TIME', time)

    def get_exposure_time(self):
        # TODO: Not working.
        exposure_time = self.hcam.prop_getvalue('EXPOSURE TIME')
        print("Exposure Time:", exposure_time)
        return exposure_time

    def set_line_interval(self, time=0.000075):
        print("Setting the Internal Line Interval:", time)
        self.hcam.prop_setvalue('INTERNAL LINE INTERVAL', 0.000075)

    def get_line_interval(self):
        line_interval = self.hcam.prop_getvalue('INTERNAL LINE INTERVAL')
        print("Internal Line Interval:", line_interval)
        return line_interval

    def set_binning(self, binning=1):
        self.hcam.prop_setvalue('BINNING', binning)
        self.binning = int(self.binning)
        self.x_pixels = int(self.x_pixels / self.binning)
        self.y_pixels = int(self.y_pixels / self.binning)

    def show_camera_properties(self):
        """ Show supported camera properties  """
        idprop = self.hcam.prop_getnextid(0)
        while idprop is not False:
            output = '0x{:08X}: '.format(idprop)
            propname = dcam.prop_getname(idprop)
            propval = dcam.prop_getvalue(idprop)
            if propname is not False:
                output = output + propname + ' = ' + str(propval)
            print(output)
            idprop = dcam.prop_getnextid(idprop)

    '''
    def initialize_image_series(self):
        self.hcam.startAcquisition()

    def get_images_in_series(self):
        [frames, _] = self.hcam.getFrames()
        images = [np.reshape(aframe.getData(), (-1, self.x_pixels)) for aframe in frames]
        return images

    def close_image_series(self):
        self.hcam.stopAcquisition()

    def get_image(self):
        [frames, _] = self.hcam.getFrames()
        images = [np.reshape(aframe.getData(), (-1, self.x_pixels)) for aframe in frames]
        print("The dimensions of the image are: ", np.shape(images))
        return images
        # return images[0]
        # TODO this is causing errors, index is out of bounds

    def initialize_live_mode(self):
        self.hcam.setACQMode(mode="run_till_abort")
        self.hcam.startAcquisition()

    def get_live_image(self):
        [frames, _] = self.hcam.getFrames()
        images = [np.reshape(aframe.getData(), (-1, self.x_pixels)) for aframe in frames]
        return images

    def close_live_mode(self):
     self.hcam.stopAcquisition()
    '''


if __name__ == '__main__':
    def dcam_show_device_list():
        """  Show device list  """

        if Dcamapi.init() is not False:
            n = Dcamapi.get_devicecount()
            for i in range(0, n):
                dcam = Dcam(i)
                output = '#{}: '.format(i)

                model = dcam.dev_getstring(DCAM_IDSTR.MODEL)
                if model is False:
                    output = output + 'No DCAM_IDSTR.MODEL'
                else:
                    output = output + 'MODEL={}'.format(model)

                cameraid = dcam.dev_getstring(DCAM_IDSTR.CAMERAID)
                if cameraid is False:
                    output = output + ', No DCAM_IDSTR.CAMERAID'
                else:
                    output = output + ', CAMERAID={}'.format(cameraid)

                print(output)
        else:
            print('-NG: Dcamapi.init() fails with error {}'.format(Dcamapi.lasterr()))

        Dcamapi.uninit()


    def dcam_show_properties(iDevice=0):
        """
        Show supported properties
        """
        if Dcamapi.init() is not False:
            dcam = Dcam(iDevice)
            if dcam.dev_open() is not False:
                idprop = dcam.prop_getnextid(0)
                while idprop is not False:
                    output = '0x{:08X}: '.format(idprop)
                    propname = dcam.prop_getname(idprop)
                    propval = dcam.prop_getvalue(idprop)

                    if propname is not False:
                        output = output + propname + ' ' + str(propval)

                    print(output)
                    idprop = dcam.prop_getnextid(idprop)

                dcam.dev_close()
            else:
                print('-NG: Dcam.dev_open() fails with error {}'.format(dcam.lasterr()))
        else:
            print('-NG: Dcamapi.init() fails with error {}'.format(Dcamapi.lasterr()))

        Dcamapi.uninit()


    # dcam_show_device_list()

    camera = HamamatsuCamera()
    propid = camera.prop_getnextid(0)
    camera.prop_getname(propid)
    # camera.hcam.open()
    # camera.set_camera_sensor_mode('Area')


    # camera.show_camera_properties()
    # camera.set_exposure_time(0.02)
    # camera.get_exposure_time()
    # camera.set_line_interval()
    # camera.close_camera()
    # dcam_show_properties(0)

# HamamatsuCamera.dcam_show_device_list()
# HamamatsuCamera.dcam_show_properties()
