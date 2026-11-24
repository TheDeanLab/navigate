"""Optional laser software configuration with backward-compatible defaults."""

from dataclasses import dataclass
from math import isfinite
from multiprocessing.managers import DictProxy
from typing import Optional


@dataclass(frozen=True)
class LaserSoftwareConfig:
    """Resolved optional settings; legacy lasers remain externally controlled."""

    power_source: str = "hardware"
    backend: str = "none"
    mode: str = "preserve"
    port: str = ""
    baudrate: int = 19200
    timeout: float = 0.5
    power_reference_mw: Optional[float] = None
    max_power_mw: float = 100.0


def resolve_laser_software_config(laser: dict) -> LaserSoftwareConfig:
    """Validate optional settings without opening devices or changing defaults.

    Parameters
    ----------
    laser : dict
        One configuration.yaml laser entry; shared mappings are also accepted.

    Returns
    -------
    LaserSoftwareConfig
        Validated settings. Missing or null software_control disables software.

    Raises
    ------
    ValueError
        An explicitly configured software path is invalid or ambiguous.
    """
    power = laser.get("power") or {}
    options = laser.get("software_control") or {}
    if not isinstance(options, (dict, DictProxy)):
        raise ValueError("laser.software_control must be a mapping.")
    source = str(power.get("source", "hardware")).lower()
    backend = str(options.get("type") or "none").lower()
    mode = str(options.get("mode") or "preserve").lower()
    if source not in ("hardware", "serial"):
        raise ValueError("laser.power.source must be hardware or serial.")
    if backend not in ("none", "synthetic", "vortran", "obis", "luxx"):
        raise ValueError(
            "laser.software_control.type must be None, Synthetic, Vortran, OBIS, or LuxX."
        )
    if source == "serial" and backend == "none":
        raise ValueError("Serial laser power requires a software_control adapter.")
    if mode not in ("preserve", "cw", "digital", "analog", "mixed"):
        raise ValueError("Unknown laser.software_control.mode.")
    if backend == "none":
        return LaserSoftwareConfig(power_source=source)
    if backend == "luxx" and mode in ("digital", "mixed"):
        raise ValueError(
            "Original LuxX supports CW and analog software modes only; NI/ASI handles its separate electronic shutter."
        )
    if source == "serial" and mode in ("analog", "mixed"):
        raise ValueError(
            "Serial laser power cannot be combined with external analog power."
        )
    port = str(options.get("port") or "")
    if backend in ("vortran", "obis", "luxx") and not port:
        raise ValueError(f"{backend} software control requires a serial port.")
    try:
        timeout = float(options.get("timeout", 0.5))
        default_baudrate = {"obis": 115200, "luxx": 500000}.get(backend, 19200)
        configured_baudrate = options.get("baudrate")
        baudrate = int(
            default_baudrate if configured_baudrate is None else configured_baudrate
        )
        maximum = float(options.get("max_power_mw", 100.0))
        reference = power.get("percent_reference_mw")
        reference = float(reference) if reference is not None else None
    except (TypeError, ValueError) as error:
        raise ValueError("Invalid numeric laser software setting.") from error
    if not isfinite(timeout) or timeout <= 0 or baudrate <= 0:
        raise ValueError("Laser timeout and baudrate must be positive and finite.")
    if not isfinite(maximum) or maximum <= 0:
        raise ValueError("Synthetic max_power_mw must be positive and finite.")
    if reference is not None and (not isfinite(reference) or reference <= 0):
        raise ValueError("Laser percent_reference_mw must be positive and finite.")
    if source == "serial":
        analog_type = str((power.get("hardware") or {}).get("type") or "").lower()
        if analog_type not in (
            "",
            "none",
            "synthetic",
            "syntheticlaser",
            "synthetic.synthetic",
            "synthetic.syntheticlaser",
        ):
            raise ValueError(
                "Serial power requires power.hardware.type: Synthetic (no analog output)."
            )
        gate = (laser.get("onoff") or {}).get("hardware") or {}
        gate_type = str(gate.get("type") or "").lower()
        if backend != "synthetic" and gate_type not in (
            "ni",
            "nilaser",
            "ni.ni",
            "ni.nilaser",
            "asi",
            "asilaser",
            "asi.asi",
            "asi.asilaser",
        ):
            raise ValueError("Serial laser power requires an NI or ASI digital gate.")
    return LaserSoftwareConfig(
        source, backend, mode, port, baudrate, timeout, reference, maximum
    )
