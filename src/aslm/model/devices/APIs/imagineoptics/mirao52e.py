#from Priithon.all import F, N
import numpy as N
import ctypes as C

basepath = 'C:\\Users\\LouisXIV\\Documents\\Python\\Git\\ASLM\\src\\aslm\\model\\devices\\APIs\\imagineoptics'

import os,sys,time

# try:
#     sys.path.index(basepath)
# except:
#     sys.path.append(basepath)

#m52e = C.windll.mirao52e

m52e = C.WinDLL(os.path.join(basepath, 'mirao52e.dll'))

class DM(object):
    def __init__(self):
        self.cmd = N.zeros(52)
        self.flat_file = 'FLAT_MIRAO_0126_01.mro'

    def __del__(self):
        pass

    def getDLLVersion(self):
        version = C.create_string_buffer(1024)
        status = C.c_int(-1)
        m52e.mro_getVersion(version,C.byref(status))
        print(version.value)
        return status.value

    def open(self):
        print("Initializing DM")
        status = C.c_int(-1)
        m52e.mro_open(C.byref(status))
        if (status.value != 0):
            raise ValueError(self.err_key(status.value))
        return status.value

    def close(self):
        print("Shutting down DM")
        status = C.c_int(-1)
        m52e.mro_close(C.byref(status))
        return status.value

    def set_monitor(self):
        en = C.c_int(1)
        status = C.c_int(-1)
        m52e.mro_setMonitoringEnabled(en,C.byref(status))
        return status.value

    def get_ps_temp(self):
        status = C.c_int(-1)
        temp = C.c_double(0)
        m52e.mro_getPowerSupplyTemperature(C.byref(temp),C.byref(status))
        print(temp.value)
        return status.value

    def set_mirror(self,cmd,smooth=True,trig=False):
        status = C.c_int(-1)
        if trig:
            settrig = C.c_int(1)
        else:
            settrig = C.c_int(0)
        if (abs(cmd).max()>0.5):
            raise ValueError('DM voltage out of bound (>0.5)')
        if smooth:
            m52e.mro_applySmoothCommand(cmd.ctypes.data_as(C.POINTER(C.c_double)),
                                        settrig,
                                        C.byref(status))
        else:
            m52e.mro_applyCommand(cmd.ctypes.data_as(C.POINTER(C.c_double)),
                                        settrig,
                                        C.byref(status))
        if (status.value==0):
            self.cmd = cmd
        return status.value
        
    def get_last_mirror_cmd(self):
        ''' gets last command array sent to DM '''
        status = C.c_int(-1)
        cmd_ret = N.zeros(52)
        m52e.mro_getLastAppliedCommand(cmd_ret.ctypes.data_as(C.POINTER(C.c_double)),
                                       C.byref(status))
        return (cmd_ret,status.value)            

    def read_command_file(self,filename):
        ''' read a file with the mro extension '''
        cmd_name = C.create_string_buffer(filename)
        cmd_arr = N.zeros(52) # default type is float64 (double)
        status = C.c_int(-1)
        m52e.mro_readCommandFile(cmd_name,cmd_arr.ctypes.data_as(C.POINTER(C.c_double)),
                                   C.byref(status))
        self.cmd = cmd_arr
        return (cmd_arr,status.value)

    def write_command_file(self,filename,cmd,overwrite=1):
        cmd_name = C.create_string_buffer(filename)
        status = C.c_int(-1)
        m52e.mro_writeCommandFile(cmd.ctypes.data_as(C.POINTER(C.c_double)),
                                    cmd_name,C.c_int(overwrite),C.byref(status))
        return status.value

    def err_key(self,status):
        err_dict = {0:"MRO_OK",1:"MRO_UNKNOWN_ERROR",
                    2:"MRO_DEVICE_NOT_OPENED_ERROR",
                    3:"MRO_DEFECTIVE_DEVICE_ERROR",
                    4:"MRO_DEVICE_ALREADY_OPENED_ERROR",
                    5:"MRO_DEVICE_IO_ERROR",
                    6:"MRO_DEVICE_LOCKED_ERROR",
                    7:"MRO_DEVICE_DISCONNECTED_ERROR",
                    8:"MRO_DEVICE_DRIVER_ERROR",
                    9:"MRO_FILE_EXISTS_ERROR",
                    10:"MRO_FILE_FORMAT_ERROR",
                    11:"MRO_FILE_IO_ERROR",
                    12:"MRO_INVALID_COMMAND_ERROR",
                    13:"MRO_NULL_POINTER_ERROR",
                    14:"MRO_OUT_OF_BOUNDS_ERROR",
                    15:"MRO_OPERATION_ONGOING_ERROR",
                    16:"MRO_SYSTEM_ERROR",
                    17:"MRO_UNAVAILABLE_DATA_ERROR",
                    18:"MRO_UNDEFINED_VALUE_ERROR",
                    19:"MRO_OUT_OF_SPECIFICATIONS_ERROR",
                    20:"MRO_FILE_FORMAT_VERSION_ERROR",
                   21:"MRO_USB_INVALID_HANDLE",
                    22:"MRO_USB_DEVICE_NOT_FOUND",
                    23:"MRO_USB_DEVICE_NOT_OPENED",
                    24:"MRO_USB_IO_ERROR",
                    25:"MRO_USB_INSUFFICIENT_RESOURCES",
                    26:"MRO_USB_INVALID_BAUD_RATE",
                    27:"MRO_USB_NOT_SUPPORTED",
                    28:"MRO_FILE_IO_EACCES",
                    29:"MRO_FILE_IO_EAGAIN",
                    30:"MRO_FILE_IO_EBADF",
                    31:"MRO_FILE_IO_EINVAL",
                    32:"MRO_FILE_IO_EMFILE",
                    33:"MRO_FILE_IO_ENOENT",
                    34:"MRO_FILE_IO_ENOMEM",
                    35:"MRO_FILE_IO_ENOSPC"}
        return err_dict.get(status)
