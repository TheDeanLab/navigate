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

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class LaserTriggerBase:
    def __init__(self, configuration):
        self.configuration = configuration
        self.experiment = self.configuration['experiment']
        self.microscope = self.experiment['MicroscopeState']['resolution_mode'] 

        # Number of Lasers
        # TODO: Make it so that we can iterate through each laser and create a
        # task.
        self.lasers = self.configuration['configuration']['microscopes'][self.microscope]['lasers']
        self.number_of_lasers = len(self.lasers)

        # Minimum and Maximum Laser Voltages
        self.laser_min_do = self.lasers[0]['onoff']['hardware']['min']
        self.laser_max_do = self.lasers[0]['onoff']['hardware']['max']
        self.laser_min_ao = self.lasers[0]['power']['hardware']['min']
        self.laser_max_ao = self.lasers[0]['power']['hardware']['max']

        # Digital Ports
        self.switching_port = self.configuration['configuration']['microscopes']['low']['daq']['laser_port_switcher']
        self.laser_0_do_port = self.lasers[0]['onoff']['hardware']['channel']
        self.laser_1_do_port = self.lasers[1]['onoff']['hardware']['channel']
        self.laser_2_do_port = self.lasers[2]['onoff']['hardware']['channel']

        # Analog Ports
        self.laser_0_ao_port = self.lasers[0]['power']['hardware']['channel']
        self.laser_1_ao_port = self.lasers[1]['power']['hardware']['channel']
        self.laser_2_ao_port = self.lasers[2]['power']['hardware']['channel']

        # Digital Output Default State
        self.switching_state = False
        self.laser_0_do_state = False
        self.laser_1_do_state = False
        self.laser_2_do_state = False

        # Analog Output Default Voltage
        self.laser_0_ao_voltage = 0
        self.laser_1_ao_voltage = 0
        self.laser_2_ao_voltage = 0

    def __del__(self):
        logger.debug("Not Implemented in LaserTriggerBase")

    def enable_low_resolution_laser(self):
        """
        # Evaluates the experiment configuration in the model for the resolution mode.
        # Triggers the DAQ to select the correct laser path.
        """
        logger.debug("Not Implemented in LaserTriggerBase")

    def enable_high_resolution_laser(self):
        """
        # Evaluates the experiment configuration in the model for the resolution mode.
        # Triggers the DAQ to select the correct laser path.
        """
        logger.debug("Not Implemented in LaserTriggerBase")
    def trigger_digital_laser(self, current_laser_index):
        logger.debug("Not Implemented in LaserTriggerBase")

    def turn_off_lasers(self):
        logger.debug("Not Implemented in LaserTriggerBase")

    def set_laser_analog_voltage(
            self,
            current_laser_index,
            current_laser_intensity):
        """
        # Sets the constant voltage on the DAQ according to the laser index and intensity, which is a percentage.
        """
        logger.debug("Not Implemented in LaserTriggerBase")

