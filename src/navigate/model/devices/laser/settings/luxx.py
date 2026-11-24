"""Omicron LuxX settings adapter using its existing serial API."""

from math import isclose

from navigate.model.devices.APIs.omicron.LuxxLaser import LuxxLaser
from .base import (
    LaserControlError,
    LaserMode,
    LaserModeUnavailableError,
    LaserSettingsBase,
    LaserStatus,
)


class LuxxLaserSettings(LaserSettingsBase):
    """Adapt original LuxX CW/analog modes and 12-bit power settings.

    Parameters
    ----------
    api : LuxxLaser
        Connected API owned by this adapter. Digital gating remains on the
        separate electrical laser-enable input, controlled by NI/ASI.
    """

    def __init__(self, api: LuxxLaser) -> None:
        self.api = api
        self._lock = api._lock

    @classmethod
    def connect(
        cls, port: str, baudrate: int = 500000, timeout: float = 0.5
    ) -> "LuxxLaserSettings":
        """Connect through LuxxLaser without calling its emission initializer."""
        return cls(LuxxLaser(port, baudrate=baudrate, timeout=timeout))

    def get_supported_modes(self) -> frozenset[LaserMode]:
        """Advertise only modes supported by the original LuxX ROM interface."""
        return frozenset((LaserMode.CW, LaserMode.ANALOG))

    def get_power_limits_mw(self) -> tuple[float, float]:
        """Return zero and the queried maximum power in mW."""
        return 0.0, self.api.pmax

    def get_mode(self) -> LaserMode:
        """Read the modulation category; standby is not an acquisition mode."""
        raw = self.api.get_mode()
        if raw in ("CW-ACC", "CW-APC"):
            return LaserMode.CW
        if raw == "Analog":
            return LaserMode.ANALOG
        raise LaserModeUnavailableError("LuxX is in Standby; select CW or Analog.")

    def set_mode(self, mode: LaserMode) -> None:
        """Select CW-APC or Analog and verify the exact device mode."""
        mode = LaserMode(mode)
        if mode not in self.get_supported_modes():
            raise LaserControlError(
                "Original LuxX supports CW and analog software modes only."
            )
        requested = "CW-APC" if mode == LaserMode.CW else "Analog"
        with self._lock:
            self.api.set_mode(requested)
            if self.api.get_mode() != requested:
                raise LaserControlError("LuxX did not accept the requested mode.")

    def get_power_setpoint_mw(self) -> float:
        """Read the 12-bit GLP register converted to mW by the API."""
        return self.api.get_power()

    def set_power_mw(self, power_mw: float) -> float:
        """Verify the quantized internal setting without changing emission."""
        with self._lock:
            requested = self.validate_power(power_mw)
            if self.get_mode() != LaserMode.CW:
                raise LaserControlError("LuxX serial power requires CW mode.")
            code = self.api.power_code(requested)
            self.api.set_power(requested)
            confirmed = self.get_power_setpoint_mw()
            expected = code * self.api.pmax / 4095.0
            if not isclose(expected, confirmed, rel_tol=0, abs_tol=1e-9):
                raise LaserControlError(
                    "LuxX power readback does not match the request."
                )
            return confirmed

    def get_status(self) -> LaserStatus:
        """Keep measured diode power separate from its internal setpoint."""
        with self._lock:
            return {
                "identity": f"Omicron LuxX {self.api.wavelength:g} nm / {self.api.serial}",
                "simulated": False,
                "emission_enabled": self.api.get_emission_enabled(),
                "measured_power_mw": self.api.get_measured_power(),
            }

    def close(self) -> None:
        """Close only the owned software connection."""
        self.api.close()
