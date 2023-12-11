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
from navigate.tools.file_functions import load_yaml_file
from navigate.tools.common_functions import combine_funcs, load_module_from_file
from navigate.model.features import feature_related_functions

class PluginsController:

    def __init__(self, view, parent_controller):
        self.view = view
        self.parent_controller = parent_controller
        self.plugins_path = os.path.join(Path(__file__).resolve().parent.parent.parent, "plugins")
        self.plugins_dict = {}

    def populate_experiment_setting(self):
        for plugin_name in self.plugins_dict:
            try:
                self.plugins_dict[plugin_name].populate_experiment_setting()
            except:
                pass

    def load_plugins(self):
        plugins = os.listdir(self.plugins_path)
        for f in plugins:
            if not os.path.isdir(os.path.join(self.plugins_path, f)):
                continue

            # read "plugin_config.yml"
            plugin_config = load_yaml_file(os.path.join(self.plugins_path, f, "plugin_config.yml"))
            if plugin_config is None:
                continue
            plugin_name = plugin_config.get("name", f)
            plugin_file_name = "_".join(plugin_name.lower().split())
            plugin_class_name = "".join(plugin_name.title().split())
            if "view" in plugin_config:
                # verify if "frame_name" and "file_name" are given and correct
                view_file = os.path.join(self.plugins_path, f, "view", f"{plugin_file_name}_frame.py")
                controller_file = os.path.join(self.plugins_path, f, "controller", f"{plugin_file_name}_controller.py")
                if os.path.exists(view_file) and os.path.isfile(view_file) and os.path.exists(controller_file) and os.path.isfile(controller_file):
                    plugin_frame_module = load_module_from_file(f"{plugin_class_name}Frame", view_file)
                    plugin_frame = getattr(plugin_frame_module, f"{plugin_class_name}Frame")
                    plugin_controller_module = load_module_from_file(f"{plugin_class_name}Controller", controller_file)
                    plugin_controller = getattr(plugin_controller_module, f"{plugin_class_name}Controller")

                    if plugin_config["view"] == "Popup":
                        # menu
                        self.parent_controller.view.menubar.menu_plugins.add_command(
                            label=plugin_name, command=self.build_popup_window(plugin_name, plugin_frame, plugin_controller)
                        )
                    else:
                        self.build_tab_window(plugin_name, plugin_frame, plugin_controller)
            # feature
            features_dir = os.path.join(self.plugins_path, f, "model", "features")
            if os.path.exists(features_dir):
                features = os.listdir(features_dir)
                for feature in features:
                    feature_file = os.path.join(features_dir, feature)
                    if os.path.isfile(feature_file):
                        temp = load_module_from_file(feature, feature_file)
                        for c in dir(temp):
                            if inspect.isclass(getattr(temp, c)):
                                setattr(feature_related_functions, c, getattr(temp, c))

    def build_tab_window(self, plugin_name, frame, controller):
        plugin_frame = frame(self.view.settings)
        self.view.settings.add(plugin_frame, text=plugin_name, sticky=tk.NSEW)
        plugin_controller = controller(plugin_frame, self.parent_controller)
        controller_name = "__plugin" + "_".join(plugin_name.lower().split()) + "_controller"
        self.plugins_dict[controller_name] = plugin_controller

    def build_popup_window(self, plugin_name, frame, controller):
        controller_name = "__plugin" + "_".join(plugin_name.lower().split()) + "_controller"

        def func(*args, **kwargs):
            if controller_name in self.plugins_dict:
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
            
            popup.protocol("WM_DELETE_WINDOW", combine_funcs(
                popup.dismiss,
                lambda: self.plugin_controller.pop(controller_name)
            ))

        return func