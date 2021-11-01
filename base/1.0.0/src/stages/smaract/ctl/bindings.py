#######################################################################
# Copyright (c) 2020 SmarAct GmbH
#
# THIS  SOFTWARE, DOCUMENTS, FILES AND INFORMATION ARE PROVIDED 'AS IS'
# WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING,
# BUT  NOT  LIMITED  TO, THE  IMPLIED  WARRANTIES  OF MERCHANTABILITY,
# FITNESS FOR A PURPOSE, OR THE WARRANTY OF NON - INFRINGEMENT.
# THE  ENTIRE  RISK  ARISING OUT OF USE OR PERFORMANCE OF THIS SOFTWARE
# REMAINS WITH YOU.
# IN  NO  EVENT  SHALL  THE  SMARACT  GMBH  BE  LIABLE  FOR ANY DIRECT,
# INDIRECT, SPECIAL, INCIDENTAL, CONSEQUENTIAL OR OTHER DAMAGES ARISING
# OUT OF THE USE OR INABILITY TO USE THIS SOFTWARE.
#
# Generated on 2020-06-03 10:20 +0200
#

"""
Python bindings for SmarActCTL
(C) SmarAct GmbH
Refer to the SmarAct EULA for licensing
SmarActCTL Python API
"""

from cffi import FFI
import enum
import sys
assert sys.version_info >= (3, 4), "Python v3.4 or higher is required"
apigen_version = (1, 3, 5)
api_version = (1, 3, 13)
def __initBindings(libName):
    global ffi, lib
    ffi = FFI()
    ffi.cdef("""
typedef unsigned char uint8_t;
typedef unsigned int uint32_t;
typedef uint32_t SA_CTL_StreamHandle_t;
typedef uint32_t SA_CTL_TransmitHandle_t;
typedef long long int64_t;
typedef int int32_t;
typedef unsigned long long size_t;
typedef uint32_t SA_CTL_DeviceHandle_t;
typedef uint32_t SA_CTL_Result_t;
typedef struct { uint32_t idx; uint32_t type; union { int32_t i32; int64_t i64; uint8_t unused[24];};}SA_CTL_Event_t;
typedef signed char int8_t;
typedef uint8_t SA_CTL_RequestID_t;
typedef uint32_t SA_CTL_PropertyKey_t;
char const *SA_CTL_GetFullVersionString();
char const *SA_CTL_GetResultInfo(SA_CTL_Result_t result);
char const *SA_CTL_GetEventInfo(SA_CTL_Event_t const *event);
SA_CTL_Result_t SA_CTL_Open(SA_CTL_DeviceHandle_t *dHandle, char const *locator, char const *config);
SA_CTL_Result_t SA_CTL_Close(SA_CTL_DeviceHandle_t dHandle);
SA_CTL_Result_t SA_CTL_Cancel(SA_CTL_DeviceHandle_t dHandle);
SA_CTL_Result_t SA_CTL_FindDevices(char const *options, char *deviceList, size_t *deviceListLen);
SA_CTL_Result_t SA_CTL_GetProperty_i32(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_PropertyKey_t pkey, int32_t *value, size_t *ioArraySize);
SA_CTL_Result_t SA_CTL_SetProperty_i32(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_PropertyKey_t pkey, int32_t value);
SA_CTL_Result_t SA_CTL_SetPropertyArray_i32(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_PropertyKey_t pkey, int32_t const *values, size_t arraySize);
SA_CTL_Result_t SA_CTL_GetProperty_i64(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_PropertyKey_t pkey, int64_t *value, size_t *ioArraySize);
SA_CTL_Result_t SA_CTL_SetProperty_i64(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_PropertyKey_t pkey, int64_t value);
SA_CTL_Result_t SA_CTL_SetPropertyArray_i64(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_PropertyKey_t pkey, int64_t const *values, size_t arraySize);
SA_CTL_Result_t SA_CTL_GetProperty_s(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_PropertyKey_t pkey, char *value, size_t *ioArraySize);
SA_CTL_Result_t SA_CTL_SetProperty_s(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_PropertyKey_t pkey, char const *value);
SA_CTL_Result_t SA_CTL_RequestReadProperty(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_PropertyKey_t pkey, SA_CTL_RequestID_t *rID, SA_CTL_TransmitHandle_t tHandle);
SA_CTL_Result_t SA_CTL_ReadProperty_i32(SA_CTL_DeviceHandle_t dHandle, SA_CTL_RequestID_t rID, int32_t *value, size_t *ioArraySize);
SA_CTL_Result_t SA_CTL_ReadProperty_i64(SA_CTL_DeviceHandle_t dHandle, SA_CTL_RequestID_t rID, int64_t *value, size_t *ioArraySize);
SA_CTL_Result_t SA_CTL_ReadProperty_s(SA_CTL_DeviceHandle_t dHandle, SA_CTL_RequestID_t rID, char *value, size_t *ioArraySize);
SA_CTL_Result_t SA_CTL_RequestWriteProperty_i32(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_PropertyKey_t pkey, int32_t value, SA_CTL_RequestID_t *rID, SA_CTL_TransmitHandle_t tHandle);
SA_CTL_Result_t SA_CTL_RequestWriteProperty_i64(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_PropertyKey_t pkey, int64_t value, SA_CTL_RequestID_t *rID, SA_CTL_TransmitHandle_t tHandle);
SA_CTL_Result_t SA_CTL_RequestWriteProperty_s(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_PropertyKey_t pkey, char const *value, SA_CTL_RequestID_t *rID, SA_CTL_TransmitHandle_t tHandle);
SA_CTL_Result_t SA_CTL_RequestWritePropertyArray_i32(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_PropertyKey_t pkey, int32_t const *values, size_t arraySize, SA_CTL_RequestID_t *rID, SA_CTL_TransmitHandle_t tHandle);
SA_CTL_Result_t SA_CTL_RequestWritePropertyArray_i64(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_PropertyKey_t pkey, int64_t const *values, size_t arraySize, SA_CTL_RequestID_t *rID, SA_CTL_TransmitHandle_t tHandle);
SA_CTL_Result_t SA_CTL_WaitForWrite(SA_CTL_DeviceHandle_t dHandle, SA_CTL_RequestID_t rID);
SA_CTL_Result_t SA_CTL_CancelRequest(SA_CTL_DeviceHandle_t dHandle, SA_CTL_RequestID_t rID);
SA_CTL_Result_t SA_CTL_CreateOutputBuffer(SA_CTL_DeviceHandle_t dHandle, SA_CTL_TransmitHandle_t *tHandle);
SA_CTL_Result_t SA_CTL_FlushOutputBuffer(SA_CTL_DeviceHandle_t dHandle, SA_CTL_TransmitHandle_t tHandle);
SA_CTL_Result_t SA_CTL_CancelOutputBuffer(SA_CTL_DeviceHandle_t dHandle, SA_CTL_TransmitHandle_t tHandle);
SA_CTL_Result_t SA_CTL_OpenCommandGroup(SA_CTL_DeviceHandle_t dHandle, SA_CTL_TransmitHandle_t *tHandle, uint32_t triggerMode);
SA_CTL_Result_t SA_CTL_CloseCommandGroup(SA_CTL_DeviceHandle_t dHandle, SA_CTL_TransmitHandle_t tHandle);
SA_CTL_Result_t SA_CTL_CancelCommandGroup(SA_CTL_DeviceHandle_t dHandle, SA_CTL_TransmitHandle_t tHandle);
SA_CTL_Result_t SA_CTL_WaitForEvent(SA_CTL_DeviceHandle_t dHandle, SA_CTL_Event_t *event, uint32_t timeout);
SA_CTL_Result_t SA_CTL_Calibrate(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_TransmitHandle_t tHandle);
SA_CTL_Result_t SA_CTL_Reference(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_TransmitHandle_t tHandle);
SA_CTL_Result_t SA_CTL_Move(SA_CTL_DeviceHandle_t dHandle, int8_t idx, int64_t moveValue, SA_CTL_TransmitHandle_t tHandle);
SA_CTL_Result_t SA_CTL_Stop(SA_CTL_DeviceHandle_t dHandle, int8_t idx, SA_CTL_TransmitHandle_t tHandle);
SA_CTL_Result_t SA_CTL_OpenStream(SA_CTL_DeviceHandle_t dHandle, SA_CTL_StreamHandle_t *sHandle, uint32_t triggerMode);
SA_CTL_Result_t SA_CTL_StreamFrame(SA_CTL_DeviceHandle_t dHandle, SA_CTL_StreamHandle_t sHandle, uint8_t const *frameData, uint32_t frameSize);
SA_CTL_Result_t SA_CTL_CloseStream(SA_CTL_DeviceHandle_t dHandle, SA_CTL_StreamHandle_t sHandle);
SA_CTL_Result_t SA_CTL_AbortStream(SA_CTL_DeviceHandle_t dHandle, SA_CTL_StreamHandle_t sHandle);
""")
    lib = ffi.dlopen(libName)

class Error(Exception):
    def __init__(self, func, code, arguments):
        self.func = func
        self.code = code
        self.arguments = arguments
    def __str__(self):
        return "{} returned {} with arguments {}".format(self.func, self.code, self.arguments)
class Event_t:
    def __init__(self, inst):
        self.inst = inst
    def asFFI(self):
        return self.inst
    def __getattr__(self, attr):
        return getattr(self.inst, attr)
def GetFullVersionString():
    """
    Returns the version of the library as a human readable string
    """
    local_0 = lib.SA_CTL_GetFullVersionString()
    return ffi.string(local_0).decode()
def GetResultInfo(result):
    """
    Returns a human readable string for the given result code

    Parameters:
     - result: Resultcode to get the description for
    """
    local_0 = lib.SA_CTL_GetResultInfo(result)
    return ffi.string(local_0).decode()
def GetEventInfo(event):
    """
    Returns a human readable info string for the given event

    Parameters:
     - event: Event to get the description for
    """
    local_0 = event.asFFI()
    local_1 = lib.SA_CTL_GetEventInfo(local_0)
    return ffi.string(local_1).decode()
def Open(locator, config = ""):
    """
    Opens a connection to a device specified by a locator string
    
    Parameters:
     - locator: Specifies the device
     - config = "": Configuration options for the initialization
    
    Return value(s):
     - dHandle: Handle to the device. Must be passed to following function
    calls.
    """
    local_0 = ffi.new("SA_CTL_DeviceHandle_t *")
    local_1 = lib.SA_CTL_Open(local_0, locator.encode(), config.encode())
    if local_1 != ErrorCode.NONE.value:
        raise Error("Open", local_1, {"locator": locator, "config": config})
    return local_0[0]
def Close(dHandle):
    """
    Closes a previously established connection to a device

    Parameters:
     - dHandle: Handle to the device
    """
    local_0 = lib.SA_CTL_Close(dHandle)
    if local_0 != ErrorCode.NONE.value:
        raise Error("Close", local_0, {"dHandle": dHandle})
    return 
def Cancel(dHandle):
    """
    Aborts all blocking functions
    
    Parameters:
     - dHandle: Handle to the device
    """
    local_0 = lib.SA_CTL_Cancel(dHandle)
    if local_0 != ErrorCode.NONE.value:
        raise Error("Cancel", local_0, {"dHandle": dHandle})
    return 
def FindDevices(options = "", deviceListLen = 1024):
    """
    Returns a list of locator strings of available devices
    
    Parameters:
     - options = "": Options for the find procedure
     - deviceListLen = 1024: Length of the buffer to allocate
    
    Return value(s):
     - deviceList: Buffer for device locators
    """
    local_0 = ffi.new("char []", deviceListLen)
    local_1 = ffi.new("size_t *", deviceListLen)
    local_2 = lib.SA_CTL_FindDevices(options.encode(), local_0, local_1)
    if local_2 != ErrorCode.NONE.value:
        raise Error("FindDevices", local_2, {"options": options})
    return ffi.string(local_0, local_1[0]).decode()
def GetProperty_i32(dHandle, idx, pkey, ioArraySize = None):
    """
    Directly returns the value of a 32-bit integer (array) property
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the addressed device, module or channel
     - pkey: Key that identifies the property
     - ioArraySize: Size of the buffer for values
    
    Return value(s):
     - value: Buffer for the read values
    """
    if ioArraySize == None:
        local_0 = ffi.new("int32_t *")
        local_1 = ffi.NULL
    else:
        local_0 = ffi.new("int32_t []", ioArraySize)
        local_1 = ffi.new("size_t *", ioArraySize)
    local_2 = lib.SA_CTL_GetProperty_i32(dHandle, idx, pkey, local_0, local_1)
    if local_2 != ErrorCode.NONE.value:
        raise Error("GetProperty_i32", local_2, {"dHandle": dHandle, "idx": idx, "pkey": pkey})
    return ffi.unpack(local_0, local_1[0]) if ioArraySize != None else local_0[0]
def SetProperty_i32(dHandle, idx, pkey, value):
    """
    Directly sets the value of a 32-bit integer property
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the addressed device, module or channel
     - pkey: Key that identifies the property
     - value: Value that should be written
    """
    local_0 = lib.SA_CTL_SetProperty_i32(dHandle, idx, pkey, value)
    if local_0 != ErrorCode.NONE.value:
        raise Error("SetProperty_i32", local_0, {"dHandle": dHandle, "idx": idx, "pkey": pkey, "value": value})
    return 
def SetPropertyArray_i32(dHandle, idx, pkey, values = None):
    """
    Directly sets the value of a 32-bit integer array property
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the addressed device, module or channel
     - pkey: Key that identifies the property
     - values: Buffer containing the values to be written
    """
    if values == None:
        local_0 = ffi.NULL
    else:
        local_0 = ffi.new("int32_t const *", values)
    local_1 = len(values)
    local_2 = lib.SA_CTL_SetPropertyArray_i32(dHandle, idx, pkey, local_0, local_1)
    if local_2 != ErrorCode.NONE.value:
        raise Error("SetPropertyArray_i32", local_2, {"dHandle": dHandle, "idx": idx, "pkey": pkey, "values": values})
    return 
def GetProperty_i64(dHandle, idx, pkey, ioArraySize = None):
    """
    Directly returns the value of a 64-bit integer (array) property
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the addressed device, module or channel
     - pkey: Key that identifies the property
     - ioArraySize: Size of the buffer for values
    
    Return value(s):
     - value: Buffer for the read values
    """
    if ioArraySize == None:
        local_0 = ffi.new("int64_t *")
        local_1 = ffi.NULL
    else:
        local_0 = ffi.new("int64_t []", ioArraySize)
        local_1 = ffi.new("size_t *", ioArraySize)
    local_2 = lib.SA_CTL_GetProperty_i64(dHandle, idx, pkey, local_0, local_1)
    if local_2 != ErrorCode.NONE.value:
        raise Error("GetProperty_i64", local_2, {"dHandle": dHandle, "idx": idx, "pkey": pkey})
    return ffi.unpack(local_0, local_1[0]) if ioArraySize != None else local_0[0]
def SetProperty_i64(dHandle, idx, pkey, value):
    """
    Directly sets the value of a 64-bit integer property
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the addressed device, module or channel
     - pkey: Key that identifies the property
     - value: Value that should be written
    """
    local_0 = lib.SA_CTL_SetProperty_i64(dHandle, idx, pkey, value)
    if local_0 != ErrorCode.NONE.value:
        raise Error("SetProperty_i64", local_0, {"dHandle": dHandle, "idx": idx, "pkey": pkey, "value": value})
    return 
def SetPropertyArray_i64(dHandle, idx, pkey, values):
    """
    Directly sets the value of a 64-bit integer array property
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the addressed device, module or channel
     - pkey: Key that identifies the property
     - values: Buffer containing the values to be written
    """
    local_0 = len(values)
    local_1 = lib.SA_CTL_SetPropertyArray_i64(dHandle, idx, pkey, values, local_0)
    if local_1 != ErrorCode.NONE.value:
        raise Error("SetPropertyArray_i64", local_1, {"dHandle": dHandle, "idx": idx, "pkey": pkey, "values": values})
    return 
def GetProperty_s(dHandle, idx, pkey, ioArraySize = 64):
    """
    Directly returns the value of a string (array) property
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the addressed device, module or channel
     - pkey: Key that identifies the property
     - ioArraySize = 64: Size of the buffer for values
    
    Return value(s):
     - value: Buffer for the read values
    """
    local_0 = ffi.new("char []", ioArraySize)
    local_1 = ffi.new("size_t *", ioArraySize)
    local_2 = lib.SA_CTL_GetProperty_s(dHandle, idx, pkey, local_0, local_1)
    if local_2 != ErrorCode.NONE.value:
        raise Error("GetProperty_s", local_2, {"dHandle": dHandle, "idx": idx, "pkey": pkey})
    return ffi.string(local_0, local_1[0]).decode()
def SetProperty_s(dHandle, idx, pkey, value):
    """
    Directly sets the value of a string property
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the addressed device, module or channel
     - pkey: Key that identifies the property
     - value: Value that should be written
    """
    local_0 = lib.SA_CTL_SetProperty_s(dHandle, idx, pkey, value.encode())
    if local_0 != ErrorCode.NONE.value:
        raise Error("SetProperty_s", local_0, {"dHandle": dHandle, "idx": idx, "pkey": pkey, "value": value})
    return 
def RequestReadProperty(dHandle, idx, pkey, tHandle = 0):
    """
    Requests the value of a property (non-blocking)
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the addressed device, module or channel
     - pkey: Key that identifies the property
     - tHandle = 0: Optional handle to a transmit buffer. If unused set to
    zero.
    
    Return value(s):
     - rID: Request ID
    """
    local_0 = ffi.new("SA_CTL_RequestID_t *")
    local_1 = lib.SA_CTL_RequestReadProperty(dHandle, idx, pkey, local_0, tHandle)
    if local_1 != ErrorCode.NONE.value:
        raise Error("RequestReadProperty", local_1, {"dHandle": dHandle, "idx": idx, "pkey": pkey, "tHandle": tHandle})
    return local_0[0]
def ReadProperty_i32(dHandle, rID, ioArraySize = None):
    """
    Reads a 32-bit integer property value (array) that has previously been
    requested using RequestReadProperty
    
    Parameters:
     - dHandle: Handle to the device
     - rID: Request ID
     - ioArraySize: Size of the buffer for values
    
    Return value(s):
     - value: Buffer for the read values
    """
    if ioArraySize == None:
        local_0 = ffi.new("int32_t *")
        local_1 = ffi.NULL
    else:
        local_0 = ffi.new("int32_t []", ioArraySize)
        local_1 = ffi.new("size_t *", ioArraySize)
    local_2 = lib.SA_CTL_ReadProperty_i32(dHandle, rID, local_0, local_1)
    if local_2 != ErrorCode.NONE.value:
        raise Error("ReadProperty_i32", local_2, {"dHandle": dHandle, "rID": rID})
    return ffi.unpack(local_0, local_1[0]) if ioArraySize != None else local_0[0]
def ReadProperty_i64(dHandle, rID, ioArraySize = None):
    """
    Reads a 64-bit integer property value (array) that has previously been
    requested using RequestReadProperty
    
    Parameters:
     - dHandle: Handle to the device
     - rID: Request ID
     - ioArraySize: Size of the buffer for values
    
    Return value(s):
     - value: Buffer for the read values
    """
    if ioArraySize == None:
        local_0 = ffi.new("int64_t *")
        local_1 = ffi.NULL
    else:
        local_0 = ffi.new("int64_t []", ioArraySize)
        local_1 = ffi.new("size_t *", ioArraySize)
    local_2 = lib.SA_CTL_ReadProperty_i64(dHandle, rID, local_0, local_1)
    if local_2 != ErrorCode.NONE.value:
        raise Error("ReadProperty_i64", local_2, {"dHandle": dHandle, "rID": rID})
    return ffi.unpack(local_0, local_1[0]) if ioArraySize != None else local_0[0]
def ReadProperty_s(dHandle, rID, ioArraySize = 64):
    """
    Reads a string property value (array) that has previously been
    requested using RequestReadProperty
    
    Parameters:
     - dHandle: Handle to the device
     - rID: Request ID
     - ioArraySize = 64: Size of the buffer for values
    
    Return value(s):
     - value: Buffer for the read values
    """
    local_0 = ffi.new("char []", ioArraySize)
    local_1 = ffi.new("size_t *", ioArraySize)
    local_2 = lib.SA_CTL_ReadProperty_s(dHandle, rID, local_0, local_1)
    if local_2 != ErrorCode.NONE.value:
        raise Error("ReadProperty_s", local_2, {"dHandle": dHandle, "rID": rID})
    return ffi.string(local_0, local_1[0]).decode()
def RequestWriteProperty_i32(dHandle, idx, pkey, value, pass_rID = True, tHandle = 0):
    """
    Requests to write the value of a 32-bit integer property (non-blocking)
    
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the addressed device, module or channel
     - pkey: Key that identifies the property
     - value: Value that should be written
     - pass_rID: Whether to pass rID to the function
     - tHandle = 0: Optional handle to a transmit buffer. If unused set to
    zero.
    
    Return value(s):
     - rID: Request ID
    """
    if pass_rID:
        local_0 = ffi.new("SA_CTL_RequestID_t *")
    else:
        local_0 = ffi.NULL
    local_1 = lib.SA_CTL_RequestWriteProperty_i32(dHandle, idx, pkey, value, local_0, tHandle)
    if local_1 != ErrorCode.NONE.value:
        raise Error("RequestWriteProperty_i32", local_1, {"dHandle": dHandle, "idx": idx, "pkey": pkey, "value": value, "tHandle": tHandle})
    return local_0[0] if pass_rID else None
def RequestWriteProperty_i64(dHandle, idx, pkey, value, pass_rID = True, tHandle = 0):
    """
    Requests to write the value of a 64-bit integer property (non-blocking)
    
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the addressed device, module or channel
     - pkey: Key that identifies the property
     - value: Value that should be written
     - pass_rID: Whether to pass rID to the function
     - tHandle = 0: Optional handle to a transmit buffer. If unused set to
    zero.
    
    Return value(s):
     - rID: Request ID
    """
    if pass_rID:
        local_0 = ffi.new("SA_CTL_RequestID_t *")
    else:
        local_0 = ffi.NULL
    local_1 = lib.SA_CTL_RequestWriteProperty_i64(dHandle, idx, pkey, value, local_0, tHandle)
    if local_1 != ErrorCode.NONE.value:
        raise Error("RequestWriteProperty_i64", local_1, {"dHandle": dHandle, "idx": idx, "pkey": pkey, "value": value, "tHandle": tHandle})
    return local_0[0] if pass_rID else None
def RequestWriteProperty_s(dHandle, idx, pkey, value, pass_rID = True, tHandle = 0):
    """
    Requests to write the value of a string property (non-blocking)
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the addressed device, module or channel
     - pkey: Key that identifies the property
     - value: Value that should be written
     - pass_rID: Whether to pass rID to the function
     - tHandle = 0: Optional handle to a transmit buffer. If unused set to
    zero.
    
    Return value(s):
     - rID: Request ID
    """
    if pass_rID:
        local_0 = ffi.new("SA_CTL_RequestID_t *")
    else:
        local_0 = ffi.NULL
    local_1 = lib.SA_CTL_RequestWriteProperty_s(dHandle, idx, pkey, value.encode(), local_0, tHandle)
    if local_1 != ErrorCode.NONE.value:
        raise Error("RequestWriteProperty_s", local_1, {"dHandle": dHandle, "idx": idx, "pkey": pkey, "value": value, "tHandle": tHandle})
    return local_0[0] if pass_rID else None
def RequestWritePropertyArray_i32(dHandle, idx, pkey, values, arraySize, pass_rID = True, tHandle = 0):
    """
    Requests to write the value of a 32-bit integer array property
    (non-blocking)
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the addressed device, module or channel
     - pkey: Key that identifies the property
     - values
     - arraySize
     - pass_rID: Whether to pass rID to the function
     - tHandle = 0: Optional handle to a transmit buffer. If unused set to
    zero.
    
    Return value(s):
     - rID: Request ID
    """
    if pass_rID:
        local_0 = ffi.new("SA_CTL_RequestID_t *")
    else:
        local_0 = ffi.NULL
    local_1 = lib.SA_CTL_RequestWritePropertyArray_i32(dHandle, idx, pkey, values, arraySize, local_0, tHandle)
    if local_1 != ErrorCode.NONE.value:
        raise Error("RequestWritePropertyArray_i32", local_1, {"dHandle": dHandle, "idx": idx, "pkey": pkey, "values": values, "arraySize": arraySize, "tHandle": tHandle})
    return local_0[0] if pass_rID else None
def RequestWritePropertyArray_i64(dHandle, idx, pkey, values, arraySize, pass_rID = True, tHandle = 0):
    """
    Requests to write the value of a 64-bit integer array property
    (non-blocking)
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the addressed device, module or channel
     - pkey: Key that identifies the property
     - values
     - arraySize
     - pass_rID: Whether to pass rID to the function
     - tHandle = 0: Optional handle to a transmit buffer. If unused set to
    zero.
    
    Return value(s):
     - rID: Request ID
    """
    if pass_rID:
        local_0 = ffi.new("SA_CTL_RequestID_t *")
    else:
        local_0 = ffi.NULL
    local_1 = lib.SA_CTL_RequestWritePropertyArray_i64(dHandle, idx, pkey, values, arraySize, local_0, tHandle)
    if local_1 != ErrorCode.NONE.value:
        raise Error("RequestWritePropertyArray_i64", local_1, {"dHandle": dHandle, "idx": idx, "pkey": pkey, "values": values, "arraySize": arraySize, "tHandle": tHandle})
    return local_0[0] if pass_rID else None
def WaitForWrite(dHandle, rID):
    """
    Returns the result of a property write access that has previously been
    requested using the data type specific RequestWriteProperty_x
    function
    
    Parameters:
     - dHandle: Handle to the device
     - rID: Request ID
    """
    local_0 = lib.SA_CTL_WaitForWrite(dHandle, rID)
    if local_0 != ErrorCode.NONE.value:
        raise Error("WaitForWrite", local_0, {"dHandle": dHandle, "rID": rID})
    return 
def CancelRequest(dHandle, rID):
    """
    Cancels a non-blocking read or write request
    
    Parameters:
     - dHandle: Handle to the device
     - rID: Request ID
    """
    local_0 = lib.SA_CTL_CancelRequest(dHandle, rID)
    if local_0 != ErrorCode.NONE.value:
        raise Error("CancelRequest", local_0, {"dHandle": dHandle, "rID": rID})
    return 
def CreateOutputBuffer(dHandle):
    """
    Opens an output buffer for delayed transmission of several commands
    
    Parameters:
     - dHandle: Handle to the device
    
    Return value(s):
     - tHandle: Handle to a transmit buffer
    """
    local_0 = ffi.new("SA_CTL_TransmitHandle_t *")
    local_1 = lib.SA_CTL_CreateOutputBuffer(dHandle, local_0)
    if local_1 != ErrorCode.NONE.value:
        raise Error("CreateOutputBuffer", local_1, {"dHandle": dHandle})
    return local_0[0]
def FlushOutputBuffer(dHandle, tHandle):
    """
    Parameters:
     - dHandle: Handle to the device
     - tHandle: Handle to a transmit buffer
    """
    local_0 = lib.SA_CTL_FlushOutputBuffer(dHandle, tHandle)
    if local_0 != ErrorCode.NONE.value:
        raise Error("FlushOutputBuffer", local_0, {"dHandle": dHandle, "tHandle": tHandle})
    return 
def CancelOutputBuffer(dHandle, tHandle):
    """
    Parameters:
     - dHandle: Handle to the device
     - tHandle: Handle to a transmit buffer
    """
    local_0 = lib.SA_CTL_CancelOutputBuffer(dHandle, tHandle)
    if local_0 != ErrorCode.NONE.value:
        raise Error("CancelOutputBuffer", local_0, {"dHandle": dHandle, "tHandle": tHandle})
    return 
def OpenCommandGroup(dHandle, triggerMode):
    """
    Opens a command group that can be used to combine multiple asynchronous
     commands into an atomic group
    
    Parameters:
     - dHandle: Handle to the device
     - triggerMode: Trigger mode for this command group
    
    Return value(s):
     - tHandle: Handle to a transmit buffer
    """
    local_0 = ffi.new("SA_CTL_TransmitHandle_t *")
    local_1 = lib.SA_CTL_OpenCommandGroup(dHandle, local_0, triggerMode)
    if local_1 != ErrorCode.NONE.value:
        raise Error("OpenCommandGroup", local_1, {"dHandle": dHandle, "triggerMode": triggerMode})
    return local_0[0]
def CloseCommandGroup(dHandle, tHandle):
    """
    Closes and eventually executes the assembled command group depending on
     the configured trigger mode
    
    Parameters:
     - dHandle: Handle to the device
     - tHandle: Handle to a transmit buffer
    """
    local_0 = lib.SA_CTL_CloseCommandGroup(dHandle, tHandle)
    if local_0 != ErrorCode.NONE.value:
        raise Error("CloseCommandGroup", local_0, {"dHandle": dHandle, "tHandle": tHandle})
    return 
def CancelCommandGroup(dHandle, tHandle):
    """
    Discards all buffered commands and releases the associated transmit
    handle
    
    Parameters:
     - dHandle: Handle to the device
     - tHandle: Handle to a transmit buffer
    """
    local_0 = lib.SA_CTL_CancelCommandGroup(dHandle, tHandle)
    if local_0 != ErrorCode.NONE.value:
        raise Error("CancelCommandGroup", local_0, {"dHandle": dHandle, "tHandle": tHandle})
    return 
def WaitForEvent(dHandle, timeout):
    """
    Listens to events from the device
    
    Parameters:
     - dHandle: Handle to the device
     - timeout: Maximum time to wait for an event to occur
    
    Return value(s):
     - event: Event that occurred
    """
    local_0 = ffi.new("SA_CTL_Event_t *")
    local_1 = lib.SA_CTL_WaitForEvent(dHandle, local_0, timeout)
    if local_1 != ErrorCode.NONE.value:
        raise Error("WaitForEvent", local_1, {"dHandle": dHandle, "timeout": timeout})
    return Event_t(local_0)
def Calibrate(dHandle, idx, tHandle = 0):
    """
    Starts a calibration routine for a given channel
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the channel
     - tHandle = 0: Optional handle to a transmit buffer. If unused set to
    zero.
    """
    local_0 = lib.SA_CTL_Calibrate(dHandle, idx, tHandle)
    if local_0 != ErrorCode.NONE.value:
        raise Error("Calibrate", local_0, {"dHandle": dHandle, "idx": idx, "tHandle": tHandle})
    return 
def Reference(dHandle, idx, tHandle = 0):
    """
    Starts a referencing routine for a given channel
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the channel
     - tHandle = 0: Optional handle to a transmit buffer. If unused set to
    zero.
    """
    local_0 = lib.SA_CTL_Reference(dHandle, idx, tHandle)
    if local_0 != ErrorCode.NONE.value:
        raise Error("Reference", local_0, {"dHandle": dHandle, "idx": idx, "tHandle": tHandle})
    return 
def Move(dHandle, idx, moveValue, tHandle = 0):
    """
    Instructs a positioner to move according to the current move
    configuration
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the channel
     - moveValue: The interpretation depends on the configured move mode
     - tHandle = 0: Optional handle to a transmit buffer. If unused set to
    zero.
    """
    local_0 = lib.SA_CTL_Move(dHandle, idx, moveValue, tHandle)
    if local_0 != ErrorCode.NONE.value:
        raise Error("Move", local_0, {"dHandle": dHandle, "idx": idx, "moveValue": moveValue, "tHandle": tHandle})
    return 
def Stop(dHandle, idx, tHandle = 0):
    """
    Stops any ongoing movement of the given channel
    
    Parameters:
     - dHandle: Handle to the device
     - idx: Index of the channel
     - tHandle = 0: Optional handle to a transmit buffer. If unused set to
    zero.
    """
    local_0 = lib.SA_CTL_Stop(dHandle, idx, tHandle)
    if local_0 != ErrorCode.NONE.value:
        raise Error("Stop", local_0, {"dHandle": dHandle, "idx": idx, "tHandle": tHandle})
    return 
def OpenStream(dHandle, triggerMode):
    """
    Opens a trajectory stream to the device
    
    Parameters:
     - dHandle: Handle to the device
     - triggerMode: Trigger mode for the trajectory stream
    
    Return value(s):
     - sHandle: Stream Handle
    """
    local_0 = ffi.new("SA_CTL_StreamHandle_t *")
    local_1 = lib.SA_CTL_OpenStream(dHandle, local_0, triggerMode)
    if local_1 != ErrorCode.NONE.value:
        raise Error("OpenStream", local_1, {"dHandle": dHandle, "triggerMode": triggerMode})
    return local_0[0]
def StreamFrame(dHandle, sHandle, frameData):
    """
    Supplies the device with stream data by sending one frame per function
    call
    
    Parameters:
     - dHandle: Handle to the device
     - sHandle: Stream Handle
     - frameData: Frame data buffer
    """
    local_0 = len(frameData)
    local_1 = lib.SA_CTL_StreamFrame(dHandle, sHandle, frameData, local_0)
    if local_1 != ErrorCode.NONE.value:
        raise Error("StreamFrame", local_1, {"dHandle": dHandle, "sHandle": sHandle, "frameData": frameData})
    return 
def CloseStream(dHandle, sHandle):
    """
    Closes a trajectory stream
    
    Parameters:
     - dHandle: Handle to the device
     - sHandle: Stream Handle
    """
    local_0 = lib.SA_CTL_CloseStream(dHandle, sHandle)
    if local_0 != ErrorCode.NONE.value:
        raise Error("CloseStream", local_0, {"dHandle": dHandle, "sHandle": sHandle})
    return 
def AbortStream(dHandle, sHandle):
    """
    Aborts a trajectory stream
    
    Parameters:
     - dHandle: Handle to the device
     - sHandle: Stream Handle
    """
    local_0 = lib.SA_CTL_AbortStream(dHandle, sHandle)
    if local_0 != ErrorCode.NONE.value:
        raise Error("AbortStream", local_0, {"dHandle": dHandle, "sHandle": sHandle})
    return 
class Global(enum.IntEnum):
    INFINITE = 4294967295
    HOLD_TIME_INFINITE = -1
    FALSE = 0
    TRUE = 1
    DISABLED = 0
    ENABLED = 1
    NON_INVERTED = 0
    INVERTED = 1
    FORWARD_DIRECTION = 0
    BACKWARD_DIRECTION = 1
    EITHER_DIRECTION = 2
    STRING_MAX_LENGTH = 63
    REQUEST_ID_MAX_COUNT = 240
INFINITE = Global.INFINITE
HOLD_TIME_INFINITE = Global.HOLD_TIME_INFINITE
FALSE = Global.FALSE
TRUE = Global.TRUE
DISABLED = Global.DISABLED
ENABLED = Global.ENABLED
NON_INVERTED = Global.NON_INVERTED
INVERTED = Global.INVERTED
FORWARD_DIRECTION = Global.FORWARD_DIRECTION
BACKWARD_DIRECTION = Global.BACKWARD_DIRECTION
EITHER_DIRECTION = Global.EITHER_DIRECTION
STRING_MAX_LENGTH = Global.STRING_MAX_LENGTH
REQUEST_ID_MAX_COUNT = Global.REQUEST_ID_MAX_COUNT
class InterfaceType(enum.IntEnum):
    USB      = 0x1
    ETHERNET = 0x2
class ChannelModuleType(enum.IntEnum):
    STICK_SLIP_PIEZO_DRIVER = 0x1
    MAGNETIC_DRIVER         = 0x2
class EventType(enum.IntEnum):
    NONE                      = 0x0000
    MOVEMENT_FINISHED         = 0x0001
    SENSOR_STATE_CHANGED      = 0x0002
    REFERENCE_FOUND           = 0x0003
    FOLLOWING_ERR_LIMIT       = 0x0004
    HOLDING_ABORTED           = 0x0005
    POSITIONER_TYPE_CHANGED   = 0x0006
    PHASING_FINISHED          = 0x0007
    SM_STATE_CHANGED          = 0x4000
    OVER_TEMPERATURE          = 0x4001
    HIGH_VOLTAGE_OVERLOAD     = 0x4002
    POWER_SUPPLY_OVERLOAD     = 0x4002
    POWER_SUPPLY_FAILURE      = 0x4003
    FAN_FAILURE_STATE_CHANGED = 0x4004
    ADJUSTMENT_FINISHED       = 0x4010
    ADJUSTMENT_STATE_CHANGED  = 0x4011
    ADJUSTMENT_UPDATE         = 0x4012
    DIGITAL_INPUT_CHANGED     = 0x4040
    STREAM_FINISHED           = 0x8000
    STREAM_READY              = 0x8001
    STREAM_TRIGGERED          = 0x8002
    CMD_GROUP_TRIGGERED       = 0x8010
    HM_STATE_CHANGED          = 0x8020
    EMERGENCY_STOP_TRIGGERED  = 0x8030
    EXT_INPUT_TRIGGERED       = 0x8040
    BUS_RESYNC_TRIGGERED      = 0x8050
    REQUEST_READY             = 0xf000
    CONNECTION_LOST           = 0xf001
class EventParameter(enum.IntEnum):
    PARAM_DETACHED = 0
    PARAM_ATTACHED = 1
    REQ_READY_TYPE_READ = 0
    REQ_READY_TYPE_WRITE = 1
    PARAM_RESULT_MASK = 65535
    PARAM_INDEX_MASK = 16711680
    PARAM_HANDLE_MASK = 4278190080
    REQ_READY_ID_MASK = 255
    REQ_READY_TYPE_MASK = 65280
    REQ_READY_DATA_TYPE_MASK = 16711680
    REQ_READY_ARRAY_SIZE_MASK = 4278190080
    REQ_READY_PROPERTY_KEY_MASK = 18446744069414584320
class ErrorCode(enum.IntEnum):
    NONE                           = 0x0000
    UNKNOWN_COMMAND                = 0x0001
    INVALID_PACKET_SIZE            = 0x0002
    TIMEOUT                        = 0x0004
    INVALID_PROTOCOL               = 0x0005
    BUFFER_UNDERFLOW               = 0x000c
    BUFFER_OVERFLOW                = 0x000d
    INVALID_FRAME_SIZE             = 0x000e
    INVALID_PACKET                 = 0x0010
    INVALID_KEY                    = 0x0012
    INVALID_PARAMETER              = 0x0013
    INVALID_DATA_TYPE              = 0x0016
    INVALID_DATA                   = 0x0017
    HANDLE_LIMIT_REACHED           = 0x0018
    ABORTED                        = 0x0019
    INVALID_DEVICE_INDEX           = 0x0020
    INVALID_MODULE_INDEX           = 0x0021
    INVALID_CHANNEL_INDEX          = 0x0022
    PERMISSION_DENIED              = 0x0023
    COMMAND_NOT_GROUPABLE          = 0x0024
    MOVEMENT_LOCKED                = 0x0025
    SYNC_FAILED                    = 0x0026
    INVALID_ARRAY_SIZE             = 0x0027
    OVERRANGE                      = 0x0028
    INVALID_CONFIGURATION          = 0x0029
    NO_HM_PRESENT                  = 0x0100
    NO_IOM_PRESENT                 = 0x0101
    NO_SM_PRESENT                  = 0x0102
    NO_SENSOR_PRESENT              = 0x0103
    SENSOR_DISABLED                = 0x0104
    POWER_SUPPLY_DISABLED          = 0x0105
    AMPLIFIER_DISABLED             = 0x0106
    INVALID_SENSOR_MODE            = 0x0107
    INVALID_ACTUATOR_MODE          = 0x0108
    INVALID_INPUT_TRIG_MODE        = 0x0109
    INVALID_CONTROL_OPTIONS        = 0x010a
    INVALID_REFERENCE_TYPE         = 0x010b
    INVALID_ADJUSTMENT_STATE       = 0x010c
    INVALID_INFO_TYPE              = 0x010d
    NO_FULL_ACCESS                 = 0x010e
    ADJUSTMENT_FAILED              = 0x010f
    MOVEMENT_OVERRIDDEN            = 0x0110
    NOT_CALIBRATED                 = 0x0111
    NOT_REFERENCED                 = 0x0112
    NOT_ADJUSTED                   = 0x0113
    SENSOR_TYPE_NOT_SUPPORTED      = 0x0114
    CONTROL_LOOP_INPUT_DISABLED    = 0x0115
    INVALID_CONTROL_LOOP_INPUT     = 0x0116
    UNEXPECTED_SENSOR_DATA         = 0x0117
    NOT_PHASED                     = 0x0118
    POSITIONER_FAULT               = 0x0119
    DRIVER_FAULT                   = 0x011a
    POSITIONER_TYPE_NOT_SUPPORTED  = 0x011b
    POSITIONER_TYPE_NOT_IDENTIFIED = 0x011c
    POSITIONER_TYPE_NOT_WRITEABLE  = 0x011e
    INVALID_ACTUATOR_TYPE          = 0x0121
    NO_COMMUTATION_SENSOR_PRESENT  = 0x0122
    AMPLIFIER_LOCKED               = 0x0123
    BUSY_MOVING                    = 0x0150
    BUSY_CALIBRATING               = 0x0151
    BUSY_REFERENCING               = 0x0152
    BUSY_ADJUSTING                 = 0x0153
    END_STOP_REACHED               = 0x0200
    FOLLOWING_ERR_LIMIT            = 0x0201
    RANGE_LIMIT_REACHED            = 0x0202
    POSITIONER_OVERLOAD            = 0x0203
    POWER_SUPPLY_FAILURE           = 0x0205
    OVER_TEMPERATURE               = 0x0206
    POWER_SUPPLY_OVERLOAD          = 0x0208
    INVALID_STREAM_HANDLE          = 0x0300
    INVALID_STREAM_CONFIGURATION   = 0x0301
    INSUFFICIENT_FRAMES            = 0x0302
    BUSY_STREAMING                 = 0x0303
    HM_INVALID_SLOT_INDEX          = 0x0400
    HM_INVALID_CHANNEL_INDEX       = 0x0401
    HM_INVALID_GROUP_INDEX         = 0x0402
    HM_INVALID_CH_GRP_INDEX        = 0x0403
    INTERNAL_COMMUNICATION         = 0x0500
    FEATURE_NOT_SUPPORTED          = 0x7ffd
    FEATURE_NOT_IMPLEMENTED        = 0x7ffe
    DEVICE_LIMIT_REACHED           = 0xf000
    INVALID_LOCATOR                = 0xf001
    INITIALIZATION_FAILED          = 0xf002
    NOT_INITIALIZED                = 0xf003
    COMMUNICATION_FAILED           = 0xf004
    INVALID_QUERYBUFFER_SIZE       = 0xf006
    INVALID_DEVICE_HANDLE          = 0xf007
    INVALID_TRANSMIT_HANDLE        = 0xf008
    UNEXPECTED_PACKET_RECEIVED     = 0xf00f
    CANCELED                       = 0xf010
    DRIVER_FAILED                  = 0xf013
    BUFFER_LIMIT_REACHED           = 0xf016
    INVALID_PROTOCOL_VERSION       = 0xf017
    DEVICE_RESET_FAILED            = 0xf018
    BUFFER_EMPTY                   = 0xf019
    DEVICE_NOT_FOUND               = 0xf01a
    THREAD_LIMIT_REACHED           = 0xf01b
    NO_APPLICATION                 = 0xf01c
class DataType(enum.IntEnum):
    UINT16  = 0x03
    INT32   = 0x06
    INT64   = 0x0e
    FLOAT32 = 0x10
    FLOAT64 = 0x11
    STRING  = 0x12
    NONE    = 0xff
class BaseUnit(enum.IntEnum):
    NONE    = 0x0
    PERCENT = 0x1
    METER   = 0x2
    DEGREE  = 0x3
    SECOND  = 0x4
    HERTZ   = 0x5
class Property(enum.IntEnum):
    NUMBER_OF_CHANNELS = 34537495
    NUMBER_OF_BUS_MODULES = 34537494
    INTERFACE_TYPE = 34537574
    DEVICE_STATE = 34537487
    DEVICE_SERIAL_NUMBER = 34537566
    DEVICE_NAME = 34537533
    EMERGENCY_STOP_MODE = 34537608
    DEFAULT_EMERGENCY_STOP_MODE = 34537750
    NETWORK_DISCOVER_MODE = 34537817
    NETWORK_DHCP_TIMEOUT = 34537820
    POWER_SUPPLY_ENABLED = 33751056
    NUMBER_OF_BUS_MODULE_CHANNELS = 33751063
    MODULE_TYPE = 33751142
    MODULE_STATE = 33751055
    STARTUP_OPTIONS = 167903325
    AMPLIFIER_ENABLED = 50462733
    AMPLIFIER_MODE = 50462911
    POSITIONER_CONTROL_OPTIONS = 50462813
    ACTUATOR_MODE = 50462745
    CONTROL_LOOP_INPUT = 50462744
    SENSOR_INPUT_SELECT = 50462877
    POSITIONER_TYPE = 50462780
    POSITIONER_TYPE_NAME = 50462781
    MOVE_MODE = 50659463
    CHANNEL_TYPE = 33685606
    CHANNEL_STATE = 50659343
    POSITION = 50659357
    TARGET_POSITION = 50659358
    SCAN_POSITION = 50659359
    SCAN_VELOCITY = 50659370
    HOLD_TIME = 50659368
    MOVE_VELOCITY = 50659369
    MOVE_ACCELERATION = 50659371
    MAX_CL_FREQUENCY = 50659375
    DEFAULT_MAX_CL_FREQUENCY = 50659415
    STEP_FREQUENCY = 50659374
    STEP_AMPLITUDE = 50659376
    FOLLOWING_ERROR_LIMIT = 50659413
    FOLLOWING_ERROR = 50462805
    FOLLOWING_ERROR_MAX = 84017237
    BROADCAST_STOP_OPTIONS = 50659421
    SENSOR_POWER_MODE = 50855961
    SENSOR_POWER_SAVE_DELAY = 50856020
    POSITION_MEAN_SHIFT = 50921506
    SAFE_DIRECTION = 50921511
    CL_INPUT_SENSOR_VALUE = 50462749
    CL_INPUT_AUX_VALUE = 50462898
    TARGET_TO_ZERO_VOLTAGE_HOLD_TH = 50462905
    CH_EMERGENCY_STOP_MODE = 33685640
    IN_POSITION_THRESHOLD = 50659416
    IN_POSITION_DELAY = 50659412
    LOGICAL_SCALE_OFFSET = 33816612
    LOGICAL_SCALE_INVERSION = 33816613
    RANGE_LIMIT_MIN = 33816608
    RANGE_LIMIT_MAX = 33816609
    DEFAULT_RANGE_LIMIT_MIN = 33816768
    DEFAULT_RANGE_LIMIT_MAX = 33816769
    CALIBRATION_OPTIONS = 50724957
    SIGNAL_CORRECTION_OPTIONS = 50724892
    REFERENCING_OPTIONS = 50790493
    DIST_CODE_INVERTED = 50790414
    DISTANCE_TO_REF_MARK = 50790562
    POS_MOVEMENT_TYPE = 50921535
    POS_IS_CUSTOM_TYPE = 50921537
    POS_BASE_UNIT = 50921538
    POS_BASE_RESOLUTION = 50921539
    POS_HEAD_TYPE = 50921614
    POS_REF_TYPE = 50921544
    POS_P_GAIN = 50921547
    POS_I_GAIN = 50921548
    POS_D_GAIN = 50921549
    POS_PID_SHIFT = 50921550
    POS_ANTI_WINDUP = 50921551
    POS_ESD_DIST_TH = 50921552
    POS_ESD_COUNTER_TH = 50921553
    POS_TARGET_REACHED_TH = 50921554
    POS_TARGET_HOLD_TH = 50921555
    POS_SAVE = 50921482
    POS_WRITE_PROTECTION = 50921485
    STREAM_BASE_RATE = 68091948
    STREAM_EXT_SYNC_RATE = 68091949
    STREAM_OPTIONS = 68091997
    STREAM_LOAD_MAX = 68092673
    CHANNEL_ERROR = 84017274
    CHANNEL_TEMPERATURE = 84017204
    BUS_MODULE_TEMPERATURE = 84082740
    POSITIONER_FAULT_REASON = 84017427
    MOTOR_LOAD = 84017429
    DIAG_CLOSED_LOOP_FREQUENCY_AVG = 84017198
    DIAG_CLOSED_LOOP_FREQUENCY_MAX = 84017199
    DIAG_CLF_MEASURE_TIME_BASE = 84017350
    IO_MODULE_OPTIONS = 100859997
    IO_MODULE_VOLTAGE = 100859953
    IO_MODULE_ANALOG_INPUT_RANGE = 100860064
    AUX_POSITIONER_TYPE = 134348860
    AUX_POSITIONER_TYPE_NAME = 134348861
    AUX_INPUT_SELECT = 134348824
    AUX_IO_MODULE_INPUT_INDEX = 135332010
    AUX_SENSOR_MODULE_INPUT_INDEX = 134938794
    AUX_IO_MODULE_INPUT0_VALUE = 135331840
    AUX_IO_MODULE_INPUT1_VALUE = 135331841
    AUX_SENSOR_MODULE_INPUT0_VALUE = 134938624
    AUX_SENSOR_MODULE_INPUT1_VALUE = 134938625
    AUX_DIRECTION_INVERSION = 134807566
    AUX_DIGITAL_INPUT_VALUE = 134414509
    AUX_DIGITAL_OUTPUT_VALUE = 134414510
    AUX_DIGITAL_OUTPUT_SET = 134414512
    AUX_DIGITAL_OUTPUT_CLEAR = 134414513
    AUX_ANALOG_OUTPUT_VALUE0 = 134414336
    AUX_ANALOG_OUTPUT_VALUE1 = 134414337
    THD_INPUT_SELECT = 151126040
    THD_IO_MODULE_INPUT_INDEX = 152109226
    THD_SENSOR_MODULE_INPUT_INDEX = 151716010
    THD_THRESHOLD_HIGH = 151126196
    THD_THRESHOLD_LOW = 151126197
    THD_INVERSION = 151126030
    DEV_INPUT_TRIG_SELECT = 101515421
    DEV_INPUT_TRIG_MODE = 101515399
    DEV_INPUT_TRIG_CONDITION = 101515354
    CH_INPUT_TRIG_MODE = 102039687
    CH_INPUT_TRIG_CONDITION = 102039642
    CH_OUTPUT_TRIG_MODE = 101580935
    CH_OUTPUT_TRIG_POLARITY = 101580891
    CH_OUTPUT_TRIG_PULSE_WIDTH = 101580892
    CH_POS_COMP_START_THRESHOLD = 101580888
    CH_POS_COMP_INCREMENT = 101580889
    CH_POS_COMP_DIRECTION = 101580838
    CH_POS_COMP_LIMIT_MIN = 101580832
    CH_POS_COMP_LIMIT_MAX = 101580833
    HM_STATE = 34340879
    HM_LOCK_OPTIONS = 34340995
    HM_DEFAULT_LOCK_OPTIONS = 34340996
    API_EVENT_NOTIFICATION_OPTIONS = 4027580509
    EVENT_NOTIFICATION_OPTIONS = 4027580509
    API_AUTO_RECONNECT = 4027580577
    AUTO_RECONNECT = 4027580577
class DeviceState(enum.IntEnum):
    HM_PRESENT            = 0x0001
    MOVEMENT_LOCKED       = 0x0002
    AMPLIFIER_LOCKED      = 0x0004
    INTERNAL_COMM_FAILURE = 0x0100
    IS_STREAMING          = 0x1000
class ModuleState(enum.IntEnum):
    SM_PRESENT            = 0x0001
    BOOSTER_PRESENT       = 0x0002
    ADJUSTMENT_ACTIVE     = 0x0004
    IOM_PRESENT           = 0x0008
    INTERNAL_COMM_FAILURE = 0x0100
    FAN_FAILURE           = 0x0800
    POWER_SUPPLY_FAILURE  = 0x1000
    HIGH_VOLTAGE_FAILURE  = 0x1000
    POWER_SUPPLY_OVERLOAD = 0x2000
    HIGH_VOLTAGE_OVERLOAD = 0x2000
    OVER_TEMPERATURE      = 0x4000
class ChannelState(enum.IntEnum):
    ACTIVELY_MOVING         = 0x00001
    CLOSED_LOOP_ACTIVE      = 0x00002
    CALIBRATING             = 0x00004
    REFERENCING             = 0x00008
    MOVE_DELAYED            = 0x00010
    SENSOR_PRESENT          = 0x00020
    IS_CALIBRATED           = 0x00040
    IS_REFERENCED           = 0x00080
    END_STOP_REACHED        = 0x00100
    RANGE_LIMIT_REACHED     = 0x00200
    FOLLOWING_LIMIT_REACHED = 0x00400
    MOVEMENT_FAILED         = 0x00800
    IS_STREAMING            = 0x01000
    POSITIONER_OVERLOAD     = 0x02000
    OVER_TEMPERATURE        = 0x04000
    REFERENCE_MARK          = 0x08000
    IS_PHASED               = 0x10000
    POSITIONER_FAULT        = 0x20000
    AMPLIFIER_ENABLED       = 0x40000
    IN_POSITION             = 0x80000
class HMState(enum.IntEnum):
    INTERNAL_COMM_FAILURE = 0x100
    IS_INTERNAL           = 0x200
class MoveMode(enum.IntEnum):
    CL_ABSOLUTE   = 0x0
    CL_RELATIVE   = 0x1
    SCAN_ABSOLUTE = 0x2
    SCAN_RELATIVE = 0x3
    STEP          = 0x4
class ActuatorMode(enum.IntEnum):
    NORMAL        = 0x0
    QUIET         = 0x1
    LOW_VIBRATION = 0x2
class ControlLoopInput(enum.IntEnum):
    DISABLED = 0x0
    SENSOR   = 0x1
    POSITION = 0x1
    AUX_IN   = 0x2
class SensorInputSelect(enum.IntEnum):
    POSITION = 0x0
    CALC_SYS = 0x1
class AuxInputSelect(enum.IntEnum):
    IO_MODULE     = 0x0
    SENSOR_MODULE = 0x1
class THDInputSelect(enum.IntEnum):
    IO_MODULE     = 0x0
    SENSOR_MODULE = 0x1
class EmergencyStopMode(enum.IntEnum):
    NORMAL       = 0x0
    RESTRICTED   = 0x1
    AUTO_RELEASE = 0x2
class CmdGroupTriggerMode(enum.IntEnum):
    DIRECT   = 0x0
    EXTERNAL = 0x1
class StreamTriggerMode(enum.IntEnum):
    DIRECT        = 0x0
    EXTERNAL_ONCE = 0x1
    EXTERNAL_SYNC = 0x2
    EXTERNAL      = 0x3
class StreamOption(enum.IntEnum):
    INTERPOLATION_DIS = 0x1
class StartupOption(enum.IntEnum):
    AMPLIFIER_ENABLE = 0x1
class PosControlOption(enum.IntEnum):
    ACC_REL_POS_DIS          = 0x001
    NO_SLIP                  = 0x002
    NO_SLIP_WHILE_HOLDING    = 0x004
    FORCED_SLIP_DIS          = 0x008
    STOP_ON_FOLLOWING_ERR    = 0x010
    TARGET_TO_ZERO_VOLTAGE   = 0x020
    CL_DIS_ON_FOLLOWING_ERR  = 0x040
    CL_DIS_ON_EMERGENCY_STOP = 0x080
    IN_POSITION              = 0x100
class CalibrationOption(enum.IntEnum):
    DIRECTION            = 0x001
    DIST_CODE_INV_DETECT = 0x002
    ASC_CALIBRATION      = 0x004
    REF_MARK_TEST        = 0x008
    LIMITED_TRAVEL_RANGE = 0x100
class ReferencingOption(enum.IntEnum):
    START_DIR             = 0x01
    REVERSE_DIR           = 0x02
    AUTO_ZERO             = 0x04
    ABORT_ON_ENDSTOP      = 0x08
    CONTINUE_ON_REF_FOUND = 0x10
    STOP_ON_REF_FOUND     = 0x20
class SensorPowerMode(enum.IntEnum):
    DISABLED   = 0x0
    ENABLED    = 0x1
    POWER_SAVE = 0x2
class BroadcastStopOption(enum.IntEnum):
    END_STOP_REACHED        = 0x1
    RANGE_LIMIT_REACHED     = 0x2
    FOLLOWING_LIMIT_REACHED = 0x4
class AmplifierMode(enum.IntEnum):
    DEFAULT              = 0x0
    POSITIONER_INTERLOCK = 0x1
class DeviceInputTriggerSelect(enum.IntEnum):
    IO_MODULE    = 0x0
    GLOBAL_INPUT = 0x1
class DeviceInputTriggerMode(enum.IntEnum):
    DISABLED       = 0x0
    EMERGENCY_STOP = 0x1
    STREAM         = 0x2
    CMD_GROUP      = 0x3
    EVENT          = 0x4
    AMPLIFIER_LOCK = 0x5
class ChannelInputTriggerMode(enum.IntEnum):
    DISABLED       = 0x0
    EMERGENCY_STOP = 0x1
class ChannelOutputTriggerMode(enum.IntEnum):
    CONSTANT         = 0x0
    POSITION_COMPARE = 0x1
    TARGET_REACHED   = 0x2
    ACTIVELY_MOVING  = 0x3
    IN_POSITION      = 0x4
class TriggerCondition(enum.IntEnum):
    RISING  = 0x0
    FALLING = 0x1
    EITHER  = 0x2
class TriggerPolarity(enum.IntEnum):
    ACTIVE_LOW  = 0x0
    ACTIVE_HIGH = 0x1
class HM1LockOption(enum.IntEnum):
    GLOBAL               = 0x000001
    CONTROL              = 0x000002
    CHANNEL_MENU         = 0x000010
    GROUP_MENU           = 0x000020
    SETTINGS_MENU        = 0x000040
    LOAD_CFG_MENU        = 0x000080
    SAVE_CFG_MENU        = 0x000100
    CTRL_MODE_PARAM_MENU = 0x000200
    CHANNEL_NAME         = 0x001000
    POS_TYPE             = 0x002000
    SAFE_DIR             = 0x004000
    CALIBRATE            = 0x008000
    REFERENCE            = 0x010000
    SET_POSITION         = 0x020000
    MAX_CLF              = 0x040000
    POWER_MODE           = 0x080000
    ACTUATOR_MODE        = 0x100000
    RANGE_LIMIT          = 0x200000
    CONTROL_LOOP_INPUT   = 0x400000
class EventNotificationOption(enum.IntEnum):
    REQUEST_READY_ENABLED = 0x1
class PositionerType(enum.IntEnum):
    MODIFIED  = 0x000
    AUTOMATIC = 0x12b
    CUSTOM0   = 0x0fa
    CUSTOM1   = 0x0fb
    CUSTOM2   = 0x0fc
    CUSTOM3   = 0x0fd
class PosWriteProtection(enum.IntEnum):
    KEY = 0x534d4152
class MovementType(enum.IntEnum):
    LINEAR          = 0x0
    ROTATORY        = 0x1
    GONIOMETER      = 0x2
    TIP_TILT        = 0x3
    IRIS            = 0x4
    OSCILLATOR      = 0x5
    HIGH_LOAD_TABLE = 0x6
class IOModuleVoltage(enum.IntEnum):
    VOLTAGE_3V3 = 0x0
    VOLTAGE_5V  = 0x1
class IOModuleOption(enum.IntEnum):
    ENABLED                = 0x1
    DIGITAL_OUTPUT_ENABLED = 0x1
    EVENTS_ENABLED         = 0x2
    ANALOG_OUTPUT_ENABLED  = 0x4
class IOModuleAnalogInputRange(enum.IntEnum):
    IO_MODULE_ANALOG_INPUT_RANGE_BI_10V  = 0x0
    IO_MODULE_ANALOG_INPUT_RANGE_BI_5V   = 0x1
    IO_MODULE_ANALOG_INPUT_RANGE_BI_2_5V = 0x2
    IO_MODULE_ANALOG_INPUT_RANGE_UNI_10V = 0x3
    IO_MODULE_ANALOG_INPUT_RANGE_UNI_5V  = 0x4
class SignalCorrectionOption(enum.IntEnum):
    DAC  = 0x02
    DPEC = 0x08
    ASC  = 0x10
class NetworkDiscoverMode(enum.IntEnum):
    DISABLED = 0x0
    PASSIVE  = 0x1
    ACTIVE   = 0x2
class ReferenceType(enum.IntEnum):
    NONE           = 0x0
    END_STOP       = 0x1
    SINGLE_CODED   = 0x2
    DISTANCE_CODED = 0x3
class PositionerFaultReason(enum.IntEnum):
    U_PHASE_SHORT     = 0x0001
    V_PHASE_SHORT     = 0x0002
    W_PHASE_SHORT     = 0x0004
    U_PHASE_OPEN      = 0x0008
    V_PHASE_OPEN      = 0x0010
    W_PHASE_OPEN      = 0x0020
    CURRENT_DEVIATION = 0x0040
    DRIVER_FAULT      = 0x8000
class ApiVersion(enum.IntEnum):
    MAJOR  = 0x1
    MINOR  = 0x3
    UPDATE = 0xd
import platform
__initBindings("SmarActCTL.dll" if platform.system() == "Windows" else ("lib" + "SmarActCTL".lower() + ".so"))
__all__ = ["api_version", "apigen_version", "Error", "Event_t", "GetFullVersionString", "GetResultInfo", "GetEventInfo", "Open", "Close", "Cancel", "FindDevices", "GetProperty_i32", "SetProperty_i32", "SetPropertyArray_i32", "GetProperty_i64", "SetProperty_i64", "SetPropertyArray_i64", "GetProperty_s", "SetProperty_s", "RequestReadProperty", "ReadProperty_i32", "ReadProperty_i64", "ReadProperty_s", "RequestWriteProperty_i32", "RequestWriteProperty_i64", "RequestWriteProperty_s", "RequestWritePropertyArray_i32", "RequestWritePropertyArray_i64", "WaitForWrite", "CancelRequest", "CreateOutputBuffer", "FlushOutputBuffer", "CancelOutputBuffer", "OpenCommandGroup", "CloseCommandGroup", "CancelCommandGroup", "WaitForEvent", "Calibrate", "Reference", "Move", "Stop", "OpenStream", "StreamFrame", "CloseStream", "AbortStream", "INFINITE", "HOLD_TIME_INFINITE", "FALSE", "TRUE", "DISABLED", "ENABLED", "NON_INVERTED", "INVERTED", "FORWARD_DIRECTION", "BACKWARD_DIRECTION", "EITHER_DIRECTION", "STRING_MAX_LENGTH", "REQUEST_ID_MAX_COUNT", "InterfaceType", "ChannelModuleType", "EventType", "EventParameter", "ErrorCode", "DataType", "BaseUnit", "Property", "DeviceState", "ModuleState", "ChannelState", "HMState", "MoveMode", "ActuatorMode", "ControlLoopInput", "SensorInputSelect", "AuxInputSelect", "THDInputSelect", "EmergencyStopMode", "CmdGroupTriggerMode", "StreamTriggerMode", "StreamOption", "StartupOption", "PosControlOption", "CalibrationOption", "ReferencingOption", "SensorPowerMode", "BroadcastStopOption", "AmplifierMode", "DeviceInputTriggerSelect", "DeviceInputTriggerMode", "ChannelInputTriggerMode", "ChannelOutputTriggerMode", "TriggerCondition", "TriggerPolarity", "HM1LockOption", "EventNotificationOption", "PositionerType", "PosWriteProtection", "MovementType", "IOModuleVoltage", "IOModuleOption", "IOModuleAnalogInputRange", "SignalCorrectionOption", "NetworkDiscoverMode", "ReferenceType", "PositionerFaultReason", "ApiVersion"]
