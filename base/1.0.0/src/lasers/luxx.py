#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module uses **pyserial** module for communication with OMICRON LuxX
laser. The class **Laser** provides convenient methods for control of one
or several lasers, connected to the computer.

Example
-------
>>> laser1 = Laser()
>>> laser1.smart_ask("GSI")
>>> laser1.smart_ask("GOM")
>>> laser1.start()
>>> laser1.set_power(24)
>>> laser1.stop()
>>> del laser1

Author
------
Roman Kiselev, January 2014

License
-------
GNU GPL - use it for any purpose
"""


import serial
import sys
import re
from time import time

class Laser(port):
    """
    This class represents OMICRON LuxX laser. It opens the communication
    port upon object creation and asks the device for model and maximum
    power.

    Functions
    ---------
     * __init__(port="auto", baudrate=500000)
         constructor. Open port, get model name and power
     * __del__()
         destructor. Close the port upon completion
     * write(command)
         send command to device
     * read()
         read all data from port buffer
     * ask(command)
         send command and get only the relevant answer, as well as time
     * smart_ask(command)
         ask, which prints HEX answers in a table
     * print_HEX(HEXstring)
         print a nice table representing bits in a HEX number
     * start()
         start emission (takes 3 seconds)
     * stop()
         stop emission immediately
     * setPower(power_value)
         change the emitted power
     * getPower()
         ask for the current power (seting point, not actual emitted power)
     * setMode
         set an operating mode: standby, current control, power control
         or analog modulation.
     * getMode
         determine current operating mode
     * setAutostart
         if set, the laser will start emission on key turn event or on
         powerup. Otherwise, it can be started only from software with
         *LOn* command (**start** function).
     * getAutostart
         determine if autostart is active


    Laser control
    -------------
    The device itself contains FTDI microchip, which emulates serial port
    via USB. In Linux it appears as **\dev\ttyUSB#** file, where **#**
    is a number. In Windows, it leads to appearance of an additional COM
    port (**COM##**).

    If the laser is connected via USB cable, the baudrate is 500000; it can
    also be connected via RS-232 interface with a special cable, then the
    baudrate should be set to 57600.

    The laser is controlled with short commands (register matters!). The
    full desciption of commands can be found in the file
    *PhoxX_LuxX_BrixX_command_list V1.0.pdf*. Here is a list of commands
    that are relevant to the LuxX model:
     * RsC
         Reset Controller
     * GFw
         Get Firmware
     * GSN
         Get Serial Number
     * GSI
         Get Spec Info
     * GMP
         Get Maximum Power
     * GWH
         Get Working Hours
     * ROM
         Recall Operating Mode (Standby, CW-ACC, CW-APC, Analog)
     * GOM
         Get Operating Mode (**ASCII HEX**)
     * SOM
         Set Operating Mode (**ASCII HEX**)
     * SAS
         Set Auto Start (Laser will emit after startup)
     * SAP
         Set Auto Powerup
     * LOn
         Laser On - start emission
     * LOf
         Laser Off
     * POn
         Power On
     * POf
         Power Off
     * GAS
         Get Actual Status
     * GFB
         Get Failure Byte (**ASCII HEX**)
     * GLF
         Get Last Failurebyte (**ASCII HEX**)
     * MDP
         Measure Diode Power
     * MTD
         Measure Temperature Diode
     * MTA
         Measure Temperature Ambient
     * CLD
         Calibrate Laser Diode
     * SLP
         Set Level Power - set the emitted power (**ASCII HEX up to 0xFFF**)
     * GLP
         Get Level Power (**ASCII HEX**)

    """


    def __init__(self, port, baudrate=500000):
        try:
            self.port = serial.Serial(port, baudrate, timeout=0.3)
            self.firmware = self.ask("GFw")
            if self.firmware.find("LuxX")  < 0 & \
               self.firmware.find("BrixX") < 0 & \
               self.firmware.find("PhoxX") < 0:
                print("The LuxX | BrixX | PhoxX laser is not connected. " + \
                      "The received answer for '?GFw\\r' command is:\n" + \
                      self.firmware)
                raise serial.SerialException
            # From this point we know, that the right laser is connected
            self.wavelength = float(self.ask("GSI").split()[0])
            self.serial = self.ask("GSN")
            self.hours = self.ask("GWH")
            self.pmax = float(self.ask("GMP"))
        except serial.SerialException:
            raise OSError('Port "%s" is unavailable.\n' % port + \
                          'May be the laser is not connected, the wrong' + \
                          ' port is specified or the port is already opened')


    def __del__(self):
        """Close the port before exit."""
        try:
            self.port.close()
            print("Port closed")
        except serial.SerialException:
            print('could not close the port')


    def write(self, command):
        """Send *command* to device. Preceed it with "?" und end with CR."""
        self.port.write("?" + command + "\r")


    def read(self):
        """Read all information from the port and return it as string."""
        answer = self.port.readall()
        return answer.replace("\r", "\n").replace("\xa7", " | ")


    def ask(self, command):
        """Write, then read. However, return only the relevant info."""
        self.write(command)
        response = self.read()
        if re.findall("!UK\n", response):
            print("Command '%s' is unknown for this device" % command)
        else:
            response = re.findall("!%s(.+)\n" % command[:3], response)[-1]
            if response[0] == "x":
                print("Laser responded with error to command '%s'" % command)
            return response


    def smart_ask(self, command):
        """
        Several commands return information coded in ASCII HEX numbers.
        The relevant are bits in the registers. For convenient
        representation, we will print these bytes in tables.
        This is relevant for the following commands:
            * GOM
            * GFB
            * GLF
            * GLP
        For all other commands the behavior is identical to **ask** function
        """
        if command in ["GOM", "GFB", "GLF", "GLP"]:
            return print_hex(self.ask(command))
        else:
            return self.ask(command)


    def start(self):
        """Start the emission (takes about 3 seconds)"""
        self.write("LOn")


    def stop(self):
        """Stop the emission immediately"""
        self.write("LOf")


    def set_power(self, power):
        """Set the desired power in mW"""
        # Calculate the corresponding HEX code and transmit it
        if power > self.pmax:
            print("Laser provides %imW only. The maximum power is set" % self.pmax)
            self.write("SLPFFF")
        else:
            code = hex(int(4095*power/self.pmax))[2:].upper().zfill(3)
            stopwatch(self.ask, "SLP%s" % code)


    def get_power(self):
        """Get the current power value in mW"""
        code = stopwatch(self.ask, "GLP")
        return int(code, 16)*self.pmax/4095.


    def set_mode(self, mode):
        """
        The device is able to work in the following modes:
          * Standby
              Laser is ready, but no emission is produced. However, if we
              it is turned on (e.g. with **start** function), then change to
              other mode will result in immediate emission, i.e. without
              3 seconds delay.
          * CW-ACC
              constant wave, automatic current control
          * CW-APC
              constant wave, automatic power control
          * Analog
              the output power is dependent on the analog input; however,
              it cannot exceed the specified with **set_power** value.
        """
        if mode == "Standby" or mode == 0:
            mode = 0
        elif mode == "CW-ACC" or mode == 1:
            mode = 1
        elif mode == "CW-APC" or mode == 2:
            mode = 2
        elif mode == "Analog" or mode == 3:
            mode = 3
        else:
            print("**mode** must be one of 'Standby', 'CW-ACC', " + 
            "'CW-APC', 'Analog' or number 0-3. Nothing changed.")
            return
        stopwatch(self.ask, "ROM%i" % mode)


    def get_mode(self):
        """
        The device is able to work in the following modes:
          * Standby
              turned off
          * CW-ACC
              constant wave, automatic current control
          * CW-APC
              constant wave, automatic power control
          * Analog
              the output power is dependent on the analog input; however,
              it cannot exceed the specified with **set_power** value.
        """
        mode = int(stopwatch(self.ask, "ROM"))
        if mode == 0:
            return "Standby"
        elif mode == 1:
            return "CW-ACC"
        elif mode == 2:
            return "CW-APC"
        elif mode == 3:
            return "Analog"
        else:
            return mode


    def set_autostart(self, state):
        """Decide if light is emitted on powerup."""
        if state:
            self.ask("SAS1")
        else:
            self.ask("SAS0")


    def get_autostart(self):
        """Check if light is emitted on powerup."""
        return self.ask("SAS")


    def get_parameters(self):
        """Print a table showing laser status."""
        self.smart_ask("GOM")
        print("""Bit description:
        15  Auto PowerUP if ONE
        14  Autostart (emission at powerup) if ONE
        13  Adhoc USB - Laser sends info messages from time to time if ONE
        8   Power control (APC) mode if ONE; current control (ACC) if ZERO
        7   External analog input enabled if ONE
        4   Mod level: ONE - active; ZERO - not active
        3   Bias level: ONE - active; ZERO - not active

        Bits 0, 1, 2, 5, 6, 9, 10, 11, 12 are reserved
        """)


    def get_errors(self):
        """Print contents of failure byte"""
        self.smart_ask("GFB")
        print("""Bit description:
        15  Diode power exceeded maximum value
        14  An internal error occured
        12  The temperature at the diode exceeded the valid temperature range
        11  The ambient temperature exceeded the minimum or maximum value
        10  The current through the diode exceeded the maximum allowed value
        9   The interlock loop is not closed. Please close the interlockt loop
        8   Overvoltage or Undervoltage lockout occured. Bring supply voltage to a valid range
        4   If CDRH-Bit is set and no CDRH-Kit is connected or
            CDRH-Bit is not set but a CDRH-Kit is connected
            CDRH-Kit is a box with a key, a LED and an interlock
        0   Soft interlock: If an interlock error occurs, this bit is set. It can only be
            reset by resetting the whole system, even if the interlock error is
            not present anymore.

        Bits 1, 2, 3, 5, 6, 7, 13 are reserved
        """)


def stopwatch(func, *func_args, **func_kwargs):
    """Call **func** and print elapsed time"""
    start_time = time()
    result = func(*func_args, **func_kwargs)
    print("Time elapsed: %5.2f ms" % ((time() - start_time)*1000.0))
    return result


def print_hex(hex_code):
    """
    Print a nice table that represents *hex_code* (ASCII HEX string)
    in a binary code.

    Returns
    -------
    corresponding decimal numbers in array
    """
    # If the number is odd, pad it with leading zero
    length = len(hex_code)
    byte_number = (length/2) + (length % 2)
    if length % 2:
        hex_code = "0" + hex_code

    # Split it into 8-bit numbers coded in ASCII HEX
    hex_numbers = []
    for i in range(byte_number):
        hex_numbers.append(hex_code[i*2 : i*2+2])

    # Convert each of them into decimal
    decimals = []
    for hex_number in hex_numbers:
        decimals.append(int(hex_number, 16))

    # Print a table
    table = """BYTE ##  :  '?'
    | ## | ## | ## | ## | ## | ## | ## | ## |
    |----|----|----|----|----|----|----|----|
    |  ? |  ? |  ? |  ? |  ? |  ? |  ? |  ? |
    """
    table = table.replace("##", "%2i").replace("?", "%s")

    print("\nRepresentation of ASCII HEX '%s'" % hex_code)
    for i, number in enumerate(decimals):
        byte = len(decimals) - i - 1
        content = range(byte*8, byte*8+8)[::-1] + \
                                          list(bin(number)[2:].zfill(8))
        print(table % tuple([byte, hex_numbers[i]] + content))
    return decimals













