"""
Laser Base Class
"""
import logging
from pathlib import Path


class LaserBase:
    def __init__(self, port, verbose):
        # Logger Setup
        p = Path(__file__).resolve().parts[7]
        self.logger = logging.getLogger(p)

        self.verbose = verbose

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
