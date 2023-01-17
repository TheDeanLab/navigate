# -*- coding: utf-8 -*-
"""
    This file refers to `ZhuangLab <https://github.com/ZhuangLab/storm-control>`, 'dcamapi4.py' and 'dcam.py'
    This is a simplified version.

    Constants can be found at 'dcamsdk4/inc/dcamapi4.h' and 'dcamsdk4/inc/dcamprop.h'
    Function definitions can be found at 'dcamsdk4/doc/api_reference/dcamapi4_en.html'
"""

# Standard Library Imports
from ctypes import *
from enum import IntEnum
import logging

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

# ==== load shared library ====

__dll = windll.LoadLibrary("dcamapi.dll")

# ==== declare constants ====
DCAMBUF_ATTACHKIND_FRAME = 0
DCAMCAP_START_SEQUENCE = -1
DCAMWAIT_CAPEVENT_FRAMEREADY = 2
DCAMWAIT_CAPEVENT_STOPPED = 16
DCAMPROP_MODE__OFF = 1  # OFF
DCAMPROP_MODE__ON = 2  # ON


class DCAMPROP:
    """
    Valuable reference for understanding the values returned by the camera
    """

    class SENSORMODE(IntEnum):
        AREA = 1
        LINE = 3
        TDI = 4
        TDI_EXTENDED = 10
        PROGRESSIVE = 12
        SPLITVIEW = 14
        DUALLIGHTSHEET = 16
        PHOTONNUMBERRESOLVING = 18

    class SHUTTER_MODE(IntEnum):
        GLOBAL = 1
        ROLLING = 2

    class READOUTSPEED(IntEnum):
        SLOWEST = 1
        FASTEST = 0x7FFFFFFF

    class READOUT_DIRECTION(IntEnum):
        FORWARD = 1
        BACKWARD = 2
        BYTRIGGER = 3
        DIVERGE = 5

    class READOUT_UNIT(IntEnum):
        FRAME = 2
        BUNDLEDLINE = 3
        BUNDLEDFRAME = 4

    class CMOSMODE(IntEnum):
        NORMAL = 1
        NONDESTRUCTIVE = 2

    class OUTPUT_INTENSITY(IntEnum):
        NORMAL = 1
        TESTPATTERN = 2

    class OUTPUTDATA_OPERATION(IntEnum):
        RAW = 1
        ALIGNED = 2

    class TESTPATTERN_KIND(IntEnum):
        FLAT = 2
        IFLAT = 3
        HORZGRADATION = 4
        IHORZGRADATION = 5
        VERTGRADATION = 6
        IVERTGRADATION = 7
        LINE = 8
        ILINE = 9
        DIAGONAL = 10
        IDIAGONAL = 11
        FRAMECOUNT = 12

    class DIGITALBINNING_METHOD(IntEnum):
        MINIMUM = 1
        MAXIMUM = 2
        ODD = 3
        EVEN = 4
        SUM = 5
        AVERAGE = 6

    class TRIGGERSOURCE(IntEnum):
        INTERNAL = 1
        EXTERNAL = 2
        SOFTWARE = 3
        MASTERPULSE = 4

    class TRIGGERACTIVE(IntEnum):
        EDGE = 1
        LEVEL = 2
        SYNCREADOUT = 3
        POINT = 4

    class BUS_SPEED(IntEnum):
        SLOWEST = 1
        FASTEST = 0x7FFFFFFF

    class TRIGGER_MODE(IntEnum):
        NORMAL = 1
        PIV = 3
        START = 6

    class TRIGGERPOLARITY(IntEnum):
        NEGATIVE = 1
        POSITIVE = 2

    class TRIGGER_CONNECTOR(IntEnum):
        INTERFACE = 1
        BNC = 2
        MULTI = 3

    class INTERNALTRIGGER_HANDLING(IntEnum):
        SHORTEREXPOSURETIME = 1
        FASTERFRAMERATE = 2
        ABANDONWRONGFRAME = 3
        BURSTMODE = 4
        INDIVIDUALEXPOSURE = 7

    class SYNCREADOUT_SYSTEMBLANK(IntEnum):
        STANDARD = 1
        MINIMUM = 2

    class TRIGGERENABLE_ACTIVE(IntEnum):
        DENY = 1
        ALWAYS = 2
        LEVEL = 3
        START = 4

    class TRIGGERENABLE_POLARITY(IntEnum):
        NEGATIVE = 1
        POSITIVE = 2
        INTERLOCK = 3

    class OUTPUTTRIGGER_CHANNELSYNC(IntEnum):
        _1CHANNEL = 1
        _2CHANNELS = 2
        _3CHANNELS = 3

    class OUTPUTTRIGGER_PROGRAMABLESTART(IntEnum):
        FIRSTEXPOSURE = 1
        FIRSTREADOUT = 2

    class OUTPUTTRIGGER_SOURCE(IntEnum):
        EXPOSURE = 1
        READOUTEND = 2
        VSYNC = 3
        HSYNC = 4
        TRIGGER = 6

    class OUTPUTTRIGGER_POLARITY(IntEnum):
        NEGATIVE = 1
        POSITIVE = 2

    class OUTPUTTRIGGER_ACTIVE(IntEnum):
        EDGE = 1
        LEVEL = 2

    class OUTPUTTRIGGER_KIND(IntEnum):
        LOW = 1
        GLOBALEXPOSURE = 2
        PROGRAMABLE = 3
        TRIGGERREADY = 4
        HIGH = 5
        ANYROWEXPOSURE = 6

    class OUTPUTTRIGGER_BASESENSOR(IntEnum):
        VIEW1 = 1
        VIEW2 = 2
        ANYVIEW = 15
        ALLVIEWS = 16

    class EXPOSURETIME_CONTROL(IntEnum):
        OFF = 1
        NORMAL = 2

    class TRIGGER_FIRSTEXPOSURE(IntEnum):
        NEW = 1
        CURRENT = 2

    class TRIGGER_GLOBALEXPOSURE(IntEnum):
        NONE = 1
        ALWAYS = 2
        DELAYED = 3
        EMULATE = 4
        GLOBALRESET = 5

    class FIRSTTRIGGER_BEHAVIOR(IntEnum):
        STARTEXPOSURE = 1
        STARTREADOUT = 2

    class MASTERPULSE_MODE(IntEnum):
        CONTINUOUS = 1
        START = 2
        BURST = 3

    class MASTERPULSE_TRIGGERSOURCE(IntEnum):
        EXTERNAL = 1
        SOFTWARE = 2

    class MECHANICALSHUTTER(IntEnum):
        AUTO = 1
        CLOSE = 2
        OPEN = 3

    class LIGHTMODE(IntEnum):
        LOWLIGHT = 1
        HIGHLIGHT = 2

    class SENSITIVITYMODE(IntEnum):
        OFF = 1
        ON = 2
        INTERLOCK = 3

    class EMGAINWARNING_STATUS(IntEnum):
        NORMAL = 1
        WARNING = 2
        PROTECTED = 3

    class PHOTONIMAGINGMODE(IntEnum):
        _0 = 0
        _1 = 1
        _2 = 2
        _3 = 3

    class SENSORCOOLER(IntEnum):
        OFF = 1
        ON = 2
        MAX = 4

    class SENSORTEMPERATURE_STATUS(IntEnum):
        NORMAL = 0
        WARNING = 1
        PROTECTION = 2

    class SENSORCOOLERSTATUS(IntEnum):
        ERROR4 = -4
        ERROR3 = -3
        ERROR2 = -2
        ERROR1 = -1
        NONE = 0
        OFF = 1
        READY = 2
        BUSY = 3
        ALWAYS = 4
        WARNING = 5

    class REALTIMEGAINCORRECT_LEVEL(IntEnum):
        _1 = 1
        _2 = 2
        _3 = 3
        _4 = 4
        _5 = 5

    class WHITEBALANCEMODE(IntEnum):
        FLAT = 1
        AUTO = 2
        TEMPERATURE = 3
        USERPRESET = 4

    class DARKCALIB_TARGET(IntEnum):
        ALL = 1
        ANALOG = 2

    class SHADINGCALIB_METHOD(IntEnum):
        AVERAGE = 1
        MAXIMUM = 2
        USETARGET = 3

    class CAPTUREMODE(IntEnum):
        NORMAL = 1
        DARKCALIB = 2
        SHADINGCALIB = 3
        TAPGAINCALIB = 4
        BACKFOCUSCALIB = 5

    class INTERFRAMEALU_ENABLE(IntEnum):
        OFF = 1
        TRIGGERSOURCE_ALL = 2
        TRIGGERSOURCE_INTERNAL = 3

    class SHADINGCALIB_DATASTATUS(IntEnum):
        NONE = 1
        FORWARD = 2
        BACKWARD = 3
        BOTH = 4

    class TAPGAINCALIB_METHOD(IntEnum):
        AVE = 1
        MAX = 2
        MIN = 3

    class RECURSIVEFILTERFRAMES(IntEnum):
        _2 = 2
        _4 = 4
        _8 = 8
        _16 = 16
        _32 = 32
        _64 = 64

    class INTENSITYLUT_MODE(IntEnum):
        THROUGH = 1
        PAGE = 2
        CLIP = 3

    class BINNING(IntEnum):
        _1 = 1
        _2 = 2
        _4 = 4
        _8 = 8
        _16 = 16
        _1_2 = 102
        _2_4 = 204

    class COLORTYPE(IntEnum):
        BW = 0x00000001
        RGB = 0x00000002
        BGR = 0x00000003

    class BITSPERCHANNEL(IntEnum):
        _8 = 8
        _10 = 10
        _12 = 12
        _14 = 14
        _16 = 16

    class DEFECTCORRECT_MODE(IntEnum):
        OFF = 1
        ON = 2

    class DEFECTCORRECT_METHOD(IntEnum):
        CEILING = 3
        PREVIOUS = 4

    class HOTPIXELCORRECT_LEVEL(IntEnum):
        STANDARD = 1
        MINIMUM = 2
        AGGRESSIVE = 3

    class DEVICEBUFFER_MODE(IntEnum):
        THRU = 1
        SNAPSHOT = 2

    class SYSTEM_ALIVE(IntEnum):
        OFFLINE = 1
        ONLINE = 2
        ERROR = 3

    class TIMESTAMP_MODE(IntEnum):
        NONE = 1
        LINEBEFORELEFT = 2
        LINEOVERWRITELEFT = 3
        AREABEFORELEFT = 4
        AREAOVERWRITELEFT = 5

    class TIMING_EXPOSURE(IntEnum):
        AFTERREADOUT = 1
        OVERLAPREADOUT = 2
        ROLLING = 3
        ALWAYS = 4
        TDI = 5

    class TIMESTAMP_PRODUCER(IntEnum):
        NONE = 1
        DCAMMODULE = 2
        KERNELDRIVER = 3
        CAPTUREDEVICE = 4
        IMAGINGDEVICE = 5

    class FRAMESTAMP_PRODUCER(IntEnum):
        NONE = 1
        DCAMMODULE = 2
        KERNELDRIVER = 3
        CAPTUREDEVICE = 4
        IMAGINGDEVICE = 5

    class CAMERASTATUS_INTENSITY(IntEnum):
        GOOD = 1
        TOODARK = 2
        TOOBRIGHT = 3
        UNCARE = 4
        EMGAIN_PROTECTION = 5
        INCONSISTENT_OPTICS = 6
        NODATA = 7

    class CAMERASTATUS_INPUTTRIGGER(IntEnum):
        GOOD = 1
        NONE = 2
        TOOFREQUENT = 3

    class CAMERASTATUS_CALIBRATION(IntEnum):
        DONE = 1
        NOTYET = 2
        NOTRIGGER = 3
        TOOFREQUENTTRIGGER = 4
        OUTOFADJUSTABLERANGE = 5
        UNSUITABLETABLE = 6
        TOODARK = 7
        TOOBRIGHT = 8
        NOTDETECTOBJECT = 9

    class CONFOCAL_SCANMODE(IntEnum):
        SIMULTANEOUS = 1
        SEQUENTIAL = 2

    class SUBUNIT_CONTROL(IntEnum):
        NOTINSTALLED = 0
        OFF = 1
        ON = 2

    class SUBUNIT_PINHOLESIZE(IntEnum):
        ERROR = 1
        SMALL = 2
        MEDIUM = 3
        LARGE = 4

    class MODE(IntEnum):
        OFF = 1
        ON = 2


class DCAMDEV_OPEN(Structure):
    _pack_ = 8
    _fields_ = [("size", c_int32), ("index", c_int32), ("hdcam", c_void_p)]  # out

    def __init__(self):
        self.size = sizeof(DCAMDEV_OPEN)
        self.index = 0


class DCAMAPI_INIT(Structure):
    _pack_ = 8
    _fields_ = [
        ("size", c_int32),
        ("iDeviceCount", c_int32),  # out
        ("reserved", c_int32),
        ("initoptionbytes", c_int32),
        ("initoption", POINTER(c_int32)),
        ("guid", c_void_p),  # const DCAM_GUID*
    ]

    def __init__(self):
        self.size = sizeof(DCAMAPI_INIT)


class DCAMWAIT_OPEN(Structure):
    _pack_ = 8
    _fields_ = [
        ("size", c_int32),
        ("supportevent", c_int32),  # out
        ("hwait", c_void_p),  # out
        ("hdcam", c_void_p),
    ]

    def __init__(self):
        self.size = sizeof(DCAMWAIT_OPEN)


class DCAMWAIT_START(Structure):
    _pack_ = 8
    _fields_ = [
        ("size", c_int32),
        ("eventhappened", c_int32),  # out
        ("eventmask", c_int32),
        ("timeout", c_int32),
    ]

    def __init__(self):
        self.size = sizeof(DCAMWAIT_START)


class DCAMERR(IntEnum):
    # success
    SUCCESS = (
        1  # 1, no error, general success code, app should check the value is positive
    )
    ALREADYOPENED = -520093694  # 0xE1000002
    NOTSUPPORT = (
        -2147479805
    )  # 0x80000f03, camera does not support the function or property with current settings
    TIMEOUT = -2147483386  # 0x80000106, timeout

    # status error
    BUSY = -2147483391  # 0x80000101, API cannot process in busy state.
    NOTREADY = -2147483389  # 0x80000103, API requires ready state.
    NOTSTABLE = -2147483388  # 0x80000104, API requires stable or unstable state.
    UNSTABLE = -2147483387  # 0x80000105, API does not support in unstable state.

    # calling error
    INVALIDCAMERA = -2147481594  # 0x80000806, invalid camera
    INVALIDHANDLE = -2147481593  # 0x80000807, invalid camera handle
    INVALIDPARAM = -2147481592  # 0x80000808, invalid parameter
    INVALIDVALUE = -2147481567  # 0x80000821, invalid property value
    OUTOFRANGE = -2147481566  # 0x80000822, value is out of range
    NOTWRITABLE = -2147481565  # 0x80000823, the property is not writable
    NOTREADABLE = -2147481564  # 0x80000824, the property is not readable
    INVALIDPROPERTYID = -2147481563  # 0x80000825, the property id is invalid


class DCAMPROP_ATTR(Structure):
    _pack_ = 8
    _fields_ = [
        ("cbSize", c_int32),
        ("iProp", c_int32),
        ("option", c_int32),
        ("iReserved1", c_int32),
        ("attribute", c_int32),
        ("iGroup", c_int32),
        ("iUnit", c_int32),
        ("attribute2", c_int32),
        ("valuemin", c_double),
        ("valuemax", c_double),
        ("valuestep", c_double),
        ("valuedefault", c_double),
        ("nMaxChannel", c_int32),
        ("iReserved3", c_int32),
        ("nMaxView", c_int32),
        ("iProp_NumberOfElement", c_int32),
        ("iProp_ArrayBase", c_int32),
        ("iPropStep_Element", c_int32),
    ]

    def __init__(self):
        self.cbSize = sizeof(DCAMPROP_ATTR)


class DCAMBUF_ATTACH(Structure):
    _pack_ = 8
    _fields_ = [
        ("size", c_int32),  # sizeof(*this)
        ("iKind", c_int32),  # DCAMBUF_ATTAHKIND: DCAMBUF_ATTACHKIND_FRAME = 0
        ("buffer", POINTER(c_void_p)),  # array of buffer pointers
        ("buffercount", c_int32),  # number of pointers in array "buffer"
    ]

    def __init__(self):
        self.size = sizeof(DCAMBUF_ATTACH)


class DCAMCAP_TRANSFERINFO(Structure):
    _pack_ = 8
    _fields_ = [
        ("size", c_int32),
        ("iKind", c_int32),
        ("nNewestFrameIndex", c_int32),
        ("nFrameCount", c_int32),
    ]

    def __init__(self):
        self.size = sizeof(DCAMCAP_TRANSFERINFO)
        self.iKind = 0
        self.nNewestFrameIndex = -1
        self.nFrameCount = 0


class DCAMDATA_HDR(Structure):
    _pack_ = 8
    _fields_ = [
        ("size", c_int32),
        ("iKind", c_int32),
        ("option", c_int32),
        ("reserved2", c_int32),
    ]

    def __init__(self):
        self.size = sizeof(DCAMDATA_HDR)
        self.iKind = 0
        self.option = 0
        self.reserved2 = 0


class DCAMDATA_REGIONRECT(Structure):
    _pack_ = 8
    _fields_ = [
        ("left", c_short),
        ("top", c_short),
        ("right", c_short),
        ("bottom", c_short),
    ]


class DCAMDATA_REGION(Structure):
    _pack_ = 8
    _fields_ = [
        ("hdr", POINTER(DCAMDATA_HDR)),
        ("option", c_int32),
        ("type", c_int32),
        ("data", c_void_p),
        ("datasize", c_int32),
        ("reserved", c_int32),
    ]


class DCAMDEV_STRING(Structure):
    _fields_ = [
        ("size", c_int32),
        ("iString", c_int32),
        ("text", c_char_p),
        ("textbytes", c_int32),
    ]


property_dict = {
    "exposure_time": 2031888,  # 0x001F0110, R/W, sec, "EXPOSURE TIME"
    "sensor_mode": 4194832,  # 0x00400210, R/W, mode,  "SENSOR MODE"
    "defect_correct_mode": 4653072,  # 0x00470010, R/W, mode,  "DEFECT CORRECT MODE"
    "binning": 4198672,  # 0x00401110, R/W, mode, "BINNING"
    "readout_speed": 4194576,  # 0x00400110, R/W, long,    "READOUT SPEED"
    "readout_direction": 4194608,  # 0x00400130, R/W, mode,   "READOUT DIRECTION"
    "readout_time": 4206608,  # 0x00403010, R/O, sec,   "TIMING READOUT TIME"
    "trigger_active": 1048864,  # 0x00100120, R/W, mode,   "TRIGGER ACTIVE"
    "trigger_mode": 1049104,  # 0x00100210, R/W, mode,    "TRIGGER MODE"
    "trigger_polarity": 1049120,  # 0x00100220, R/W, mode, "TRIGGER POLARITY"
    "trigger_source": 1048848,  # 0x00100110, R/W, mode,   "TRIGGER SOURCE"
    "trigger_delay": 1049184,  # 0x00100260,	/* R/W, sec,	"TRIGGER DELAY"			*/
    "internal_line_interval": 4208720,  # 0x00403850, R/W, sec,    "INTERNAL LINE INTERVAL"
    "image_width": 4325904,  # 0x00420210, R/O, long, "IMAGE WIDTH"
    "image_height": 4325920,  # 0x00420220, R/O, long,    "IMAGE HEIGHT"
    "exposuretime_control": 2031920,  # 0x001F0130, R/W, mode,    "EXPOSURE TIME CONTROL"
    "subarray_hpos": 4202768,  # 0x00402110, R/W, long,    "SUBARRAY HPOS"
    "subarray_hsize": 4202784,  # 0x00402120, R/W, long,   "SUBARRAY HSIZE"
    "subarray_vpos": 4202800,  # 0x00402130, R/W, long,    "SUBARRAY VPOS"
    "subarray_vsize": 4202816,  # 0x00402140, R/W, long,   "SUBARRAY VSIZE"
    "subarray_mode": 4202832,  # 0x00402150, R/W, mode,    "SUBARRAY MODE"
    "cyclic_trigger_period": 4206624,  # 0x00403020, R/O, sec,	"TIMING CYCLIC TRIGGER PERIOD"
    "minimum_trigger_blank": 4206640,  # 0x00403030, R/O, sec,	"TIMING MINIMUM TRIGGER BLANKING"
    "minimum_trigger_interval": 4206672,  # 0x00403050, R/O, sec,	"TIMING MINIMUM TRIGGER INTERVAL"
}


# ==== api function references ====
dcamapi_init = __dll.dcamapi_init
dcamapi_uninit = __dll.dcamapi_uninit
dcamdev_open = __dll.dcamdev_open
dcamdev_close = __dll.dcamdev_close
dcamwait_open = __dll.dcamwait_open
dcamwait_close = __dll.dcamwait_close
dcamprop_getattr = __dll.dcamprop_getattr
dcamprop_getvalue = __dll.dcamprop_getvalue
dcamprop_setvalue = __dll.dcamprop_setvalue
dcamprop_setgetvalue = __dll.dcamprop_setgetvalue
dcambuf_attach = __dll.dcambuf_attach
dcambuf_release = __dll.dcambuf_release
dcamcap_start = __dll.dcamcap_start
dcamcap_stop = __dll.dcamcap_stop
dcamcap_transferinfo = __dll.dcamcap_transferinfo
dcamwait_start = __dll.dcamwait_start
dcamwait_abort = __dll.dcamwait_abort
dcamcap_firetrigger = __dll.dcamcap_firetrigger
#dcamdev_setdata = __dll.dcamdev_setdata
dcamdev_getstring = __dll.dcamdev_getstring


class camReg(object):
    """
    Keep track of the number of cameras initialised so we can initialise and
    finalise the library.

    Cribbed from https://github.com/python-microscopy/python-microscopy/blob/master/PYME/Acquire/Hardware/HamamatsuDCAM/HamamatsuDCAM.py
    """

    numCameras = 0
    maxCameras = 0

    @classmethod
    def regCamera(cls):
        if cls.numCameras <= 0:
            # Initialize the API
            paraminit = DCAMAPI_INIT()
            if int(dcamapi_init(byref(paraminit))) < 0:
                # NOTE: This is an AttributeError to match the other error thrown by this class in startup functions.
                # This really makes no sense as an attribute error.
                dcamapi_uninit()
                raise Exception("DCAM initialization failed.")
            cls.maxCameras = paraminit.iDeviceCount
            cls.numCameras = 0

        cls.numCameras += 1
        print(f"Number of cameras is {cls.numCameras}")

    @classmethod
    def unregCamera(cls):
        cls.numCameras -= 1
        if cls.numCameras == 0:
            print('Uninit DCAM API!')
            dcamapi_uninit()


class DCAM:
    def __init__(self, index=0):
        self.__hdcam = 0
        self.__hdcamwait = 0

        # open camera
        if not self.dev_open(index):
            raise Exception(f"DCAM_{index} failed to open!")
        self.__open_hdcamwait()

        self.prop_setvalue(property_dict["subarray_mode"], DCAMPROP_MODE__OFF)
        self.max_image_width = self.get_property_value("image_width")
        self.max_image_height = self.get_property_value("image_height")

        self.is_acquiring = False

        self._serial_number = self.get_string_value(
            c_int32(int("0x04000102", 0))
        ).strip("S/N: ")

        print(f'>>> IN DCAM CLASS: {index} | {self._serial_number}')

    def __del__(self):
        print("DCAM::__del__ called!")
        self.dev_close()

    def __result(self, errvalue):
        """
        Internal use. Keep last error code
        """
        if errvalue < 0:
            try:
                print("error message: ", DCAMERR(errvalue))
            except:
                print("error message: ", errvalue)
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

        self.__hdcamwait = c_void_p(paramwaitopen.hwait)
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
        print("Opening Camera")
        if self.__hdcam:
            print("Camera already open")
            return self.__result(
                DCAMERR.ALREADYOPENED
            )  # instance is already opened. New Error.

        camReg.regCamera()  # Make sure DCAMAPI is initialized

        paramopen = DCAMDEV_OPEN()
        if index >= 0:
            paramopen.index = index
        else:
            paramopen.index = self.__iDevice

        ret = self.__result(dcamdev_open(byref(paramopen)))
        if ret is False:
            print("Camera dev_open failed")
            return False
        else:
            print("Camera Open")

        self.__hdcam = c_void_p(paramopen.hdcam)

        return True

    def dev_close(self):
        """
        Close dcam handle.
        Call this if you need to close the current device.

        Returns:
            True:
        """
        print(f"Closing camera...")
        if self.__hdcam:
            self.__close_hdcamwait()
            dcamdev_close(self.__hdcam)
            self.__hdcam = 0

        camReg.unregCamera()

        return True

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
        if not self.__hdcam:
            self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.
            return None

        propattr = DCAMPROP_ATTR()
        propattr.iProp = idprop
        ret = self.__result(dcamprop_getattr(self.__hdcam, byref(propattr)))
        if ret is False:
            return None

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
        if not self.__hdcam:
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        cDouble = c_double()
        ret = self.__result(dcamprop_getvalue(self.__hdcam, idprop, byref(cDouble)))
        # print("prop_getvalue response:", cDouble.value)
        # print("property id:", idprop)
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
        if not self.__hdcam:
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        fValue = c_double(fValue)
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
        if not self.__hdcam:
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        cDouble = c_double(fValue)
        cOption = c_int32(option)
        cIDProp = c_int32(idprop)
        ret = self.__result(
            dcamprop_setgetvalue(self.__hdcam, cIDProp, byref(cDouble), cOption)
        )
        if ret is False:
            return False

        return cDouble.value

    def get_property_range(self, idprop):
        """
        # Returns the range of appropriate values
        """
        property_attribute = self.prop_getattr(idprop)
        if property_attribute != None:
            return [
                float(property_attribute.valuemin),
                float(property_attribute.valuemax),
            ]
        return [None, None]

    def set_property_value(self, name, value):
        """
        # this function will set property value according to property name
        """
        if name not in property_dict:
            print(
                "could not set value for",
                name,
                "please make sure the property name is correct and is added to property_dict!",
            )
            return False

        # get property code setPropertyValue
        idprop = property_dict[name]

        # Find property limits and correct value if necessary
        r = self.get_property_range(idprop)

        [property_value_min, property_value_max] = r  # self.get_property_range(idprop)
        if property_value_min is None:
            print("Could not set attribute", name)
            print("property range:", name, r)
            return False

        if value < property_value_min:
            print(
                " The property value of ",
                value,
                "is less than minimum of",
                property_value_min,
                name,
                "setting to minimum",
            )
            value = property_value_min
        if value > property_value_max:
            print(
                " The property value of",
                value,
                "is greater than maximum of",
                property_value_max,
                name,
                "setting to maximum",
            )
            value = property_value_max

        # Set value and get what is set
        final_configuration = self.prop_setgetvalue(idprop, value)

        if (
            final_configuration >= value - value / 100
            and final_configuration <= value + value / 100
        ):
            return True
        else:
            print(name, "Configuration Failed", value, final_configuration)
            return False

    def get_property_value(self, name):
        """
        Provides the idprop value after looking it up in the property_dict
        """
        return self.prop_getvalue(property_dict[name])

    def get_string_value(self, id_str):
        """
        Get attribute value from the camera by IDSTR (or ERR) as a string.

        Parameters
        ----------
        id_str : c_int32

        Returns
        -------
        Value of IDSTR or ERR as a string.
        """

        c_buf_len = 256
        c_buf = create_string_buffer(c_buf_len)
        param = DCAMDEV_STRING()
        param.size = sizeof(param)
        param.text = addressof(c_buf)
        param.textbytes = c_int32(c_buf_len)
        param.iString = id_str
        dcamdev_getstring(self.__hdcam, byref(param))

        return c_buf.value.decode()

    def set_ROI(self, left, top, right, bottom):
        """
        # this function set 'subarray' properties.
        # Width - Can be an even or odd number.
        # Height - Can be an even number.
        # Horizontal Position - Can be even or odd number.
        # Vertical Position - Can be even number.
        # Bottom must be even number.
        """
        # TODO: parameter verification
        if (
            top % 2
            or bottom % 2 == 0
            or (right - left + 1) > self.max_image_width
            or (bottom - top + 1) > self.max_image_height
        ):
            print("Invalid size")
            return (
                self.prop_getvalue(property_dict["image_width"]),
                self.prop_getvalue(property_dict["image_height"]),
            )

        # test if hsize and vsize equal to maximum image width and height
        # if the same, set subarray_mode to DCAMPROP_MODE__OFF
        if (
            right - left + 1 == self.max_image_width
            and bottom - top + 1 == self.max_image_height
        ):
            self.prop_setgetvalue(property_dict["subarray_mode"], DCAMPROP_MODE__OFF)
            # TODO: double check if the width/height is set to maximum value.
            # self.prop_setvalue(property_dict['image_width'], self.max_image_width)
            # self.prop_setvalue(property_dict['image_height'], self.max_image_height)
            return (self.max_image_width, self.max_image_height)

        width = self.prop_getvalue(property_dict["image_width"])
        height = self.prop_getvalue(property_dict["image_height"])
        if right - left + 1 == width and bottom - top + 1 == height:
            self.prop_setvalue(property_dict["subarray_hpos"], left)
            self.prop_setvalue(property_dict["subarray_vpos"], top)
        else:
            # set DCAM_IDPROP_SUBARRAYMODE to 'OFF'
            if self.prop_setgetvalue(
                property_dict["subarray_mode"], DCAMPROP_MODE__OFF
            ):
                # set hpos, hsize, vpos, vsize
                # self.prop_setvalue(property_dict['subarray_hpos'], 0)
                self.prop_setvalue(property_dict["subarray_hpos"], left)

                # hsize works.
                self.prop_setvalue(property_dict["subarray_hsize"], right - left + 1)

                self.prop_setvalue(property_dict["subarray_vpos"], top)

                # vsize must be an even number? Probably need a mod statement.
                self.prop_setvalue(property_dict["subarray_vsize"], bottom - top + 1)

        # set DCAM_IDPROP_SUBARRAYMODE to 'ON'
        self.prop_setgetvalue(property_dict["subarray_mode"], DCAMPROP_MODE__ON)

        return (
            self.prop_getvalue(property_dict["image_width"]),
            self.prop_getvalue(property_dict["image_height"]),
        )

    def start_acquisition(self, data_buffer, number_of_frames=100):
        """
        # this function will initialize parameters, attach buffer, start capture
        """
        # initialize buffer index
        self.pre_index = -1
        self.number_of_frames = number_of_frames

        # prepare buffer pointer array
        self.data_buffer = data_buffer
        ptr_array = c_void_p * number_of_frames
        self.data_ptr = ptr_array()
        for i in range(number_of_frames):
            np_array = data_buffer[i]
            self.data_ptr[i] = np_array.ctypes.data

        # attach buffer
        attach_param = DCAMBUF_ATTACH()
        attach_param.iKind = DCAMBUF_ATTACHKIND_FRAME
        attach_param.buffer = self.data_ptr
        attach_param.buffercount = self.number_of_frames
        if self.__result(dcambuf_attach(self.__hdcam, attach_param)):
            self.pre_frame_count = 0
            self.pre_index = 0
            # start capture
            self.is_acquiring = True
            return self.__result(dcamcap_start(self.__hdcam, DCAMCAP_START_SEQUENCE))
        return False

    def stop_acquisition(self):
        """
        # this function will stop capture and detach buffer
        """
        # stop capture
        dcamcap_stop(self.__hdcam)

        self.is_acquiring = False

        # detach buffer
        return self.__result(dcambuf_release(self.__hdcam, DCAMBUF_ATTACHKIND_FRAME))

    def get_frames(self):
        """
        # this function will return a list of frame index
        # following lines are from documents: 'dcamapi4-en.html'
        # The host software can check the capturing status with the dcamcap_status() function. It will return a DCAMCAP_STATUS.
        # The dcamcap_transferinfo() function returns the total number of images captured and the frame index of the last captured image.
        # These functions do not wait for any events and will return with their values immediately.
        # These functions are useful for polling however this is stressful to the CPU.
        # We recommend using dcamwait functions to wait for events such as the arrival of new frames, then calling these functions to check status and/or transferred information.
        """
        # current solution: wait for a new frame, then call dcamcap_transferinfo()
        frame_idx_list = []
        wait_param = DCAMWAIT_START()
        wait_param.eventmask = DCAMWAIT_CAPEVENT_FRAMEREADY | DCAMWAIT_CAPEVENT_STOPPED
        wait_param.timeout = 500  # 500ms
        #  Timeout Duration - Will throw an error if the timeout is too small.
        #  Currently set to a value > maximum typical integration time.

        if self.__result(dcamwait_start(self.__hdcamwait, byref(wait_param))):
            cap_info = DCAMCAP_TRANSFERINFO()
            dcamcap_transferinfo(self.__hdcam, byref(cap_info))
            # after testing with the camera, we find out that:
            # nNewestFrameIndex starts from 0;
            # nFrameCount increments all the frames from beginning even we have already pulled the info out
            frame_count = cap_info.nFrameCount - self.pre_frame_count

            # print("Frame Count - cap_info", cap_info.nFrameCount, frame_count)
            # print("Newest Frame Index - cap_info", cap_info.nNewestFrameIndex)
            #
            if frame_count <= cap_info.nNewestFrameIndex + 1:
                frame_idx_list = list(
                    range(
                        cap_info.nNewestFrameIndex - frame_count + 1,
                        cap_info.nNewestFrameIndex + 1,
                    )
                )
            else:
                frame_idx_list = list(
                    range(
                        self.number_of_frames
                        - frame_count
                        + cap_info.nNewestFrameIndex
                        + 1,
                        self.number_of_frames,
                    )
                ) + list(range(0, cap_info.nNewestFrameIndex + 1))

            # check if backlog happens
            # if (self.pre_index+1) % self.number_of_frames != frame_idx_list[0]:
            #    print('backlog happens!')
            self.pre_index = cap_info.nNewestFrameIndex
            self.pre_frame_count = cap_info.nFrameCount

        return frame_idx_list

    def get_camera_handler(self):
        return self.__hdcam

    def fire_software_trigger(self):
        trigger_source = self.get_property_value("trigger_source")
        if trigger_source == 3.0:
            # fire trigger to camera
            err = dcamcap_firetrigger(self.__hdcam, 0)
            if err < 0:
                print("an error happened when sending trigger to the camera", err)
        else:
            print(f"Camera is in mode {trigger_source}, not software mode (3).")


if __name__ == "__main__":
    print("start testing Hamamatsu API!")

    # create shared memory buffer
    import sys

    sys.path.append("../../../concurrency")
    from concurrency_tools import SharedNDArray
    import threading
    import time

    number_of_frames = 200
    # TODO: Get the shape of the image from the configuration file (at least for the real software not testing)
    # CameraParameters:
    # # Hamamatsu Orca Flash 4.0
    # number_of_cameras: 1
    # x_pixels: 2048.0
    # y_pixels: 2048.0

    start_time = time.time()
    data_buffer = [
        SharedNDArray(shape=(2048, 2048), dtype="uint16")
        for i in range(number_of_frames)
    ]
    stop_time = time.time()
    print(
        "Duration of time to create a buffer for ",
        number_of_frames,
        stop_time - start_time,
    )
    # Grows linearly with the number of frames.

    # start camera
    camera = DCAM(0)

    # initialize camera
    configuration = {
        "image_width": 2048.0,
        "image_height": 2048.0,
        "sensor_mode": 12,  # 12 for progressive
        "defect_correct_mode": 2.0,
        "binning": 1.0,
        "readout_speed": 1.0,
        "trigger_active": 1.0,
        "trigger_mode": 1.0,  # external light-sheet mode
        "trigger_polarity": 2.0,  # positive pulse
        "trigger_source": 3.0,  # software
        "exposure_time": 0.02,
        "internal_line_interval": 0.000075,
    }
    # camera.prop_getvalue(property_dict['exposuretime_control'])

    # configure camera
    for key in configuration:
        # INVALIDVALUE = -2147481567  # 0x80000821, invalid property value
        # INVALIDPROPERTYID = -2147481563  # 0x80000825, the property id is invalid
        # print("property:", property_dict[key], " key:", key)
        camera.prop_setvalue(property_dict[key], configuration[key])

    # start data process
    def data_func():
        while True:
            frames = camera.get_frames()
            if not frames:
                break
            # print('get image frame:', frames)

    def test_acquisition():
        data_process = threading.Thread(target=data_func)
        data_process.name = "HamamatsuAPI Data Process"
        data_process.start()

        # start acquisition
        camera.start_acquisition(data_buffer, number_of_frames)

        # set camera that trigger from software
        TRIGGERSOURCE_SOFTWARE = 3
        if camera.prop_setgetvalue(
            property_dict["trigger_source"], TRIGGERSOURCE_SOFTWARE
        ):

            # fire trigger to camera
            for i in range(10):
                err = dcamcap_firetrigger(camera.get_camera_handler(), 0)
                if err < 0:
                    print("an error happened when sending trigger to the camera", err)
                    break
                time.sleep(configuration["exposure_time"] + 0.005)
        # end acquisition
        camera.stop_acquisition()
        data_process.join()

    def get_buffer_duration():
        # get time cost of attaching and detaching buffer
        for i in range(20):
            number_of_frames += 100
            start_time = time.perf_counter()
            camera.start_acquisition()
            camera.stop_acquisition()
            end_time = time.perf_counter()
            print(
                "time cost to attach a buffer(",
                number_of_frames,
                "):",
                end_time - start_time,
            )

    # test ROI setting
    def test_ROI(roi_height=2048, roi_width=2048):
        camera_height = 2048
        camera_width = 2048

        roi_top = (camera_height - roi_height) / 2
        roi_bottom = roi_top + roi_height - 1
        roi_left = (camera_width - roi_width) / 2
        roi_right = roi_left + roi_width - 1

        width, height = camera.set_ROI(roi_left, roi_top, roi_right, roi_bottom)

        print("image width and height:", width, height)
        print("subarray_hpos", camera.prop_getvalue(property_dict["subarray_hpos"]))
        print("subarray_hsize", camera.prop_getvalue(property_dict["subarray_hsize"]))
        print("subarray_vpos", camera.prop_getvalue(property_dict["subarray_vpos"]))
        print("subarray_vsize", camera.prop_getvalue(property_dict["subarray_vsize"]))
        print(
            "sub array mode(1: OFF, 2: ON): ",
            camera.prop_getvalue(property_dict["subarray_mode"]),
        )

    # test_ROI(1024, 1024)
    # print("camera.prop_getvalue:")
    # print("Camera Exposure Time:", camera.prop_getvalue(property_dict['exposure_time']))
    # print("Camera Readout Time:", camera.prop_getvalue(property_dict['readout_time']))
    #
    # print("camera.get_property_value:")
    # print("Camera Exposure Time:", camera.get_property_value(property_dict['exposure_time']))
    # print("Camera Readout Time:", camera.get_property_value(property_dict['readout_time']))

    test_ROI(512, 512)
    # test_ROI(100, 100, 1124, 1123)
    # test_ROI(0, 0, 1024, 1023)
    # test_ROI(0, 0, 2047, 2047)
    data_buffer = [
        SharedNDArray(shape=(512, 512), dtype="uint16") for i in range(number_of_frames)
    ]
    test_acquisition()
