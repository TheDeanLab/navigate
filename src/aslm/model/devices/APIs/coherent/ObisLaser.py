"""
Obis Laser Class
OBIS561, 150 mW, is COM4
Useful information can be found on Page C-22 of the OBIS_LX_LS Operators Manual
"""
import logging
from pathlib import Path

import serial
from time import time, sleep

from aslm.model.devices.lasers.LaserBase import LaserBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class ObisLaser(LaserBase):
    def __init__(self, verbose, port='COM4'):
        self.timeout = 0.05
        self.end_of_line = '\r'

        try:
            # Open serial port
            self.laser = serial.Serial()
            self.laser.port = port
            self.laser.baudrate = 115200
            self.laser.parity = 'N'
            self.laser.stopbits = 1
            self.laser.bytesize = 8
            self.laser.timeout = self.timeout
            self.laser.open()
            if self.verbose:
                print("Port opened")

        except serial.SerialException:
            raise OSError('Port "%s" is unavailable.\n' % port + \
                          'Maybe the laser is not connected, the wrong' + \
                          ' port is specified or the port is already opened')

    def __del__(self):
        """
        # Close the port before exit.
        """
        try:
            # self.set_power(0)
            self.laser.close()
            if self.verbose:
                print("Port closed")
        except serial.SerialException:
            print('Could not close the port')

    def close(self):
        """
        # Close the port before exit.
        """
        try:
            self.laser.close()
            if self.verbose:
                print("Port Closed")
        except serial.SerialException:
            print('could not close the port')

    def ask(self, command):
        self.laser.write(str(command + self.end_of_line).encode())
        response = ''
        read_iteration = self.laser.read()
        while read_iteration != b'\r':
            response += read_iteration.decode()
            sleep(self.timeout)
            read_iteration = self.laser.read()
        if self.verbose:
            print("Command:", command, "Response:", response)
        return response

    
    """
    # System Information Queries
    """

    def get_laser_model(self):
        """
        # Get the laser model.
        """
        command = "SYSTem:INFormation:MODel?"
        laser_model = self.ask(command)
        if self.verbose:
            print("Laser Model:", laser_model)
        self.laser_model = laser_model
        return laser_model

    def get_laser_calibration_date(self):
        """
        # Get the laser calibration date
        """
        command = "SYSTem:INFormation:CDATe?"
        laser_calibration_date = self.ask(command)
        if self.verbose:
            print("Laser Calibration Date:", laser_calibration_date)
        self.laser_calibration_date = laser_calibration_date
        return laser_calibration_date

    def get_laser_firmware(self):
        """
        # Get the lasers current firmware version
        """
        command = "SYSTem:INFormation:FVERsion?"
        laser_firmware = self.ask(command)
        if self.verbose:
            print("Laser Firmware:", laser_firmware)
        self.laser_firmware = laser_firmware
        return laser_firmware

    def get_laser_protocol(self):
        """
        # Get the lasers protocol version
        """
        command = "SYSTem:INFormation:PVERsion?"
        laser_protocol = self.ask(command)
        if self.verbose:
            print("Laser Protocol Version:", laser_protocol)
        self.laser_protocol = laser_protocol
        return laser_protocol

    def get_laser_wavelength(self):
        """
        # Get the current laser wavelength in nm.
        """
        command = "SYSTem:INFormation:WAVelength?"
        laser_wavelength = self.ask(command)
        if self.verbose:
            print("Laser Wavelength:", laser_wavelength)
        self.laser_wavelength = laser_wavelength
        return laser_wavelength

    def get_minimum_laser_power(self):
        """
        # Get the maximum laser power in mW.
        """
        command = "SOURce:POWer:LIMit:LOW?"
        minimum_laser_power = self.ask(command)
        if self.verbose:
            print("Minimum Laser Power:", minimum_laser_power)
        self.minimum_laser_power = minimum_laser_power
        return minimum_laser_power

    def get_maximum_laser_power(self):
        """
        # Get the maximum laser power in mW.
        """
        command = "SOURce:POWer:LIMit:HIGH?"
        maximum_laser_power = self.ask(command)
        if self.verbose:
            print("Maximum Laser Power:", maximum_laser_power)
        self.maximum_laser_power = maximum_laser_power
        return maximum_laser_power

    def get_laser_system_info(self):
        """
        # Get all of the lasers system info.
        """
        self.get_maximum_laser_power(self)
        self.get_minimum_laser_power(self)
        self.get_laser_wavelength(self)
        self.get_laser_model(self)
        self.get_laser_calibration_date(self)
        self.get_laser_firmware(self)
        self.get_laser_protocol(self)

    """
    # System State Commands and Queries
    """

    def get_laser_power(self):
        """
        # Get the current laser power in mW.
        """
        command = "SOURce:POWer:LEVel?"
        laser_power = self.ask(command)
        if self.verbose:
            print("Laser Power:", laser_power)
        self.laser_power = laser_power
        return laser_power

    def get_laser_output_current(self):
        """
        # Get the current laser output current in amps.
        """
        command = "SOURce:POWer:CURRent?"
        laser_output_current = self.ask(command)
        if self.verbose:
            print("Laser Output Current:", laser_output_current)
        self.laser_output_current = laser_output_current
        return laser_output_current

    
    """
    # Operational Commands and Querie
    """

    def set_laser_operating_mode(self, mode):
        """
        # Set the laser operating mode. Seven mutually exclusive operating modes are available
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
        if mode == 'cwp':
            command = "SOURce:AM:INTernal CWP"
        elif mode == 'cwc':
            command = "SOURce:AM:INTernal CWC"
        elif mode == 'digital':
            command = "SOURce:AM:EXTernal DIGital"
        elif mode == 'analog':
            command = "SOURce:AM:EXTernal ANALog"
        elif mode == 'mixed':
            command = "SOURce:AM:EXTernal MIXed"
        elif mode == 'digso':
            command = "SOURce:AM:EXTernal DIGSO"
        elif mode == 'mixso':
            command = "SOURce:AM:EXTernal MIXSO"
        else:
            print("Invalid mode")
            return

        self.laser.write(command.encode())
        if self.verbose:
            print("Set Laser Operating Mode to:", self.laser_operating_mode)

    def get_laser_operating_mode(self):
        """
        # Get the laser operating mode.
        """
        #  ToDo: Fix (looks right but might have to look at the actal reply back to see what mode is written in the repose - more info is on page C-22)

        command = "SOURce:AM:SOURce?"
        laser_operating_mode = self.ask(command)

        # use this print for debugging if the function doesnt work
        print(laser_operating_mode)

        if ("CWP" in laser_operating_mode):
            self.laser_operating_mode = "cwp"
        elif ("CWC" in laser_operating_mode):
            self.laser_operating_mode = "cwc"
        elif ("DIGITAL" in laser_operating_mode):
            self.laser_operating_mode = "digital"
        elif ("ANALOG" in laser_operating_mode):
            self.laser_operating_mode = "analog"
        elif ("MIXED" in laser_operating_mode):
            self.laser_operating_mode = "mixed"
        elif ("DIGSO" in laser_operating_mode):
            self.laser_operating_mode = "digso"
        elif ("MIXSO" in laser_operating_mode):
            self.laser_operating_mode = "mixso"
        else:
            print("Invalid Laser Operating Mode")
            return
        if self.verbose:
            print("Laser Operating Mode:", laser_operating_mode)
        return laser_operating_mode

    def get_laser_power_level(self):
        """
        # Get the current laser Laser Power Level.
        The reply string represents the present laser power level setting as an NRf value in watts.
        """
        command = "SOURce:POWer:LEVel:IMMediate:AMPLitude?"
        laser_power_level = self.ask(command)
        if self.verbose:
            print("Laser State:", laser_power_level)
        self.laser_power_level = laser_power_level
        return laser_power_level

    def set_laser_power_level(self, level):
        """
        # Set the current laser Laser Power Level.
        level represants the power level to set in watts
        """

        # not sure if this will work like this but worth a test
        command = "SOURce:POWer:LEVel:IMMediate:AMPLitude " + level
        laser_power_level = self.ask(command)
        if self.verbose:
            print("Laser State:", laser_power_level)
        self.laser_power_level = laser_power_level
        return laser_power_level

    # we could add an API function here to rise or lower power level by x amuont

    def get_laser_state(self):
        """
        # Get the current laser state On/Off.
        """
        command = "SOURce:AM:STATe?"
        laser_state = self.ask(command)
        if self.verbose:
            print("Laser State:", laser_state)
        self.laser_state = laser_state
        return laser_state

    def set_laser_to_on(self):
        """
        # Set the laser state On state.
        """
        command = "SOURce:AM:STATe ON"
        laser_state = self.ask(command)
        if self.verbose:
            print("Laser State:", laser_state)
        self.laser_state = laser_state
        return laser_state

    def set_laser_to_off(self):
        """
        # Set the laser state Off state.
        """
        command = "SOURce:AM:STATe OFF"
        laser_state = self.ask(command)
        if self.verbose:
            print("Laser State:", laser_state)
        self.laser_state = laser_state
        return laser_state


    
    # we can add to this when we know what we want our laser setting to be when we turn it on
    def initialize_laser(self):
        """
        # Initialize the laser.
        """
        self.set_laser_to_on(self)
        self.set_laser_operating_mode('mixed')
        self.set_laser_power(self.get_maximum_laser_power())




    # I am not sure where these command come from as I cant find it in the documentation
    def get_ext_control(self):
        """
        # Get the external control status.
        """
        command = "SYSTem:EXTernal:CONTRol?"
        ext_control = self.ask(command)
        if self.verbose:
            print("External Control:", ext_control)
        self.ext_control = ext_control
        return ext_control


    def get_laser_status(self):
        """
        # Get the current laser status.
        """
        command = "SOURce:STATus?"
        laser_status = self.ask(command)
        if self.verbose:
            print("Laser Status:", laser_status)
        self.laser_status = laser_status
        return laser_status

    













