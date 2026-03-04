import os
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

import navigate.controller.sub_controllers.menus as menus_module


class DummyVar:
    def __init__(self, value=None):
        self.value = value
        self.trace_calls = []

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

    def trace_add(self, *args):
        self.trace_calls.append(args)


@pytest.fixture
def menu_controller(monkeypatch):
    monkeypatch.setattr(
        menus_module.tk,
        "StringVar",
        lambda *args, **kwargs: DummyVar(kwargs.get("value")),
    )
    monkeypatch.setattr(
        menus_module.tk,
        "IntVar",
        lambda *args, **kwargs: DummyVar(kwargs.get("value", 0)),
    )
    monkeypatch.setattr(
        menus_module.tk,
        "BooleanVar",
        lambda *args, **kwargs: DummyVar(kwargs.get("value", False)),
    )

    view = MagicMock()
    view.settings = MagicMock()
    view.camera_waveform = MagicMock()
    view.menubar = MagicMock()

    parent_controller = SimpleNamespace()
    parent_controller.view = view
    parent_controller.configuration = {
        "experiment": {
            "StageParameters": {"limits": True},
            "MicroscopeState": {"microscope_name": "ScopeA"},
        },
        "configuration": {
            "microscopes": {
                "ScopeA": {
                    "zoom": {"position": {"10x": 10, "20x": 20}},
                    "mirror": {"hardware": {"type": "real-mirror"}},
                }
            }
        },
        "rest_api_config": {"Ilastik": {"url": "http://ilastik.invalid"}},
        "waveform_constants": {"constants": "value"},
    }
    parent_controller.model = MagicMock()
    parent_controller.execute = MagicMock()
    parent_controller.default_experiment_file = "/tmp/default.yml"
    parent_controller.update_experiment_setting = MagicMock(return_value=None)
    parent_controller.configuration_controller = MagicMock()
    parent_controller.waveform_constants_path = "/tmp/waveform.yml"
    parent_controller.acquire_bar_controller = SimpleNamespace(
        is_acquiring=False,
        mode="z-stack",
        launch_popup_window=MagicMock(),
    )

    controller = menus_module.MenuController(view, parent_controller)
    return controller, parent_controller


def test_populate_menu_handles_bindings_separator_and_state(menu_controller, monkeypatch):
    controller, _ = menu_controller
    menu = MagicMock()
    action = MagicMock()
    monkeypatch.setattr(menus_module.platform, "platform", lambda: "Darwin")

    controller.populate_menu(
        {
            menu: {
                "Info Only": ["standard", None, "Ctrl+I", None, None],
                "Run Action": [
                    "standard",
                    action,
                    "Ctrl+R",
                    "<Control-r>",
                    "<Command-r>",
                    "disabled",
                ],
                "add_separator": [None],
            }
        }
    )

    menu.add_separator.assert_called_once()
    menu.add_command.assert_any_call(label="Info Only", accelerator="Ctrl+I")
    menu.add_command.assert_any_call(
        label="Run Action",
        command=action,
        accelerator="Ctrl+R",
    )
    menu.bind_all.assert_called_with("<Command-r>", action)
    menu.entryconfig.assert_called_once_with("Run Action", state="disabled")


def test_toggle_stage_limits_updates_configuration_and_popup(menu_controller):
    controller, parent_controller = menu_controller
    popup_var = DummyVar(True)
    parent_controller.stage_limits_popup_controller = SimpleNamespace(
        view=SimpleNamespace(enable_stage_limits_var=popup_var)
    )

    controller.disable_stage_limits.set(1)
    controller.toggle_stage_limits()
    assert parent_controller.configuration["experiment"]["StageParameters"]["limits"] is False
    assert popup_var.get() is False
    parent_controller.execute.assert_called_with("stage_limits", False)

    controller.disable_stage_limits.set(0)
    controller.toggle_stage_limits()
    assert parent_controller.configuration["experiment"]["StageParameters"]["limits"] is True
    assert popup_var.get() is True
    assert parent_controller.execute.call_args.args == ("stage_limits", True)


def test_popup_camera_map_setting_reuses_existing_controller(menu_controller):
    controller, parent_controller = menu_controller
    parent_controller.camera_map_popup_controller = MagicMock()

    controller.popup_camera_map_setting()

    parent_controller.camera_map_popup_controller.showup.assert_called_once()


def test_popup_camera_map_setting_creates_controller(menu_controller, monkeypatch):
    controller, parent_controller = menu_controller
    popup = MagicMock()
    popup_ctor = Mock(return_value=popup)
    popup_controller = MagicMock()
    popup_controller_ctor = Mock(return_value=popup_controller)
    monkeypatch.setattr(menus_module, "CameraMapSettingPopup", popup_ctor)
    monkeypatch.setattr(
        menus_module,
        "CameraMapSettingPopupController",
        popup_controller_ctor,
    )

    controller.popup_camera_map_setting()

    popup_ctor.assert_called_once_with(controller.view)
    popup_controller_ctor.assert_called_once_with(popup, parent_controller)
    assert parent_controller.camera_map_popup_controller is popup_controller


def test_popup_waveform_setting_reuses_existing_controller(menu_controller):
    controller, parent_controller = menu_controller
    parent_controller.waveform_popup_controller = MagicMock()

    controller.popup_waveform_setting()

    parent_controller.waveform_popup_controller.showup.assert_called_once()


def test_popup_waveform_setting_creates_controller(menu_controller, monkeypatch):
    controller, parent_controller = menu_controller
    popup = MagicMock()
    popup_ctor = Mock(return_value=popup)
    waveform_controller = MagicMock()
    waveform_controller_ctor = Mock(return_value=waveform_controller)
    monkeypatch.setattr(menus_module, "WaveformParameterPopupWindow", popup_ctor)
    monkeypatch.setattr(menus_module, "WaveformPopupController", waveform_controller_ctor)

    controller.popup_waveform_setting()

    popup_ctor.assert_called_once_with(controller.view, parent_controller.configuration_controller)
    waveform_controller_ctor.assert_called_once_with(
        popup,
        parent_controller,
        parent_controller.waveform_constants_path,
    )
    waveform_controller.populate_experiment_values.assert_called_once()
    assert parent_controller.waveform_popup_controller is waveform_controller


def test_popup_camera_setting_creates_controller_and_close_handler(
    menu_controller, monkeypatch
):
    controller, parent_controller = menu_controller
    parent_controller.acquire_bar_controller.is_acquiring = True
    parent_controller.acquire_bar_controller.mode = "live"

    popup = MagicMock()
    popup.popup = MagicMock()
    popup.camera_setting = MagicMock()
    popup_ctor = Mock(return_value=popup)

    camera_setting_controller = MagicMock()
    camera_setting_controller_ctor = Mock(return_value=camera_setting_controller)
    monkeypatch.setattr(menus_module, "CameraSettingPopup", popup_ctor)
    monkeypatch.setattr(
        menus_module, "CameraSettingController", camera_setting_controller_ctor
    )

    show_camera_popup = controller.popup_camera_setting("ScopeA")
    show_camera_popup()

    controller_name = "scopea_camera_setting_controller"
    assert getattr(parent_controller, controller_name) is camera_setting_controller
    camera_setting_controller.populate_experiment_values.assert_called_once()
    popup.popup.protocol.assert_called_once()
    camera_setting_controller.set_mode.assert_called_once_with("live")

    close_callback = popup.popup.protocol.call_args.args[1]
    close_callback()
    camera_setting_controller.update_experiment_values.assert_called_once()
    popup.popup.dismiss.assert_called_once()
    assert not hasattr(parent_controller, controller_name)


def test_popup_camera_setting_reuses_existing_controller(menu_controller):
    controller, parent_controller = menu_controller
    existing_controller = MagicMock()
    existing_controller.popup = SimpleNamespace(popup=MagicMock())
    setattr(parent_controller, "scopea_camera_setting_controller", existing_controller)

    show_camera_popup = controller.popup_camera_setting("ScopeA")
    show_camera_popup()

    existing_controller.popup.popup.deiconify.assert_called_once()
    existing_controller.popup.popup.attributes.assert_called_once_with("-topmost", 1)


def test_install_plugin_warns_for_duplicate_name(menu_controller, monkeypatch):
    controller, _ = menu_controller
    monkeypatch.setattr(menus_module.filedialog, "askdirectory", lambda: "/plugins/demo")
    monkeypatch.setattr(
        menus_module.os.path,
        "exists",
        lambda path: path.endswith("plugin_config.yml"),
    )
    monkeypatch.setattr(menus_module, "get_navigate_path", lambda: "/tmp/navigate-home")

    def fake_load_yaml(path):
        if path.endswith("plugin_config.yml"):
            return {"name": "DemoPlugin"}
        return {"DemoPlugin": "/existing/path"}

    save = Mock()
    warning = Mock()
    monkeypatch.setattr(menus_module, "load_yaml_file", fake_load_yaml)
    monkeypatch.setattr(menus_module, "save_yaml_file", save)
    monkeypatch.setattr(menus_module.messagebox, "showwarning", warning)

    controller.install_plugin()

    save.assert_not_called()
    warning.assert_called_once()


def test_install_plugin_saves_new_plugin(menu_controller, monkeypatch):
    controller, _ = menu_controller
    monkeypatch.setattr(menus_module.filedialog, "askdirectory", lambda: "/plugins/demo")
    monkeypatch.setattr(
        menus_module.os.path,
        "exists",
        lambda path: path.endswith("plugin_config.yml"),
    )
    monkeypatch.setattr(menus_module, "get_navigate_path", lambda: "/tmp/navigate-home")

    def fake_load_yaml(path):
        if path.endswith("plugin_config.yml"):
            return {"name": "DemoPlugin"}
        return None

    save = Mock()
    warning = Mock()
    monkeypatch.setattr(menus_module, "load_yaml_file", fake_load_yaml)
    monkeypatch.setattr(menus_module, "save_yaml_file", save)
    monkeypatch.setattr(menus_module.messagebox, "showwarning", warning)

    controller.install_plugin()

    save.assert_called_once_with(
        os.path.join("/tmp/navigate-home", "config"),
        {"DemoPlugin": "/plugins/demo"},
        "plugins_config.yml",
    )
    warning.assert_called_once()


def test_popup_uninstall_plugin_reuses_and_creates_controller(menu_controller, monkeypatch):
    controller, _ = menu_controller
    controller.uninstall_plugin_controller = MagicMock()
    controller.popup_uninstall_plugin()
    controller.uninstall_plugin_controller.showup.assert_called_once()

    del controller.uninstall_plugin_controller
    uninstall_controller = MagicMock()
    uninstall_controller_ctor = Mock(return_value=uninstall_controller)
    monkeypatch.setattr(
        menus_module, "UninstallPluginController", uninstall_controller_ctor
    )

    controller.popup_uninstall_plugin()

    uninstall_controller_ctor.assert_called_once_with(controller.view, controller)
    assert controller.uninstall_plugin_controller is uninstall_controller
