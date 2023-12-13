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

import os
from pathlib import Path
import inspect

from navigate.tools.common_functions import load_module_from_file
from navigate.tools.file_functions import load_yaml_file
from navigate.model.features import feature_related_functions


class PluginsModel:
    def __init__(self):
        self.plugins_path = os.path.join(
            Path(__file__).resolve().parent.parent, "plugins"
        )

    def load_plugins(self):
        devices_dict = {}
        plugins = os.listdir(self.plugins_path)
        for f in plugins:
            if not os.path.isdir(os.path.join(self.plugins_path, f)):
                continue

            # read "plugin_config.yml"
            plugin_config = load_yaml_file(
                os.path.join(self.plugins_path, f, "plugin_config.yml")
            )
            if plugin_config is None:
                continue
            plugin_name = plugin_config.get("name", f)
            plugin_file_name = "_".join(plugin_name.lower().split())
            plugin_class_name = "".join(plugin_name.title().split())

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

            # device
            device_dir = os.path.join(self.plugins_path, f, "model", "devices")
            if os.path.exists(device_dir):
                devices = os.listdir(device_dir)
                for device in devices:
                    device_path = os.path.join(device_dir, device)
                    if not os.path.isdir(device_path):
                        continue
                    module = load_module_from_file(
                        "device_module",
                        os.path.join(device_path, "device_startup_functions.py"),
                    )
                    if module:
                        devices_dict[device] = {}
                        devices_dict[device]["ref_list"] = module.DEVICE_REF_LIST
                        devices_dict[device]["load_device"] = module.load_device
                        devices_dict[device]["start_device"] = module.start_device
        return devices_dict
