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
import time
import traceback
from typing import Any, Dict

# Third Party Imports

# Local Imports
from navigate.model.devices.laser.base import LaserBase
from navigate.model.devices.device_types import SerialDevice
from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class ASILaser(LaserBase, SerialDevice):
    """ASILaser - Class for controlling ASI Lasers

    This class is used to control a laser connected to a ASI Device.
    """

    def __init__(self, microscope_name, device_connection, configuration, device_id: int = 0):
        """Initialize the ASILaser class.

        Parameters
        ----------
        microscope_name : str
            The microscope name.
        device_connection : TigerController
            The device connection object.
        configuration : dict
            The device configuration.
        device_id : int
            The laser id.
        """

        super().__init__(microscope_name, device_connection, configuration, device_id)
        analog = configuration["configuration"]["microscopes"][microscope_name][
            "laser"
        ][device_id]["power"]["hardware"].get("type", None)

        digital = configuration["configuration"]["microscopes"][microscope_name][
            "laser"
        ][device_id]["onoff"]["hardware"].get("type", None)

        if "ASI" in analog and "ASI" in digital:
            modulation_type = "mixed"
            #: float: The minimum digital modulation voltage.
            self.laser_min_do = self.device_config["onoff"]["hardware"]["min"]
            #: float: The maximum digital modulation voltage.
            self.laser_max_do = self.device_config["onoff"]["hardware"]["max"]
            #: float: The minimum analog modulation voltage.
            self.laser_min_ao = self.device_config["power"]["hardware"]["min"]
            #: float: The maximum analog modulation voltage.
            self.laser_max_ao = self.device_config["power"]["hardware"]["max"]
            #: str: Output axes on Tiger Controller
            self.analog_axis = self.device_config["power"]["hardware"]["axis"]
            self.digital_axis = self.device_config["onoff"]["hardware"]["axis"]
        elif "ASI" in analog:
            modulation_type = "analog"
            #: float: The minimum analog modulation voltage.
            self.laser_min_ao = self.device_config["power"]["hardware"]["min"]
            #: float: The maximum analog modulation voltage.
            self.laser_max_ao = self.device_config["power"]["hardware"]["max"]
            #: str: Output axis on Tiger Controller
            self.analog_axis = self.device_config["power"]["hardware"]["axis"]
        elif "ASI" in digital:
            modulation_type = "digital"
            #: float: The minimum digital modulation voltage.
            self.laser_min_do = self.device_config["onoff"]["hardware"]["min"]
            #: float: The maximum digital modulation voltage.
            self.laser_max_do = self.device_config["onoff"]["hardware"]["max"]
            #: str: Output axes on Tiger Controller
            self.digital_axis = self.device_config["onoff"]["hardware"]["axis"]
        else:
            raise ValueError("Laser modulation type not recognized.")

        #: str: The modulation type of the laser - Analog, Digital, or Mixed.
        self.modulation_type = modulation_type

        #: TigerController: ASI Tiger Controller object.
        self.laser = device_connection

        #: float: Current laser intensity.
        self._current_intensity = 0

    def __str__(self):
        """String representation of the class."""
        return "ASILaser"

    @classmethod
    def connect(cls, port, baudrate=115200, timeout=0.25):
        """Build ASILaser Serial Port connection

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
    
    def set_power(self, laser_intensity: float):
        """Sets the analog laser power.

        Parameters
        ----------
        laser_intensity : float
            The laser intensity.
        """
        if self.modulation_type in ("digital", "mixed"):
            self.laser.setup_laser(self.digital_axis) 

        if self.modulation_type in ("analog", "mixed"):
            self.output_voltage = (int(laser_intensity) / 100) * self.laser_max_ao * 1000
            if self.output_voltage > (self.laser_max_ao * 1000):
                self.output_voltage = self.laser_max_ao * 1000
            self.laser.move_axis(self.analog_axis, self.output_voltage)
            self._current_intensity = laser_intensity

    def turn_on(self):
        """Turns on the laser."""
        if self.modulation_type == "mixed":
            self.set_power(self._current_intensity)
            self.laser.logic_card_on(self.digital_axis)
            logger.info(f"{str(self)} initialized with mixed modulation.")

        elif self.modulation_type == "analog":
            self.set_power(self._current_intensity)
            logger.info(f"{str(self)} initialized with analog modulation.")

        elif self.modulation_type == "digital":
            self.laser.logic_card_on(self.digital_axis)
            logger.info(f"{str(self)} initialized with digital modulation.")
        

    def turn_off(self):
        """Turns off the laser."""
        if self.modulation_type == "mixed":
            tmp = self._current_intensity
            self.set_power(0)
            self._current_intensity = tmp
            self.laser.logic_card_off(self.digital_axis)
            logger.info(f"{str(self)} initialized with mixed modulation.")

        elif self.modulation_type == "analog":
            tmp = self._current_intensity
            self.set_power(0)
            self._current_intensity = tmp
            logger.info(f"{str(self)} initialized with analog modulation.")

        elif self.modulation_type == "digital":
            self.laser.logic_card_off(self.digital_axis)
            logger.info(f"{str(self)} initialized with digital modulation.")

    
    def close(self):
        """Close the ASI Laser serial port.

        Turns the laser off and then closes the port.
        """
        if self.laser.is_open():
            self.turn_off()
            logger.debug("ASI Laser - Closing Device.")
            self.laser.disconnect_from_serial()

    def __del__(self):
        """Destructor for the ASILaser class."""
        self.close()
