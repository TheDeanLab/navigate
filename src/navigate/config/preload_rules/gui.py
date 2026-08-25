# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""GUI configuration preload rules."""

from multiprocessing.managers import DictProxy

from navigate.config.config import GUI_SETTING_DEFAULTS, update_config_dict
from navigate.config.preload import PreloadContext, PreloadRule


def ensure_gui_channel_settings(context: PreloadContext) -> None:
    """Repair GUI channel count and waveform setting defaults."""
    gui_settings = context.configuration["gui"]
    if "channel_settings" not in gui_settings:
        update_config_dict(context.manager, gui_settings, "channel_settings", {})
    gui_settings["channel_settings"]["count"] = _configuration_channel_count(
        context.configuration["configuration"]["microscopes"]
    )
    for group_name, defaults in GUI_SETTING_DEFAULTS.items():
        if group_name not in gui_settings:
            update_config_dict(context.manager, gui_settings, group_name, defaults)
            continue
        for setting_name, value in defaults.items():
            if setting_name not in gui_settings[group_name]:
                gui_settings[group_name][setting_name] = value


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


GUI_RULES = [
    PreloadRule(
        "gui",
        "channel_settings",
        ensure_gui_channel_settings,
    ),
]
