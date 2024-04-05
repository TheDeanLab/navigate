# serialport.py
from serial import Serial
from serial import SerialException
from serial import SerialTimeoutException
from serial import EIGHTBITS
from serial import PARITY_NONE
from serial import STOPBITS_ONE
from serial.tools import list_ports
import threading

import time
from navigate.model.devices.APIs.asi.asi_tiger_controller import (
    TigerController
)

class TigerException(Exception):
    """
    Exception raised when error code from Tiger Console is received.

    Attributes:
        - command: error code received from Tiger Console
    """

    def __init__(self, code: str):
        """Initialize the TigerException class
        Parameters
        ----------
        code : str
            Error code received from Tiger Console
        """

        #: dict: Dictionary of error codes and their corresponding error messages
        self.error_codes = {
            ":N-1": "Unknown Command (Not Issued in TG-1000)",
            ":N-2": "Unrecognized Axis Parameter (valid axes are dependent on the "
            "controller)",
            ":N-3": "Missing parameters (command received requires an axis parameter "
            "such as x=1234)",
            ":N-4": "Parameter Out of Range",
            ":N-5": "Operation failed",
            ":N-6": "Undefined Error (command is incorrect, but the controller does "
            "not know exactly why.",
            ":N-7": "Invalid Card Address",
            ":N-21": "Serial Command halted by the HALT command",
        }
        #: str: Error code received from Tiger Console
        self.code = code

        #: str: Error message
        self.message = self.error_codes[code]

        # Gets the proper message based on error code received.
        super().__init__(self.message)
        # Sends message to base exception constructor for python purposes

    def __str__(self):
        """Overrides base Exception string to be displayed
        in traceback"""
        return f"{self.code} -> {self.message}"

class MFCTwoThousand(TigerController):
    def set_speed_as_percent_max(self, pct):
        """Set speed as a percentage of the maximum speed

        Parameters
        ----------
        pct : float
            Percentage of the maximum speed
        """
        if self.default_axes_sequence is None:
            raise TigerException(
                "Unable to query system for axis sequence. Cannot set speed."
            )
        if self._max_speeds is None:
            # First, set the speed crazy high
            self.send_command(
                f"SPEED {' '.join([f'{ax}=1000' for ax in self.default_axes_sequence])}\r"  # noqa
            )
            self.read_response()

            # Next query the maximum speed
            self.send_command(
                f"SPEED {' '.join([f'{ax}?' for ax in self.default_axes_sequence])}\r"
            )
            res = self.read_response()
            new_max_speed = float(res.split()[0].split("=")[1])
            print(f"new_max_speed: {new_max_speed}")
            self._max_speeds = [new_max_speed * 1000]

        # Now set to pct
        self.send_command(
            f"SPEED {' '.join([f'{ax}={pct*speed:.7f}' for ax, speed in zip(self.default_axes_sequence, self._max_speeds)])}\r"  # noqa
        )
        self.read_response()