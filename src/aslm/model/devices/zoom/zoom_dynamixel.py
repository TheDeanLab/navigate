# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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
import time

# Third Party Imports

# Local Imports
from aslm.model.devices.APIs.dynamixel import dynamixel_functions as dynamixel
from aslm.model.devices.zoom.zoom_base import ZoomBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_dynamixel_zoom_connection(configuration):
    id = configuration["configuration"]["hardware"]["zoom"]["servo_id"]
    comport = configuration["configuration"]["hardware"]["zoom"]["port"]
    devicename = comport.encode("utf-8")
    baudrate = configuration["configuration"]["hardware"]["zoom"]["baudrate"]

    port_num = dynamixel.portHandler(devicename)
    dynamixel.packetHandler()

    # Open port and set baud rate
    if not dynamixel.openPort(port_num):
        logger.debug("Unable to open DynamixelZoom")
        raise RuntimeError(f"Unable to open port {port_num}.")

    dynamixel.setBaudRate(port_num, baudrate)
    logger.debug("DynamixelZoom Initialized")

    return port_num


class DynamixelZoom(ZoomBase):
    r"""DynamixelZoom Class

    Controls the Dynamixel Servo.

    Methods
    -------
    set_zoom(zoom, wait_until_done)
        Change the DynamixelZoom position to zoom value of the microscope.
    move(position, wait_until_done)
        Move the DynamixelZoom position.
    read_position()
        Read the position of the DynamixelZoom servo.

    """

    def __init__(self, microscope_name, device_connection, configuration):
        super().__init__(microscope_name, device_connection, configuration)
        self.dynamixel = dynamixel
        self.id = configuration["configuration"]["microscopes"][microscope_name][
            "zoom"
        ]["hardware"]["servo_id"]
        self.addr_mx_torque_enable = 24
        self.addr_mx_goal_position = 30
        self.addr_mx_present_position = 36
        self.addr_mx_p_gain = 28
        self.addr_mx_torque_limit = 34
        self.addr_mx_moving_speed = 32

        # Specifies how much the goal position can be off (+/-) from the target
        self.goal_position_offset = 10

        # Specifies how long to sleep for the wait until done function

        self.sleeptime = 0.05
        self.timeout = 15

        # the dynamixel library uses integers instead of booleans for binary
        # information
        self.torque_enable = 1
        self.torque_disable = 0

        self.port_num = device_connection

    def __del__(self):
        logger.debug("DynamixelZoom Instance Deleted")
        self.dynamixel.closePort(self.port_num)

    def set_zoom(self, zoom, wait_until_done=False):
        r"""Change the DynamixelZoom Servo.

        Confirms tha the zoom position is available in the zoomdict

        Parameters
        ----------
        zoom : dict
            Zoom dictionary
        wait_until_done : bool
            Delay parameter.

        # Changes zoom after checking that the commanded value exists
        """
        if zoom in self.zoomdict:
            self.move(self.zoomdict[zoom], wait_until_done)
            self.zoomvalue = zoom
        else:
            logger.error(f"Zoom designation, {zoom}, not in the configuration")
            raise ValueError("Zoom designation not in the configuration")
        logger.debug(f"Changed DynamixelZoom to {zoom}")
        logger.debug(f"DynamixelZoom position: {self.read_position()}")

    def move(self, position, wait_until_done=False):
        r"""Move the DynamixelZoom Servo

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
            logger.debug(f"DynamixelZoom Upper Limit: {upper_limit}")

            lower_limit = position - self.goal_position_offset
            logger.debug(f"DynamixelZoom Lower Limit: {lower_limit}")

            cur_position = self.dynamixel.read4ByteTxRx(
                self.port_num, 1, self.id, self.addr_mx_present_position
            )

            while (cur_position < lower_limit) or (cur_position > upper_limit):
                # Timeout function
                if time.time() - start_time > self.timeout:
                    logger.debug(f"DynamixelZoom Timeout Event")
                    break
                time.sleep(0.05)
                cur_position = self.dynamixel.read4ByteTxRx(
                    self.port_num, 1, self.id, self.addr_mx_present_position
                )
                logger.debug(f"DynamixelZoom Current Position: {cur_position}")

    def read_position(self):
        r"""Read the position of the Zoom Servo.

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
