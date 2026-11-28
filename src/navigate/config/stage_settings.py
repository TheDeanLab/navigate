"""Stage polling availability for configuration-driven GUI controls."""

from typing import Any


def stage_position_polling_supported(
    stage_configuration: Any, synthetic_hardware: bool = False
) -> bool:
    """Return whether a microscope contains a stage supported by idle polling.

    Parameters
    ----------
    stage_configuration : mapping
        Stage section, containing one hardware mapping or a list of mappings.
        Multiprocessing manager proxies are also accepted.
    synthetic_hardware : bool
        Whether Virtual Devices mode replaces the configured hardware.

    Returns
    -------
    bool
        True for synthetic or built-in ASI stage configurations. Other devices
        in a mixed configuration remain unpolled.
    """
    hardware = stage_configuration.get("hardware", [])
    if hasattr(hardware, "get"):
        hardware = [hardware]
    for device in hardware:
        if synthetic_hardware:
            return True
        name = str(device.get("type", ""))
        # Match the built-in startup aliases without admitting unrelated plugins.
        if name.lower().startswith("synthetic"):
            return True
        name = name.removesuffix("Stage")
        manufacturer, _, kind = name.rpartition(".")
        if (not manufacturer or manufacturer == "asi") and kind in {
            "ASI",
            "MS2000",
            "MFC2000",
        }:
            return True
        if manufacturer == "synthetic" and kind == "Synthetic":
            return True
    return False
