# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
from tkinter import filedialog

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

# Logger Setup
import logging

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Configurator:
    """Navigate Configurator"""

    def __init__(self, root, splash_screen):
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
        self.view.top_window.save_button.config(command=self.save)
        self.view.top_window.cancel_button.config(command=self.on_cancel)
        self.create_config_window(0)
        self.microscope_id = 1

        print(
            "WARNING: The Configuration Assistant is not fully implemented. "
            "Users are still required to manually configure their system."
        )

    def on_cancel(self):
        """Closes the window and exits the program"""
        self.root.destroy()
        exit()

    def add_microscope(self):
        """Evaluate the number of configurations and create the configuration window"""
        self.create_config_window(self.microscope_id)
        self.microscope_id += 1

    def save(self):
        def set_value(temp_dict, key_list, value):
            if type(key_list) is list:
                for i in range(len(key_list)-1):
                    k = key_list[i]
                    temp_dict[k] = temp_dict.get(k, {})
                    temp_dict = temp_dict[k]
            temp_dict[key_list[-1]] = value

        filename = filedialog.asksaveasfilename(
            defaultextension=".yml", filetypes=[("Yaml file", "*.yml *.yaml")]
        )
        if not filename:
            return
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
                microscope_dict[hardwares_config_name_dict.get(hardware_name, hardware_name)] = hardware_dict
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
                                k_idx = format[format.index("(")+1: format.index(",")].strip()
                                v_idx = format[format.index(",")+1:format.index(")")].strip()
                                k = variables[k_idx].get()
                                if k_idx in value_dict:
                                    k = value_dict[k_idx][v]   
                                v = variables[v_idx].get()
                                if v_idx in value_dict:
                                    v = value_dict[v_idx][v]
                                temp_dict[k] = v
                            continue
                        else:
                            temp_dict = {}
                            hardware_dict[ref] = hardware_dict.get("ref", temp_dict)
                    for k, var in variables.items():
                        if k in value_dict:
                            v = value_dict[k][var.get()]
                        else:
                            v = var.get()
                        set_value(temp_dict, k.split("/"), v)

        self.write_to_yaml(config_dict, filename)

    def write_to_yaml(self, config, filename):

        def write_func(prefix, config_dict, f):
            for k in config_dict:
                if type(config_dict[k]) == dict:
                    f.write(f"{prefix}{k}:\n")
                    write_func(prefix+" "*2, config_dict[k], f)
                elif type(config_dict[k]) == list:
                    list_prefix = " "
                    if k != "None":
                        f.write(f"{prefix}{k}:\n")
                        list_prefix = " " * 2
                    for list_item in config_dict[k]:
                        f.write(f"{prefix}{list_prefix}-\n")
                        write_func(prefix+list_prefix*2, list_item, f)
                else:
                    f.write(f"{prefix}{k}: {config_dict[k]}\n")
    
        with open(filename, "w") as f:
            f.write("microscopes:\n")
            write_func("  ", config, f)


    def create_config_window(self, id):
        """Creates the configuration window tabs."""

        tab_name = "Microscope-" + str(id)
        microscope_tab = MicroscopeTab(
                            self.view.microscope_window,
                            name=tab_name,
                            index=id,
                            root=self.view.root,
                        )
        setattr(
            self.view.microscope_window,
            f"microscope_tab_{id}",
            microscope_tab,
        )
        self.view.microscope_window.tab_list.append(tab_name)
        for hardware_type, widgets in hardwares_dict.items():
            if not widgets:
                continue
            if type(widgets) == dict:
                microscope_tab.create_hardware_tab(hardware_type, widgets)
            else:
                microscope_tab.create_hardware_tab(hardware_type, hardware_widgets=widgets[1], widgets=widgets[2], top_widgets=widgets[0])

        # Adding tabs to self notebook
        self.view.microscope_window.add(
            getattr(self.view.microscope_window, f"microscope_tab_{id}"),
            text=tab_name,
            sticky=tk.NSEW,
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
