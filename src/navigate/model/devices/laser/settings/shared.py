"""Share protocol transactions and verification state across microscope owners."""

from threading import RLock
from typing import Any

from .base import LaserControlError, LaserMode, LaserSettingsBase, LaserStatus


class SharedLaserSettings(LaserSettingsBase):
    """Factory-owned adapter; microscope wrappers hold counted factory leases.

    Parameters
    ----------
    adapter : LaserSettingsBase
        Connected protocol adapter owned by this shared session.
    """

    def __init__(self, adapter: LaserSettingsBase) -> None:
        self.adapter = adapter
        #: RLock: Covers complete wrapper operations, including metadata readbacks.
        self.lock = RLock()
        #: int: Changes before every attempted write or failed read.
        self.revision = 0
        #: int: Changes before mode writes, invalidating prepared mode descriptions.
        self.mode_revision = 0
        #: str | None: A failed mode transaction must be repaired before acquisition.
        self.mode_error = None
        self._closed = False

    @classmethod
    def connect(
        cls, port: str, baudrate: int, timeout: float, backend: str
    ) -> "SharedLaserSettings":
        """Create one protocol adapter without changing emission or power."""
        from .vortran import VortranLaserSettings
        from .obis import ObisLaserSettings
        from .luxx import LuxxLaserSettings

        adapters = {
            "vortran": VortranLaserSettings,
            "obis": ObisLaserSettings,
            "luxx": LuxxLaserSettings,
        }
        return cls(adapters[backend].connect(port, baudrate, timeout))

    def _call(self, method: str, *args: Any) -> Any:
        """Serialize an adapter operation and invalidate confirmations on error."""
        with self.lock:
            if self._closed:
                raise LaserControlError("Shared laser connection is closed.")
            try:
                return getattr(self.adapter, method)(*args)
            except Exception:
                self.revision += 1
                raise

    def get_supported_modes(self) -> frozenset[LaserMode]:
        """Return the shared adapter's advertised modes."""
        return self._call("get_supported_modes")

    def get_power_limits_mw(self) -> tuple[float, float]:
        """Return the device limits in mW."""
        return self._call("get_power_limits_mw")

    def get_mode(self) -> LaserMode:
        """Read the current shared hardware mode."""
        return self._call("get_mode")

    def set_mode(self, mode: LaserMode) -> None:
        """Apply and verify a mode, invalidating every owner's confirmation."""
        with self.lock:
            self.revision += 1
            self.mode_revision += 1
            try:
                self._call("set_mode", mode)
                if self.get_mode() != mode:
                    raise LaserControlError("Laser did not accept the requested mode.")
            except Exception as error:
                self.mode_error = str(error)
                raise
            self.mode_error = None

    def get_power_setpoint_mw(self) -> float:
        """Read the current internal power setting."""
        return self._call("get_power_setpoint_mw")

    def set_power_mw(self, power_mw: float) -> float:
        """Apply power, invalidating other owners even if the write fails."""
        with self.lock:
            self.revision += 1
            return self._call("set_power_mw", power_mw)

    def get_status(self) -> LaserStatus:
        """Read status under the shared transaction lock."""
        return self._call("get_status")

    def close(self) -> None:
        """Disconnect once, when the factory releases the final lease."""
        with self.lock:
            if not self._closed:
                self._closed = True
                self.revision += 1
                self.adapter.close()
