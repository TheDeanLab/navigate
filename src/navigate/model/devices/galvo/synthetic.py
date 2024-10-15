# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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


#  Standard Library Imports
import logging
from typing import Any, Dict, Optional

# Third Party Imports

# Local Imports
from navigate.model.devices.galvo.base import GalvoBase
from navigate.tools.decorators import log_initialization

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class SyntheticGalvo(GalvoBase):
    """SyntheticGalvo Class"""

    def __init__(
        self,
        microscope_name: str,
        device_connection: Optional[Any],
        configuration: Dict[str, Any],
        galvo_id: int = 0,
    ) -> None:
        """Initialize the SyntheticGalvo class.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : Any
            Device connection.
        configuration : Dict[str, Any]
            Dictionary of configuration parameters.
        galvo_id : int
            Galvo ID. Default is 0.
        """
        super().__init__(microscope_name, device_connection, configuration, galvo_id)

        #: str: Name of the microscope.
        self.microscope_name = microscope_name

        #: object: Device connection.
        self.device_connection = device_connection

        #: dict: Configuration parameters.
        self.configuration = configuration

        #: int: Galvo ID.
        self.galvo_id = galvo_id

    def __str__(self) -> str:
        """Return string representation of the GalvoNI."""
        return "SyntheticGalvo"
