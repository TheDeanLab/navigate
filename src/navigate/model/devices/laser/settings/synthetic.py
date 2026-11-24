"""In-memory laser settings for simulation and integration tests."""

from math import isfinite

from .base import LaserControlError, LaserMode, LaserSettingsBase, LaserStatus


class SyntheticLaserSettings(LaserSettingsBase):
    """Simulate internal settings without opening a hardware connection.

    Parameters
    ----------
    max_power_mw : float, optional
        Maximum simulated power and default percentage reference.
    """

    def __init__(self, max_power_mw: float = 100.0) -> None:
        if not isfinite(max_power_mw) or max_power_mw <= 0:
            raise ValueError("Synthetic maximum power must be positive and finite.")
        #: float: Simulated maximum output in mW.
        self.max_power_mw = float(max_power_mw)
        #: LaserMode: Simulated operating mode.
        self.mode = LaserMode.DIGITAL
        #: float: Simulated internal power setpoint in mW.
        self.power_mw = 0.0
        #: bool: Whether the settings connection has been closed.
        self.closed = False

    def _check_open(self) -> None:
        """Reject operations after closing the settings connection."""
        if self.closed:
            raise LaserControlError("Synthetic laser settings connection is closed.")

    def get_supported_modes(self) -> frozenset[LaserMode]:
        """Return all simulated modulation modes."""
        return frozenset(LaserMode)

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
            self.mode = LaserMode(mode)
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
