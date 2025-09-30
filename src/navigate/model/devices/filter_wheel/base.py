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
#

#  Standard Library Imports
import logging
from typing import Any, Dict
from abc import ABC, abstractmethod

# Third Party Imports

# Local Imports
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class FilterWheelBase(ABC):
    """Abstract base class for filter wheels.

    This class defines the interface for filter wheel devices used in the Navigate software.
    Implementations should handle the specifics of communication with particular hardware.
    """

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
        device_id: int = 0,
    ) -> None:
        """Initialize the FilterWheelBase class.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : Any
            The communication instance with the device.
        configuration : Dict[str, Any]
            Global configuration dictionary.
        device_id : int
            The ID of the device. Default is 0.
        """
        #: Any: Device connection object.
        self.device_connection = device_connection

        #: Dict[str, Any]: Dictionary of device configuration parameters.
        device_config = configuration["configuration"]["microscopes"][microscope_name][
            "filter_wheel"
        ][device_id]
        self.device_config = device_config

        #: dict: Dictionary of filters available on the filter wheel.
        self.filter_dictionary = device_config["available_filters"]

        #: int: Filter wheel position.
        self.wheel_position = 0

        #: int: index of filter wheel
        self.filter_wheel_number = device_config["hardware"]["wheel_number"]

    @abstractmethod
    def set_filter(self, position: Any, wait_until_done: bool=True) -> None:
        """Set the filter wheel to the specified position.

        Parameters
        ----------
        position : Any
            The desired filter position.
        wait_until_done : bool
            Whether to wait until the filter wheel has completed the move. Default is True.
        """
        pass

    def __str__(self) -> str:
        """Return the string representation of the FilterWheelBase class."""
        return "FilterWheelBase"

    def __del__(self) -> None:
        """Destructor for the FilterWheelBase class."""
        pass

    def check_if_filter_in_filter_dictionary(self, filter_name: str) -> bool:
        """Checks if the filter designation (string) given exists in the
        filter dictionary

        Parameters
        ----------
        filter_name : str
            Name of filter.

        Returns
        -------
        filter_exists : bool
            Flag if filter exists in the filter dictionary.

        Raises
        ------
        ValueError
            If filter name is not in the filter dictionary.
        """

        if filter_name in self.filter_dictionary:
            filter_exists = True
        else:
            logger.error(f"Unknown filter name: {filter_name}")
            raise ValueError(f"Unknown filter name: {filter_name}")
        return filter_exists
