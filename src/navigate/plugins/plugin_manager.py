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
import importlib
from importlib.metadata import entry_points
import importlib.resources
import pkgutil
import os
import inspect

# Local application imports
from navigate.tools.file_functions import load_yaml_file
from navigate.tools.common_functions import load_module_from_file
from navigate.model.features import feature_related_functions


def register_features(module):
    """Register features

    Parameters
    ----------
    module : module
        A python module contains features
    """
    for c in dir(module):
        if inspect.isclass(getattr(module, c)):
            setattr(feature_related_functions, c, getattr(module, c))


class PluginPackageManager:
    """Plugin package manager"""

    @staticmethod
    def get_plugins():
        """Get plugins

        Returns
        -------
        plugins : dict
            plugins dict
        """
        plugins = {}
        for entry_point in entry_points().get("navigate.plugins", []):
            plugin_package_name = entry_point.module.split(".")[0]
            if plugin_package_name in plugins:
                print(
                    f"*** Warning: plugin {plugin_package_name} exists!"
                    "Can't load twice!"
                    "Please double-check the installed plugins!"
                )
                continue
            plugins[plugin_package_name] = plugin_package_name
        return plugins

    @staticmethod
    def load_config(package_name):
        """Load plugin_config.yml

        Parameters
        ----------
        package_name : str
            package name

        Returns
        -------
        plugin_config : dict
            plugin configuration
        """
        package_path = importlib.resources.files(package_name)
        plugin_config = load_yaml_file(os.path.join(package_path, "plugin_config.yml"))
        return plugin_config

    @staticmethod
    def load_controller(package_name, controller_name):
        """Load controller

        Parameters
        ----------
        package_name : str
            package name
        controller_name : str
            controller name

        Returns
        -------
        controller_class : class
            controller class
        """
        controller_file_name = "_".join(controller_name.lower().split()) + "_controller"
        controller_class_name = "".join(controller_name.title().split()) + "Controller"
        try:
            controller_module = importlib.import_module(
                f"{package_name}.controller.{controller_file_name}"
            )
            return getattr(controller_module, controller_class_name)
        except (ImportError, AttributeError):
            return None

    @staticmethod
    def load_view(package_name, frame_name):
        """Load view

        Parameters
        ----------
        package_name : str
            package name
        frame_name : str
            frame name

        Returns
        -------
        frame_class : class
            frame class
        """
        frame_file_name = "_".join(frame_name.lower().split()) + "_frame"
        frame_class_name = "".join(frame_name.title().split()) + "Frame"
        try:
            view_module = importlib.import_module(
                f"{package_name}.view.{frame_file_name}"
            )
            return getattr(view_module, frame_class_name)
        except (ImportError, AttributeError):
            return None

    @staticmethod
    def load_feature_lists(package_name, register_func):
        """Load feature lists

        Parameters
        ----------
        package_name : str
            package name
        register_func : func
            the function to handle feature lists
        """
        try:
            module = importlib.import_module(f"{package_name}.feature_list")
            register_func(
                importlib.resources.files(package_name).joinpath("feature_list.py"),
                module,
            )
        except (ImportError, AttributeError):
            pass

    @staticmethod
    def load_features(package_name):
        """Load features

        Parameters
        ----------
        package_name : str
            package name
        """
        for _, module_name, is_pkg in pkgutil.iter_modules(
            [importlib.resources.files(package_name).joinpath("model/features")]
        ):
            if not is_pkg:
                full_module_name = f"{package_name}.model.features.{module_name}"
                try:
                    module = importlib.import_module(full_module_name)
                except (ImportError, AttributeError):
                    continue
                register_features(module)

    @staticmethod
    def load_acquisition_modes(package_name, acquisition_modes, register_func):
        """Load acquisition modes

        Parameters
        ----------
        package_name : str
            package name
        acquisition_modes : []
            list of acquisition mode configurations
        register_func : func
            the function to register acquisition modes
        """
        for acquisition_mode_config in acquisition_modes:
            acquisition_file = acquisition_mode_config["file_name"][:-3]
            try:
                module = importlib.import_module(f"{package_name}.{acquisition_file}")
            except (ImportError, AttributeError):
                continue
            if module:
                register_func(acquisition_mode_config["name"], module)

    @staticmethod
    def load_devices(package_name, register_func):
        """Load devices

        Parameters
        ----------
        package_name : str
            package name
        register_func : func
            the function to register devices
        """
        for _, module_name, is_pkg in pkgutil.iter_modules(
            [importlib.resources.files(package_name).joinpath("model/devices")]
        ):
            if is_pkg:
                full_module_name = (
                    f"{package_name}.model."
                    f"devices.{module_name}.device_startup_functions"
                )
                try:
                    module = importlib.import_module(full_module_name)
                except (ImportError, AttributeError):
                    continue
                register_func(module_name, module)


class PluginFileManager:
    """Plugin file manager"""

    def __init__(self, plugins_path, plugins_config_path):
        """Initialize PluginFileManager

        Parameters
        ----------
        plugins_path : str
            plugins path
        plugins_config_path : str
            plugins config path
        """

        #: str: plugins path
        self.plugins_path = plugins_path

        #: str: plugins config path
        self.plugins_config_path = plugins_config_path

    def get_plugins(self):
        """Get plugins

        Returns
        -------
        plugins : dict
            plugins dict
        """
        plugins = {}

        folder_names = os.listdir(self.plugins_path)
        full_path_names = dict(
            [(f, os.path.join(self.plugins_path, f)) for f in folder_names]
        )
        # add plugins from plugins_config.yml
        plugins_config = load_yaml_file(self.plugins_config_path)
        if plugins_config:
            full_path_names.update(plugins_config)

        for plugin_name, plugin_path in full_path_names.items():
            if (
                plugin_path
                and os.path.exists(plugin_path)
                and os.path.isdir(plugin_path)
            ):
                plugins[plugin_name] = plugin_path

        return plugins

    @staticmethod
    def load_config(plugin_path):
        """Load plugin_config.yml

        Parameters
        ----------
        plugin_path : str
            plugin path

        Returns
        -------
        plugin_config : dict
            plugin configuration
        """
        plugin_config = load_yaml_file(os.path.join(plugin_path, "plugin_config.yml"))
        return plugin_config

    @staticmethod
    def load_controller(plugin_path, controller_name):
        """Load controller

        Parameters
        ----------
        plugin_path : str
            plugin path
        controller_name : str
            controller name

        Returns
        -------
        controller_class : class
            controller class
        """
        controller_file_name = (
            "_".join(controller_name.lower().split()) + "_controller.py"
        )
        controller_class_name = "".join(controller_name.title().split()) + "Controller"
        controller_file_path = os.path.join(
            plugin_path, "controller", controller_file_name
        )
        if os.path.exists(controller_file_path) and os.path.isfile(
            controller_file_path
        ):
            module = load_module_from_file(controller_class_name, controller_file_path)
            return getattr(module, controller_class_name)
        return None

    @staticmethod
    def load_view(plugin_path, frame_name):
        """Load view

        Parameters
        ----------
        plugin_path : str
            plugin path
        frame_name : str
            frame name

        Returns
        -------
        frame_class : class
            tkinter frame class
        """
        frame_file_name = "_".join(frame_name.lower().split()) + "_frame.py"
        frame_class_name = "".join(frame_name.title().split()) + "Frame"
        frame_file_path = os.path.join(plugin_path, "view", frame_file_name)
        if os.path.exists(frame_file_path) and os.path.isfile(frame_file_path):
            module = load_module_from_file(frame_class_name, frame_file_path)
            return getattr(module, frame_class_name)
        return None

    @staticmethod
    def load_feature_lists(plugin_path, register_func):
        """Load feature lists

        Parameters
        ----------
        plugin_path : str
            plugin path
        register_func : func
            the function to handle feature lists
        """
        plugin_feature_list = os.path.join(plugin_path, "feature_list.py")
        if os.path.exists(plugin_feature_list):
            module = load_module_from_file("feature_list_temp", plugin_feature_list)
            register_func(plugin_feature_list, module)

    @staticmethod
    def load_features(plugin_path):
        """Load features

        Parameters
        ----------
        plugin_path : str
            plugin path
        """
        features_dir = os.path.join(plugin_path, "model", "features")
        features = []
        if os.path.exists(features_dir):
            features = os.listdir(features_dir)
        for feature in features:
            feature_file = os.path.join(features_dir, feature)
            if os.path.isfile(feature_file):
                module = load_module_from_file(feature, feature_file)
                register_features(module)

    @staticmethod
    def load_acquisition_modes(plugin_path, acquisition_modes, register_func):
        """Load acquisition modes

        Parameters
        ----------
        plugin_path : str
            plugin path
        acquisition_modes : []
            list of acquisition mode configurations
        register_func : func
            the function to register acquisition modes
        """
        for acquisition_mode_config in acquisition_modes:
            acquisition_file = acquisition_mode_config["file_name"]
            full_path_name = os.path.join(plugin_path, acquisition_file)
            if os.path.exists(full_path_name):
                module = load_module_from_file(acquisition_file[:-3], full_path_name)
                if module:
                    register_func(acquisition_mode_config["name"], module)

    @staticmethod
    def load_devices(plugin_path, register_func):
        """Load devices

        Parameters
        ----------
        plugin_path : str
            plugin path
        register_func : func
            the function to register devices
        """
        device_dir = os.path.join(plugin_path, "model", "devices")
        if os.path.exists(device_dir) and os.path.isdir(device_dir):
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
                register_func(device, module)
