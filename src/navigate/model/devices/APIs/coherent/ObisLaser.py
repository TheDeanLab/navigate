"""Coherent OBIS LX/LS SCPI API; power values at this layer are watts.

Protocol reference: Coherent OBIS LX/LS Operator's Manual, Host Interface.
This API is independent of Navigate's acquisition laser interface.
"""

from math import isfinite
from typing import Any, Optional

from navigate.model.devices.APIs.laser_serial import SerialLaserAPI
from navigate.model.devices.laser.settings.base import LaserControlError


class ObisLaser(SerialLaserAPI):
    """Open OBIS RS232 without changing emission, power or modulation mode.

    Parameters
    ----------
    port : str, optional
        Serial port name.
    baudrate : int, optional
        Serial baud rate; OBIS defaults to 115200.
    timeout : float, optional
        Bounded transaction timeout in seconds.
    connection : object, optional
        Owned serial connection supplied for protocol testing.
    """

    def __init__(
        self,
        port: str = "COM4",
        baudrate: int = 115200,
        timeout: float = 0.5,
        *,
        connection: Optional[Any] = None,
    ) -> None:
        super().__init__(port, baudrate, timeout, connection)
        try:
            self.ask("SYSTem:COMMunicate:HANDshaking ON")
            self.ask("SYSTem:COMMunicate:PROMpt OFF")
        except Exception:
            self.close()
            raise

    def ask(self, command: str) -> str:
        """Exchange a complete SCPI command, data reply and OK/ERR handshake.

        Parameters
        ----------
        command : str
            SCPI query or command without its terminator.

        Returns
        -------
        str
            Query data, or an empty string for an acknowledged command.
        """
        with self._lock:
            deadline = self._send((command + "\r").encode("ascii"))
            response = None
            while True:
                try:
                    frame = self._read_frame(deadline).decode("ascii").lstrip("> ")
                except UnicodeError:
                    self._fail("Non-ASCII OBIS response.")
                if not frame or frame == command:
                    continue
                if frame.startswith("ERR"):
                    raise LaserControlError(f"OBIS rejected {command!r}: {frame}")
                if frame == "OK":
                    if "?" in command and response is None:
                        self._fail("OBIS query returned no data.")
                    return response or ""
                if "?" not in command or response is not None:
                    self._fail(f"Unexpected OBIS response: {frame!r}")
                response = frame

    def get_laser_model(self) -> str:
        """Return the manufacturer, device identity and firmware string."""
        return self.ask("*IDN?")

    def get_laser_wavelength(self) -> str:
        """Return the wavelength in nm."""
        return self.ask("SYSTem:INFormation:WAVelength?")

    def get_minimum_laser_power(self) -> str:
        """Return the minimum power limit in watts."""
        return self.ask("SOURce:POWer:LIMit:LOW?")

    def get_maximum_laser_power(self) -> str:
        """Return the maximum power limit in watts."""
        return self.ask("SOURce:POWer:LIMit:HIGH?")

    def get_laser_power(self) -> str:
        """Return measured output power in watts, distinct from its setpoint."""
        return self.ask("SOURce:POWer:LEVel?")

    def get_power_setpoint(self) -> str:
        """Return the internal power setting in watts."""
        return self.ask("SOURce:POWer:LEVel:IMMediate:AMPLitude?")

    def set_laser_power(self, power: float) -> None:
        """Set the internal power in watts without enabling emission.

        Parameters
        ----------
        power : float
            Nonnegative finite power in watts; caller validates device limits.
        """
        if not isfinite(power) or power < 0:
            raise LaserControlError("OBIS power must be nonnegative and finite.")
        self.ask(f"SOURce:POWer:LEVel:IMMediate:AMPLitude {power:.9f}")

    def get_ext_control(self) -> str:
        """Return the external control status."""
        return self.ask("SYSTem:EXTernal:CONTRol?")

    def get_laser_status(self) -> str:
        """Return the raw status register for existing API clients."""
        return self.ask("SOURce:STATus?")

    def get_emission_enabled(self) -> bool:
        """Read emission enable separately from the general status register."""
        reply = self.ask("SOURce:AM:STATe?").upper()
        if reply not in ("ON", "OFF"):
            self._fail("Invalid OBIS emission readback.")
        return reply == "ON"

    def set_laser_operating_mode(self, mode: str) -> None:
        """Select an OBIS mode without enabling emission.

        Parameters
        ----------
        mode : str
            CWP, CWC, digital, analog, mixed, DIGSO or MIXSO.
        """
        mode = mode.upper()
        if mode in ("CWP", "CWC"):
            self.ask(f"SOURce:AM:INTernal {mode}")
        elif mode in ("DIGITAL", "ANALOG", "MIXED", "DIGSO", "MIXSO"):
            self.ask(f"SOURce:AM:EXTernal {mode}")
        else:
            raise LaserControlError(f"Unsupported OBIS mode: {mode}")

    def get_laser_operating_mode(self) -> str:
        """Return the current OBIS operating mode token."""
        return self.ask("SOURce:AM:SOURce?").upper()

    def initialize_laser(self) -> None:
        """Explicit legacy initialization; adapters never call this method."""
        self.set_laser_operating_mode("mixed")
        self.set_laser_power(float(self.get_maximum_laser_power()))
