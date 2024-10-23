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

# Standard Library Imports
import logging
import time

# Third Party Imports

# Local Imports
from navigate.model.devices.APIs.dynamixel import dynamixel_functions as dynamixel
from navigate.model.devices.zoom.base import ZoomBase
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_dynamixel_zoom_connection(configuration):
    """Connect to the DynamixelZoom Servo.

    Parameters
    ----------
    configuration : dict
        Configuration dictionary for the device.

    Returns
    -------
    port_num : int
        DynamixelZoom port number.
    """
    # id = configuration["configuration"]["hardware"]["zoom"]["servo_id"]
    comport = configuration["configuration"]["hardware"]["zoom"]["port"]
    devicename = comport.encode("utf-8")
    baudrate = configuration["configuration"]["hardware"]["zoom"]["baudrate"]

    port_num = dynamixel.portHandler(devicename)
    dynamixel.packetHandler()

    # Open port and set baud rate
    if not dynamixel.openPort(port_num):
        logger.error(f"Communication Error with Port {port_num}")
        raise RuntimeError(f"Unable to open port {port_num}.")

    dynamixel.setBaudRate(port_num, baudrate)
    return port_num


@log_initialization
class DynamixelZoom(ZoomBase):
    """DynamixelZoom Class - Controls the Dynamixel Servo."""

    def __init__(self, microscope_name, device_connection, configuration):
        """Initialize the DynamixelZoom Servo.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : int
            Connection string for the device.
        configuration : dict
            Configuration dictionary for the device.
        """
        super().__init__(microscope_name, device_connection, configuration)

        #: object: DynamixelZoom object.
        self.dynamixel = dynamixel

        #: int: DynamixelZoom ID.
        self.id = configuration["configuration"]["microscopes"][microscope_name][
            "zoom"
        ]["hardware"]["servo_id"]

        #: int: DynamixelZoom torque enable.
        self.addr_mx_torque_enable = 24

        #: int: DynamixelZoom goal position.
        self.addr_mx_goal_position = 30

        #: int: DynamixelZoom present position.
        self.addr_mx_present_position = 36

        #: int: DynamixelZoom p gain.
        self.addr_mx_p_gain = 28

        #: int: DynamixelZoom torque limit.
        self.addr_mx_torque_limit = 34

        #: int: DynamixelZoom moving speed.
        self.addr_mx_moving_speed = 32

        # Specifies how much the goal position can be off (+/-) from the target
        #: int: DynamixelZoom goal position offset.
        self.goal_position_offset = 10

        # Specifies how long to sleep for the wait until done function
        #: float: DynamixelZoom sleep time.
        self.sleeptime = 0.05

        #: float: DynamixelZoom timeout duration.
        self.timeout = 15

        # the dynamixel library uses integers instead of booleans for binary
        # information
        #: int: DynamixelZoom torque enable.
        self.torque_enable = 1

        #: int: DynamixelZoom torque disable.
        self.torque_disable = 0

        #: obj: DynamixelZoom port number.
        self.port_num = device_connection

    def __del__(self):
        """Delete the DynamixelZoom Instance"""
        try:
            self.dynamixel.closePort(self.port_num)
        except Exception as e:
            logger.exception(e)

    def set_zoom(self, zoom, wait_until_done=False):
        """Change the DynamixelZoom Servo.

        Confirms that the zoom position is available in the zoomdict, and then
        changes to that zoom value.

        Parameters
        ----------
        zoom : dict
            Zoom dictionary
        wait_until_done : bool
            Delay parameter.

        Raises
        ------
        ValueError
            If the zoom designation is not in the configuration.

        """
        if zoom in self.zoomdict:
            self.move(self.zoomdict[zoom], wait_until_done)
            #: str: Current zoom value.
            self.zoomvalue = zoom
        else:
            logger.error(f"Zoom designation, {zoom}, not in the configuration")
            raise ValueError("Zoom designation not in the configuration")

    def move(self, position, wait_until_done=False):
        """Move the DynamixelZoom Servo

        Parameters
        ----------
        position : int
            Location to move to.
        wait_until_done : bool
            Delay parameter
        """

        # Enable servo
        self.dynamixel.write1ByteTxRx(
            self.port_num, 1, self.id, self.addr_mx_torque_enable, self.torque_enable
        )

        # Write Moving Speed
        self.dynamixel.write2ByteTxRx(
            self.port_num, 1, self.id, self.addr_mx_moving_speed, 100
        )

        # Write Torque Limit
        self.dynamixel.write2ByteTxRx(
            self.port_num, 1, self.id, self.addr_mx_torque_limit, 200
        )

        # Write P Gain
        self.dynamixel.write1ByteTxRx(
            self.port_num, 1, self.id, self.addr_mx_p_gain, 44
        )

        # Write Goal Position
        self.dynamixel.write2ByteTxRx(
            self.port_num, 1, self.id, self.addr_mx_goal_position, position
        )

        # Check position
        if wait_until_done:
            start_time = time.time()
            upper_limit = position + self.goal_position_offset
            lower_limit = position - self.goal_position_offset
            cur_position = self.dynamixel.read4ByteTxRx(
                self.port_num, 1, self.id, self.addr_mx_present_position
            )

            while (cur_position < lower_limit) or (cur_position > upper_limit):
                # Timeout function
                if time.time() - start_time > self.timeout:
                    logger.debug("DynamixelZoom Timeout Event")
                    break
                time.sleep(0.05)
                cur_position = self.dynamixel.read4ByteTxRx(
                    self.port_num, 1, self.id, self.addr_mx_present_position
                )

    def read_position(self):
        """Read the position of the Zoom Servo.

        Returned position is an int between 0 and 4096.
        Opens and closes the port.

        Returns
        -------
        cur_position : int
            Servo position.
        """
        cur_position = self.dynamixel.read4ByteTxRx(
            self.port_num, 1, self.id, self.addr_mx_present_position
        )
        logger.debug(f"Zoom position {cur_position}")
        return cur_position
