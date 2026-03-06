# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only.

from multiprocessing import Manager
from pathlib import Path

from navigate.config.config import (
    load_configs,
    verify_configuration,
    verify_experiment_config,
)


def _configuration_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    return root / "src" / "navigate" / "config" / "configuration.yaml"


def test_missing_experiment_file_generates_defaults(tmp_path):
    configuration_path = _configuration_path()
    experiment_path = tmp_path / "experiment.yml"

    with Manager() as manager:
        configuration = load_configs(
            manager,
            configuration=configuration_path,
            experiment=experiment_path,
        )
        verify_configuration(manager, configuration)
        verify_experiment_config(manager, configuration)

        experiment = configuration["experiment"]
        assert "Saving" in experiment
        assert "MicroscopeState" in experiment
        assert "StageParameters" in experiment
        assert "channel_1" in experiment["MicroscopeState"]["channels"]
        assert "z" in experiment["StageParameters"]
        assert "f" in experiment["StageParameters"]


def test_invalid_experiment_file_is_backed_up_and_recovered(tmp_path):
    configuration_path = _configuration_path()
    experiment_path = tmp_path / "experiment.yml"
    experiment_path.write_text("invalid: [", encoding="utf-8")

    with Manager() as manager:
        configuration = load_configs(
            manager,
            configuration=configuration_path,
            experiment=experiment_path,
        )
        verify_configuration(manager, configuration)
        verify_experiment_config(manager, configuration)

        backups = list(tmp_path.glob("experiment.invalid.*.yml"))
        assert len(backups) == 1
        assert experiment_path.exists() is False
        assert "MicroscopeState" in configuration["experiment"]
