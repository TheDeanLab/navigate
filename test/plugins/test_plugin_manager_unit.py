import os
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock
import builtins

import pytest

try:
    from navigate.plugins import plugin_manager as pm
except ModuleNotFoundError:  # pragma: no cover - fallback for src-layout test envs
    from src.navigate.plugins import plugin_manager as pm


class _ResourcePath:
    def __init__(self, base):
        self.base = base

    def joinpath(self, name):
        return f"{self.base}/{name}"


def _write_python(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_register_features_registers_classes_only():
    feature_cls = type("UnitTestFeatureClass", (), {})
    module = ModuleType("dummy_module")
    module.UnitTestFeatureClass = feature_cls
    module.helper = lambda: None
    module.VALUE = 5

    try:
        pm.register_features(module)
        assert getattr(pm.feature_related_functions, "UnitTestFeatureClass") is feature_cls
    finally:
        if hasattr(pm.feature_related_functions, "UnitTestFeatureClass"):
            delattr(pm.feature_related_functions, "UnitTestFeatureClass")


def test_package_manager_get_plugins_deduplicates_names(monkeypatch):
    test_entry_points = [
        SimpleNamespace(module="plugin_alpha.controller"),
        SimpleNamespace(module="plugin_alpha.view"),
        SimpleNamespace(module="plugin_beta.main"),
    ]
    monkeypatch.setattr(
        pm,
        "entry_points",
        lambda: {"navigate.plugins": test_entry_points},
    )
    print_mock = MagicMock()
    monkeypatch.setattr(builtins, "print", print_mock)

    plugins = pm.PluginPackageManager.get_plugins()

    assert plugins == {
        "plugin_alpha": "plugin_alpha",
        "plugin_beta": "plugin_beta",
    }
    assert any(
        "Warning: plugin plugin_alpha exists and cannot be loaded more than once."
        in str(call.args[0])
        for call in print_mock.call_args_list
        if call.args
    )


def test_package_manager_load_config_reads_from_package_resources(monkeypatch):
    load_yaml_mock = MagicMock(return_value={"name": "Demo Plugin"})
    monkeypatch.setattr(pm, "load_yaml_file", load_yaml_mock)
    monkeypatch.setattr(
        pm.importlib.resources,
        "files",
        lambda package_name: f"/fake/{package_name}",
    )

    config = pm.PluginPackageManager.load_config("demo_pkg")

    assert config == {"name": "Demo Plugin"}
    load_yaml_mock.assert_called_once_with(
        os.path.join("/fake/demo_pkg", "plugin_config.yml")
    )


@pytest.mark.parametrize(
    ("loader", "item_name", "module_name", "class_name"),
    [
        (
            pm.PluginPackageManager.load_controller,
            "camera",
            "demo_pkg.controller.camera_controller",
            "CameraController",
        ),
        (
            pm.PluginPackageManager.load_view,
            "camera",
            "demo_pkg.view.camera_frame",
            "CameraFrame",
        ),
    ],
)
def test_package_manager_dynamic_load_success(
    monkeypatch, loader, item_name, module_name, class_name
):
    klass = type(class_name, (), {})
    loaded_module = SimpleNamespace(**{class_name: klass})
    monkeypatch.setattr(
        pm.importlib,
        "import_module",
        lambda name: loaded_module if name == module_name else None,
    )

    assert loader("demo_pkg", item_name) is klass


@pytest.mark.parametrize(
    ("loader", "item_name"),
    [
        (pm.PluginPackageManager.load_controller, "camera"),
        (pm.PluginPackageManager.load_view, "camera"),
    ],
)
def test_package_manager_dynamic_load_returns_none_on_import_error(
    monkeypatch, loader, item_name
):
    monkeypatch.setattr(
        pm.importlib,
        "import_module",
        MagicMock(side_effect=ImportError("missing plugin module")),
    )

    assert loader("demo_pkg", item_name) is None


@pytest.mark.parametrize(
    ("loader", "item_name"),
    [
        (pm.PluginPackageManager.load_controller, "camera"),
        (pm.PluginPackageManager.load_view, "camera"),
    ],
)
def test_package_manager_dynamic_load_returns_none_on_missing_attribute(
    monkeypatch, loader, item_name
):
    monkeypatch.setattr(
        pm.importlib,
        "import_module",
        lambda _name: SimpleNamespace(),
    )

    assert loader("demo_pkg", item_name) is None


def test_package_manager_load_feature_lists_registers_module(monkeypatch):
    module = SimpleNamespace()
    register = MagicMock()
    monkeypatch.setattr(
        pm.importlib.resources,
        "files",
        lambda package_name: _ResourcePath(f"/fake/{package_name}"),
    )
    monkeypatch.setattr(pm.importlib, "import_module", lambda _name: module)

    pm.PluginPackageManager.load_feature_lists("demo_pkg", register)

    register.assert_called_once_with("/fake/demo_pkg/feature_list.py", module)


def test_package_manager_load_feature_lists_ignores_import_errors(monkeypatch):
    register = MagicMock()
    monkeypatch.setattr(
        pm.importlib,
        "import_module",
        MagicMock(side_effect=ImportError("not found")),
    )

    pm.PluginPackageManager.load_feature_lists("demo_pkg", register)

    register.assert_not_called()


def test_package_manager_load_features_registers_non_package_modules(monkeypatch):
    good_module = SimpleNamespace()
    monkeypatch.setattr(
        pm.importlib.resources,
        "files",
        lambda package_name: _ResourcePath(f"/fake/{package_name}"),
    )
    monkeypatch.setattr(
        pm.pkgutil,
        "iter_modules",
        lambda _paths: [
            (None, "good_feature", False),
            (None, "nested_package", True),
            (None, "bad_feature", False),
        ],
    )

    def _import_module(name):
        if name.endswith("good_feature"):
            return good_module
        raise ImportError("bad feature import")

    monkeypatch.setattr(pm.importlib, "import_module", _import_module)
    register_features_mock = MagicMock()
    monkeypatch.setattr(pm, "register_features", register_features_mock)

    pm.PluginPackageManager.load_features("demo_pkg")

    register_features_mock.assert_called_once_with(good_module)


def test_package_manager_load_acquisition_modes_handles_missing_modules(monkeypatch):
    mode_module = SimpleNamespace()

    def _import_module(name):
        if name == "demo_pkg.fast_scan":
            return mode_module
        raise ImportError("mode missing")

    monkeypatch.setattr(pm.importlib, "import_module", _import_module)
    register = MagicMock()
    acquisition_modes = [
        {"file_name": "fast_scan.py", "name": "Fast Scan"},
        {"file_name": "slow_scan.py", "name": "Slow Scan"},
    ]

    pm.PluginPackageManager.load_acquisition_modes(
        "demo_pkg", acquisition_modes, register
    )

    register.assert_called_once_with("Fast Scan", mode_module)


def test_package_manager_load_devices_registers_only_package_modules(monkeypatch):
    device_module = SimpleNamespace()
    monkeypatch.setattr(
        pm.importlib.resources,
        "files",
        lambda package_name: _ResourcePath(f"/fake/{package_name}"),
    )
    monkeypatch.setattr(
        pm.pkgutil,
        "iter_modules",
        lambda _paths: [
            (None, "camera", True),
            (None, "helpers", False),
            (None, "laser", True),
        ],
    )

    def _import_module(name):
        if name.endswith("camera.device_startup_functions"):
            return device_module
        raise ImportError("device module missing")

    monkeypatch.setattr(pm.importlib, "import_module", _import_module)
    register = MagicMock()

    pm.PluginPackageManager.load_devices("demo_pkg", register)

    register.assert_called_once_with("camera", device_module)


def test_file_manager_get_plugins_combines_local_and_configured_paths(
    tmp_path, monkeypatch
):
    plugins_path = tmp_path / "plugins"
    plugins_path.mkdir()
    (plugins_path / "local_plugin").mkdir()
    (plugins_path / "not_a_plugin.txt").write_text("ignore me", encoding="utf-8")

    extra_plugin = tmp_path / "external_plugin"
    extra_plugin.mkdir()
    missing_plugin = tmp_path / "missing_plugin"

    monkeypatch.setattr(
        pm,
        "load_yaml_file",
        lambda _path: {
            "external_plugin": str(extra_plugin),
            "missing_plugin": str(missing_plugin),
        },
    )
    manager = pm.PluginFileManager(str(plugins_path), str(tmp_path / "plugins.yml"))

    plugins = manager.get_plugins()

    assert plugins == {
        "local_plugin": str(plugins_path / "local_plugin"),
        "external_plugin": str(extra_plugin),
    }


def test_file_manager_load_config_reads_yaml(monkeypatch):
    load_yaml_mock = MagicMock(return_value={"name": "Test"})
    monkeypatch.setattr(pm, "load_yaml_file", load_yaml_mock)

    config = pm.PluginFileManager.load_config("/tmp/my_plugin")

    assert config == {"name": "Test"}
    load_yaml_mock.assert_called_once_with(
        os.path.join("/tmp/my_plugin", "plugin_config.yml")
    )


def test_file_manager_load_controller_and_view_from_files(tmp_path):
    plugin_path = tmp_path / "example_plugin"
    controller_path = plugin_path / "controller" / "camera_controller.py"
    view_path = plugin_path / "view" / "camera_frame.py"
    _write_python(controller_path, "class CameraController:\n    pass\n")
    _write_python(view_path, "class CameraFrame:\n    pass\n")

    controller_cls = pm.PluginFileManager.load_controller(str(plugin_path), "camera")
    view_cls = pm.PluginFileManager.load_view(str(plugin_path), "camera")

    assert controller_cls.__name__ == "CameraController"
    assert view_cls.__name__ == "CameraFrame"


def test_file_manager_load_controller_and_view_return_none_when_missing(tmp_path):
    plugin_path = tmp_path / "example_plugin"
    plugin_path.mkdir()

    assert pm.PluginFileManager.load_controller(str(plugin_path), "camera") is None
    assert pm.PluginFileManager.load_view(str(plugin_path), "camera") is None


def test_file_manager_load_feature_lists_registers_only_if_feature_list_exists(tmp_path):
    plugin_path = tmp_path / "feature_plugin"
    register = MagicMock()

    pm.PluginFileManager.load_feature_lists(str(plugin_path), register)
    register.assert_not_called()

    feature_list_path = plugin_path / "feature_list.py"
    _write_python(feature_list_path, "VALUE = 1\n")
    pm.PluginFileManager.load_feature_lists(str(plugin_path), register)
    register.assert_called_once()
    assert register.call_args.args[0] == str(feature_list_path)


def test_file_manager_load_features_loads_only_feature_files(tmp_path, monkeypatch):
    plugin_path = tmp_path / "feature_plugin"
    features_dir = plugin_path / "model" / "features"
    _write_python(features_dir / "focus_lock.py", "class FocusLock:\n    pass\n")
    (features_dir / "nested_dir").mkdir(parents=True)

    register_features_mock = MagicMock()
    monkeypatch.setattr(pm, "register_features", register_features_mock)

    pm.PluginFileManager.load_features(str(plugin_path))

    assert register_features_mock.call_count == 1


def test_file_manager_load_acquisition_modes_registers_existing_files(tmp_path):
    plugin_path = tmp_path / "acq_plugin"
    _write_python(plugin_path / "fast_scan.py", "VALUE = 'fast'\n")
    register = MagicMock()

    pm.PluginFileManager.load_acquisition_modes(
        str(plugin_path),
        [
            {"file_name": "fast_scan.py", "name": "Fast Scan"},
            {"file_name": "slow_scan.py", "name": "Slow Scan"},
        ],
        register,
    )

    register.assert_called_once()
    assert register.call_args.args[0] == "Fast Scan"


def test_file_manager_load_devices_registers_device_folders(tmp_path):
    plugin_path = tmp_path / "device_plugin"
    devices_path = plugin_path / "model" / "devices"
    _write_python(
        devices_path / "camera" / "device_startup_functions.py",
        "DEVICE_TYPE_NAME='camera'\n"
        "SUPPORTED_DEVICE_TYPES=['synthetic']\n"
        "def load_device():\n    return 'load'\n"
        "def start_device():\n    return 'start'\n",
    )
    (devices_path / "missing_startup").mkdir(parents=True)
    _write_python(devices_path / "README.txt", "not a folder\n")
    register = MagicMock()

    pm.PluginFileManager.load_devices(str(plugin_path), register)

    register.assert_called_once()
    assert register.call_args.args[0] == "camera"
