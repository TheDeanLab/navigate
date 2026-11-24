"""Bounded serial transport shared by the OBIS and LuxX protocol APIs."""

from math import isfinite
from threading import RLock
from time import monotonic
from typing import Any, NoReturn, Optional

import serial

from navigate.model.devices.laser.settings.base import LaserControlError


class SerialLaserAPI:
    """Own a serial connection without changing laser emission.

    Parameters
    ----------
    port : str
        Serial port name.
    baudrate : int
        Device-specific baud rate.
    timeout : float
        Maximum duration of one response, in seconds.
    connection : object, optional
        Existing serial connection, primarily for protocol tests. Ownership is
        transferred to this API.
    """

    def __init__(
        self, port: str, baudrate: int, timeout: float, connection: Optional[Any] = None
    ) -> None:
        if not isfinite(timeout) or timeout <= 0 or baudrate <= 0:
            raise ValueError("Laser baud rate and timeout must be positive and finite.")
        self.timeout = float(timeout)
        self._lock = RLock()
        self._failed = False
        self._closed = False
        #: serial.Serial: Owned serial connection with bounded reads and writes.
        self.laser = (
            connection
            if connection is not None
            else serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                write_timeout=timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=False,
            )
        )
        try:
            self.laser.timeout = timeout
            self.laser.write_timeout = timeout
            self.laser.reset_input_buffer()
        except Exception:
            self.close()
            raise

    def _send(self, data: bytes) -> float:
        """Send a frame and return its response deadline under the caller's lock."""
        if self._closed or self._failed:
            raise LaserControlError(
                "Reconnect the laser after a closed or failed serial connection."
            )
        try:
            if self.laser.write(data) != len(data):
                self._fail("Incomplete laser serial write.")
        except (serial.SerialException, OSError) as error:
            self._fail(f"Laser serial write failed: {error}")
        return monotonic() + self.timeout

    def _read_frame(self, deadline: float) -> bytes:
        """Read one complete CR-terminated frame within the transaction deadline."""
        while monotonic() < deadline:
            try:
                self.laser.timeout = max(0.001, deadline - monotonic())
                frame = self.laser.read_until(b"\r", size=1024)
            except (serial.SerialException, OSError) as error:
                self._fail(f"Laser serial read failed: {error}")
            if not frame or not frame.endswith(b"\r"):
                self._fail("Missing or incomplete laser serial response.")
            frame = frame.strip()
            if frame:
                return frame
        self._fail("Laser serial response timed out.")

    def _fail(self, message: str) -> NoReturn:
        """Prevent late replies from being accepted by subsequent transactions."""
        self._failed = True
        raise LaserControlError(message)

    def close(self) -> None:
        """Release the connection once without sending emission commands."""
        with self._lock:
            if not self._closed:
                self._closed = True
                self.laser.close()

    def __del__(self) -> None:
        """Best-effort cleanup, including partially initialized API objects."""
        try:
            self.close()
        except Exception:
            pass
