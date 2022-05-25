"""
Synthetic Laser Class
"""
import logging
from pathlib import Path

from model.devices.lasers.LaserBase import LaserBase


class SyntheticLaser(LaserBase):
    def __init__(self, model, verbose):
        # Logger Setup
        p = Path(__file__).resolve().parts[7]
        self.logger = logging.getLogger(p)

        super().__init__(model, verbose)

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
