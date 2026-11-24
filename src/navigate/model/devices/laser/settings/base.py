"""Contracts for configuring a laser independently of its electrical inputs."""

from abc import ABC, abstractmethod
from enum import Enum
from math import isfinite
from typing import Optional, TypedDict

from navigate.model.utils.exceptions import UserVisibleException


class LaserControlError(UserVisibleException):
    """A requested laser setting could not be applied or verified."""


class LaserMode(str, Enum):
    """Common modulation modes; adapters advertise their supported subset."""

    CW = "cw"
    DIGITAL = "digital"
    ANALOG = "analog"
    MIXED = "mixed"


class LaserStatus(TypedDict):
    """Laser-reported status; unavailable telemetry is explicitly unknown."""

    identity: str
    simulated: bool
    emission_enabled: Optional[bool]
    measured_power_mw: Optional[float]


class LaserSettingsBase(ABC):
    """Software settings interface, distinct from acquisition on/off control.

    Implementations must not enable emission on connection or on power changes.
    Power values are in mW at the laser, never calibrated sample-plane power.
    Unsupported operations and unsuccessful readbacks raise LaserControlError.
    """

    @abstractmethod
    def get_supported_modes(self) -> frozenset[LaserMode]:
        """Return the modes supported by this adapter and device."""

    @abstractmethod
    def get_power_limits_mw(self) -> tuple[float, float]:
        """Return the minimum and maximum internal power setpoints in mW."""

    @abstractmethod
    def get_mode(self) -> LaserMode:
        """Read the current modulation mode."""

    @abstractmethod
    def set_mode(self, mode: LaserMode) -> None:
        """Apply and verify a mode while the caller blocks sample illumination.

        Parameters
        ----------
        mode : LaserMode
            Requested modulation mode.
        """

    @abstractmethod
    def get_power_setpoint_mw(self) -> float:
        """Read the internal CW or peak pulse power setting in mW."""

    @abstractmethod
    def set_power_mw(self, power_mw: float) -> float:
        """Apply power and return its confirmed, possibly quantized setting.

        Parameters
        ----------
        power_mw : float
            Requested internal power setting in mW.

        Returns
        -------
        float
            Confirmed setpoint in mW, not a sample-plane measurement.
        """

    @abstractmethod
    def get_status(self) -> LaserStatus:
        """Read identity and status; unavailable telemetry must be None."""

    @abstractmethod
    def close(self) -> None:
        """Release the connection without changing emission settings."""

    def validate_power(self, power_mw: float) -> float:
        """Validate an internal power request against the device limits.

        Parameters
        ----------
        power_mw : float
            Requested power in mW.

        Returns
        -------
        float
            Validated finite power value.
        """
        power = float(power_mw)
        minimum, maximum = self.get_power_limits_mw()
        if not isfinite(power) or not minimum <= power <= maximum:
            raise LaserControlError(
                f"Laser power must be between {minimum} and {maximum} mW."
            )
        return power
