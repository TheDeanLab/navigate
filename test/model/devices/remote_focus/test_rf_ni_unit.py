import importlib
import sys
import types
from unittest.mock import MagicMock

import pytest


MODULE_PATH = "navigate.model.devices.remote_focus.ni"
BASE_MODULE_PATH = "navigate.model.devices.remote_focus.base"


class _FakeRemoteFocusBase:
    def __init__(self, microscope_name, device_connection, configuration, *args, **kwargs):
        self.device_connection = device_connection
        self.configuration = configuration
        self.microscope_name = microscope_name
        self.device_config = configuration["configuration"]["microscopes"][microscope_name][
            "remote_focus"
        ]

    def adjust(self, exposure_times, sweep_times, offset=None):
        return {"ch1": [0.1, 0.2]}


class _FakeDAQ:
    def __init__(self):
        self.analog_outputs = {}
        self.updated_boards = []

    def update_analog_task(self, board_name):
        self.updated_boards.append(board_name)


@pytest.fixture
def ni_module(monkeypatch):
    fake_base_module = types.ModuleType(BASE_MODULE_PATH)
    fake_base_module.RemoteFocusBase = _FakeRemoteFocusBase

    monkeypatch.setitem(sys.modules, BASE_MODULE_PATH, fake_base_module)

    sys.modules.pop(MODULE_PATH, None)
    module = importlib.import_module(MODULE_PATH)
    return importlib.reload(module)


@pytest.fixture
def ni_config():
    return {
        "configuration": {
            "microscopes": {
                "TestScope": {
                    "remote_focus": {"hardware": {"channel": "Dev7/ao3"}},
                    "daq": {"sample_rate": 10, "trigger_source": "PFI1"},
                }
            }
        }
    }


def test_ni_init_sets_trigger_and_board_name(ni_module, ni_config):
    daq = _FakeDAQ()
    rf = ni_module.NIRemoteFocus("TestScope", daq, ni_config)

    assert rf.trigger_source == "PFI1"
    assert rf.board_name == "Dev7"
    assert rf.daq is daq


def test_ni_adjust_updates_analog_outputs(ni_module, ni_config, monkeypatch):
    daq = _FakeDAQ()
    rf = ni_module.NIRemoteFocus("TestScope", daq, ni_config)

    parent_adjust = MagicMock(return_value={"ch1": [1.0, 2.0]})
    monkeypatch.setattr(ni_module.RemoteFocusBase, "adjust", parent_adjust)

    exposure_times = {"ch1": 0.1}
    sweep_times = {"ch1": 0.3}
    waveform = rf.adjust(exposure_times, sweep_times, offset=0.25)

    assert waveform == {"ch1": [1.0, 2.0]}
    parent_adjust.assert_called_once_with(exposure_times, sweep_times, 0.25)
    assert daq.analog_outputs["Dev7/ao3"] == {
        "trigger_source": "PFI1",
        "waveform": waveform,
    }


def test_ni_move_calls_adjust_and_updates_task(ni_module, ni_config):
    daq = _FakeDAQ()
    rf = ni_module.NIRemoteFocus("TestScope", daq, ni_config)
    rf.adjust = MagicMock(return_value={"ch1": [0.0]})

    exposure_times = {"ch1": 0.2}
    sweep_times = {"ch1": 0.4}
    rf.move(exposure_times, sweep_times, offset=-0.1)

    rf.adjust.assert_called_once_with(exposure_times, sweep_times, -0.1)
    assert daq.updated_boards == ["Dev7"]
