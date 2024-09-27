# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

# Standard library imports
from pathlib import Path
import os
import tkinter as tk
from tkinter import messagebox

# Third-party imports

# Local application imports
from navigate.config.config import get_navigate_path
from navigate.view.custom_widgets.popup import PopUp
from navigate.tools.file_functions import load_yaml_file, save_yaml_file
from navigate.tools.common_functions import combine_funcs
from navigate.tools.decorators import AcquisitionMode
from navigate.controller.sub_controllers.gui import GUIController
from navigate.view.popups.plugins_popup import PluginsPopup
from navigate.plugins.plugin_manager import PluginFileManager, PluginPackageManager


class PluginsController:
    """Plugins manager in the controller side"""

    def __init__(self, view, parent_controller):
        """Initialize plugins manager class.

        Parameters
        ----------
        view: object
            tkinter frame object.
        parent_controller: object
            navigate controller.
        """
        #: object: tkinter frame object.
        self.view = view

        #: object: navigate controller.
        self.parent_controller = parent_controller

        #: dict: installed plugins with GUI
        self.plugins_dict = {}

    def populate_experiment_setting(self):
        """populate experiment values to plugin GUI"""
        for plugin_name in self.plugins_dict:
            try:
                self.plugins_dict[plugin_name].populate_experiment_setting()
            except Exception:
                pass

    def load_plugins(self):
        """Load plugins"""
        # load through files
        plugins_path = os.path.join(
            Path(__file__).resolve().parent.parent.parent, "plugins"
        )
        plugins_config_path = os.path.join(
            get_navigate_path(), "config", "plugins_config.yml"
        )
        plugin_file_manager = PluginFileManager(plugins_path, plugins_config_path)
        self.load_plugins_through_manager(plugin_file_manager)
        self.load_plugins_through_manager(PluginPackageManager)

    def load_plugins_through_manager(self, plugin_manager):
        """Load plugins through plugin manager

        Parameters
        ----------
        plugin_manager : object
            PluginManager object
        """
        plugins = plugin_manager.get_plugins()

        for plugin_name, plugin_ref in plugins.items():

            # read "plugin_config.yml"
            plugin_config = plugin_manager.load_config(plugin_ref)
            if plugin_config is None:
                continue
            plugin_display_name = plugin_config.get("name", plugin_name)

            plugin_frame = plugin_manager.load_view(plugin_ref, plugin_display_name)
            plugin_controller = plugin_manager.load_controller(
                plugin_ref, plugin_display_name
            )

            if plugin_frame and plugin_controller:
                if plugin_config["view"] == "Popup":
                    # menu
                    self.parent_controller.view.menubar.menu_plugins.add_command(
                        label=plugin_name,
                        command=self.build_popup_window(
                            plugin_name, plugin_frame, plugin_controller
                        ),
                    )
                else:
                    self.build_tab_window(plugin_name, plugin_frame, plugin_controller)
            # feature
            plugin_manager.load_features(plugin_ref)

            # acquisition mode
            acquisition_modes = plugin_config.get("acquisition_modes", [])
            plugin_manager.load_acquisition_modes(
                plugin_ref,
                acquisition_modes,
                self.register_acquisition_mode,
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
            Controller Class
        """
        try:
            plugin_frame = frame(self.view.settings)
            self.view.settings.add(plugin_frame, text=plugin_name, sticky=tk.NSEW)
            plugin_controller = controller(plugin_frame, self.parent_controller)
            self.parent_controller.register_event_listeners(
                getattr(plugin_controller, "custom_events", {})
            )
            controller_name = (
                "__plugin" + "_".join(plugin_name.lower().split()) + "_controller"
            )
            self.plugins_dict[controller_name] = plugin_controller
        except Exception as e:
            messagebox.showwarning(
                title="Warning",
                message=(
                    f"Plugin {plugin_name} has something went wrong."
                    f"Error: {e}"
                    f"Please make sure the plugin works correctly or uninstall it!"
                ),
            )

    def build_popup_window(self, plugin_name, frame, controller):
        """Build popup window for a plugin

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
            """Function to build popup window for a plugin

            Parameters
            ----------
            args: list
                arguments.
            kwargs: dict
                keyword arguments.
            """
            if controller_name in self.plugins_dict:
                self.plugins_dict[controller_name].popup.deiconify()
                return
            popup = PopUp(self.view, plugin_name, "+320+180", transient=False)
            popup.configure(bg="white")
            content_frame = popup.get_frame()
            plugin_frame = frame(content_frame)
            plugin_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=10, pady=10)

            plugin_controller = controller(plugin_frame, self.parent_controller)
            self.parent_controller.register_event_listeners(
                getattr(plugin_controller, "custom_events", {})
            )

            plugin_controller.popup = popup
            popup.deiconify()
            self.plugins_dict[controller_name] = plugin_controller

            popup.protocol(
                "WM_DELETE_WINDOW",
                combine_funcs(
                    popup.dismiss, lambda: self.plugins_dict.pop(controller_name)
                ),
            )

        def func_with_wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception:
                messagebox.showwarning(
                    title="Warning",
                    message=(
                        f"Plugin {plugin_name} has something went wrong."
                        "Please make sure the plugin works correctly or uninstall it "
                        "from navigate!"
                    ),
                )

        return func_with_wrapper

    def register_acquisition_mode(self, acquisition_mode_name, module):
        """Register acquisition mode

        Parameters
        ----------
        acquisition_mode_name : str
            The name of an acquisition mode
        module : module
            acquisition mode module
        """
        if not module:
            return
        acquisition_mode = [
            m for m in dir(module) if isinstance(getattr(module, m), AcquisitionMode)
        ]
        if acquisition_mode:
            self.parent_controller.add_acquisition_mode(
                acquisition_mode_name,
                getattr(module, acquisition_mode[0]),
            )


class UninstallPluginController(GUIController):
    """Uninstall plugin controller"""

    def __init__(self, view, parent_controller):
        """Initialize uninstall plugin controller class.

        Parameters
        ----------
        view: object
            tkinter frame object.
        parent_controller: object
            navigate controller.
        """
        super().__init__(view, parent_controller)

        #: str: plugin config path.
        self.plugin_config_path = os.path.join(get_navigate_path(), "config")

        #: PluginsPopup: popup window object.
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

        if self.plugin_config is None:
            self.plugin_config = {}

        self.popup.build_widgets(self.plugin_config)

    def uninstall_plugins(self, *args):
        """Uninstall plugins.

        Parameters
        ----------
        args: list
            arguments.
        """
        feature_lists_path = get_navigate_path() + "/feature_lists"
        features = os.listdir(feature_lists_path)
        feature_config = {}
        for feature_name in features:
            if feature_name.endswith(".yml") and feature_name != "__sequence.yml":
                feature_content = load_yaml_file(
                    os.path.join(feature_lists_path, feature_name)
                )
                if feature_content and feature_content.get("filename", None):
                    feature_config[feature_name] = feature_content["filename"]
        flag = False
        for var in self.popup.variables:
            if var.get():
                # remove the feature list if a deleted plugin has any.
                for feature_name in feature_config:
                    if feature_config[feature_name].startswith(
                        self.plugin_config[var.get()]
                    ):
                        os.remove(f"{feature_lists_path}/{feature_name}")
                self.plugin_config.pop(var.get())
                flag = True
        if flag:
            save_yaml_file(
                self.plugin_config_path, self.plugin_config, "plugins_config.yml"
            )
            messagebox.showwarning(
                title="Navigate",
                message="Plugins are uninstalled! Please restart Navigate!",
            )
            self.showup()
