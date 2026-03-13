from types import SimpleNamespace
from unittest.mock import MagicMock
import builtins

import pytest

try:
    import navigate.model.plugins_model as plugins_model_module
    from navigate.model.plugins_model import PluginsModel
    from navigate.tools.decorators import AcquisitionMode, FeatureList
except ModuleNotFoundError:  # pragma: no cover - fallback for src-layout test envs
    import src.navigate.model.plugins_model as plugins_model_module
    from src.navigate.model.plugins_model import PluginsModel
    from src.navigate.tools.decorators import AcquisitionMode, FeatureList


@pytest.fixture
def plugins_model_instance(monkeypatch, tmp_path):
    navigate_home = tmp_path / "navigate_home"
    (navigate_home / "config").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        plugins_model_module,
        "get_navigate_path",
        lambda: str(navigate_home),
    )
    return PluginsModel()


def test_load_plugins_creates_feature_lists_path_and_loads_both_managers(
    plugins_model_instance, monkeypatch
):
    plugin_file_manager_instance = object()
    plugin_file_manager_ctor = MagicMock(return_value=plugin_file_manager_instance)
    monkeypatch.setattr(
        plugins_model_module, "PluginFileManager", plugin_file_manager_ctor
    )

    load_through_manager_mock = MagicMock()
    monkeypatch.setattr(
        plugins_model_instance, "load_plugins_through_manager", load_through_manager_mock
    )

    devices_dict, acquisition_modes = plugins_model_instance.load_plugins()

    assert plugins_model_instance.feature_lists_path
    assert devices_dict == {}
    assert acquisition_modes == {}
    plugin_file_manager_ctor.assert_called_once()
    assert load_through_manager_mock.call_count == 2
    assert load_through_manager_mock.call_args_list[0].args[0] is (
        plugin_file_manager_instance
    )
    assert load_through_manager_mock.call_args_list[1].args[0] is (
        plugins_model_module.PluginPackageManager
    )


def test_load_plugins_through_manager_skips_plugins_with_missing_config(
    plugins_model_instance,
):
    plugin_manager = MagicMock()
    plugin_manager.get_plugins.return_value = {"one": "ref_one", "two": "ref_two"}
    plugin_manager.load_config.side_effect = [
        None,
        {"acquisition_modes": [{"file_name": "fast_mode.py", "name": "Fast Mode"}]},
    ]

    plugins_model_instance.load_plugins_through_manager(plugin_manager)

    plugin_manager.load_features.assert_called_once_with("ref_two")
    plugin_manager.load_feature_lists.assert_called_once_with(
        "ref_two", plugins_model_instance.register_feature_list
    )
    plugin_manager.load_acquisition_modes.assert_called_once_with(
        "ref_two",
        [{"file_name": "fast_mode.py", "name": "Fast Mode"}],
        plugins_model_instance.register_acquisition_mode,
    )
    plugin_manager.load_devices.assert_called_once_with(
        "ref_two", plugins_model_instance.register_device
    )


def test_register_device_ignores_none_module(plugins_model_instance):
    plugins_model_instance.register_device("camera", None)
    assert plugins_model_instance.devices_dict == {}


def test_register_device_reports_missing_device_type_name(
    plugins_model_instance, monkeypatch
):
    print_mock = MagicMock()
    monkeypatch.setattr(builtins, "print", print_mock)

    plugins_model_instance.register_device("bad_device", SimpleNamespace())

    print_mock.assert_called_once()
    assert "not set correctly" in print_mock.call_args.args[0]
    assert plugins_model_instance.devices_dict == {}


def test_register_device_reports_missing_supported_types_for_core_device(
    plugins_model_instance, monkeypatch
):
    print_mock = MagicMock()
    monkeypatch.setattr(builtins, "print", print_mock)
    module = SimpleNamespace(
        DEVICE_TYPE_NAME="camera",
        load_device=lambda: "load",
        start_device=lambda: "start",
    )

    plugins_model_instance.register_device("camera", module)

    print_mock.assert_called_once()
    assert "SUPPORTED_DEVICE_TYPES" in print_mock.call_args.args[0]
    assert plugins_model_instance.devices_dict == {}


def test_register_device_adds_supported_core_device_types(plugins_model_instance):
    load_device = lambda: "load_camera"
    start_device = lambda: "start_camera"
    module = SimpleNamespace(
        DEVICE_TYPE_NAME="camera",
        SUPPORTED_DEVICE_TYPES=["synthetic", "hamamatsu"],
        load_device=load_device,
        start_device=start_device,
    )

    plugins_model_instance.register_device("camera", module)

    assert "camera" in plugins_model_instance.devices_dict
    assert plugins_model_instance.devices_dict["camera"]["synthetic"] == {
        "load_device": load_device,
        "start_device": start_device,
    }
    assert plugins_model_instance.devices_dict["camera"]["hamamatsu"] == {
        "load_device": load_device,
        "start_device": start_device,
    }


def test_register_device_mmcore_maps_to_all_core_device_groups(plugins_model_instance):
    load_device = lambda: "load_mmcore"
    start_device = lambda: "start_mmcore"
    module = SimpleNamespace(
        DEVICE_TYPE_NAME="MMCore",
        load_device=load_device,
        start_device=start_device,
    )

    plugins_model_instance.register_device("multiple_devices", module)

    for core_device in [
        "camera",
        "remote_focus",
        "galvo",
        "filter_wheel",
        "stage",
        "zoom",
        "shutter",
        "laser",
    ]:
        assert plugins_model_instance.devices_dict[core_device]["MMCore"] == {
            "load_device": load_device,
            "start_device": start_device,
        }


def test_register_device_adds_non_core_device_with_ref_list(plugins_model_instance):
    load_device = lambda: "load_custom"
    start_device = lambda: "start_custom"
    module = SimpleNamespace(
        DEVICE_TYPE_NAME="spectrometer",
        DEVICE_REF_LIST=["name", "index"],
        load_device=load_device,
        start_device=start_device,
    )

    plugins_model_instance.register_device("spectrometer", module)

    assert plugins_model_instance.devices_dict["spectrometer"] == {
        "ref_list": ["name", "index"],
        "load_device": load_device,
        "start_device": start_device,
    }


def test_register_acquisition_mode_ignores_empty_module(plugins_model_instance):
    plugins_model_instance.register_acquisition_mode("Demo", None)
    plugins_model_instance.register_acquisition_mode("Demo", SimpleNamespace())
    assert plugins_model_instance.plugin_acquisition_modes == {}


def test_register_acquisition_mode_registers_first_acquisition_mode(
    plugins_model_instance,
):
    class DemoMode:
        def __init__(self, name):
            self.name = name

    module = SimpleNamespace(mode_entry=AcquisitionMode(DemoMode), other_value=1)

    plugins_model_instance.register_acquisition_mode("Demo", module)

    assert "Demo" in plugins_model_instance.plugin_acquisition_modes
    registered_mode = plugins_model_instance.plugin_acquisition_modes["Demo"]
    assert isinstance(registered_mode, DemoMode)
    assert registered_mode.name == "Demo"


def test_register_feature_list_persists_discovered_feature_metadata(
    plugins_model_instance, monkeypatch
):
    save_yaml_mock = MagicMock()
    monkeypatch.setattr(plugins_model_module, "save_yaml_file", save_yaml_mock)

    @FeatureList
    def coarse_focus():
        return None

    module = SimpleNamespace(coarse_focus=coarse_focus, non_feature="value")

    plugins_model_instance.register_feature_list("/tmp/plugin/feature_list.py", module)

    save_yaml_mock.assert_called_once()
    args = save_yaml_mock.call_args.args
    assert args[0] == plugins_model_instance.feature_lists_path
    assert args[1] == {
        "module_name": "coarse_focus",
        "feature_list_name": "Coarse Focus",
        "filename": "/tmp/plugin/feature_list.py",
    }
    assert args[2] == "Coarse_Focus.yml"
