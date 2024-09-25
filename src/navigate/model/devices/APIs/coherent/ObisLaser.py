"""
Obis Laser Class
OBIS561, 150 mW, is COM4
Useful information can be found on Page C-22 of the OBIS_LX_LS Operators Manual
"""
import logging

import serial
from time import sleep

from navigate.model.devices.lasers.base import LaserBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ObisLaser(LaserBase):
    def __init__(self, port="COM4"):

        #: float: The timeout for the laser in seconds.
        self.timeout = 0.05

        #: str: The end of line character for the laser
        self.end_of_line = "\r"

        try:
            # Open serial port
            #: serial.Serial: The serial port for the laser.
            self.laser = serial.Serial()
            self.laser.port = port
            self.laser.baudrate = 115200
            self.laser.parity = "N"
            self.laser.stopbits = 1
            self.laser.bytesize = 8
            self.laser.timeout = self.timeout
            self.laser.open()

        except serial.SerialException:
            logger.error(f"Could not open port {port}")
            raise OSError(
                'Port "%s" is unavailable.\n' % port
                + "Maybe the laser is not connected, the wrong"
                + " port is specified or the port is already opened"
            )

    def __del__(self):
        """
        # Close the port before exit.
        """
        try:
            # self.set_power(0)
            self.laser.close()

        except serial.SerialException:
            print("Could not close the port")

    def close(self):
        """
        # Close the port before exit.
        """
        try:
            self.laser.close()

        except serial.SerialException:
            print("could not close the port")

    def get_laser_model(self):
        """
        # Get the laser model.
        """
        command = "?SYSTem:INFormation:MODel?"
        laser_model = self.ask(command)
        self.laser_model = laser_model
        return laser_model

    def get_laser_wavelength(self):
        """
        # Get the current laser wavelength in nm.
        """
        command = "SYSTem:INFormation:WAVelength?"
        laser_wavelength = self.ask(command)
        self.laser_wavelength = laser_wavelength
        return laser_wavelength

    def get_minimum_laser_power(self):
        """
        # Get the maximum laser power in mW.
        """
        command = "SOURce:POWer:LIMit:LOW?"
        minimum_laser_power = self.ask(command)
        self.minimum_laser_power = minimum_laser_power
        return minimum_laser_power

    def get_maximum_laser_power(self):
        """
        # Get the maximum laser power in mW.
        """
        command = "SOURce:POWer:LIMit:HIGH?"
        maximum_laser_power = self.ask(command)
        self.maximum_laser_power = maximum_laser_power
        return maximum_laser_power

    def get_laser_power(self):
        """
        # Get the current laser power in mW.
        """
        command = "SOURce:POWer:LEVel?"
        laser_power = self.ask(command)
        self.laser_power = laser_power
        return laser_power

    def get_ext_control(self):
        """
        # Get the external control status.
        """
        command = "SYSTem:EXTernal:CONTRol?"
        ext_control = self.ask(command)
        self.ext_control = ext_control
        return ext_control

    def get_laser_status(self):
        """
        # Get the current laser status.
        """
        command = "SOURce:STATus?"
        laser_status = self.ask(command)
        self.laser_status = laser_status
        return laser_status

    def set_laser_operating_mode(self, mode):
        """
        # Set the laser operating mode.
        # Seven mutually exclusive operating modes are available
        # CWP (continuous wave, constant power)
        # CWC (continuous wave, constant current)
        # DIGITAL (CW with external digital modulation)
        # ANALOG (CW with external analog modulation)
        # MIXED (CW with external digital + analog modulation)
        # DIGSO (External digital modulation with power feedback) Note: This
        # operating mode is not supported in some device models.
        # MIXSO (External mixed modulation with power feedback) Note: This
        # operating mode is not supported in some device models.
        """
        if mode == "cwp":
            command = "SOURce:AM:INTernal CWP"
        elif mode == "cwc":
            command = "SOURce:AM:INTernal CWC"
        elif mode == "digital":
            command = "SOURce:AM:EXTernal DIGital"
        elif mode == "analog":
            command = "SOURce:AM:EXTernal ANALog"
        elif mode == "mixed":
            command = "SOURce:AM:EXTernal MIXed"
        elif mode == "digso":
            command = "SOURce:AM:EXTernal DIGSO"
        elif mode == "mixso":
            command = "SOURce:AM:EXTernal MIXSO"
        else:
            print("Invalid mode")
            return

        self.laser.write(command.encode())

    def get_laser_operating_mode(self):
        """
        # Get the laser operating mode.
        """
        #  TODO: Fix

        command = "SOURce:AM:SOURce?"
        laser_operating_mode = self.ask(command)
        if "CWP" in laser_operating_mode:
            self.laser_operating_mode = "cwp"
        elif "CWC" in laser_operating_mode:
            self.laser_operating_mode = "cwc"
        elif "DIGITAL" in laser_operating_mode:
            self.laser_operating_mode = "digital"
        elif "ANALOG" in laser_operating_mode:
            self.laser_operating_mode = "analog"
        elif "MIXED" in laser_operating_mode:
            self.laser_operating_mode = "mixed"
        elif "DIGSO" in laser_operating_mode:
            self.laser_operating_mode = "digso"
        elif "MIXSO" in laser_operating_mode:
            self.laser_operating_mode = "mixso"
        else:
            print("Invalid Laser Operating Mode")
            return
        return laser_operating_mode

    def ask(self, command):
        self.laser.write(str(command + self.end_of_line).encode())
        response = ""
        read_iteration = self.laser.read()
        while read_iteration != b"\r":
            response += read_iteration.decode()
            sleep(self.timeout)
            read_iteration = self.laser.read()
        return response

    def initialize_laser(self):
        """
        # Initialize the laser.
        """
        self.set_laser_operating_mode("mixed")
        self.set_laser_power(self.get_maximum_laser_power())
