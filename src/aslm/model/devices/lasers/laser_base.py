"""
Laser Base Class
"""
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class LaserBase:
    def __init__(self, microscope_name, device_connection, configuration, laser_id):
        self.configuration = configuration
        self.microscope_name = microscope_name

        self.device_config = configuration['configuration']['microscopes'][microscope_name]['lasers'][laser_id]

    def set_power(self, laser_intensity):
        pass

    def turn_on(self):
        pass

    def turn_off(self):
        pass

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
