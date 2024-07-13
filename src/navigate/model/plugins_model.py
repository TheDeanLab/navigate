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

# Standard library imports
import os
from pathlib import Path

# Third-party imports

# Local application imports
from navigate.tools.common_functions import load_module_from_file
from navigate.tools.file_functions import load_yaml_file, save_yaml_file
from navigate.tools.decorators import FeatureList, AcquisitionMode
from navigate.config.config import get_navigate_path
from navigate.config import set_feature_attributes


class PluginsModel:
    """Plugins manager in the model side"""

    def __init__(self):
        """Initialize plugins manager class"""
        #: str: plugins default path.
        self.plugins_path = os.path.join(
            Path(__file__).resolve().parent.parent, "plugins"
        )

    def load_plugins(self):
        """Load plugins"""
        devices_dict = {}
        plugin_acquisition_modes = {}

        feature_lists_path = os.path.join(get_navigate_path(), "feature_lists")
        if not os.path.exists(feature_lists_path):
            os.makedirs(feature_lists_path)

        plugins_dict = self.load_plugins_from_plugins_folder()
        plugins_dict = self.load_plugins_from_plugin_config(plugins_dict)

        for _, plugin_path in plugins_dict.items():
            if not os.path.isdir(plugin_path):
                continue

            plugin_config = load_yaml_file(
                os.path.join(plugin_path, "plugin_config.yml")
            )
            if plugin_config is None:
                continue

            set_feature_attributes(plugin_path)

            self.load_plugin_features(feature_lists_path, plugin_path)

            plugin_acquisition_modes = self.load_plugin_acquisition_modes(
                plugin_acquisition_modes, plugin_config, plugin_path
            )

            devices_dict = self.load_plugin_devices(devices_dict, plugin_path)

        return devices_dict, plugin_acquisition_modes

    @staticmethod
    def load_plugin_devices(devices_dict, plugin_path):
        device_dir = os.path.join(plugin_path, "model", "devices")
        if os.path.exists(device_dir):
            devices = os.listdir(device_dir)
            for device in devices:
                device_path = os.path.join(device_dir, device)
                if not os.path.isdir(device_path):
                    continue
                try:
                    module = load_module_from_file(
                        "device_module",
                        os.path.join(device_path, "device_startup_functions.py"),
                    )
                except FileNotFoundError:
                    continue
                if module:
                    try:
                        device_type_name = module.DEVICE_TYPE_NAME
                    except AttributeError:
                        print(
                            f"Plugin device: {device} is not set correctly!"
                            "Please make sure the DEVICE_TYPE_NAME is given right!"
                        )
                        continue
                    # core devices
                    core_devices = [
                        "camera",
                        "remote_focus_device",
                        "galvo",
                        "filter_wheel",
                        "stage",
                        "zoom",
                        "shutter",
                        "lasers",
                    ]
                    if device_type_name in core_devices:
                        if device_type_name not in devices_dict:
                            devices_dict[device_type_name] = {}
                            devices_dict[device_type_name]["load_device"] = []
                            devices_dict[device_type_name]["start_device"] = []
                        devices_dict[device_type_name]["load_device"].append(
                            module.load_device
                        )
                        devices_dict[device_type_name]["start_device"].append(
                            module.start_device
                        )
                    elif device_type_name == "multiple_devices":
                        for device_name in core_devices:
                            if device_name not in devices_dict:
                                devices_dict[device_name] = {}
                                devices_dict[device_name]["load_device"] = []
                                devices_dict[device_name]["start_device"] = []
                            devices_dict[device_name]["load_device"].append(
                                module.load_device
                            )
                            devices_dict[device_name]["start_device"].append(
                                module.start_device
                            )
                    else:
                        devices_dict[device_type_name] = {}
                        devices_dict[device_type_name][
                            "ref_list"
                        ] = module.DEVICE_REF_LIST
                        devices_dict[device_type_name][
                            "load_device"
                        ] = module.load_device
                        devices_dict[device_type_name][
                            "start_device"
                        ] = module.start_device
        return devices_dict

    @staticmethod
    def load_plugin_acquisition_modes(
        plugin_acquisition_modes, plugin_config, plugin_path
    ):
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
                    plugin_acquisition_modes[acquisition_mode_config["name"]] = getattr(
                        module, acquisition_mode[0]
                    )(acquisition_mode_config["name"])
        return plugin_acquisition_modes

    @staticmethod
    def load_plugin_features(self, feature_lists_path, plugin_path):
        plugin_feature_list = os.path.join(plugin_path, "feature_list.py")
        if os.path.exists(plugin_feature_list):
            module = load_module_from_file("feature_list_temp", plugin_feature_list)
            features = [
                f for f in dir(module) if isinstance(getattr(module, f), FeatureList)
            ]
            for feature_name in features:
                feature = getattr(module, feature_name)
                feature_list_name = feature.feature_list_name
                feature_list_file_name = "_".join(feature_list_name.split())
                feature_list_content = {
                    "module_name": feature_name,
                    "feature_list_name": feature_list_name,
                    "filename": plugin_feature_list,
                }
                save_yaml_file(
                    feature_lists_path,
                    feature_list_content,
                    f"{feature_list_file_name}.yml",
                )

    @staticmethod
    def load_plugins_from_plugin_config(plugins_dict):
        # load plugins from plugins_config
        plugins_config_path = os.path.join(
            get_navigate_path(), "config", "plugins_config.yml"
        )
        plugins_config = load_yaml_file(plugins_config_path)
        if plugins_config is None:
            plugins_config = {}
            save_yaml_file(
                os.path.join(get_navigate_path(), "config"), {}, "plugins_config.yml"
            )
        else:
            verified_plugins_config = {}
            for plugin_name, plugin_path in plugins_config.items():
                if not plugin_path:
                    print(
                        f"Plugin '{plugin_name}' is not installed correctly. "
                        f"Please reinstall it if necessary."
                    )
                    continue
                if os.path.exists(plugin_path):
                    if plugin_name in plugins_dict:
                        print(
                            f"There are two plugins named '{plugin_name}'. Please "
                            f"rename Plugin '{plugin_name}' in plugins folder!"
                        )
                    plugins_dict[plugin_name] = plugin_path
                    verified_plugins_config[plugin_name] = plugin_path
                else:
                    print(
                        f"Couldn't load plugin '{plugin_name}' please make sure "
                        f"it exists!"
                    )
            save_yaml_file(
                os.path.join(get_navigate_path(), "config"),
                verified_plugins_config,
                "plugins_config.yml",
            )

        return plugins_dict

    def load_plugins_from_plugins_folder(self):
        # load plugins from plugins folder
        plugins = os.listdir(self.plugins_path)
        plugins_dict = {}
        for f in plugins:
            if not os.path.isdir(os.path.join(self.plugins_path, f)):
                continue
            # read "plugin_config.yml"
            plugin_config = load_yaml_file(
                os.path.join(self.plugins_path, f, "plugin_config.yml")
            )
            if plugin_config:
                plugins_dict[plugin_config.get("name", f)] = os.path.join(
                    self.plugins_path, f
                )

        return plugins_dict
