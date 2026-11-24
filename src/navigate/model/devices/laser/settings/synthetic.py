"""In-memory laser settings for simulation and integration tests."""

from math import isfinite
from typing import Optional

from .base import LaserControlError, LaserMode, LaserSettingsBase, LaserStatus


class SyntheticLaserSettings(LaserSettingsBase):
    """Simulate internal settings without opening a hardware connection.

    Parameters
    ----------
    max_power_mw : float, optional
        Maximum simulated power and default percentage reference.
    supported_modes : frozenset of LaserMode, optional
        Capabilities of a substituted physical backend; defaults to all modes.
    """

    def __init__(
        self,
        max_power_mw: float = 100.0,
        supported_modes: Optional[frozenset[LaserMode]] = None,
    ) -> None:
        if not isfinite(max_power_mw) or max_power_mw <= 0:
            raise ValueError("Synthetic maximum power must be positive and finite.")
        #: float: Simulated maximum output in mW.
        self.max_power_mw = float(max_power_mw)
        #: frozenset[LaserMode]: Modes advertised by this simulated device.
        self.supported_modes = (
            frozenset(LaserMode) if supported_modes is None else supported_modes
        )
        if not self.supported_modes or not self.supported_modes.issubset(
            frozenset(LaserMode)
        ):
            raise ValueError("Synthetic laser needs at least one valid supported mode.")
        #: LaserMode: Simulated operating mode.
        self.mode = next(
            mode
            for mode in (
                LaserMode.DIGITAL,
                LaserMode.CW,
                LaserMode.ANALOG,
                LaserMode.MIXED,
            )
            if mode in self.supported_modes
        )
        #: float: Simulated internal power setpoint in mW.
        self.power_mw = 0.0
        #: bool: Whether the settings connection has been closed.
        self.closed = False

    def _check_open(self) -> None:
        """Reject operations after closing the settings connection."""
        if self.closed:
            raise LaserControlError("Synthetic laser settings connection is closed.")

    def get_supported_modes(self) -> frozenset[LaserMode]:
        """Return the simulated device's supported modulation modes."""
        return self.supported_modes

    def get_power_limits_mw(self) -> tuple[float, float]:
        """Return simulated internal power limits in mW."""
        return 0.0, self.max_power_mw

    def get_mode(self) -> LaserMode:
        """Read the simulated modulation mode."""
        self._check_open()
        return self.mode

    def set_mode(self, mode: LaserMode) -> None:
        """Apply a simulated mode, using the base interface's semantics."""
        self._check_open()
        try:
            requested = LaserMode(mode)
            if requested not in self.supported_modes:
                raise ValueError("unsupported mode")
            self.mode = requested
        except ValueError as error:
            raise LaserControlError(f"Unsupported laser mode: {mode!r}") from error

    def get_power_setpoint_mw(self) -> float:
        """Read the simulated power setpoint in mW."""
        self._check_open()
        return self.power_mw

    def set_power_mw(self, power_mw: float) -> float:
        """Apply and return a simulated internal power setting in mW."""
        self._check_open()
        if self.mode not in (LaserMode.CW, LaserMode.DIGITAL):
            raise LaserControlError("External analog control overrides serial power.")
        self.power_mw = self.validate_power(power_mw)
        return self.power_mw

    def get_status(self) -> LaserStatus:
        """Return explicitly simulated status without invented measurements."""
        self._check_open()
        return {
            "identity": "Synthetic laser",
            "simulated": True,
            "emission_enabled": None,
            "measured_power_mw": None,
        }

    def close(self) -> None:
        """Close the simulated connection."""
        self.closed = True
