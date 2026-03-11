from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

import navigate.controller.sub_controllers.plugins as plugins_module
from navigate.tools.decorators import AcquisitionMode


@pytest.fixture
def plugins_controller():
    view = MagicMock()
    view.settings = MagicMock()

    parent_controller = MagicMock()
    parent_controller.view = SimpleNamespace(
        menubar=SimpleNamespace(menu_plugins=MagicMock())
    )
    parent_controller.register_event_listeners = MagicMock()
    parent_controller.add_acquisition_mode = MagicMock()

    return plugins_module.PluginsController(view, parent_controller)


def test_load_plugins_uses_file_and_package_managers(monkeypatch, plugins_controller):
    file_manager = MagicMock()
    file_manager_ctor = Mock(return_value=file_manager)
    monkeypatch.setattr(plugins_module, "PluginFileManager", file_manager_ctor)
    monkeypatch.setattr(plugins_module, "get_navigate_path", lambda: "/tmp/navigate-home")

    plugins_controller.load_plugins_through_manager = MagicMock()

    plugins_controller.load_plugins()

    file_manager_ctor.assert_called_once()
    assert plugins_controller.load_plugins_through_manager.call_args_list[0].args[0] is file_manager
    assert (
        plugins_controller.load_plugins_through_manager.call_args_list[1].args[0]
        is plugins_module.PluginPackageManager
    )


def test_load_plugins_through_manager_skips_plugins_without_config(plugins_controller):
    plugin_manager = MagicMock()
    plugin_manager.get_plugins.return_value = {"Plugin A": "ref-a"}
    plugin_manager.load_config.return_value = None

    plugins_controller.load_plugins_through_manager(plugin_manager)

    plugin_manager.load_view.assert_not_called()
    plugin_manager.load_controller.assert_not_called()
    plugin_manager.load_features.assert_not_called()
    plugin_manager.load_acquisition_modes.assert_not_called()


def test_load_plugins_through_manager_registers_popup_plugins(plugins_controller):
    plugin_manager = MagicMock()
    plugin_manager.get_plugins.return_value = {"Plugin A": "ref-a"}
    plugin_manager.load_config.return_value = {
        "name": "Plugin A Display",
        "view": "Popup",
        "acquisition_modes": ["fast"],
    }
    frame_cls = Mock(name="FrameClass")
    controller_cls = Mock(name="ControllerClass")
    plugin_manager.load_view.return_value = frame_cls
    plugin_manager.load_controller.return_value = controller_cls

    plugins_controller.load_plugins_through_manager(plugin_manager)

    add_command = plugins_controller.parent_controller.view.menubar.menu_plugins.add_command
    add_command.assert_called_once()
    call_kwargs = add_command.call_args.kwargs
    assert call_kwargs["label"] == "Plugin A"
    assert callable(call_kwargs["command"])
    plugin_manager.load_features.assert_called_once_with("ref-a")
    plugin_manager.load_acquisition_modes.assert_called_once()


def test_load_plugins_through_manager_registers_tab_plugins(plugins_controller):
    plugin_manager = MagicMock()
    plugin_manager.get_plugins.return_value = {"Plugin A": "ref-a"}
    plugin_manager.load_config.return_value = {
        "name": "Plugin A Display",
        "view": "Tab",
        "acquisition_modes": [],
    }
    frame_cls = Mock(name="FrameClass")
    controller_cls = Mock(name="ControllerClass")
    plugin_manager.load_view.return_value = frame_cls
    plugin_manager.load_controller.return_value = controller_cls
    plugins_controller.build_tab_window = MagicMock()

    plugins_controller.load_plugins_through_manager(plugin_manager)

    plugins_controller.build_tab_window.assert_called_once_with(
        "Plugin A", frame_cls, controller_cls
    )


def test_build_tab_window_registers_controller_and_events(plugins_controller):
    plugin_frame = MagicMock()
    frame_cls = Mock(return_value=plugin_frame)
    plugin_controller = SimpleNamespace(custom_events={"evt": "handler"})
    controller_cls = Mock(return_value=plugin_controller)

    plugins_controller.build_tab_window("My Plugin", frame_cls, controller_cls)

    plugins_controller.view.settings.add.assert_called_once_with(
        plugin_frame, text="My Plugin", sticky=plugins_module.tk.NSEW
    )
    plugins_controller.parent_controller.register_event_listeners.assert_called_once_with(
        plugin_controller.custom_events
    )
    assert "__pluginmy_plugin_controller" in plugins_controller.plugins_dict


def test_build_tab_window_warns_on_failure(monkeypatch, plugins_controller):
    frame_cls = Mock(side_effect=RuntimeError("broken frame"))
    warning = Mock()
    monkeypatch.setattr(plugins_module.messagebox, "showwarning", warning)

    plugins_controller.build_tab_window("My Plugin", frame_cls, Mock())

    warning.assert_called_once()
    assert "__pluginmy_plugin_controller" not in plugins_controller.plugins_dict


def test_build_popup_window_reuses_existing_popup(plugins_controller):
    controller_name = "__pluginmy_plugin_controller"
    existing_controller = SimpleNamespace(popup=MagicMock())
    plugins_controller.plugins_dict[controller_name] = existing_controller

    show_popup = plugins_controller.build_popup_window("My Plugin", Mock(), Mock())
    show_popup()

    existing_controller.popup.deiconify.assert_called_once()


def test_build_popup_window_creates_popup_and_unregisters_on_close(
    monkeypatch, plugins_controller
):
    class FakePopup:
        def __init__(self):
            self._frame = MagicMock()
            self.deiconify = MagicMock()
            self.dismiss = MagicMock()
            self.protocol_name = None
            self.protocol_callback = None

        def configure(self, **kwargs):
            return None

        def resizable(self, *args):
            return None

        def get_frame(self):
            return self._frame

        def protocol(self, name, callback):
            self.protocol_name = name
            self.protocol_callback = callback

    popup = FakePopup()
    monkeypatch.setattr(plugins_module, "PopUp", Mock(return_value=popup))
    monkeypatch.setattr(plugins_module, "uniform_grid", Mock())

    plugin_frame = MagicMock()
    frame_cls = Mock(return_value=plugin_frame)
    plugin_controller = SimpleNamespace(custom_events={"evt": "handler"})
    controller_cls = Mock(return_value=plugin_controller)

    show_popup = plugins_controller.build_popup_window("My Plugin", frame_cls, controller_cls)
    show_popup()

    controller_name = "__pluginmy_plugin_controller"
    assert plugins_controller.plugins_dict[controller_name] is plugin_controller
    assert plugin_controller.popup is popup
    assert popup.protocol_name == "WM_DELETE_WINDOW"
    plugins_controller.parent_controller.register_event_listeners.assert_called_once_with(
        plugin_controller.custom_events
    )

    popup.protocol_callback()
    popup.dismiss.assert_called_once()
    assert controller_name not in plugins_controller.plugins_dict


def test_build_popup_window_wrapper_shows_warning_on_error(
    monkeypatch, plugins_controller
):
    warning = Mock()
    monkeypatch.setattr(plugins_module.messagebox, "showwarning", warning)
    monkeypatch.setattr(plugins_module, "PopUp", Mock(return_value=MagicMock()))

    show_popup = plugins_controller.build_popup_window(
        "Broken Plugin", Mock(side_effect=RuntimeError("boom")), Mock()
    )
    show_popup()

    warning.assert_called_once()


def test_populate_experiment_setting_ignores_plugin_exceptions(plugins_controller):
    good_plugin = MagicMock()
    bad_plugin = MagicMock()
    bad_plugin.populate_experiment_setting.side_effect = RuntimeError("bad plugin")
    plugins_controller.plugins_dict = {"good": good_plugin, "bad": bad_plugin}

    plugins_controller.populate_experiment_setting()

    good_plugin.populate_experiment_setting.assert_called_once()
    bad_plugin.populate_experiment_setting.assert_called_once()


def test_register_acquisition_mode_branches(plugins_controller):
    plugins_controller.register_acquisition_mode("mode-a", None)
    plugins_controller.parent_controller.add_acquisition_mode.assert_not_called()

    module = SimpleNamespace(
        not_mode=object(),
        mode=AcquisitionMode(object),
    )
    plugins_controller.register_acquisition_mode("mode-a", module)

    plugins_controller.parent_controller.add_acquisition_mode.assert_called_once_with(
        "mode-a", module.mode
    )
