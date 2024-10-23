# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
from typing import Optional

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

    def __init__(self, root: tk.Tk, splash_screen):
        """Initiates the configurator application window.

        Parameters
        ----------
        root : tk.Tk
            The main window of the application
        splash_screen : SplashScreen
            The splash screen of the application
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

    def on_cancel(self) -> None:
        """Closes the window and exits the program"""
        self.root.destroy()
        exit()

    def add_microscope(self) -> None:
        """Add a new microscope tab"""
        self.microscope_id += 1
        self.create_config_window(self.microscope_id)

    def delete_microscopes(self) -> None:
        """Delete all microscopes"""
        # delete microscopes
        for tab_id in self.view.microscope_window.tabs():
            self.view.microscope_window.forget(tab_id)
        self.view.microscope_window.tab_list = []
        self.microscope_id = 0

    def new_configuration(self) -> None:
        """Create new configurations"""
        self.delete_microscopes()
        self.create_config_window(self.microscope_id)

    def save(self) -> None:
        """Save configuration file"""

        def set_value(temp_dict, key_list, value):
            """Set value

            Parameters
            ----------
            temp_dict: dict
                Target dictionary
            key_list: list
                keyword list
            value: any
                value of the item
            """
            if type(key_list) is list:
                for i in range(len(key_list) - 1):
                    k = key_list[i]
                    temp_dict[k] = temp_dict.get(k, {})
                    temp_dict = temp_dict[k]
            temp_dict[key_list[-1]] = value

        filename = filedialog.asksaveasfilename(
            defaultextension=".yml", filetypes=[("Yaml file", "*.yml *.yaml")]
        )
        if not filename:
            return
        # warning_info
        warning_info = {}
        config_dict = {}
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
                            else:
                                v = var.get()
                        except tk._tkinter.TclError:
                            v = ""
                            print(
                                f"Notice: {hardware_name} has an empty value {k}! "
                                f"Please double check!"
                            )
                            warning_info[hardware_name] = True
                        set_value(temp_dict, k.split("/"), v)

        self.write_to_yaml(config_dict, filename)
        # display warning
        if warning_info:
            messagebox.showwarning(
                title="Configuration",
                message=f"There are empty value(s) with "
                f"{', '.join(warning_info.keys())}"
                f". Please double check!",
            )

    def write_to_yaml(self, config: dict, filename: str) -> None:
        """write yaml file

        Parameters
        ----------
        config: dict
            configuration dictionary
        filename: str
            yaml file name
        """

        def write_func(prefix, config_dict, f):
            for k in config_dict:
                if type(config_dict[k]) == dict:
                    f.write(f"{prefix}{k}:\n")
                    write_func(prefix + " " * 2, config_dict[k], f)
                elif type(config_dict[k]) == list:
                    list_prefix = " "
                    if k != "None":
                        f.write(f"{prefix}{k}:\n")
                        list_prefix = " " * 2
                    for list_item in config_dict[k]:
                        f.write(f"{prefix}{list_prefix}-\n")
                        write_func(prefix + list_prefix * 2, list_item, f)
                else:
                    f.write(f"{prefix}{k}: {config_dict[k]}\n")

        with open(filename, "w") as f:
            f.write("microscopes:\n")
            write_func("  ", config, f)

    def create_config_window(self, id: int) -> None:
        """Creates the configuration window tabs.

        Parameters
        ----------
        id : int
            The id of the microscope
        """

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
        """Load configuration"""

        def get_widget_value(name, value_dict) -> Optional[str]:
            """Get the value from a dict

            Parameters
            ----------
            name: str
                key name
            value_dict: dict
                value dictionary

            Returns
            -------
            value : Optional[str]

                - The value of the key if it exists
                - None if the key does not exist
            """
            value = value_dict
            for key in name.split("/"):
                if key.strip() == "":
                    return value
                value = value.get(key, None)
                if value is None:
                    return None
            return value

        def get_widgets_value(widgets, value_dict):
            """Get all key-value from value_dict, keys are from widgets"""
            temp = {}
            for key in widgets:
                if key == "frame_config":
                    continue
                if widgets[key][1] in ["Button", "Label"]:
                    continue
                value = get_widget_value(key, value_dict)
                # widgets[key][3] is the value mapping dict
                if widgets[key][1] != "Spinbox" and widgets[key][3]:
                    # if the value is not valid, return the last valid value
                    if type(widgets[key][3]) == list:
                        reverse_value_dict = dict(
                            map(lambda v: (v, v), widgets[key][3])
                        )
                    else:
                        reverse_value_dict = dict(
                            map(lambda v: (v[1], v[0]), widgets[key][3].items())
                        )
                    temp[key] = reverse_value_dict.get(
                        value, list(reverse_value_dict.values())[-1]
                    )
                else:
                    temp[key] = value
            return temp

        def build_widgets_value(widgets, value_dict):
            """According to value_dict build values for widgets"""
            if widgets is None or value_dict is None:
                return [None]
            result = []
            ref = ""
            format = ""
            if "frame_config" in widgets:
                ref = widgets["frame_config"].get("ref", "")
                format = widgets["frame_config"].get("format", "")
            if format.startswith("list"):
                if ref != "" and ref.lower() != "none":
                    value_dict = get_widget_value(ref, value_dict)
                if type(value_dict) is not list:
                    return [None]
                for i in range(len(value_dict)):
                    result.append(get_widgets_value(widgets, value_dict[i]))
            elif format.startswith("item"):
                format_list = format.split(";")
                ref_list = ref.split(";")
                for i, format_item in enumerate(format_list):
                    k_idx = format_item[
                        format_item.index("(") + 1 : format_item.index(",")
                    ].strip()
                    v_idx = format_item[
                        format_item.index(",") + 1 : format_item.index(")")
                    ].strip()
                    temp_widget_values = get_widget_value(ref_list[i], value_dict)
                    for j, k in enumerate(temp_widget_values.keys()):
                        if len(result) < j + 1:
                            result.append({k_idx: k, v_idx: temp_widget_values[k]})
                        else:
                            result[j][k_idx] = k
                            result[j][v_idx] = temp_widget_values[k]
            else:
                if ref != "" and ref.lower() != "none":
                    value_dict = get_widget_value(ref, value_dict)
                result.append(get_widgets_value(widgets, value_dict))

            return result

        # ask file name
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
                if type(widgets) == dict:
                    try:
                        widgets_value = build_widgets_value(
                            widgets,
                            config_dict["microscopes"][microscope_name][
                                hardware_ref_name
                            ],
                        )
                    except Exception:
                        widgets_value = [None]
                    microscope_tab.create_hardware_tab(
                        hardware_type, widgets, hardware_widgets_value=widgets_value
                    )
                else:
                    try:
                        widgets_value = [
                            build_widgets_value(
                                widgets[1],
                                config_dict["microscopes"][microscope_name][
                                    hardware_ref_name
                                ],
                            ),
                            build_widgets_value(
                                widgets[2],
                                config_dict["microscopes"][microscope_name][
                                    hardware_ref_name
                                ],
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

    def device_selected(self, event):
        """Handle the event when a device is selected from the dropdown."""
        # # Get the selected device name
        # selected_device_name = self.view.microscope_frame.get()
        # # Find the key in the dictionary that corresponds to the selected value
        # selected_key = next(
        #     key for key, value in device_types.items()
        #     if value == selected_device_name)
        # print(f"Selected Device Key: {selected_key}")
        # print(f"Selected Device Name: {selected_device_name}")
        pass
