"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
# Help
# https://www.micron.ox.ac.uk/software/microscope/_modules/microscope/lights/obis.html

# Standard Library Imports
import logging
from pathlib import Path

import serial
from time import time, sleep

from aslm.model.devices.lasers.LaserBase import LaserBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

errors = {
    '-400': "Query Unavailable",
    "-350": "Queue overflow",
    "-321": "Out of memory",
    "-310": "System error",
    "-257": "File to open not named",
    "-256": "File does not exist",
    "-241": "Device unavailable",
    "-221": "Settings conflict",
    "-220": "Invalid parameter",
    "-203": "Command protected",
    "-200": "Execution error (command is out of order). Are you setting a parameter while the laser is in an ON state?",
    "-109": "Parameter missing",
    "-102": "Syntax error",
    "-100": "Unrecognized command or query",
    "0": "No error",
    "500": "CCB fault",
    "510": "I2C bus fault",
    "520": "Controller time out",
    "900": "CCB message timed out"
}

class ObisLaser(LaserBase):
    """
    Obis Laser Class
    OBIS561, 150 mW, is COM4
    Useful information can be found on Page C-22 of the OBIS_LX_LS Operators Manual
    """

    def __init__(self, verbose, port='COM28'):
        self.timeout = 0.05
        self.end_of_line = '\r\n'
        self.verbose = verbose

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
        self.laser.write((str(command) + self.end_of_line).encode('ascii'))
        print("command to write: ", str(command) + self.end_of_line)
        print("readline: ",self.laser.readline())
        response = self.laser.read_until(self.end_of_line.encode('ascii')).decode('ascii').strip('\r\n')
        print("Response: ", response)
        # print(self.laser.readline())
        if response.startswith('ERR'):
            code = response.strip('ERR')
            print(f"Error {code}: {errors[code]}.")
        return response

    # New version of ask() and moving it int two functions.
    # send() and read()

    def send(self, command):
        response = self.laser.write(command + b"\r\n")
        print(response)
        return response

    def read(self):
        response = self.laser.readline().strip()
        if self.laser.readline().strip() != b"OK":
            # This is be the error message if it isnt okay
            print(self.laser.readline().strip()) 
        return response



    def testing_handshake(self):
        self.laser.write("SOURce:AM:STATe?" + b"\r\n")
        print(self.laser.readline())
        print(self.laser.readline())
        print(self.laser.readline())
        print(self.laser.readline())

        self.laser.write("SOURce:AM:STATe OFF" + b"\r\n")
        print(self.laser.readline())
        print(self.laser.readline())
        print(self.laser.readline())
        print(self.laser.readline())

        self.laser.write("SOURce:AM:STATe?" + b"\r\n")
        self.laser.readline()
        print(self.laser.readline())
        self.laser.readline()
        print(self.laser.readline())

        self.laser.write("SOURce:AM:STATe OFF" + b"\r\n")
        self.laser.readline()
        print(self.laser.readline())
        self.laser.readline()
        print(self.laser.readline())

        self.laser.write("SOURce:AM:STATe?" + b"\r\n")
        print(self.laser.readline())
        self.laser.readline()
        print(self.laser.readline())
        self.laser.readline()

        self.laser.write("SOURce:AM:STATe OFF" + b"\r\n")
        print(self.laser.readline())
        self.laser.readline()
        print(self.laser.readline())
        self.laser.readline()


    
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
        # self.laser_model = laser_model
        return laser_model

    def get_laser_model_v2(self):
        """
        # Get the laser model.
        """
        self.send("SYSTem:INFormation:MODel?")
        response = self.read()
        if self.verbose:
            print("Laser Model:", laser_model)
        # self.laser_model = laser_model
        return laser_model

    def get_laser_calibration_date(self):
        """
        # Get the laser calibration date
        """
        command = "SYSTem:INFormation:CDATe?"
        laser_calibration_date = self.ask(command)
        if self.verbose:
            print("Laser Calibration Date:", laser_calibration_date)
        # self.laser_calibration_date = laser_calibration_date
        return laser_calibration_date
    
    def get_laser_serial_number(self):
        """
        # System Serial Number Query
        Retrieves the serial number of the laser.
        """
        command = "SYSTem:INFormation:SNUMber?"
        laser_serial_number = self.ask(command)
        if self.verbose:
            print("Laser Serial Number:", laser_serial_number)
        # self.laser_serial_number = laser_serial_number
        return laser_serial_number

    def get_laser_part_number(self):
        """
        # System Part Number Query
        Retrieves the manufacturer part number of the laser. 
        """
        command = "SYSTem:INFormation:PNUMber?"
        laser_part_number = self.ask(command)
        if self.verbose:
            print("Laser Part Number:", laser_part_number)
        # self.laser_part_number = laser_part_number
        return laser_part_number

    def get_laser_firmware(self):
        """
        # Get the lasers current firmware version
        """
        command = "SYSTem:INFormation:FVERsion?"
        laser_firmware = self.ask(command)
        if self.verbose:
            print("Laser Firmware:", laser_firmware)
        # self.laser_firmware = laser_firmware
        return laser_firmware

    def get_laser_protocol(self):
        """
        # Get the lasers protocol version
        """
        command = "SYSTem:INFormation:PVERsion?"
        laser_protocol = self.ask(command)
        if self.verbose:
            print("Laser Protocol Version:", laser_protocol)
        # self.laser_protocol = laser_protocol
        return laser_protocol

    def get_laser_wavelength(self):
        """
        # Get the current laser wavelength in nm.
        """
        command = "SYSTem:INFormation:WAVelength?"
        laser_wavelength = self.ask(command)
        if self.verbose:
            print("Laser Wavelength:", laser_wavelength)
        # self.laser_wavelength = laser_wavelength
        return laser_wavelength

    def get_power_rating(self):
        """
        # System Power Rating Query
        Retrieves the power rating (in watts) of the laser. 
        """
        command = "SYSTem:INFormation:POWer?"
        laser_power_rating = self.ask(command)
        if self.verbose:
            print("Laser Power Rating:", laser_power_rating)
        # self.laser_power_rating = laser_power_rating
        return laser_power_rating

    def get_minimum_laser_power(self):
        """
        # Get the maximum laser power in mW.
        """
        command = "SOURce:POWer:LIMit:LOW?"
        minimum_laser_power = self.ask(command)
        if self.verbose:
            print("Minimum Laser Power:", minimum_laser_power)
        # self.minimum_laser_power = minimum_laser_power
        return minimum_laser_power

    def get_maximum_laser_power(self):
        """
        # Get the maximum laser power in mW.
        """
        command = "SOURce:POWer:LIMit:HIGH?"
        maximum_laser_power = self.ask(command)
        if self.verbose:
            print("Maximum Laser Power:", maximum_laser_power)
        # self.maximum_laser_power = maximum_laser_power
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
        # self.laser_power = laser_power
        return laser_power

    def get_laser_output_current(self):
        """
        # Get the current laser output current in amps.
        """
        command = "SOURce:POWer:CURRent?"
        laser_output_current = self.ask(command)
        if self.verbose:
            print("Laser Output Current:", laser_output_current)
        # self.laser_output_current = laser_output_current
        return laser_output_current

    def get_base_plate_temp(self, unit="C"):
        """
        # Base Plate Temperature Query
        Returns the present laser base plate temperature. An optional unit indicator 
        may be specified. If the 'C' unit indicator is specified, or if the unit indicator 
        is left off, the returned value represents the laser base plate temperature in 
        degrees C. If the 'F' unit indicator is specified, the returned value represents 
        the laser base temperature in degrees F.
        """
        if unit == "C":
            #passed
            valid = True
        elif unit == "F":
            #passed
            valid = True
        else:
            valid = False
            unit = "C"

        command = "SOURce:TEMPerature:BASeplate? {unit}"
        laser_base_plate_temp = self.ask(command)
        if self.verbose:
            print("Laser Base Plate Temp:", laser_base_plate_temp)
        # self.laser_base_plate_temp = laser_base_plate_temp
        return laser_base_plate_temp

    
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
        
        # check if laser is on
        # if it is turned off then save the state so we can turn it back on
        # self.get_laser_state()
        # state = 'OFF'
        # if self.laser_state == 'ON':
        #     # save current state
        #     state = self.laser_state
        #     self.set_laser_to_off()

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

        # self.laser.write(command.encode())
        self.ask(command)
        if self.verbose:
            print("Set Laser Operating Mode to:", self.get_laser_operating_mode())

        # if state == 'ON':
        #     # turn laser back on
        #     self.set_laser_to_on()

    def get_laser_operating_mode(self):
        """
        # Get the laser operating mode.
        """
        #  ToDo: Fix (looks right but might have to look at the actal reply back to see what mode is written in the repose - more info is on page C-22)

        command = "SOURce:AM:SOURce?"
        laser_operating_mode = self.ask(command)

        # use this print for debugging if the function doesnt work
        print(f"test: {laser_operating_mode}")

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
        # self.laser_power_level = laser_power_level
        # return laser_power_level

    def set_laser_power_level(self, level):
        """
        # Set the current laser Laser Power Level.
        level represants the power level to set in watts
        """

        # check if laser is on
        # if it is turned off then save the state so we can turn it back on
        laser_state = self.get_laser_state()
        state = 'OFF'
        if laser_state == 'ON':
            # save current state
            state = laser_state
            self.set_laser_to_off()

        # not sure if this will work like this but worth a test
        command = f"SOURce:POWer:LEVel:IMMediate:AMPLitude {level}"
        print(command)
        self.ask(command)
        laser_power_level = self.ask("SOURce:POWer:LEVel:IMMediate:AMPLitude?")
        if self.verbose:
            print("Laser State:", laser_power_level)
        self.laser_power_level = laser_power_level

        if state == 'ON':
            # turn laser back on
            self.set_laser_to_on()
        
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
        # self.laser_state = laser_state
        return laser_state

    def set_laser_to_on(self):
        """
        # Set the laser state On state.
        """
        command = "SOURce:AM:STATe ON"
        laser_state = self.ask(command)
        if self.verbose:
            print("Laser State:", laser_state)
        # self.laser_state = laser_state
        return laser_state

    def set_laser_to_off(self):
        """
        # Set the laser state Off state.
        """
        command = "SOURce:AM:STATe OFF"
        laser_state = self.ask(command)
        if self.verbose:
            print("Laser State:", laser_state)
        # self.laser_state = laser_state
        return laser_state


    """
    # OBIS Mandatory Commands and Queries
        The OBIS Mandatory Command set is implemented by all OBIS compatible devices
    """

    def get_analog_mod_type(self):
        """
        # Get Analog Modulation Type
        Gets the analog modulation type that provides unique electrical impedance 
        on the analog interface of the OBIS Remote. The factory default is 50Ω. 
        """
        command = "SYSTem:INFormation:AMODulation:TYPe?"
        analog_mod_type = self.ask(command)
        if self.verbose:
            print("Laser Analog Modulation Type:", analog_mod_type)
        # self.analog_mod_type = analog_mod_type
        return analog_mod_type

    def set_analog_mod_type(self, type):
        """
        # Set Analog Modulation Type
        Sets the analog modulation type that provides unique electrical impedance 
        on the analog interface of the OBIS Remote. The factory default is 50Ω. 
        """

        self.get_laser_state()
        state = 'OFF'
        if self.laser_state == 'ON':
            # save current state
            state = self.laser_state
            self.set_laser_to_off()

        command = "SYSTem:INFormation:AMODulation:TYPe {type}"
        self.ask(command)
        analog_mod_type = self.ask("SYSTem:INFormation:AMODulation:TYPe?")
        if self.verbose:
            print("Laser Analog Modulation Type:", analog_mod_type)
        # self.analog_mod_type = analog_mod_type

        if state == 'ON':
            # turn laser back on
            self.set_laser_to_on()

        return analog_mod_type

    def get_system_status(self):
        """
        # System Status Query
        Gets the system status code. The status code is returned in a string 
        expressed in uppercase hexadecimal integer form. The 32-bit word 
        represents a bit-mapped status indicator. 
        """
        command = "SYSTem:STATus?"
        system_ststus = self.ask(command)
        if self.verbose:
            print("Laser System Status:", system_ststus)
        # self.system_ststus = system_ststus
        return system_ststus

    def get_system_fault(self):
        """
        # System Fault Query
        Gets the system fault code. The fault code is returned in a string expressed 
        in uppercase hexadecimal integer form. The 32-bit word represents a 
        bit-mapped fault indicator. 
        """
        command = "SYSTem:FAULt?"
        system_fault = self.ask(command)
        if self.verbose:
            print("Laser System Fault:", system_fault)
        # self.system_fault = system_fault
        return system_fault


    """
    # OBIS Optional Commands
        This section describes the optional commands for OBIS lasers.
    """
    
    def get_laser_blanking_status(self):
        """
        # Get Blanking Status
        """
        command = "SOURce:AModulation:BLANKing?"
        laser_blanking_status = self.ask(command)
        if self.verbose:
            print("Laser Blanking Status:", laser_blanking_status)
        # self.laser_blanking_status = laser_blanking_status
        return laser_blanking_status

    def set_laser_blanking_on(self):
        """
        # Set Blanking Status to ON
        """

        self.get_laser_state()
        state = 'OFF'
        if self.laser_state == 'ON':
            # save current state
            state = self.laser_state
            self.set_laser_to_off()

        command = "SOURce:AModulation:BLANKing ON"
        self.ask(command)
        laser_blanking_status = self.ask("SOURce:AModulation:BLANKing?")
        if self.verbose:
            print("Laser Blanking Status:", laser_blanking_status)
        # self.laser_blanking_status = laser_blanking_status

        if state == 'ON':
            # turn laser back on
            self.set_laser_to_on()

        return laser_blanking_status

    def set_laser_blanking_off(self):
        """
        # Set Blanking Status to OFF
        """
        
        self.get_laser_state()
        state = 'OFF'
        if self.laser_state == 'ON':
            # save current state
            state = self.laser_state
            self.set_laser_to_off()

        command = "SOURce:AModulation:BLANKing OFF"
        self.ask(command)
        laser_blanking_status = self.ask("SOURce:AModulation:BLANKing?")
        if self.verbose:
            print("Laser Blanking Status:", laser_blanking_status)
        # self.laser_blanking_status = laser_blanking_status

        if state == 'ON':
            # turn laser back on
            self.set_laser_to_on()

        return laser_blanking_status

    
    
    # we can add to this when we know what we want our laser setting to be when we turn it on
    def initialize_laser(self):
        """
        # Initialize the laser.
        """
        self.set_laser_to_on()
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
        # self.ext_control = ext_control
        return ext_control


    def get_laser_status(self):
        """
        # Get the current laser status.
        """
        command = "SOURce:STATus?"
        laser_status = self.ask(command)
        if self.verbose:
            print("Laser Status:", laser_status)
        # self.laser_status = laser_status
        return laser_status

    













