# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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
from typing import Any

# Third Party Imports

# Local Imports
from navigate.model.devices.filter_wheel.base import FilterWheelBase
from navigate.model.devices.device_types import SerialDevice
from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class ASIFilterWheel(FilterWheelBase, SerialDevice):
    """ASIFilterWheel - Class for controlling ASI Filter Wheels

    Note
    ----
        Additional information on the ASI Filter Wheel can be found at:
        https://asiimaging.com/docs/fw_1000#fw-1000_ascii_command_set
    """

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        device_id: int = 0,
    ) -> None:
        """Initialize the ASIFilterWheel class.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : TigerController
            Communication object for the ASI Filter Wheel.
        configuration : dict
            Global configuration of the microscope.
        device_id : int
            The ID of the device. Default is 0.
        """

        super().__init__(microscope_name, device_connection, configuration, device_id)

        #: float: Delay for filter wheel to change positions.
        self.wait_until_done_delay = self.device_config["filter_wheel_delay"]

        self.filter_wheel = device_connection

        # Send Filter Wheel/Wheels to Zeroth Position
        self.filter_wheel.select_filter_wheel(
            filter_wheel_number=self.filter_wheel_number
        )

        self.filter_wheel.move_filter_wheel(filter_wheel_position=0)

        #: int: Filter wheel position.
        self.filter_wheel_position = 0

    def __str__(self) -> str:
        """String representation of the class."""
        return "ASIFilterWheel"

    @classmethod
    def connect(
        cls, port: str, baudrate: int = 115200, timeout: float = 0.25
    ) -> TigerController:
        """Build ASIFilterWheel Serial Port connection

        Parameters
        ----------
        port : str
            Port for communicating with the filter wheel, e.g., COM1.
        baudrate : int
            Baud rate for communicating with the filter wheel, default is 115200.
        timeout : float
            Timeout for communicating with the filter wheel, default is 0.25.

        Returns
        -------
        tiger_controller : TigerController
            ASI Tiger Controller object.
        """
        # wait until ASI device is ready
        tiger_controller = TigerController(port, baudrate)
        tiger_controller.connect_to_serial()
        if not tiger_controller.is_open():
            logger.error("ASI stage connection failed.")
            raise Exception("ASI stage connection failed.")
        return tiger_controller

    def filter_change_delay(self, filter_name: str) -> None:
        """Estimate duration of time necessary to move the filter wheel

        Assumes that it is ~40ms per adjacent position.
        Depends on filter wheel parameters and load.

        Parameters
        ----------
        filter_name : str
            Name of filter to move to.

        """
        old_position = self.filter_wheel_position
        new_position = self.filter_dictionary[filter_name]
        delta_position = int(abs(old_position - new_position))
        self.wait_until_done_delay = delta_position * 0.04

    def set_filter(self, filter_name: str, wait_until_done=True) -> None:
        """Change the filter wheel to the filter designated by the filter
        position argument.

        Parameters
        ----------
        filter_name : str
            Name of filter to move to.
        wait_until_done : bool
            Waits duration of time necessary for filter wheel to change positions.
        """
        if self.check_if_filter_in_filter_dictionary(filter_name) is True:

            # Calculate the Delay Needed to Change the Positions
            self.filter_change_delay(filter_name)

            self.filter_wheel.select_filter_wheel(
                filter_wheel_number=self.filter_wheel_number
            )

            try:
                self.filter_wheel.move_filter_wheel(self.filter_dictionary[filter_name])
                self.filter_wheel_position = self.filter_dictionary[filter_name]
            except Exception as e:
                logger.error(f"Filter wheel movement failed: {e}")
                raise

            #  Wheel Position Change Delay
            if wait_until_done:
                time.sleep(self.wait_until_done_delay)

    def close(self) -> None:
        """Close the ASI Filter Wheel serial port.

        Sets the filter wheel to the home position and then closes the port.
        """
        if self.filter_wheel.is_open():
            self.filter_wheel.move_filter_wheel_to_home()
            logger.debug("ASI Filter Wheel - Closing Device.")
            self.filter_wheel.disconnect_from_serial()

    def __del__(self) -> None:
        """Destructor for the ASIFilterWheel class."""
        self.close()


@log_initialization
class ASICubeSliderFilterWheel(FilterWheelBase, SerialDevice):
    """ASICubeSlider - Class for controlling the C60 Cube Slider from ASI.

    Note
    ----
        Additional information on the ASI Filter Wheel can be found at:
        www.asiimaging.com/docs/filter_and_turret_changer?s%5B%5D=filter&s%5B%5D=slider

        Maximum number of positions is 4.

        Typical switch time between adjacent positions is < 250 ms.
    """

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        device_id: int = 0,
    ) -> None:
        """Initialize the ASICubeSlider class.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : TigerController
            Communication object for the ASI Filter Wheel.
        configuration : dict
            Global configuration of the microscope.
        device_id : int
            The ID of the device. Default is 0.
        """

        super().__init__(microscope_name, device_connection, configuration, device_id)

        #: obj: ASI Tiger Controller object.
        self.dichroic = device_connection

        #: float: Delay for filter wheel to change positions.
        self.wait_until_done_delay = self.device_config["filter_wheel_delay"]

        #: str: The ID of the dichroic in the Tiger Controller. e.g., "T"
        self.dichroic_id = self.filter_wheel_number

        self.dichroic.move_dichroic(dichroic_id=self.dichroic_id, dichroic_position=0)

        #: int: Filter wheel position.
        self.dichroic_position = 0

    @classmethod
    def connect(
        cls, port: str, baudrate: int = 115200, timeout: float = 0.25
    ) -> TigerController:
        """Build ASIFilterWheel Serial Port connection

        Parameters
        ----------
        port : str
            Port for communicating with the filter wheel, e.g., COM1.
        baudrate : int
            Baud rate for communicating with the filter wheel, default is 115200.
        timeout : float
            Timeout for communicating with the filter wheel, default is 0.25.

        Returns
        -------
        tiger_controller : TigerController
            ASI Tiger Controller object.
        """
        # wait until ASI device is ready
        tiger_controller = TigerController(port, baudrate)
        tiger_controller.connect_to_serial()
        if not tiger_controller.is_open():
            logger.error("ASI stage connection failed.")
            raise Exception("ASI stage connection failed.")
        return tiger_controller

    def filter_change_delay(self, filter_name: str) -> None:
        """Estimate duration of time necessary to move the dichroic

        Assumes that it is <250 ms per adjacent position.

        Parameters
        ----------
        filter_name : str
            Name of filter to move to.

        """
        old_position = self.dichroic_position
        new_position = self.filter_dictionary[filter_name]
        delta_position = int(abs(old_position - new_position))
        self.wait_until_done_delay = delta_position * 0.25

    def set_filter(self, filter_name: str, wait_until_done: bool = True) -> None:
        """Change the dichroic position.

        Parameters
        ----------
        filter_name : str
            Name of filter to move to.
        wait_until_done : bool
            Waits duration of time necessary for filter wheel to change positions.
        """
        if self.check_if_filter_in_filter_dictionary(filter_name) is True:

            # Calculate the Delay Needed to Change the Positions
            self.filter_change_delay(filter_name)
            target_position = self.filter_dictionary[
                filter_name
            ]  # Where we want to move the filter.

            assert target_position in range(4)

            try:
                self.dichroic.move_dichroic(
                    dichroic_id=self.dichroic_id, dichroic_position=target_position
                )
                self.dichroic_position = target_position
            except Exception as e:
                logger.error(f"Dichroic movement failed: {e}")
                raise

            #  Wheel Position Change Delay
            if wait_until_done:
                time.sleep(self.wait_until_done_delay)

    def close(self) -> None:
        """Close the ASI Filter Wheel serial port.

        Sets the filter wheel to the home position and then closes the port.
        """
        if self.dichroic.is_open():
            logger.debug("ASI C60 Motorized Slider - Closing Device.")
            self.dichroic.disconnect_from_serial()
