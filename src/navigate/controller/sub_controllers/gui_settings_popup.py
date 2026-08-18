# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Controller for the GUI settings popup."""

from collections.abc import Mapping, Sequence
from typing import Any

from navigate.view.popups.gui_settings_popup import GuiSettingsPopup


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


def is_nonnegative_gui_setting(path: tuple[str, ...]) -> bool:
    """Return whether a GUI setting is constrained to non-negative values."""
    return (
        path[:2]
        in {
            ("channel_settings", "laser_power"),
            ("channel_settings", "exposure_time"),
            ("channel_settings", "interval"),
            ("stack_acquisition", "step_size"),
        }
    )


def gui_setting_minimum(path: tuple[str, ...]) -> str:
    """Return the entry minimum for GUI settings with lower-bound constraints."""
    if path == ("channel_settings", "count"):
        return "1"
    if (
        is_step_size_gui_setting(path)
        or is_nonnegative_gui_setting(path)
        or path[0] == "time"
    ):
        return "0"
    return "-Infinity"


def gui_setting_group(path: tuple[str, ...]) -> str:
    """Return the human-readable group title for a GUI setting path."""
    group_names = {
        "remote_focus_waveform": "Remote Focus Waveform",
        "galvo_waveform": "Galvo Waveform",
    }
    return group_names.get(path[0], path[0].replace("_", " ").title())


def coerce_gui_value(value: str, path: tuple[str, ...]) -> Any:
    """Convert text entered in the popup to the value type for a GUI setting."""
    parsed_value = int(value) if is_integer_gui_setting(path) else float(value)
    if path == ("channel_settings", "count") and parsed_value <= 0:
        raise ValueError("Value must be greater than 0")
    if is_step_size_gui_setting(path) and parsed_value <= 0:
        raise ValueError("Value must be greater than 0")
    if (path[0] == "time" or is_nonnegative_gui_setting(path)) and parsed_value < 0:
        raise ValueError("Value must be greater than or equal to 0")
    return parsed_value


class GuiSettingsPopupController:
    """Connect the GUI settings view to the shared GUI configuration."""

    def __init__(self, view: GuiSettingsPopup, parent_controller: "Controller") -> None:
        self.view = view
        self.parent_controller = parent_controller
        self.view.buttons["apply"].configure(command=self.apply_settings)
        self.view.buttons["close"].configure(command=self.close_popup)
        self.view.popup.protocol("WM_DELETE_WINDOW", self.close_popup)
        self.populate_settings()

    def populate_settings(self) -> None:
        """Populate the view from the active GUI configuration."""
        fields = []
        for path, value in iter_gui_settings(self.parent_controller.configuration["gui"]):
            fields.append(
                {
                    "path": path,
                    "value": value,
                    "group": gui_setting_group(path),
                    "label": ".".join(path[1:]).replace("_", " "),
                    "minimum": gui_setting_minimum(path),
                    "type": (
                        "boolean"
                        if is_boolean_gui_setting(path)
                        else "integer"
                        if is_integer_gui_setting(path)
                        else "float"
                    ),
                }
            )
        self.view.populate_settings(fields)

    def apply_settings(self) -> bool:
        """Validate and write user edits to the shared GUI configuration."""
        updates: list[tuple[tuple[str, ...], Any]] = []
        for path, (value_var, entry) in self.view.entries.items():
            try:
                updates.append((path, coerce_gui_value(value_var.get(), path)))
                entry._toggle_error(False)
            except ValueError as error:
                entry._toggle_error(True)
                self.view.set_status(f"{'.'.join(path)}: {error}")
                entry.focus_set()
                return False
        updates.extend(
            (path, value_var.get())
            for path, value_var in self.view.boolean_variables.items()
        )

        waveform_settings_changed = False
        other_settings_changed = False
        display_setting_updates: list[tuple[tuple[str, ...], bool]] = []
        for path, value in updates:
            parent = self.parent_controller.configuration["gui"]
            for key in path[:-1]:
                parent = parent[key]
            if parent[path[-1]] != value:
                if is_waveform_gui_setting(path):
                    waveform_settings_changed = True
                elif is_boolean_gui_setting(path):
                    display_setting_updates.append((path, value))
                else:
                    other_settings_changed = True
            parent[path[-1]] = value

        self._apply_display_setting_updates(display_setting_updates)
        messages = []
        if waveform_settings_changed:
            waveform_popup = getattr(
                self.parent_controller, "waveform_popup_controller", None
            )
            messages.append("Waveform step-size settings were applied successfully.")
            if waveform_popup is not None:
                messages.append(
                    "The Waveform Parameters window was reopened to take effect"
                )
            self._refresh_waveform_popup(waveform_popup)
        if other_settings_changed:
            messages.append(
                "Setting changes were saved. Restart Navigate for the changes "
                "to take effect."
            )
        if messages:
            self.view.show_info("Settings Saved", "\n\n".join(messages))
        return True

    def _apply_display_setting_updates(
        self, updates: list[tuple[tuple[str, ...], bool]]
    ) -> None:
        """Apply display toggles through the existing menu-controller workflow."""
        menu_controller = self.parent_controller.menu_controller
        for path, value in updates:
            if path == ("histogram", "enabled"):
                menu_controller.histogram_enabled.set(value)
                menu_controller.toggle_histogram()
            elif path == ("mip_display", "enabled"):
                menu_controller.mip_enabled.set(value)
                menu_controller.toggle_mip()

    def _refresh_waveform_popup(self, waveform_popup=None) -> None:
        """Reopen an existing waveform popup so it uses the updated increments."""
        if waveform_popup is None:
            waveform_popup = getattr(
                self.parent_controller, "waveform_popup_controller", None
            )
        if waveform_popup is None:
            return
        waveform_popup.close_window()
        self.parent_controller.menu_controller.popup_waveform_setting()

    def showup(self) -> None:
        """Show the existing settings window."""
        self.view.showup()

    def close_popup(self) -> None:
        """Close the popup and discard its controller reference."""
        self.view.popup.destroy()
        if hasattr(self.parent_controller, "gui_settings_popup_controller"):
            del self.parent_controller.gui_settings_popup_controller
