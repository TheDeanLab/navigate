# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Standard Library Imports
from unittest.mock import patch

import pytest

# Local Imports
from navigate.model.devices.pump.tecan import XCaliburPump
from navigate.model.utils.exceptions import UserVisibleException


class FakeSerial:
    def __init__(self, port="FAKE", baudrate=9600, timeout=0.5):
        self.commands = []
        self.is_open = True
        self.last_command = None
        self.last_read_n = None
        self.command_responses = {}
        self.write_exception = None
        self.read_exception = None

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def write(self, data: bytes):
        if self.write_exception:
            raise self.write_exception

        self.last_command = data.decode("ascii").strip()
        self.commands.append(data)

    def read(self, n: int) -> bytes:
        if self.read_exception:
            raise self.read_exception

        self.last_read_n = n

        if self.last_command in self.command_responses:
            return self.command_responses[self.last_command]

        return b"/00"


@pytest.fixture
def fake_pump():
    min_speed_code = 2
    max_speed_code = 19

    fake_serial = FakeSerial()

    return XCaliburPump(
        microscope_name="TestPump",
        device_connection=fake_serial,
        configuration={
            "min_speed_code": min_speed_code,
            "max_speed_code": max_speed_code,
            "fine_positioning": False,
        },
    )


@patch("navigate.model.devices.pump.tecan.Serial")
def test_connect_uses_serial_at_module_import_boundary(mock_serial_class):
    fake_serial = FakeSerial()
    mock_serial_class.return_value = fake_serial

    serial_connection = XCaliburPump.connect(port="FAKE", baudrate=9600, timeout=0.5)

    assert serial_connection is fake_serial
    mock_serial_class.assert_called_once_with(port="FAKE", baudrate=9600, timeout=0.5)


def test_initialize_pump_success(fake_pump):
    fake_pump.serial.command_responses["ZR"] = b"/00"

    fake_pump.initialize_pump()

    assert fake_pump.serial.commands[-1] == b"ZR\r"


def test_initialize_pump_error(fake_pump):
    fake_pump.serial.command_responses["ZR"] = b"/01"

    with pytest.raises(UserVisibleException, match="Pump error /1: Initialization error"):
        fake_pump.initialize_pump()

    assert fake_pump.serial.commands[-1] == b"ZR\r"


def test_send_command_success_returns_encoded_bytes(fake_pump):
    sent = fake_pump.send_command("ZR")

    assert sent == b"ZR\r"
    assert fake_pump.serial.commands[-1] == b"ZR\r"


def test_send_command_raises_if_serial_is_none():
    pump = XCaliburPump(
        microscope_name="TestPump",
        device_connection=FakeSerial(),
        configuration={},
    )
    pump.serial = None

    with pytest.raises(UserVisibleException, match="Serial object is None"):
        pump.send_command("ZR")


def test_send_command_raises_if_serial_port_not_open(fake_pump):
    fake_pump.serial.is_open = False

    with pytest.raises(UserVisibleException, match="Serial port not open"):
        fake_pump.send_command("ZR")


def test_send_command_wraps_write_exception(fake_pump):
    fake_pump.serial.write_exception = RuntimeError("write failed")

    with pytest.raises(
        UserVisibleException,
        match=r"Error sending command 'ZR': write failed",
    ):
        fake_pump.send_command("ZR")


def test_read_response_success_decodes_and_tracks_expected_byte_count(fake_pump):
    fake_pump.serial.command_responses["ZR"] = b"/00  "
    fake_pump.send_command("ZR")

    response = fake_pump.read_response(expected_bytes=7)

    assert response == "/00"
    assert fake_pump.serial.last_read_n == 7


def test_read_response_raises_if_serial_is_none():
    pump = XCaliburPump(
        microscope_name="TestPump",
        device_connection=FakeSerial(),
        configuration={},
    )
    pump.serial = None

    with pytest.raises(UserVisibleException, match="Serial object is None"):
        pump.read_response()


def test_read_response_raises_if_serial_port_not_open(fake_pump):
    fake_pump.serial.is_open = False

    with pytest.raises(UserVisibleException, match="Serial port not open"):
        fake_pump.read_response()


def test_read_response_wraps_empty_response(fake_pump):
    fake_pump.serial.command_responses["ZR"] = b""
    fake_pump.send_command("ZR")

    with pytest.raises(
        UserVisibleException,
        match="Error during read: .*No response received",
    ):
        fake_pump.read_response()


def test_read_response_wraps_decode_error(fake_pump):
    fake_pump.serial.command_responses["ZR"] = b"\xff"
    fake_pump.send_command("ZR")

    with pytest.raises(UserVisibleException, match="Error during read"):
        fake_pump.read_response()


def test_read_response_wraps_serial_read_exception(fake_pump):
    fake_pump.serial.read_exception = TimeoutError("timed out")

    with pytest.raises(UserVisibleException, match="Error during read: timed out"):
        fake_pump.read_response()


def test_parse_response_success_returns_zero(fake_pump):
    assert fake_pump.parse_response("/00") == "0"


def test_parse_response_raises_for_missing_start_character(fake_pump):
    with pytest.raises(UserVisibleException, match="Malformed response"):
        fake_pump.parse_response("00")


def test_parse_response_raises_for_incomplete_response(fake_pump):
    with pytest.raises(UserVisibleException, match="Incomplete response"):
        fake_pump.parse_response("/0")


def test_parse_response_raises_for_known_error_code(fake_pump):
    with pytest.raises(
        UserVisibleException,
        match="Pump error /3: Invalid operand - bad parameter value",
    ):
        fake_pump.parse_response("/03")


def test_parse_response_raises_for_unknown_error_code(fake_pump):
    with pytest.raises(UserVisibleException, match="Pump error /X: Unknown error code: X"):
        fake_pump.parse_response("/0X")


def test_disconnect_closes_open_serial_connection(fake_pump):
    assert fake_pump.serial.is_open is True

    fake_pump.disconnect()

    assert fake_pump.serial.is_open is False


def test_disconnect_noop_if_serial_already_closed(fake_pump):
    fake_pump.serial.is_open = False

    fake_pump.disconnect()

    assert fake_pump.serial.is_open is False


def test_disconnect_noop_if_serial_is_none(fake_pump):
    fake_pump.serial = None

    fake_pump.disconnect()


def test_get_status_sends_query_and_returns_raw_response(fake_pump):
    fake_pump.serial.command_responses["?"] = b"/0A "

    response = fake_pump.get_status()

    assert response == "/0A"
    assert fake_pump.serial.commands[-1] == b"?\r"


def test_move_absolute_accepts_mode_specific_max_values(fake_pump):
    fake_pump.fine_positioning = False
    fake_pump.serial.command_responses["A3000"] = b"/00"
    fake_pump.move_absolute(3000)
    assert fake_pump.serial.commands[-1] == b"A3000\r"

    fake_pump.fine_positioning = True
    fake_pump.serial.command_responses["A24000"] = b"/00"
    fake_pump.move_absolute(24000)
    assert fake_pump.serial.commands[-1] == b"A24000\r"


@pytest.mark.parametrize(
    "fine_positioning,position",
    [
        (False, -1),
        (False, 3001),
        (True, 24001),
    ],
)
def test_move_absolute_out_of_bounds_raises(fake_pump, fine_positioning, position):
    fake_pump.fine_positioning = fine_positioning

    with pytest.raises(UserVisibleException, match="out of bounds"):
        fake_pump.move_absolute(position)


@pytest.mark.parametrize("steps", [50, -7, 0])
def test_move_relative_sends_command(fake_pump, steps):
    fake_pump.move_relative(steps)

    assert fake_pump.serial.commands[-1] == f"M{steps}\r".encode()


def test_move_relative_rejected_by_pump_raises(fake_pump):
    fake_pump.serial.command_responses["M-1"] = b"/09"

    with pytest.raises(UserVisibleException, match="Pump error /9: Plunger overload"):
        fake_pump.move_relative(-1)


@pytest.mark.parametrize("speed", [2, 19])
def test_set_speed_accepts_configured_min_and_max(fake_pump, speed):
    fake_pump.set_speed(speed)

    assert fake_pump.serial.commands[-1] == f"S{speed}\r".encode()


@pytest.mark.parametrize("speed", [1, 20])
def test_set_speed_rejects_out_of_bounds_codes(fake_pump, speed):
    with pytest.raises(UserVisibleException, match=r"Speed code .* out of bounds \(2-19\)"):
        fake_pump.set_speed(speed)


def test_set_speed_command_rejected_by_pump(fake_pump):
    valid_speed = fake_pump.max_speed_code - 1
    fake_pump.serial.command_responses[f"S{valid_speed}"] = b"/03"

    with pytest.raises(
        UserVisibleException,
        match="Pump error /3: Invalid operand - bad parameter value",
    ):
        fake_pump.set_speed(valid_speed)


@pytest.mark.parametrize(
    "method_name,command",
    [
        ("valve_input", "I"),
        ("valve_output", "O"),
        ("valve_bypass", "B"),
        ("valve_extra", "E"),
    ],
)
def test_valve_commands_send_expected_command(fake_pump, method_name, command):
    getattr(fake_pump, method_name)()

    assert fake_pump.serial.commands[-1] == f"{command}\r".encode()


@pytest.mark.parametrize(
    "method_name,command",
    [
        ("valve_input", "I"),
        ("valve_output", "O"),
        ("valve_bypass", "B"),
        ("valve_extra", "E"),
    ],
)
def test_valve_commands_propagate_pump_errors(fake_pump, method_name, command):
    fake_pump.serial.command_responses[command] = b"/01"

    with pytest.raises(UserVisibleException, match="Pump error /1: Initialization error"):
        getattr(fake_pump, method_name)()


def test_set_fine_positioning_mode_toggle_success(fake_pump):
    fake_pump.serial.command_responses["N1"] = b"/00"
    fake_pump.serial.command_responses["N0"] = b"/00"
    fake_pump.serial.command_responses["R"] = b"/00"

    fake_pump.set_fine_positioning_mode(True)
    assert fake_pump.fine_positioning is True
    assert fake_pump.serial.commands[-2:] == [b"N1\r", b"R\r"]

    fake_pump.set_fine_positioning_mode(False)
    assert fake_pump.fine_positioning is False
    assert fake_pump.serial.commands[-2:] == [b"N0\r", b"R\r"]


def test_set_fine_positioning_mode_failure_on_load_preserves_state_and_skips_apply(fake_pump):
    fake_pump.fine_positioning = False
    fake_pump.serial.command_responses["N1"] = b"/03"

    with pytest.raises(
        UserVisibleException,
        match="Pump error /3: Invalid operand - bad parameter value",
    ):
        fake_pump.set_fine_positioning_mode(True)

    assert fake_pump.fine_positioning is False
    assert fake_pump.serial.commands == [b"N1\r"]


def test_set_fine_positioning_mode_failure_on_apply_preserves_previous_state(fake_pump):
    fake_pump.fine_positioning = True
    fake_pump.serial.command_responses["N0"] = b"/00"
    fake_pump.serial.command_responses["R"] = b"/04"

    with pytest.raises(
        UserVisibleException,
        match="Pump error /4: Invalid command sequence - check protocol structure",
    ):
        fake_pump.set_fine_positioning_mode(False)

    assert fake_pump.fine_positioning is True
    assert fake_pump.serial.commands == [b"N0\r", b"R\r"]


def test_get_max_position_reflects_mode(fake_pump):
    fake_pump.fine_positioning = False
    assert fake_pump.get_max_position() == 3000

    fake_pump.fine_positioning = True
    assert fake_pump.get_max_position() == 24000
