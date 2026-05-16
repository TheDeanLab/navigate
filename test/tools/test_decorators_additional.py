import json
from unittest.mock import Mock

import pytest

import navigate.tools.decorators as decorators


def test_performance_monitor_logs_visible_args_and_result(monkeypatch):
    logger = Mock()
    perf_counter = Mock(side_effect=[100, 160])

    monkeypatch.setattr(decorators, "logger", logger)
    monkeypatch.setattr(decorators.time, "perf_counter_ns", perf_counter)
    monkeypatch.setattr(decorators.time, "time", lambda: 12.5)

    @decorators.performance_monitor(
        prefix="Acquire",
        display_args=lambda *args: {"arg0": args[0]},
        display_result=lambda result: f"result:{result}",
    )
    def sample(value):
        return value + 1

    assert sample(4) == 5

    payload = json.loads(logger.performance.call_args.args[0])
    assert payload["kind"] == "Acquire"
    assert payload["args"] == {"arg0": 4}
    assert payload["result"] == "result:5"
    assert payload["duration_ns"] == 60
    assert payload["timestamp"] == 12.5


def test_performance_monitor_hides_args_and_result_by_default(monkeypatch):
    logger = Mock()
    monkeypatch.setattr(decorators, "logger", logger)
    monkeypatch.setattr(decorators.time, "perf_counter_ns", Mock(side_effect=[1, 2]))
    monkeypatch.setattr(decorators.time, "time", lambda: 1.0)

    @decorators.performance_monitor()
    def sample():
        return "done"

    assert sample() == "done"

    payload = json.loads(logger.performance.call_args.args[0])
    assert payload["kind"] == "General"
    assert payload["args"] == "Hidden"
    assert payload["result"] == "Hidden"


def test_log_initialization_logs_success(monkeypatch):
    logger = Mock()
    monkeypatch.setattr(decorators.logging, "getLogger", Mock(return_value=logger))

    class Device:
        __module__ = "navigate.fake_device"

        def __init__(self, port, baudrate=None):
            self.port = port
            self.baudrate = baudrate

    Device = decorators.log_initialization(Device)
    device = Device("COM1", baudrate=115200)

    assert device.port == "COM1"
    logger.info.assert_called_once()
    assert "Device" in logger.info.call_args.args[0]


def test_log_initialization_logs_failure_and_reraises(monkeypatch):
    logger = Mock()
    monkeypatch.setattr(decorators.logging, "getLogger", Mock(return_value=logger))

    class Device:
        __module__ = "navigate.fake_device"

        def __init__(self, port):
            raise ValueError(f"bad port: {port}")

    Device = decorators.log_initialization(Device)

    with pytest.raises(ValueError, match="bad port: COM2"):
        Device("COM2")

    assert logger.error.call_count == 3
