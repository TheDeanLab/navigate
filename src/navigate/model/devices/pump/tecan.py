# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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
from typing import Any, Dict

# Third Party imports
from serial import Serial

# Local imports
from navigate.model.devices.configuration_schema import SettingSpec
from navigate.model.devices.device_types import SerialDevice
from navigate.model.devices.pump.base import PumpBase
from navigate.model.utils.exceptions import UserVisibleException

# Initialize logger
logger = logging.getLogger(__name__)


class XCaliburPump(PumpBase, SerialDevice):
    """
    Driver for the Tecan Cavro XCalibur syringe pump.
    Uses ASCII DT protocol over RS-232 via USB-Serial adapter.
    """

    configuration_schema = {
        "min_speed_code": SettingSpec(
            int,
            default=0,
            label="Minimum Speed Code",
            help_text="Lowest allowed pump speed code (0 is the fastest).",
            minimum=0,
            maximum=40,
            step=1,
            required=False,
        ),
        "max_speed_code": SettingSpec(
            int,
            default=40,
            label="Maximum Speed Code",
            help_text="Highest allowed pump speed code (40 is the slowest).",
            minimum=0,
            maximum=40,
            step=1,
            required=False,
        ),
        "fine_positioning": SettingSpec(
            bool,
            default=False,
            label="Fine Positioning",
            help_text="Enable the pump's fine-positioning mode.",
            required=False,
        ),
    }

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
        "15": "Command overflow - too many characters in buffer",
    }

    def __init__(
        self,
        microscope_name: str,
        device_connection: Any,
        configuration: Dict[str, Any],
        device_id: int = 0,
    ) -> None:
        """
        Initialize the XCaliburPump.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope system using this device.
        device_connection : Serial
            Pre-established serial connection (created via `connect()` class method).
        configuration : dict
            Device-specific configuration dictionary from YAML.
        device_id : int, optional
            Identifier if multiple pumps of same type are used.
        """
        #: str: Name of the microscope system using this device.
        self.device_name = microscope_name

        #: Serial: Pre-established serial connection to the pump.
        self.serial = device_connection

        #: dict: Configuration dictionary from YAML.
        self.configuration = configuration

        #: int: Identifier for this pump instance (if multiple pumps are used).
        self.device_id = device_id

        # Safe fallback values. Ensures the code will work before the pump section is
        # added to configuration file.
        #: int: Minimum speed code for plunger movement. Default is 0.
        self.min_speed_code = configuration.get("min_speed_code", 0)

        #: int: Maximum speed code for plunger movement. Default is 40.
        self.max_speed_code = configuration.get("max_speed_code", 40)

        #: bool: Whether the pump is in fine positioning mode.
        self.fine_positioning = configuration.get("fine_positioning", False)

        # Optionally store port/baudrate for logging/debugging
        #: str: Serial port name (e.g., '/dev/ttyUSB0').
        self.port = getattr(self.serial, "port", "Unknown")

        #: int: Baudrate for the serial connection (e.g., 9600).
        self.baudrate = getattr(self.serial, "baudrate", "Unknown")

        #: str: Timeout for the serial connection (e.g., 0.25 seconds).
        self.timeout = getattr(self.serial, "timeout", "Unknown")

    @classmethod
    def connect(cls, port: str, baudrate: int = 9600, timeout: float = 0.25) -> Serial:
        """
        Create a new Serial connection to the pump.

        Parameters
        ----------
        port : str
            The serial port to connect to (e.g., '/dev/ttyUSB0').
        baudrate : int, optional
            The baud rate for the serial connection (default is 9600).
        timeout : float, optional
            The timeout for read operations (default is 0.25 seconds).

        Returns
        -------
        Serial
            An open Serial object connected to the specified port.
        """

        return Serial(port=port, baudrate=baudrate, timeout=timeout)

    def initialize_pump(self) -> None:
        """
        Send the 'ZR' (Zero and Reset) command to initialize the pump state.

        This is typically called at startup to ensure the pump is in a known
        idle state and the plunger position is zeroed.

        It's not strictly required before all commands, but it's good practice,
        especially after power-on or fault conditions.
        """
        self.send_command("ZR")
        response = self.read_response()
        self.parse_response(response)

    def disconnect(self) -> None:
        """
        Close the serial connection to the pump.
        """
        if self.serial and self.serial.is_open:
            self.serial.close()
            logger.info(f"[{self.device_name}] Serial connection closed")
        else:
            logger.warning(
                f"[{self.device_name}] Serial already closed or uninitialized"
            )

    def send_command(self, command: str) -> bytes:
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
        UserVisibleException
            If the serial connection is not established or the write fails.
        """
        if not self.serial:
            raise UserVisibleException(f"[{self.device_name}] Serial object is None")

        if not self.serial.is_open:
            raise UserVisibleException(f"[{self.device_name}] Serial port not open")

        full_command = (command + "\r").encode("ascii")

        try:
            self.serial.write(full_command)
            logger.debug(f"[{self.device_name}] Sent: {repr(full_command)}")
            return full_command
        except Exception as e:
            raise UserVisibleException(
                f"[{self.device_name}] Error sending command {repr(command)}: {e}"
            )

    def read_response(self, expected_bytes: int = 32) -> str:
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
        UserVisibleException
            If the serial connection is not open, the response is empty,
            or a decoding error occurs.
        """
        if not self.serial:
            raise UserVisibleException(f"[{self.device_name}] Serial object is None")

        if not self.serial.is_open:
            raise UserVisibleException(f"[{self.device_name}] Serial port not open")

        try:
            response = self.serial.read(expected_bytes)
            if not response:
                raise UserVisibleException(
                    f"[{self.device_name}] No response received (timeout or disconnected)"
                )
            decoded = response.decode("ascii").strip()
            logger.debug(f"[{self.device_name}] Received: {repr(decoded)}")

            return decoded

        except Exception as e:
            raise UserVisibleException(f"[{self.device_name}] Error during read: {e}")

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
        UserVisibleException
            If the response is malformed or indicates a hardware error.
        """
        if not response.startswith("/"):
            raise UserVisibleException(
                f"[{self.device_name}] Malformed response (missing start '/'): {repr(response)}"
            )

        if len(response) < 3:
            raise UserVisibleException(
                f"[{self.device_name}] Incomplete response: {repr(response)}"
            )

        status_code = response[2]

        if status_code != "0":
            # Try to find error in dict of all known errors.
            error_message = self.ERROR_CODES.get(
                status_code, f"Unknown error code: {status_code}"
            )

            raise UserVisibleException(
                f"[{self.device_name}] Pump error /{status_code}: {error_message}"
            )

        logger.info(f"[{self.device_name}] Status OK (/0)")
        return status_code

    def get_status(self) -> str:
        """Send the '?' command to query current pump status."""
        self.send_command("?")
        logger.info(f"[{self.device_name}] Queried current pump status")

        return self.read_response()

    def move_absolute(self, position: int) -> None:
        """
        Move the syringe plunger to an absolute position.

        Sends the 'A' (move Absolute) command to the pump,
        instructing it to move the plunger to the specified absolute position.

        Parameters
        ----------
        position : int
            Target plunger position, in pump-specific units (e.g., microsteps or encoder units).
            Must be within the valid motion range defined by the pump configuration.

        Raises
        ------
        UserVisibleException
            If the specified position is out of bounds or if the pump returns an error status.
        """
        max_pos = self.get_max_position()
        if not (0 <= position <= max_pos):
            raise UserVisibleException(
                f"[{self.device_name}] Position {position} is out of bounds "
                f"(0–{max_pos}) for {'fine' if self.fine_positioning else 'standard'} mode"
            )

        self.send_command(f"A{position}")
        self.parse_response(self.read_response())

    def move_relative(self, steps: int) -> None:
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
        UserVisibleException
            If the pump rejects the command or serial communication fails.
        """
        self.send_command(f"M{steps}")
        self.parse_response(self.read_response())

    def set_speed(self, speed: int) -> None:
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
        UserVisibleException
            If the speed code is out of bounds or the command is rejected.
        """
        if not (self.min_speed_code <= speed <= self.max_speed_code):
            raise UserVisibleException(
                f"Speed code {speed} out of bounds ({self.min_speed_code}-{self.max_speed_code})"
            )
        self.send_command(f"S{speed}")
        self.parse_response(self.read_response())

    def valve_input(self) -> None:
        """Move valve to input position (aspiration setup).

        Raises
        ------
        UserVisibleException
            If the valve command fails or the pump returns an error.
        """
        self.send_command("I")
        self.parse_response(self.read_response())

    def valve_output(self) -> None:
        """Move valve to output position (dispensing setup).

        Raises
        ------
        UserVisibleException
            If the valve command fails or the pump returns an error.

        """
        self.send_command("O")
        self.parse_response(self.read_response())

    def valve_bypass(self) -> None:
        """Move valve to bypass position (input connected directly to output).

        Raises
        ------
        UserVisibleException
            If the valve command fails or the pump returns an error.
        """
        self.send_command("B")
        self.parse_response(self.read_response())

    def valve_extra(self) -> None:
        """Move valve to extra port (3-port distribution valve only).

        Raises
        ------
        UserVisibleException
            If the valve command fails or the pump returns an error.
        """
        self.send_command("E")
        self.parse_response(self.read_response())

    def set_fine_positioning_mode(self, enable: bool = True) -> None:
        """
        Enable or disable fine positioning mode and update internal state.

        The pump must be initialized and idle before calling this method.

        Parameters
        ----------
        enable : bool
            If True, enables fine positioning mode (N1).
            If False, disables it (N0 - standard mode).

        Raises
        ------
        UserVisibleException
            If the pump rejects the configuration command or fails to apply it.
        """
        mode = "1" if enable else "0"
        # Load fine positioning mode (1 = on, 0 = off) into the pump's command buffer.
        self.send_command(f"N{mode}")
        self.parse_response(self.read_response())

        # Execute the buffered configuration command to apply the mode change.
        self.send_command("R")
        self.parse_response(self.read_response())

        self.fine_positioning = enable
        logger.info(f"[{self.device_name}] Fine positioning set to: {enable}")

    def get_max_position(self) -> int:
        """Return the maximum allowed plunger position based on positioning mode.

        Returns
        -------
        int
            Maximum plunger position in microsteps or encoder units.
        """
        return 24000 if self.fine_positioning else 3000
