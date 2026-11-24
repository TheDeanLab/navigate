"""Composition, routing, and backward-compatibility tests."""

from copy import deepcopy
from unittest.mock import Mock

import pytest

from navigate.config.laser import resolve_laser_software_config
from navigate.model.devices.laser.settings.base import LaserControlError, LaserMode
from navigate.model.devices.laser.settings.synthetic import SyntheticLaserSettings
from navigate.model.devices.laser.software import (
    SoftwareControlledLaser,
    add_software_control,
)
from navigate.model.devices.laser.synthetic import SyntheticLaser


def configuration(source="serial", backend="Synthetic"):
    return {
        "configuration": {
            "microscopes": {
                "scope": {
                    "laser": [
                        {
                            "wavelength": 488,
                            "power": {
                                "source": source,
                                "hardware": {"type": "Synthetic"},
                            },
                            "onoff": {
                                "hardware": {
                                    "type": "NI",
                                    "channel": "Dev1/port0/line0",
                                }
                            },
                            "software_control": {"type": backend, "port": "COM7"},
                        }
                    ]
                }
            }
        }
    }


def make_laser(config=None):
    config = configuration() if config is None else config
    external = SyntheticLaser("scope", None, config, 0)
    external.set_power = Mock(wraps=external.set_power)
    external.turn_on = Mock()
    external.turn_off = Mock()
    external.close = Mock()
    return add_software_control(external)


@pytest.mark.parametrize(
    "backend,timeout",
    [("Vortran", 2.0), ("OBIS", 0.5), ("LuxX", 0.5), ("Synthetic", 0.5)],
)
def test_backend_timeout_defaults_and_explicit_overrides(backend, timeout):
    entry = configuration(backend=backend)["configuration"]["microscopes"]["scope"][
        "laser"
    ][0]
    assert resolve_laser_software_config(entry).timeout == timeout
    entry["software_control"]["timeout"] = None
    assert resolve_laser_software_config(entry).timeout == timeout
    entry["software_control"]["timeout"] = 0.75
    assert resolve_laser_software_config(entry).timeout == 0.75


@pytest.mark.parametrize("software", [None, {}, {"type": None}, {"type": "None"}])
def test_legacy_configuration_never_creates_adapter(software, monkeypatch):
    config = configuration()
    entry = config["configuration"]["microscopes"]["scope"]["laser"][0]
    entry["power"].pop("source")
    entry["software_control"] = software
    original = deepcopy(config)
    external = SyntheticLaser("scope", None, config, 0)
    connect = Mock(side_effect=AssertionError("legacy configuration opened serial"))
    monkeypatch.setattr(
        "navigate.model.devices.laser.settings.vortran.VortranLaserSettings.connect",
        connect,
    )
    assert add_software_control(external) is external
    assert config == original
    connect.assert_not_called()


def test_serial_percentage_reference_and_unchanged_gating():
    config = configuration()
    config["configuration"]["microscopes"]["scope"]["laser"][0]["power"][
        "percent_reference_mw"
    ] = 80
    laser = make_laser(config)
    laser.prepare_acquisition()
    laser.settings.set_power_mw = Mock(wraps=laser.settings.set_power_mw)
    laser.set_power(25.5)
    assert laser.power_metadata["confirmed_setpoint_mw"] == 20.4
    assert laser.power_metadata["percent_reference_mw"] == 80
    laser.turn_on()
    laser.turn_off()
    laser.set_power(25.5)
    laser.settings.set_power_mw.assert_called_once_with(20.4)
    assert laser.external.set_power.call_count == 2
    laser.external.set_power.assert_called_with(25.5)
    laser.external.turn_on.assert_called_once()
    laser.external.turn_off.assert_called_once()
    assert laser.settings.get_power_setpoint_mw() == 20.4


def test_new_acquisition_reconfirms_identical_power():
    laser = make_laser()
    laser.prepare_acquisition()
    laser.set_power(25)
    laser.settings.set_power_mw = Mock(wraps=laser.settings.set_power_mw)
    laser.prepare_acquisition()
    laser.set_power(25)
    laser.settings.set_power_mw.assert_called_once_with(25)


def test_two_channel_powers_on_one_laser_are_applied_on_each_switch():
    laser = make_laser()
    laser.prepare_acquisition()
    for power in (10, 40, 10):
        laser.set_power(power)
        assert laser.settings.get_power_setpoint_mw() == power


def test_preserve_mode_does_not_reconfigure_laser():
    laser = make_laser()
    laser.settings.set_mode = Mock()
    laser.prepare_acquisition()
    laser.settings.set_mode.assert_not_called()


def test_real_vortran_bench_uses_serial_with_synthetic_gate(monkeypatch):
    from test.model.devices.lasers.test_laser_settings import StradusSerial
    from navigate.model.devices.laser.settings.vortran import VortranLaserSettings

    config = configuration(backend="Vortran")
    entry = config["configuration"]["microscopes"]["scope"]["laser"][0]
    entry["onoff"]["hardware"]["type"] = "Synthetic"
    entry["power"]["percent_reference_mw"] = 10
    entry["software_control"]["bench_mode"] = True
    adapter = VortranLaserSettings(StradusSerial())
    connect = Mock(return_value=adapter)
    monkeypatch.setattr(VortranLaserSettings, "connect", connect)
    laser = make_laser(config)
    connect.assert_called_once()
    assert laser.settings is adapter
    laser.prepare_acquisition()
    laser.set_power(100)
    assert laser.power_metadata["confirmed_setpoint_mw"] == 10
    assert laser.power_metadata["bench_mode"] is True
    assert laser.advanced_settings_snapshot()["bench_mode"] is True
    laser.close()


@pytest.mark.parametrize(
    "bench,gate,source",
    [
        (False, "Synthetic", "serial"),
        (True, "NI", "serial"),
        (True, "Synthetic", "hardware"),
        ("false", "Synthetic", "serial"),
    ],
)
def test_invalid_bench_configurations_are_rejected(bench, gate, source):
    entry = configuration(source=source, backend="Vortran")["configuration"][
        "microscopes"
    ]["scope"]["laser"][0]
    entry["software_control"]["bench_mode"] = bench
    entry["onoff"]["hardware"]["type"] = gate
    with pytest.raises(ValueError):
        resolve_laser_software_config(entry)


def test_obis_cw_requires_explicit_bench_mode(monkeypatch):
    config = configuration(backend="OBIS")
    entry = config["configuration"]["microscopes"]["scope"]["laser"][0]
    entry["software_control"]["mode"] = "cw"
    with pytest.raises(ValueError, match="OBIS CW"):
        resolve_laser_software_config(entry)
    entry["software_control"]["mode"] = "preserve"
    external = SyntheticLaser("scope", None, config, 0)
    laser = add_software_control(external, is_synthetic=True)
    laser.settings.set_mode(LaserMode.CW)
    with pytest.raises(LaserControlError, match="OBIS requires digital"):
        laser.prepare_acquisition()
    entry["software_control"]["bench_mode"] = True
    entry["onoff"]["hardware"]["type"] = "Synthetic"
    external = SyntheticLaser("scope", None, config, 0)
    laser = add_software_control(external, is_synthetic=True)
    laser.settings.set_mode(LaserMode.CW)
    laser.prepare_acquisition()
    assert LaserMode.CW in laser.available_modes()


def test_failed_update_invalidates_cached_confirmation_and_gate():
    laser = make_laser()
    laser.prepare_acquisition()
    laser.set_power(10)
    laser.settings.set_power_mw = Mock(side_effect=LaserControlError("disconnected"))
    with pytest.raises(LaserControlError, match="disconnected"):
        laser.set_power(30)
    assert laser.power_metadata is None
    with pytest.raises(LaserControlError, match="confirmed"):
        laser.turn_on()
    laser.external.turn_on.assert_not_called()


def test_analog_mode_rejects_serial_power():
    laser = make_laser()
    laser.settings.set_mode(LaserMode.ANALOG)
    with pytest.raises(LaserControlError, match="CW or digital"):
        laser.prepare_acquisition()


def test_hardware_power_source_keeps_existing_set_power():
    laser = make_laser(configuration(source="hardware"))
    laser.set_power(37)
    laser.external.set_power.assert_called_once_with(37)
    assert laser.settings.get_power_setpoint_mw() == 0


def test_synthetic_mode_never_opens_configured_vortran(monkeypatch):
    config = configuration(backend="Vortran")
    external = SyntheticLaser("scope", None, config, 0)
    connect = Mock(side_effect=AssertionError("simulation accessed hardware"))
    monkeypatch.setattr(
        "navigate.model.devices.laser.settings.vortran.VortranLaserSettings.connect",
        connect,
    )
    laser = add_software_control(external, is_synthetic=True)
    assert isinstance(laser.settings, SyntheticLaserSettings)
    connect.assert_not_called()


def test_adapter_connection_error_closes_external(monkeypatch):
    external = SyntheticLaser("scope", None, configuration(backend="Vortran"), 0)
    external.close = Mock()
    monkeypatch.setattr(
        "navigate.model.devices.laser.settings.vortran.VortranLaserSettings.connect",
        Mock(side_effect=OSError("no port")),
    )
    with pytest.raises(OSError):
        add_software_control(external)
    external.close.assert_called_once()


def test_close_releases_both_connections_once():
    laser = make_laser()
    laser.settings.close = Mock()
    laser.close()
    laser.close()
    laser.settings.close.assert_called_once()
    laser.external.close.assert_called_once()


def test_serial_gate_refuses_unprepared_power():
    laser = make_laser()
    with pytest.raises(LaserControlError, match="Prepare"):
        laser.set_power(20)
    with pytest.raises(LaserControlError, match="confirmed"):
        laser.turn_on()


def test_start_device_composes_optional_control_for_plain_yaml_lists():
    from navigate.model.device_startup_functions import start_device

    config = configuration()
    config["configuration"]["microscopes"]["scope"]["laser"][0]["hardware"] = {
        "type": "Synthetic"
    }
    laser = start_device("scope", config, "laser", 0, is_synthetic=True)
    assert isinstance(laser, SoftwareControlledLaser)
    laser.prepare_acquisition()
    laser.set_power(0)
    assert laser.power_metadata["confirmed_setpoint_mw"] == 0


@pytest.mark.parametrize("invalid", [-1, 101, float("nan"), "invalid"])
def test_invalid_new_request_invalidates_old_confirmation(invalid):
    laser = make_laser()
    laser.prepare_acquisition()
    laser.set_power(10)
    with pytest.raises(LaserControlError):
        laser.set_power(invalid)
    assert laser.power_metadata is None
    with pytest.raises(LaserControlError):
        laser.turn_on()


def test_mode_changes_cannot_produce_incorrect_power_metadata():
    laser = make_laser()
    laser.prepare_acquisition()
    laser.set_power(10)
    laser.settings.set_mode(LaserMode.CW)
    with pytest.raises(LaserControlError, match="mode changed"):
        laser.set_power(20)
    assert laser.power_metadata is None


def test_virtual_devices_honors_a_real_lasers_larger_power_reference(monkeypatch):
    config = configuration(backend="Vortran")
    config["configuration"]["microscopes"]["scope"]["laser"][0]["power"][
        "percent_reference_mw"
    ] = 250
    external = SyntheticLaser("scope", None, config, 0)
    connect = Mock(side_effect=AssertionError("simulation accessed hardware"))
    monkeypatch.setattr(
        "navigate.model.devices.laser.settings.vortran.VortranLaserSettings.connect",
        connect,
    )
    laser = add_software_control(external, is_synthetic=True)
    laser.prepare_acquisition()
    laser.set_power(100)
    assert laser.power_metadata["confirmed_setpoint_mw"] == 250
    assert laser.power_metadata["simulated"] is True
    connect.assert_not_called()


@pytest.mark.parametrize(
    "gate", ["NI", "ni.NI", "ni.NILaser", "ASI", "asi.ASI", "asi.ASILaser"]
)
def test_serial_config_accepts_standard_device_type_aliases(gate):
    config = configuration(backend="Vortran")
    entry = config["configuration"]["microscopes"]["scope"]["laser"][0]
    entry["power"]["hardware"]["type"] = "synthetic.Synthetic"
    entry["onoff"]["hardware"]["type"] = gate
    assert resolve_laser_software_config(entry).power_source == "serial"


def test_explicit_cw_mode_normalizes_constant_current_before_serial_power():
    from navigate.model.devices.laser.settings.vortran import VortranLaserSettings
    from test.model.devices.lasers.test_laser_settings import StradusSerial

    config = configuration()
    config["configuration"]["microscopes"]["scope"]["laser"][0]["software_control"][
        "mode"
    ] = "cw"
    laser = make_laser(config)
    connection = StradusSerial()
    connection.values.update(PUL="0", C="1")
    laser.settings = VortranLaserSettings(connection)
    laser.prepare_acquisition()
    laser.set_power(20)
    assert connection.values["C"] == "0"
    assert laser.power_metadata["confirmed_setpoint_mw"] == 20
