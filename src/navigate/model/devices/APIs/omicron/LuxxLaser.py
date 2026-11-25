"""Omicron LuxX serial API, independent of acquisition gating.

The original LuxX exposes Standby, CW-ACC, CW-APC and Analog through ROM.
The electronic shutter input is separate from these software mode selections.
"""

from math import isfinite
from typing import Any, Optional, Union

from navigate.model.devices.APIs.laser_serial import SerialLaserAPI
from navigate.model.devices.laser.settings.base import LaserControlError


class LuxxLaser(SerialLaserAPI):
    """Connect and read identity/limits without initializing emission or power.

    Parameters
    ----------
    comport : str
        Serial port name.
    baudrate : int, optional
        Baud rate, retaining the existing API default of 500000.
    timeout : float, optional
        Bounded transaction timeout in seconds.
    connection : object, optional
        Owned serial connection supplied for protocol testing.
    """

    MODES = ("Standby", "CW-ACC", "CW-APC", "Analog")

    def __init__(
        self,
        comport: str,
        baudrate: int = 500000,
        timeout: float = 0.3,
        *,
        connection: Optional[Any] = None,
    ) -> None:
        self.comport = comport
        self.baudrate = baudrate
        super().__init__(comport, baudrate, timeout, connection)
        try:
            # GSI separates wavelength and rated power with a single 0xA7 byte.
            self.wavelength = self._number(self.ask("GSI").split(b"\xa7", 1)[0])
            self.serial = self.ask("GSN").decode("ascii")
            self.hours = self.ask("GWH").decode("ascii")
            self.pmax = self._number(self.ask("GMP"))
            if self.pmax <= 0:
                raise LaserControlError("LuxX reported an invalid maximum power.")
        except Exception:
            self.close()
            raise

    def write(self, command: str) -> None:
        """Write and consume the acknowledgment so later queries stay aligned."""
        self.ask(command)

    def ask(self, command: str) -> bytes:
        """Exchange one bounded command with a matching response prefix.

        Parameters
        ----------
        command : str
            Three-letter command and optional value, without '?' or CR.

        Returns
        -------
        bytes
            Response payload, preserving GSI's non-ASCII separator.
        """
        with self._lock:
            wire = ("?" + command + "\r").encode("ascii")
            deadline = self._send(wire)
            prefix = ("!" + command[:3]).encode("ascii")
            while True:
                response = self._read_frame(deadline)
                if response == wire.strip():
                    continue
                if response == b"!UK":
                    raise LaserControlError(f"LuxX does not support {command!r}.")
                if not response.startswith(prefix):
                    self._fail(f"Unexpected LuxX response: {response!r}")
                value = response[len(prefix) :].strip()
                if not value:
                    self._fail("LuxX returned an empty response.")
                if value.lower().startswith((b"x", b"err")):
                    raise LaserControlError(f"LuxX rejected {command!r}: {value!r}")
                return value

    @staticmethod
    def _number(value: bytes) -> float:
        """Reject nonnumeric or nonfinite telemetry."""
        try:
            number = float(value)
        except (TypeError, ValueError) as error:
            raise LaserControlError("Invalid LuxX numeric response.") from error
        if not isfinite(number):
            raise LaserControlError("Nonfinite LuxX numeric response.")
        return number

    def _hex(self, command: str, maximum: int = 0xFFFF) -> int:
        """Read a bounded hexadecimal register value."""
        try:
            value = int(self.ask(command), 16)
        except ValueError as error:
            raise LaserControlError("Invalid LuxX hexadecimal response.") from error
        if not 0 <= value <= maximum:
            raise LaserControlError("LuxX register readback is out of range.")
        return value

    def power_code(self, power: float) -> int:
        """Convert a valid mW request to the existing 12-bit power scale."""
        if not isfinite(power) or not 0 <= power <= self.pmax:
            raise LaserControlError(
                f"LuxX power must be between 0 and {self.pmax:g} mW."
            )
        return int(4095 * power / self.pmax)

    def set_power(self, power: float) -> None:
        """Set internal power without enabling emission or silently clamping.

        Parameters
        ----------
        power : float
            Requested power in mW.
        """
        self.ask(f"SLP{self.power_code(power):03X}")

    def get_power(self) -> float:
        """Return the internal power setpoint in mW, not measured output."""
        return self._hex("GLP", 0xFFF) * self.pmax / 4095.0

    def get_measured_power(self) -> float:
        """Return measured diode output power in mW."""
        return self._number(self.ask("MDP"))

    def get_emission_enabled(self) -> bool:
        """Read GAS bit 1, the laser operation enable flag."""
        return bool(self._hex("GAS") & 2)

    def set_mode(self, mode: Union[str, int]) -> None:
        """Select an existing LuxX ROM mode.

        Parameters
        ----------
        mode : str or int
            Standby, CW-ACC, CW-APC, Analog, or their numeric indices 0–3.
        """
        if isinstance(mode, str) and mode in self.MODES:
            mode = self.MODES.index(mode)
        if isinstance(mode, bool) or not isinstance(mode, int) or mode not in range(4):
            raise LaserControlError(f"Unsupported LuxX mode: {mode!r}")
        self.ask(f"ROM{mode}")

    def get_mode(self) -> str:
        """Return the current ROM mode, rejecting invalid device replies."""
        try:
            value = int(self.ask("ROM"))
        except ValueError as error:
            raise LaserControlError("Invalid LuxX mode readback.") from error
        if value not in range(4):
            raise LaserControlError(f"Unknown LuxX ROM mode: {value}")
        return self.MODES[value]

    def start(self) -> None:
        """Explicitly enable emission for legacy API clients; adapters never call."""
        self.write("LOn")

    def stop(self) -> None:
        """Explicitly disable emission for legacy API clients; adapters never call."""
        self.write("LOf")

    def set_autostart(self, state: bool) -> None:
        """Set emission on power-up for explicit legacy API clients only."""
        self.ask(f"SAS{int(bool(state))}")

    def get_autostart(self) -> bool:
        """Read the GOM autostart flag; GAS is a different status register."""
        return bool(self._hex("GOM") & (1 << 14))

    def smart_ask(self, command: str) -> Union[list[int], bytes]:
        """Return register byte values or the original payload."""
        value = self.ask(command)
        return print_hex(value) if command in ("GOM", "GFB", "GLF", "GLP") else value

    def get_parameters(self) -> list[int]:
        """Return operating-register bytes for legacy API clients."""
        return print_hex(self.ask("GOM"))

    def get_errors(self) -> list[int]:
        """Return fault-register bytes for explicit legacy API clients."""
        return print_hex(self.ask("GFB"))

    def initialize_laser(self) -> None:
        """Explicit legacy initialization; settings adapters never call this."""
        self.set_power(self.pmax)
        self.set_mode("CW-APC")
        self.start()


def stopwatch(func: Any, *func_args: Any, **func_kwargs: Any) -> Any:
    """Retain the legacy forwarding helper without console output."""
    return func(*func_args, **func_kwargs)


def print_hex(hex_code: Union[str, bytes]) -> list[int]:
    """Decode ASCII hexadecimal register bytes without printing debug output."""
    value = hex_code.decode("ascii") if isinstance(hex_code, bytes) else hex_code
    if len(value) % 2:
        value = "0" + value
    return list(bytes.fromhex(value))
