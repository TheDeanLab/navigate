"""
ASLM laser trigger classes.
Class for mixed digital and analog modulation of laser devices.
Goal is to set the DC value of the laser intensity with the analog voltage, and then rapidly turn it on and off
with the digital signal.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

# Standard Library Imports
import logging

# Third Party Imports
import nidaqmx
from nidaqmx.errors import DaqError
from nidaqmx.constants import LineGrouping

# Local Imports
from aslm.model.devices.lasers.laser_base import LaserBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class LaserNI(LaserBase):
    def __init__(self, microscope_name, device_connection, configuration, laser_id):
        super().__init__(microscope_name, device_connection, configuration, laser_id)

        # Digital out (if using mixed modulation mode)
        try:
            laser_do_port = self.device_config["onoff"]["hardware"]["channel"]

            self.laser_do_task = nidaqmx.Task()
            self.laser_do_task.do_channels.add_do_chan(
                laser_do_port, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES
            )
        except (KeyError, DaqError) as e:
            self.laser_do_task = None
            if isinstance(e, DaqError):
                logger.exception(e)
                logger.debug(e.error_code)
                logger.debug(e.error_type)
                print(e)
                print(e.error_code)
                print(e.error_type)

        self._current_intensity = 0

        # Analog out
        try:
            laser_ao_port = self.device_config["power"]["hardware"]["channel"]
            self.laser_min_ao = self.device_config["power"]["hardware"]["min"]
            self.laser_max_ao = self.device_config["power"]["hardware"]["max"]

            self.laser_ao_task = nidaqmx.Task()
            self.laser_ao_task.ao_channels.add_ao_voltage_chan(
                laser_ao_port, min_val=self.laser_min_ao, max_val=self.laser_max_ao
            )
        except DaqError as e:
            logger.exception(e)
            logger.debug(e.error_code)
            logger.debug(e.error_type)
            print(e)
            print(e.error_code)
            print(e.error_type)

    def set_power(self, laser_intensity):
        try:
            scaled_laser_voltage = (int(laser_intensity) / 100) * self.laser_max_ao
            self.laser_ao_task.write(scaled_laser_voltage, auto_start=True)
            self._current_intensity = laser_intensity
        except DaqError as e:
            logger.exception(e)

    def turn_on(self):
        try:
            if self.laser_do_task is not None:
                self.laser_do_task.write(True, auto_start=True)
            self.set_power(self._current_intensity)
        except DaqError as e:
            logger.exception(e)

    def turn_off(self):
        try:
            if self.laser_do_task is None:
                tmp = self._current_intensity
                self.set_power(0)
                self._current_intensity = tmp
            else:
                self.laser_do_task.write(False, auto_start=True)
        except DaqError as e:
            logger.exception(e)

    def close(self):
        """
        # Close the port before exit.
        """
        try:
            self.laser_ao_task.close()
            if self.laser_do_task is not None:
                self.laser_do_task.close()
        except DaqError as e:
            logger.exception(e)
