# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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

# Standard Library Imports
import logging
from typing import Any
from abc import ABC, abstractmethod

# Third Party Imports

# Local Imports
from navigate.tools.decorators import log_initialization
from navigate.config.configuration_schema import SettingSpec

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class LaserBase(ABC):
    """Laser Base Class"""

    configuration_schema = {
        "power/source": SettingSpec(
            str,
            default="hardware",
            choices=("hardware", "serial"),
            label="Power Control Source",
            required=False,
            help_text="Use existing electrical power control, or an optional laser software adapter.",
        ),
        "power/percent_reference_mw": SettingSpec(
            float,
            default=None,
            exclusive_minimum=0,
            required=False,
            label="Serial Power at 100% (mW)",
            help_text="Serial power reference; omitted values use the laser's queried maximum.",
        ),
        "software_control/type": SettingSpec(
            str,
            default="None",
            choices=("None", "Synthetic", "Vortran", "OBIS", "LuxX"),
            label="Laser Software Adapter",
            required=False,
            help_text="Optional connection to settings inside the laser; disabled by default.",
        ),
        "software_control/mode": SettingSpec(
            str,
            default="preserve",
            choices=("preserve", "cw", "digital", "analog", "mixed"),
            label="Laser Operating Mode",
            required=False,
            help_text="Preserve the current laser mode unless a mode is explicitly selected.",
        ),
        "software_control/port": SettingSpec(
            str,
            default="",
            label="Laser Serial Port",
            required=False,
        ),
        "software_control/baudrate": SettingSpec(
            int,
            default=None,
            minimum=1,
            label="Laser Baud Rate",
            required=False,
            help_text="Omit for the adapter default: Vortran 19200, OBIS 115200, LuxX 500000.",
        ),
        "software_control/timeout": SettingSpec(
            float,
            default=None,
            exclusive_minimum=0,
            label="Laser Timeout (s)",
            required=False,
            help_text="Omit for the adapter default: Vortran 2 seconds; other adapters 0.5 seconds.",
        ),
        "software_control/max_power_mw": SettingSpec(
            float,
            default=100.0,
            exclusive_minimum=0,
            label="Synthetic Maximum Power (mW)",
            required=False,
            help_text="Used only by the synthetic settings adapter.",
        ),
        "wavelength": SettingSpec(
            int,
            default=488,
            label="Wavelength (nm)",
            help_text="Laser emission wavelength in nanometres.",
            required=True,
        ),
        "power/hardware/type": SettingSpec(
            str,
            default="Synthetic",
            label="Power Type",
            choices=("NI", "ASI", "Synthetic"),
            help_text="Hardware used to control laser power.",
            required=True,
        ),
        "power/hardware/min": SettingSpec(
            float,
            default=0.0,
            label="Power Minimum",
            help_text="Lowest voltage used for analog laser-power control.",
            required=False,
        ),
        "power/hardware/max": SettingSpec(
            float,
            default=5.0,
            label="Power Maximum",
            help_text="Highest voltage used for analog laser-power control.",
            required=False,
        ),
        "onoff/hardware/type": SettingSpec(
            str,
            default="Synthetic",
            label="On/Off Type",
            choices=("NI", "ASI", "Synthetic"),
            help_text="Hardware used to switch the laser on and off.",
            required=True,
        ),
        "onoff/hardware/min": SettingSpec(
            float,
            default=0.0,
            label="On/Off Minimum",
            help_text="Lowest signal value used for laser on/off control.",
            required=False,
        ),
        "onoff/hardware/max": SettingSpec(
            float,
            default=5.0,
            label="On/Off Maximum",
            help_text="Highest signal value used for laser on/off control.",
            required=False,
        ),
    }

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: dict[str, Any],
        device_id: int,
    ) -> None:
        """Initialize Laser Base Class

        Parameters
        ----------
        microscope_name : str
            Name of the microscope
        device_connection : Any
            Communication instance with the device.
        configuration : Dict[str, Any]
            Configuration dictionary
        device_id : int
            Laser ID
        """
        #: Any: Communication instance with the device
        self.device_connection = device_connection

        #: dict: Configuration dictionary
        self.configuration = configuration

        #: str: Name of the microscope
        self.microscope_name = microscope_name

        #: int: Laser ID
        self.device_config = configuration["configuration"]["microscopes"][
            microscope_name
        ]["laser"][device_id]

    def __str__(self) -> str:
        """Return string representation of the class"""
        return "LaserBase"

    @abstractmethod
    def set_power(self, laser_intensity: int) -> None:
        """Set laser power

        This abstract method must be implemented by all subclasses.

        Parameters
        ----------
        laser_intensity : int
            Laser intensity
        """
        pass

    @abstractmethod
    def turn_on(self) -> None:
        """Turn on the laser

        This abstract method must be implemented by all subclasses.
        """
        pass

    @abstractmethod
    def turn_off(self) -> None:
        """Turn off the laser

        This abstract method must be implemented by all subclasses.
        """

        pass

    def close(self) -> None:
        """
        Close the laser before exit.
        """
        pass
