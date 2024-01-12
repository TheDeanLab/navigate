# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
#

from pathlib import Path
import os
import inspect
import tkinter as tk

from navigate.config.config import get_navigate_path
from navigate.view.custom_widgets.popup import PopUp
from navigate.tools.file_functions import load_yaml_file, save_yaml_file
from navigate.tools.common_functions import combine_funcs, load_module_from_file
from navigate.tools.decorators import AcquisitionMode
from navigate.model.features import feature_related_functions
from navigate.controller.sub_controllers.gui_controller import GUIController
from navigate.view.popups.plugins_popup import PluginsPopup


class PluginsController:
    """Plugins manaager in the controller side"""

    def __init__(self, view, parent_controller):
        """Initialize plugins manager class"""
        #: object: tkinter frame object.
        self.view = view
        #: object: navigate controller.
        self.parent_controller = parent_controller
        #: str: plugins default path.
        self.plugins_path = os.path.join(
            Path(__file__).resolve().parent.parent.parent, "plugins"
        )
        #: dict: installed plugins with GUI
        self.plugins_dict = {}

    def populate_experiment_setting(self):
        """populate experiment values to plugin GUI"""
        for plugin_name in self.plugins_dict:
            try:
                self.plugins_dict[plugin_name].populate_experiment_setting()
            except:
                pass

    def load_plugins(self):
        """Load plugins"""
        plugins = os.listdir(self.plugins_path)
        installed_plugins = dict(
            [(f, os.path.join(self.plugins_path, f)) for f in plugins]
        )
        # load plugins from plugins_config
        plugins_config_path = os.path.join(
            get_navigate_path(), "config", "plugins_config.yml"
        )
        if not os.path.exists(plugins_config_path):
            save_yaml_file(get_navigate_path(), {}, "plugins_config.yml")
        else:
            plugins_config = load_yaml_file(plugins_config_path)
            for plugin_name, plugin_path in plugins_config.items():
                if plugin_path and os.path.exists(plugin_path):
                    installed_plugins[plugin_name] = plugin_path
        for _, plugin_path in installed_plugins.items():
            if not os.path.isdir(plugin_path):
                continue

            # read "plugin_config.yml"
            plugin_config = load_yaml_file(
                os.path.join(plugin_path, "plugin_config.yml")
            )
            if plugin_config is None:
                continue
            plugin_name = plugin_config.get("name", _)
            plugin_file_name = "_".join(plugin_name.lower().split())
            plugin_class_name = "".join(plugin_name.title().split())
            if "view" in plugin_config:
                # verify if "frame_name" and "file_name" are given and correct
                view_file = os.path.join(
                    plugin_path, "view", f"{plugin_file_name}_frame.py"
                )
                controller_file = os.path.join(
                    plugin_path,
                    "controller",
                    f"{plugin_file_name}_controller.py",
                )
                if (
                    os.path.exists(view_file)
                    and os.path.isfile(view_file)
                    and os.path.exists(controller_file)
                    and os.path.isfile(controller_file)
                ):
                    plugin_frame_module = load_module_from_file(
                        f"{plugin_class_name}Frame", view_file
                    )
                    plugin_frame = getattr(
                        plugin_frame_module, f"{plugin_class_name}Frame"
                    )
                    plugin_controller_module = load_module_from_file(
                        f"{plugin_class_name}Controller", controller_file
                    )
                    plugin_controller = getattr(
                        plugin_controller_module, f"{plugin_class_name}Controller"
                    )

                    if plugin_config["view"] == "Popup":
                        # menu
                        self.parent_controller.view.menubar.menu_plugins.add_command(
                            label=plugin_name,
                            command=self.build_popup_window(
                                plugin_name, plugin_frame, plugin_controller
                            ),
                        )
                    else:
                        self.build_tab_window(
                            plugin_name, plugin_frame, plugin_controller
                        )
            # feature
            features_dir = os.path.join(plugin_path, "model", "features")
            if os.path.exists(features_dir):
                features = os.listdir(features_dir)
                for feature in features:
                    feature_file = os.path.join(features_dir, feature)
                    if os.path.isfile(feature_file):
                        module = load_module_from_file(feature, feature_file)
                        for c in dir(module):
                            if inspect.isclass(getattr(module, c)):
                                setattr(
                                    feature_related_functions, c, getattr(module, c)
                                )

            # acquisition mode
            acquisition_modes = plugin_config.get("acquisition_modes", [])
            for acquisition_mode_config in acquisition_modes:
                acquisition_file = os.path.join(
                    plugin_path, acquisition_mode_config["file_name"]
                )
                if os.path.exists(acquisition_file):
                    module = load_module_from_file(
                        acquisition_mode_config["file_name"][:-3], acquisition_file
                    )
                    acquisition_mode = [
                        m
                        for m in dir(module)
                        if isinstance(getattr(module, m), AcquisitionMode)
                    ]
                    if acquisition_mode:
                        self.parent_controller.add_acquisition_mode(
                            acquisition_mode_config["name"],
                            getattr(module, acquisition_mode[0]),
                        )

    def build_tab_window(self, plugin_name, frame, controller):
        """Build tab for a plugin

        Parameters
        ----------
        plugin_name : str
            plugin name.
        frame: object
            navigate frame object
        controller: object
            navigate controller
        """
        plugin_frame = frame(self.view.settings)
        self.view.settings.add(plugin_frame, text=plugin_name, sticky=tk.NSEW)
        plugin_controller = controller(plugin_frame, self.parent_controller)
        controller_name = (
            "__plugin" + "_".join(plugin_name.lower().split()) + "_controller"
        )
        self.plugins_dict[controller_name] = plugin_controller

    def build_popup_window(self, plugin_name, frame, controller):
        """Build popup window for plugins

        Parameters
        ----------
        plugin_name : str
            plugin name.
        frame: object
            navigate frame object
        controller: object
            navigate controller
        """
        controller_name = (
            "__plugin" + "_".join(plugin_name.lower().split()) + "_controller"
        )

        def func(*args, **kwargs):
            if controller_name in self.plugins_dict:
                self.plugins_dict[controller_name].popup.deiconify()
                return
            popup = PopUp(self.view, plugin_name, "+320+180", transient=False)
            popup.configure(bg="white")
            content_frame = popup.get_frame()
            plugin_frame = frame(content_frame)
            plugin_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=10, pady=10)

            plugin_controller = controller(plugin_frame, self.parent_controller)

            plugin_controller.popup = popup
            popup.deiconify()
            self.plugins_dict[controller_name] = plugin_controller

            popup.protocol(
                "WM_DELETE_WINDOW",
                combine_funcs(
                    popup.dismiss, lambda: self.plugins_dict.pop(controller_name)
                ),
            )

        return func


class UninstallPluginController(GUIController):
    def __init__(self, view, parent_controller):
        super().__init__(view, parent_controller)

        self.plugin_config_path = os.path.join(get_navigate_path(), "config")

        self.popup = PluginsPopup(view)
        self.popup.uninstall_btn.config(command=self.uninstall_plugins)
        self.popup.popup.protocol("WM_DELETE_WINDOW", self.exit_func)
        self.refresh_plugins()

    def showup(self):
        """Show up the popup window"""
        self.refresh_plugins()
        self.popup.popup.showup()

    def exit_func(self):
        """Exit"""
        self.popup.popup.dismiss()
        delattr(self.parent_controller, "uninstall_plugin_controller")

    def refresh_plugins(self):
        """Show installed plugins"""
        self.plugin_config = load_yaml_file(
            os.path.join(self.plugin_config_path, "plugins_config.yml")
        )

        self.popup.build_widgets(self.plugin_config)

    def uninstall_plugins(self, *args):
        """Uninstall plugins"""
        flag = False
        for var in self.popup.variables:
            if var.get():
                self.plugin_config.pop(var.get())
                flag = True
        if flag:
            save_yaml_file(
                self.plugin_config_path, self.plugin_config, "plugins_config.yml"
            )
            tk.messagebox.showwarning(
                title="Navigate",
                message="Plugins are uninstalled! Please restart Navigate!",
            )
            self.showup()
