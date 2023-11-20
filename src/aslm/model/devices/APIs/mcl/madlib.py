import ctypes
from enum import IntEnum

__dll = ctypes.WinDLL(r"C:\Program Files\Mad City Labs\NanoDrive\Madlib.dll")


class MadlibErrorCode(IntEnum):
    MCL_GENERAL_ERROR = -1
    MCL_DEV_ERROR = -2
    MCL_DEV_NOT_ATTACHED = -3
    MCL_USAGE_ERROR = -4
    MCL_DEV_NOT_READY = -5
    MCL_ARGUMENT_ERROR = -6
    MCL_INVALID_AXIS = -7
    MCL_INVALID_HANDLE = -8


MadlibErrorCodeDescription = {
    MadlibErrorCode.MCL_GENERAL_ERROR: "General error",
    MadlibErrorCode.MCL_DEV_ERROR: "Device error",
    MadlibErrorCode.MCL_DEV_NOT_ATTACHED: "Device not attached",
    MadlibErrorCode.MCL_USAGE_ERROR: "Usage error",
    MadlibErrorCode.MCL_DEV_NOT_READY: "Device not ready",
    MadlibErrorCode.MCL_ARGUMENT_ERROR: "Invalid argument",
    MadlibErrorCode.MCL_INVALID_AXIS: "Invalid axis",
    MadlibErrorCode.MCL_INVALID_HANDLE: "Invalid axis handle",
}

# TODO: 'z' and 'f' have the same number? 
axes = {"x": 1, "y": 2, "z": 3, "f": 3, "aux": 4}


class MadlibError(Exception):
    """Exception for Mad City Labs device run off Madlib API."""


def in_enum(value, enum):
    values = set(item.value for item in enum)
    return value in values


def errcheck(result, func, args):
    """
    Wraps the call to DLL functions.

    Parameters
    ----------
    result : numeric or None
        Error code or positive number if successful.
    func : function
        DLL function
    args : tuple
        Arguments passed to the DLL function, defined in argtypes

    Returns
    -------
    result : int
        Error code or 0 if successful.
    """
    if result and result < 0:
        # returned a non-zero value
        if in_enum(result, MadlibErrorCode):
            raise MadlibError(MadlibErrorCodeDescription[result])
        else:
            raise Exception(f"Unknown error {result} in MCL device.")
    return result


__dll.MCL_InitHandle.restype = ctypes.c_int
__dll.MCL_InitHandle.errcheck = errcheck


def MCL_InitHandle():
    """Requests control of a single Mad City Labs Nano-Drive.

    If multiple Mad City Labs Nano-Drives are attached but not yet controlled, it is
    indeterminate which of the uncontrolled Nano-Drives this function will gain
    control of.

    Use a combination of MCL_GrabHandle, MCL_GrabAllHandles, MCL_GetAllHandles, and
    MCL_GetHandleBySerial to acquire the handle to a specific device.

    Returns
    -------
    int
        Returns a valid handle or returns 0 to indicate failure.
    """
    return int(__dll.MCL_InitHandle())


__dll.MCL_GrabAllHandles.restype = ctypes.c_int
__dll.MCL_GrabAllHandles.errcheck = errcheck


def MCL_GrabAllHandles():
    """Requests control of all of the attached  Mad City Labs Nano-Drives that are not
    yet under control.

    After calling this function use MCL_GetHandleBySerialNumber to get the handle of a
    specific device.

    Use MCL_NumberOfCurrentHandles and MCL_GetAllHandles to get a list of the handles
    acquired by this function.

    Remember that this function will take control of all of the attached Nano-Drives not
    currently under control. Some of the acquired handles may need to be released if
    those Nano-Drives are needed in other applications.

    Returns
    -------
    int
        Number of Nano-Drives currently controlled by this instance of the DLL.
    """
    return int(__dll.MCL_GrabAllHandles())


__dll.MCL_GetHandleBySerial.argtypes = [ctypes.c_short]
__dll.MCL_GetHandleBySerial.restype = ctypes.c_int
__dll.MCL_GetHandleBySerial.errcheck = errcheck


def MCL_GetHandleBySerial(serial_number):
    """Searches Nano-Drives currently controlled for a Nano-Drive whose serial number
    matches 'serial_number'.

    Parameters
    ----------
    serial_number : int
        Serial # of the Nano-Drive whose handle you want to lookup.

    Returns
    -------
    int
        Returns a valid handle or returns 0 to indicate failure
    """
    return int(__dll.MCL_GetHandleBySerial(serial_number))


__dll.MCL_ReleaseHandle.argtypes = [ctypes.c_int]
__dll.MCL_ReleaseHandle.restype = None
__dll.MCL_ReleaseHandle.errcheck = errcheck


def MCL_ReleaseHandle(handle):
    """Releases control of the specified Nano-Drive."""
    return __dll.MCL_ReleaseHandle(handle)


__dll.MCL_SingleWriteN.argtypes = [ctypes.c_double, ctypes.c_uint, ctypes.c_int]
__dll.MCL_SingleWriteN.restype = ctypes.c_int
__dll.MCL_SingleWriteN.errcheck = errcheck


def MCL_SingleWriteN(position, axis, handle):
    """Commands the Nano-Drive to move the specified axis to a position.

    Parameters
    ----------
    position : float
        Commanded position in microns.
    axis: str
        Which axis to move.  (X=1,Y=2,Z=3,AUX=4)
    handle: int
        Specifies which Nano-Drive to communicate with.

    Returns
    -------
    int
        0 if successful,  or the appropriate error code.
    """
    return int(__dll.MCL_SingleWriteN(position, axes[axis], handle))


__dll.MCL_SingleReadN.argtypes = [ctypes.c_uint, ctypes.c_int]
__dll.MCL_SingleReadN.restype = ctypes.c_double
__dll.MCL_SingleReadN.errcheck = errcheck


def MCL_SingleReadN(axis, handle):
    """Read the current position of the specified axis.

    Parameters
    ----------
    axis: str
        Which axis to read.  (X=1,Y=2,Z=3,AUX=4)
    handle: int
        Specifies which Nano-Drive to communicate with.

    Returns
    -------
    float
        Position value in microns or the appropriate error code.
    """
    return float(__dll.MCL_SingleReadN(axes[axis], handle))
