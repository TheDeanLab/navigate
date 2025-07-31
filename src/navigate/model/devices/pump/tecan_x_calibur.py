# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Standard Library Imports
import logging

# Third Party imports

# Local imports
from navigate.model.devices.device_types import SerialDevice

logger = logging.getLogger(__name__)

class TecanXCaliburPump(SerialDevice):
    """
    Driver for the Tecan Cavro XCalibur syringe pump.
    Uses ASCII DT protocol over RS-232 via USB-Serial adapter.
    """

    ERROR_CODES = {
        "0": "No error",
        "1": "Initialization error - pump failed to initialize",
        "2": "Invalid command",
        "3": "Invalid operand - bad parameter value",
        "4": "Invalid command sequence - check protocol structure",
        "5": "Fluid detection - leak sensor triggered",
        "6": "EEPROM failure - hardware fault",
        "7": "Device not initialized - run ZR command",
        "9": "Plunger overload - blocked or overpressured",
        "10": "Valve overload - valve blocked or slipping",
        "11": "Plunger move not allowed - valve in wrong position",
        "15": "Command overflow - too many characters in buffer"
    }  

    def __init__(
        self,
        device_name: str,
        port: str,
        baudrate: int = 9600,
        timeout: float = 0.5,
        min_speed_code: int = 0,
        max_speed_code: int = 40,
        fine_positioning: bool = False,
        **kwargs
    ):
        """
        Initialize the Tecan Cavro XCalibur pump driver.

        Parameters
        ----------
        device_name : str
            Identifier for the device within the system.
        port : str
            Serial port used to connect to the pump (e.g., 'COM3' or '/dev/ttyUSB0').
        baudrate : int, optional
            Serial baud rate for communication. Default is 9600.
        timeout : float, optional
            Serial read timeout in seconds. Default is 0.5.
        min_speed_code : int, optional
            Minimum allowed speed code for set_speed(). Default is 0 (fastest, 6000 pulses/sec).
        max_speed_code : int, optional
            Maximum allowed speed code for set_speed(). Default is 40 (slowest, 10 pulses/sec).
        fine_positioning : bool, optional
            If True, enables fine positioning mode (24,000 increments); else standard (3,000 increments).

        Notes
        -----
        Speed codes must be between 0 and 40 inclusive. Code 0 corresponds to the fastest
        movement, and code 40 to the slowest, based on internal pulse timing defined in
        the pump firmware.
        """
        super().__init__(device_name, port=port, baudrate=baudrate, timeout=timeout, **kwargs)

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.min_speed_code = min_speed_code
        self.max_speed_code = max_speed_code

        self.fine_positioning = fine_positioning

    def connect(self):
        """
        Connect to the Tecan pump and initialize it with ZR.
        """ 
        super().connect(self.port, self.baudrate, self.timeout)

        # Ensure pump is ready to receive motion commands. 
        # ZR stands for to "zero and reset".
        self.send_command("ZR")
        response = self.read_response()
        self.parse_response(response)

    def disconnect(self):
        """
        Close the serial connection to the pump.
        """
        if self.serial and self.serial.is_open:
            self.serial.close()
            logger.info(f"[{self.device_name}] Serial connection closed")
        else:
            logger.warning(f"[{self.device_name}] Serial already closed or uninitialized")
    
    def send_command(self, command: str):
        """
        Send a command string to the pump, appending carriage return.

        Parameters
        ----------
        command : str
            The ASCII command to send (without carriage return).

        Returns
        -------
        bytes
            The raw command sent, encoded as bytes.

        Raises
        ------
        RuntimeError
            If the serial connection is not established or write fails.
        """
        if not self.serial:
            raise RuntimeError(f"[{self.device_name}] Serial object is None")

        if not self.serial.is_open:
            raise RuntimeError(f"[{self.device_name}] Serial port not open")

        full_command = (command + "\r").encode("ascii")

        try:
            self.serial.write(full_command)
            logger.info(f"[{self.device_name}] Sent: {repr(full_command)}")
            return full_command
        except Exception as e:
            raise RuntimeError(f"[{self.device_name}] Error sending command {repr(command)}: {e}")
        
    def read_response(self, expected_bytes=32) -> str:
        """
        Read a response from the pump after sending a command.

        Parameters
        ----------
        expected_bytes : int
            How many bytes to attempt to read (or until timeout).

        Returns
        -------
        str
            The decoded response string.

        Raises
        ------
        RuntimeError
            If the serial connection is not open or the response is empty/invalid.
        """
        if not self.serial:
            raise RuntimeError(f"[{self.device_name}] Serial object is None")

        if not self.serial.is_open:
            raise RuntimeError(f"[{self.device_name}] Serial port not open")

        try:
            response = self.serial.read(expected_bytes)
            if not response:
                raise RuntimeError(f"[{self.device_name}] No response received (timeout or disconnected)")
            decoded = response.decode("ascii").strip()
            logger.info(f"[{self.device_name}] Received: {repr(decoded)}")
            
            return decoded
        
        except Exception as e:
            raise RuntimeError(f"[{self.device_name}] Error during read: {e}")

    def parse_response(self, response: str) -> str:
        """
        Parse the response string from the pump and extract the status code.

        The status code indicates whether the command was accepted (/0),
        or rejected due to a specific error (e.g. /1 = invalid command, /3 = not initialized).

        Parameters
        ----------
        response : str
            Full raw response string from the pump (e.g., "/00").

        Returns
        -------
        str
            Status code as a string ("0" = success, "1" = error, etc.)

        Raises
        ------
        RuntimeError
            If the response is malformed or indicates an error.
        """
        if not response.startswith("/"):
            raise RuntimeError(f"[{self.device_name}] Malformed response (missing start '/'): {repr(response)}")

        if len(response) < 3:
            raise RuntimeError(f"[{self.device_name}] Incomplete response: {repr(response)}")

        status_code = response[2]

        if status_code != "0":
            # Try to find error in dict of all known errors.
            error_message = self.ERROR_CODES.get(status_code, f"Unknown error code: {status_code}")
            
            raise RuntimeError(f"[{self.device_name}] Pump error /{status_code}: {error_message}")

        logger.info(f"[{self.device_name}] Status OK (/0)")
        return status_code
    
    def get_status(self):
        """Send the '?' command to query current pump status."""
        self.send_command("?")
        logger.info()

        return self.read_response()

    def move_absolute(self, position: int):
        """
        Move the syringe plunger to an absolute position.

        This method sends the 'A' (move Absolute) command to the pump,
        instructing it to move the plunger to the specified absolute position.
        The pump must be initialized and idle before this command can succeed.

        Parameters
        ----------
        position : int
            Target plunger position, in pump-specific units (e.g., microsteps or encoder units).
            Must be within the valid motion range defined by the pump configuration.

        Raises
        ------
        ValueError
            If the specified position is outside the allowed range.
        RuntimeError
            If the serial communication fails or the pump returns an error status.
        """
        max_pos = self.get_max_position()
        if not (0 <= position <= max_pos):
            raise ValueError(
                f"[{self.device_name}] Position {position} is out of bounds"
                f"(0–{max_pos}) for {'fine' if self.fine_positioning else 'standard'} mode"
            )

        self.send_command(f"A{position}")
        self.parse_response(self.read_response())

    def move_relative(self, steps: int):
        """
        Move the syringe plunger by a relative number of steps.

        This sends the 'M' (move Relative) command to the pump. The motion will be
        accepted as long as the resulting absolute position remains within the allowed
        range (0 to 3000 in standard mode, 0 to 24000 in fine positioning mode).

        Notes
        -----
        This method does not perform bounds checking. If the relative move would
        result in an invalid plunger position, the pump will reject the command and
        return an appropriate error status (e.g., plunger overtravel).

        Parameters
        ----------
        steps : int
            Number of increments to move. Positive = forward, negative = backward.

        Raises
        ------
        RuntimeError
            If the pump rejects the command or serial communication fails.
        """
        self.send_command(f"M{steps}")
        self.parse_response(self.read_response())

    def set_speed(self, speed: int):
        """
        Set the pump plunger speed using a predefined speed code.

        Sends the 'S' (Speed) command to configure the speed at which the
        plunger moves during subsequent operations. The speed is specified as
        an integer code between 0 and 40, which the pump firmware maps to a
        specific plunger velocity and stroke time.

        Speed code 0 corresponds to the fastest movement (6000 pulses/sec),
        and code 40 to the slowest (10 pulses/sec). These codes are defined by
        the internal firmware and can be constrained during driver initialization
        using 'min_speed_code' and 'max_speed_code'.

        Parameters
        ----------
        speed : int
            Speed code to set. Must be within the range defined by
            'self.min_speed_code' and 'self.max_speed_code'.

        Raises
        ------
        ValueError
            If the speed code is outside the allowed range.
        RuntimeError
            If the serial communication fails or the pump returns an error status.
        """
        if not (self.min_speed_code <= speed <= self.max_speed_code):
            raise ValueError(f"Speed code {speed} out of bounds ({self.min_speed_code}-{self.max_speed_code})")
        
        self.send_command(f"S{speed}")
        self.parse_response(self.read_response())

    def valve_input(self):
        """Move valve to input position (aspiration setup)."""
        self.send_command("I")
        self.parse_response(self.read_response())

    def valve_output(self):
        """Move valve to output position (dispensing setup)."""
        self.send_command("O")
        self.parse_response(self.read_response())

    def valve_bypass(self):
        """Move valve to bypass position (input connected directly to output)."""
        self.send_command("B")
        self.parse_response(self.read_response())

    def valve_extra(self):
        """Move valve to extra port (3-port distribution valve only)."""
        self.send_command("E")
        self.parse_response(self.read_response())

    def set_fine_positioning_mode(self, enable: bool = True):
        """
        Enable or disable fine positioning mode and update internal state.

        The pump must be initialized and idle before calling this method.

        Parameters
        ----------
        enable : bool
            If True, enables fine positioning mode (N1).
            If False, disables it (N0 - standard mode).
        """
        mode = "1" if enable else "0"
        self.send_command(f"N{mode}") # # Load fine positioning mode (1 = on, 0 = off) into the pump's command buffer.
        self.parse_response(self.read_response())
        
        self.send_command("R") # Execute the buffered configuration command to apply the mode change.
        self.parse_response(self.read_response())

        self.fine_positioning = enable
        logger.info(f"[{self.device_name}] Fine positioning set to: {enable}")

    def get_max_position(self):
        return 24000 if self.fine_positioning else 3000