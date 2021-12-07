# dcam.py : Jun 30, 2021
#
# Copyright (C) 2021 Hamamatsu Photonics K.K.. All right reserved.
#
# The declarations of classes and functions in this file are subject to change without notice.

from .dcamapi4 import *
import numpy as np
import cv2 

# ==== DCAMAPI helper functions ====

def dcammisc_setupframe(hdcam, bufframe: DCAMBUF_FRAME):
    """
    Setup DCAMBUF_FRAME instance based on camera setting with hdcam

    """
    fValue = c_double()
    idprop = DCAM_IDPROP.IMAGE_PIXELTYPE
    err = dcamprop_getvalue(hdcam, idprop, byref(fValue))
    if not err.is_failed():
        bufframe.type = int(fValue.value)

        idprop = DCAM_IDPROP.IMAGE_WIDTH
        err = dcamprop_getvalue(hdcam, idprop, byref(fValue))
        if not err.is_failed():
            bufframe.width = int(fValue.value)

            idprop = DCAM_IDPROP.IMAGE_HEIGHT
            err = dcamprop_getvalue(hdcam, idprop, byref(fValue))
            if not err.is_failed():
                bufframe.height = int(fValue.value)

                idprop = DCAM_IDPROP.IMAGE_ROWBYTES
                err = dcamprop_getvalue(hdcam, idprop, byref(fValue))
                if not err.is_failed():
                    bufframe.rowbytes = int(fValue.value)

    return err


def dcammisc_alloc_ndarray(frame: DCAMBUF_FRAME):
    """
    Allocate NumPy ndarray based on information of DCAMBUF_FRAME.

    """

    if frame.type == DCAM_PIXELTYPE.MONO16:
        return np.zeros((frame.height, frame.width), dtype='uint16')

    if frame.type == DCAM_PIXELTYPE.MONO8:
        return np.zeros((frame.height, frame.width), dtype='uint8')

    return False


# ==== declare Dcamapi class ====


class Dcamapi:
    # class instance
    __lasterr = DCAMERR.SUCCESS  # the last error from functions with dcamapi_ prefix.
    __bInitialized = False  # Once Dcamapi.init() is called, then True.  Dcamapi.uninit() reset this.
    __devicecount = 0

    @classmethod
    def __result(cls, errvalue):
        """
        Internal use. Keep last error code
        """
        if errvalue < 0:
            cls.__lasterr = errvalue
            return False

        return True

    @classmethod
    def lasterr(cls):
        """
        Return last error code of Dcamapi member functions
        """
        return cls.__lasterr

    @classmethod
    def init(cls, *initparams):
        """
        Initialize dcamapi.
        Do not call this when Dcam object exists because constructor of Dcam ececute this.
        After calling close(), call this again if you need to resume measurement.

        Returns:
            True:   if dcamapi_init() succeeded.
            False:  if dcamapi_init() returned DCAMERR except SUCCESS.  lasterr() returns the DCAMERR value.
        """
        if cls.__bInitialized:
            return cls.__result(DCAMERR.ALREADYINITIALIZED)  # dcamapi_init() is called. New Error.

        paraminit = DCAMAPI_INIT()
        err = dcamapi_init(byref(paraminit))
        cls.__bInitialized = True
        if cls.__result(err) is False:
            return False

        cls.__devicecount = paraminit.iDeviceCount
        return True

    @classmethod
    def uninit(cls):
        """
        Uninitlaize dcamapi.
        After using DCAM-API, call this function to close all resources.

        Returns:
            True:
        """
        if cls.__bInitialized:
            dcamapi_uninit()
            cls.__lasterr = DCAMERR.SUCCESS
            cls.__bInitialized = False
            cls.__devicecount = 0

        return True

    @classmethod
    def get_devicecount(cls):
        """
        Return number of connected cameras.

        Returns:
            nDeviceCount
            False:  if not initialized.
        """
        if not cls.__bInitialized:
            return False

        return cls.__devicecount

# ==== Dcam class ====


class Dcam:
    def __init__(self, iDevice=0):
        self.__lasterr = DCAMERR.SUCCESS
        self.__iDevice = iDevice
        self.__hdcam = 0
        self.__hdcamwait = 0
        self.__bufframe = DCAMBUF_FRAME()
        self.verbose = False

    def __repr__(self):
        return 'Dcam()'

    def __result(self, errvalue):
        """
        Internal use. Keep last error code
        """
        if errvalue < 0:
            self.__lasterr = errvalue
            return False

        return True

    def lasterr(self):
        """
        Return last error code.
        """
        return self.__lasterr

    def is_opened(self):
        """
        Check DCAM handle is opened.

        Returns:
            True:   DCAM handle is opened
            False:  DCAM handle is not opened
        """
        if self.__hdcam == 0:
            return False
        else:
            return True

    def dev_open(self, index=-1):
        """
        Get HDCAM handle for controling camera.
        After calling close(), call this again if you need to resume measurement.

        Args:
            arg1(int): device index

        Returns:
            True:   if dcamdev_open() succeeded.
            False:  if dcamdev_open() returned DCAMERR except SUCCESS.  lasterr() returns the DCAMERR value.
        """
        if self.is_opened():
            return self.__result(DCAMERR.ALREADYOPENED)  # instance is already opened. New Error.

        paramopen = DCAMDEV_OPEN()
        if index >= 0:
            paramopen.index = index
        else:
            paramopen.index = self.__iDevice

        ret = self.__result(dcamdev_open(byref(paramopen)))
        if ret is False:
            return False

        self.__hdcam = paramopen.hdcam
        return True

    def dev_close(self):
        """
        Close dcam handle.
        Call this if you need to close the current device.

        Returns:
            True:
        """
        if self.is_opened():
            self.__close_hdcamwait()
            dcamdev_close(self.__hdcam)
            self.__lasterr = DCAMERR.SUCCESS
            self.__hdcam = 0

        return True

    def dev_getstring(self, idstr):
        """
        Get string of device

        Args:
            arg1(DCAM_IDSTR): string id

        Returns:
            String
            False:  error happened.  lasterr() returns the DCAMERR value
        """
        if self.is_opened():
            hdcam = self.__hdcam
        else:
            hdcam = self.__iDevice

        paramdevstr = DCAMDEV_STRING()
        paramdevstr.iString = idstr
        paramdevstr.alloctext(256)

        ret = self.__result(dcamdev_getstring(hdcam, byref(paramdevstr)))
        if ret is False:
            return False

        return paramdevstr.text.decode()

    # dcamprop functions

    def prop_getattr(self, idprop):
        """
        Get property attribute

        args:
            arg1(DCAM_IDPROP): property id

        Returns:
            DCAMPROP_ATTR
            if False, error happened.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        propattr = DCAMPROP_ATTR()
        propattr.iProp = idprop
        ret = self.__result(dcamprop_getattr(self.__hdcam, byref(propattr)))
        if ret is False:
            return False

        return propattr

    def prop_getvalue(self, idprop):
        """
        Get property value

        args:
            arg1(DCAM_IDPROP): property id

        Returns:
            double
            if False, error happened.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        cDouble = c_double()
        ret = self.__result(dcamprop_getvalue(self.__hdcam, idprop, byref(cDouble)))
        if ret is False:
            return False

        return cDouble.value

    def prop_setvalue(self, idprop, fValue):
        """
        Set property value

        args:
            arg1(DCAM_IDPROP): property id
            arg2(double): setting value

        Returns:
            True   success
            False  error happened.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        ret = self.__result(dcamprop_setvalue(self.__hdcam, idprop, fValue))
        if ret is False:
            return False

        return True

    def prop_setgetvalue(self, idprop, fValue, option=0):
        """
        Set and get property value

        args:
            arg1(DCAM_IDPROP): property id
            arg2(double): input value for setting and receive actual set value by ref

        Returns:
            double
            if False, error happened.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        cDouble = c_double(fValue)
        cOption = c_int32(option)
        ret = self.__result(dcamprop_setgetvalue(self.__hdcam, idprop, byref(cDouble), cOption))
        if ret is False:
            return False

        return cDouble.value

    def prop_queryvalue(self, idprop, fValue, option=0):
        """
        Query property value

        Args:
            arg1(DCAM_IDPROP): property id
            arg2(double): value of property

        Returns:
            double
            if False, error happened.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        cDouble = c_double(fValue)
        cOption = c_int32(option)
        ret = self.__result(dcamprop_queryvalue(self.__hdcam, idprop, byref(cDouble), cOption))
        if ret is False:
            return False

        return cDouble.value

    def prop_getnextid(self, idprop):
        """
        Get next property id

        Args:
            arg1(DCAM_IDPROP): property id

        Returns:
            DCAM_IDPROP
            if False, no more property or error happened.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        cIdprop = c_int32(idprop)
        cOption = c_int32(0)  # search next ID

        ret = self.__result(dcamprop_getnextid(self.__hdcam, byref(cIdprop), cOption))
        if ret is False:
            return False

        return cIdprop.value

    def prop_getname(self, idprop):
        """
        Get name of property

        Args:
            arg1(DCAM_IDPROP): property id

        Returns:
            String
            if False, error happened.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        textbuf = create_string_buffer(256)
        ret = self.__result(dcamprop_getname(self.__hdcam, idprop, textbuf, sizeof(textbuf)))
        if ret is False:
            return False

        return textbuf.value.decode()

    def prop_getvaluetext(self, idprop, fValue):
        """
        Get text of property value

        Args:
            arg1(DCAM_IDSTR): string id
            arg2(double): setting value

        Returns:
            String
            if False, error happened.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        paramvaluetext = DCAMPROP_VALUETEXT()
        paramvaluetext.iProp = idprop
        paramvaluetext.value = fValue
        paramvaluetext.alloctext(256)

        ret = self.__result(dcamprop_getvaluetext(self.__hdcam, byref(paramvaluetext)))
        if ret is False:
            return False

        return paramvaluetext.text.decode()

    # dcambuf functions

    def buf_alloc(self, nFrame):
        """
        Alloc DCAM internal buffer

        Arg:
            arg1(int): Number of frames

        Returns:
            True:   buffer is prepared.
            False:  buffer is not prepared.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        cFrame = c_int32(nFrame)
        ret = self.__result(dcambuf_alloc(self.__hdcam, cFrame))
        if ret is False:
            return False

        return self.__result(dcammisc_setupframe(self.__hdcam, self.__bufframe))

    def buf_release(self):
        """
        Release DCAM internal buffer

        Returns:
            True:   success
            False:  error happens during releasing buffer.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        cOption = c_int32(0)
        return self.__result(dcambuf_release(self.__hdcam, cOption))

    def buf_getframe(self, iFrame):
        """
        Return DCAMBUF_FRAME instance with image data specified by iFrame.

        Arg:
            arg1(int): Index of target frame

        Returns:
            (aFrame, npBuf): aFrame is DCAMBUF_FRAME, npBuf is NumPy buffer
            False:  error happens.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        npBuf = dcammisc_alloc_ndarray(self.__bufframe)
        if npBuf is False:
            return self.__result(DCAMERR.INVALIDPIXELTYPE)

        aFrame = DCAMBUF_FRAME()
        aFrame.iFrame = iFrame

        aFrame.buf = npBuf.ctypes.data_as(c_void_p)
        aFrame.rowbytes = self.__bufframe.rowbytes
        aFrame.type = self.__bufframe.type
        aFrame.width = self.__bufframe.width
        aFrame.height = self.__bufframe.height

        ret = self.__result(dcambuf_copyframe(self.__hdcam, byref(aFrame)))
        if ret is False:
            return False

        return (aFrame, npBuf)

    def buf_getframedata(self, iFrame):
        """
        Return NumPy buffer of image data specified by iFrame.

        Arg:
            arg1(int): Index of target frame

        Returns:
            npBuf:  NumPy buffer
            False:  error happens.  lasterr() returns the DCAMERR value
        """
        ret = self.buf_getframe(iFrame)
        if ret is False:
            return False

        return ret[1]

    def buf_getlastframedata(self):
        """
        Return NumPy buffer of image data of last updated frame

        Returns:
            npBuf:  NumPy buffer
            False:  error happens.  lasterr() returns the DCAMERR value
        """
        return self.buf_getframedata(-1)

    # dcamcap functions

    def cap_start(self, bSequence=True):
        """
        Start capturing

        Arg:
            arg1(Boolean)  False means SNAPSHOT, others means SEQUENCE

        Returns:
            True:   start capture
            False:  error happened.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        if bSequence:
            mode = DCAMCAP_START.SEQUENCE
        else:
            mode = DCAMCAP_START.SNAP

        return self.__result(dcamcap_start(self.__hdcam, mode))

    def cap_snapshot(self):
        """
        Capture snapshot. Get the frames specified in buf_alloc().

        Returns:
            True:   start snapshot
            False:  error happened.  lasterr() returns the DCAMERR value
        """
        return self.cap_start(False)

    def cap_stop(self):
        """
        Stop capturing

        Returns:
            True:   stop capture
            False:  error happened.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        return self.__result(dcamcap_stop(self.__hdcam))

    def cap_status(self):
        """
        Get capture status

        Returns:
            DCAMCAP_STATUS
            if False, error happened.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        cStatus = c_int32()
        ret = self.__result(dcamcap_status(self.__hdcam, byref(cStatus)))
        if ret is False:
            return False

        return cStatus.value

    def cap_transferinfo(self):
        """
        Get transfer info

        Args:
            False

        Returns:
            DCAMCAP_TRANSFERINFO
            if False, error happened.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        paramtransferinfo = DCAMCAP_TRANSFERINFO()
        ret = self.__result(dcamcap_transferinfo(self.__hdcam, byref(paramtransferinfo)))
        if ret is False:
            return False

        return paramtransferinfo

    def cap_firetrigger(self):
        """
        Fire software trigger

        Returns:
            True    Firing trigger was succeeded.
            if False, error happened.  lasterr() returns the DCAMERR value
        """
        if not self.is_opened():
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        cOption = c_int32(0)
        ret = self.__result(dcamcap_firetrigger(self.__hdcam, cOption))
        if ret is False:
            return False

        return True


    # dcamwait functions

    def __open_hdcamwait(self):
        """
        Get HDCAMWAIT handle
        """
        if not self.__hdcamwait == 0:
            return True

        paramwaitopen = DCAMWAIT_OPEN()
        paramwaitopen.hdcam = self.__hdcam
        ret = self.__result(dcamwait_open(byref(paramwaitopen)))
        if ret is False:
            return False

        if paramwaitopen.hwait == 0:
            return self.__result(DCAMERR.INVALIDWAITHANDLE)

        self.__hdcamwait = paramwaitopen.hwait
        return True

    def __close_hdcamwait(self):
        """
        Close HDCAMWAIT handle
        """

        if self.__hdcamwait == 0:
            return True

        ret = self.__result(dcamwait_close(self.__hdcamwait))
        if ret is False:
            return False

        self.__hdcamwait = 0
        return True

    def wait_event(self, eventmask, timeout_millisec):
        """
        Wait event

        Arg:
            arg1(DCAMWAIT_CAPEVENT) Event mask to wait
            arg2(int)   timeout by milliseconds.

        Returns:
            DCAMWAIT_CAPEVENT: happened event
            False:  error happened.  lasterr() returns the DCAMERR value
        """
        ret = self.__open_hdcamwait()
        if ret is False:
            return False

        paramwaitstart = DCAMWAIT_START()
        paramwaitstart.eventmask = eventmask
        paramwaitstart.timeout = timeout_millisec
        ret = self.__result(dcamwait_start(self.__hdcamwait, byref(paramwaitstart)))
        if ret is False:
            return False

        return paramwaitstart.eventhappened

    def wait_capevent_frameready(self, timeout_millisec):
        """
        Wait DCAMWAIT_CAPEVENT.FRAMEREADY event

        Arg:
            arg1(int)   timeout by milliseconds.

        Returns:
            True:   wait capture
            False:  error happened.  lasterr() returns the DCAMERR value
        """
        ret = self.wait_event(DCAMWAIT_CAPEVENT.FRAMEREADY, timeout_millisec)
        if ret is False:
            return False

        # ret is DCAMWAIT_CAPEVENT.FRAMEREADY

        return True

    # custom functions
    def dcam_set_camera_exposure(self, exposure=0.1):
        """
        Change the camera exposure time.
        Arg:
            arg1(float)   exposure time in seconds.
        Returns:
           True:   exposure set
           False:  error happened.
        """
        exposure_idprop = 2031888

        # Get the current exposure duration
        initial_exposure_duration = self.prop_getvalue(exposure_idprop)
        if self.verbose:
            print("Original Exposure Time: {}".format(initial_exposure_duration))

        # Change the exposure duration
        self.prop_setvalue(exposure_idprop, exposure)

        # Confirm the exposure was changed.
        final_exposure_duration = self.prop_getvalue(exposure_idprop)
        if self.verbose:
            print("Current Exposure Time: {}".format(final_exposure_duration))

        if final_exposure_duration == exposure:
            return True
        else:
            print("Camera Exposure Configuration Failed")
            return False

    def dcam_set_camera_sensor_mode(self, sensor_mode=1):
        """
        Change the camera sensor mode.
        Arg:
            arg1(int)   Sensor mode.
            AREA = 1
            LINE = 3
            TDI = 4
            TDI_EXTENDED = 10
            PROGRESSIVE = 12
            SPLITVIEW = 14
            DUAL LIGHTSHEET = 16
            PHOTON NUMBER RESOLVING = 18
        Returns:
           True:   configuration set
           False:  error happened.
        """
        idprop = 4194832

        # Get the current exposure duration
        initial_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Original Sensor Mode: {}".format(initial_configuration))

        # Change the exposure duration
        self.prop_setvalue(idprop, sensor_mode)

        # Confirm the exposure was changed.
        final_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Current Sensor Time: {}".format(final_configuration))

        if final_configuration == sensor_mode:
            return True
        else:
            print("Camera Sensor Mode Configuration Failed")
            return False

    def dcam_set_camera_defect_correction_mode(self, correction_mode=2):
        """
        Change the camera defect correction mode.
        Arg:
            arg1(int)   Defect correction mode.
            OFF = 1
            ON = 2
        Returns:
           True:   configuration set
           False:  error happened.
        """
        idprop = 4653072

        # Get the current exposure duration
        initial_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Original Defect Correction Mode: {}".format(initial_configuration))

        # Change the exposure duration
        self.prop_setvalue(idprop, correction_mode)

        # Confirm the exposure was changed.
        final_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Current Defect Correction Mode: {}".format(final_configuration))

        if final_configuration == correction_mode:
            return True
        else:
            print("Defect Correction Configuration Failed")
            return False

    def dcam_set_camera_binning_mode(self, binning=1):
        """
        Change the camera binning mode.
        Arg:
            arg1(int)   binning mode.
            _1 = 1
            _2 = 2
            _4 = 4
            _8 = 8
            _16 = 16
            _1_2 = 102
            _2_4 = 204
            Returns:
           True:   configuration set
           False:  error happened.
        """

        binning = int(binning)
        idprop = 4198672

        # Get the current binning mode
        initial_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Original Binning Mode: {}".format(initial_configuration))

        # Change the binning mode
        self.prop_setvalue(idprop, binning)

        # Confirm the binning mode was changed.
        final_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Current Binning Mode: {}".format(final_configuration))

        if final_configuration == binning:
            return True
        else:
            print("Camera Binning Mode Configuration Failed")
            return False

    def dcam_set_camera_readout_speed(self, speed_mode=1):
        """
        Change the camera readout speed.
        This property allows you to specify the speed of reading out sensor.
        Usually slower speed has better signal noise ratio (SNR).
        Arg:
            arg1(int)   camera readout speed.
            SLOWEST = 1
            FASTEST = 0x7FFFFFFF2
        Returns:
           True:   configuration set
           False:  error happened.
        """
        idprop = 4194576

        # Get the current readout speed
        initial_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Original Camera Readout Speed: {}".format(initial_configuration))

        # Change the exposure duration
        self.prop_setvalue(idprop, speed_mode)

        # Confirm the exposure was changed.
        final_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Current Camera Readout Speed: {}".format(final_configuration))

        if final_configuration == speed_mode:
            return True
        else:
            print("Readout Speed Configuration Failed")
            return False

    def dcam_set_camera_trigger_active(self, mode=1):
        """
        Change the camera defect correction mode.
        Arg:
            arg1(int)   Trigger active mode.
            EDGE = 1
            LEVEL = 2
            SYNCREADOUT = 3
            POINT = 4
        Returns:
           True:   configuration set
           False:  error happened.
        """
        idprop = 1048864

        # Get the current trigger active mode
        initial_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Original Trigger Active Mode: {}".format(initial_configuration))

        # Change the exposure duration
        self.prop_setvalue(idprop, mode)

        # Confirm the exposure was changed.
        final_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Current Trigger Active Mode: {}".format(final_configuration))

        if final_configuration == mode:
            return True
        else:
            print("Camera Trigger Active Configuration Failed")
            return False

    def dcam_set_camera_trigger_mode(self, mode=1):
        """
        Change the camera defect correction mode.
        Arg:
            arg1(float)   Camera trigger mode.
            NORMAL = 1
            PIV = 3
            START = 6
        Returns:
           True:   configuration set
           False:  error happened.
        """
        idprop = 1049104
        mode = float(mode)

        # Get the current exposure duration
        initial_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Original Trigger Mode: {}".format(initial_configuration))

        # Change the exposure duration
        self.prop_setvalue(idprop, mode)

        # Confirm the exposure was changed.
        final_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Current Trigger Mode: {}".format(final_configuration))

        if final_configuration == mode:
            return True
        else:
            print("Camera Trigger Mode Configuration Failed")
            return False

    def dcam_set_camera_trigger_polarity(self, mode=2):
        """
        Change the camera trigger polarity.
        Arg:
            arg1(int)   Trigger polarity mode
            NEGATIVE = 1
            POSITIVE = 2
        Returns:
           True:   configuration set
           False:  error happened.
        """
        idprop = 1049120

        # Get the current exposure duration
        initial_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Original Trigger Polarity: {}".format(initial_configuration))

        # Change the exposure duration
        self.prop_setvalue(idprop, mode)

        # Confirm the exposure was changed.
        final_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Current Trigger Polarity: {}".format(final_configuration))

        if final_configuration == mode:
            return True
        else:
            print("Camera Trigger Polarity Configuration Failed")
            return False

    def dcam_set_camera_trigger_source(self, mode=2):
        """
        Change the camera defect correction mode.
        Arg:
            arg1(int)   Camera trigger source
            INTERNAL = 1
            EXTERNAL = 2
            SOFTWARE = 3
            MASTERPULSE = 4
        Returns:
           True:   configuration set
           False:  error happened.
        """
        idprop = 1048848

        # Get the current trigger source
        initial_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Original Trigger Source: {}".format(initial_configuration))

        # Change the exposure duration
        self.prop_setvalue(idprop, mode)

        # Confirm the exposure was changed.
        final_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Current Trigger Source: {}".format(final_configuration))

        if final_configuration == mode:
            return True
        else:
            print("Camera Trigger Source Configuration Failed")
            return False

    def dcam_set_camera_internal_line_interval(self, mode=0.000075):
        """
        Change the camera defect correction mode.
        Arg:
            arg1(float)   Camera internal line interval.
        Returns:
           True:   configuration set
           False:  error happened.
        """
        idprop = 4208720

        # Get the current exposure duration
        initial_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Original Internal line Interval: {}".format(initial_configuration))

        # Change the exposure duration
        self.prop_setvalue(idprop, mode)

        # Confirm the exposure was changed.
        final_configuration = self.prop_getvalue(idprop)
        if self.verbose:
            print("Current Internal Line Interval: {}".format(final_configuration))

        if final_configuration == mode:
            return True
        else:
            print("Camera Internal Line Interval Configuration Failed")
            return False

    def dcam_set_default_light_sheet_mode_parameters(self):
        """
        Change the camera to the default light-sheet mode.
        Arg:
        Returns:
        """
        if self.verbose:
            print("Setting Default Camera Light-Sheet Mode Parameters")
        self.dcam_set_camera_exposure(0.2)
        self.dcam_set_camera_sensor_mode(12)
        self.dcam_set_camera_defect_correction_mode(1)
        self.dcam_set_camera_binning_mode(1)
        self.dcam_set_camera_readout_speed(1)
        self.dcam_set_camera_trigger_active(1)
        self.dcam_set_camera_trigger_mode(2)
        self.dcam_set_camera_trigger_polarity(2)
        self.dcam_set_camera_trigger_source(2)
        self.dcam_set_camera_internal_line_interval(0.000075)

    def dcam_set_default_area_mode_parameters(self):
        """
        Change the camera to the default area mode paramters.
        Arg:
        Returns:
        """
        if self.verbose:
            print("Setting Default Camera Area Mode Parameters")
        self.dcam_set_camera_exposure(0.2)
        self.dcam_set_camera_sensor_mode(1)
        self.dcam_set_camera_defect_correction_mode(1)
        self.dcam_set_camera_binning_mode(1)
        self.dcam_set_camera_readout_speed(1)
        self.dcam_set_camera_trigger_active(1)
        self.dcam_set_camera_trigger_mode(2)
        self.dcam_set_camera_trigger_polarity(2)
        self.dcam_set_camera_trigger_source(2)

    def dcam_show_properties(self):
        """
        Show supported properties
        """
        if self.dev_open() is not False:
            idprop = self.prop_getnextid(0)
            print(" IDPROP - BINARY - PROPNAME - PROPVAL")
            while idprop is not False:
                output = '0x{:08X}'.format(idprop)
                propname = self.prop_getname(idprop)
                propval = self.prop_getvalue(idprop)
                if propname is not False:
                    output = str(idprop) + " - " + output + " - " + propname + " - " + str(propval)

                print(output)
                idprop = self.prop_getnextid(idprop)

            self.dev_close()
        else:
            print('-NG: Dcam.dev_open() fails with error {}'.format(self.lasterr()))



if __name__ == '__main__':
    from dcamapi4 import *

    ''' Testing and Examples Section '''
    # dcam_set_camera_exposure(0, 0.1)
    if Dcamapi.init() is not False:
        camera = Dcam(iDevice=0)
        camera.dcam_show_properties()
        #dcam.dcam_set_default_light_sheet_mode_parameters()
        #dcam_show_properties()   # dcam_show_device_list()
        #dcam_live_capturing()

    def dcamtest_show_framedata(data, windowtitle, iShown):
        """
        Show numpy buffer as an image

        Arg1:   NumPy array
        Arg2:   Window name
        Arg3:   Last window status.
            0   open as a new window
            <0  already closed
            >0  already openend
        """
        if iShown > 0 and cv2.getWindowProperty(windowtitle, 0) < 0:
            return -1  # Window has been closed.
        if iShown < 0:
            return -1  # Window is already closed.

        if data.dtype == np.uint16:
            imax = np.amax(data)
            if imax > 0:
                imul = int(65535 / imax)
                # print('Multiple %s' % imul)
                data = data * imul

            cv2.imshow(windowtitle, data)
            return 1
        else:
            print('-NG: dcamtest_show_image(data) only support Numpy.uint16 data')
            return -1

    def dcamtest_thread_live(dcam):
        """
        Show live image

        Arg1:   Dcam instance
        """
        if dcam.cap_start() is not False:

            timeout_milisec = 100
            iWindowStatus = 0
            while iWindowStatus >= 0:
                if dcam.wait_capevent_frameready(timeout_milisec) is not False:
                    data = dcam.buf_getlastframedata()
                    iWindowStatus = dcamtest_show_framedata(data, 'test', iWindowStatus)
                else:
                    dcamerr = dcam.lasterr()
                    if dcamerr.is_timeout():
                        print('===: timeout')
                    else:
                        print('-NG: Dcam.wait_event() fails with error {}'.format(dcamerr))
                        break

                key = cv2.waitKey(1)
                if key == ord('q') or key == ord('Q'):  # if 'q' was pressed with the live window, close it
                    break

            dcam.cap_stop()
        else:
            print('-NG: Dcam.cap_start() fails with error {}'.format(dcam.lasterr()))

    def dcam_live_capturing(iDevice=0):
        """
        Capture and show a image
        """
        if Dcamapi.init() is not False:
            dcam = Dcam(iDevice)
            if dcam.dev_open() is not False:
                if dcam.buf_alloc(3) is not False:
                    # th = threading.Thread(target=dcamtest_thread_live, args=(dcam,))
                    # th.start()
                    # th.join()
                    dcamtest_thread_live(dcam)

                    # release buffer
                    dcam.buf_release()
                else:
                    print('-NG: Dcam.buf_alloc(3) fails with error {}'.format(dcam.lasterr()))
                dcam.dev_close()
            else:
                print('-NG: Dcam.dev_open() fails with error {}'.format(dcam.lasterr()))
        else:
            print('-NG: Dcamapi.init() fails with error {}'.format(Dcamapi.lasterr()))

        Dcamapi.uninit()

    def dcam_show_device_list():
        """
        Show device list
        """
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
                # dcam.dcam_set_camera_exposure(0.2)
                # dcam.dcam_set_camera_sensor_mode(12)
                # dcam.dcam_set_camera_defect_correction_mode(2)
                # dcam.dcam_set_camera_binning_mode(2)
                dcam.dcam_set_default_light_sheet_mode_parameters()
                idprop = dcam.prop_getnextid(0)
                print(" IDPROP - BINARY - PROPNAME - PROPVAL")
                while idprop is not False:
                    output = '0x{:08X}'.format(idprop)

                    propname = dcam.prop_getname(idprop)

                    propval = dcam.prop_getvalue(idprop)

                    if propname is not False:
                        output = str(idprop) + " - " + output + " - " + propname + " - " + str(propval)

                    print(output)
                    idprop = dcam.prop_getnextid(idprop)

                dcam.dev_close()
            else:
                print('-NG: Dcam.dev_open() fails with error {}'.format(dcam.lasterr()))
        else:
            print('-NG: Dcamapi.init() fails with error {}'.format(Dcamapi.lasterr()))

        Dcamapi.uninit()

    def dcam_set_camera_exposure(iDevice=0, exposure=0.1):
        """
        Show supported properties
        """
        if Dcamapi.init() is not False:
            dcam = Dcam(iDevice)
            if dcam.dev_open() is not False:
                idprop = 2031888
                # Get the current exposure duration
                propval = dcam.prop_getvalue(idprop)
                print("Original Exposure Time: {}".format(propval))

                # Change the exposure duration
                dcam.prop_setvalue(idprop, exposure)

                # Confirm the exposure was changed.
                propval = dcam.prop_getvalue(idprop)
                print("Current Exposure Time: {}".format(propval))

                dcam.dev_close()
            else:
                print('-NG: Dcam.dev_open() fails with error {}'.format(dcam.lasterr()))
        else:
            print('-NG: Dcamapi.init() fails with error {}'.format(Dcamapi.lasterr()))

        Dcamapi.uninit()





