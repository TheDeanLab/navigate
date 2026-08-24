# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

from multiprocessing import Manager
from multiprocessing.managers import DictProxy
from pathlib import Path

import pytest
import yaml

from navigate.config.config import load_configs
from navigate.config.preload import PreloadError, preload_configuration
from navigate.model.devices.configuration_schema import SettingSpec


CONFIG_DIR = Path(__file__).resolve().parents[2] / "src" / "navigate" / "config"


@pytest.fixture
def loaded_configuration():
    with Manager() as manager:
        configuration = load_configs(
            manager,
            configuration=CONFIG_DIR / "configuration.yaml",
            experiment=CONFIG_DIR / "experiment.yml",
            waveform_constants=CONFIG_DIR / "waveform_constants.yml",
            rest_api_config=CONFIG_DIR / "rest_api_config.yml",
            waveform_templates=CONFIG_DIR / "waveform_templates.yml",
            gui=CONFIG_DIR / "gui_configuration.yml",
        )
        yield manager, configuration


def test_preload_keeps_loaded_sections_as_shared_dicts(loaded_configuration):
    manager, configuration = loaded_configuration

    preload_configuration(manager, configuration)

    for name in (
        "configuration",
        "experiment",
        "waveform_constants",
        "rest_api_config",
        "waveform_templates",
        "gui",
    ):
        assert isinstance(configuration[name], DictProxy)


def test_preload_renames_lasers_without_user_facing_report(loaded_configuration):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    microscope["lasers"] = microscope.pop("laser")

    report = preload_configuration(manager, configuration)

    assert "laser" in microscope
    assert "lasers" not in microscope
    assert not any("lasers" in change.path for change in report.changes)
    assert any("laser" in change.path for change in report.debug_changes)


def test_preload_adds_synthetic_missing_required_device(loaded_configuration):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    microscope.pop("camera")

    report = preload_configuration(manager, configuration)

    assert microscope["camera"]["hardware"]["type"].lower() == "synthetic"
    assert any(
        change.rule == "missing-required-device" and change.path.endswith(".camera")
        for change in report.changes
    )


def test_preload_preserves_stage_axes_as_lists(loaded_configuration):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]

    preload_configuration(manager, configuration)

    stage_hardware = microscope["stage"]["hardware"][0]
    assert list(stage_hardware["axes"]) == ["x", "y", "z", "theta", "f"]


@pytest.mark.parametrize(
    "axes_yaml",
    [
        "['x', 'y', 'z']",
        '["x", "y", "z"]',
        "[x, y, z]",
    ],
)
def test_preload_accepts_yaml_stage_axes_list_forms(loaded_configuration, axes_yaml):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    stage_hardware = microscope["stage"]["hardware"][0]
    stage_hardware["axes"] = yaml.load(axes_yaml, Loader=yaml.FullLoader)
    stage_hardware["axes_mapping"] = ["X", "Y", "Z"]

    preload_configuration(manager, configuration)

    assert list(stage_hardware["axes"]) == ["x", "y", "z"]


def test_preload_synthetic_stage_axes_are_lists(loaded_configuration):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    microscope.pop("stage")

    preload_configuration(manager, configuration)

    stage_hardware = microscope["stage"]["hardware"][0]
    assert list(stage_hardware["axes"]) == ["x", "y", "z", "theta", "f"]


def test_preload_adds_missing_required_devices_after_inheritance(loaded_configuration):
    manager, configuration = loaded_configuration
    microscopes = configuration["configuration"]["microscopes"]
    microscopes["Child (Mesoscale)"] = {}
    microscopes["Mesoscale"].pop("zoom")

    report = preload_configuration(manager, configuration)

    assert "Child" in microscopes
    assert "Child (Mesoscale)" not in microscopes
    assert microscopes["Child"]["zoom"]["hardware"]["type"].lower() == "synthetic"
    assert any(change.path.endswith(".Mesoscale.zoom") for change in report.changes)
    assert any(change.path.endswith(".Child.zoom") for change in report.changes)


def test_preload_does_not_change_existing_real_type_in_synthetic_mode(
    loaded_configuration,
):
    manager, configuration = loaded_configuration
    camera = configuration["configuration"]["microscopes"]["Mesoscale"]["camera"]
    camera["hardware"]["type"] = "HamamatsuOrca"

    preload_configuration(manager, configuration, is_synthetic=True)

    assert camera["hardware"]["type"] == "HamamatsuOrca"


def test_preload_does_not_change_laser_control_types_in_synthetic_mode(
    loaded_configuration,
):
    manager, configuration = loaded_configuration
    laser = configuration["configuration"]["microscopes"]["Mesoscale"]["laser"][0]
    laser["onoff"]["hardware"]["type"] = "RealOnOffController"
    laser["power"]["hardware"]["type"] = "RealPowerController"

    preload_configuration(manager, configuration, is_synthetic=True)

    assert laser["onoff"]["hardware"]["type"] == "RealOnOffController"
    assert laser["power"]["hardware"]["type"] == "RealPowerController"


def test_preload_adds_required_schema_default(loaded_configuration, monkeypatch):
    manager, configuration = loaded_configuration
    camera = configuration["configuration"]["microscopes"]["Mesoscale"]["camera"]
    camera.pop("required_default", None)

    monkeypatch.setattr(
        "navigate.config.preload_rules.configuration.get_configuration_schema",
        lambda category, manufacturer, model: (
            {"required_default": SettingSpec(str, default="present", required=True)}
            if category == "camera"
            else {}
        ),
    )

    report = preload_configuration(manager, configuration)

    assert camera["required_default"] == "present"
    assert any(change.rule == "schema-required-default" for change in report.changes)


def test_preload_raises_for_required_schema_value_without_default(
    loaded_configuration, monkeypatch
):
    manager, configuration = loaded_configuration

    monkeypatch.setattr(
        "navigate.config.preload_rules.configuration.get_configuration_schema",
        lambda category, manufacturer, model: (
            {"missing_required": SettingSpec(str, required=True)}
            if category == "camera"
            else {}
        ),
    )

    with pytest.raises(PreloadError) as error:
        preload_configuration(manager, configuration)

    assert error.value.report.has_fatal_issues
    assert any(
        issue.rule == "schema-required-missing" for issue in error.value.report.issues
    )


def test_preload_validates_multi_positions(loaded_configuration):
    manager, configuration = loaded_configuration
    positions = [
        ["X", "Y", "Z"],
        [1, 2, 3],
        ["bad", 2, 3],
    ]

    preload_configuration(manager, configuration, multi_positions=positions)

    assert configuration["multi_positions"] == [["X", "Y", "Z"], [1, 2, 3]]
