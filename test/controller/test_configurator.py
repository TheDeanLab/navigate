# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Regression tests for configuration-assistant serialization helpers."""

from navigate.controller import configurator as configurator_module
from navigate.controller.configurator import Configurator, InlineYamlList
from navigate.config.configuration_schema import SettingSpec
from navigate.model.devices.zoom.base import ZoomBase


def test_saved_device_type_uses_manufacturer_and_short_model_name():
    """Saved device types use the module name and omit the category suffix."""
    assert (
        Configurator.saved_device_type(
            "camera", "hamamatsu", "HamamatsuOrcaLightningCamera"
        )
        == "hamamatsu.HamamatsuOrcaLightning"
    )
    assert Configurator.saved_device_type("stage", "asi", "ASIStage") == "asi.ASI"
    assert Configurator.saved_device_type("daq", "ni", "NIDAQ") == "NI"
    assert Configurator.saved_device_type("daq", "asi", "ASIDaq") == "ASI"


def test_resolve_device_type_uses_shared_canonical_hardware_type_rule():
    """Configurator accepts all YAML hardware.type forms handled by preload."""
    assert Configurator.resolve_device_type("camera", "HamamatsuOrca") == (
        "hamamatsu",
        "HamamatsuOrcaCamera",
    )
    assert Configurator.resolve_device_type("camera", "HamamatsuOrcaCamera") == (
        "hamamatsu",
        "HamamatsuOrcaCamera",
    )
    assert Configurator.resolve_device_type("camera", "hamamatsu.HamamatsuOrca") == (
        "hamamatsu",
        "HamamatsuOrcaCamera",
    )
    assert Configurator.resolve_device_type(
        "camera", "hamamatsu.HamamatsuOrcaCamera"
    ) == ("hamamatsu", "HamamatsuOrcaCamera")


def test_resolve_device_type_preserves_deceased_type_repair():
    """Legacy deceased model names still resolve through the shared helper."""
    assert Configurator.resolve_device_type("stage", "Thorlabs") == (
        "thorlabs",
        "KIM001Stage",
    )


def test_resolve_daq_type_uses_database_name_not_class_suffix():
    """DAQ class names resolve but save as configuration_database model names."""
    assert Configurator.resolve_device_type("daq", "asi.ASIDaq") == (
        "asi",
        "ASIDaq",
    )
    assert Configurator.resolve_device_type("daq", "ASIDaq") == (
        "asi",
        "ASIDaq",
    )


def test_laser_control_types_are_qualified_using_onoff_priority():
    """Laser power and on/off types use qualified YAML type identifiers."""
    configurator = Configurator.__new__(Configurator)
    configurator.get_connect_params = lambda *_: []
    configurator.get_configuration_schema = lambda *_: {
        "power/hardware/type": SettingSpec(str, default="NI"),
        "onoff/hardware/type": SettingSpec(str, default="ASI"),
    }

    device = configurator.device_configuration("laser", "ni", "NILaser", {})

    assert device["power"]["hardware"]["type"] == "ni.NI"
    assert device["onoff"]["hardware"]["type"] == "asi.ASI"
    assert device["type"] == "asi.ASI"


def test_qualified_synthetic_laser_type_allows_power_fallback():
    """A qualified Synthetic on/off type still allows a non-synthetic power type."""
    configuration = {
        "power": {"hardware": {"type": "ni.NI"}},
        "onoff": {"hardware": {"type": "synthetic.Synthetic"}},
    }

    assert Configurator.laser_device_type(configuration) == "ni.NI"


def test_qualified_laser_control_types_load_as_editor_choices():
    """Qualified YAML laser types are converted back to the editor's choices."""
    configurator = Configurator.__new__(Configurator)
    configurator.get_connect_params = lambda *_: []
    configurator.get_configuration_schema = lambda *_: {
        "power/hardware/type": SettingSpec(str, default="Synthetic"),
        "onoff/hardware/type": SettingSpec(str, default="ASI"),
    }
    configuration = {
        "power": {"hardware": {"type": "synthetic.Synthetic"}},
        "onoff": {"hardware": {"type": "asi.ASI"}},
    }

    settings = configurator.settings_from_configuration(
        "laser", "asi", "ASILaser", configuration
    )

    assert settings == {
        "power/hardware/type": "Synthetic",
        "onoff/hardware/type": "ASI",
    }


def test_stage_axis_home_and_offset_round_trip():
    """Per-axis home and offset values load from and save to stage settings."""
    configurator = Configurator.__new__(Configurator)
    configurator.get_connect_params = lambda *_: []
    configurator.get_configuration_schema = lambda *_: {
        "axes": SettingSpec(str),
    }
    configuration = {
        "hardware": {"axes": ["x"]},
        "x_min": -100.0,
        "x_max": 100.0,
        "x_home": 0.0,
        "x_offset": 2.5,
    }

    settings = configurator.settings_from_configuration(
        "stage", "asi", "ASIStage", configuration
    )
    device = configurator.device_configuration("stage", "asi", "ASIStage", settings)

    assert settings["x_home"] == 0.0
    assert settings["x_offset"] == 2.5
    assert device["x_home"] == 0.0
    assert device["x_offset"] == 2.5


def test_empty_stage_home_and_offset_are_not_saved():
    """Blank optional stage Home and Offset settings are omitted from YAML."""
    configurator = Configurator.__new__(Configurator)
    configurator.get_connect_params = lambda *_: []
    configurator.get_configuration_schema = lambda *_: {
        "axes": SettingSpec(str),
    }

    device = configurator.device_configuration(
        "stage",
        "asi",
        "ASIStage",
        {
            "axes": "x",
            "x_home": "",
            "x_offset": "",
        },
    )

    assert "x_home" not in device
    assert "x_offset" not in device


def test_optional_numeric_setting_can_be_cleared(monkeypatch):
    """Optional numeric settings use a text variable so an empty value is valid."""

    class StringVariable:
        def __init__(self, master, value):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    monkeypatch.setattr(configurator_module.tk, "StringVar", StringVariable)
    configurator = Configurator.__new__(Configurator)
    configurator.root = object()

    variable = configurator.create_value_variable(SettingSpec(float, default=1), 1.0)
    variable.set("")

    assert variable.get() == ""


def test_cleared_optional_setting_is_not_saved():
    """A cleared optional setting is omitted from the device configuration."""

    class Variable:
        def get(self):
            return ""

    configurator = Configurator.__new__(Configurator)
    configurator.active_device_item_id = "camera-1"
    configurator.device_data = {
        "camera-1": ("camera", "photometrics", "PhotometricsCamera"),
    }
    configurator.device_settings = {"camera-1": {"unitforlinedelay": 1}}
    configurator.value_variables = {"unitforlinedelay": Variable()}
    configurator.collection_rows = {}
    configurator.get_configuration_schema = lambda *_: {
        "unitforlinedelay": SettingSpec(float, default=1),
    }
    configurator.get_connect_params = lambda *_: []

    configurator.store_active_device_settings()

    assert configurator.device_settings["camera-1"] == {"unitforlinedelay": None}
    assert "unitforlinedelay" not in configurator.device_configuration(
        "camera",
        "photometrics",
        "PhotometricsCamera",
        configurator.device_settings["camera-1"],
    )


def test_cleared_optional_ni_daq_laser_port_switcher_is_not_saved():
    """A cleared NI DAQ laser port switcher is absent from saved YAML."""
    configurator = Configurator.__new__(Configurator)
    configurator.get_connect_params = lambda *_: []
    configurator.get_configuration_schema = lambda *_: {
        "laser_port_switcher": SettingSpec(
            str,
            default="PXI6733/port0/line0",
            required=False,
        ),
    }

    device = configurator.device_configuration(
        "daq",
        "ni",
        "NIDAQ",
        {"laser_port_switcher": None},
    )

    assert "laser_port_switcher" not in device


def test_partial_zoom_stage_position_calibration_is_reported():
    """Partially entered calibration rows cannot be silently discarded on save."""

    class Variable:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    configurator = Configurator.__new__(Configurator)
    configurator.active_device_item_id = "zoom-1"
    configurator.device_data = {"zoom-1": ("zoom", "synthetic", "SyntheticZoom")}
    configurator.collection_rows = {
        "stage_positions": [
            {
                "solvent": Variable("BABB"),
                "axis": Variable("f"),
                "zoom": Variable(""),
                "position": Variable(100),
            }
        ]
    }

    assert configurator.invalid_stage_position_calibrations() == [
        "Synthetic, row 1: Zoom",
    ]


def test_zoom_pixel_size_is_positive_float():
    """Pixel size is a positive floating-point Zoom Values setting."""
    pixel_size = ZoomBase.configuration_schema["zoom_values"].item_schema["pixel_size"]

    assert pixel_size.value_type is float
    assert pixel_size.minimum is not None
    assert pixel_size.minimum > 0


def test_invalid_zoom_pixel_size_is_reported():
    """Zero and negative Zoom pixel sizes block configuration saving."""
    configurator = Configurator.__new__(Configurator)
    configurator.microscope_devices = {
        "Microscope-0": [
            (
                "zoom",
                "synthetic",
                "SyntheticZoom",
                {"zoom_values": {"pixel_size": {"1x": 0}}},
            )
        ]
    }

    assert configurator.invalid_zoom_pixel_sizes() == [
        "Microscope-0 / Synthetic (1x)",
    ]


def test_stage_joystick_axes_are_combined_across_stages():
    """Joystick axes from each stage are saved as one combined list."""
    microscope = {}

    Configurator.add_device_to_microscope(
        microscope,
        "stage",
        {
            "hardware": {"type": "asi.ASI"},
            "joystick_axes": InlineYamlList(["x", "y"]),
        },
    )
    Configurator.add_device_to_microscope(
        microscope,
        "stage",
        {
            "hardware": {"type": "synthetic.Synthetic"},
            "joystick_axes": InlineYamlList(["z", "x"]),
        },
    )

    assert microscope["stage"]["joystick_axes"] == ["x", "y", "z"]


def test_stage_coupled_axes_are_combined_with_first_pair_precedence():
    """Stage coupling pairs combine without overwriting an existing pairing."""
    assert Configurator.parse_coupled_axes("x:x1, y:y1") == {
        "x": "x1",
        "y": "y1",
    }
    assert Configurator.parse_coupled_axes("x, x:x") == {}

    microscope = {}

    Configurator.add_device_to_microscope(
        microscope,
        "stage",
        {
            "hardware": {"type": "asi.ASI"},
            "coupled_axes": {"x": "x1"},
        },
    )
    Configurator.add_device_to_microscope(
        microscope,
        "stage",
        {
            "hardware": {"type": "synthetic.Synthetic"},
            "coupled_axes": {"y": "y1"},
        },
    )
    Configurator.add_device_to_microscope(
        microscope,
        "stage",
        {
            "hardware": {"type": "ni.NI"},
            "coupled_axes": {"x1": "x"},
        },
    )

    assert microscope["stage"]["coupled_axes"] == {"x": "x1", "y": "y1"}


def test_stage_shared_axes_load_as_text_values():
    """Shared stage lists and mappings load into their respective text fields."""
    configurator = Configurator.__new__(Configurator)
    configurator.get_connect_params = lambda *_: []
    configurator.get_configuration_schema = lambda *_: {
        "joystick_axes": SettingSpec(str),
        "coupled_axes": SettingSpec(str),
    }

    settings = configurator.settings_from_configuration(
        "stage",
        "asi",
        "ASIStage",
        {
            "hardware": {"axes": ["x", "y"]},
            "joystick_axes": ["x", "y", "z"],
            "coupled_axes": {"x": "x1", "y": "y1", "z": "z1"},
        },
    )

    assert settings["joystick_axes"] == "x, y, z"
    assert settings["coupled_axes"] == "x:x1, y:y1"
