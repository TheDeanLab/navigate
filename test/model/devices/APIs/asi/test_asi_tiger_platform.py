"""Serial discovery and connection portability without physical motion."""

from unittest.mock import MagicMock, call

import pytest
import serial
from serial.tools.list_ports_common import ListPortInfo

from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController


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
