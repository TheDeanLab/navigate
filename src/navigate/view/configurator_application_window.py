# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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
from tkinter import ttk
from pathlib import Path
from typing import Callable, Optional

# Local Imports
from navigate.view.theme import (
    get_theme_color,
    get_theme_padding_px,
    get_theme_space_px,
)


class ConfigurationAssistantWindow(ttk.Frame):
    """Base application window for the configurator.

    The action row deliberately mirrors the current configurator so existing
    controller actions can be connected as the new workflow is developed.
    """

    def __init__(self, root: tk.Tk, *args, **kwargs) -> None:
        """Create the configurator window and its top action row."""
        self.root = root
        self.root.title("New Configuration Assistant")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        super().__init__(self.root, *args, **kwargs)
        self.grid(column=0, row=0, sticky=tk.NSEW)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.top_frame = ttk.Frame(self)
        self.top_frame.grid(
            row=0,
            column=0,
            sticky=tk.EW,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )
        self.top_frame.columnconfigure(0, weight=1)

        self.top_window = TopWindow(self.top_frame)
        self.top_window.grid(row=0, column=0, sticky=tk.EW)

        self.microscope_frame = ttk.Frame(self)
        self.microscope_frame.grid(
            row=1,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_padding_px((3, 0)),
        )

        self.selected_microscope = tk.StringVar(master=self)
        self.microscope_buttons: dict[str, ttk.Radiobutton] = {}
        self._context_microscope_name: Optional[str] = None
        self.microscope_menu = tk.Menu(self, tearoff=False)
        self.microscope_menu.add_command(label="Rename", command=self.rename_microscope)
        self.microscope_menu.add_command(label="Delete", command=self.delete_microscope)
        self.add_microscope("Microscope-0")

        self.configuration_frame = ttk.Frame(self)
        self.configuration_frame.grid(
            row=2,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_padding_px((0, 3)),
        )
        self.configuration_frame.columnconfigure(0, weight=0, minsize=300)
        self.configuration_frame.columnconfigure(1, weight=1)
        self.configuration_frame.rowconfigure(0, weight=1)

        self.devices_frame = DevicesFrame(self.configuration_frame)
        self.devices_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.devices_frame.add_button.config(command=self.show_add_device_dialog)
        self.devices_frame.edit_button.config(command=self.show_edit_device_dialog)

        self.device_info_frame = DeviceInfoFrame(self.configuration_frame)
        self.device_info_frame.grid(row=0, column=1, sticky=tk.NSEW)

    def add_microscope(self, name: str) -> None:
        """Add a microscope radio button to the microscope list."""
        if name in self.microscope_buttons:
            raise ValueError(f"A microscope named '{name}' already exists.")

        button = ttk.Radiobutton(
            self.microscope_frame,
            text=name,
            value=name,
            variable=self.selected_microscope,
        )
        button.grid(
            row=0,
            column=len(self.microscope_buttons),
            sticky=tk.W,
            padx=get_theme_space_px(3),
            pady=get_theme_padding_px((1, 1)),
        )
        button.bind("<Button-3>", self.show_microscope_menu)
        button.bind("<Control-Button-1>", self.show_microscope_menu)
        self.microscope_buttons[name] = button
        if not self.selected_microscope.get():
            self.selected_microscope.set(name)

    def show_microscope_menu(self, event: tk.Event) -> None:
        """Show the common microscope context menu for the clicked button."""
        try:
            self._context_microscope_name = event.widget.cget("text")
            self.microscope_menu.tk_popup(event.x_root, event.y_root)
        except tk.TclError:
            # A pending mouse event can arrive after the root window closes.
            return
        finally:
            try:
                self.microscope_menu.grab_release()
            except tk.TclError:
                pass

    def rename_microscope(self) -> None:
        """Rename the microscope selected by the context menu."""
        current_name = self._context_microscope_name
        if current_name is None:
            return

        new_name = RenameMicroscopeDialog.ask(self.root, current_name)
        if not new_name or new_name == current_name:
            return
        if new_name in self.microscope_buttons:
            return

        button = self.microscope_buttons.pop(current_name)
        button.config(text=new_name, value=new_name)
        self.microscope_buttons[new_name] = button
        if self.selected_microscope.get() == current_name:
            self.selected_microscope.set(new_name)
        self._context_microscope_name = new_name

    def delete_microscope(self) -> None:
        """Delete the microscope selected by the context menu."""
        name = self._context_microscope_name
        if name is None:
            return

        button = self.microscope_buttons.pop(name)
        button.destroy()
        if self.selected_microscope.get() == name:
            self.selected_microscope.set(next(iter(self.microscope_buttons), ""))
        self._context_microscope_name = None
        self._reposition_microscopes()

    def _reposition_microscopes(self) -> None:
        """Keep microscope radio buttons contiguous after a deletion."""
        for column, button in enumerate(self.microscope_buttons.values()):
            button.grid_configure(row=0, column=column)

    def show_add_device_dialog(self) -> None:
        """Open the dialog for selecting a device category and device."""
        AddDeviceDialog(self.root, on_add=self.add_device)

    def show_edit_device_dialog(self) -> None:
        """Open the selected device in a dialog where its choices can be updated."""
        selected_device = self.devices_frame.get_selected_device()
        if selected_device is None:
            return
        item_id, device = selected_device
        AddDeviceDialog(
            self.root,
            on_add=lambda category, manufacturer, model: self.update_device(
                item_id, category, manufacturer, model
            ),
            title="Edit Device",
            action_text="Update",
            initial_device=device,
        )

    def add_device(self, category: str, manufacturer: str, model: str) -> None:
        """Add a selected device to the Devices panel."""
        device_name = (
            f"{AddDeviceDialog.format_category_name(category)}: "
            f"{AddDeviceDialog.format_manufacturer_name(manufacturer)} - "
            f"{AddDeviceDialog.format_model_name(model, category)}"
        )
        self.devices_frame.add_device(device_name, category, manufacturer, model)

    def update_device(
        self,
        item_id: str,
        category: str,
        manufacturer: str,
        model: str,
    ) -> None:
        """Update a device listed in the Devices panel."""
        device_name = (
            f"{AddDeviceDialog.format_category_name(category)}: "
            f"{AddDeviceDialog.format_manufacturer_name(manufacturer)} - "
            f"{AddDeviceDialog.format_model_name(model, category)}"
        )
        self.devices_frame.update_device(
            item_id, device_name, category, manufacturer, model
        )


class AddDeviceDialog(tk.Toplevel):
    """Three-column dialog for adding a device to the selected microscope."""

    def __init__(
        self,
        parent: tk.Misc,
        on_add: Callable[[str, str, str], None],
        title: str = "Add Device",
        action_text: str = "Add",
        initial_device: Optional[tuple[str, str, str]] = None,
    ) -> None:
        """Create the dialog and populate its device category column."""
        super().__init__(parent)
        self.title(title)
        self.on_add = on_add
        self.initial_device = initial_device
        self._initializing_selection = initial_device is not None
        self.transient(parent)
        self.geometry("900x480")
        self.minsize(720, 360)
        self.configure(background=get_theme_color("panel_bg"))
        self._configure_category_list_style()

        content = ttk.Frame(self, padding=get_theme_padding_px((3, 3)))
        content.grid(row=0, column=0, sticky=tk.NSEW)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        for column in range(3):
            content.columnconfigure(column, weight=1, uniform="add-device-columns")
        content.rowconfigure(0, weight=1)

        self.categories_frame = ttk.LabelFrame(content, text="Device Categories")
        self.categories_frame.grid(
            row=0,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_padding_px((0, 1)),
        )
        self.categories_frame.columnconfigure(0, weight=1)
        self.categories_frame.rowconfigure(0, weight=1)

        self.categories_list = ttk.Treeview(
            self.categories_frame,
            show="tree",
            selectmode="browse",
            style="AddDevice.Treeview",
        )
        self.categories_list.grid(
            row=0,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )
        for category in self.get_device_categories():
            self.categories_list.insert(
                "",
                tk.END,
                iid=category,
                text=self.format_category_name(category),
            )

        self.manufacturers_frame = ttk.LabelFrame(content, text="Manufacturer")
        self.manufacturers_frame.grid(
            row=0,
            column=1,
            sticky=tk.NSEW,
            padx=get_theme_padding_px((1, 1)),
        )
        self.manufacturers_frame.columnconfigure(0, weight=1)
        self.manufacturers_frame.rowconfigure(0, weight=1)
        self.manufacturers_list = ttk.Treeview(
            self.manufacturers_frame,
            show="tree",
            selectmode="browse",
            style="AddDevice.Treeview",
        )
        self.manufacturers_list.grid(
            row=0,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )

        self.models_frame = ttk.LabelFrame(content, text="Model")
        self.models_frame.grid(
            row=0,
            column=2,
            sticky=tk.NSEW,
            padx=get_theme_padding_px((1, 0)),
        )
        self.models_frame.columnconfigure(0, weight=1)
        self.models_frame.rowconfigure(0, weight=1)
        self.models_list = ttk.Treeview(
            self.models_frame,
            show="tree",
            selectmode="browse",
            style="AddDevice.Treeview",
        )
        self.models_list.grid(
            row=0,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )

        actions = ttk.Frame(self)
        actions.grid(
            row=1,
            column=0,
            sticky=tk.E,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )
        self.add_button = ttk.Button(
            actions, text=action_text, width=8, command=self.add
        )
        self.add_button.grid(row=0, column=0)
        self._select_initial_device()
        self.categories_list.bind(
            "<<TreeviewSelect>>", self.populate_manufacturers
        )
        self.manufacturers_list.bind("<<TreeviewSelect>>", self.populate_models)
        if self._initializing_selection:
            self.after_idle(self._finish_initial_selection)

    @staticmethod
    def get_device_categories() -> list[str]:
        """Return device-package folder names, excluding the API package."""
        devices_directory = Path(__file__).resolve().parents[1] / "model" / "devices"
        return sorted(
            path.name
            for path in devices_directory.iterdir()
            if path.is_dir() and path.name != "APIs" and not path.name.startswith("__")
        )

    @staticmethod
    def format_category_name(category: str) -> str:
        """Convert a package folder name to a readable category label."""
        return category.replace("_", " ").title()

    @staticmethod
    def get_device_manufacturers(category: str) -> list[str]:
        """Return manufacturer modules for a device category."""
        category_directory = (
            Path(__file__).resolve().parents[1] / "model" / "devices" / category
        )
        return sorted(
            path.stem
            for path in category_directory.glob("*.py")
            if path.stem not in {"__init__", "base"}
        )

    @staticmethod
    def format_manufacturer_name(manufacturer: str) -> str:
        """Convert a manufacturer module name to its display label."""
        if manufacturer == "synthetic":
            return "Virtual Device"
        return manufacturer.replace("_", " ").title()

    @staticmethod
    def get_device_models(category: str, manufacturer: str) -> list[str]:
        """Return classes in a module that inherit from the category base class."""
        category_directory = (
            Path(__file__).resolve().parents[1] / "model" / "devices" / category
        )
        module_path = category_directory / f"{manufacturer}.py"
        module = ast.parse(module_path.read_text(encoding="utf-8"))
        class_nodes = [node for node in module.body if isinstance(node, ast.ClassDef)]
        class_bases = {
            node.name: [
                base.id
                if isinstance(base, ast.Name)
                else base.attr
                if isinstance(base, ast.Attribute)
                else ""
                for base in node.bases
            ]
            for node in class_nodes
        }
        base_class_name = "".join(word.title() for word in category.split("_")) + "Base"

        def inherits_category_base(class_name: str, visited: set[str]) -> bool:
            """Determine whether a local class inherits from the category base."""
            if class_name in visited:
                return False
            visited.add(class_name)
            for base_name in class_bases[class_name]:
                if base_name == base_class_name:
                    return True
                if (
                    base_name in class_bases
                    and inherits_category_base(base_name, visited)
                ):
                    return True
            return False

        return [
            class_name
            for class_name in class_bases
            if (
                inherits_category_base(class_name, set())
                and not class_name.endswith("Base")
            )
        ]

    @staticmethod
    def format_model_name(model: str, category: str) -> str:
        """Remove a trailing device-type suffix from a model class name."""
        suffix = "".join(word.title() for word in category.split("_"))
        if model.endswith(suffix):
            return model[: -len(suffix)]
        return model

    def populate_manufacturers(self, _event: Optional[tk.Event] = None) -> None:
        """List manufacturer modules for the selected device category."""
        if _event is not None and self._initializing_selection:
            return
        selection = self.categories_list.selection()
        if not selection:
            return

        for item in self.manufacturers_list.get_children():
            self.manufacturers_list.delete(item)
        for item in self.models_list.get_children():
            self.models_list.delete(item)
        for manufacturer in self.get_device_manufacturers(selection[0]):
            self.manufacturers_list.insert(
                "",
                tk.END,
                iid=manufacturer,
                text=self.format_manufacturer_name(manufacturer),
            )

    def populate_models(self, _event: Optional[tk.Event] = None) -> None:
        """List models inherited from the base class for the chosen manufacturer."""
        if _event is not None and self._initializing_selection:
            return
        category_selection = self.categories_list.selection()
        manufacturer_selection = self.manufacturers_list.selection()
        if not category_selection or not manufacturer_selection:
            return

        for item in self.models_list.get_children():
            self.models_list.delete(item)
        category = category_selection[0]
        manufacturer = manufacturer_selection[0]
        models = self.get_device_models(category, manufacturer)
        if not models:
            self.models_list.insert(
                "",
                tk.END,
                iid=manufacturer,
                text=self.format_manufacturer_name(manufacturer),
            )
            return

        for model in models:
            self.models_list.insert(
                "",
                tk.END,
                iid=model,
                text=self.format_model_name(model, category),
            )

    def add(self) -> None:
        """Add the chosen device and close the dialog."""
        category_selection = self.categories_list.selection()
        manufacturer_selection = self.manufacturers_list.selection()
        model_selection = self.models_list.selection()
        if not category_selection or not manufacturer_selection or not model_selection:
            return
        self.on_add(
            category_selection[0],
            manufacturer_selection[0],
            model_selection[0],
        )
        self.destroy()

    def _select_initial_device(self) -> None:
        """Preselect category, manufacturer, and model for an edit operation."""
        if self.initial_device is None:
            return
        category, manufacturer, model = self.initial_device
        if not self.categories_list.exists(category):
            return
        self.categories_list.selection_set(category)
        self.populate_manufacturers()
        if not self.manufacturers_list.exists(manufacturer):
            return
        self.manufacturers_list.selection_set(manufacturer)
        self.populate_models()
        if self.models_list.exists(model):
            self.models_list.selection_set(model)

    def _finish_initial_selection(self) -> None:
        """Enable user selection callbacks after defaults are fully displayed."""
        self._initializing_selection = False

    @staticmethod
    def _configure_category_list_style() -> None:
        """Apply Navigate's dark colors to the category list."""
        style = ttk.Style()
        input_background = get_theme_color("input_bg")
        text_color = get_theme_color("text")
        style.configure(
            "AddDevice.Treeview",
            background=input_background,
            fieldbackground=input_background,
            foreground=text_color,
        )
        style.map(
            "AddDevice.Treeview",
            background=[("selected", get_theme_color("accent"))],
            foreground=[("selected", text_color)],
        )


class RenameMicroscopeDialog(tk.Toplevel):
    """Dark-themed modal dialog for renaming a microscope."""

    def __init__(self, parent: tk.Misc, current_name: str) -> None:
        """Create the dialog with a pre-filled microscope name field."""
        super().__init__(parent)
        self.result: Optional[str] = None
        self.title("Rename Microscope")
        self.transient(parent)
        self.resizable(False, False)
        self.configure(background=get_theme_color("panel_bg"))
        self._configure_entry_style()

        content = ttk.Frame(self, padding=get_theme_padding_px((3, 3)))
        content.grid(row=0, column=0, sticky=tk.NSEW)
        content.columnconfigure(0, weight=1)

        ttk.Label(content, text="Microscope name:").grid(
            row=0,
            column=0,
            sticky=tk.W,
            pady=get_theme_padding_px((0, 1)),
        )
        self.name_var = tk.StringVar(master=self, value=current_name)
        self.name_entry = ttk.Entry(
            content,
            textvariable=self.name_var,
            style="RenameMicroscope.TEntry",
            width=30,
        )
        self.name_entry.grid(row=1, column=0, sticky=tk.EW)

        actions = ttk.Frame(content)
        actions.grid(
            row=2,
            column=0,
            sticky=tk.E,
            pady=get_theme_padding_px((3, 0)),
        )
        ttk.Button(actions, text="OK", width=8, command=self.confirm).grid(
            row=0,
            column=0,
            padx=get_theme_padding_px((0, 1)),
        )
        ttk.Button(actions, text="Cancel", width=8, command=self.cancel).grid(
            row=0,
            column=1,
        )

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind("<Return>", self.confirm)
        self.bind("<Escape>", self.cancel)
        self.name_entry.focus_set()
        self.name_entry.selection_range(0, tk.END)
        self.grab_set()

    @staticmethod
    def ask(parent: tk.Misc, current_name: str) -> Optional[str]:
        """Show the dialog and return the confirmed name, if any."""
        dialog = RenameMicroscopeDialog(parent, current_name)
        dialog.wait_window()
        return dialog.result

    @staticmethod
    def _configure_entry_style() -> None:
        """Use a flat dark field instead of the native white entry border."""
        input_background = get_theme_color("input_bg")
        style = ttk.Style()
        style.configure(
            "RenameMicroscope.TEntry",
            fieldbackground=input_background,
            foreground=get_theme_color("text"),
            bordercolor=input_background,
            lightcolor=input_background,
            darkcolor=input_background,
            insertcolor=get_theme_color("text"),
            padding=0,
        )

    def confirm(self, _event: Optional[tk.Event] = None) -> None:
        """Return the entered microscope name and close the dialog."""
        self.result = self.name_var.get().strip()
        self.destroy()

    def cancel(self, _event: Optional[tk.Event] = None) -> None:
        """Close the dialog without changing the microscope name."""
        self.destroy()


class DevicesFrame(ttk.LabelFrame):
    """Left-hand third-row panel for configuring microscope devices."""

    def __init__(self, parent: ttk.Frame, *args, **kwargs) -> None:
        """Create the Devices panel title row."""
        super().__init__(parent, text="", width=300, height=200, *args, **kwargs)
        self.grid_propagate(False)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._configure_list_style()

        self.devices_label = ttk.Label(self, text="Devices")
        self.devices_label.grid(
            row=0,
            column=0,
            sticky=tk.W,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )

        self.edit_button = ttk.Button(self, text="Edit", width=5)
        self.edit_button.grid(
            row=0,
            column=1,
            sticky=tk.E,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )

        self.device_list = ttk.Treeview(
            self,
            show="tree",
            selectmode="browse",
            style="Devices.Treeview",
        )
        self.device_list.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_padding_px((0, 3)),
        )
        self.device_data: dict[str, tuple[str, str, str]] = {}

        self.add_button = ttk.Button(self, text="Add", width=5)
        self.add_button.grid(
            row=2,
            column=0,
            sticky=tk.W,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )

    @staticmethod
    def _configure_list_style() -> None:
        """Apply Navigate's dark colors to the device list."""
        style = ttk.Style()
        input_background = get_theme_color("input_bg")
        text_color = get_theme_color("text")
        style.configure(
            "Devices.Treeview",
            background=input_background,
            fieldbackground=input_background,
            foreground=text_color,
        )
        style.map(
            "Devices.Treeview",
            background=[("selected", get_theme_color("accent"))],
            foreground=[("selected", text_color)],
        )

    def add_device(
        self,
        device_name: str,
        category: str,
        manufacturer: str,
        model: str,
    ) -> None:
        """Append a device name to the panel list."""
        item_id = self.device_list.insert("", tk.END, text=device_name)
        self.device_data[item_id] = (category, manufacturer, model)

    def get_selected_device(self) -> Optional[tuple[str, tuple[str, str, str]]]:
        """Return the selected device item and its stored selection values."""
        selection = self.device_list.selection()
        if not selection:
            return None
        item_id = selection[0]
        return item_id, self.device_data[item_id]

    def update_device(
        self,
        item_id: str,
        device_name: str,
        category: str,
        manufacturer: str,
        model: str,
    ) -> None:
        """Replace a listed device's name and stored selection values."""
        self.device_list.item(item_id, text=device_name)
        self.device_data[item_id] = (category, manufacturer, model)


class DeviceInfoFrame(ttk.LabelFrame):
    """Right-hand third-row panel for displaying device information."""

    def __init__(self, parent: ttk.Frame, *args, **kwargs) -> None:
        """Create an empty property/value list for the selected device."""
        super().__init__(parent, text="", *args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._configure_list_style()

        self.device_info_label = ttk.Label(self, text="Device Info")
        self.device_info_label.grid(
            row=0,
            column=0,
            sticky=tk.W,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )

        self.device_info_list = ttk.Treeview(
            self,
            columns=("property", "value"),
            show="headings",
            height=8,
            style="DeviceInfo.Treeview",
        )
        self.device_info_list.heading("property", text="Property")
        self.device_info_list.heading("value", text="Value")
        self.device_info_list.column(
            "property", anchor=tk.W, width=130, stretch=False
        )
        self.device_info_list.column("value", anchor=tk.W, width=160, stretch=False)
        self.device_info_list.grid(
            row=1,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_padding_px((0, 3)),
        )
        self.horizontal_scrollbar = ttk.Scrollbar(
            self,
            orient=tk.HORIZONTAL,
            command=self.device_info_list.xview,
        )
        self.horizontal_scrollbar.grid(
            row=2,
            column=0,
            sticky=tk.EW,
            padx=get_theme_space_px(3),
            pady=get_theme_padding_px((0, 3)),
        )
        self.device_info_list.configure(
            xscrollcommand=self.horizontal_scrollbar.set,
        )
        self.device_info_list.bind("<Configure>", self._resize_columns)

    @staticmethod
    def _configure_list_style() -> None:
        """Apply Navigate's dark theme colors to the device information list."""
        style = ttk.Style()
        input_background = get_theme_color("input_bg")
        surface_background = get_theme_color("surface_bg")
        text_color = get_theme_color("text")
        accent_color = get_theme_color("accent")
        style.configure(
            "DeviceInfo.Treeview",
            background=input_background,
            fieldbackground=input_background,
            foreground=text_color,
        )
        style.map(
            "DeviceInfo.Treeview",
            background=[("selected", accent_color)],
            foreground=[("selected", text_color)],
        )
        style.configure(
            "DeviceInfo.Treeview.Heading",
            background=surface_background,
            foreground=text_color,
        )

    def set_device_info(self, device_info: dict[str, str]) -> None:
        """Replace the displayed device information with ``device_info``."""
        for item in self.device_info_list.get_children():
            self.device_info_list.delete(item)
        for property_name, value in device_info.items():
            self.device_info_list.insert("", tk.END, values=(property_name, value))

    def _resize_columns(self, event: tk.Event) -> None:
        """Expand both columns while preserving horizontal scrolling when narrow."""
        property_width = 130
        value_width = 160
        extra_width = max(0, event.width - property_width - value_width)
        property_width += extra_width // 2
        value_width += extra_width - extra_width // 2
        self.device_info_list.column("property", width=property_width)
        self.device_info_list.column("value", width=value_width)


class TopWindow(ttk.Frame):
    """Top action row for the new configurator."""

    def __init__(self, parent: ttk.Frame, *args, **kwargs) -> None:
        """Create the action buttons from the current configurator."""
        super().__init__(parent, *args, **kwargs)
        self.columnconfigure(0, weight=1)

        button_options = {
            "sticky": tk.NE,
            "padx": get_theme_space_px(3),
            "pady": get_theme_padding_px((10, 1)),
        }
        self.microscopes_label = ttk.Label(
            self,
            text="Microscopes",
            font=("TkDefaultFont", 16, "bold"),
        )
        self.microscopes_label.grid(row=0, column=0, sticky=tk.W)

        self.new_button = ttk.Button(self, text="New Configuration", width=12)
        self.new_button.grid(row=0, column=1, **button_options)

        self.load_button = ttk.Button(self, text="Load Configuration", width=12)
        self.load_button.grid(row=0, column=2, **button_options)

        self.add_button = ttk.Button(self, text="Add A Microscope", width=12)
        self.add_button.grid(row=0, column=3, **button_options)

        self.save_button = ttk.Button(self, text="Save", width=12)
        self.save_button.grid(row=0, column=4, **button_options)

        self.cancel_button = ttk.Button(self, text="Cancel", width=12)
        self.cancel_button.grid(row=0, column=5, **button_options)
