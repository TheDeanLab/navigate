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

from .bindings import *
from . import bindings

def StreamFrame(dHandle, sHandle, frameData):
    """
    Supplies the device with stream data by sending one frame per function call
    
    Parameters:
     - dHandle: Handle to the device
     - sHandle: Stream Handle
     - frameData: Frame data buffer

    frameData must be a list of channel indexes and target positions.
    Even elements must be channel indexes and odd elements must be
    absolute target positions. The list must be even size.
    """
    if len(frameData) % 2 == 1:
        raise ValueError("frameData needs to have an even length")
    result = []
    for ch_idx, position in zip(frameData[::2], frameData[1::2]):
        if ch_idx < 0 or ch_idx >= 256:
            raise ValueError("channel index does not fit into a byte")
        pos_limit = 2**(8 * 8)
        if position >= pos_limit:
            raise ValueError("position does not fit into 8 bytes")
        result.append(ch_idx)
        position_bytes = []
        for _ in range(8):
            position_bytes.append(position & 0xFF)
            position = position >> 8
        result.extend(position_bytes)
    bindings.StreamFrame(dHandle, sHandle, result)

def _bind_macro_funcs():
    def PARAM_RESULT(param):
        return (param & EventParameter.PARAM_RESULT_MASK)
    def PARAM_INDEX(param):
        return (param & EventParameter.PARAM_INDEX_MASK) >> 16
    def PARAM_HANDLE(param):
        return (param & EventParameter.PARAM_HANDLE_MASK) >> 24
    def REQ_READY_ID(param):
        return (param & EventParameter.REQ_READY_ID_MASK)
    def REQ_READY_TYPE(param):
        return (param & EventParameter.REQ_READY_TYPE_MASK) >> 8
    def REQ_READY_DATA_TYPE(param):
        return (param & EventParameter.REQ_READY_DATA_TYPE_MASK) >> 16
    def REQ_READY_ARRAY_SIZE(param):
        return (param & EventParameter.REQ_READY_ARRAY_SIZE_MASK) >> 24
    def REQ_READY_PROPERTY_KEY(param):
        return (param & EventParameter.REQ_READY_PROPERTY_KEY_MASK) >> 32
    for func in (PARAM_RESULT, PARAM_INDEX, PARAM_HANDLE,
                 REQ_READY_ID, REQ_READY_TYPE, REQ_READY_DATA_TYPE,
                 REQ_READY_ARRAY_SIZE, REQ_READY_PROPERTY_KEY):
            setattr(EventParameter, func.__name__, func)
_bind_macro_funcs()


__all__ = bindings.__all__
