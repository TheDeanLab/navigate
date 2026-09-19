# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""GUI configuration preload rules."""

import copy
from pathlib import Path
from typing import Any
from multiprocessing.managers import DictProxy

import yaml

from navigate.config.config import update_config_dict
from navigate.config.gui_settings import (
    coerce_boolean_gui_value,
    coerce_gui_value,
    is_boolean_gui_setting,
    iter_gui_settings,
)
from navigate.config.preload import PreloadContext, PreloadRule


def ensure_gui_settings(context: PreloadContext) -> None:
    """Repair GUI defaults and validate popup-editable setting values."""
    gui_settings = context.configuration["gui"]
    gui_defaults = _gui_defaults()

    _ensure_missing_gui_defaults(context, gui_settings, gui_defaults)
    gui_settings["channel_settings"]["count"] = _configuration_channel_count(
        context.configuration["configuration"]["microscopes"]
    )
    _validate_gui_setting_values(context, gui_settings, gui_defaults)


def _ensure_missing_gui_defaults(
    context: PreloadContext,
    gui_settings,
    gui_defaults: dict[str, Any],
    path: tuple[str, ...] = (),
) -> None:
    """Recursively add missing GUI defaults without replacing existing groups."""
    for key, default_value in gui_defaults.items():
        current_path = (*path, str(key))
        if key not in gui_settings:
            update_config_dict(context.manager, gui_settings, key, default_value)
            context.report.add_change(
                _gui_report_path(current_path),
                "gui-default",
                f"Added missing GUI setting {'.'.join(current_path)}.",
            )
            continue
        if isinstance(default_value, dict) and isinstance(
            gui_settings[key], (dict, DictProxy)
        ):
            _ensure_missing_gui_defaults(
                context, gui_settings[key], default_value, current_path
            )


def _validate_gui_setting_values(
    context: PreloadContext, gui_settings, gui_defaults: dict[str, Any]
) -> None:
    """Validate non-theme GUI leaves using the GUI settings popup rules."""
    for path, value in iter_gui_settings(gui_settings):
        if not path:
            continue
        found, default_value = _get_path(gui_defaults, path, with_found=True)
        try:
            normalized_value = (
                coerce_boolean_gui_value(value)
                if is_boolean_gui_setting(path)
                else coerce_gui_value(value, path)
            )
        except (TypeError, ValueError):
            if found:
                _set_path(context.manager, gui_settings, path, default_value)
                context.report.add_issue(
                    _gui_report_path(path),
                    "gui-invalid-default",
                    (
                        f"GUI setting {'.'.join(path)} was invalid and was replaced "
                        "with the default."
                    ),
                    fatal=False,
                )
            else:
                _delete_path(gui_settings, path)
                context.report.add_issue(
                    _gui_report_path(path),
                    "gui-invalid-removed",
                    (
                        f"GUI setting {'.'.join(path)} was invalid and had no "
                        "default, so it was removed."
                    ),
                    fatal=False,
                )
            continue
        if normalized_value != value:
            _set_path(context.manager, gui_settings, path, normalized_value)
            context.report.add_change(
                _gui_report_path(path),
                "gui-type-normalized",
                f"Normalized GUI setting {'.'.join(path)}.",
            )


def _configuration_channel_count(microscopes) -> int:
    """Return the repaired GUI channel count from configured camera counts."""
    channel_count = 5
    for microscope_config in microscopes.values():
        camera_config = microscope_config.get("camera")
        if not isinstance(camera_config, (dict, DictProxy)):
            continue
        try:
            channel_count = max(channel_count, int(camera_config.get("count", 5)))
        except (TypeError, ValueError):
            channel_count = 5
    return channel_count


def _gui_defaults() -> dict[str, Any]:
    """Return startup-safe defaults for GUI settings."""
    gui_path = Path(__file__).resolve().parent.parent / "gui_configuration.yml"
    with open(gui_path) as gui_file:
        defaults = yaml.load(gui_file, Loader=yaml.FullLoader) or {}
    defaults = copy.deepcopy(defaults)
    defaults.setdefault("histogram", {}).setdefault("enabled", True)
    defaults.setdefault("mip_display", {}).setdefault("enabled", True)
    return defaults


def _get_path(target, path: tuple[str, ...], *, with_found: bool = False):
    """Read a nested GUI setting path."""
    current = target
    for key in path:
        if not isinstance(current, (dict, DictProxy)) or key not in current:
            return (False, None) if with_found else None
        current = current[key]
    return (True, current) if with_found else current


def _set_path(manager, target, path: tuple[str, ...], value: Any) -> None:
    """Set a nested GUI setting path."""
    current = target
    for key in path[:-1]:
        if key not in current or not isinstance(current[key], (dict, DictProxy)):
            update_config_dict(manager, current, key, {})
        current = current[key]
    if isinstance(value, (dict, list)):
        update_config_dict(manager, current, path[-1], copy.deepcopy(value))
    else:
        current[path[-1]] = value


def _delete_path(target, path: tuple[str, ...]) -> None:
    """Delete a nested GUI setting path if present."""
    current = target
    for key in path[:-1]:
        if not isinstance(current, (dict, DictProxy)) or key not in current:
            return
        current = current[key]
    if isinstance(current, (dict, DictProxy)):
        current.pop(path[-1], None)


def _gui_report_path(path: tuple[str, ...]) -> str:
    """Return the structured preload-report path for one GUI setting."""
    return "gui." + ".".join(path)


GUI_RULES = [
    PreloadRule(
        "gui",
        "settings",
        ensure_gui_settings,
    ),
]
