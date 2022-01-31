'''
Obis Laser Class
OBIS561, 150 mW, is COM4
Useful information can be found on Page C-22 of the OBIS_LX_LS Operators Manual
'''

import serial
import sys
import re
from time import time, sleep

class ObisLaser():
    def __init__(self, port='COM4'):
        self.verbose = False
        self.timeout = 0.05
        self.end_of_line = '\r'

        try:
            # Open serial port
            self.port = serial.Serial()
            self.port.port = port
            self.port.baudrate = 115200
            self.port.parity = 'N'
            self.port.stopbits = 1
            self.port.bytesize = 8
            self.port.timeout = self.timeout
            self.port.open()
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
            self.port.close()
            if self.verbose:
                print("Port closed")
        except serial.SerialException:
            print('Could not close the port')

    def close(self):
        """
        # Close the port before exit.
        """
        try:
            self.port.close()
            if self.verbose:
                print("Port Closed")
        except serial.SerialException:
            print('could not close the port')

    def get_laser_model(self):
        """
        # Get the laser model.
        """
        command = "?SYSTem:INFormation:MODel?"
        laser_model = self.ask(command)
        if self.verbose:
            print("Laser Model:", laser_model)
        self.laser_model = laser_model
        return laser_model

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

        self.port.write(command.encode())
        if self.verbose:
            print("Set Laser Operating Mode to:", self.laser_operating_mode)

    def get_laser_operating_mode(self):
        """
        # Get the laser operating mode.
        """
        #  TODO: Fix

        command = "SOURce:AM:SOURce?"
        laser_operating_mode = self.ask(command)
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

    def ask(self, command):
        self.port.write(str(command + self.end_of_line).encode())
        response = ''
        read_iteration = self.port.read()
        while read_iteration != b'\r':
            response += read_iteration.decode()
            sleep(self.timeout)
            read_iteration = self.port.read()
        if self.verbose:
            print("Command:", command, "Response:", response)
        return response

    #def initialize_laser(self):
        #TODO: Finish this function
        # self.set_autostart(True)
        # self.set_power(laser1.pmax)
        # self.set_mode("Analog")
        # self.start()
        # print((self.wavelength, "nm Laser Initialized - Max Power: ", self.pmax, "mW"))

if (__name__ == "__main__"):
    # OBIS Laser Testing.
    pass












