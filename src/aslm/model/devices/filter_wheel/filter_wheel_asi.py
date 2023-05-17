# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

#  Standard Library Imports
import logging
import time

# Third Party Imports
import numpy as np
import serial

# Local Imports
from aslm.model.devices.filter_wheel.filter_wheel_base import FilterWheelBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_filter_wheel_connection(comport, baudrate, timeout=0.25):
    """Build SutterFilterWheel Serial Port connection
    Attributes
    ----------
    comport : str
        Comport for communicating with the filter wheel, e.g., COM1.
    baudrate : int
        Baud rate for communicating with the filter wheel, e.g., 9600.
    """
    logging.debug(f"SutterFilterWheel - Opening Serial Port {comport}")
    try:
        return serial.Serial(comport, baudrate, timeout=0.25)
    except serial.SerialException:
        logger.warning("SutterFilterWheel - Could not establish Serial Port Connection")
        raise UserWarning(
            "Could not communicate with Sutter Lambda 10-B via COMPORT", comport
        )


class ASIFilterWheel(FilterWheelBase):
    """ASIFilterWheel Class

    Class for controlling ASI Filter Wheels
    https://asiimaging.com/docs/fw_1000#fw-1000_ascii_command_set

    """

    def __init__(self, microscope_name, device_connection, configuration):
        super().__init__(microscope_name, device_connection, configuration)

        print("ASI Filter wheel launched.")
        print("Device connection:", device_connection)


    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass

    def filter_change_delay(self, filter_name):
        pass

    def set_filter(self, filter_name, wait_until_done=True):
        pass

    def read(self, num_bytes):
        pass

    def close(self):
        pass