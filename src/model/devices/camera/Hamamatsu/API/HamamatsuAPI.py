# -*- coding: utf-8 -*-
"""
    This file refers to `ZhuangLab <https://github.com/ZhuangLab/storm-control>`, 'dcamapi4.py' and 'dcam.py'
    This is a simplified version.

    Constants can be found at 'dcamsdk4/inc/dcamapi4.h'
    Function definitions can be found at 'dcamsdk4/doc/api_reference/dcamapi4_en.html'
"""

from ctypes import *
from enum import IntEnum

# ==== load shared library ====

__dll = windll.LoadLibrary('dcamapi.dll')

# ==== declare constants ====
DCAMBUF_ATTACHKIND_FRAME = 0
DCAMCAP_START_SEQUENCE = -1
DCAMWAIT_CAPEVENT_FRAMEREADY = 2
DCAMWAIT_CAPEVENT_STOPPED = 16

class DCAMDEV_OPEN(Structure):
    _pack_ = 8
    _fields_ = [
        ('size', c_int32),
        ('index', c_int32),
        ('hdcam', c_void_p)  # out
    ]

    def __init__(self, index):
        self.size = sizeof(DCAMDEV_OPEN)
        self.index = 0

class DCAMWAIT_OPEN(Structure):
    _pack_ = 8
    _fields_ = [
        ('size', c_int32),
        ('supportevent', c_int32),  # out
        ('hwait', c_void_p),  # out
        ('hdcam', c_void_p)
    ]

    def __init__(self):
        self.size = sizeof(DCAMWAIT_OPEN)

class DCAMWAIT_START(Structure):
    _pack_ = 8
    _fields_ = [
        ('size', c_int32),
        ('eventhappened', c_int32),  # out
        ('eventmask', c_int32),
        ('timeout', c_int32)
    ]

    def __init__(self):
        self.size = sizeof(DCAMWAIT_START)

class DCAMERR(IntEnum):
    # success
    SUCCESS = 1  # 1, no error, general success code, app should check the value is positive
    ALREADYOPENED = -520093694  # 0xE1000002
    INVALIDHANDLE = -2147481593  # 0x80000807, invalid camera handle
    INVALIDWAITHANDLE = -2080366591  # 0x84002001, DCAMWAIT is invalid handle
    INVALIDPARAM = -2147481592  # 0x80000808, invalid parameter
    NOTSUPPORT = -2147479805  # 0x80000f03, camera does not support the function or property with current settings

class DCAMPROP_ATTR(Structure):
    _pack_ = 8
    _fields_ = [
        ('cbSize', c_int32),
        ('iProp', c_int32),
        ('option', c_int32),
        ('iReserved1', c_int32),
        ('attribute', c_int32),
        ('iGroup', c_int32),
        ('iUnit', c_int32),
        ('attribute2', c_int32),
        ('valuemin', c_double),
        ('valuemax', c_double),
        ('valuestep', c_double),
        ('valuedefault', c_double),
        ('nMaxChannel', c_int32),
        ('iReserved3', c_int32),
        ('nMaxView', c_int32),
        ('iProp_NumberOfElement', c_int32),
        ('iProp_ArrayBase', c_int32),
        ('iPropStep_Element', c_int32)
    ]

    def __init__(self):
        self.cbSize = sizeof(DCAMPROP_ATTR)

class DCAMBUF_ATTACH(Structure):
    _pack_ = 8
    _field_ = [
        ('size', c_int32), # sizeof(*this)
        ('iKind', c_int32), # DCAMBUF_ATTAHKIND: DCAMBUF_ATTACHKIND_FRAME = 0
        ('buffer', POINTER(c_void_p)), # array of buffer pointers
        ('buffercount', c_int32) # number of pointers in array "buffer"
    ]

    def __init__(self):
        self.size = sizeof(DCAMBUF_ATTACH)

class DCAMCAP_TRANSFERINFO(Structure):
    _pack_ = 8
    _fields_ = [
        ('size', c_int32),
        ('iKind', c_int32),
        ('nNewestFrameIndex', c_int32),
        ('nFrameCount', c_int32)
    ]

    def __init__(self):
        self.size = sizeof(DCAMCAP_TRANSFERINFO)
        self.iKind = 0
        self.nNewestFrameIndex = -1
        self.nFrameCount = 0

property_dict = {
    'exposure_time': 2031888, # 0x001F0110, R/W, sec, "EXPOSURE TIME"
    'sensor_mode': 4194832, # 0x00400210, R/W, mode,  "SENSOR MODE"
    'defect_correct_mode': 4653072, # 0x00470010, R/W, mode,  "DEFECT CORRECT MODE"
    'binning': 4198672, # 0x00401110, R/W, mode, "BINNING"
    'readout_speed': 4194576,  # 0x00400110, R/W, long,    "READOUT SPEED"
    'trigger_active': 1048864,  # 0x00100120, R/W, mode,   "TRIGGER ACTIVE"
    'trigger_mode': 1049104,  # 0x00100210, R/W, mode,    "TRIGGER MODE"
    'trigger_polarity': 1049120, # 0x00100220, R/W, mode, "TRIGGER POLARITY"
    'trigger_source': 1048848,  # 0x00100110, R/W, mode,   "TRIGGER SOURCE"
    'internal_line_interval': 4208720,  # 0x00403850, R/W, sec,    "INTERNAL LINE INTERVAL"
    'image_width': 4325904,  # 0x00420210, R/O, long, "IMAGE WIDTH"
    'image_height': 4325920  # 0x00420220, R/O, long,    "IMAGE HEIGHT"
}


# ==== api function references ====
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


class DCAM:
    def __init__(self, index=0):
        self.__hdcam = 0
        self.__hdcamwait = 0
        # open camera
        self.dev_open(index)
        self.__open_hdcamwait()

    def __result(self, errvalue):
        """
        Internal use. Keep last error code
        """
        if errvalue < 0:
            self.__lasterr = errvalue
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
            return self.__result(DCAMERR.ALREADYOPENED)  # instance is already opened. New Error.

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

        self.__hdcam = paramopen.hdcam
        return True

    def dev_close(self):
        """
        Close dcam handle.
        Call this if you need to close the current device.

        Returns:
            True:
        """
        if self.__hdcam:
            self.__close_hdcamwait()
            dcamdev_close(self.__hdcam)
            self.__hdcam = 0

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
        if not self.__hdcam:
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
        if not self.__hdcam:
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
        if not self.__hdcam:
            return self.__result(DCAMERR.INVALIDHANDLE)  # instance is not opened yet.

        cDouble = c_double(fValue)
        cOption = c_int32(option)
        ret = self.__result(dcamprop_setgetvalue(self.__hdcam, idprop, byref(cDouble), cOption))
        if ret is False:
            return False

        return cDouble.value

    def set_property_value(self, name, value):
        """
        # this function will set property value according to property name
        """
        if name not in property_dict:
            print('could not set value for', name, 'please make sure the property name is correct and is added to property_dict!')
            return False
        # get property code
        idprop = property_dict[name]

        # Set value and get what is set
        final_configuration = self.prop_setgetvalue(idprop, value)
        
        if final_configuration == value:
            return True
        else:
            print(name, "Configuration Failed")
            return False

    def start_acquisition(self, data_buffer, number_of_frames=100):
        """
        # this function will initialize parameters, attach buffer, start capture
        """
        # initialize buffer index
        self.pre_index = -1
        self.number_of_frames = number_of_frames

        # prepare buffer pointer array
        self.data_buffer = data_buffer
        ptr_array= c_void_p * number_of_frames
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
            # start capture
            return self.__result(dcamcap_start(self.__hdcam, DCAMCAP_START_SEQUENCE))
        return False
        

    def stop_acquisition(self):
        """
        # this function will stop capture and detach buffer
        """
        # stop capture
        dcamcap_stop(self.__hdcam)
        # abort any waiting event
        dcamwait_abort(self.__hdcamwait)
        # detach buffer
        return self.__result(dcamcap_stop(self.__hdcam, DCAMBUF_ATTACHKIND_FRAME))

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
        # need to test with camera device
        # solution 1: wait for a new frame, then call dcamcap_transferinfo()
        # solution 2: get status; if busy, wait for a new frame; call dcamcap_transferinfo()
        frame_idx_list = []
        wait_param = DCAMWAIT_START()
        wait_param.eventmask = DCAMWAIT_CAPEVENT_FRAMEREADY | DCAMWAIT_CAPEVENT_STOPPED
        wait_param.timeout = 100 # 100ms
        if self.__result(dcamwait_start(self.__hdcamwait, POINTER(wait_param))):
            cap_info = DCAMCAP_TRANSFERINFO()
            dcamcap_transferinfo(self.__hdcam, POINTER(cap_info))
            #TODO: assume the index is from 0, but need to test on the camera device
            if cap_info.nFrameCount <= cap_info.nNewestFrameIndex + 1:
                frame_idx_list = list(range(cap_info.nNewestFrameIndex - cap_info.nFrameCount + 1, cap_info.nNewestFrameIndex + 1))
            else:
                frame_idx_list = list(range(self.number_of_frames - cap_info.nFrameCount + cap_info.nNewestFrameIndex + 1, self.number_of_frames)) + list(range(0, cap_info.nNewestFrameIndex + 1))

            # check if backlog happens
            if (self.pre_index+1)%self.number_of_frames != frame_idx_list[0]:
                print('backlog happens!')
            self.pre_index = cap_info.nNewestFrameIndex

        return frame_idx_list

if __name__ == '__main__':
    print('start testing Hamamatsu API!')

    number_of_frames = 1000
    # create shared memory buffer
    from model.concurrency.concurrency_tools import SharedNDArray

    data_buffer = [SharedNDArray(shape=(2048, 2048), dtype='uint16') for i in range(number_of_frames)]

    # start camera
    camera = DCAM(0)
    # initialize camera
    configuration = {
        'x_pixels': 2048,
        'y_pixels': 2048,
        'sensor_mode': 12,  # 12 for progressive
        'defect_correct_mode': 2,
        'binning': '1x1',
        'readout_speed': 1,
        'trigger_active': 1,
        'trigger_mode': 1, # external light-sheet mode
        'trigger_polarity': 2, # positive pulse
        'trigger_source': 3,  # software
        'exposure_time': 0.02,
        'line_interval': 0.000075
    }
    camera.prop_setgetvalue("sensor_mode", configuration['sensor_mode'])
    camera.prop_setgetvalue("defect_correct_mode", configuration['defect_correct_mode'])
    camera.prop_setgetvalue("exposure_time", configuration['exposure_time'])
    camera.prop_setgetvalue("binning", int(configuration['binning'][0]))
    camera.prop_setgetvalue("readout_speed", configuration['readout_speed'])
    camera.prop_setgetvalue("trigger_active", configuration['trigger_active'])
    camera.prop_setgetvalue("trigger_mode", configuration['trigger_mode'])
    camera.prop_setgetvalue("trigger_polarity", configuration['trigger_polarity'])
    camera.prop_setgetvalue("trigger_source", configuration['trigger_source'])
    camera.prop_setgetvalue("internal_line_interval", configuration['line_interval'])
    camera.prop_setgetvalue("image_height", configuration['y_pixels'])
    camera.prop_setgetvalue("image_width", configuration['x_pixels'])
    # start Acquisition
    camera.start_acquisition(data_buffer, number_of_frames)
    # start data process
    def data_func():
        while True:
            frames = camera.get_frames()
            if not frames:
                break
            print('get image frame:', frames)

    import threading
    import time
    data_process = threading.Thread(target=data_func)
    data_process.start()

    # set camera that trigger from software
    TRIGGERSOURCE_SOFTWARE = 3
    if camera.prop_setgetvalue('trigger_source', TRIGGERSOURCE_SOFTWARE):

        # fire trigger to camera
        for i in range(2000):
            err = dcamcap_firetrigger(camera.__hdcam, 0)
            if err < 0:
                print('an error happened when sending trigger to the camera', err)
                break
            time.sleep(configuration['exposure_time'] + 0.005)
    # end acquisition
    camera.stop_acquisition()
    data_process.join()
