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

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import navigate.model.plugins_model as plugins_model_module
from navigate.model.plugins_model import PluginsModel


class TestPluginsModel(unittest.TestCase):

    # comment this testcase since plugin_model doesn't have plugins_path now
    # @patch("os.path.join")
    # @patch("pathlib.Path.resolve")
    # def test_initialization(self, mock_resolve, mock_join):
    #     mock_resolve.return_value.parent.parent = "mocked_path"
    #     mock_join.return_value = "mocked_path/plugins"
    #     model = PluginsModel()
    #     self.assertEqual(model.plugins_path, "mocked_path/plugins")

    @patch("navigate.config.config.get_navigate_path")
    @patch("os.makedirs")
    def test_load_plugins(
        self,
        mock_get_nav_path,
        mock_makedirs,
    ):
        mock_get_nav_path.return_value = "mocked_navigate_path"
        model = PluginsModel()
        devices_dict, plugin_acquisition_modes = model.load_plugins()
        self.assertIsInstance(devices_dict, dict)
        self.assertIsInstance(plugin_acquisition_modes, dict)


@pytest.fixture
def plugins_model(tmp_path, monkeypatch):
    monkeypatch.setattr(
        plugins_model_module, "get_navigate_path", lambda: str(tmp_path)
    )
    return plugins_model_module.PluginsModel()


def test_load_plugins_creates_feature_list_path_and_uses_managers(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        plugins_model_module, "get_navigate_path", lambda: str(tmp_path)
    )
    model = plugins_model_module.PluginsModel()
    manager_instance = MagicMock(name="plugin_file_manager")
    manager_factory = MagicMock(return_value=manager_instance)
    load_plugins_through_manager = MagicMock()
    makedirs = MagicMock()

    monkeypatch.setattr(plugins_model_module.os.path, "exists", lambda _: False)
    monkeypatch.setattr(plugins_model_module.os, "makedirs", makedirs)
    monkeypatch.setattr(plugins_model_module, "PluginFileManager", manager_factory)
    monkeypatch.setattr(
        model, "load_plugins_through_manager", load_plugins_through_manager
    )

    devices_dict, plugin_acquisition_modes = model.load_plugins()

    assert devices_dict == {}
    assert plugin_acquisition_modes == {}
    makedirs.assert_called_once_with(str(tmp_path / "feature_lists"))
    assert manager_factory.call_count == 1
    assert (
        manager_factory.call_args.args[1]
        == str(tmp_path / "config" / "plugins_config.yml")
    )
    assert load_plugins_through_manager.call_count == 2
    assert load_plugins_through_manager.call_args_list[0].args[0] is manager_instance
    assert (
        load_plugins_through_manager.call_args_list[1].args[0]
        is plugins_model_module.PluginPackageManager
    )


def test_load_plugins_through_manager_skips_plugins_with_no_config(plugins_model):
    manager = MagicMock()
    manager.get_plugins.return_value = {
        "plugin-a": "ref-a",
        "plugin-b": "ref-b",
    }
    manager.load_config.side_effect = [
        None,
        {"acquisition_modes": [{"name": "Mode A", "file_name": "mode_a.py"}]},
    ]

    plugins_model.load_plugins_through_manager(manager)

    manager.load_features.assert_called_once_with("ref-b")
    manager.load_feature_lists.assert_called_once()
    manager.load_acquisition_modes.assert_called_once_with(
        "ref-b",
        [{"name": "Mode A", "file_name": "mode_a.py"}],
        plugins_model.register_acquisition_mode,
    )
    manager.load_devices.assert_called_once_with("ref-b", plugins_model.register_device)


def test_register_device_ignores_none_module(plugins_model):
    plugins_model.register_device("camera", None)
    assert plugins_model.devices_dict == {}


def test_register_device_prints_error_when_device_type_missing(plugins_model, capsys):
    module = SimpleNamespace(load_device=lambda: None, start_device=lambda: None)

    plugins_model.register_device("bad-device", module)

    assert "not set correctly" in capsys.readouterr().out


def test_register_device_prints_error_when_supported_types_missing(
    plugins_model, capsys
):
    module = SimpleNamespace(
        DEVICE_TYPE_NAME="camera",
        load_device=lambda: None,
        start_device=lambda: None,
    )

    plugins_model.register_device("camera-plugin", module)

    assert "SUPPORTED_DEVICE_TYPES" in capsys.readouterr().out


def test_register_device_core_device_adds_supported_types(plugins_model):
    load_device = lambda: "loaded"
    start_device = lambda: "started"
    module = SimpleNamespace(
        DEVICE_TYPE_NAME="camera",
        SUPPORTED_DEVICE_TYPES=["synthetic", "usb"],
        load_device=load_device,
        start_device=start_device,
    )

    plugins_model.register_device("camera-plugin", module)

    assert set(plugins_model.devices_dict["camera"]) == {"synthetic", "usb"}
    assert (
        plugins_model.devices_dict["camera"]["synthetic"]["load_device"]
        is load_device
    )
    assert (
        plugins_model.devices_dict["camera"]["synthetic"]["start_device"]
        is start_device
    )


def test_register_device_mmcore_expands_to_all_core_devices(plugins_model):
    load_device = lambda: "loaded"
    start_device = lambda: "started"
    module = SimpleNamespace(
        DEVICE_TYPE_NAME="MMCore",
        load_device=load_device,
        start_device=start_device,
    )

    plugins_model.register_device("mmcore-plugin", module)

    for device_name in (
        "camera",
        "remote_focus",
        "galvo",
        "filter_wheel",
        "stage",
        "zoom",
        "shutter",
        "laser",
    ):
        assert plugins_model.devices_dict[device_name]["MMCore"]["load_device"] is load_device
        assert (
            plugins_model.devices_dict[device_name]["MMCore"]["start_device"]
            is start_device
        )


def test_register_device_custom_device_adds_ref_list_and_handlers(plugins_model):
    load_device = lambda: "loaded"
    start_device = lambda: "started"
    module = SimpleNamespace(
        DEVICE_TYPE_NAME="multiple_devices",
        DEVICE_REF_LIST=["type"],
        load_device=load_device,
        start_device=start_device,
    )

    plugins_model.register_device("custom-plugin", module)

    assert plugins_model.devices_dict["multiple_devices"]["ref_list"] == ["type"]
    assert plugins_model.devices_dict["multiple_devices"]["load_device"] is load_device
    assert (
        plugins_model.devices_dict["multiple_devices"]["start_device"] is start_device
    )


def test_register_acquisition_mode_handles_none_and_valid_modes(plugins_model):
    class DemoMode:
        def __init__(self, name):
            self.name = name

    plugins_model.register_acquisition_mode("none", None)
    assert "none" not in plugins_model.plugin_acquisition_modes

    plugins_model.register_acquisition_mode("invalid", SimpleNamespace(value=123))
    assert "invalid" not in plugins_model.plugin_acquisition_modes

    module = SimpleNamespace(
        DemoAcquisition=plugins_model_module.AcquisitionMode(DemoMode)
    )
    plugins_model.register_acquisition_mode("demo", module)
    assert plugins_model.plugin_acquisition_modes["demo"].name == "demo"


def test_register_feature_list_serializes_each_feature_entry(plugins_model, monkeypatch):
    def feature_one():
        return []

    def feature_two():
        return []

    module = SimpleNamespace(
        FeatureOne=plugins_model_module.FeatureList(feature_one),
        FeatureTwo=plugins_model_module.FeatureList(feature_two),
        other_value=42,
    )
    save_yaml = MagicMock()
    monkeypatch.setattr(plugins_model_module, "save_yaml_file", save_yaml)

    plugins_model.register_feature_list("plugin/feature_list.py", module)

    assert save_yaml.call_count == 2
    serialized_files = {call.args[2] for call in save_yaml.call_args_list}
    assert serialized_files == {"Feature_One.yml", "Feature_Two.yml"}
    for call in save_yaml.call_args_list:
        assert call.args[0] == plugins_model.feature_lists_path
        assert call.args[1]["filename"] == "plugin/feature_list.py"
