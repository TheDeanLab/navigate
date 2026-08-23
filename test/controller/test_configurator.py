# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Regression tests for configuration-assistant serialization helpers."""

from navigate.controller.configurator import Configurator
from navigate.model.devices.configuration_schema import SettingSpec


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
