from types import SimpleNamespace
from unittest.mock import MagicMock

import navigate.main as main_module


class _FakeRoot:
    def __init__(self):
        self.withdraw = MagicMock()
        self.mainloop = MagicMock()
        self.destroy = MagicMock()


def _evaluation_result():
    return (
        "config.yml",
        "experiment.yml",
        "waveforms.yml",
        "rest.yml",
        "templates.yml",
        "logdir",
        False,
        "gui.yml",
        "positions.yml",
    )


def test_main_uses_controller_branch_and_stops_log_listener(monkeypatch, capsys):
    root = _FakeRoot()
    splash = object()
    args = SimpleNamespace(configurator=False, viewer=False)
    listener = MagicMock()
    controller = MagicMock()
    configurator = MagicMock()

    monkeypatch.setattr(main_module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(main_module.tk, "Tk", lambda: root)
    monkeypatch.setattr(main_module, "SplashScreen", MagicMock(return_value=splash))
    monkeypatch.setattr(
        main_module,
        "create_parser",
        lambda: SimpleNamespace(parse_args=lambda: args),
    )
    monkeypatch.setattr(
        main_module,
        "evaluate_parser_input_arguments",
        lambda parsed_args: _evaluation_result(),
    )
    monkeypatch.setattr(
        main_module, "log_setup", MagicMock(return_value=("queue", listener))
    )
    monkeypatch.setattr(main_module, "Controller", controller)
    monkeypatch.setattr(main_module, "Configurator", configurator)

    main_module.main()

    assert (
        "WARNING: navigate was built to operate on a Windows platform."
        in capsys.readouterr().out
    )
    root.withdraw.assert_called_once_with()
    root.mainloop.assert_called_once_with()
    controller.assert_called_once_with(
        root=root,
        splash_screen=splash,
        configuration_path="config.yml",
        experiment_path="experiment.yml",
        waveform_constants_path="waveforms.yml",
        rest_api_path="rest.yml",
        waveform_templates_path="templates.yml",
        gui_configuration_path="gui.yml",
        multi_positions_path="positions.yml",
        log_queue="queue",
        args=args,
    )
    configurator.assert_not_called()
    listener.stop.assert_called_once_with()


def test_main_uses_configurator_branch(monkeypatch, capsys):
    root = _FakeRoot()
    splash = object()
    args = SimpleNamespace(configurator=True, viewer=False)
    listener = MagicMock()
    controller = MagicMock()
    configurator = MagicMock()

    monkeypatch.setattr(main_module.platform, "system", lambda: "Windows")
    monkeypatch.setattr(main_module.tk, "Tk", lambda: root)
    monkeypatch.setattr(main_module, "SplashScreen", MagicMock(return_value=splash))
    monkeypatch.setattr(
        main_module,
        "create_parser",
        lambda: SimpleNamespace(parse_args=lambda: args),
    )
    monkeypatch.setattr(
        main_module,
        "evaluate_parser_input_arguments",
        lambda parsed_args: _evaluation_result(),
    )
    monkeypatch.setattr(
        main_module, "log_setup", MagicMock(return_value=("queue", listener))
    )
    monkeypatch.setattr(main_module, "Controller", controller)
    monkeypatch.setattr(main_module, "Configurator", configurator)

    main_module.main()

    assert capsys.readouterr().out == ""
    configurator.assert_called_once_with(root, splash)
    controller.assert_not_called()
    listener.stop.assert_called_once_with()


def test_main_cleans_up_when_optional_viewer_is_unavailable(monkeypatch):
    root = _FakeRoot()
    splash = MagicMock()
    splash.destroy.side_effect = RuntimeError("splash window is already closed")
    args = SimpleNamespace(configurator=False, viewer=True)
    listener = MagicMock()

    monkeypatch.setattr(main_module.platform, "system", lambda: "Windows")
    monkeypatch.setattr(main_module.tk, "Tk", lambda: root)
    monkeypatch.setattr(main_module, "SplashScreen", MagicMock(return_value=splash))
    monkeypatch.setattr(
        main_module,
        "create_parser",
        lambda: SimpleNamespace(parse_args=lambda: args),
    )
    monkeypatch.setattr(
        main_module,
        "evaluate_parser_input_arguments",
        lambda parsed_args: _evaluation_result(),
    )
    monkeypatch.setattr(
        main_module, "log_setup", MagicMock(return_value=("queue", listener))
    )
    monkeypatch.setattr(main_module, "_load_volume_viewer", lambda: None)

    main_module.main()

    splash.destroy.assert_called_once_with()
    root.destroy.assert_called_once_with()
    root.mainloop.assert_not_called()
    listener.stop.assert_called_once_with()
