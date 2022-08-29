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
from serial import SerialTimeoutException
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

# ToDO - add fault status here if need be
fault = {
    '00000000': 'A value of 0 indicates no fault conditions',
}

# Started to add dictionary but I have not tested it out
commands = {
    # commands to get info from laser
    "l_model": "SYSTem:INFormation:MODel?",
    "l_cabibration_date": "SYSTem:INFormation:CDATe?",
    "l_serial_num": "SYSTem:INFormation:SNUMber?",
    "l_part_num": "SYSTem:INFormation:PNUMber?",
    "l_firmware_version": "SYSTem:INFormation:FVERsion?",
    "l_wavelength": "SYSTem:INFormation:WAVelength?",
    "l_power_rating": "SYSTem:INFormation:POWer?",
    "l_min_power": "SOURce:POWer:LIMit:LOW?",
    "l_max_power": "SOURce:POWer:LIMit:HIGH?",
    "l_output_power_level": "SOURce:POWer:LEVel?",
    "l_output_current": "SOURce:POWer:CURRent?",
    "l_opperating_mode": "SOURce:AM:SOURce?",
    "l_current_power_level": "SOURce:POWer:LEVel:IMMediate:AMPLitude?",
    "l_status": "SYSTem:STATus?",
    "l_state": "SOURce:AM:STATe?",
    "l_system_fault": "SYSTem:FAULt?",

    # set commands and values will need to be passed in function
    # valid value are ON or OFF
    "set_blanking": "SOURce:AModulation:BLANKing ",

    # Set operating mode Internal - valid values = CWP|CWC
    # Note CWC didnt work when base testing
    "set_operating_mode_Int": "SOURce:AM:INTernal ",

    # Set operating mode External - valid values = DIGital|ANALog|MIXed|DIGSO|MIXSO
    # Note DIGSO|MIXSO didnt work when base testing
    "set_operating_mode_Ext": "SOURce:AM:EXTernal ",

    # Set power level - needs to be exactly 5 decimal places or it will not work!
    "set_power_level": "SOURce:POWer:LEVel:IMMediate:AMPLitude ",

    # Set laser state - valid values = ON or OFF
    "set_state": "SOURce:AM:STATe ",


    # unrecognized commands Below
    "l_blanking_status": "SOURce:AModulation:BLANKing?",
    "l_analog_type": "SYSTem:INFormation:AMODulation:TYPe?",
    # set analog mod type - valid values = 1 or 2
    "set_analog_type": "SYSTem:INFormation:AMODulation:TYPe ",
    # set blanking status - valid values = On or OFF
    "set_blanking_status": "SOURce:AModulation:BLANKing ",
}

class ObisLaser(LaserBase):
    """
    Obis Laser Class
    OBIS561, 150 mW, is COM4
    Useful information can be found on Page C-22 of the OBIS_LX_LS Operators Manual
    """

    # took out verbose but you might have to change the com port as you use it
    def __init__(self, port='COM28'):
    # def __init__(self, port='COM4'):
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

        except serial.SerialException:
            print('Could not close the port')

    def close(self):
        """
        # Close the port before exit.
        """
        try:
            self.laser.close()

        except serial.SerialException:
            print('could not close the port')

    def send_and_read(self, command, value=''):
        self.send(command, value)
        self.read()

    # send() and read()

    def send(self, command, value=''):
        try:
            response = self.laser.write((command + value + self.end_of_line).encode())
            # print (command + value + self.end_of_line)
        except SerialTimeoutException as e:
            print(e)
        sleep(0.5)
        print(command + value)
        # return response


    #ToDo - Update with what might be needs to use the errors in the software or to log them
    def read(self):
        # this while loop fixed most of the blanking response issue
        response = ''
        while result := self.laser.readline():
            # print("Output: ",result)
            # print(result.decode('ascii').strip('\r\n'))
            if result == b'OK\r\n':
                # print('line is OK')
                # result = "OK"
                result = result.decode('ascii').strip('\r\n')
                break
            # if result == b'OFF\r\n':
            #     print('line is OFF')
            #     continue
            # if result == b'ON\r\n':
            #     print('line is OFF')
            #     continue
            if result.startswith(b'ERR'):
                # print('line is Error')
                # result = "ERROR"
                # Future error handling call TODO
                # result = result.strip('ERR')
                # print(f"Error {code}: {errors[code]}.")
                code = result.decode('ascii').strip('\r\n')
                message = code.strip('ERR')
                result = f"Error: {code}, Message: {errors[message]}"
                break
            # response = result
            response = result.decode('ascii').strip('\r\n')
            
        # Sleeps allowing serial communicate to finish???
        # look into instead of using sleep make sure we get an OK or response we are expecting before we send another
        # Fixing this would help speed up the code
        sleep(.5)
        # print(type(result))
        print(f"Result: {result}, Resp: {response}")
        return result, response


    # funstion is as it descibles an is what was used to test all of the commands
    def testing(self):

        # self.send_and_read(commands['l_state'])
        # self.send_and_read(commands['l_current_power_level'])
        # self.send_and_read(commands['set_power_level'], '.00200')
        # self.send_and_read(commands['l_model'])
        # self.send_and_read(commands['l_cabibration_date'])
        # self.send_and_read(commands['l_serial_num'])
        # self.send_and_read(commands['l_part_num'])
        # self.send_and_read(commands['l_firmware_version'])
        # self.send_and_read(commands['l_wavelength'])
        # self.send_and_read(commands['l_power_rating'])
        # self.send_and_read(commands['l_min_power'])
        # self.send_and_read(commands['l_max_power'])
        # self.send_and_read(commands['l_output_power_level'])
        # self.send_and_read(commands['l_output_current'])
        # self.send_and_read(commands['l_opperating_mode'])
        # self.send_and_read(commands['l_current_power_level'])
        # self.send_and_read(commands['l_status'])
        # self.send_and_read(commands['l_state'])
        # self.send_and_read(commands['l_system_fault'])

        # self.send_and_read(commands['set_operating_mode_Int'], 'CWP')
        # self.send_and_read(commands['l_opperating_mode'])
        # self.send_and_read(commands['set_operating_mode_Ext'], 'DIGital')
        # self.send_and_read(commands['l_opperating_mode'])
        # self.send_and_read(commands['set_operating_mode_Ext'], 'ANALog')
        # self.send_and_read(commands['l_opperating_mode'])
        # self.send_and_read(commands['set_operating_mode_Ext'], 'MIXed')
        # self.send_and_read(commands['l_opperating_mode'])

        self.send_and_read(commands['set_analog_type'], '1')
        self.send_and_read(commands['l_analog_type'])


        # level = 0.02
        # # Need to test this now
        # self.send("SOURce:POWer:LEVel:IMMediate:AMPLitude %.5f" % level)
        # # self.send("SOURce:POWer:LEVel:IMMediate:AMPLitude 0.20000 ")
        # # Sleeps allowing serial commaction to finish???
        # sleep(.5)
        # response = self.read()













