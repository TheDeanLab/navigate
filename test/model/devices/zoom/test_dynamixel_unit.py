from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import navigate.model.devices.zoom.dynamixel as dynamixel_module


def _build_configuration():
    return {
        "configuration": {
            "microscopes": {
                "scope": {
                    "zoom": {
                        "position": {"low": 100, "high": 200},
                        "hardware": {"servo_id": 7},
                    }
                }
            }
        }
    }


def _build_api_mock():
    return SimpleNamespace(
        closePort=Mock(),
        portHandler=Mock(return_value=11),
        packetHandler=Mock(),
        openPort=Mock(return_value=True),
        setBaudRate=Mock(),
        write1ByteTxRx=Mock(),
        write2ByteTxRx=Mock(),
        read4ByteTxRx=Mock(return_value=123),
    )


def test_connect_success(monkeypatch):
    api = _build_api_mock()
    monkeypatch.setattr(dynamixel_module, "dynamixel", api)

    port_num = dynamixel_module.DynamixelZoom.connect("COM7", baudrate=57600)

    assert port_num == 11
    api.portHandler.assert_called_once_with(b"COM7")
    api.packetHandler.assert_called_once()
    api.openPort.assert_called_once_with(11)
    api.setBaudRate.assert_called_once_with(11, 57600)


def test_connect_failure_raises_runtime_error(monkeypatch):
    api = _build_api_mock()
    api.openPort.return_value = False
    monkeypatch.setattr(dynamixel_module, "dynamixel", api)

    with pytest.raises(RuntimeError, match="Unable to open port"):
        dynamixel_module.DynamixelZoom.connect("COM9")


def test_set_zoom_valid_and_invalid(monkeypatch):
    api = _build_api_mock()
    monkeypatch.setattr(dynamixel_module, "dynamixel", api)

    zoom = dynamixel_module.DynamixelZoom("scope", 42, _build_configuration())
    zoom.move = Mock()

    zoom.set_zoom("low", wait_until_done=True)
    zoom.move.assert_called_once_with(100, True)
    assert zoom.zoomvalue == "low"

    with pytest.raises(ValueError, match="Zoom designation"):
        zoom.set_zoom("missing")


def test_move_without_wait_writes_expected_commands(monkeypatch):
    api = _build_api_mock()
    monkeypatch.setattr(dynamixel_module, "dynamixel", api)
    zoom = dynamixel_module.DynamixelZoom("scope", 77, _build_configuration())

    zoom.move(position=333, wait_until_done=False)

    assert api.write1ByteTxRx.call_count == 2
    assert api.write2ByteTxRx.call_count == 3
    api.read4ByteTxRx.assert_not_called()


def test_move_wait_until_done_reads_until_in_range(monkeypatch):
    api = _build_api_mock()
    api.read4ByteTxRx = Mock(side_effect=[0, 95])
    monkeypatch.setattr(dynamixel_module, "dynamixel", api)
    monkeypatch.setattr(dynamixel_module.time, "sleep", Mock())
    monkeypatch.setattr(dynamixel_module.time, "time", Mock(side_effect=[0, 0.1, 0.2]))

    zoom = dynamixel_module.DynamixelZoom("scope", 88, _build_configuration())
    zoom.timeout = 10

    zoom.move(position=100, wait_until_done=True)

    assert api.read4ByteTxRx.call_count == 2


def test_move_wait_until_done_times_out(monkeypatch):
    api = _build_api_mock()
    api.read4ByteTxRx = Mock(return_value=0)
    monkeypatch.setattr(dynamixel_module, "dynamixel", api)
    monkeypatch.setattr(dynamixel_module.time, "sleep", Mock())
    monkeypatch.setattr(dynamixel_module.time, "time", Mock(side_effect=[0, 20]))

    zoom = dynamixel_module.DynamixelZoom("scope", 99, _build_configuration())
    zoom.timeout = 1

    zoom.move(position=100, wait_until_done=True)
    assert api.read4ByteTxRx.call_count == 1


def test_read_position_returns_current_servo_value(monkeypatch):
    api = _build_api_mock()
    api.read4ByteTxRx.return_value = 2048
    monkeypatch.setattr(dynamixel_module, "dynamixel", api)
    zoom = dynamixel_module.DynamixelZoom("scope", 123, _build_configuration())

    assert zoom.read_position() == 2048


def test_del_swallows_close_errors(monkeypatch):
    api = _build_api_mock()
    api.closePort.side_effect = RuntimeError("close failed")
    monkeypatch.setattr(dynamixel_module, "dynamixel", api)
    zoom = dynamixel_module.DynamixelZoom("scope", 456, _build_configuration())

    # Should not raise.
    zoom.__del__()
