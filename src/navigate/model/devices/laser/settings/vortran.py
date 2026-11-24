"""Vortran Stradus RS232 settings, using the documented ASCII protocol.

This adapter uses pyserial directly to avoid the upstream driver's duplicate
power writes and fault-query side effects. No emission, interlock, delay, or
nonvolatile save command is issued by this adapter.
"""

from math import floor, isclose, isfinite
import re
from threading import RLock
from time import monotonic
from typing import Any

import serial

from .base import LaserControlError, LaserMode, LaserSettingsBase, LaserStatus


class VortranLaserSettings(LaserSettingsBase):
    """Configure a Stradus through its RS232 port, not its native USB HID port.

    Parameters
    ----------
    connection : Any
        Open serial connection with finite read and write timeouts.
    """

    def __init__(self, connection: Any) -> None:
        #: Any: Owned RS232 connection.
        self.connection = connection
        #: RLock: Serializes complete command/readback transactions.
        self._lock = RLock()
        self._communication_failed = False
        try:
            timeout = connection.timeout
            if timeout is None or not isfinite(timeout) or timeout <= 0:
                raise ValueError("Vortran requires a positive, finite timeout.")
            self._timeout = float(timeout)
            connection.reset_input_buffer()
            self._request("ECHO=0")
            self._request("PROMPT=0")
            self._maximum_mw = self._number("?MAXP")
            if self._maximum_mw <= 0:
                raise LaserControlError("Vortran reported invalid maximum power.")
            self._identity = self._request("?LI")
        except Exception:
            connection.close()
            raise

    @classmethod
    def connect(
        cls, port: str, baudrate: int = 19200, timeout: float = 2.0
    ) -> "VortranLaserSettings":
        """Open an RS232 settings connection without enabling emission.

        Parameters
        ----------
        port : str
            Serial port name.
        baudrate : int, optional
            RS232 baud rate, normally 19200.
        timeout : float, optional
            Finite read and write timeout in seconds. Configuration writes can
            take about one second on Stradus firmware.

        Returns
        -------
        VortranLaserSettings
            Connected settings adapter.
        """
        if not port or not isfinite(timeout) or timeout <= 0:
            raise ValueError("Vortran needs a port and a positive, finite timeout.")
        return cls(
            serial.Serial(
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

    def _request(self, command: str) -> str:
        """Exchange one bounded, prefix-checked ASCII transaction."""
        key = command.lstrip("?").split("=", 1)[0]
        with self._lock:
            if self._communication_failed:
                raise LaserControlError(
                    "Reconnect Vortran after a serial communication failure."
                )
            try:
                self.connection.write((command + "\r").encode("ascii"))
                deadline = monotonic() + self._timeout
                while monotonic() < deadline:
                    reply = self.connection.read_until(b"\r\n", size=1024)
                    if not reply:
                        break
                    if not reply.endswith(b"\r\n"):
                        raise LaserControlError("Incomplete Vortran serial response.")
                    text = reply.decode("ascii").strip().lstrip(">").strip()
                    # A prompt from the previous command precedes the next frame
                    # until PROMPT=0 takes effect. Its status is not a reply.
                    text = re.sub(r"^Stradus:\d+>\s*", "", text)
                    if (
                        not text
                        or reply.endswith(b"\r\r\n")
                        or text == command
                        and command.startswith("?")
                    ):
                        continue
                    prefix, separator, value = text.partition("=")
                    if separator and prefix.strip().lstrip("?") == key:
                        return value.strip()
                    raise LaserControlError(f"Unexpected Vortran response: {text!r}")
            except (serial.SerialException, UnicodeError, LaserControlError) as error:
                self._communication_failed = True
                raise LaserControlError(
                    f"Vortran communication failed: {error}"
                ) from error
            self._communication_failed = True
        raise LaserControlError(f"Vortran timed out waiting for {key}.")

    def _number(self, command: str) -> float:
        """Read a finite numeric response."""
        try:
            value = float(self._request(command))
        except ValueError as error:
            raise LaserControlError("Vortran returned a nonnumeric value.") from error
        if not isfinite(value):
            raise LaserControlError("Vortran returned a nonfinite value.")
        return value

    def _flag(self, command: str) -> bool:
        """Read a strictly boolean protocol value."""
        value = self._number(command)
        if value not in (0, 1):
            raise LaserControlError(f"Vortran returned an invalid flag for {command}.")
        return bool(value)

    def get_supported_modes(self) -> frozenset[LaserMode]:
        """Return modes represented by the Stradus PUL and EPC controls.

        Digital modulation requires a laser equipped with that option. A device
        rejecting an optional mode is detected by the mode readback.
        """
        return frozenset(LaserMode)

    def get_power_limits_mw(self) -> tuple[float, float]:
        """Return the maximum queried at connection and the zero lower limit."""
        return 0.0, self._maximum_mw

    def get_mode(self) -> LaserMode:
        """Read the external analog and digital modulation flags."""
        with self._lock:
            analog = self._flag("?EPC")
            digital = self._flag("?PUL")
            return {
                (False, False): LaserMode.CW,
                (False, True): LaserMode.DIGITAL,
                (True, False): LaserMode.ANALOG,
                (True, True): LaserMode.MIXED,
            }[analog, digital]

    def set_mode(self, mode: LaserMode) -> None:
        """Set modulation flags and verify them with illumination blocked."""
        try:
            mode = LaserMode(mode)
        except ValueError as error:
            raise LaserControlError(f"Unsupported laser mode: {mode!r}") from error
        with self._lock:
            digital = mode in (LaserMode.DIGITAL, LaserMode.MIXED)
            analog = mode in (LaserMode.ANALOG, LaserMode.MIXED)
            # PUL and PP require power control; C=1 makes this firmware reject
            # digital modulation even though the current-control write succeeds.
            self._request("C=0")
            self._request(f"PUL={int(digital)}")
            self._request(f"EPC={int(analog)}")
            if self.get_mode() != mode or self._flag("?C"):
                raise LaserControlError(f"Vortran did not accept {mode.value} mode.")

    def get_power_setpoint_mw(self) -> float:
        """Read CW setpoint or calibrated peak pulse power, in mW."""
        with self._lock:
            return self._number("?PP" if self._flag("?PUL") else "?LPS")

    def set_power_mw(self, power_mw: float) -> float:
        """Write the mode-appropriate setting once and verify its readback.

        Stradus firmware may reject changes when emission is not already enabled.
        This method reports that condition; it never enables emission to apply a
        setting. Analog and mixed modes use external voltage for amplitude.
        """
        with self._lock:
            requested = self.validate_power(power_mw)
            mode = self.get_mode()
            if mode not in (LaserMode.CW, LaserMode.DIGITAL):
                raise LaserControlError(
                    "Vortran external analog control overrides serial power."
                )
            if not self._flag("?LE"):
                raise LaserControlError(
                    "Enable the Vortran laser before setting its power."
                )
            if self._flag("?C"):
                raise LaserControlError(
                    "Vortran power requires constant-power control (C=0)."
                )
            # Firmware 3.2.0 stores PP in whole mW, while LP supports tenths.
            # Quantize before sending so a fractional request is not silently
            # truncated by the device. Never round above its maximum.
            scale = 1 if mode == LaserMode.DIGITAL else 10
            target = (
                min(round(requested * scale), floor(self._maximum_mw * scale)) / scale
            )
            command = "PP" if mode == LaserMode.DIGITAL else "LP"
            self._number(f"{command}={target:.1f}")
            confirmed = self.get_power_setpoint_mw()
            if not isclose(confirmed, target, rel_tol=0, abs_tol=0.11):
                raise LaserControlError(
                    f"Vortran power readback {confirmed} mW does not match {target} mW."
                )
            return confirmed

    def get_status(self) -> LaserStatus:
        """Read status without the fault query that clears stored fault flags."""
        with self._lock:
            return {
                "identity": self._identity,
                "simulated": False,
                "emission_enabled": self._flag("?LE"),
                "measured_power_mw": self._number("?LP"),
            }

    def close(self) -> None:
        """Close RS232 without changing the externally managed emission state."""
        with self._lock:
            self.connection.close()
