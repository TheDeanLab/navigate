# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
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

# Standard Imports
import logging
import time

# Third Party Imports

# Local Imports
from navigate.model.devices.stages.stage_base import StageBase
from navigate.model.devices.APIs.asi.asi_MFC_controller import (
    TigerException,
    MFCTwoThousand
)

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_ASI_Stage_connection(com_port, baud_rate=115200):
    """Connect to the ASI Stage

    Parameters
    ----------
    com_port : str
        Communication port for ASI MFC2000 Controller - e.g., COM1
    baud_rate : int
        Baud rate for ASI MFC2000 Controller - e.g., 9600

    Returns
    -------
    asi_stage : object
        Successfully initialized stage object.
    """

    # wait until ASI device is ready
    asi_stage = MFCTwoThousand(com_port, baud_rate)
    asi_stage.connect_to_serial()
    if not asi_stage.is_open():
        raise Exception("ASI stage connection failed.")

    return asi_stage
