"""
https://pypi.org/project/luxx_communication/

"""

import serial
import time
import re

class LuxxLaser():
    def __init__(self, comport = 'COM19', baudrate=500000, read_on_init=True):

        # Load the Default Parameters
        self.comport = comport
        self.baudrate = baudrate
        self.verbose = True

        # Delay in s for the wait until done function
        self.wait_until_done_delay = 0.500

        # Open Serial Port
        try:
            if self.verbose:
                print('Opening Serial Port')
            self.serial = serial.Serial(self.comport, self.baudrate, timeout=.25)
        except serial.SerialException:
            raise UserWarning('Could not communicate with Luxx via ' + self.comport)

        # Check to see if the initialization sequence has finished.
        if read_on_init:
            self.init_finished = True
            if self.verbose:
                print('Done initializing Luxx laser on ' + self.comport)
        else:
            self.init_finished = False


    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.verbose:
            print('Closing the Luxx Serial Port')
        self.close()

    def get_firmware_version(self):
        """
        Ask for the model code, device ID and firmware version
        Provides answer as following: ! G F w ModelCode § Device-ID § Firmware cr
        0xa7 = Section Sign

        """
        command = "GFw"
        command_response = self.ask(command)
        if self.verbose:
            print("Command Received from Firmware Check: ", command_response)
        model_code = command_response[4:8].decode()
        device_id = command_response[2:4].decode()
        firmware = command_response[4:8].decode()

        print("Model Code:", model_code)
        print("Device ID:", device_id)
        print("Firmware:", firmware)

        # 0xa7, xa74, and xa72 are ascii extended characters that are not supported by Python.
        #answer = answer.replace(b'\0xa7', b'')
        #answer = answer.replace(b'\xa74', b'')
        #answer = answer.replace(b'\xa72', b'')

        # Convert it to a string
        #answer = answer.decode(

        # return self.firmware

    def write(self, command):
        """Send command to device.
         Command proceeds with a ?, and ends with a \r
         """
        command = str("?").encode() + str(command).encode() + str("\r").encode()
        self.serial.write(command)
        if self.verbose:
            print("Command Sent", command)

    def read(self):
        """
        Read all information from the port and return it as string.
        Port by default reads a hexadecimal code in type bytes
        """
        answer = self.serial.readall()
        if self.verbose:
            print("Command Received", answer)
        return answer


    def ask(self, command):
        """
        Write, then read. However, return only the relevant info.
        """
        self.write(command)
        response = self.read()

        # Use regular expressions to clean up response
        # An unknown command or an incomplete command is followed by a “!UK” answer
        if re.findall(b"!UK\n", response):
            print("Command '%s' is unknown for this device" % command)
        else:
            # Confirm that the !CMd\n command is complete
            #TODO: Figure this shit out.
            response = re.findall(b"!%s(.+)\n" % command[:3], response)[-1]
            if response[0] == "x":
                print("Laser responded with error to command '%s'" % command)
            return response
        #return response

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
            code = hex(int(4095 * power / self.pmax))[2:].upper().zfill(3)
            stopwatch(self.ask, "SLP%s" % code)

    def get_power(self):
        """Get the current power value in mW"""
        code = stopwatch(self.ask, "GLP")
        return int(code, 16) * self.pmax / 4095.

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
        print("Time elapsed: %5.2f ms" % ((time() - start_time) * 1000.0))
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
        byte_number = (length / 2) + (length % 2)
        if length % 2:
            hex_code = "0" + hex_code

        # Split it into 8-bit numbers coded in ASCII HEX
        hex_numbers = []
        for i in range(byte_number):
            hex_numbers.append(hex_code[i * 2: i * 2 + 2])

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
            content = range(byte * 8, byte * 8 + 8)[::-1] + \
                      list(bin(number)[2:].zfill(8))
            print(table % tuple([byte, hex_numbers[i]] + content))
        return decimals

    def close(self):
        try:
            self.serial.close()
            if self.verbose:
                print('Closing the Luxx Serial Port')
        except serial.SerialException:
            print('Could not Close the Luxx Serial Port')




# Filter Wheel Testing.
if (__name__ == "__main__"):

    laser1 = LuxxLaser()
    laser1.get_firmware_version()
    laser1.close()
    print('Done')

# self.wavelength = float(self.ask("GSI").split()[0])
# self.serial = self.ask("GSN")
# self.hours = self.ask("GWH")
# self.pmax = float(self.ask("GMP"))
# print("Laser Wavelength:", self.wavelength, "nm")
# print("Laser Serial Number:", self.serial)
# print("Laser Hours:", self.hours)
# print("Laser Max Power:", self.pmax, "mW")