# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Standard Library Imports
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

import yaml

from navigate.config.configuration_schema import (
    CollectionSpec,
    SettingSpec,
)
from navigate.config.device_schema import (
    canonical_device_type,
    category_base_class_name,
    category_model_suffix,
    class_inherits,
    device_directory,
    get_configuration_schema,
    get_connect_params,
    module_classes,
    strip_category_model_suffix,
)

# Local Imports
from navigate.view.configurator_application_window import (
    AddDeviceDialog,
    ConfigurationAssistantWindow,
    ConfiguratorTooltip,
    RenameMicroscopeDialog,
)
from navigate.view.custom_widgets.validation import ValidatedSpinbox
from navigate.view.theme import apply_theme, get_theme_padding_px, get_theme_space_px

# Logger Setup
import logging

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class InlineYamlList(list):
    """A list that is written with YAML flow style (``[item, ...]``)."""


class ConfiguratorYamlDumper(yaml.SafeDumper):
    """YAML dumper with compact formatting for stage axes lists."""


def _represent_inline_yaml_list(
    dumper: yaml.SafeDumper, value: InlineYamlList
) -> yaml.nodes.SequenceNode:
    """Represent stage axes lists as inline YAML sequences."""
    return dumper.represent_sequence(
        yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG, value, flow_style=True
    )


ConfiguratorYamlDumper.add_representer(InlineYamlList, _represent_inline_yaml_list)


class Configurator:
    """Coordinate configurator state, events, and dynamic widgets."""

    singleton_device_categories = {
        "camera",
        "daq",
        "remote_focus",
        "mirror",
        "pump",
        "shutter",
        "zoom",
    }

    def __init__(self, root: tk.Tk, splash_screen) -> None:
        self.root = root
        splash_screen.destroy()
        self.root.deiconify()
        try:
            apply_theme(root)
        except Exception:
            logger.exception("Failed to apply GUI theme in configurator.")
        self.view = ConfigurationAssistantWindow(root)
        self.microscope_id = 1
        self.microscope_buttons: dict[str, ttk.Radiobutton] = {}
        self.selected_microscope = tk.StringVar(master=root)
        self.context_microscope_name: Optional[str] = None
        self.device_data: dict[str, tuple[str, str, str]] = {}
        self.device_settings: dict[str, dict[str, object]] = {}
        self.microscope_devices: dict[
            str, list[tuple[str, str, str, dict[str, object]]]
        ] = {}
        self.displayed_microscope_name: Optional[str] = None
        self.active_device_item_id: Optional[str] = None
        self.value_variables: dict[str, tk.Variable] = {}
        self.collection_rows: dict[str, list[dict[str, tk.Variable]]] = {}
        self.stage_axis_range_frame: Optional[ttk.Frame] = None
        self.stage_axis_setting_names: set[str] = set()
        self.device_dialog: Optional[AddDeviceDialog] = None
        self.rename_dialog: Optional[RenameMicroscopeDialog] = None
        self.editing_item_id: Optional[str] = None
        self.last_configuration_path: Optional[Path] = None

        self.microscope_menu = tk.Menu(root, tearoff=False)
        self.microscope_menu.add_command(label="Rename", command=self.rename_microscope)
        self.microscope_menu.add_command(label="Delete", command=self.delete_microscope)
        self._bind_events()
        self.add_microscope("Microscope-0")

    def _bind_events(self) -> None:
        """Connect all static view controls to controller handlers."""
        self.view.top_window.cancel_button.config(command=self.on_cancel)
        self.view.top_window.new_button.config(command=self.new_configuration)
        self.view.top_window.load_button.config(command=self.load_configuration)
        self.view.top_window.save_button.config(command=self.save_configuration)
        self.view.top_window.add_button.config(command=self.add_next_microscope)
        self.view.devices_frame.add_button.config(command=self.show_add_device_dialog)
        self.view.devices_frame.edit_button.config(command=self.show_edit_device_dialog)
        self.view.devices_frame.delete_button.config(
            command=self.delete_selected_device
        )
        self.view.devices_frame.device_list.bind(
            "<<TreeviewSelect>>", self.show_device_info
        )
        self.view.device_info_frame.settings_frame.bind(
            "<Configure>", self.update_scrollregion
        )
        self.view.device_info_frame.settings_canvas.bind(
            "<Configure>", self.resize_settings_form
        )
        self.view.device_info_frame.horizontal_scrollbar.config(
            command=self.view.device_info_frame.settings_canvas.xview
        )
        self.view.device_info_frame.settings_canvas.config(
            xscrollcommand=self.view.device_info_frame.horizontal_scrollbar.set
        )

    def on_cancel(self) -> None:
        """Close the configurator application."""
        self.root.destroy()

    def new_configuration(self) -> None:
        """Confirm and reset the configurator to a clean configuration."""
        confirmed = messagebox.askyesno(
            "New Configuration",
            "Create a clean new configuration?\n\nAll current microscopes, "
            "devices, and entered settings will be removed.",
            parent=self.root,
        )
        if not confirmed:
            return
        for button in self.microscope_buttons.values():
            button.destroy()
        self.clear_tree(self.view.devices_frame.device_list)
        self.microscope_buttons.clear()
        self.device_data.clear()
        self.device_settings.clear()
        self.microscope_devices.clear()
        self.value_variables.clear()
        self.collection_rows.clear()
        self.stage_axis_setting_names.clear()
        self.stage_axis_range_frame = None
        self.active_device_item_id = None
        self.displayed_microscope_name = None
        self.context_microscope_name = None
        self.selected_microscope.set("")
        self.microscope_id = 1
        self.render_device_info({})
        self.add_microscope("Microscope-0")

    def load_configuration(self) -> None:
        """Choose a YAML file and populate the configurator from its devices."""
        filename = filedialog.askopenfilename(
            parent=self.root,
            title="Load Configuration",
            filetypes=(("YAML files", "*.yaml *.yml"), ("All files", "*")),
        )
        if not filename:
            return
        try:
            with open(filename, encoding="utf-8") as configuration_file:
                configuration = yaml.safe_load(configuration_file)
            microscopes = (
                configuration.get("microscopes")
                if isinstance(configuration, dict)
                else None
            )
            if not isinstance(microscopes, dict):
                raise yaml.YAMLError(
                    "The configuration must contain a microscopes mapping."
                )
        except (OSError, yaml.YAMLError) as error:
            messagebox.showerror(
                "Load Configuration",
                f"Could not load configuration:\n{error}",
                parent=self.root,
            )
            return
        if self.device_data and not messagebox.askyesno(
            "Load Configuration",
            "Loading a configuration will replace all current inputs. Continue?",
            parent=self.root,
        ):
            return
        self.clear_loaded_configuration()
        self.last_configuration_path = Path(filename)
        for microscope_name, microscope_config in microscopes.items():
            self.add_microscope(str(microscope_name))
            if isinstance(microscope_config, dict):
                self.load_microscope_devices(str(microscope_name), microscope_config)
        if not self.microscope_buttons:
            self.add_microscope("Microscope-0")
        else:
            first_microscope = next(iter(self.microscope_buttons))
            self.selected_microscope.set(first_microscope)
            self.show_selected_microscope_devices()

    def clear_loaded_configuration(self) -> None:
        """Clear configuration widgets and controller state before loading a file."""
        for button in self.microscope_buttons.values():
            button.destroy()
        self.clear_tree(self.view.devices_frame.device_list)
        self.microscope_buttons.clear()
        self.device_data.clear()
        self.device_settings.clear()
        self.microscope_devices.clear()
        self.value_variables.clear()
        self.collection_rows.clear()
        self.stage_axis_setting_names.clear()
        self.stage_axis_range_frame = None
        self.active_device_item_id = None
        self.displayed_microscope_name = None
        self.selected_microscope.set("")
        self.microscope_id = 1
        self.render_device_info({})

    def load_microscope_devices(
        self, microscope_name: str, configuration: dict
    ) -> None:
        """Add every recognizable device from one microscope configuration."""
        for category, category_config in configuration.items():
            if category == "stage" and isinstance(category_config, dict):
                for hardware in category_config.get("hardware", []):
                    if isinstance(hardware, dict):
                        self.load_device_from_configuration(
                            microscope_name,
                            category,
                            {**category_config, "hardware": hardware},
                        )
            elif isinstance(category_config, list):
                for device in category_config:
                    if isinstance(device, dict):
                        self.load_device_from_configuration(
                            microscope_name, category, device
                        )
            elif isinstance(category_config, dict):
                self.load_device_from_configuration(
                    microscope_name, category, category_config
                )

    def load_device_from_configuration(
        self, microscope_name: str, category: str, configuration: dict
    ) -> None:
        """Insert one YAML device and retain its matching schema values."""
        hardware = configuration.get("hardware", {})
        device_type = (
            self.laser_device_type(configuration)
            if category == "laser"
            else hardware.get("type")
        )
        if not isinstance(device_type, str):
            return
        resolved = self.resolve_device_type(category, device_type)
        if resolved is None:
            logger.warning(
                "Could not resolve %s device type %s.", category, device_type
            )
            return
        manufacturer, model = resolved
        existing_devices = self.microscope_devices.setdefault(microscope_name, [])
        if category in self.singleton_device_categories and any(
            device[0] == category for device in existing_devices
        ):
            logger.warning(
                "Skipping an additional %s device for microscope %s.",
                category,
                microscope_name,
            )
            return
        existing_devices.append(
            (
                category,
                manufacturer,
                model,
                self.settings_from_configuration(
                    category, manufacturer, model, configuration
                ),
            )
        )

    @staticmethod
    def laser_device_type(configuration: dict) -> str:
        """Resolve a laser type from its on/off and power hardware types."""
        power_type = Configurator.configuration_path_value(
            configuration, "power/hardware/type"
        )
        onoff_type = Configurator.configuration_path_value(
            configuration, "onoff/hardware/type"
        )
        if not Configurator.is_synthetic_laser_type(onoff_type):
            return onoff_type
        if not Configurator.is_synthetic_laser_type(power_type):
            return power_type
        return "Synthetic"

    @staticmethod
    def is_synthetic_laser_type(device_type: object) -> bool:
        """Return whether a simple or qualified laser type is synthetic."""
        return not isinstance(device_type, str) or any(
            part.lower().startswith("synthetic") for part in device_type.split(".")
        )

    @staticmethod
    def laser_control_hardware_path(configuration: dict) -> Optional[str]:
        """Return the laser control branch selected by its hardware-type rule."""
        onoff_type = configuration.get("onoff/hardware/type")
        if onoff_type is None:
            onoff_type = Configurator.configuration_path_value(
                configuration, "onoff/hardware/type"
            )
        if not Configurator.is_synthetic_laser_type(onoff_type):
            return "onoff/hardware"

        power_type = configuration.get("power/hardware/type")
        if power_type is None:
            power_type = Configurator.configuration_path_value(
                configuration, "power/hardware/type"
            )
        if not Configurator.is_synthetic_laser_type(power_type):
            return "power/hardware"
        return None

    def store_visible_microscope_devices(self) -> None:
        """Persist the current device panel before changing microscopes."""
        if self.displayed_microscope_name is None:
            return
        self.store_active_device_settings()
        self.microscope_devices[self.displayed_microscope_name] = [
            (*self.device_data[item_id], self.device_settings.get(item_id, {}))
            for item_id in self.view.devices_frame.device_list.get_children()
        ]

    def show_selected_microscope_devices(self) -> None:
        """Display only the devices belonging to the selected microscope."""
        self.store_visible_microscope_devices()
        self.clear_tree(self.view.devices_frame.device_list)
        self.device_data.clear()
        self.device_settings.clear()
        self.active_device_item_id = None
        self.render_device_info({})
        microscope_name = self.selected_microscope.get()
        self.displayed_microscope_name = microscope_name
        for category, manufacturer, model, settings in self.microscope_devices.get(
            microscope_name, []
        ):
            item_id = self.view.devices_frame.device_list.insert(
                "",
                tk.END,
                text=(
                    f"{self.format_category_name(category)}: "
                    f"{self.format_manufacturer_name(manufacturer)} - "
                    f"{self.format_model_name(model, category)}"
                ),
            )
            self.device_data[item_id] = (category, manufacturer, model)
            self.device_settings[item_id] = settings.copy()

    @classmethod
    def resolve_device_type(
        cls, category: str, device_type: str
    ) -> Optional[tuple[str, str]]:
        """Match a YAML type to an optional manufacturer and required model name.

        YAML may name a model directly (``NI``), use its full class-style name
        (``NIDAQ``), or qualify either form with ``manufacturer.``.
        """
        canonical_type = canonical_device_type(category, device_type)
        if canonical_type is None or "." not in canonical_type:
            return None
        manufacturer, model = canonical_type.split(".", maxsplit=1)
        suffix = category_model_suffix(category)
        class_name = model if model.endswith(suffix) else model + suffix
        for available_model in cls.get_device_models(category, manufacturer):
            if available_model.casefold() == class_name.casefold():
                return manufacturer, available_model
        return None

    @staticmethod
    def configuration_path_value(configuration: dict, path: str) -> object:
        """Return a nested configuration value, or ``None`` when it is absent."""
        value: object = configuration
        for part in path.split("/"):
            if not isinstance(value, dict) or part not in value:
                return None
            value = value[part]
        return value

    def settings_from_configuration(
        self, category: str, manufacturer: str, model: str, configuration: dict
    ) -> dict[str, object]:
        """Extract known schema values from one YAML device configuration."""
        schema = self.get_configuration_schema(category, manufacturer, model)
        connection_names = set(get_connect_params(category, manufacturer, model))
        connection_names.update({"port", "baudrate", "timeout", "serial_number"})
        settings = {}
        for name, spec in schema.items():
            if isinstance(spec, CollectionSpec) and spec.storage == "parallel_mappings":
                settings[name] = {
                    field: self.configuration_path_value(configuration, field) or {}
                    for field in spec.storage_fields or ()
                }
                continue
            if category == "stage" and name == "joystick_axes":
                joystick_axes = configuration.get("joystick_axes", [])
                if isinstance(joystick_axes, (list, tuple)):
                    settings[name] = ", ".join(str(axis) for axis in joystick_axes)
                elif isinstance(joystick_axes, str):
                    settings[name] = joystick_axes
                continue
            if category == "stage" and name == "coupled_axes":
                coupled_axes = configuration.get("coupled_axes", {})
                axes = self.configuration_path_value(configuration, "hardware/axes")
                if isinstance(coupled_axes, dict) and isinstance(axes, list):
                    pairs = [
                        f"{axis}:{coupled_axes[axis]}"
                        for axis in axes
                        if coupled_axes.get(axis) is not None
                    ]
                    if pairs:
                        settings[name] = ", ".join(pairs)
                continue
            path = name
            if category == "stage" and name in {
                "axes",
                "axes_mapping",
                "feedback_alignment",
            }:
                path = f"hardware/{name}"
            elif category == "laser" and "/" not in name and name in connection_names:
                hardware_path = self.laser_control_hardware_path(configuration)
                if hardware_path is None:
                    continue
                path = f"{hardware_path}/{name}"
            elif "/" not in name and name in connection_names:
                path = f"hardware/{name}"
            value = self.configuration_path_value(configuration, path)
            if (
                category == "laser"
                and name in {"power/hardware/type", "onoff/hardware/type"}
                and isinstance(value, str)
            ):
                resolved_type = self.resolve_device_type(category, value)
                if resolved_type is not None:
                    value = self.format_model_name(resolved_type[1], category)
            if value is not None:
                settings[name] = value
        if category == "stage":
            for axis in (
                self.configuration_path_value(configuration, "hardware/axes") or []
            ):
                for suffix in ("min", "max", "home", "offset"):
                    name = f"{axis}_{suffix}"
                    if name in configuration:
                        settings[name] = configuration[name]
                name = f"flip_{axis}"
                if name in configuration:
                    settings[name] = configuration[name]
        return settings

    def add_next_microscope(self) -> None:
        """Add and select the next default-named microscope."""
        name = "Microscope-{}".format(self.microscope_id)
        self.add_microscope(name)
        self.microscope_id += 1
        self.selected_microscope.set(name)
        self.show_selected_microscope_devices()

    def add_microscope(self, name: str) -> None:
        """Create and display one microscope selection button."""
        button = ttk.Radiobutton(
            self.view.microscope_frame,
            text=name,
            value=name,
            variable=self.selected_microscope,
            style="Configurator.TRadiobutton",
            command=self.show_selected_microscope_devices,
        )
        button.grid(
            row=0,
            column=len(self.microscope_buttons),
            sticky=tk.W,
            padx=get_theme_space_px(3),
            pady=get_theme_padding_px((1, 1)),
        )
        # Button-3 is the usual right click; Button-2 and Control-click cover
        # the equivalent gestures used by macOS Tk.
        for sequence in ("<Button-3>", "<Button-2>", "<Control-Button-1>"):
            button.bind(sequence, self.show_microscope_menu, add="+")
        self.microscope_buttons[name] = button
        self.microscope_devices.setdefault(name, [])
        if not self.selected_microscope.get():
            self.selected_microscope.set(name)

    def show_microscope_menu(self, event: tk.Event) -> str:
        """Show the Rename/Delete menu for the microscope button clicked."""
        try:
            self.context_microscope_name = event.widget.cget("text")
            self.microscope_menu.tk_popup(event.x_root, event.y_root)
        except tk.TclError:
            return "break"
        finally:
            try:
                self.microscope_menu.grab_release()
            except tk.TclError:
                pass
        return "break"

    def rename_microscope(self) -> None:
        """Open a controller-driven rename dialog for the context microscope."""
        if self.context_microscope_name is None:
            return
        dialog = RenameMicroscopeDialog(self.root, self.context_microscope_name)
        self.rename_dialog = dialog
        dialog.ok_button.config(command=self.confirm_microscope_rename)
        dialog.cancel_button.config(command=dialog.destroy)
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.bind("<Return>", self.confirm_microscope_rename)
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.name_entry.focus_set()
        dialog.name_entry.selection_range(0, tk.END)
        dialog.grab_set()

    def confirm_microscope_rename(self, _event: Optional[tk.Event] = None) -> None:
        """Apply the pending rename if it is unique and non-empty."""
        if self.rename_dialog is None or self.context_microscope_name is None:
            return
        new_name = self.rename_dialog.name_var.get().strip()
        old_name = self.context_microscope_name
        if (
            new_name
            and new_name != old_name
            and new_name not in self.microscope_buttons
        ):
            button = self.microscope_buttons.pop(old_name)
            button.config(text=new_name, value=new_name)
            self.microscope_buttons[new_name] = button
            self.microscope_devices[new_name] = self.microscope_devices.pop(
                old_name, []
            )
            if self.displayed_microscope_name == old_name:
                self.displayed_microscope_name = new_name
            if self.selected_microscope.get() == old_name:
                self.selected_microscope.set(new_name)
        self.rename_dialog.destroy()
        self.rename_dialog = None

    def delete_microscope(self) -> None:
        """Delete the microscope targeted by the context menu."""
        name = self.context_microscope_name
        if name is None or name not in self.microscope_buttons:
            return
        self.microscope_buttons.pop(name).destroy()
        self.microscope_devices.pop(name, None)
        if self.selected_microscope.get() == name:
            self.selected_microscope.set(next(iter(self.microscope_buttons), ""))
            self.displayed_microscope_name = None
            self.show_selected_microscope_devices()
        for column, button in enumerate(self.microscope_buttons.values()):
            button.grid_configure(row=0, column=column)
        self.context_microscope_name = None

    def show_add_device_dialog(self) -> None:
        """Open the Add Device selection dialog."""
        self.editing_item_id = None
        self.open_device_dialog("Add Device", "Add")

    def show_edit_device_dialog(self) -> None:
        """Open the selected device in an Edit Device dialog."""
        selected = self.selected_device()
        if selected is None:
            return
        self.editing_item_id, initial = selected
        self.open_device_dialog("Edit Device", "Update", initial)

    def open_device_dialog(
        self,
        title: str,
        action_text: str,
        initial: Optional[tuple[str, str, str]] = None,
    ) -> None:
        """Build a device dialog and populate its controller-owned lists."""
        dialog = AddDeviceDialog(self.root, title, action_text)
        self.device_dialog = dialog
        for category in self.get_device_categories():
            dialog.categories_list.insert(
                "", tk.END, iid=category, text=self.format_category_name(category)
            )
        dialog.action_button.config(command=self.confirm_device_dialog)
        if initial is not None:
            category, manufacturer, model = initial
            dialog.categories_list.selection_set(category)
            self.populate_manufacturers()
            dialog.manufacturers_list.selection_set(manufacturer)
            self.populate_models()
            if dialog.models_list.exists(model):
                dialog.models_list.selection_set(model)
        dialog.categories_list.bind("<<TreeviewSelect>>", self.populate_manufacturers)
        dialog.manufacturers_list.bind("<<TreeviewSelect>>", self.populate_models)

    def populate_manufacturers(self, _event: Optional[tk.Event] = None) -> None:
        """Fill manufacturers for the selected category."""
        if self.device_dialog is None:
            return
        selection = self.device_dialog.categories_list.selection()
        if not selection:
            return
        self.clear_tree(self.device_dialog.manufacturers_list)
        self.clear_tree(self.device_dialog.models_list)
        for manufacturer in self.get_device_manufacturers(selection[0]):
            self.device_dialog.manufacturers_list.insert(
                "",
                tk.END,
                iid=manufacturer,
                text=self.format_manufacturer_name(manufacturer),
            )

    def populate_models(self, _event: Optional[tk.Event] = None) -> None:
        """Fill models for the selected category and manufacturer."""
        if self.device_dialog is None:
            return
        categories = self.device_dialog.categories_list.selection()
        manufacturers = self.device_dialog.manufacturers_list.selection()
        if not categories or not manufacturers:
            return
        category, manufacturer = categories[0], manufacturers[0]
        self.clear_tree(self.device_dialog.models_list)
        models = self.get_device_models(category, manufacturer)
        if not models:
            self.device_dialog.models_list.insert(
                "",
                tk.END,
                iid=manufacturer,
                text=self.format_manufacturer_name(manufacturer),
            )
            return
        for model in models:
            self.device_dialog.models_list.insert(
                "", tk.END, iid=model, text=self.format_model_name(model, category)
            )

    def confirm_device_dialog(self) -> None:
        """Add or update a device from the selections in the active dialog."""
        if self.device_dialog is None:
            return
        categories = self.device_dialog.categories_list.selection()
        manufacturers = self.device_dialog.manufacturers_list.selection()
        models = self.device_dialog.models_list.selection()
        if not categories or not manufacturers or not models:
            return
        category, manufacturer, model = categories[0], manufacturers[0], models[0]
        if self.displayed_microscope_name is None:
            self.displayed_microscope_name = self.selected_microscope.get()
        if self.category_is_already_configured(category):
            messagebox.showwarning(
                "One Device Per Microscope",
                f"{self.format_category_name(category)} is already configured for "
                "this microscope. Remove it before adding another one.",
                parent=self.device_dialog,
            )
            return
        name = "{}: {} - {}".format(
            self.format_category_name(category),
            self.format_manufacturer_name(manufacturer),
            self.format_model_name(model, category),
        )
        if self.editing_item_id is None:
            item_id = self.view.devices_frame.device_list.insert("", tk.END, text=name)
            self.device_settings[item_id] = self.initial_device_settings(
                category, model
            )
        else:
            item_id = self.editing_item_id
            previous_device = self.device_data[item_id]
            self.store_active_device_settings()
            self.view.devices_frame.device_list.item(item_id, text=name)
            if previous_device != (category, manufacturer, model):
                # Settings belong to a device type. Do not carry an old form
                # into a different category, manufacturer, or model.
                self.device_settings[item_id] = self.initial_device_settings(
                    category, model
                )
                self.active_device_item_id = None
            else:
                self.device_settings.setdefault(item_id, {})
        self.device_data[item_id] = (category, manufacturer, model)
        self.view.devices_frame.device_list.selection_set(item_id)
        self.view.devices_frame.device_list.focus(item_id)
        self.device_dialog.destroy()
        self.device_dialog = None
        self.editing_item_id = None
        self.show_device_info()
        self.store_visible_microscope_devices()

    @staticmethod
    def initial_device_settings(category: str, model: str) -> dict[str, object]:
        """Return initial values that depend on the selected device model."""
        if category != "laser":
            return {}
        laser_type = Configurator.format_model_name(model, category)
        if laser_type not in {"NI", "ASI", "Synthetic"}:
            return {}
        return {
            "power/hardware/type": laser_type,
            "onoff/hardware/type": laser_type,
        }

    def category_is_already_configured(self, category: str) -> bool:
        """Return whether adding or changing would duplicate a singleton category."""
        if category not in self.singleton_device_categories:
            return False
        return any(
            item_id != self.editing_item_id and device[0] == category
            for item_id, device in self.device_data.items()
        )

    def selected_device(self) -> Optional[tuple[str, tuple[str, str, str]]]:
        """Return the selected device item and its controller-owned data."""
        selection = self.view.devices_frame.device_list.selection()
        if not selection:
            return None
        return selection[0], self.device_data[selection[0]]

    def delete_selected_device(self) -> None:
        """Confirm and delete the device selected in the device list."""
        selected = self.selected_device()
        if selected is None:
            return
        item_id, _ = selected
        name = self.view.devices_frame.device_list.item(item_id, "text")
        if messagebox.askyesno(
            "Delete Device", "Delete '{}' ?".format(name), parent=self.root
        ):
            self.view.devices_frame.device_list.delete(item_id)
            del self.device_data[item_id]
            self.device_settings.pop(item_id, None)
            self.active_device_item_id = None
            self.render_device_info({})
            self.store_visible_microscope_devices()

    def show_device_info(self, _event: Optional[tk.Event] = None) -> None:
        """Render editable settings for the selected device."""
        self.store_active_device_settings()
        selected = self.selected_device()
        if selected is None:
            self.active_device_item_id = None
            self.render_device_info({})
            return
        item_id, (category, manufacturer, model) = selected
        schema = self.get_configuration_schema(category, manufacturer, model)
        self.active_device_item_id = item_id
        self.render_device_info(schema, self.device_settings.get(item_id, {}))

    def store_active_device_settings(self) -> None:
        """Copy the currently visible editors into controller-owned device data."""
        if self.active_device_item_id is None:
            return
        category, manufacturer, model = self.device_data[self.active_device_item_id]
        schema = self.get_configuration_schema(category, manufacturer, model)
        values = {}
        for name, variable in self.value_variables.items():
            value = variable.get()
            spec = schema.get(name)
            if (
                isinstance(spec, SettingSpec)
                and not spec.required
                and not self.setting_value_is_present(value)
            ):
                if spec.default is not None:
                    values[name] = None
                continue
            values[name] = value
        for name, rows in self.collection_rows.items():
            spec = schema.get(name)
            if not isinstance(spec, CollectionSpec):
                continue
            key_field, value_field = spec.key_field, spec.value_field
            if spec.storage == "parallel_mappings":
                values[name] = {
                    field: {
                        row[key_field].get(): row[field].get()
                        for row in rows
                        if row[key_field].get()
                    }
                    for field in spec.storage_fields or ()
                }
            elif spec.storage == "nested_mapping":
                nested_values = {}
                for row in rows:
                    solvent = row["solvent"].get()
                    axis = row["axis"].get()
                    zoom = row["zoom"].get()
                    if solvent and axis and zoom:
                        nested_values.setdefault(solvent, {}).setdefault(axis, {})[
                            zoom
                        ] = row["position"].get()
                values[name] = nested_values
            else:
                values[name] = {
                    row[key_field].get(): row[value_field].get()
                    for row in rows
                    if (
                        key_field in row and value_field in row and row[key_field].get()
                    )
                }
        self.device_settings[self.active_device_item_id] = values

    @staticmethod
    def set_configuration_value(configuration: dict, path: str, value: object) -> None:
        """Set a slash-separated configuration path in a nested dictionary."""
        target = configuration
        parts = path.split("/")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value

    @classmethod
    def saved_device_type(cls, category: str, manufacturer: str, model: str) -> str:
        """Return a YAML device type as ``manufacturer.Model``."""
        model_name = strip_category_model_suffix(category, model)
        if category == "daq":
            return model_name
        return f"{manufacturer}.{model_name}"

    @classmethod
    def saved_laser_control_type(cls, device_type: object) -> object:
        """Return a laser control type in the YAML ``manufacturer.Model`` form."""
        if not isinstance(device_type, str):
            return device_type
        canonical_type = canonical_device_type("laser", device_type)
        if canonical_type is None:
            return device_type
        return canonical_type

    def device_configuration(
        self, category: str, manufacturer: str, model: str, settings: dict[str, object]
    ) -> dict:
        """Convert one configured device into its configuration.yaml section."""
        schema = self.get_configuration_schema(category, manufacturer, model)
        values = {
            name: spec.default
            for name, spec in schema.items()
            if isinstance(spec, SettingSpec) and spec.default is not None
        }
        values.update(settings)
        device_type = self.saved_device_type(category, manufacturer, model)
        device = (
            {"type": device_type}
            if category == "laser"
            else {"hardware": {"type": device_type}}
        )

        connection_names = set(get_connect_params(category, manufacturer, model))
        # those connection names are from SerialDevice and SequenceDevice
        connection_names.update({"port", "baudrate", "timeout", "serial_number"})
        for name, value in values.items():
            spec = schema.get(name)
            if (
                isinstance(spec, SettingSpec)
                and not spec.required
                and not self.setting_value_is_present(value)
            ):
                continue
            if isinstance(spec, CollectionSpec) and spec.storage == "parallel_mappings":
                if (
                    category == "zoom"
                    and name == "zoom_values"
                    and not any(value.values() for value in value.values())
                ):
                    value = {
                        "position": {"N/A": 0},
                        "pixel_size": {"N/A": 1},
                    }
                device.update(value)
            elif name in {"position", "pixel_size", "available_filters"}:
                device[name] = value
            elif "/" in name:
                if category == "laser" and name in {
                    "power/hardware/type",
                    "onoff/hardware/type",
                }:
                    value = self.saved_laser_control_type(value)
                self.set_configuration_value(device, name, value)
            elif category == "stage" and name in {
                "axes",
                "axes_mapping",
            }:
                device["hardware"][name] = InlineYamlList(self.parse_stage_axes(value))
            elif category == "stage" and name == "joystick_axes":
                device[name] = InlineYamlList(self.parse_stage_axes(value))
            elif category == "stage" and name == "coupled_axes":
                coupled_axes = self.parse_coupled_axes(value)
                if coupled_axes:
                    device[name] = coupled_axes
            elif category == "stage" and name.endswith(("_home", "_offset")):
                if self.setting_value_is_present(value):
                    device[name] = value
            elif category == "stage" and (
                name.endswith(("_min", "_max")) or name.startswith("flip_")
            ):
                device[name] = value
            elif category == "stage":
                device["hardware"][name] = value
            elif name in connection_names:
                if category == "laser":
                    hardware_path = self.laser_control_hardware_path(values)
                    if hardware_path is not None:
                        self.set_configuration_value(
                            device, f"{hardware_path}/{name}", value
                        )
                else:
                    device["hardware"][name] = value
            else:
                device[name] = value
        if category == "laser":
            selected_type = self.laser_device_type(device)
            resolved_type = self.resolve_device_type(category, selected_type)
            if resolved_type is not None:
                device["type"] = self.saved_device_type(category, *resolved_type)
            else:
                device["type"] = selected_type
        return device

    def build_configuration(self) -> dict:
        """Build a configuration.yaml-compatible dictionary from added devices."""
        self.store_visible_microscope_devices()
        microscopes = {}
        for microscope_name in self.microscope_buttons:
            devices = self.microscope_devices.get(microscope_name, [])
            microscope = {}
            for category, manufacturer, model, settings in devices:
                device = self.device_configuration(
                    category, manufacturer, model, settings
                )
                self.add_device_to_microscope(microscope, category, device)
            microscopes[microscope_name] = microscope
        return {"microscopes": microscopes}

    @staticmethod
    def add_device_to_microscope(microscope: dict, category: str, device: dict) -> None:
        """Add one serialized device using its category's YAML structure."""
        if category == "stage":
            stage = microscope.setdefault("stage", {"hardware": []})
            stage["hardware"].append(device["hardware"])
            joystick_axes = device.get("joystick_axes", [])
            if joystick_axes:
                combined_axes = list(stage.get("joystick_axes", []))
                for axis in joystick_axes:
                    if axis not in combined_axes:
                        combined_axes.append(axis)
                stage["joystick_axes"] = InlineYamlList(combined_axes)
            coupled_axes = device.get("coupled_axes", {})
            if coupled_axes:
                combined_coupled_axes = dict(stage.get("coupled_axes", {}))
                used_axes = set(combined_coupled_axes) | set(
                    combined_coupled_axes.values()
                )
                for leader, follower in coupled_axes.items():
                    if leader not in used_axes and follower not in used_axes:
                        combined_coupled_axes[leader] = follower
                        used_axes.update({leader, follower})
                stage["coupled_axes"] = combined_coupled_axes
            stage.update(
                {
                    name: value
                    for name, value in device.items()
                    if name not in {"hardware", "joystick_axes", "coupled_axes"}
                }
            )
        elif category in {"filter_wheel", "galvo", "laser"}:
            microscope.setdefault(category, []).append(device)
        elif category not in microscope:
            microscope[category] = device
        elif isinstance(microscope[category], list):
            microscope[category].append(device)
        else:
            microscope[category] = [microscope[category], device]

    def save_configuration(self) -> None:
        """Ask for a YAML path and write the configurator's device configuration."""
        invalid_calibrations = self.invalid_stage_position_calibrations()
        if invalid_calibrations:
            messagebox.showwarning(
                "Save Configuration",
                "Complete or remove each partially entered stage position "
                "calibration before saving:\n\n" + "\n".join(invalid_calibrations),
                parent=self.root,
            )
            return
        missing_settings = self.required_settings_missing_values()
        if missing_settings:
            messagebox.showwarning(
                "Save Configuration",
                "Provide values for the following required settings before saving:\n\n"
                + "\n".join(missing_settings),
                parent=self.root,
            )
            return
        invalid_pixel_sizes = self.invalid_zoom_pixel_sizes()
        if invalid_pixel_sizes:
            messagebox.showwarning(
                "Save Configuration",
                "Zoom pixel sizes must be positive values:\n\n"
                + "\n".join(invalid_pixel_sizes),
                parent=self.root,
            )
            return
        duplicate_wavelengths = self.duplicate_laser_wavelengths()
        if duplicate_wavelengths:
            messagebox.showwarning(
                "Save Configuration",
                "Each laser wavelength must be unique within a microscope:\n\n"
                + "\n".join(duplicate_wavelengths),
                parent=self.root,
            )
            return
        duplicate_wheel_numbers = self.duplicate_filter_wheel_numbers()
        if duplicate_wheel_numbers:
            messagebox.showwarning(
                "Save Configuration",
                "Filter wheels of the same type must use different wheel numbers "
                "within a microscope:\n\n" + "\n".join(duplicate_wheel_numbers),
                parent=self.root,
            )
            return
        dialog_options = {
            "parent": self.root,
            "title": "Save Configuration",
            "defaultextension": ".yaml",
            "filetypes": (("YAML files", "*.yaml *.yml"), ("All files", "*")),
        }
        if self.last_configuration_path is not None:
            dialog_options["initialdir"] = str(self.last_configuration_path.parent)
            dialog_options["initialfile"] = self.last_configuration_path.name
        else:
            dialog_options["initialfile"] = "new-config.yaml"
        filename = filedialog.asksaveasfilename(**dialog_options)
        if not filename:
            return
        try:
            with open(filename, "w", encoding="utf-8") as configuration_file:
                yaml.dump(
                    self.build_configuration(),
                    configuration_file,
                    Dumper=ConfiguratorYamlDumper,
                    sort_keys=False,
                    default_flow_style=False,
                )
        except (OSError, yaml.YAMLError) as error:
            messagebox.showerror(
                "Save Configuration",
                f"Could not save configuration:\n{error}",
                parent=self.root,
            )
            return
        self.last_configuration_path = Path(filename)
        messagebox.showinfo(
            "Save Configuration",
            f"Configuration saved to:\n{filename}",
            parent=self.root,
        )

    @staticmethod
    def setting_value_is_present(value: object) -> bool:
        """Return whether a value satisfies a required configuration setting."""
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, tuple, dict, set)):
            return bool(value)
        return True

    def invalid_stage_position_calibrations(self) -> list[str]:
        """Return partially entered Zoom stage-position calibration rows.

        ``stage_positions`` is stored as a nested mapping, so every row needs a
        solvent, axis, zoom, and position before it can be represented in YAML.
        Empty rows are ignored and may be completed later.
        """
        if self.active_device_item_id is None:
            return []
        category, _, model = self.device_data[self.active_device_item_id]
        if category != "zoom":
            return []

        invalid_rows = []
        field_labels = {
            "solvent": "Solvent",
            "axis": "Stage Axis",
            "zoom": "Zoom",
            "position": "Position",
        }
        for row_index, row in enumerate(
            self.collection_rows.get("stage_positions", []), start=1
        ):
            values = {}
            for name in field_labels:
                try:
                    values[name] = row[name].get()
                except tk.TclError:
                    values[name] = ""
            populated = [
                name
                for name, value in values.items()
                if self.setting_value_is_present(value)
            ]
            if not populated or len(populated) == len(field_labels):
                continue
            missing = [
                label for name, label in field_labels.items() if name not in populated
            ]
            invalid_rows.append(
                f"{self.format_model_name(model, category)}, row {row_index}: "
                + ", ".join(missing)
            )
        return invalid_rows

    def invalid_zoom_pixel_sizes(self) -> list[str]:
        """Return Zoom value rows whose pixel size is not a positive float."""
        invalid_sizes = []
        for microscope_name, devices in self.microscope_devices.items():
            for category, _, model, settings in devices:
                if category != "zoom":
                    continue
                zoom_values = settings.get("zoom_values", {})
                pixel_sizes = (
                    zoom_values.get("pixel_size", {})
                    if isinstance(zoom_values, dict)
                    else {}
                )
                for zoom, pixel_size in pixel_sizes.items():
                    try:
                        is_positive = float(pixel_size) > 0
                    except (TypeError, ValueError):
                        is_positive = False
                    if not is_positive:
                        invalid_sizes.append(
                            f"{microscope_name} / "
                            f"{self.format_model_name(model, category)} "
                            f"({zoom})"
                        )
        return invalid_sizes

    def required_settings_missing_values(self) -> list[str]:
        """Return user-facing descriptions of required settings without values."""
        self.store_visible_microscope_devices()
        missing = []
        for microscope_name, devices in self.microscope_devices.items():
            for category, manufacturer, model, settings in devices:
                schema = self.get_configuration_schema(category, manufacturer, model)
                device_name = (
                    f"{microscope_name} / "
                    f"{self.format_category_name(category)}: "
                    f"{self.format_model_name(model, category)}"
                )
                for name, spec in schema.items():
                    if isinstance(spec, SettingSpec) and spec.required:
                        value = settings.get(name, spec.default)
                        if not self.setting_value_is_present(value):
                            label = spec.label or name.replace("_", " ").title()
                            missing.append(f"{device_name} — {label}")
                    elif isinstance(spec, CollectionSpec) and spec.minimum_items:
                        value = settings.get(name, {})
                        item_count = len(value) if hasattr(value, "__len__") else 0
                        if item_count < spec.minimum_items:
                            label = spec.label or name.replace("_", " ").title()
                            missing.append(
                                f"{device_name} — {label} "
                                f"(at least {spec.minimum_items} required)"
                            )
        return missing

    def duplicate_laser_wavelengths(self) -> list[str]:
        """Return duplicate laser wavelengths grouped by microscope."""
        self.store_visible_microscope_devices()
        duplicates = []
        for microscope_name, devices in self.microscope_devices.items():
            wavelengths = {}
            for category, manufacturer, model, settings in devices:
                if category != "laser":
                    continue
                schema = self.get_configuration_schema(category, manufacturer, model)
                spec = schema.get("wavelength")
                default = spec.default if isinstance(spec, SettingSpec) else None
                wavelength = settings.get("wavelength", default)
                if not self.setting_value_is_present(wavelength):
                    continue
                try:
                    wavelength_key = float(str(wavelength).strip())
                except (TypeError, ValueError):
                    wavelength_key = str(wavelength).strip()
                if wavelength_key in wavelengths:
                    duplicates.append(f"{microscope_name} — {wavelength} nm")
                else:
                    wavelengths[wavelength_key] = wavelength
        return duplicates

    def duplicate_filter_wheel_numbers(self) -> list[str]:
        """Return duplicate wheel numbers for matching filter-wheel types."""
        self.store_visible_microscope_devices()
        duplicates = []
        for microscope_name, devices in self.microscope_devices.items():
            wheel_numbers = {}
            for category, manufacturer, model, settings in devices:
                if category != "filter_wheel":
                    continue
                schema = self.get_configuration_schema(category, manufacturer, model)
                spec = schema.get("hardware/wheel_number")
                default = spec.default if isinstance(spec, SettingSpec) else None
                wheel_number = settings.get("hardware/wheel_number", default)
                if not self.setting_value_is_present(wheel_number):
                    continue
                wheel_type = model.casefold()
                key = (wheel_type, str(wheel_number).strip())
                if key in wheel_numbers:
                    duplicates.append(
                        f"{microscope_name} — "
                        f"{self.format_model_name(model, category)} "
                        f"wheel {wheel_number}"
                    )
                else:
                    wheel_numbers[key] = wheel_number
        return duplicates

    def get_configuration_schema(
        self, category: str, manufacturer: str, model: str
    ) -> dict[str, object]:
        """Resolve the currently available configuration schema for a device.

        Base-class schemas are authoritative. ``get_connect_params`` remains a
        compatibility fallback until concrete device classes declare their own
        ``configuration_schema`` values.
        """
        return get_configuration_schema(category, manufacturer, model)

    def render_device_info(
        self, schema: dict[str, object], values: Optional[dict[str, object]] = None
    ) -> None:
        """Create Property/Value widgets inside the passive Device Info panel."""
        values = values or {}
        frame = self.view.device_info_frame.settings_frame
        for child in frame.winfo_children():
            child.destroy()
        self.value_variables = {}
        self.collection_rows = {}
        self.stage_axis_range_frame = None
        self.stage_axis_setting_names = set()
        for column, heading in enumerate(("Property", "Value")):
            ttk.Label(frame, text=heading, font="TkDefaultFont").grid(
                row=0,
                column=column,
                sticky=tk.W,
                padx=get_theme_space_px(3),
                pady=get_theme_padding_px((1, 1)),
            )
        row = 1
        for name, spec in schema.items():
            if isinstance(spec, CollectionSpec):
                self.render_collection_setting(frame, row, name, spec, values.get(name))
                row += 1
                continue
            label = spec.label or name.replace("_", " ").title()
            property_label = ttk.Label(frame, text=label, font="TkDefaultFont")
            property_label.grid(
                row=row,
                column=0,
                sticky=tk.W,
                padx=get_theme_space_px(3),
                pady=get_theme_padding_px((1, 1)),
            )
            if spec.help_text:
                ConfiguratorTooltip(property_label, spec.help_text)
            variable = self.create_value_variable(spec, values.get(name))
            self.value_variables[name] = variable
            self.create_setting_widget(frame, row, spec, variable)
            row += 1
        if self.active_device_is_stage() and "axes" in self.value_variables:
            self.stage_axis_range_frame = ttk.Frame(frame)
            self.stage_axis_range_frame.grid(
                row=row,
                column=0,
                columnspan=2,
                sticky=tk.EW,
                padx=get_theme_space_px(3),
                pady=get_theme_padding_px((1, 1)),
            )
            self.stage_axis_range_frame.columnconfigure(1, weight=1)
            self.value_variables["axes"].trace_add(
                "write", self.update_stage_axis_range_fields
            )
            self.update_stage_axis_range_fields()

    def active_device_is_stage(self) -> bool:
        """Return whether the visible settings belong to a stage device."""
        return (
            self.active_device_item_id is not None
            and self.device_data[self.active_device_item_id][0] == "stage"
        )

    @staticmethod
    def parse_stage_axes(value: str) -> list[str]:
        """Convert an axes entry into a YAML list, even for one axis."""
        if isinstance(value, (list, tuple)):
            return [str(axis) for axis in value]
        return [
            axis.strip("'\"")
            for axis in re.split(r"[\s,]+", str(value).strip().strip("[]"))
            if axis.strip("'\"")
        ]

    @staticmethod
    def parse_coupled_axes(value: str) -> dict[str, str]:
        """Convert comma-separated ``leader:follower`` pairs into a mapping."""
        if not isinstance(value, str):
            return {}
        coupled_axes = {}
        used_axes = set()
        for pair in value.split(","):
            leader, separator, follower = pair.partition(":")
            leader, follower = leader.strip(), follower.strip()
            if (
                not separator
                or not leader
                or not follower
                or leader == follower
                or leader in used_axes
                or follower in used_axes
            ):
                continue
            coupled_axes[leader] = follower
            used_axes.update({leader, follower})
        return coupled_axes

    def update_stage_axis_range_fields(self, *_args) -> None:
        """Show editable limits and flip flags for the entered stage axes."""
        if self.stage_axis_range_frame is None or self.active_device_item_id is None:
            return
        saved_values = self.device_settings.setdefault(self.active_device_item_id, {})
        previous_names = self.stage_axis_setting_names.copy()
        saved_values.update(
            {
                name: self.value_variables[name].get()
                for name in previous_names
                if name in self.value_variables
            }
        )
        for name in previous_names:
            self.value_variables.pop(name, None)
        self.stage_axis_setting_names = set()
        for child in self.stage_axis_range_frame.winfo_children():
            child.destroy()

        axes = self.parse_stage_axes(self.value_variables["axes"].get())
        row = 0
        for axis in axes:
            for name, spec in (
                (
                    f"{axis}_min",
                    SettingSpec(
                        float,
                        default=-100000.0,
                        label=f"{axis} Minimum",
                        help_text=f"Minimum travel position for the {axis} stage axis.",
                        required=True,
                    ),
                ),
                (
                    f"{axis}_max",
                    SettingSpec(
                        float,
                        default=100000.0,
                        label=f"{axis} Maximum",
                        help_text=f"Maximum travel position for the {axis} stage axis.",
                        required=True,
                    ),
                ),
                (
                    f"{axis}_home",
                    SettingSpec(
                        float,
                        default=None,
                        label=f"{axis} Home",
                        help_text=f"Home position for the {axis} stage axis.",
                        required=False,
                    ),
                ),
                (
                    f"{axis}_offset",
                    SettingSpec(
                        float,
                        default=None,
                        label=f"{axis} Offset",
                        help_text=f"Position offset for the {axis} stage axis.",
                        required=False,
                    ),
                ),
                (
                    f"flip_{axis}",
                    SettingSpec(
                        bool,
                        default=False,
                        label=f"Flip {axis}",
                        help_text=f"Reverse movement direction for the {axis} stage axis.",
                        required=False,
                    ),
                ),
            ):
                ttk.Label(
                    self.stage_axis_range_frame,
                    text=spec.label,
                    font="TkDefaultFont",
                ).grid(
                    row=row,
                    column=0,
                    sticky=tk.W,
                    padx=get_theme_space_px(3),
                    pady=get_theme_padding_px((1, 1)),
                )
                variable = self.create_value_variable(spec, saved_values.get(name))
                self.value_variables[name] = variable
                self.stage_axis_setting_names.add(name)
                self.create_setting_widget(
                    self.stage_axis_range_frame, row, spec, variable
                )
                row += 1
        for name in previous_names - self.stage_axis_setting_names:
            saved_values.pop(name, None)

    def render_collection_setting(
        self,
        parent: ttk.Frame,
        row: int,
        name: str,
        spec: CollectionSpec,
        values: Optional[object] = None,
    ) -> None:
        """Render a repeatable configuration collection as an editable table."""
        collection_frame = ttk.LabelFrame(
            parent,
            text=spec.label or name.replace("_", " ").title(),
        )
        collection_frame.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky=tk.EW,
            padx=get_theme_space_px(3),
            pady=get_theme_padding_px((2, 2)),
        )
        self.collection_rows[name] = []
        if isinstance(values, dict):
            if spec.storage == "parallel_mappings":
                zoom_names = set().union(
                    *(
                        mapping.keys()
                        for mapping in values.values()
                        if isinstance(mapping, dict)
                    )
                )
                for zoom in sorted(zoom_names):
                    row_values = {"zoom": zoom}
                    row_values.update(
                        {
                            field: mapping.get(zoom)
                            for field, mapping in values.items()
                            if isinstance(mapping, dict)
                        }
                    )
                    self.collection_rows[name].append(
                        {
                            field_name: self.create_value_variable(
                                field_spec, row_values.get(field_name)
                            )
                            for field_name, field_spec in spec.item_schema.items()
                        }
                    )
            elif spec.storage == "nested_mapping":
                for solvent, axes in values.items():
                    if not isinstance(axes, dict):
                        continue
                    for axis, zooms in axes.items():
                        if not isinstance(zooms, dict):
                            continue
                        for zoom, position in zooms.items():
                            row_values = {
                                "solvent": solvent,
                                "axis": axis,
                                "zoom": zoom,
                                "position": position,
                            }
                            self.collection_rows[name].append(
                                {
                                    field_name: self.create_value_variable(
                                        field_spec, row_values.get(field_name)
                                    )
                                    for field_name, field_spec in spec.item_schema.items()
                                }
                            )
            else:
                for key, value in values.items():
                    row_data = {
                        field_name: self.create_value_variable(
                            field_spec,
                            (
                                key
                                if field_name == spec.key_field
                                else value if field_name == spec.value_field else None
                            ),
                        )
                        for field_name, field_spec in spec.item_schema.items()
                    }
                    self.collection_rows[name].append(row_data)
        for column, field_name in enumerate(spec.item_schema):
            label = spec.item_schema[field_name].label or field_name.title()
            ttk.Label(collection_frame, text=label, font="TkDefaultFont").grid(
                row=0,
                column=column,
                sticky=tk.W,
                padx=get_theme_space_px(3),
                pady=get_theme_padding_px((1, 1)),
            )
        add_button = ttk.Button(
            collection_frame,
            text=(
                "Add Filter"
                if name == "available_filters"
                else f"Add {(spec.label or name).rstrip('s')}"
            ),
            command=lambda: self.add_collection_row(name, spec, collection_frame),
        )
        add_button.grid(
            row=0,
            column=len(spec.item_schema),
            sticky=tk.E,
            padx=get_theme_space_px(3),
            pady=get_theme_padding_px((1, 1)),
        )
        self.refresh_collection_rows(name, spec, collection_frame)

    def add_collection_row(
        self,
        name: str,
        spec: CollectionSpec,
        parent: ttk.LabelFrame,
    ) -> None:
        """Append a row of editable collection values."""
        row_data = {
            field_name: self.create_value_variable(field_spec)
            for field_name, field_spec in spec.item_schema.items()
        }
        self.collection_rows[name].append(row_data)
        self.refresh_collection_rows(name, spec, parent)

    def refresh_collection_rows(
        self,
        name: str,
        spec: CollectionSpec,
        parent: ttk.LabelFrame,
    ) -> None:
        """Rebuild only the dynamic rows of a collection table."""
        for widget in parent.grid_slaves():
            if int(widget.grid_info()["row"]) >= 2:
                widget.destroy()
        for row_index, row_data in enumerate(self.collection_rows[name], start=2):
            for column, (field_name, field_spec) in enumerate(spec.item_schema.items()):
                self.create_setting_widget(
                    parent,
                    row_index,
                    field_spec,
                    row_data[field_name],
                    column=column,
                )
            ttk.Button(
                parent,
                text="×",
                width=3,
                style="Danger.TButton",
                command=lambda index=row_index - 2: self.delete_collection_row(
                    name, spec, parent, index
                ),
            ).grid(
                row=row_index,
                column=len(spec.item_schema),
                padx=get_theme_space_px(3),
                pady=get_theme_padding_px((1, 1)),
            )

    def delete_collection_row(
        self,
        name: str,
        spec: CollectionSpec,
        parent: ttk.LabelFrame,
        index: int,
    ) -> None:
        """Remove one collection row and redraw its table."""
        del self.collection_rows[name][index]
        self.refresh_collection_rows(name, spec, parent)

    def create_value_variable(
        self, spec: SettingSpec, value: Optional[object] = None
    ) -> tk.Variable:
        """Create a Tk value variable matching the schema's declared type."""
        value = spec.default if value is None else value
        if spec.value_type is bool:
            return tk.BooleanVar(master=self.root, value=bool(value))
        if spec.value_type is int:
            if not spec.required:
                return tk.StringVar(
                    master=self.root,
                    value="" if value is None else str(value),
                )
            return tk.IntVar(master=self.root, value=0 if value is None else value)
        if spec.value_type is float:
            if not spec.required:
                return tk.StringVar(
                    master=self.root,
                    value="" if value is None else str(value),
                )
            return tk.DoubleVar(master=self.root, value=0.0 if value is None else value)
        return tk.StringVar(
            master=self.root,
            value="" if value is None else str(value),
        )

    def create_setting_widget(
        self,
        parent: ttk.Frame,
        row: int,
        spec: SettingSpec,
        variable: tk.Variable,
        column: int = 1,
    ) -> None:
        """Render the editor appropriate for a setting schema definition."""
        grid_options = {
            "row": row,
            "column": column,
            "sticky": tk.EW,
            "padx": get_theme_space_px(3),
            "pady": get_theme_padding_px((1, 1)),
        }
        if spec.value_type is bool:
            ttk.Checkbutton(parent, variable=variable).grid(**grid_options)
            return
        if spec.choices is not None:
            ttk.Combobox(
                parent,
                textvariable=variable,
                values=spec.choices,
                state="readonly",
            ).grid(**grid_options)
            return
        if spec.value_type in (int, float):
            lower_bound = (
                spec.minimum
                if spec.minimum is not None
                else (
                    spec.exclusive_minimum
                    if spec.exclusive_minimum is not None
                    else -1000000
                )
            )
            ValidatedSpinbox(
                parent,
                textvariable=variable,
                from_=lower_bound,
                to=1000000 if spec.maximum is None else spec.maximum,
                increment=(
                    (0.1 if spec.value_type is float else 1)
                    if spec.step is None
                    else spec.step
                ),
                required=spec.required,
                value_type=spec.value_type,
            ).grid(**grid_options)
            return
        ttk.Entry(parent, textvariable=variable, style="DeviceInfo.TEntry").grid(
            **grid_options
        )

    def update_scrollregion(self, _event: tk.Event) -> None:
        """Update horizontal scrolling for dynamically created setting widgets."""
        canvas = self.view.device_info_frame.settings_canvas
        canvas.configure(scrollregion=canvas.bbox(tk.ALL))

    def resize_settings_form(self, event: tk.Event) -> None:
        """Expand settings values with the panel while retaining a minimum width."""
        self.view.device_info_frame.settings_canvas.itemconfigure(
            self.view.device_info_frame.settings_window, width=max(330, event.width)
        )

    @staticmethod
    def clear_tree(tree: ttk.Treeview) -> None:
        """Delete all rows from a Treeview."""
        for item in tree.get_children():
            tree.delete(item)

    @classmethod
    def get_device_categories(cls) -> list[str]:
        """Return device category package names, excluding APIs and caches."""
        return sorted(
            path.name
            for path in device_directory().iterdir()
            if path.is_dir() and path.name != "APIs" and not path.name.startswith("__")
        )

    @classmethod
    def get_device_manufacturers(cls, category: str) -> list[str]:
        """Return Python manufacturer modules for a category."""
        return sorted(
            path.stem
            for path in (device_directory() / category).glob("*.py")
            if path.stem not in {"__init__", "base"}
        )

    @classmethod
    def get_device_models(cls, category: str, manufacturer: str) -> list[str]:
        """Return non-base device classes inheriting from the category base class."""
        parent = category_base_class_name(category)
        return [
            name
            for name in module_classes(category, manufacturer)
            if not name.endswith("Base")
            and class_inherits(category, manufacturer, name, parent)
        ]

    @staticmethod
    def format_category_name(name: str) -> str:
        return name.replace("_", " ").title()

    @staticmethod
    def format_manufacturer_name(name: str) -> str:
        return (
            "Virtual Device" if name == "synthetic" else name.replace("_", " ").title()
        )

    @staticmethod
    def format_model_name(name: str, category: str) -> str:
        suffix = "".join(word.title() for word in category.split("_"))
        return name[: -len(suffix)] if name.endswith(suffix) else name
