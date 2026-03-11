import copy
import importlib
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "navigate.model.devices.remote_focus.asi"
TIGER_MODULE_PATH = "navigate.model.devices.APIs.asi.asi_tiger_controller"


class _FakeTigerController:
    default_is_open = True

    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.connect_calls = 0
        self.disconnect_calls = 0
        self._is_open = type(self).default_is_open

    def connect_to_serial(self):
        self.connect_calls += 1

    def is_open(self):
        return self._is_open

    def disconnect_from_serial(self):
        self.disconnect_calls += 1


@pytest.fixture
def asi_module(monkeypatch):
    _FakeTigerController.default_is_open = True

    fake_tiger_module = types.ModuleType(TIGER_MODULE_PATH)
    fake_tiger_module.TigerController = _FakeTigerController
    monkeypatch.setitem(sys.modules, TIGER_MODULE_PATH, fake_tiger_module)

    sys.modules.pop(MODULE_PATH, None)
    module = importlib.import_module(MODULE_PATH)
    return importlib.reload(module)


def _build_config(sensor_mode="Widefield", readout_direction="Top-to-Bottom"):
    return {
        "configuration": {
            "microscopes": {
                "TestScope": {
                    "remote_focus": {
                        "hardware": {
                            "axis": "B",
                            "max": 5.0,
                            "min": -5.0,
                            "channel": "Dev7/ao3",
                        }
                    },
                    "daq": {"sample_rate": 10, "trigger_source": "PFI1"},
                    "camera": {"delay": 5},
                }
            }
        },
        "experiment": {
            "CameraParameters": {
                "TestScope": {
                    "sensor_mode": sensor_mode,
                    "readout_direction": readout_direction,
                }
            },
            "MicroscopeState": {
                "microscope_name": "test_mode",
                "zoom": "1x",
                "channels": {
                    "ch1": {"is_selected": True, "laser": "488"},
                    "ch2": {"is_selected": False, "laser": "561"},
                },
            },
        },
        "waveform_constants": {
            "other_constants": {
                "remote_focus_ramp_falling": "17.5",
                "remote_focus_delay": "0",
                "percent_smoothing": "0",
            },
            "remote_focus_constants": {
                "test_mode": {
                    "1x": {
                        "488": {"amplitude": "2.0", "offset": "0.1"},
                        "561": {"amplitude": "1.0", "offset": "0.0"},
                    }
                }
            },
        },
    }


def _new_rf(asi_module, config=None, remote_focus=None):
    if config is None:
        config = _build_config()
    if remote_focus is None:
        remote_focus = MagicMock()
        remote_focus.is_open.return_value = False
    return asi_module.ASIRemoteFocus("TestScope", remote_focus, copy.deepcopy(config))


def test_connect_success(asi_module):
    controller = asi_module.ASIRemoteFocus.connect(port="COM5", baudrate=9600)

    assert isinstance(controller, _FakeTigerController)
    assert controller.port == "COM5"
    assert controller.baudrate == 9600
    assert controller.connect_calls == 1


def test_connect_raises_when_not_open(asi_module):
    _FakeTigerController.default_is_open = False

    with patch.object(asi_module.logger, "error") as mock_error:
        with pytest.raises(Exception, match="ASI stage connection failed."):
            asi_module.ASIRemoteFocus.connect(port="COM5")

    mock_error.assert_called_once_with("ASI stage connection failed.")


def test_adjust_routes_to_triangle_for_bidirectional(asi_module):
    config = _build_config(sensor_mode="Light-Sheet", readout_direction="Bidirectional")
    constants = config["waveform_constants"]["remote_focus_constants"]["test_mode"]["1x"]["488"]
    constants["amplitude"] = "."
    constants["offset"] = "-"

    rf = _new_rf(asi_module, config=config)
    rf.triangle = MagicMock()
    rf.ramp = MagicMock()

    exposure_times = {"ch1": 0.05, "ch2": 0.03}
    sweep_times = {"ch1": 0.3, "ch2": 0.2}
    rf.adjust(exposure_times, sweep_times, offset=0.2)

    rf.triangle.assert_called_once_with(0.3, 1000.0, 0.2)
    rf.ramp.assert_not_called()
    rf_constants = rf.configuration["waveform_constants"]["remote_focus_constants"][
        "test_mode"
    ]["1x"]["488"]
    assert rf_constants["amplitude"] == "1000"
    assert rf_constants["offset"] == "0"
    rf.remote_focus.is_open.return_value = False


def test_adjust_routes_to_ramp_for_non_lightsheet(asi_module):
    config = _build_config(sensor_mode="Widefield", readout_direction="Bidirectional")
    constants = config["waveform_constants"]["remote_focus_constants"]["test_mode"]["1x"]["488"]
    constants["amplitude"] = "-"
    constants["offset"] = "."

    rf = _new_rf(asi_module, config=config)
    rf.triangle = MagicMock()
    rf.ramp = MagicMock()

    exposure_times = {"ch1": 0.1, "ch2": 0.07}
    sweep_times = {"ch1": 0.3, "ch2": 0.2}
    rf.adjust(exposure_times, sweep_times, offset=0.5)

    rf.ramp.assert_called_once_with(0.1, 17.5, 1000.0, 0.5)
    rf.triangle.assert_not_called()
    rf_constants = rf.configuration["waveform_constants"]["remote_focus_constants"][
        "test_mode"
    ]["1x"]["488"]
    assert rf_constants["amplitude"] == "1000"
    assert rf_constants["offset"] == "0"
    rf.remote_focus.is_open.return_value = False


def test_triangle_converts_units_and_sends_commands(asi_module):
    remote_focus = MagicMock()
    remote_focus.is_open.return_value = False
    rf = _new_rf(asi_module, remote_focus=remote_focus)

    rf.triangle(sweep_time=0.234, amplitude=1.5, offset=-0.25)

    remote_focus.single_axis_waveform.assert_called_once_with("B", 129, 1500.0, -250.0, 234)
    remote_focus.single_axis_mode.assert_called_once_with("B", 4)
    remote_focus.is_open.return_value = False


def test_ramp_converts_units_and_sends_commands(asi_module):
    remote_focus = MagicMock()
    remote_focus.is_open.return_value = False
    rf = _new_rf(asi_module, remote_focus=remote_focus)

    rf.ramp(exposure_time=0.101, flyback_time=20, amplitude=1.25, offset=0.5)

    remote_focus.single_axis_waveform.assert_called_once_with(
        "B", 132, 1250.0, 500.0, 121, 101
    )
    remote_focus.single_axis_mode.assert_called_once_with("B", 2)
    remote_focus.is_open.return_value = False


def test_move_delegates_to_adjust(asi_module):
    rf = _new_rf(asi_module)
    rf.adjust = MagicMock()

    exposure_times = {"ch1": 0.2}
    sweep_times = {"ch1": 0.3}
    rf.move(exposure_times, sweep_times, offset=-0.1)

    rf.adjust.assert_called_once_with(exposure_times, sweep_times, -0.1)
    rf.remote_focus.is_open.return_value = False


def test_close_turns_off_and_disconnects_when_open(asi_module):
    remote_focus = MagicMock()
    remote_focus.is_open.return_value = True
    rf = _new_rf(asi_module, remote_focus=remote_focus)

    rf.close()

    remote_focus.single_axis_mode.assert_called_once_with("B", 0)
    remote_focus.disconnect_from_serial.assert_called_once_with()
    remote_focus.is_open.return_value = False


def test_close_is_noop_when_not_open(asi_module):
    remote_focus = MagicMock()
    remote_focus.is_open.return_value = False
    rf = _new_rf(asi_module, remote_focus=remote_focus)

    rf.close()

    remote_focus.single_axis_mode.assert_not_called()
    remote_focus.disconnect_from_serial.assert_not_called()
    remote_focus.is_open.return_value = False
