from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from navigate.controller.sub_controllers.plugins import (
    PluginsController,
    UninstallPluginController,
)
from navigate.tools.decorators import AcquisitionMode


@pytest.fixture
def plugins_controller():
    view = MagicMock()
    view.settings = MagicMock()
    view.menubar.menu_plugins = MagicMock()
    parent_controller = MagicMock()
    parent_controller.view = view
    parent_controller.register_event_listeners = MagicMock()
    return PluginsController(view, parent_controller)


def test_populate_experiment_setting_handles_controller_error(plugins_controller):
    good_plugin = MagicMock()
    bad_plugin = MagicMock()
    bad_plugin.populate_experiment_setting.side_effect = RuntimeError("boom")
    plugins_controller.plugins_dict = {"good": good_plugin, "bad": bad_plugin}

    plugins_controller.populate_experiment_setting()

    good_plugin.populate_experiment_setting.assert_called_once()
    bad_plugin.populate_experiment_setting.assert_called_once()


@patch("navigate.controller.sub_controllers.plugins.get_navigate_path")
@patch("navigate.controller.sub_controllers.plugins.PluginFileManager")
@patch("navigate.controller.sub_controllers.plugins.PluginPackageManager")
def test_load_plugins_calls_both_managers(
    mock_package_manager, mock_file_manager, mock_get_navigate_path, plugins_controller
):
    mock_get_navigate_path.return_value = "/tmp/navigate"
    file_manager_instance = MagicMock()
    mock_file_manager.return_value = file_manager_instance
    plugins_controller.load_plugins_through_manager = MagicMock()

    plugins_controller.load_plugins()

    mock_file_manager.assert_called_once()
    assert plugins_controller.load_plugins_through_manager.call_count == 2
    first_call_arg = plugins_controller.load_plugins_through_manager.call_args_list[0][
        0
    ][0]
    second_call_arg = plugins_controller.load_plugins_through_manager.call_args_list[1][
        0
    ][0]
    assert first_call_arg is file_manager_instance
    assert second_call_arg is mock_package_manager


def test_load_plugins_through_manager_routes_popup_and_tab(plugins_controller):
    popup_frame = MagicMock()
    tab_frame = MagicMock()
    popup_controller = MagicMock()
    tab_controller = MagicMock()
    popup_menu_command = MagicMock()

    manager = MagicMock()
    manager.get_plugins.return_value = {"popup_plugin": "p_ref", "tab_plugin": "t_ref"}
    manager.load_config.side_effect = lambda ref: {
        "p_ref": {"view": "Popup", "name": "Popup Display", "acquisition_modes": ["m"]},
        "t_ref": {"view": "Tab", "name": "Tab Display", "acquisition_modes": []},
    }[ref]
    manager.load_view.side_effect = lambda ref, _name: {
        "p_ref": popup_frame,
        "t_ref": tab_frame,
    }[ref]
    manager.load_controller.side_effect = lambda ref, _name: {
        "p_ref": popup_controller,
        "t_ref": tab_controller,
    }[ref]

    plugins_controller.build_popup_window = MagicMock(return_value=popup_menu_command)
    plugins_controller.build_tab_window = MagicMock()

    plugins_controller.load_plugins_through_manager(manager)

    plugins_controller.view.menubar.menu_plugins.add_command.assert_called_once_with(
        label="popup_plugin", command=popup_menu_command
    )
    plugins_controller.build_tab_window.assert_called_once_with(
        "tab_plugin", tab_frame, tab_controller
    )
    assert manager.load_features.call_count == 2
    assert manager.load_acquisition_modes.call_count == 2


def test_load_plugins_through_manager_skips_none_config(plugins_controller):
    manager = MagicMock()
    manager.get_plugins.return_value = {"bad_plugin": "bad_ref"}
    manager.load_config.return_value = None

    plugins_controller.load_plugins_through_manager(manager)

    manager.load_view.assert_not_called()
    manager.load_controller.assert_not_called()


def test_build_tab_window_success(plugins_controller):
    plugin_frame_obj = MagicMock()
    plugin_controller_obj = MagicMock()
    plugin_controller_obj.custom_events = {"evt": MagicMock()}
    frame_factory = MagicMock(return_value=plugin_frame_obj)
    controller_factory = MagicMock(return_value=plugin_controller_obj)

    plugins_controller.build_tab_window("My Plugin", frame_factory, controller_factory)

    plugins_controller.view.settings.add.assert_called_once()
    plugins_controller.parent_controller.register_event_listeners.assert_called_once_with(
        {"evt": plugin_controller_obj.custom_events["evt"]}
    )
    assert "__pluginmy_plugin_controller" in plugins_controller.plugins_dict


@patch("navigate.controller.sub_controllers.plugins.messagebox.showwarning")
def test_build_tab_window_failure_shows_warning(mock_warning, plugins_controller):
    frame_factory = MagicMock(side_effect=RuntimeError("tab failure"))
    controller_factory = MagicMock()

    plugins_controller.build_tab_window("Broken Plugin", frame_factory, controller_factory)

    mock_warning.assert_called_once()


def test_build_popup_window_existing_controller(plugins_controller):
    existing = MagicMock()
    controller_name = "__pluginpopup_plugin_controller"
    plugins_controller.plugins_dict[controller_name] = existing

    func = plugins_controller.build_popup_window("Popup Plugin", MagicMock(), MagicMock())
    func()

    existing.popup.deiconify.assert_called_once()


@patch("navigate.controller.sub_controllers.plugins.PopUp")
@patch("navigate.controller.sub_controllers.plugins.messagebox.showwarning")
def test_build_popup_window_wrapper_handles_error(
    mock_warning, mock_popup, plugins_controller
):
    popup = MagicMock()
    popup.get_frame.return_value = MagicMock()
    mock_popup.return_value = popup
    frame_factory = MagicMock(side_effect=RuntimeError("popup failure"))

    func = plugins_controller.build_popup_window("Popup Plugin", frame_factory, MagicMock())
    func()

    mock_warning.assert_called_once()


def test_register_acquisition_mode(plugins_controller):
    plugins_controller.parent_controller.add_acquisition_mode = MagicMock()
    plugins_controller.register_acquisition_mode("my_mode", None)
    plugins_controller.parent_controller.add_acquisition_mode.assert_not_called()

    class DummyAcquisition:
        pass

    module = SimpleNamespace(MyMode=AcquisitionMode(DummyAcquisition), not_mode=object())
    plugins_controller.register_acquisition_mode("my_mode", module)
    plugins_controller.parent_controller.add_acquisition_mode.assert_called_once_with(
        "my_mode", module.MyMode
    )


def test_uninstall_refresh_plugins_defaults_to_empty():
    controller = UninstallPluginController.__new__(UninstallPluginController)
    controller.plugin_config_path = "/tmp/navigate/config"
    controller.popup = MagicMock()

    with patch(
        "navigate.controller.sub_controllers.plugins.load_yaml_file", return_value=None
    ):
        controller.refresh_plugins()

    assert controller.plugin_config == {}
    controller.popup.build_widgets.assert_called_once_with({})


@patch("navigate.controller.sub_controllers.plugins.messagebox.showwarning")
@patch("navigate.controller.sub_controllers.plugins.save_yaml_file")
@patch("navigate.controller.sub_controllers.plugins.load_yaml_file")
@patch("navigate.controller.sub_controllers.plugins.os.remove")
@patch("navigate.controller.sub_controllers.plugins.os.listdir")
@patch("navigate.controller.sub_controllers.plugins.get_navigate_path")
def test_uninstall_plugins_removes_files_and_updates_config(
    mock_get_navigate_path,
    mock_listdir,
    mock_remove,
    mock_load_yaml,
    mock_save_yaml,
    mock_warning,
):
    mock_get_navigate_path.return_value = "/tmp/navigate"
    mock_listdir.return_value = ["plugin_feature.yml", "__sequence.yml"]

    def load_side_effect(path):
        if path.endswith("plugin_feature.yml"):
            return {"filename": "/plugins/a/features.py"}
        return {}

    mock_load_yaml.side_effect = load_side_effect

    controller = UninstallPluginController.__new__(UninstallPluginController)
    controller.plugin_config_path = "/tmp/navigate/config"
    controller.plugin_config = {"PluginA": "/plugins/a"}
    selected_var = MagicMock()
    selected_var.get.return_value = "PluginA"
    controller.popup = MagicMock()
    controller.popup.variables = [selected_var]
    controller.showup = MagicMock()

    controller.uninstall_plugins()

    mock_remove.assert_called_once()
    mock_save_yaml.assert_called_once()
    mock_warning.assert_called_once()
    controller.showup.assert_called_once()
    assert "PluginA" not in controller.plugin_config
