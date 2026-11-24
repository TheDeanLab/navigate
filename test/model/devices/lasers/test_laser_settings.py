"""Contract and RS232 transcript tests; these do not validate physical lasers."""

from collections import deque
from unittest.mock import Mock

import pytest
import serial

from navigate.model.devices.laser.settings.base import (
    LaserControlError,
    LaserMode,
    LaserSettingsBase,
)
from navigate.model.devices.laser.settings.synthetic import SyntheticLaserSettings
from navigate.model.devices.laser.settings.vortran import VortranLaserSettings


class StradusSerial:
    """Small command-level emulator with configurable rejected writes."""

    timeout = 0.01

    def __init__(self):
        self.values = {
            "MAXP": "100",
            "LI": "Stradus test",
            "PUL": "1",
            "EPC": "0",
            "LE": "1",
            "C": "0",
            "LPS": "10.0",
            "LP": "0.0",
            "PP": "10.0",
            "ECHO": "1",
            "PROMPT": "1",
        }
        self.commands = []
        self.replies = deque()
        self.rejected = set()
        self.response_override = None
        self.closed = False

    def reset_input_buffer(self):
        self.replies.clear()

    def write(self, data):
        command = data.decode("ascii").strip()
        self.commands.append(command)
        if command.startswith("?"):
            key = command[1:]
        else:
            key, value = command.split("=")
            requires_power_control = (key == "PUL" and value == "1") or key in (
                "LP",
                "PP",
            )
            if key not in self.rejected and not (
                requires_power_control and self.values["C"] != "0"
            ):
                self.values[key] = value
                if key == "PP":
                    self.values[key] = str(int(float(value)))
                if key == "LP":
                    self.values["LPS"] = value
        response = f"{key}={self.values[key]}\r\n".encode("ascii")
        if self.response_override is not None:
            response = self.response_override
        self.replies.extend([b"\r\n", response])

    def read_until(self, expected, size):
        return self.replies.popleft() if self.replies else b""

    def close(self):
        self.closed = True


@pytest.fixture
def vortran():
    connection = StradusSerial()
    adapter = VortranLaserSettings(connection)
    connection.commands.clear()
    return adapter, connection


def test_abc_rejects_missing_interface():
    class Incomplete(LaserSettingsBase):
        pass

    with pytest.raises(TypeError, match="abstract"):
        Incomplete()


@pytest.mark.parametrize("mode", list(LaserMode))
def test_synthetic_modes_and_no_invented_measurement(mode):
    laser = SyntheticLaserSettings(120)
    laser.set_mode(mode)
    assert laser.get_mode() == mode
    assert laser.get_power_limits_mw() == (0, 120)
    assert laser.get_status()["measured_power_mw"] is None
    assert laser.get_status()["simulated"] is True
    if mode in (LaserMode.CW, LaserMode.DIGITAL):
        assert laser.set_power_mw(30.5) == 30.5
        assert laser.get_power_setpoint_mw() == 30.5
    else:
        with pytest.raises(LaserControlError, match="analog"):
            laser.set_power_mw(30)


@pytest.mark.parametrize("power", [-1, 101, float("inf"), float("nan")])
def test_synthetic_invalid_power_preserves_setting(power):
    laser = SyntheticLaserSettings()
    laser.set_power_mw(20)
    with pytest.raises(LaserControlError):
        laser.set_power_mw(power)
    assert laser.get_power_setpoint_mw() == 20


def test_synthetic_close_is_idempotent():
    laser = SyntheticLaserSettings()
    laser.close()
    laser.close()
    with pytest.raises(LaserControlError, match="closed"):
        laser.get_mode()


def test_vortran_connection_only_sets_protocol_options():
    connection = StradusSerial()
    laser = VortranLaserSettings(connection)
    assert connection.commands == ["ECHO=0", "PROMPT=0", "?MAXP", "?LI"]
    laser.close()
    assert connection.closed


def test_vortran_connect_uses_bounded_read_and_write_timeouts(monkeypatch):
    connection = StradusSerial()
    factory = Mock(return_value=connection)
    monkeypatch.setattr(serial, "Serial", factory)
    VortranLaserSettings.connect("COM7")
    assert factory.call_args.kwargs["port"] == "COM7"
    assert factory.call_args.kwargs["baudrate"] == 19200
    assert factory.call_args.kwargs["timeout"] == 2.0
    assert factory.call_args.kwargs["write_timeout"] == 2.0


def test_vortran_accepts_recorded_firmware_startup_frames():
    """Firmware 3.2.0 leaves a status prompt ahead of PROMPT=0's reply."""

    class RecordedSerial(StradusSerial):
        def write(self, data):
            command = data.decode("ascii").strip()
            self.commands.append(command)
            self.replies.extend(
                {
                    "ECHO=0": [b"ECHO=0\r\r\n", b"ECHO=0\r\n"],
                    "PROMPT=0": [b"Stradus:0> \r\n", b"PROMPT=0\r\n"],
                    "?MAXP": [b"\r\n", b"?MAXP=250.0\r\n"],
                    "?LI": [b"\r\n", b"?LI=VL07261L02, 12805, 488nm, 250mW, C\r\n"],
                }[command]
            )

    laser = VortranLaserSettings(RecordedSerial())
    assert laser.get_power_limits_mw() == (0, 250)
    assert laser._identity == "VL07261L02, 12805, 488nm, 250mW, C"


@pytest.mark.parametrize("response", [b"Stradus:17> ?LE=0\r\n", b"Stradus:0> LE=0\r\n"])
def test_vortran_prompt_is_not_mistaken_for_command_reply(vortran, response):
    laser, connection = vortran
    connection.response_override = response
    assert laser._flag("?LE") is False


@pytest.mark.parametrize(
    "response", [b"Stradus:bad> LE=0\r\n", b"Stradus:0> EPC=0\r\n"]
)
def test_vortran_prompt_handling_preserves_response_validation(vortran, response):
    laser, connection = vortran
    connection.response_override = response
    with pytest.raises(LaserControlError, match="Unexpected"):
        laser._flag("?LE")


@pytest.mark.parametrize(
    "mode,analog,digital",
    [
        (LaserMode.CW, "0", "0"),
        (LaserMode.DIGITAL, "0", "1"),
        (LaserMode.ANALOG, "1", "0"),
        (LaserMode.MIXED, "1", "1"),
    ],
)
def test_vortran_mode_mapping_and_readback(vortran, mode, analog, digital):
    laser, connection = vortran
    connection.values["C"] = "1"
    laser.set_mode(mode)
    assert laser.get_mode() == mode
    assert connection.values["EPC"] == analog
    assert connection.values["PUL"] == digital
    assert connection.values["C"] == "0"
    assert not any(
        command.startswith(("LE=", "DELAY=", "?FC")) for command in connection.commands
    )


def test_vortran_rejected_mode_raises(vortran):
    laser, connection = vortran
    connection.rejected.add("EPC")
    with pytest.raises(LaserControlError, match="did not accept"):
        laser.set_mode(LaserMode.MIXED)


@pytest.mark.parametrize("previous,requested", [(0.1, 0), (9.9, 10), (10.1, 10)])
def test_vortran_rejected_adjacent_cw_setpoint_is_not_confirmed(
    vortran, previous, requested
):
    laser, connection = vortran
    laser.set_mode(LaserMode.CW)
    connection.values["LPS"] = str(previous)
    connection.rejected.add("LP")
    with pytest.raises(LaserControlError, match="readback"):
        laser.set_power_mw(requested)
    assert laser.get_power_setpoint_mw() == previous


def test_vortran_rejected_power_control_mode_does_not_report_success(vortran):
    laser, connection = vortran
    connection.values["C"] = "1"
    connection.rejected.add("C")
    with pytest.raises(LaserControlError, match="did not accept"):
        laser.set_mode(LaserMode.DIGITAL)


@pytest.mark.parametrize("mode", [LaserMode.CW, LaserMode.DIGITAL])
def test_vortran_current_control_rejects_power_without_writing(vortran, mode):
    laser, connection = vortran
    laser.set_mode(mode)
    connection.values["C"] = "1"
    connection.commands.clear()
    with pytest.raises(LaserControlError, match="constant-power"):
        laser.set_power_mw(5)
    assert not any("=" in command for command in connection.commands)


@pytest.mark.parametrize(
    "mode,command", [(LaserMode.CW, "LP"), (LaserMode.DIGITAL, "PP")]
)
@pytest.mark.parametrize("power,expected", [(0, 0), (23.26, 23.3), (100, 100)])
def test_vortran_writes_only_the_correct_power_register(
    vortran, mode, command, power, expected
):
    laser, connection = vortran
    laser.set_mode(mode)
    if mode == LaserMode.DIGITAL:
        expected = round(power)
    connection.commands.clear()
    assert laser.set_power_mw(power) == expected
    writes = [value for value in connection.commands if "=" in value]
    assert writes == [f"{command}={expected:.1f}"]


@pytest.mark.parametrize("power,expected", [(0.1, 0), (0.5, 0), (2.3, 2), (2.9, 3)])
def test_vortran_pulse_power_reports_whole_mw_quantization(vortran, power, expected):
    laser, connection = vortran
    assert laser.set_power_mw(power) == expected
    assert connection.values["PP"] == str(expected)


@pytest.mark.parametrize(
    "mode,maximum,expected",
    [(LaserMode.DIGITAL, 99.9, 99), (LaserMode.CW, 99.99, 99.9)],
)
def test_vortran_power_quantization_never_exceeds_maximum(
    vortran, mode, maximum, expected
):
    laser, connection = vortran
    laser._maximum_mw = maximum
    laser.set_mode(mode)
    assert laser.set_power_mw(maximum) == expected


def test_vortran_rejected_zero_cw_power_does_not_claim_zero_output(vortran):
    laser, connection = vortran
    laser.set_mode(LaserMode.CW)
    connection.rejected.add("LP")
    with pytest.raises(LaserControlError, match="does not match"):
        laser.set_power_mw(0)
    assert laser.get_power_setpoint_mw() == 10
    assert connection.values["LE"] == "1"


@pytest.mark.parametrize("power", [-1, 100.1, float("nan"), float("inf")])
def test_vortran_rejects_invalid_power_before_writing(vortran, power):
    laser, connection = vortran
    with pytest.raises(LaserControlError):
        laser.set_power_mw(power)
    assert not connection.commands


def test_vortran_rejected_power_never_reports_success(vortran):
    laser, connection = vortran
    connection.rejected.add("PP")
    with pytest.raises(LaserControlError, match="does not match"):
        laser.set_power_mw(25)


@pytest.mark.parametrize(
    "flag,value,message", [("LE", "0", "Enable"), ("EPC", "1", "analog")]
)
def test_vortran_does_not_enable_emission_or_override_external_power(
    vortran, flag, value, message
):
    laser, connection = vortran
    connection.values[flag] = value
    with pytest.raises(LaserControlError, match=message):
        laser.set_power_mw(25)
    assert not any("=" in command for command in connection.commands)


@pytest.mark.parametrize(
    "response", [b"", b"PP=20", b"OTHER=20\r\n", b"PP=nan\r\n", b"PP=bad\r\n"]
)
def test_vortran_bad_or_missing_replies_fail_closed(vortran, response):
    laser, connection = vortran
    connection.response_override = response
    with pytest.raises(LaserControlError):
        laser.set_power_mw(20)


def test_vortran_init_failure_closes_connection():
    connection = StradusSerial()
    connection.values["MAXP"] = "nan"
    with pytest.raises(LaserControlError):
        VortranLaserSettings(connection)
    assert connection.closed


def test_vortran_status_does_not_clear_faults(vortran):
    laser, connection = vortran
    status = laser.get_status()
    assert status["measured_power_mw"] == 0
    assert status["identity"] == "Stradus test"
    assert connection.commands == ["?LE", "?LP"]


def test_timeout_does_not_allow_a_late_reply_to_confirm_a_later_command(vortran):
    laser, connection = vortran
    connection.response_override = b""
    with pytest.raises(LaserControlError):
        laser.set_power_mw(20)
    connection.response_override = None
    connection.replies.append(b"PP=20.0\r\n")
    with pytest.raises(LaserControlError, match="Reconnect"):
        laser.set_power_mw(20)
