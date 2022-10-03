"""
Synthetic Laser Class
"""
import logging

from aslm.model.devices.lasers.laser_base import LaserBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class SyntheticLaser(LaserBase):
    def __init__(self, microscope_name, device_connection, configuration, laser_id):
        super().__init__(microscope_name, device_connection, configuration, laser_id)

    def close(self):
        """
        # Close the port before exit.
        """
        pass

    def initialize_laser(self):
        """
        # Initialize lasers.
        # Sets the laser to the maximum power, and sets the mode to CW-APC.
        """
        pass
