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
from nidaqmx.constants import LineGrouping

# Local Imports
from aslm.model.devices.lasers.laser_base import LaserBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class LaserNI(LaserBase):
    def __init__(self, microscope_name, device_connection, configuration, laser_id):
        super().__init__(microscope_name, device_connection, configuration, laser_id)

        laser_do_port = self.device_config['onoff']['hardware']['channel']
        laser_ao_port = self.device_config['power']['hardware']['channel']
        self.laser_min_ao = self.device_config['power']['hardware']['min']
        self.laser_max_ao = self.device_config['power']['hardware']['max']

        self.laser_do_task = nidaqmx.Task()

        # Initialize Analog Tasks
        self.laser_ao_task = nidaqmx.Task()

        # Add Ports to each Task
        self.laser_do_task.do_channels.add_do_chan(
            laser_do_port, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        self.laser_ao_task.ao_channels.add_ao_voltage_chan(
            laser_ao_port, min_val=self.laser_min_ao, max_val=self.laser_max_ao)

    def set_power(self, laser_intensity):
        scaled_laser_voltage = (
            int(laser_intensity) / 100) * self.laser_max_ao
        self.laser_ao_task.write(scaled_laser_voltage, auto_start=True)

    def turn_on(self):
        self.laser_do_task.write(True, auto_start=True)

    def turn_off(self):
        self.laser_do_task.write(False, auto_start=True)

    def close(self):
        """
        # Close the port before exit.
        """
        self.laser_ao_task.close()
        self.laser_do_task.close()
