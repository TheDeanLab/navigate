"""Idle laser settings, acquisition compatibility and failure handling."""

from queue import Queue
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from navigate.model.model import Model
from navigate.model.microscope import Microscope
from navigate.model.devices.laser.settings.base import LaserControlError, LaserMode
from test.model.devices.lasers.test_laser_software import configuration, make_laser
from test.model.devices.lasers.test_laser_settings import StradusSerial
from navigate.model.devices.laser.settings.vortran import VortranLaserSettings


@pytest.fixture
def model():
    model = Model.__new__(Model)
    model.configuration = configuration()
    model.configuration["experiment"] = {
        "MicroscopeState": {
            "microscope_name": "scope",
            "channels": {"channel_1": {"laser_index": 0, "laser_power": 25}},
        }
    }
    model.is_acquiring = False
    model.virtual_microscopes = {}
    scope = Microscope.__new__(Microscope)
    scope.microscope_name = "scope"
    scope.laser = {"488": make_laser()}
    scope.laser_wavelength = [488]
    scope.shutter = Mock()
    scope.camera = SimpleNamespace(is_acquiring=False)
    scope.output_event_queue = Queue()
    model.microscopes = {"scope": scope}
    return model


def request(model, **kwargs):
    return model.laser_advanced_settings(
        {"microscope": "scope", "laser": "488", "request_id": 1, **kwargs}
    )


def test_refresh_is_read_only_and_reports_truthful_simulation(model):
    laser = model.microscopes["scope"].laser["488"]
    laser.settings.set_mode = Mock()
    result = request(model)
    assert result["error"] is None
    assert result["connection"] == "simulated"
    assert result["mode"] == "digital"
    assert result["available_modes"] == ["cw", "digital"]
    assert result["minimum_mw"] == 0
    assert result["maximum_mw"] == 100
    assert result["percent_reference_mw"] == 100
    assert result["setpoint_mw"] == 0
    assert result["measured_power_mw"] is None
    assert result["emission_enabled"] is None
    assert result["acquisition_mode"] == "preserve"
    laser.settings.set_mode.assert_not_called()
    laser.external.turn_on.assert_not_called()
    laser.external.turn_off.assert_not_called()
    model.microscopes["scope"].shutter.close_shutter.assert_not_called()


@pytest.mark.parametrize("mode", list(LaserMode))
def test_external_power_supports_all_modes_without_changing_routing(model, mode):
    laser = make_laser(configuration(source="hardware"))
    model.microscopes["scope"].laser["488"] = laser
    result = request(model, identity=request(model)["identity"], mode=mode.value)
    assert result["error"] is None
    assert result["mode"] == mode.value
    assert result["available_modes"] == [m.value for m in LaserMode]
    if mode in (LaserMode.ANALOG, LaserMode.MIXED):
        assert result["setpoint_mw"] is None
    laser.set_power(45)
    laser.external.set_power.assert_called_once_with(45)
    laser.prepare_acquisition()
    metadata = model.microscopes["scope"].describe_laser_power(
        {"laser_index": 0, "laser_power": 45}
    )
    assert metadata["mode"] == mode.value
    assert metadata["verification"] == "unverified_external"
    assert metadata["confirmed_setpoint_mw"] is None


def test_session_mode_overrides_startup_policy_and_reconfirms_power(model):
    config = configuration()
    config["configuration"]["microscopes"]["scope"]["laser"][0]["software_control"][
        "mode"
    ] = "digital"
    laser = make_laser(config)
    scope = model.microscopes["scope"]
    scope.laser["488"] = laser
    laser.prepare_acquisition()
    laser.set_power(25)
    previous = laser.settings.set_mode

    def apply(mode):
        scope.shutter.close_shutter.assert_called_once()
        laser.external.turn_off.assert_called_once()
        previous(mode)

    laser.settings.set_mode = Mock(side_effect=apply)
    result = request(model, identity=request(model)["identity"], mode="cw")
    assert result["error"] is None
    assert result["mode"] == result["acquisition_mode"] == "cw"
    assert laser.power_metadata is None
    with pytest.raises(LaserControlError, match="confirmed"):
        laser.turn_on()
    event, record = scope.output_event_queue.get_nowait()
    assert event == "laser_power"
    assert record["verification"] == "pending"
    assert record["confirmed_setpoint_mw"] is None
    assert record["requested_percent"] == 25
    scope.shutter.open_shutter.assert_not_called()
    laser.settings.set_mode = previous
    laser.prepare_acquisition()
    laser.set_power(25)
    assert laser.power_metadata["mode"] == "cw"
    assert laser.power_metadata["power_kind"] == "cw_setpoint"
    assert laser.options.mode == "digital"
    assert laser.device_config["software_control"]["mode"] == "digital"


@pytest.mark.parametrize("mode", ["analog", "mixed", "invalid"])
def test_invalid_mode_never_reaches_hardware(model, mode):
    laser = model.microscopes["scope"].laser["488"]
    identity = request(model)["identity"]
    laser.settings.set_mode = Mock()
    result = request(model, identity=identity, mode=mode)
    assert result["error"]
    laser.settings.set_mode.assert_not_called()
    model.microscopes["scope"].shutter.close_shutter.assert_not_called()


@pytest.mark.parametrize("busy", ["model", "camera", "virtual"])
def test_acquisition_blocks_reads_and_writes_without_any_laser_io(model, busy):
    laser = model.microscopes["scope"].laser["488"]
    identity = request(model)["identity"]
    laser.settings = Mock(side_effect=AssertionError("unexpected hardware I/O"))
    if busy == "model":
        model.is_acquiring = True
    elif busy == "camera":
        model.microscopes["scope"].camera.is_acquiring = True
    else:
        model.virtual_microscopes["virtual"] = SimpleNamespace(
            camera=SimpleNamespace(is_acquiring=True)
        )
    for values in ({}, {"identity": identity, "mode": "cw"}):
        assert request(model, **values)["connection"] == "busy"
    assert laser.settings.mock_calls == []


def test_connection_replacement_rejects_old_write(model):
    identity = request(model)["identity"]
    laser = make_laser()
    laser.settings.set_mode = Mock()
    model.microscopes["scope"].laser["488"] = laser
    assert "connection changed" in request(model, identity=identity, mode="cw")["error"]
    laser.settings.set_mode.assert_not_called()


def test_failed_partial_mode_change_blocks_capture_until_successfully_repaired(model):
    laser = model.microscopes["scope"].laser["488"]
    identity = request(model)["identity"]
    previous = laser.settings.set_mode

    def fail(mode):
        previous(LaserMode.ANALOG)
        raise LaserControlError("readback mismatch")

    laser.settings.set_mode = fail
    result = request(model, identity=identity, mode="cw")
    assert result["error"] == "readback mismatch"
    assert result["mode"] == "analog"
    with pytest.raises(LaserControlError, match="Apply and confirm"):
        laser.prepare_acquisition()
    assert request(model)["mode_error"] == "readback mismatch"
    laser.settings.set_mode = previous
    assert request(model, identity=identity, mode="digital")["error"] is None
    laser.prepare_acquisition()
    laser.set_power(25)
    assert laser.power_metadata["confirmed_setpoint_mw"] == 25


def test_failed_connection_returns_no_stale_readbacks(model):
    laser = model.microscopes["scope"].laser["488"]
    assert request(model)["setpoint_mw"] == 0
    laser.settings.close()
    result = request(model)
    assert result["connection"] == "unavailable"
    assert "closed" in result["error"]
    assert "setpoint_mw" not in result


def test_legacy_and_missing_lasers_have_no_settings_io(model):
    scope = model.microscopes["scope"]
    external = scope.laser["488"].external
    scope.laser["488"] = external
    assert request(model)["connection"] == "not_configured"
    assert request(model, mode="cw")["connection"] == "not_configured"
    external.turn_off.assert_not_called()
    assert request(model, laser="640")["connection"] == "unavailable"
    assert request(model, microscope="missing")["connection"] == "unavailable"


def test_shutter_failure_prevents_mode_commands(model):
    scope = model.microscopes["scope"]
    laser = scope.laser["488"]
    identity = request(model)["identity"]
    scope.shutter.close_shutter.side_effect = RuntimeError("shutter failed")
    laser.settings.set_mode = Mock()
    result = request(model, identity=identity, mode="cw")
    assert "shutter failed" in result["error"]
    laser.settings.set_mode.assert_not_called()


@pytest.mark.parametrize("mode", list(LaserMode))
def test_vortran_popup_readbacks_and_modes_use_adapter_protocol(model, mode):
    scope = model.microscopes["scope"]
    laser = make_laser(configuration(source="hardware"))
    serial = StradusSerial()
    serial.values["LP"] = "4.2"
    laser.settings = VortranLaserSettings(serial)
    scope.laser["488"] = laser
    serial.commands.clear()
    result = request(model)
    assert result["connection"] == "connected", result.get("error")
    assert result["device_identity"] == "Stradus test"
    assert result["maximum_mw"] == 100
    assert result["setpoint_mw"] == 10
    assert result["measured_power_mw"] == 4.2
    assert result["emission_enabled"] is True
    assert all(command.startswith("?") for command in serial.commands)
    result = request(model, identity=result["identity"], mode=mode.value)
    assert result["error"] is None
    assert result["mode"] == mode.value
    assert not any(
        command.startswith(("LE=", "LP=", "PP=")) for command in serial.commands
    )
    laser.external.turn_on.assert_not_called()
    scope.shutter.open_shutter.assert_not_called()


def test_unconfirmed_mode_never_becomes_session_policy(model):
    laser = model.microscopes["scope"].laser["488"]
    laser.settings.set_mode = Mock()  # Device silently ignores the request.
    result = request(model, identity=request(model)["identity"], mode="cw")
    assert "did not accept" in result["error"]
    assert result["acquisition_mode"] == "preserve"
    with pytest.raises(LaserControlError, match="Apply and confirm"):
        laser.prepare_acquisition()


@pytest.mark.parametrize(
    "backend,modes",
    [("OBIS", ["cw", "digital", "analog", "mixed"]), ("LuxX", ["cw", "analog"])],
)
def test_new_adapters_use_existing_popup_transaction_path(model, backend, modes):
    from test.model.devices.lasers.test_obis_luxx_settings import adapter

    scope = model.microscopes["scope"]
    laser = make_laser(configuration(source="hardware"))
    laser.settings, connection = adapter(backend)
    scope.laser["488"] = laser
    result = request(model)
    assert result["error"] is None
    assert result["connection"] == "connected", result.get("error")
    assert result["available_modes"] == modes
    assert result["maximum_mw"] == 200
    assert result["measured_power_mw"] == 7.25
    result = request(model, identity=result["identity"], mode="analog")
    assert result["error"] is None
    assert result["mode"] == "analog"
    scope.shutter.close_shutter.assert_called_once()
    laser.external.turn_off.assert_called_once()
    laser.prepare_acquisition()
    laser.set_power(25)
    laser.external.set_power.assert_called_once_with(25)
    assert not any(command.startswith("?LOn") for command in connection.commands)


def test_standby_luxx_is_connected_and_can_be_configured_without_enabling_emission(
    model,
):
    from test.model.devices.lasers.test_obis_luxx_settings import adapter

    laser = model.microscopes["scope"].laser["488"]
    laser.settings, connection = adapter("LuxX")
    connection.values["ROM"] = b"0"
    connection.values["GAS"] = b"0000"
    result = request(model)
    assert result["connection"] == "connected", result.get("error")
    assert result["mode"] is None
    assert "Standby" in result["mode_warning"]
    assert result["available_modes"] == ["cw"]
    with pytest.raises(LaserControlError, match="Standby"):
        laser.prepare_acquisition()
    result = request(model, identity=result["identity"], mode="cw")
    assert result["error"] is None
    assert result["mode"] == "cw"
    assert result["emission_enabled"] is False
    laser.prepare_acquisition()
    laser.set_power(25)
    assert laser.power_metadata["mode"] == "cw"
    assert laser.power_metadata["emission_enabled"] is False
    assert "?LOn" not in connection.commands
