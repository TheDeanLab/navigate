"""Coherent OBIS settings adapter using the existing SCPI API."""

from math import isclose, isfinite

from navigate.model.devices.APIs.coherent.ObisLaser import ObisLaser
from .base import (
    LaserControlError,
    LaserMode,
    LaserModeUnavailableError,
    LaserSettingsBase,
    LaserStatus,
)


class ObisLaserSettings(LaserSettingsBase):
    """Adapt the OBIS API's watts to the common settings interface's mW.

    Parameters
    ----------
    api : ObisLaser
        Connected API owned by this adapter.
    """

    def __init__(self, api: ObisLaser) -> None:
        self.api = api
        self._lock = api._lock
        try:
            self._identity = api.get_laser_model()
            self._limits = (
                self._mw(api.get_minimum_laser_power()),
                self._mw(api.get_maximum_laser_power()),
            )
            if not 0 <= self._limits[0] < self._limits[1]:
                raise LaserControlError("OBIS reported invalid power limits.")
        except Exception:
            api.close()
            raise

    @classmethod
    def connect(
        cls, port: str, baudrate: int = 115200, timeout: float = 0.5
    ) -> "ObisLaserSettings":
        """Connect through ObisLaser without initializing emission or power."""
        return cls(ObisLaser(port, baudrate=baudrate, timeout=timeout))

    @staticmethod
    def _mw(value: str) -> float:
        """Convert finite, nonnegative watts from the API to mW."""
        try:
            power = float(value) * 1000
        except (TypeError, ValueError) as error:
            raise LaserControlError("Invalid OBIS power readback.") from error
        if not isfinite(power) or power < 0:
            raise LaserControlError("Invalid OBIS power readback.")
        return power

    def get_supported_modes(self) -> frozenset[LaserMode]:
        """Return the four standard OBIS modulation modes."""
        return frozenset(LaserMode)

    def get_power_limits_mw(self) -> tuple[float, float]:
        """Return queried limits converted from watts to mW."""
        return self._limits

    def get_mode(self) -> LaserMode:
        """Read modulation category, including constant-current/feedback variants."""
        raw = self.api.get_laser_operating_mode()
        modes = {
            "CWP": LaserMode.CW,
            "CWC": LaserMode.CW,
            "DIGITAL": LaserMode.DIGITAL,
            "DIGSO": LaserMode.DIGITAL,
            "ANALOG": LaserMode.ANALOG,
            "MIXED": LaserMode.MIXED,
            "MIXSO": LaserMode.MIXED,
        }
        if raw not in modes:
            raise LaserModeUnavailableError(
                f"OBIS mode {raw!r}; select a supported mode."
            )
        return modes[raw]

    def set_mode(self, mode: LaserMode) -> None:
        """Apply the standard OBIS mode and verify its exact device token."""
        requested = {
            LaserMode.CW: "CWP",
            LaserMode.DIGITAL: "DIGITAL",
            LaserMode.ANALOG: "ANALOG",
            LaserMode.MIXED: "MIXED",
        }[LaserMode(mode)]
        with self._lock:
            self.api.set_laser_operating_mode(requested)
            if self.api.get_laser_operating_mode() != requested:
                raise LaserControlError("OBIS did not accept the requested mode.")

    def get_power_setpoint_mw(self) -> float:
        """Read the internal setpoint, distinct from measured laser output."""
        return self._mw(self.api.get_power_setpoint())

    def set_power_mw(self, power_mw: float) -> float:
        """Apply mW as watts, then return the verified mW setpoint."""
        with self._lock:
            requested = self.validate_power(power_mw)
            raw = self.api.get_laser_operating_mode()
            if raw not in ("CWP", "DIGITAL", "DIGSO"):
                raise LaserControlError(
                    "OBIS serial power requires CWP or digital mode."
                )
            self.api.set_laser_power(requested / 1000)
            confirmed = self.get_power_setpoint_mw()
            if not isclose(requested, confirmed, rel_tol=0, abs_tol=0.001):
                raise LaserControlError(
                    "OBIS power readback does not match the request."
                )
            return confirmed

    def get_status(self) -> LaserStatus:
        """Read emission enable and measured output without changing either."""
        with self._lock:
            return {
                "identity": self._identity,
                "simulated": False,
                "emission_enabled": self.api.get_emission_enabled(),
                "measured_power_mw": self._mw(self.api.get_laser_power()),
            }

    def close(self) -> None:
        """Close only the owned software connection."""
        self.api.close()
