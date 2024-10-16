# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

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

# Standard Library Imports
import logging

# Third Party Imports

# Local Imports
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class MirrorBase:
    """MirrorBase Parent camera class."""

    def __init__(self, microscope_name, device_connection, configuration):
        """Initialize the MirrorBase class.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : object
            Hardware device to connect to
        configuration : multiprocessing.managers.DictProxy
            Global configuration of the microscope
        """
        if microscope_name not in configuration["configuration"]["microscopes"].keys():
            logger.error(f"Microscope {microscope_name} does not exist.")
            raise NameError(f"Microscope {microscope_name} does not exist.")

        #: dict: Configuration of the microscope
        self.configuration = configuration

        #: object: Hardware device to connect to
        self.mirror_controller = device_connection

        #: dict: Configuration of the mirror
        self.mirror_parameters = self.configuration["configuration"]["microscopes"][
            microscope_name
        ]["mirror"]

        #: bool: Is the mirror synthetic?
        self.is_synthetic = False

    def __str__(self):
        """Return the string representation of the mirror."""
        return "MirrorBase"

    def __del__(self) -> None:
        """Delete the MirrorBase class."""
        pass
