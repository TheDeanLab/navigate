# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Controller for the GUI settings popup."""

from navigate.config.gui_settings import (
    coerce_gui_value,
    flatten_gui_settings,
    gui_setting_group,
    gui_setting_minimum,
    is_boolean_gui_setting,
    is_integer_gui_setting,
    is_nonnegative_gui_setting,
    is_positive_gui_setting,
    is_step_size_gui_setting,
    is_waveform_gui_setting,
    iter_gui_settings,
)
from navigate.view.popups.gui_settings_popup import GuiSettingsPopup


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
        for path, value in iter_gui_settings(
            self.parent_controller.configuration["gui"]
        ):
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
                        else "integer" if is_integer_gui_setting(path) else "float"
                    ),
                }
            )
        self.view.populate_settings(fields)

    def apply_settings(self) -> bool:
        """Validate and write user edits to the shared GUI configuration."""
        updates: list[tuple[tuple[str, ...], Any]] = []
        validation_errors: list[tuple[tuple[str, ...], Any, ValueError]] = []
        for path, (value_var, entry) in self.view.entries.items():
            try:
                updates.append((path, coerce_gui_value(value_var.get(), path)))
                entry._toggle_error(False)
            except ValueError as error:
                entry._toggle_error(True)
                validation_errors.append((path, entry, error))
        if validation_errors:
            path, entry, error = validation_errors[0]
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
