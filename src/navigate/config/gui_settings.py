# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Shared GUI settings traversal and validation helpers."""

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any


def iter_gui_settings(
    settings: Any, path: tuple[str, ...] = ()
) -> list[tuple[tuple[str, ...], Any]]:
    """Return non-theme GUI configuration leaves and their paths."""
    if isinstance(settings, Mapping) or hasattr(settings, "items"):
        rows: list[tuple[tuple[str, ...], Any]] = []
        for key, value in settings.items():
            key = str(key)
            if not path and key == "theme":
                continue
            rows.extend(iter_gui_settings(value, (*path, key)))
        return rows
    if isinstance(settings, Sequence) and not isinstance(settings, (str, bytes)):
        return [(path, list(settings))]
    return [(path, settings)]


def flatten_gui_settings(settings: Any) -> list[tuple[str, str]]:
    """Return non-theme GUI settings as dotted path/value pairs."""
    return [(".".join(path), str(value)) for path, value in iter_gui_settings(settings)]


def is_integer_gui_setting(path: tuple[str, ...]) -> bool:
    """Return whether a GUI setting must use an integer entry."""
    return path == ("channel_settings", "count") or path[:2] == (
        "time",
        "timepoints",
    )


def is_boolean_gui_setting(path: tuple[str, ...]) -> bool:
    """Return whether a GUI setting is represented by a checkbutton."""
    return path in {("histogram", "enabled"), ("mip_display", "enabled")}


def is_waveform_gui_setting(path: tuple[str, ...]) -> bool:
    """Return whether a setting affects waveform popup control increments."""
    return path[0] in {"remote_focus_waveform", "galvo_waveform"}


def is_step_size_gui_setting(path: tuple[str, ...]) -> bool:
    """Return whether a GUI setting defines a numeric step size."""
    return path[-1] == "step" or path[-1].endswith("_step_size")


def is_positive_gui_setting(path: tuple[str, ...]) -> bool:
    """Return whether a GUI setting must be strictly greater than zero."""
    return is_step_size_gui_setting(path) or path[:2] == (
        "stack_acquisition",
        "step_size",
    )


def is_nonnegative_gui_setting(path: tuple[str, ...]) -> bool:
    """Return whether a GUI setting is constrained to non-negative values."""
    return path[:2] in {
        ("channel_settings", "laser_power"),
        ("channel_settings", "exposure_time"),
        ("channel_settings", "interval"),
    }


def gui_setting_minimum(path: tuple[str, ...]) -> str:
    """Return the entry minimum for GUI settings with lower-bound constraints."""
    if path == ("channel_settings", "count"):
        return "1"
    if is_positive_gui_setting(path):
        return "0.000000001"
    if is_nonnegative_gui_setting(path) or path[0] == "time":
        return "0"
    return "-Infinity"


def gui_setting_group(path: tuple[str, ...]) -> str:
    """Return the human-readable group title for a GUI setting path."""
    group_names = {
        "remote_focus_waveform": "Remote Focus Waveform",
        "galvo_waveform": "Galvo Waveform",
    }
    return group_names.get(path[0], path[0].replace("_", " ").title())


def coerce_gui_value(value: Any, path: tuple[str, ...]) -> Any:
    """Convert a GUI setting value to its validated runtime type."""
    if (
        is_integer_gui_setting(path)
        and isinstance(value, int)
        and not isinstance(value, bool)
    ):
        parsed_value = value
    elif not is_integer_gui_setting(path) and isinstance(value, (int, float)):
        parsed_value = float(value)
    else:
        parsed_value = int(value) if is_integer_gui_setting(path) else float(value)
    if not is_integer_gui_setting(path) and not isfinite(parsed_value):
        raise ValueError("Value must be finite")
    if path == ("channel_settings", "count") and parsed_value <= 0:
        raise ValueError("Value must be greater than 0")
    if is_positive_gui_setting(path) and parsed_value <= 0:
        raise ValueError("Value must be greater than 0")
    if (path[0] == "time" or is_nonnegative_gui_setting(path)) and parsed_value < 0:
        raise ValueError("Value must be greater than or equal to 0")
    return parsed_value


def coerce_boolean_gui_value(value: Any) -> bool:
    """Convert a GUI display toggle to bool or raise ValueError."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    raise ValueError("Value must be true or false")
