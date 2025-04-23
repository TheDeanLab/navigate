# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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
import tkinter as tk
from time import sleep
from tkinter import filedialog, messagebox
from typing import Optional, Any, Dict, List, IO

# Third Party Imports

# Local Imports
from navigate.view.configurator_application_window import ConfigurationAssistantWindow
from navigate.view.configurator_application_window import (
    MicroscopeTab,
    MicroscopeWindow,
)
from navigate.config.configuration_database import (
    hardwares_dict,
    hardwares_config_name_dict,
)
from navigate.tools.file_functions import load_yaml_file

# Logger Setup
import logging

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Configurator:
    """Navigate Configurator"""

    def __init__(self, root: tk.Tk, splash_screen: tk.Toplevel) -> None:
        """Initialize the Configurator application window.

        Parameters
        ----------
        root : tk.Tk
            The main Tkinter root window of the application.
        splash_screen : tk.Toplevel
            The splash screen to display before showing the main window.

        Returns
        -------
        None
        """
        self.root = root

        # Show the splash screen for 1 second and then destroy it.
        sleep(1)
        splash_screen.destroy()
        self.root.deiconify()
        self.view = ConfigurationAssistantWindow(root)
        self.view.microscope_window = MicroscopeWindow(
            self.view.microscope_frame, self.view.root
        )

        self.view.top_window.add_button.config(command=self.add_microscope)
        self.view.top_window.new_button.config(command=self.new_configuration)
        self.view.top_window.load_button.config(command=self.load_configuration)
        self.view.top_window.save_button.config(command=self.save)
        self.view.top_window.cancel_button.config(command=self.on_cancel)
        self.microscope_id = 0
        self.create_config_window(0)
    
    def _set_nested_value(self, base: Dict[str, Any], keys: List[str], value: Any) -> None:
        """
        Set a value in a nested dictionary given a list of keys.

        Parameters
        ----------
        base : Dict[str, Any]
            The dictionary in which to set the nested value.
        keys : List[str]
            Sequence of keys defining the nested path.
        value : Any
            The value to assign at the final nested key.
        """
        # Traverse or create nested dictionaries up to the last key
        for key in keys[:-1]:
            base = base.setdefault(key, {})  # type: ignore
        # Assign the value at the final key
        base[keys[-1]] = value
    
    def _get_widget_value(self, path: str, data: Dict[str, Any]) -> Optional[Any]:
        """
        Retrieve a nested value from a dictionary given a slash-separated key path.

        Parameters
        ----------
        path : str
            Slash-separated keys specifying the nested path.
        data : Dict[str, Any]
            The dictionary to search.

        Returns
        -------
        Optional[Any]
            The value found at the end of the path, or None if any key is missing.
        """
        current = data
        for key in path.split("/"):
            if not key.strip():
                return current
            if not isinstance(current, dict):
                return None
            current = current.get(key)
            if current is None:
                return None
        return current

    def _extract_widgets_values(self, widgets: Dict[str, Any], value_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract flat widget key/value pairs from a nested value dictionary.

        Parameters
        ----------
        widgets : Dict[str, Any]
            Widget definition mapping keys to metadata (including type and mapping).
        value_dict : Dict[str, Any]
            The nested configuration values for these widgets.

        Returns
        -------
        Dict[str, Any]
            Mapping of widget keys to their corresponding values.
        """
        result: Dict[str, Any] = {}
        for key, meta in widgets.items():
            if key == "frame_config":
                continue
            widget_type = meta[1]
            if widget_type in ("Button", "Label"):
                continue
            raw_value = self._get_widget_value(key, value_dict)
            mapping = meta[3]
            if widget_type != "Spinbox" and mapping:
                # Create reverse lookup for valid mapping
                if isinstance(mapping, list):
                    rev_map = {v: v for v in mapping}
                else:
                    rev_map = {v: k for k, v in mapping.items()}
                # Default to last valid if missing
                mapped = rev_map.get(raw_value, list(rev_map.values())[-1])
                result[key] = mapped
            else:
                result[key] = raw_value
        return result

    def _build_widgets_values(
        self,
        widgets: Optional[Dict[str, Any]],
        data: Optional[Dict[str, Any]],
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Build a list of widget-value dictionaries based on formatting rules.

        Parameters
        ----------
        widgets : Optional[Dict[str, Any]]
            Widget definitions including format and reference metadata.
        data : Optional[Dict[str, Any]]
            The nested values to populate the widgets.

        Returns
        -------
        List[Optional[Dict[str, Any]]]
            A list of mappings for each widget instance, or [None] if unavailable.
        """
        if widgets is None or data is None:
            return [None]
        values: List[Optional[Dict[str, Any]]] = []
        ref = widgets.get("frame_config", {}).get("ref", "")
        fmt = widgets.get("frame_config", {}).get("format", "")
        if fmt.startswith("list"):
            raw = self._get_widget_value(ref, data) if ref and ref.lower() != "none" else data
            if not isinstance(raw, list):
                return [None]
            for item in raw:
                values.append(self._extract_widgets_values(widgets, item))
        elif fmt.startswith("item"):
            fmt_list = fmt.split(";")
            ref_list = ref.split(";")
            for fmt_item in fmt_list:
                k_idx = fmt_item[fmt_item.index("(") + 1 : fmt_item.index(",")].strip()
                v_idx = fmt_item[fmt_item.index(",") + 1 : fmt_item.index(")")].strip()
                temp = self._get_widget_value(ref_list[fmt_list.index(fmt_item)], data)
                if isinstance(temp, dict):
                    for j, k in enumerate(temp.keys()):
                        if len(values) <= j:
                            values.append({k_idx: k, v_idx: temp[k]})
                        else:
                            values[j][k_idx] = k  # type: ignore
                            values[j][v_idx] = temp[k]  # type: ignore
        else:
            raw = self._get_widget_value(ref, data) if ref and ref.lower() != "none" else data
            values.append(self._extract_widgets_values(widgets, raw or {}))
        return values

    def on_cancel(self) -> None:
        """Close the configurator window and exit the application.

        Returns
        -------
        None
        """
        self.root.destroy()
        exit()

    def add_microscope(self) -> None:
        """Add a new microscope tab to the configurator.

        Returns
        -------
        None
        """
        # Increment microscope ID and create a new configuration tab
        self.microscope_id += 1
        self.create_config_window(self.microscope_id)

    def delete_microscopes(self) -> None:
        """Delete all microscope tabs and reset the microscope counter.

        Returns
        -------
        None
        """
        # Remove all microscope tabs from the notebook
        for tab_id in self.view.microscope_window.tabs():
            self.view.microscope_window.forget(tab_id)
        # Clear internal tracking of tabs and reset ID counter
        self.view.microscope_window.tab_list = []
        self.microscope_id = 0

    def new_configuration(self) -> None:
        """Reset to a new, empty microscope configuration.

        Deletes existing microscopes and initializes a fresh configuration tab.

        Returns
        -------
        None
        """
        # Remove all existing tabs and create an initial microscope tab
        self.delete_microscopes()
        self.create_config_window(self.microscope_id)

    def save(self) -> None:
        """Save the current configuration to a YAML file.

        Opens a file dialog to select the save path, collects values from all
        microscope and hardware tabs, constructs a nested dictionary, and
        writes it out in YAML format.

        Returns
        -------
        None
        """


        # Prompt user for filename to save configuration
        filename = filedialog.asksaveasfilename(
            defaultextension=".yaml", filetypes=[("Yaml file", "*.yml *.yaml")]
        )
        if not filename:
            return
        # warning_info
        warning_info = {}
        config_dict: Dict[str, Any] = {}
        # Iterate over each microscope tab and collect hardware settings
        for tab_index in self.view.microscope_window.tabs():
            microscope_name = self.view.microscope_window.tab(tab_index, "text")
            microscope_tab = self.view.microscope_window.nametowidget(tab_index)
            microscope_dict = {}
            config_dict[microscope_name] = microscope_dict
            for hardware_tab_index in microscope_tab.tabs():
                hardware_name = microscope_tab.tab(hardware_tab_index, "text")
                hardware_tab = microscope_tab.nametowidget(hardware_tab_index)
                hardware_dict = {}
                microscope_dict[
                    hardwares_config_name_dict.get(hardware_name, hardware_name)
                ] = hardware_dict
                for variable_list in hardware_tab.variables_list:
                    if variable_list is None:
                        continue
                    variables, value_dict, ref, format = variable_list
                    if format is None:
                        format = ""
                    temp_dict = hardware_dict
                    if ref is not None:
                        if format.startswith("list"):
                            hardware_dict[ref] = hardware_dict.get(ref, [])
                            temp_dict = {}
                            hardware_dict[ref].append(temp_dict)
                        elif format.startswith("item"):
                            format_list = format.split(";")
                            ref_list = ref.split(";")
                            for i, format in enumerate(format_list):
                                ref = ref_list[i]
                                hardware_dict[ref] = hardware_dict.get(ref, {})
                                temp_dict = hardware_dict[ref]
                                k_idx = format[
                                    format.index("(") + 1 : format.index(",")
                                ].strip()
                                v_idx = format[
                                    format.index(",") + 1 : format.index(")")
                                ].strip()
                                k = variables[k_idx].get()
                                if k.strip() == "":
                                    warning_info[hardware_name] = True
                                    print(
                                        f"Notice: {hardware_name} has an empty value "
                                        f"{ref}! Please double check if it's okay!"
                                    )

                                if k_idx in value_dict:
                                    k = value_dict[k_idx][v]  # noqa
                                v = variables[v_idx].get()
                                if v_idx in value_dict:
                                    v = value_dict[v_idx][v]
                                temp_dict[k] = v
                            continue
                        else:
                            temp_dict = {}
                            hardware_dict[ref] = hardware_dict.get("ref", temp_dict)
                    for k, var in variables.items():
                        try:
                            if k in value_dict:
                                v = value_dict[k][var.get()]
                                # add more information such as file name of a device type
                                if type(v) is tuple:
                                    v = v[0]
                            else:
                                v = var.get()
                        except tk._tkinter.TclError:
                            v = ""
                            print(
                                f"Notice: {hardware_name} has an empty value {k}! "
                                f"Please double check!"
                            )
                            warning_info[hardware_name] = True
                        # Assign nested configuration entries
                        self._set_nested_value(temp_dict, k.split("/"), v)

        self.write_to_yaml(config_dict, filename)
        # display warning
        if warning_info:
            messagebox.showwarning(
                title="Configuration",
                message=f"There are empty value(s) with "
                f"{', '.join(warning_info.keys())}"
                f". Please double check!",
            )

    def write_to_yaml(self, config: Dict[str, Any], filename: str) -> None:
        """Write configuration dictionary to a YAML file.

        Parameters
        ----------
        config : Dict[str, Any]
            Nested dictionary representing the microscope configurations.
        filename : str
            Path to the YAML file to write.

        Returns
        -------
        None
        """

        def write_func(prefix: str, config_dict: Dict[str, Any], f: IO[str]) -> None:
            """Recursively write nested configuration dictionaries and lists to the YAML file.

            Parameters
            ----------
            prefix : str
                Current indentation prefix.
            config_dict : Dict[str, Any]
                Partial configuration dictionary to write.
            f : IO[str]
                File-like object to write YAML content.
            """
            # Iterate over keys in the current configuration dictionary
            for k in config_dict:
                if isinstance(config_dict[k], dict):
                    # Nested dictionary: write key and recurse
                    f.write(f"{prefix}{k}:\n")
                    write_func(prefix + " " * 2, config_dict[k], f)
                elif type(config_dict[k]) == list:
                    # List of items: write each item under a dash
                    list_prefix = " "
                    if k != "None":
                        f.write(f"{prefix}{k}:\n")
                        list_prefix = " " * 2
                    for list_item in config_dict[k]:
                        f.write(f"{prefix}{list_prefix}-\n")
                        write_func(prefix + list_prefix * 2, list_item, f)
                elif k != "":
                    # Scalar value: write key and its value
                    f.write(f"{prefix}{k}: {config_dict[k]}\n")

        with open(filename, "w") as f:
            f.write("microscopes:\n")
            write_func("  ", config, f)

    def create_config_window(self, id: int) -> None:
        """Create configuration window tabs for a microscope.

        Parameters
        ----------
        id : int
            Identifier for the new microscope tab.

        Returns
        -------
        None
        """
        # Construct tab name and instantiate a new MicroscopeTab

        tab_name = "Microscope-" + str(id)
        microscope_tab = MicroscopeTab(
            self.view.microscope_window,
            root=self.view.root,
        )
        self.view.microscope_window.tab_list.append(tab_name)
        for hardware_type, widgets in hardwares_dict.items():
            if not widgets:
                continue
            if type(widgets) == dict:
                microscope_tab.create_hardware_tab(hardware_type, widgets)
            else:
                microscope_tab.create_hardware_tab(
                    hardware_type,
                    hardware_widgets=widgets[1],
                    widgets=widgets[2],
                    top_widgets=widgets[0],
                )

        # Adding tabs to self notebook
        self.view.microscope_window.add(
            microscope_tab,
            text=tab_name,
            sticky=tk.NSEW,
        )

    def load_configuration(self) -> None:
        """Load configuration from a YAML file and populate GUI tabs.

        Returns
        -------
        None
        """


        # Prompt user to select a configuration YAML file
        file_name = filedialog.askopenfilename(
            defaultextension=".yml", filetypes=[("Yaml file", "*.yml *.yaml")]
        )
        if not file_name:
            return

        # read configuration.yaml
        config_dict = load_yaml_file(file_name)
        if config_dict is None or "microscopes" not in config_dict:
            messagebox.showerror(
                title="Configuration",
                message="It's not a valid configuration.yaml file!",
            )
            return

        self.delete_microscopes()

        for i, microscope_name in enumerate(config_dict["microscopes"].keys()):
            microscope_tab = MicroscopeTab(
                self.view.microscope_window,
                root=self.view.root,
            )
            self.view.microscope_window.add(
                microscope_tab,
                text=microscope_name,
                sticky=tk.NSEW,
            )
            self.view.microscope_window.tab_list.append(microscope_name)

            for hardware_type, widgets in hardwares_dict.items():
                hardware_ref_name = hardwares_config_name_dict[hardware_type]
                # build dictionary values for widgets
                if isinstance(widgets, dict):
                    try:
                        widgets_value = self._build_widgets_values(
                            widgets,
                            config_dict["microscopes"][microscope_name][hardware_ref_name],
                        )
                    except Exception:
                        widgets_value = [None]
                    microscope_tab.create_hardware_tab(
                        hardware_type,
                        widgets,
                        hardware_widgets_value=widgets_value,
                    )
                else:
                    try:
                        widgets_value = [
                            self._build_widgets_values(
                                widgets[1],
                                config_dict["microscopes"][microscope_name][hardware_ref_name],
                            ),
                            self._build_widgets_values(
                                widgets[2],
                                config_dict["microscopes"][microscope_name][hardware_ref_name],
                            ),
                        ]
                    except Exception:
                        widgets_value = [[None], [None]]
                    microscope_tab.create_hardware_tab(
                        hardware_type,
                        hardware_widgets=widgets[1],
                        widgets=widgets[2],
                        top_widgets=widgets[0],
                        hardware_widgets_value=widgets_value[0],
                        constants_widgets_value=widgets_value[1],
                    )
