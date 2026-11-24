"""Compose external laser gating with optional internal settings control."""

from datetime import datetime, timezone
from math import isfinite
from typing import Optional
from uuid import uuid4

from navigate.config.laser import LaserSoftwareConfig, resolve_laser_software_config
from .base import LaserBase
from .settings.base import (
    LaserControlError,
    LaserMode,
    LaserModeUnavailableError,
    LaserSettingsBase,
)


class SoftwareControlledLaser(LaserBase):
    """Keep the acquisition contract while routing power to its configured source.

    Parameters
    ----------
    external : LaserBase
        Existing electrical controller, responsible for illumination gating.
    settings : LaserSettingsBase
        Optional software connection, owned by this object.
    options : LaserSoftwareConfig
        Validated routing and internal settings.
    """

    def __init__(
        self,
        external: LaserBase,
        settings: LaserSettingsBase,
        options: LaserSoftwareConfig,
    ) -> None:
        #: LaserBase: Existing NI/ASI/synthetic acquisition control.
        self.external = external
        #: LaserSettingsBase: Owned software settings connection.
        self.settings = settings
        #: LaserSoftwareConfig: Explicitly configured routing policy.
        self.options = options
        self.device_config = external.device_config
        self.device_connection = external.device_connection
        self.configuration = external.configuration
        self.microscope_name = external.microscope_name
        #: Optional[dict]: Last successfully applied software power setting.
        self.power_metadata: Optional[dict] = None
        self._prepared = False
        self._closed = False
        self._last_request: Optional[float] = None
        #: str: Connection token used to reject stale popup writes.
        self.settings_identity = uuid4().hex
        self._session_mode: Optional[LaserMode] = None
        self._mode_error: Optional[str] = None

    def invalidate_power(self) -> None:
        """Require channel preparation to reconfirm power after settings changes."""
        self._prepared = False
        self._last_request = None
        self.power_metadata = None

    def available_modes(self) -> frozenset[LaserMode]:
        """Return device modes compatible with the configured power source."""
        modes = self.settings.get_supported_modes()
        if self.options.power_source == "serial":
            modes = modes.intersection((LaserMode.CW, LaserMode.DIGITAL))
        return frozenset(modes)

    @property
    def prepared_mode(self) -> Optional[str]:
        """Return the confirmed acquisition mode without querying hardware."""
        return self.mode.value if self._prepared else None

    def set_modulation_mode(self, mode: str) -> None:
        """Apply a session mode while the caller keeps illumination blocked.

        Parameters
        ----------
        mode : str
            Supported mode compatible with the configured power source.
        """
        requested = LaserMode(mode)
        if requested not in self.available_modes():
            raise LaserControlError(
                "Mode is unsupported or incompatible with serial power."
            )
        self.invalidate_power()
        try:
            self.settings.set_mode(requested)
            if self.settings.get_mode() != requested:
                raise LaserControlError("Laser did not accept the requested mode.")
        except Exception as error:
            self._mode_error = str(error)
            raise
        self._mode_error = None
        self._session_mode = requested

    def advanced_settings_snapshot(self) -> dict:
        """Read live settings through the adapter, without changing the laser.

        Returns
        -------
        dict
            Serializable limits, modes, power readings and connection status.
            Internal setpoint is unknown in modes controlled by analog voltage.
        """
        mode_warning = None
        try:
            mode = self.settings.get_mode()
        except LaserModeUnavailableError as error:
            mode = None
            mode_warning = str(error)
        minimum, maximum = self.settings.get_power_limits_mw()
        internal_power = mode in (LaserMode.CW, LaserMode.DIGITAL)
        setpoint = self.settings.get_power_setpoint_mw() if internal_power else None
        status = self.settings.get_status()
        available = self.available_modes()
        return {
            "connection": "simulated" if status["simulated"] else "connected",
            "device_identity": status["identity"],
            "simulated": status["simulated"],
            "emission_enabled": status["emission_enabled"],
            "measured_power_mw": status["measured_power_mw"],
            "mode": mode.value if mode is not None else None,
            "mode_warning": mode_warning,
            "available_modes": [m.value for m in LaserMode if m in available],
            "power_source": self.options.power_source,
            "minimum_mw": minimum,
            "maximum_mw": maximum,
            "percent_reference_mw": self.options.power_reference_mw or maximum,
            "setpoint_mw": setpoint,
            "power_kind": "peak_pulse" if mode == LaserMode.DIGITAL else "cw_setpoint",
            "acquisition_mode": (
                self._session_mode.value if self._session_mode else self.options.mode
            ),
            "mode_error": self._mode_error,
            "read_at": datetime.now(timezone.utc).isoformat(),
        }

    def prepare_acquisition(self) -> None:
        """Read settings and optionally apply mode with illumination blocked."""
        self.invalidate_power()
        if self._mode_error:
            raise LaserControlError(
                "Apply and confirm a laser mode before acquiring: " + self._mode_error
            )
        mode = self._session_mode or self.options.mode
        if mode != "preserve":
            requested = LaserMode(mode)
            if requested not in self.settings.get_supported_modes():
                raise LaserControlError(
                    f"Laser does not support {requested.value} mode."
                )
            # Apply explicit modes even when the generic modulation flags match:
            # CW may still be in constant-current rather than power control.
            self.settings.set_mode(requested)
            self.mode = self.settings.get_mode()
            if self.mode != requested:
                raise LaserControlError("Laser did not accept the requested mode.")
        else:
            self.mode = self.settings.get_mode()
        if self.options.power_source == "serial":
            if self.mode not in (LaserMode.CW, LaserMode.DIGITAL):
                raise LaserControlError(
                    "Serial power requires CW or digital laser mode."
                )
            minimum, maximum = self.settings.get_power_limits_mw()
            self.power_reference_mw = self.options.power_reference_mw or maximum
            if not 0 < self.power_reference_mw <= maximum:
                raise LaserControlError(
                    "Laser percentage reference exceeds the device's power limit."
                )
        self._prepared = True

    def set_power(self, laser_intensity: float) -> None:
        """Route channel percentage to external voltage or internal mW settings.

        Parameters
        ----------
        laser_intensity : float
            Channel power percentage. Serial power uses percent_reference_mw,
            defaulting to the queried maximum, as its 100 percent value.
        """
        if self.options.power_source == "hardware":
            self.external.set_power(laser_intensity)
            return
        if not self._prepared:
            raise LaserControlError(
                "Prepare laser settings before applying channel power."
            )
        try:
            percent = float(laser_intensity)
            if not isfinite(percent) or not 0 <= percent <= 100:
                raise ValueError("out of range")
        except (TypeError, ValueError) as error:
            self._last_request = None
            self.power_metadata = None
            raise LaserControlError(
                "Serial laser power must be between 0 and 100 percent."
            ) from error
        # Digital-only ASI set_power also prepares its logic card. Preserve that
        # existing setup; validated serial configurations have no analog output.
        try:
            self.external.set_power(percent)
        except Exception:
            self._last_request = None
            self.power_metadata = None
            raise
        if percent == self._last_request:
            return
        self._last_request = None
        self.power_metadata = None
        requested_mw = percent * self.power_reference_mw / 100
        if self.settings.get_mode() != self.mode:
            raise LaserControlError(
                "Laser mode changed after preparation. Restart acquisition."
            )
        confirmed = self.settings.set_power_mw(requested_mw)
        minimum, maximum = self.settings.get_power_limits_mw()
        if not isfinite(confirmed) or not minimum <= confirmed <= maximum:
            raise LaserControlError("Laser adapter returned an invalid power readback.")
        status = self.settings.get_status()
        self.power_metadata = {
            "requested_percent": percent,
            "requested_mw": requested_mw,
            "percent_reference_mw": self.power_reference_mw,
            "confirmed_setpoint_mw": confirmed,
            "mode": self.mode.value,
            "power_kind": (
                "peak_pulse" if self.mode == LaserMode.DIGITAL else "cw_setpoint"
            ),
            "measurement_context": "channel_preparation",
            "verification": "simulated" if status.get("simulated") else "readback",
            "confirmed_at": datetime.now(timezone.utc).isoformat(),
            **status,
        }
        self._last_request = percent

    def needs_power_update(self, percent: float) -> bool:
        """Return whether internal power needs another serial transaction."""
        try:
            return self._last_request != float(percent)
        except (TypeError, ValueError):
            return True

    def turn_on(self) -> None:
        """Use the existing electrical gate without sending serial commands."""
        if self.options.power_source == "serial" and self.power_metadata is None:
            raise LaserControlError("Laser power has not been successfully confirmed.")
        self.external.turn_on()

    def turn_off(self) -> None:
        """Blank the existing electrical gate without changing internal power."""
        self.external.turn_off()

    def close(self) -> None:
        """Close owned settings and the external controller once."""
        if self._closed:
            return
        self._closed = True
        try:
            self.settings.close()
        finally:
            self.external.close()


def add_software_control(laser: LaserBase, is_synthetic: bool = False) -> LaserBase:
    """Wrap an explicitly configured laser; return legacy devices unchanged.

    Parameters
    ----------
    laser : LaserBase
        Existing electrical laser controller.
    is_synthetic : bool, optional
        Substitute a synthetic adapter even when a physical backend is configured.

    Returns
    -------
    LaserBase
        Original device or composed software-controlled laser.
    """
    options = resolve_laser_software_config(laser.device_config)
    if options.backend == "none":
        return laser
    settings = None
    try:
        if is_synthetic or options.backend == "synthetic":
            from .settings.synthetic import SyntheticLaserSettings

            maximum = options.max_power_mw
            if is_synthetic and options.backend != "synthetic":
                # A real device's maximum is unavailable in Virtual Devices mode.
                # Honor its configured percentage reference without opening it.
                maximum = max(maximum, options.power_reference_mw or maximum)
            modes = (
                frozenset((LaserMode.CW, LaserMode.ANALOG))
                if options.backend == "luxx"
                else None
            )
            settings = SyntheticLaserSettings(maximum, supported_modes=modes)
        elif options.backend == "vortran":
            from .settings.vortran import VortranLaserSettings

            settings = VortranLaserSettings.connect(
                options.port, options.baudrate, options.timeout
            )
        elif options.backend == "obis":
            from .settings.obis import ObisLaserSettings

            settings = ObisLaserSettings.connect(
                options.port, options.baudrate, options.timeout
            )
        else:
            from .settings.luxx import LuxxLaserSettings

            settings = LuxxLaserSettings.connect(
                options.port, options.baudrate, options.timeout
            )
        return SoftwareControlledLaser(laser, settings, options)
    except Exception:
        if settings is not None:
            settings.close()
        laser.close()
        raise
