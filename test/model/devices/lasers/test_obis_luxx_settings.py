"""OBIS/LuxX protocol emulators exercise the real APIs and settings adapters."""

from unittest.mock import Mock

import pytest
import serial

from navigate.config.laser import resolve_laser_software_config
from navigate.model.devices.APIs.coherent.ObisLaser import ObisLaser
from navigate.model.devices.APIs.omicron.LuxxLaser import LuxxLaser
from navigate.model.devices.laser.settings.base import LaserControlError, LaserMode
from navigate.model.devices.laser.settings.obis import ObisLaserSettings
from navigate.model.devices.laser.settings.luxx import LuxxLaserSettings
from navigate.model.devices.laser.software import add_software_control
from navigate.model.devices.laser.synthetic import SyntheticLaser
from test.model.devices.lasers.test_laser_software import configuration, make_laser


class LaserSerial:
    """Byte-stream emulator that leaves CRLF tails for the next read."""

    def __init__(self, backend):
        self.backend = backend
        self.commands = []
        self.buffer = b""
        self.closed = False
        self.close_count = 0
        self.override = None
        self.ignore_writes = False
        self.short_write = False
        self.timeout = 0.01
        self.values = (
            {
                "*IDN?": "Coherent OBIS test",
                "SOURCE:POWER:LIMIT:LOW?": "0.0",
                "SOURCE:POWER:LIMIT:HIGH?": "0.200",
                "SOURCE:POWER:LEVEL?": "0.00725",
                "SOURCE:POWER:LEVEL:IMMEDIATE:AMPLITUDE?": "0.05",
                "SOURCE:AM:SOURCE?": "DIGITAL",
                "SOURCE:AM:STATE?": "ON",
            }
            if backend == "OBIS"
            else {
                "GSI": b"488\xa7200",
                "GSN": b"SERIAL-42",
                "GWH": b"100",
                "GMP": b"200",
                "ROM": b"2",
                "GLP": b"400",
                "MDP": b"7.25",
                "GAS": b"0002",
            }
        )

    def reset_input_buffer(self):
        self.buffer = b""

    def write(self, data):
        if self.closed:
            raise serial.SerialException("port closed")
        assert data.endswith(b"\r")
        command = data[:-1].decode("ascii")
        self.commands.append(command)
        if self.short_write:
            return len(data) - 1
        if self.override is not None:
            self.buffer += self.override
            return len(data)
        if self.backend == "OBIS":
            cmd = command.upper()
            if cmd.endswith("?"):
                self.buffer += str(self.values[cmd]).encode("ascii") + b"\r\nOK\r\n"
            else:
                if not self.ignore_writes:
                    if cmd.startswith(("SOURCE:AM:INTERNAL ", "SOURCE:AM:EXTERNAL ")):
                        self.values["SOURCE:AM:SOURCE?"] = cmd.split()[-1]
                    elif cmd.startswith("SOURCE:POWER:LEVEL:IMMEDIATE:AMPLITUDE "):
                        self.values["SOURCE:POWER:LEVEL:IMMEDIATE:AMPLITUDE?"] = (
                            cmd.split()[-1]
                        )
                self.buffer += b"OK\r\n"
        else:
            cmd = command[1:]
            key = cmd[:3]
            if len(cmd) > 3:
                if not self.ignore_writes:
                    if key == "ROM":
                        self.values["ROM"] = cmd[3:].encode("ascii")
                    if key == "SLP":
                        self.values["GLP"] = cmd[3:].encode("ascii")
                value = b">"
            else:
                value = self.values[key]
            self.buffer += b"!" + key.encode("ascii") + value + b"\r"
        return len(data)

    def read_until(self, expected, size):
        index = self.buffer.find(expected)
        length = len(self.buffer) if index < 0 else index + len(expected)
        length = min(length, size)
        result, self.buffer = self.buffer[:length], self.buffer[length:]
        return result

    def close(self):
        self.closed = True
        self.close_count += 1


def adapter(backend, connection=None):
    connection = connection or LaserSerial(backend)
    if backend == "OBIS":
        return (
            ObisLaserSettings(ObisLaser("TEST", timeout=0.01, connection=connection)),
            connection,
        )
    return (
        LuxxLaserSettings(LuxxLaser("TEST", timeout=0.01, connection=connection)),
        connection,
    )


@pytest.fixture(params=["OBIS", "LuxX"])
def device(request):
    settings, connection = adapter(request.param)
    yield settings, connection
    settings.close()


def test_existing_apis_are_instantiable_and_connection_is_read_only(device):
    settings, connection = device
    assert settings.get_power_limits_mw() == (0, 200)
    assert settings.get_status()["emission_enabled"] is True
    assert settings.get_status()["measured_power_mw"] == 7.25
    forbidden = (
        "SOURCE:AM:STATE ",
        "SOURCE:AM:EXTERNAL ",
        "SOURCE:AM:INTERNAL ",
        "SOURCE:POWER:LEVEL:IMMEDIATE:AMPLITUDE ",
        "?LOn",
        "?LOf",
        "?ROM0",
        "?ROM1",
        "?ROM2",
        "?ROM3",
        "?SLP",
        "?SAS",
        "?SAP",
    )
    assert not any(
        command.upper().startswith(tuple(c.upper() for c in forbidden))
        for command in connection.commands
    )
    assert settings.get_status()["simulated"] is False


@pytest.mark.parametrize("mode", list(LaserMode))
def test_obis_modes_are_terminated_acknowledged_and_verified(mode):
    settings, connection = adapter("OBIS")
    settings.set_mode(mode)
    assert settings.get_mode() == mode
    assert all("\n" not in command for command in connection.commands)
    settings.close()


@pytest.mark.parametrize("mode,raw", [(LaserMode.CW, b"2"), (LaserMode.ANALOG, b"3")])
def test_luxx_supported_modes_and_separate_shutter(mode, raw):
    settings, connection = adapter("LuxX")
    assert settings.get_supported_modes() == {LaserMode.CW, LaserMode.ANALOG}
    settings.set_mode(mode)
    assert connection.values["ROM"] == raw
    assert settings.get_mode() == mode
    assert "?LOn" not in connection.commands


@pytest.mark.parametrize("mode", [LaserMode.DIGITAL, LaserMode.MIXED])
def test_luxx_unsupported_modes_never_write(mode):
    settings, connection = adapter("LuxX")
    connection.commands.clear()
    with pytest.raises(LaserControlError, match="supports CW"):
        settings.set_mode(mode)
    assert not connection.commands


def test_obis_converts_watts_and_distinguishes_setpoint_from_measurement():
    settings, connection = adapter("OBIS")
    assert settings.set_power_mw(25.25) == 25.25
    assert (
        float(connection.values["SOURCE:POWER:LEVEL:IMMEDIATE:AMPLITUDE?"]) == 0.02525
    )
    assert settings.get_status()["measured_power_mw"] == 7.25
    assert settings.get_power_setpoint_mw() == 25.25


def test_luxx_quantized_power_readback_is_reported_instead_of_request():
    settings, connection = adapter("LuxX")
    confirmed = settings.set_power_mw(25)
    assert connection.values["GLP"] == b"1FF"
    assert confirmed == 511 * 200 / 4095
    assert confirmed != 25
    assert settings.get_status()["measured_power_mw"] == 7.25


@pytest.mark.parametrize("power", [-1, 201, float("nan"), float("inf")])
def test_invalid_power_never_writes(device, power):
    settings, connection = device
    connection.commands.clear()
    with pytest.raises(LaserControlError):
        settings.set_power_mw(power)
    assert connection.commands == []


def test_analog_power_is_not_overridden_by_serial(device):
    settings, connection = device
    settings.set_mode(LaserMode.ANALOG)
    connection.commands.clear()
    with pytest.raises(LaserControlError):
        settings.set_power_mw(25)
    assert not any(
        c.startswith(("?SLP", "SOURce:POWer:LEVel:IMMediate:AMPLitude "))
        for c in connection.commands
    )


def test_rejected_power_and_modes_do_not_claim_confirmation(device):
    settings, connection = device
    connection.ignore_writes = True
    with pytest.raises(LaserControlError, match="readback"):
        settings.set_power_mw(37)
    with pytest.raises(LaserControlError, match="accept"):
        settings.set_mode(LaserMode.ANALOG)


@pytest.mark.parametrize("reply", [b"", b"partial", b"WRONG\r", b"\xff\r", b"?wrong\r"])
def test_bad_responses_are_bounded_and_late_replies_cannot_recover(device, reply):
    settings, connection = device
    connection.override = reply
    with pytest.raises(LaserControlError):
        settings.get_mode()
    connection.override = None
    previous = len(connection.commands)
    with pytest.raises(LaserControlError, match="Reconnect"):
        settings.get_mode()
    assert len(connection.commands) == previous


def test_partial_writes_poison_the_connection(device):
    settings, connection = device
    connection.short_write = True
    with pytest.raises(LaserControlError, match="Incomplete"):
        settings.set_mode(LaserMode.CW)
    with pytest.raises(LaserControlError, match="Reconnect"):
        settings.get_status()


@pytest.mark.parametrize("backend", ["OBIS", "LuxX"])
def test_constructor_failure_closes_connection(backend):
    connection = LaserSerial(backend)
    connection.override = b""
    with pytest.raises(LaserControlError):
        adapter(backend, connection)
    assert connection.closed
    assert connection.close_count == 1


def test_close_is_idempotent_and_sends_no_emission_commands(device):
    settings, connection = device
    count = len(connection.commands)
    settings.close()
    settings.close()
    assert connection.close_count == 1
    assert len(connection.commands) == count


@pytest.mark.parametrize("power", [0.0, 200.0])
def test_power_endpoints_are_verified_without_clamping(device, power):
    settings, _ = device
    assert settings.set_power_mw(power) == power


@pytest.mark.parametrize(
    "backend,rejection",
    [("OBIS", b"ERR-100\r\n"), ("LuxX", b"!ROMx\r"), ("LuxX", b"!UK\r")],
)
def test_device_rejections_raise_without_losing_transaction_alignment(
    backend, rejection
):
    settings, connection = adapter(backend)
    connection.override = rejection
    with pytest.raises(LaserControlError):
        settings.set_mode(LaserMode.CW)
    connection.override = None
    assert settings.get_mode() in (LaserMode.DIGITAL, LaserMode.CW)


@pytest.mark.parametrize("backend", ["OBIS", "LuxX"])
def test_invalid_limits_close_the_connection(backend):
    connection = LaserSerial(backend)
    if backend == "OBIS":
        connection.values["SOURCE:POWER:LIMIT:HIGH?"] = "nan"
    else:
        connection.values["GMP"] = b"0"
    with pytest.raises(LaserControlError):
        adapter(backend, connection)
    assert connection.closed


def test_obis_constant_current_is_preserved_but_not_used_for_serial_power():
    settings, connection = adapter("OBIS")
    connection.values["SOURCE:AM:SOURCE?"] = "CWC"
    assert settings.get_mode() == LaserMode.CW
    with pytest.raises(LaserControlError, match="CWP"):
        settings.set_power_mw(10)
    assert connection.values["SOURCE:AM:SOURCE?"] == "CWC"
    settings.set_mode(LaserMode.CW)
    assert connection.values["SOURCE:AM:SOURCE?"] == "CWP"
    assert settings.set_power_mw(10) == 10


@pytest.mark.parametrize("backend,baudrate", [("OBIS", 115200), ("LuxX", 500000)])
def test_factory_uses_existing_api_and_backend_defaults(monkeypatch, backend, baudrate):
    connection = LaserSerial(backend)
    factory = Mock(return_value=connection)
    monkeypatch.setattr(
        "navigate.model.devices.APIs.laser_serial.serial.Serial", factory
    )
    laser = make_laser(configuration(backend=backend))
    assert factory.call_args.kwargs["baudrate"] == baudrate
    assert factory.call_args.kwargs["timeout"] == 0.5
    assert factory.call_args.kwargs["write_timeout"] == 0.5
    laser.prepare_acquisition()
    laser.set_power(25)
    assert laser.power_metadata["requested_mw"] == 50
    assert laser.power_metadata["confirmed_setpoint_mw"] == pytest.approx(50, abs=0.05)
    assert laser.power_metadata["measured_power_mw"] == 7.25
    assert laser.power_metadata["verification"] == "readback"
    laser.turn_on()
    laser.external.turn_on.assert_called_once()
    laser.close()


@pytest.mark.parametrize("backend", ["OBIS", "LuxX"])
def test_virtual_devices_and_legacy_configuration_never_open_serial(
    monkeypatch, backend
):
    factory = Mock(side_effect=AssertionError("Unexpected serial connection"))
    monkeypatch.setattr(
        "navigate.model.devices.APIs.laser_serial.serial.Serial", factory
    )
    config = configuration(backend=backend)
    external = SyntheticLaser("scope", None, config, 0)
    snapshot = add_software_control(
        external, is_synthetic=True
    ).advanced_settings_snapshot()
    assert snapshot["simulated"]
    assert snapshot["available_modes"] == (
        ["cw"] if backend == "LuxX" else ["cw", "digital"]
    )
    config["configuration"]["microscopes"]["scope"]["laser"][0].pop("software_control")
    config["configuration"]["microscopes"]["scope"]["laser"][0]["power"].pop("source")
    external = SyntheticLaser("scope", None, config, 0)
    assert add_software_control(external) is external
    factory.assert_not_called()


@pytest.mark.parametrize(
    "backend,baudrate", [("Vortran", 19200), ("OBIS", 115200), ("LuxX", 500000)]
)
def test_default_baudrates_and_explicit_overrides(backend, baudrate):
    entry = configuration(backend=backend)["configuration"]["microscopes"]["scope"][
        "laser"
    ][0]
    assert resolve_laser_software_config(entry).baudrate == baudrate
    entry["software_control"]["baudrate"] = 9600
    assert resolve_laser_software_config(entry).baudrate == 9600


@pytest.mark.parametrize("backend", ["OBIS", "LuxX"])
def test_missing_port_and_conflicting_power_routing_are_rejected(backend):
    entry = configuration(backend=backend)["configuration"]["microscopes"]["scope"][
        "laser"
    ][0]
    entry["software_control"].pop("port")
    with pytest.raises(ValueError, match="serial port"):
        resolve_laser_software_config(entry)
    entry["software_control"]["port"] = "COM3"
    entry["power"]["hardware"]["type"] = "NI"
    with pytest.raises(ValueError, match="no analog output"):
        resolve_laser_software_config(entry)
