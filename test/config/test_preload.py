# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

from multiprocessing import Manager
from multiprocessing.managers import DictProxy
from pathlib import Path

import pytest
import yaml

from navigate.config.config import load_configs, update_config_dict
from navigate.config.device_schema import canonical_device_type
from navigate.config.preload import PreloadError, preload_configuration
from navigate.config.preload_rules.configuration import _default_reference_value
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


def test_preload_renames_remote_focus_device_without_user_facing_report(
    loaded_configuration,
):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    microscope["remote_focus_device"] = microscope.pop("remote_focus")

    report = preload_configuration(manager, configuration)

    assert "remote_focus" in microscope
    assert "remote_focus_device" not in microscope
    assert not any("remote_focus_device" in change.path for change in report.changes)
    assert any("remote_focus" in change.path for change in report.debug_changes)


def test_preload_adds_synthetic_missing_required_device(loaded_configuration):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    microscope.pop("camera")

    report = preload_configuration(manager, configuration)

    assert microscope["camera"]["hardware"]["type"] == "synthetic.Synthetic"
    assert any(
        change.rule == "missing-required-device" and change.path.endswith(".camera")
        for change in report.changes
    )


def test_preload_generates_unified_laser_hardware(loaded_configuration):
    manager, configuration = loaded_configuration
    laser = configuration["configuration"]["microscopes"]["Mesoscale"]["laser"][0]
    laser["onoff"]["hardware"]["type"] = "ASI"
    laser["onoff"]["hardware"]["channel"] = "output"
    laser["power"]["hardware"]["type"] = "Synthetic"
    laser.pop("hardware", None)

    preload_configuration(manager, configuration)

    assert laser["hardware"]["type"] == "asi.ASI"
    assert laser["hardware"]["channel"] == "output"
    assert laser["hardware"]["wavelength"] == laser["wavelength"]


def test_preload_adds_zoom_hardware_defaults(loaded_configuration):
    manager, configuration = loaded_configuration
    zoom = configuration["configuration"]["microscopes"]["Mesoscale"]["zoom"]
    zoom.pop("hardware", None)

    preload_configuration(manager, configuration)

    assert zoom["hardware"]["type"] == "synthetic.Synthetic"
    assert zoom["hardware"]["servo_id"] == 0


def test_preload_adds_zoom_position_and_pixel_size_defaults(loaded_configuration):
    manager, configuration = loaded_configuration
    zoom = configuration["configuration"]["microscopes"]["Mesoscale"]["zoom"]
    zoom.pop("position", None)
    zoom.pop("pixel_size", None)

    preload_configuration(manager, configuration)

    assert dict(zoom["position"]) == {"N/A": 0}
    assert dict(zoom["pixel_size"]) == {"N/A": 1.0}


def test_preload_adds_missing_zoom_pixel_size_with_warning(loaded_configuration):
    manager, configuration = loaded_configuration
    zoom = configuration["configuration"]["microscopes"]["Mesoscale"]["zoom"]
    update_config_dict(manager, zoom, "position", {"1x": 0, "2x": 100})
    update_config_dict(manager, zoom, "pixel_size", {"1x": 0.5})

    report = preload_configuration(manager, configuration)

    assert zoom["pixel_size"]["2x"] == 1.0
    assert any(
        issue.rule == "zoom-pixel-size-default" and "2x" in issue.path
        for issue in report.issues
    )


def test_preload_removes_empty_zoom_stage_positions(loaded_configuration):
    manager, configuration = loaded_configuration
    zoom = configuration["configuration"]["microscopes"]["Mesoscale"]["zoom"]
    update_config_dict(manager, zoom, "stage_positions", {})

    preload_configuration(manager, configuration)

    assert "stage_positions" not in zoom


def test_preload_normalizes_filter_wheel_shape_and_name(loaded_configuration):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    filter_wheel = microscope["filter_wheel"]
    filter_wheel.pop("name", None)
    filter_wheel["hardware"]["name"] = "Emission Wheel"
    microscope["filter_wheel"] = filter_wheel

    preload_configuration(manager, configuration)

    assert len(microscope["filter_wheel"]) == 1
    assert microscope["filter_wheel"][0]["name"] == "Emission Wheel"


def test_preload_adds_empty_filter_for_synthetic_filter_wheel(loaded_configuration):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    filter_wheel = microscope["filter_wheel"]
    filter_wheel["hardware"]["type"] = "Synthetic"
    filter_wheel.pop("available_filters", None)

    report = preload_configuration(manager, configuration)

    assert dict(microscope["filter_wheel"][0]["available_filters"]) == {"Empty": 0}
    assert any(issue.rule == "filter-wheel-default-filter" for issue in report.issues)


def test_preload_adds_empty_filter_for_synthetic_mode_filter_wheel(
    loaded_configuration,
):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    filter_wheel = microscope["filter_wheel"]
    filter_wheel["hardware"]["type"] = "Sutter"
    update_config_dict(manager, filter_wheel, "available_filters", {})

    report = preload_configuration(manager, configuration, is_synthetic=True)

    assert dict(microscope["filter_wheel"][0]["available_filters"]) == {"Empty": 0}
    assert any(issue.rule == "filter-wheel-default-filter" for issue in report.issues)


def test_preload_raises_for_real_filter_wheel_without_filters(loaded_configuration):
    manager, configuration = loaded_configuration
    filter_wheel = configuration["configuration"]["microscopes"]["Mesoscale"][
        "filter_wheel"
    ]
    filter_wheel["hardware"]["type"] = "Sutter"
    filter_wheel.pop("available_filters", None)

    with pytest.raises(PreloadError) as error:
        preload_configuration(manager, configuration)

    assert any(
        issue.rule == "filter-wheel-missing-filters"
        for issue in error.value.report.issues
    )


def test_preload_raises_for_ni_filter_wheel_without_valid_channel(
    loaded_configuration,
):
    manager, configuration = loaded_configuration
    filter_wheel = configuration["configuration"]["microscopes"]["Mesoscale"][
        "filter_wheel"
    ]
    filter_wheel["hardware"]["type"] = "NI"
    update_config_dict(manager, filter_wheel, "available_filters", {"GFP": 1})

    with pytest.raises(PreloadError) as error:
        preload_configuration(manager, configuration)

    assert any(
        issue.rule == "filter-wheel-invalid-ni-channel"
        for issue in error.value.report.issues
    )


def test_preload_accepts_ni_filter_wheel_valid_channel(loaded_configuration):
    manager, configuration = loaded_configuration
    filter_wheel = configuration["configuration"]["microscopes"]["Mesoscale"][
        "filter_wheel"
    ]
    filter_wheel["hardware"]["type"] = "NI"
    update_config_dict(
        manager, filter_wheel, "available_filters", {"GFP": "PXI6733/port0/line1"}
    )

    report = preload_configuration(manager, configuration)

    assert not any(
        issue.rule == "filter-wheel-invalid-ni-channel" for issue in report.issues
    )


def test_preload_repairs_gui_channel_count_and_defaults(loaded_configuration):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    microscope["camera"]["count"] = 8
    configuration["gui"].pop("channel_settings", None)
    configuration["gui"].pop("remote_focus_waveform", None)

    preload_configuration(manager, configuration)

    assert configuration["gui"]["channel_settings"]["count"] == 8
    assert (
        configuration["gui"]["remote_focus_waveform"]["amplitude_step_size"] == 0.0001
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


def test_preload_adds_synthetic_stage_for_missing_required_axes(
    loaded_configuration,
):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    microscope["stage"]["hardware"][0]["axes"] = ["x", "z"]
    microscope["stage"]["hardware"][0]["axes_mapping"] = ["X", "Z"]

    report = preload_configuration(manager, configuration)

    stage_hardware = microscope["stage"]["hardware"]
    assert len(stage_hardware) == 2
    assert list(stage_hardware[0]["axes"]) == ["x", "z"]
    assert list(stage_hardware[1]["axes"]) == ["y", "f", "theta"]
    assert stage_hardware[1]["type"].lower().startswith("synthetic")
    assert str(stage_hardware[1]["serial_number"]).startswith("stage_")
    assert any(change.rule == "missing-stage-axes" for change in report.changes)


def test_preload_does_not_add_stage_when_required_axes_are_covered(
    loaded_configuration,
):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]

    preload_configuration(manager, configuration)

    assert len(microscope["stage"]["hardware"]) == 1


def test_preload_removes_invalid_stage_coupled_axes_pairs(loaded_configuration):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    microscope["stage"]["hardware"][0]["axes"] = ["x", "y", "z", "theta", "f"]
    update_config_dict(
        manager,
        microscope["stage"],
        "coupled_axes",
        {"x": "y", "z": "missing", "missing": "f"},
    )

    preload_configuration(manager, configuration)

    assert dict(microscope["stage"]["coupled_axes"]) == {"x": "y"}


def test_preload_removes_stage_coupled_axes_when_no_pairs_valid(loaded_configuration):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    update_config_dict(
        manager,
        microscope["stage"],
        "coupled_axes",
        {"missing": "y", "x": "missing"},
    )

    preload_configuration(manager, configuration)

    assert "coupled_axes" not in microscope["stage"]


def test_preload_removes_invalid_stage_joystick_axes(loaded_configuration):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    microscope["stage"]["hardware"][0]["axes"] = ["x", "y", "z"]
    update_config_dict(
        manager,
        microscope["stage"],
        "joystick_axes",
        ["x", "missing", "z"],
    )

    preload_configuration(manager, configuration)

    assert list(microscope["stage"]["joystick_axes"]) == ["x", "z"]


def test_preload_removes_stage_joystick_axes_when_none_valid(loaded_configuration):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    update_config_dict(
        manager,
        microscope["stage"],
        "joystick_axes",
        ["missing", "other"],
    )

    preload_configuration(manager, configuration)

    assert "joystick_axes" not in microscope["stage"]


def test_preload_synthetic_mode_adds_missing_stage_reference_serial_number(
    loaded_configuration,
):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    stage_hardware = microscope["stage"]["hardware"][0]
    stage_hardware["type"] = "ASI"
    stage_hardware.pop("serial_number", None)

    preload_configuration(manager, configuration, is_synthetic=True)

    assert stage_hardware["type"] == "ASI"
    assert stage_hardware["serial_number"].startswith("stage_")


def test_preload_adds_missing_required_devices_after_inheritance(loaded_configuration):
    manager, configuration = loaded_configuration
    microscopes = configuration["configuration"]["microscopes"]
    microscopes["Child (Mesoscale)"] = {}
    microscopes["Mesoscale"].pop("zoom")

    report = preload_configuration(manager, configuration)

    assert "Child" in microscopes
    assert "Child (Mesoscale)" not in microscopes
    assert microscopes["Child"]["zoom"]["hardware"]["type"] == "synthetic.Synthetic"
    assert any(change.path.endswith(".Mesoscale.zoom") for change in report.changes)
    assert any(change.path.endswith(".Child.zoom") for change in report.changes)


def test_preload_does_not_syntheticize_existing_real_type_in_synthetic_mode(
    loaded_configuration,
):
    manager, configuration = loaded_configuration
    camera = configuration["configuration"]["microscopes"]["Mesoscale"]["camera"]
    camera["hardware"]["type"] = "HamamatsuOrca"

    preload_configuration(manager, configuration, is_synthetic=True)

    assert camera["hardware"]["type"] == "hamamatsu.HamamatsuOrca"


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


def test_preload_synthetic_mode_skips_real_schema_validation(
    loaded_configuration, monkeypatch
):
    manager, configuration = loaded_configuration

    def schema(category, manufacturer, model):
        if category == "camera" and manufacturer == "hamamatsu":
            return {"real_required": SettingSpec(str, required=True)}
        return {}

    monkeypatch.setattr(
        "navigate.config.preload_rules.configuration.get_configuration_schema",
        schema,
    )

    report = preload_configuration(manager, configuration, is_synthetic=True)

    assert not report.has_fatal_issues
    assert not any(issue.path.endswith(".real_required") for issue in report.issues)


def test_preload_synthetic_mode_adds_synthetic_schema_defaults_silently(
    loaded_configuration, monkeypatch
):
    manager, configuration = loaded_configuration
    camera = configuration["configuration"]["microscopes"]["Mesoscale"]["camera"]
    camera.pop("synthetic_required", None)

    def schema(category, manufacturer, model):
        if category == "camera" and manufacturer == "synthetic":
            return {
                "synthetic_required": SettingSpec(str, default="present", required=True)
            }
        if category == "camera":
            return {"real_required": SettingSpec(str, required=True)}
        return {}

    monkeypatch.setattr(
        "navigate.config.preload_rules.configuration.get_configuration_schema",
        schema,
    )

    report = preload_configuration(manager, configuration, is_synthetic=True)

    assert camera["synthetic_required"] == "present"
    assert not report.has_fatal_issues
    assert not any(
        change.rule == "schema-required-default" for change in report.changes
    )


@pytest.mark.parametrize(
    "category,raw_type,expected",
    [
        ("camera", "hamamatsu.HamamatsuOrca", "hamamatsu.HamamatsuOrca"),
        ("camera", "hamamatsu.HamamatsuOrcaCamera", "hamamatsu.HamamatsuOrca"),
        ("camera", "HamamatsuOrcaCamera", "hamamatsu.HamamatsuOrca"),
        ("camera", "HamamatsuOrca", "hamamatsu.HamamatsuOrca"),
        ("zoom", "SyntheticZoom", "synthetic.Synthetic"),
        ("zoom", "synthetic", "synthetic.Synthetic"),
        ("galvo", "NIGalvo", "ni.NI"),
    ],
)
def test_canonical_device_type_uses_device_python_file_name(
    category, raw_type, expected
):
    assert canonical_device_type(category, raw_type) == expected


def test_preload_normalizes_device_types_before_reference_check(loaded_configuration):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    microscope["camera"]["hardware"]["type"] = "hamamatsu.HamamatsuOrcaCamera"
    microscope["zoom"]["hardware"]["type"] = "SyntheticZoom"
    microscope["galvo"][0]["hardware"]["type"] = "NIGalvo"

    report = preload_configuration(manager, configuration)

    assert microscope["camera"]["hardware"]["type"] == "hamamatsu.HamamatsuOrca"
    assert microscope["zoom"]["hardware"]["type"] == "synthetic.Synthetic"
    assert microscope["galvo"][0]["hardware"]["type"] == "ni.NI"
    assert any(change.rule == "device-type-normalized" for change in report.changes)


def test_preload_silently_adds_optional_reference_field(
    loaded_configuration, monkeypatch
):
    manager, configuration = loaded_configuration
    zoom = configuration["configuration"]["microscopes"]["Mesoscale"]["zoom"]
    zoom["hardware"]["type"] = "synthetic"
    zoom["hardware"].pop("servo_id", None)

    monkeypatch.setattr(
        "navigate.config.preload_rules.configuration.get_configuration_schema",
        lambda category, manufacturer, model: (
            {"hardware/servo_id": SettingSpec(int, required=False)}
            if category == "zoom"
            else {}
        ),
    )

    report = preload_configuration(manager, configuration)

    assert zoom["hardware"]["servo_id"] == 0
    assert not any(
        change.rule == "device-reference-fields" for change in report.changes
    )
    assert not report.has_fatal_issues


def test_reference_default_adds_unused_zoom_servo_id():
    assert (
        _default_reference_value(
            "zoom", "servo_id", 0, existing_values={0, "1", "not-a-number"}
        )
        == 2
    )


def test_preload_adds_unused_filter_wheel_number(loaded_configuration, monkeypatch):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    first_wheel = microscope["filter_wheel"]
    second_wheel = {
        "hardware": {
            "type": first_wheel["hardware"]["type"],
            "name": "Second Wheel",
        },
        "available_filters": dict(first_wheel["available_filters"]),
        "filter_wheel_delay": first_wheel.get("filter_wheel_delay", 0.03),
    }
    update_config_dict(
        manager,
        microscope,
        "filter_wheel",
        [dict(first_wheel), second_wheel],
    )
    filter_wheels = microscope["filter_wheel"]

    monkeypatch.setattr(
        "navigate.config.preload_rules.configuration.get_configuration_schema",
        lambda category, manufacturer, model: (
            {"hardware/wheel_number": SettingSpec(int, required=False)}
            if category == "filter_wheel"
            else {}
        ),
    )

    preload_configuration(manager, configuration)

    assert (
        filter_wheels[1]["hardware"]["wheel_number"]
        != filter_wheels[0]["hardware"]["wheel_number"]
    )


def test_preload_warns_for_duplicate_device_reference(loaded_configuration):
    manager, configuration = loaded_configuration
    microscope = configuration["configuration"]["microscopes"]["Mesoscale"]
    first_wheel = microscope["filter_wheel"]
    second_wheel = {
        "hardware": {
            "type": first_wheel["hardware"]["type"],
            "wheel_number": first_wheel["hardware"]["wheel_number"],
            "name": "Duplicate Wheel",
        },
        "available_filters": dict(first_wheel["available_filters"]),
        "filter_wheel_delay": first_wheel.get("filter_wheel_delay", 0.03),
    }
    update_config_dict(
        manager,
        microscope,
        "filter_wheel",
        [dict(first_wheel), second_wheel],
    )

    report = preload_configuration(manager, configuration)

    duplicate_issues = [
        issue for issue in report.issues if issue.rule == "duplicate-device-reference"
    ]
    assert duplicate_issues
    assert not duplicate_issues[0].fatal
    assert "only the first one will be loaded" in duplicate_issues[0].message


def test_preload_raises_for_required_reference_field(loaded_configuration, monkeypatch):
    manager, configuration = loaded_configuration
    zoom = configuration["configuration"]["microscopes"]["Mesoscale"]["zoom"]
    zoom["hardware"].pop("servo_id", None)

    monkeypatch.setattr(
        "navigate.config.preload_rules.configuration.get_configuration_schema",
        lambda category, manufacturer, model: (
            {"hardware/servo_id": SettingSpec(int, required=True)}
            if category == "zoom"
            else {}
        ),
    )

    with pytest.raises(PreloadError) as error:
        preload_configuration(manager, configuration)

    assert any(
        issue.rule == "schema-required-missing" for issue in error.value.report.issues
    )


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


def test_preload_ignores_missing_optional_schema_choice(
    loaded_configuration, monkeypatch
):
    manager, configuration = loaded_configuration
    camera = configuration["configuration"]["microscopes"]["Mesoscale"]["camera"]
    camera.pop("optional_choice", None)

    monkeypatch.setattr(
        "navigate.config.preload_rules.configuration.get_configuration_schema",
        lambda category, manufacturer, model: (
            {
                "optional_choice": SettingSpec(
                    str,
                    default="valid",
                    choices=("valid", "other"),
                    required=False,
                )
            }
            if category == "camera"
            else {}
        ),
    )

    report = preload_configuration(manager, configuration)

    assert "optional_choice" not in camera
    assert not any("optional_choice" in issue.path for issue in report.issues)


def test_preload_replaces_invalid_optional_schema_choice_with_default(
    loaded_configuration, monkeypatch
):
    manager, configuration = loaded_configuration
    camera = configuration["configuration"]["microscopes"]["Mesoscale"]["camera"]
    camera["optional_choice"] = "invalid"

    monkeypatch.setattr(
        "navigate.config.preload_rules.configuration.get_configuration_schema",
        lambda category, manufacturer, model: (
            {
                "optional_choice": SettingSpec(
                    str,
                    default="valid",
                    choices=("valid", "other"),
                    required=False,
                )
            }
            if category == "camera"
            else {}
        ),
    )

    report = preload_configuration(manager, configuration)

    assert camera["optional_choice"] == "valid"
    assert any(
        issue.rule == "schema-optional-invalid-default"
        and issue.path.endswith(".optional_choice")
        and not issue.fatal
        for issue in report.issues
    )


def test_preload_removes_invalid_optional_schema_choice_without_default(
    loaded_configuration, monkeypatch
):
    manager, configuration = loaded_configuration
    camera = configuration["configuration"]["microscopes"]["Mesoscale"]["camera"]
    camera["optional_choice"] = "invalid"

    monkeypatch.setattr(
        "navigate.config.preload_rules.configuration.get_configuration_schema",
        lambda category, manufacturer, model: (
            {
                "optional_choice": SettingSpec(
                    str,
                    choices=("valid", "other"),
                    required=False,
                )
            }
            if category == "camera"
            else {}
        ),
    )

    report = preload_configuration(manager, configuration)

    assert "optional_choice" not in camera
    assert any(
        issue.rule == "schema-optional-invalid-removed"
        and issue.path.endswith(".optional_choice")
        and not issue.fatal
        for issue in report.issues
    )


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
