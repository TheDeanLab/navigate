"""Serial discovery and connection portability without physical motion."""

from unittest.mock import MagicMock, call

import pytest
import serial
from serial.tools.list_ports_common import ListPortInfo

from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController
from navigate.model.devices.APIs.asi.asi_tiger_controller import ASIException


@pytest.mark.parametrize(
    "ports, expected",
    [
        (["COM10", "COM2", "COM1"], ["COM1", "COM2", "COM10"]),
        (
            ["/dev/ttyUSB10", "/dev/ttyUSB2", "/dev/ttyACM0"],
            ["/dev/ttyACM0", "/dev/ttyUSB2", "/dev/ttyUSB10"],
        ),
    ],
)
def test_scan_ports_supports_platform_device_names(monkeypatch, ports, expected):
    monkeypatch.setattr(
        "navigate.model.devices.APIs.asi.asi_tiger_controller.list_ports.comports",
        lambda: [ListPortInfo(port) for port in ports],
    )
    assert TigerController.scan_ports() == expected


@pytest.mark.parametrize("response", [b"", b":N-1\r\n", b"garbage\r\n"])
def test_checked_blanking_rejects_missing_or_failed_acknowledgement(response):
    controller = TigerController("unused", 115200)
    controller.serial = MagicMock()
    controller.serial.readline.return_value = response
    with pytest.raises(ASIException):
        controller.logic_card_off_checked("1")
    assert controller.serial.write.call_count == 1
    assert controller.safe_to_write.is_set()


def test_checked_blanking_propagates_serial_timeout_and_releases_lock():
    controller = TigerController("unused", 115200)
    controller.serial = MagicMock()
    controller.serial.write.side_effect = serial.SerialTimeoutException("write timeout")
    with pytest.raises(serial.SerialTimeoutException):
        controller.logic_card_off_checked("1")
    assert controller.safe_to_write.is_set()
    controller.serial.readline.assert_not_called()


def test_checked_blanking_requires_both_command_acknowledgements():
    controller = TigerController("unused", 115200)
    controller.serial = MagicMock()
    controller.serial.readline.return_value = b":A\r\n"
    controller.logic_card_off_checked("1")
    assert controller.serial.write.call_args_list == [
        call(b"6 M E = 33\r\r"),
        call(b"6 CCA Z=0\r\r"),
    ]
    assert controller.serial.readline.call_count == 2


@pytest.mark.parametrize("supports_buffer_size", [False, True])
def test_connection_handles_optional_buffer_size_after_open(supports_buffer_size):
    controller = TigerController("/dev/ttyUSB0", 115200)
    # An explicit interface prevents a MagicMock from inventing Windows methods.
    interface = [
        "open",
        "close",
        "is_open",
        "reset_input_buffer",
        "reset_output_buffer",
    ]
    if supports_buffer_size:
        interface.append("set_buffer_size")
    port = MagicMock(spec=interface)
    port.is_open = True
    controller.serial = port
    controller.get_default_motor_axis_sequence = MagicMock(return_value=["X", "Y"])

    controller.connect_to_serial()

    port.open.assert_called_once_with()
    assert port.baudrate == 115200
    assert port.parity == serial.PARITY_NONE
    assert port.bytesize == serial.EIGHTBITS
    assert port.stopbits == serial.STOPBITS_ONE
    assert (port.xonoff, port.rtscts, port.dsrdtr) == (False, False, False)
    assert controller.default_axes_sequence == ["X", "Y"]
    if supports_buffer_size:
        assert port.mock_calls[:2] == [call.open(), call.set_buffer_size(12800, 12800)]
    else:
        assert not hasattr(port, "set_buffer_size")
