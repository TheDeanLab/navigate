import pytest

from navigate.tools.main_functions import create_parser, evaluate_parser_input_arguments


def test_create_parser_and_evaluate_apply_all_cli_overrides(tmp_path, monkeypatch):
    defaults = (
        "default_config_path",
        "default_experiment_path",
        "default_waveform_constants_path",
        "default_rest_api_path",
        "default_waveform_templates_path",
        "default_gui_configuration_path",
        "default_multi_positions_path",
    )
    monkeypatch.setattr(
        "navigate.tools.main_functions.get_configuration_paths", lambda: defaults
    )

    config_file = tmp_path / "configuration.yml"
    experiment_file = tmp_path / "experiment.yml"
    waveform_constants_file = tmp_path / "waveform_constants.yml"
    rest_api_file = tmp_path / "rest_api.yml"
    waveform_templates_file = tmp_path / "waveform_templates.yml"
    gui_config_file = tmp_path / "gui_configuration.yml"
    multi_positions_file = tmp_path / "multi_positions.yml"
    logging_config = tmp_path / "logging.yml"

    for file_path in [
        config_file,
        experiment_file,
        waveform_constants_file,
        rest_api_file,
        waveform_templates_file,
        gui_config_file,
        multi_positions_file,
        logging_config,
    ]:
        file_path.write_text("test")

    parser = create_parser()
    args = parser.parse_args(
        [
            "--configurator",
            "--config-file",
            str(config_file),
            "--experiment-file",
            str(experiment_file),
            "--waveform-constants-file",
            str(waveform_constants_file),
            "--rest-api-file",
            str(rest_api_file),
            "--waveform-templates-file",
            str(waveform_templates_file),
            "--gui-config-file",
            str(gui_config_file),
            "--multi-positions-file",
            str(multi_positions_file),
            "--logging-config",
            str(logging_config),
        ]
    )

    assert evaluate_parser_input_arguments(args) == (
        config_file,
        experiment_file,
        waveform_constants_file,
        rest_api_file,
        waveform_templates_file,
        logging_config,
        True,
        gui_config_file,
        multi_positions_file,
    )


def test_evaluate_parser_input_arguments_uses_defaults_when_no_overrides(monkeypatch):
    defaults = (
        "default_config_path",
        "default_experiment_path",
        "default_waveform_constants_path",
        "default_rest_api_path",
        "default_waveform_templates_path",
        "default_gui_configuration_path",
        "default_multi_positions_path",
    )
    monkeypatch.setattr(
        "navigate.tools.main_functions.get_configuration_paths", lambda: defaults
    )

    args = create_parser().parse_args([])

    assert evaluate_parser_input_arguments(args) == (
        "default_config_path",
        "default_experiment_path",
        "default_waveform_constants_path",
        "default_rest_api_path",
        "default_waveform_templates_path",
        None,
        False,
        "default_gui_configuration_path",
        "default_multi_positions_path",
    )


def test_evaluate_parser_input_arguments_rejects_missing_waveform_constants_file(
    tmp_path, monkeypatch
):
    defaults = (
        "default_config_path",
        "default_experiment_path",
        "default_waveform_constants_path",
        "default_rest_api_path",
        "default_waveform_templates_path",
        "default_gui_configuration_path",
        "default_multi_positions_path",
    )
    monkeypatch.setattr(
        "navigate.tools.main_functions.get_configuration_paths", lambda: defaults
    )

    missing_file = tmp_path / "missing-waveforms.yml"
    args = create_parser().parse_args(["--waveform-constants-file", str(missing_file)])

    with pytest.raises(
        AssertionError,
        match=f"waveform_constants_file Path {missing_file} not valid",
    ):
        evaluate_parser_input_arguments(args)
