# -*- coding: utf-8 -*-
"""
    This file refers to `ZhuangLab <https://github.com/ZhuangLab/storm-control>`, 'dcamapi4.py' and 'dcam.py'
    This is a simplified version.

    Constants can be found at 'dcamsdk4/inc/dcamapi4.h' and 'dcamsdk4/inc/dcamprop.h'
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
DCAMPROP_MODE__OFF = 1 # OFF
DCAMPROP_MODE__ON = 2  # ON

class DCAMDEV_OPEN(Structure):
    _pack_ = 8
    _fields_ = [
        ('size', c_int32),
        ('index', c_int32),
        ('hdcam', c_void_p)  # out
    ]

    def __init__(self):
        self.size = sizeof(DCAMDEV_OPEN)
        self.index = 0

class DCAMAPI_INIT(Structure):
    _pack_ = 8
    _fields_ = [
        ('size', c_int32),
        ('iDeviceCount', c_int32),  # out
        ('reserved', c_int32),
        ('initoptionbytes', c_int32),
        ('initoption', POINTER(c_int32)),
        ('guid', c_void_p)  # const DCAM_GUID*
    ]

    def __init__(self):
        self.size = sizeof(DCAMAPI_INIT)

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
    NOTSUPPORT = -2147479805  # 0x80000f03, camera does not support the function or property with current settings
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
    _fields_ = [
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

class DCAMDATA_HDR(Structure):
    _pack_ = 8
    _fields_ = [
        ('size', c_int32),
        ('iKind', c_int32),
        ('option', c_int32),
        ('reserved2', c_int32)
    ]
    def __init__(self):
        self.iKind = 0
        self.option = 0
        self.reserved2 = 0

class DCAMDATA_REGIONRECT(Structure):
    _pack_ = 8
    _fields_ = [
        ('left', c_short),
        ('top', c_short),
        ('right', c_short),
        ('bottom', c_short)
    ]

class DCAMDATA_REGION(Structure):
    _pack_ = 8
    _fields_ = [
        ('hdr', POINTER(DCAMDATA_HDR)),
        ('option', c_int32),
        ('type', c_int32),
        ('data', c_void_p),
        ('datasize', c_int32),
        ('reserved', c_int32)
    ]

property_dict = {
    'exposure_time': 2031888, # 0x001F0110, R/W, sec, "EXPOSURE TIME"
    'sensor_mode': 4194832, # 0x00400210, R/W, mode,  "SENSOR MODE"
    'defect_correct_mode': 4653072, # 0x00470010, R/W, mode,  "DEFECT CORRECT MODE"
    'binning': 4198672, # 0x00401110, R/W, mode, "BINNING"
    'readout_speed': 4194576,  # 0x00400110, R/W, long,    "READOUT SPEED"
    'trigger_active': 1048864,  # 0x00100120, R/W, mode,   "TRIGGER ACTIVE"
    'trigger_mode': 1049104,  # 0x00100210, R/W, mode,    "TRIGGER MODE"
    'trigger_polarity': 1049120,  # 0x00100220, R/W, mode, "TRIGGER POLARITY"
    'trigger_source': 1048848,  # 0x00100110, R/W, mode,   "TRIGGER SOURCE"
    'internal_line_interval': 4208720,  # 0x00403850, R/W, sec,    "INTERNAL LINE INTERVAL"
    'image_width': 4325904,  # 0x00420210, R/O, long, "IMAGE WIDTH"
    'image_height': 4325920,  # 0x00420220, R/O, long,    "IMAGE HEIGHT"
    'exposuretime_control': 2031920,  # 0x001F0130, R/W, mode,    "EXPOSURE TIME CONTROL"
    'subarray_hpos': 4202768,  # 0x00402110, R/W, long,    "SUBARRAY HPOS"
    'subarray_hsize': 4202784,  # 0x00402120, R/W, long,   "SUBARRAY HSIZE"
    'subarray_vpos': 4202800,  # 0x00402130, R/W, long,    "SUBARRAY VPOS"
    'subarray_vsize': 4202816,  # 0x00402140, R/W, long,   "SUBARRAY VSIZE"
    'subarray_mode': 4202832  # 0x00402150, R/W, mode,    "SUBARRAY MODE"
}


# ==== api function references ====
dcamapi_init = __dll.dcamapi_init
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
dcamdev_setdata = __dll.dcamdev_setdata


class DCAM:
    def __init__(self, index=0):
        self.__hdcam = 0
        self.__hdcamwait = 0
        
        # initialize api
        paraminit = DCAMAPI_INIT()
        dcamapi_init(byref(paraminit))
        
        # open camera
        self.dev_open(index)
        self.__open_hdcamwait()

        # TODO: get maximum supported image width and height
        self.max_image_width = 2048
        self.max_image_height = 2048

    def __result(self, errvalue):
        """
        Internal use. Keep last error code
        """
        if errvalue < 0:
            try:
                print('error message: ', DCAMERR(errvalue))
            except:
                print('error message: ', errvalue)
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

        self.__hdcam = c_void_p(paramopen.hdcam)
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
        print("prop_getvalue response:", cDouble.value)
        print("property id:", idprop)
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
        ret = self.__result(dcamprop_setgetvalue(self.__hdcam, idprop, byref(cDouble), cOption))
        if ret is False:
            return False

        return cDouble.value

    def set_property_value(self, name, value):
        """
        # this function will set property value according to property name
        """
        if name not in property_dict:
            print('could not set value for', name,
                  'please make sure the property name is correct and is added to property_dict!')
            return False

        # get property code
        idprop = property_dict[name]

        # Set value and get what is set
        final_configuration = self.prop_setgetvalue(idprop, value)
        
        if final_configuration >= value - value/100 and final_configuration <= value + value/100:
            return True
        else:
            print(name, "Configuration Failed", value, final_configuration)
            return False

    def get_property_value(self, name):
        return self.prop_getvalue(property_dict[name])

    def set_ROI(self, left, top, right, bottom):
        """
        # this function set 'subarray' properties.
        """
        # TODO: parameter verification

        # test if hsize and vsize equal to maximum image width and height
        # if the same, set subarray_mode to DCAMPROP_MODE__OFF
        if right-left == self.max_image_width and bottom-top == self.max_image_height:
            self.prop_setgetvalue(property_dict['subarray_mode'], DCAMPROP_MODE__OFF)
            return (self.max_image_width, self.max_image_height)
        
        width = self.prop_getvalue(property_dict['image_width'])
        height = self.prop_getvalue(property_dict['image_height'])
        if right-left == width and bottom-top == height:
            self.prop_setvalue(property_dict['subarray_hpos'], left)
            self.prop_setvalue(property_dict['subarray_vpos'], top)
        else:
            # set DCAM_IDPROP_SUBARRAYMODE to 'OFF'
            if self.prop_setgetvalue(property_dict['subarray_mode'], DCAMPROP_MODE__OFF):
                # set hpos, hsize, vpos, vsize
                self.prop_setvalue(property_dict['subarray_hpos'], left)
                self.prop_setvalue(property_dict['subarray_hsize'], right-left)
                self.prop_setvalue(property_dict['subarray_vpos'], top)
                self.prop_setvalue(property_dict['subarray_vsize'], bottom-top)
        
        # set DCAM_IDPROP_SUBARRAYMODE to 'ON'
        self.prop_setgetvalue(property_dict['subarray_mode'], DCAMPROP_MODE__ON)
        # TODO:return new image width and height
        # will changing hsize and vsize affect iamge width and height?
        # not sure, need to test
        return (self.prop_getvalue(property_dict['image_width']), self.prop_getvalue(property_dict['image_height']))

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
            return self.__result(dcamcap_start(self.__hdcam, DCAMCAP_START_SEQUENCE))
        return False
        

    def stop_acquisition(self):
        """
        # this function will stop capture and detach buffer
        """
        # stop capture
        dcamcap_stop(self.__hdcam)

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
            print("Frame Count - cap_info", cap_info.nFrameCount, frame_count)
            print("Newest Frame Index - cap_info", cap_info.nNewestFrameIndex)
            
            if frame_count <= cap_info.nNewestFrameIndex + 1:
                frame_idx_list = list(range(cap_info.nNewestFrameIndex - frame_count + 1,
                                            cap_info.nNewestFrameIndex + 1))
            else:
                frame_idx_list = list(range(self.number_of_frames - frame_count + cap_info.nNewestFrameIndex +
                                            1, self.number_of_frames)) + list(range(0, cap_info.nNewestFrameIndex + 1))
            
            print("frame_idx_list:", frame_idx_list)
            # check if backlog happens
            # if (self.pre_index+1) % self.number_of_frames != frame_idx_list[0]:
            #    print('backlog happens!')
            self.pre_index = cap_info.nNewestFrameIndex
            self.pre_frame_count = cap_info.nFrameCount

        return frame_idx_list

    def get_camera_handler(self):
        return self.__hdcam


if __name__ == '__main__':

    print('start testing Hamamatsu API!')

    number_of_frames = 20
    # create shared memory buffer
    import sys
    sys.path.append('../../../../concurrency')
    from concurrency_tools import SharedNDArray

    data_buffer = [SharedNDArray(shape=(2048, 2048), dtype='uint16') for i in range(number_of_frames)]

    # start camera
    camera = DCAM(0)

    # initialize camera
    configuration = {
        'image_width': 2048.0,
        'image_height': 2048.0,
        'sensor_mode': 12.0,  # 12 for progressive
        'defect_correct_mode': 2.0,
        'binning': 1.0,
        'readout_speed': 1.0,
        'trigger_active': 1.0,
        'trigger_mode': 1.0,  # external light-sheet mode
        'trigger_polarity': 2.0,  # positive pulse
        'trigger_source': 3.0,  # software
        'exposure_time': 0.02,
        'internal_line_interval': 0.000075
    }
    camera.prop_getvalue(property_dict['exposuretime_control'])

    # configure camera
    for key in configuration:
        # INVALIDVALUE = -2147481567  # 0x80000821, invalid property value
        # INVALIDPROPERTYID = -2147481563  # 0x80000825, the property id is invalid
        print("property:", property_dict[key], " key:", key)
        camera.prop_setvalue(property_dict[key], configuration[key])

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

    def test_acquisition():
        data_process = threading.Thread(target=data_func)
        data_process.start()

        # set camera that trigger from software
        TRIGGERSOURCE_SOFTWARE = 3
        if camera.prop_setgetvalue(property_dict['trigger_source'], TRIGGERSOURCE_SOFTWARE):

            # fire trigger to camera
            for i in range(10):
                err = dcamcap_firetrigger(camera.get_camera_handler(), 0)
                if err < 0:
                    print('an error happened when sending trigger to the camera', err)
                    break
                time.sleep(configuration['exposure_time'] + 0.005)
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
            print('time cost to attach a buffer(', number_of_frames, '):', end_time - start_time )

    # test ROI setting
    def test_ROI(left, top, right, bottom):
        width, height = camera.set_ROI(left, top, right, bottom)
        print('width, height:', width, height, right-left, bottom-top)
        assert(camera.prop_getvalue(property_dict['subarray_hpos']) == left)
        assert(camera.prop_getvalue(property_dict['subarray_hsize']) == right-left)
        assert(camera.prop_getvalue(property_dict['subarray_vpos']) == top)
        assert(camera.prop_getvalue(property_dict['subarray_vsize']) == bottom-top)
        print('sub array mode(1: OFF, 2: ON): ', camera.prop_getvalue(property_dict['subarray_mode']))

    test_ROI(0, 0, 2048, 2048)
    test_ROI(0, 0, 1024, 1024)
    test_ROI(100, 100, 1124, 1124)
    test_ROI(100, 200, 1124, 1224)
    test_ROI(100, 200, 1000, 1000)
    test_ROI(100, 100, 1124, 1124)
    test_ROI(0, 0, 1024, 1024)
    test_ROI(0, 0, 2048, 2048)
    