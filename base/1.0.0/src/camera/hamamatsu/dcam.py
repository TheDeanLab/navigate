# dcam.py : Jun 30, 2021
#
# Copyright (C) 2021 Hamamatsu Photonics K.K.. All right reserved.
#
# The declarations of classes and functions in this file are subject to change without notice.

from .dcamapi4 import *
import numpy as np


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


