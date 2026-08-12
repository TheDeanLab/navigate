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
import ast
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Optional

# Local Imports
from navigate.view.configurator_application_window import (
    AddDeviceDialog,
    ConfigurationAssistantWindow,
    RenameMicroscopeDialog,
)
from navigate.view.theme import apply_theme, get_theme_padding_px, get_theme_space_px

# Logger Setup
import logging

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Configurator:
    """Coordinate configurator state, events, and dynamic widgets."""

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
        self.value_variables: dict[str, tk.StringVar] = {}
        self.device_dialog: Optional[AddDeviceDialog] = None
        self.rename_dialog: Optional[RenameMicroscopeDialog] = None
        self.editing_item_id: Optional[str] = None

        self.microscope_menu = tk.Menu(root, tearoff=False)
        self.microscope_menu.add_command(label="Rename", command=self.rename_microscope)
        self.microscope_menu.add_command(label="Delete", command=self.delete_microscope)
        self._bind_events()
        self.add_microscope("Microscope-0")

    def _bind_events(self) -> None:
        """Connect all static view controls to controller handlers."""
        self.view.top_window.cancel_button.config(command=self.on_cancel)
        self.view.top_window.add_button.config(command=self.add_next_microscope)
        self.view.devices_frame.add_button.config(command=self.show_add_device_dialog)
        self.view.devices_frame.edit_button.config(command=self.show_edit_device_dialog)
        self.view.devices_frame.delete_button.config(command=self.delete_selected_device)
        self.view.devices_frame.device_list.bind("<<TreeviewSelect>>", self.show_device_info)
        self.view.device_info_frame.settings_frame.bind("<Configure>", self.update_scrollregion)
        self.view.device_info_frame.settings_canvas.bind("<Configure>", self.resize_settings_form)
        self.view.device_info_frame.horizontal_scrollbar.config(
            command=self.view.device_info_frame.settings_canvas.xview
        )
        self.view.device_info_frame.settings_canvas.config(
            xscrollcommand=self.view.device_info_frame.horizontal_scrollbar.set
        )

    def on_cancel(self) -> None:
        """Close the configurator application."""
        self.root.destroy()

    def add_next_microscope(self) -> None:
        """Add the next default-named microscope."""
        self.add_microscope("Microscope-{}".format(self.microscope_id))
        self.microscope_id += 1

    def add_microscope(self, name: str) -> None:
        """Create and display one microscope selection button."""
        button = ttk.Radiobutton(
            self.view.microscope_frame,
            text=name,
            value=name,
            variable=self.selected_microscope,
            style="Configurator.TRadiobutton",
        )
        button.grid(row=0, column=len(self.microscope_buttons), sticky=tk.W, padx=get_theme_space_px(3), pady=get_theme_padding_px((1, 1)))
        button.bind("<Button-3>", self.show_microscope_menu)
        button.bind("<Control-Button-1>", self.show_microscope_menu)
        self.microscope_buttons[name] = button
        if not self.selected_microscope.get():
            self.selected_microscope.set(name)

    def show_microscope_menu(self, event: tk.Event) -> None:
        """Show the Rename/Delete menu for the microscope button clicked."""
        try:
            self.context_microscope_name = event.widget.cget("text")
            self.microscope_menu.tk_popup(event.x_root, event.y_root)
        except tk.TclError:
            return
        finally:
            try:
                self.microscope_menu.grab_release()
            except tk.TclError:
                pass

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
        if new_name and new_name != old_name and new_name not in self.microscope_buttons:
            button = self.microscope_buttons.pop(old_name)
            button.config(text=new_name, value=new_name)
            self.microscope_buttons[new_name] = button
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
        if self.selected_microscope.get() == name:
            self.selected_microscope.set(next(iter(self.microscope_buttons), ""))
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
            dialog.categories_list.insert("", tk.END, iid=category, text=self.format_category_name(category))
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
            self.device_dialog.manufacturers_list.insert("", tk.END, iid=manufacturer, text=self.format_manufacturer_name(manufacturer))

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
            self.device_dialog.models_list.insert("", tk.END, iid=manufacturer, text=self.format_manufacturer_name(manufacturer))
            return
        for model in models:
            self.device_dialog.models_list.insert("", tk.END, iid=model, text=self.format_model_name(model, category))

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
        name = "{}: {} - {}".format(self.format_category_name(category), self.format_manufacturer_name(manufacturer), self.format_model_name(model, category))
        if self.editing_item_id is None:
            item_id = self.view.devices_frame.device_list.insert("", tk.END, text=name)
        else:
            item_id = self.editing_item_id
            self.view.devices_frame.device_list.item(item_id, text=name)
        self.device_data[item_id] = (category, manufacturer, model)
        self.device_dialog.destroy()
        self.device_dialog = None
        self.editing_item_id = None

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
        if messagebox.askyesno("Delete Device", "Delete '{}' ?".format(name), parent=self.root):
            self.view.devices_frame.device_list.delete(item_id)
            del self.device_data[item_id]
            self.render_device_info({})

    def show_device_info(self, _event: Optional[tk.Event] = None) -> None:
        """Render editable settings for the selected device."""
        selected = self.selected_device()
        if selected is None:
            self.render_device_info({})
            return
        _, (category, manufacturer, model) = selected
        properties: dict[str, str] = {}
        if self.class_inherits(category, manufacturer, model, "SerialDevice"):
            properties.update({"port": "", "baudrate": "", "timeout": ""})
        if self.class_inherits(category, manufacturer, model, "SequenceDevice"):
            properties.setdefault("serial_number", "")
        for property_name in self.get_connect_params(category, manufacturer, model):
            properties.setdefault(property_name, "")
        self.render_device_info(properties)

    def render_device_info(self, properties: dict[str, str]) -> None:
        """Create Property/Value widgets inside the passive Device Info panel."""
        frame = self.view.device_info_frame.settings_frame
        for child in frame.winfo_children():
            child.destroy()
        self.value_variables = {}
        for column, heading in enumerate(("Property", "Value")):
            ttk.Label(frame, text=heading, font="TkDefaultFont").grid(row=0, column=column, sticky=tk.W, padx=get_theme_space_px(3), pady=get_theme_padding_px((1, 1)))
        for row, (name, value) in enumerate(properties.items(), start=1):
            ttk.Label(frame, text=name, font="TkDefaultFont").grid(row=row, column=0, sticky=tk.W, padx=get_theme_space_px(3), pady=get_theme_padding_px((1, 1)))
            variable = tk.StringVar(master=self.root, value=str(value))
            self.value_variables[name] = variable
            ttk.Entry(frame, textvariable=variable, style="DeviceInfo.TEntry").grid(row=row, column=1, sticky=tk.EW, padx=get_theme_space_px(3), pady=get_theme_padding_px((1, 1)))

    def update_scrollregion(self, _event: tk.Event) -> None:
        """Update horizontal scrolling for dynamically created setting widgets."""
        canvas = self.view.device_info_frame.settings_canvas
        canvas.configure(scrollregion=canvas.bbox(tk.ALL))

    def resize_settings_form(self, event: tk.Event) -> None:
        """Expand settings values with the panel while retaining a minimum width."""
        self.view.device_info_frame.settings_canvas.itemconfigure(self.view.device_info_frame.settings_window, width=max(330, event.width))

    @staticmethod
    def clear_tree(tree: ttk.Treeview) -> None:
        """Delete all rows from a Treeview."""
        for item in tree.get_children():
            tree.delete(item)

    @staticmethod
    def device_directory() -> Path:
        return Path(__file__).resolve().parents[1] / "model" / "devices"

    @classmethod
    def get_device_categories(cls) -> list[str]:
        """Return device category package names, excluding APIs and caches."""
        return sorted(path.name for path in cls.device_directory().iterdir() if path.is_dir() and path.name != "APIs" and not path.name.startswith("__"))

    @classmethod
    def get_device_manufacturers(cls, category: str) -> list[str]:
        """Return Python manufacturer modules for a category."""
        return sorted(path.stem for path in (cls.device_directory() / category).glob("*.py") if path.stem not in {"__init__", "base"})

    @classmethod
    def module_classes(cls, category: str, manufacturer: str) -> dict[str, list[str]]:
        """Return class names mapped to directly declared base-class names."""
        module = ast.parse((cls.device_directory() / category / (manufacturer + ".py")).read_text(encoding="utf-8"))
        return {node.name: [base.id if isinstance(base, ast.Name) else base.attr if isinstance(base, ast.Attribute) else "" for base in node.bases] for node in module.body if isinstance(node, ast.ClassDef)}

    @classmethod
    def class_inherits(cls, category: str, manufacturer: str, class_name: str, parent: str) -> bool:
        """Check direct or local indirect inheritance without importing hardware APIs."""
        classes = cls.module_classes(category, manufacturer)
        def inherits(name: str, visited: set[str]) -> bool:
            if name in visited or name not in classes:
                return False
            visited.add(name)
            return any(base == parent or inherits(base, visited) for base in classes[name])
        return inherits(class_name, set())

    @classmethod
    def get_device_models(cls, category: str, manufacturer: str) -> list[str]:
        """Return non-base device classes inheriting from the category base class."""
        parent = "".join(word.title() for word in category.split("_")) + "Base"
        return [name for name in cls.module_classes(category, manufacturer) if not name.endswith("Base") and cls.class_inherits(category, manufacturer, name, parent)]

    @classmethod
    def get_connect_params(cls, category: str, manufacturer: str, class_name: str) -> list[str]:
        """Read literal ``get_connect_params`` values from a class or local ancestor."""
        module = ast.parse((cls.device_directory() / category / (manufacturer + ".py")).read_text(encoding="utf-8"))
        nodes = {node.name: node for node in module.body if isinstance(node, ast.ClassDef)}
        def inspect(name: str, visited: set[str]) -> list[str]:
            if name in visited or name not in nodes:
                return []
            visited.add(name)
            node = nodes[name]
            for function in node.body:
                if isinstance(function, ast.FunctionDef) and function.name == "get_connect_params":
                    for statement in function.body:
                        if isinstance(statement, ast.Return) and isinstance(statement.value, (ast.List, ast.Tuple)):
                            return [value.value for value in statement.value.elts if isinstance(value, ast.Constant) and isinstance(value.value, str)]
            for base in node.bases:
                base_name = base.id if isinstance(base, ast.Name) else base.attr if isinstance(base, ast.Attribute) else ""
                params = inspect(base_name, visited)
                if params:
                    return params
            return []
        return inspect(class_name, set())

    @staticmethod
    def format_category_name(name: str) -> str:
        return name.replace("_", " ").title()

    @staticmethod
    def format_manufacturer_name(name: str) -> str:
        return "Virtual Device" if name == "synthetic" else name.replace("_", " ").title()

    @staticmethod
    def format_model_name(name: str, category: str) -> str:
        suffix = "".join(word.title() for word in category.split("_"))
        return name[: -len(suffix)] if name.endswith(suffix) else name
