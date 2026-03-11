import importlib
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "navigate.model.devices.laser.ni"
NIDAQMX_MODULE_PATH = "nidaqmx"
NIDAQMX_ERRORS_PATH = "nidaqmx.errors"
NIDAQMX_CONSTANTS_PATH = "nidaqmx.constants"


class _FakeDaqError(Exception):
    """Local stand-in for nidaqmx.errors.DaqError."""

    def __init__(self, message, error_type="DAQ_ERROR", error_code=-1):
        super().__init__(message)
        self.error_type = error_type
        self.error_code = error_code


class _FakeLineGrouping:
    CHAN_FOR_ALL_LINES = "chan_for_all_lines"


@pytest.fixture
def ni_module(monkeypatch):
    task_factory = MagicMock(name="TaskFactory")

    nidaqmx_module = types.ModuleType(NIDAQMX_MODULE_PATH)
    nidaqmx_module.Task = task_factory

    errors_module = types.ModuleType(NIDAQMX_ERRORS_PATH)
    errors_module.DaqError = _FakeDaqError

    constants_module = types.ModuleType(NIDAQMX_CONSTANTS_PATH)
    constants_module.LineGrouping = _FakeLineGrouping

    nidaqmx_module.errors = errors_module
    nidaqmx_module.constants = constants_module

    monkeypatch.setitem(sys.modules, NIDAQMX_MODULE_PATH, nidaqmx_module)
    monkeypatch.setitem(sys.modules, NIDAQMX_ERRORS_PATH, errors_module)
    monkeypatch.setitem(sys.modules, NIDAQMX_CONSTANTS_PATH, constants_module)

    sys.modules.pop(MODULE_PATH, None)
    module = importlib.import_module(MODULE_PATH)
    module = importlib.reload(module)
    return module, task_factory


def _laser_configuration(
    analog_type=None,
    digital_type=None,
    analog_channel="Dev1/ao0",
    digital_channel="Dev1/port0/line0",
):
    return {
        "configuration": {
            "microscopes": {
                "TestScope": {
                    "laser": [
                        {
                            "power": {
                                "hardware": {
                                    "type": analog_type,
                                    "channel": analog_channel,
                                    "min": 0.0,
                                    "max": 5.0,
                                }
                            },
                            "onoff": {
                                "hardware": {
                                    "type": digital_type,
                                    "channel": digital_channel,
                                    "min": 0.0,
                                    "max": 5.0,
                                }
                            },
                        }
                    ]
                }
            }
        }
    }


def _build_task_mock(name="NITask"):
    task = MagicMock(name=name)
    task.ao_channels = MagicMock(name=f"{name}.ao_channels")
    task.do_channels = MagicMock(name=f"{name}.do_channels")
    return task


def test_init_mixed_modulation_initializes_digital_and_analog(ni_module):
    module, task_factory = ni_module
    do_task = _build_task_mock(name="do_task")
    ao_task = _build_task_mock(name="ao_task")
    task_factory.side_effect = [do_task, ao_task]

    laser = module.NILaser("TestScope", None, _laser_configuration("NI", "NI"), 0)

    assert laser.modulation_type == "mixed"
    assert laser.digital_port_type == "digital"
    do_task.do_channels.add_do_chan.assert_called_once_with(
        "Dev1/port0/line0", line_grouping=module.LineGrouping.CHAN_FOR_ALL_LINES
    )
    ao_task.ao_channels.add_ao_voltage_chan.assert_called_once_with(
        "Dev1/ao0", min_val=0.0, max_val=5.0
    )


def test_init_analog_only_initializes_analog_task(ni_module):
    module, task_factory = ni_module
    ao_task = _build_task_mock(name="ao_task")
    task_factory.return_value = ao_task

    laser = module.NILaser("TestScope", None, _laser_configuration("NI", None), 0)

    assert laser.modulation_type == "analog"
    assert laser.laser_do_task is None
    ao_task.ao_channels.add_ao_voltage_chan.assert_called_once_with(
        "Dev1/ao0", min_val=0.0, max_val=5.0
    )


def test_init_digital_only_initializes_digital_task(ni_module):
    module, task_factory = ni_module
    do_task = _build_task_mock(name="do_task")
    task_factory.return_value = do_task

    laser = module.NILaser("TestScope", None, _laser_configuration(None, "NI"), 0)

    assert laser.modulation_type == "digital"
    assert laser.laser_ao_task is None
    assert laser.digital_port_type == "digital"
    do_task.do_channels.add_do_chan.assert_called_once_with(
        "Dev1/port0/line0", line_grouping=module.LineGrouping.CHAN_FOR_ALL_LINES
    )


def test_init_raises_for_unrecognized_modulation_type(ni_module):
    module, task_factory = ni_module

    with patch.object(module.NILaser, "__del__", lambda self: None):
        with pytest.raises(ValueError, match="Laser modulation type not recognized."):
            module.NILaser("TestScope", None, _laser_configuration("ASI", "ASI"), 0)

    task_factory.assert_not_called()


def test_initialize_digital_modulation_uses_ao_when_port_is_ao(ni_module):
    module, task_factory = ni_module
    do_task = _build_task_mock(name="do_task")
    task_factory.return_value = do_task

    laser = module.NILaser(
        "TestScope",
        None,
        _laser_configuration(None, "NI", digital_channel="Dev1/ao7"),
        0,
    )

    assert laser.digital_port_type == "analog"
    do_task.ao_channels.add_ao_voltage_chan.assert_called_once_with(
        "Dev1/ao7", min_val=0.0, max_val=5.0
    )
    do_task.do_channels.add_do_chan.assert_not_called()


def test_initialize_digital_modulation_handles_missing_channel_key(ni_module):
    module, task_factory = ni_module
    do_task = _build_task_mock(name="do_task")
    task_factory.return_value = do_task

    config = _laser_configuration(None, "NI")
    hardware = config["configuration"]["microscopes"]["TestScope"]["laser"][0]["onoff"][
        "hardware"
    ]
    del hardware["channel"]

    laser = module.NILaser("TestScope", None, config, 0)

    assert laser.laser_do_task is None


def test_initialize_digital_modulation_handles_daq_error(ni_module, capsys):
    module, task_factory = ni_module
    do_task = _build_task_mock(name="do_task")
    do_task.do_channels.add_do_chan.side_effect = _FakeDaqError(
        "digital setup failed", error_type="SETUP", error_code=-200
    )
    task_factory.return_value = do_task

    laser = module.NILaser("TestScope", None, _laser_configuration(None, "NI"), 0)
    out = capsys.readouterr().out

    assert laser.laser_do_task is None
    assert "digital setup failed" in out
    assert "-200" in out
    assert "SETUP" in out


def test_initialize_analog_modulation_handles_daq_error(ni_module, capsys):
    module, task_factory = ni_module
    ao_task = _build_task_mock(name="ao_task")
    ao_task.ao_channels.add_ao_voltage_chan.side_effect = _FakeDaqError(
        "analog setup failed", error_type="SETUP", error_code=-300
    )
    task_factory.return_value = ao_task

    laser = module.NILaser("TestScope", None, _laser_configuration("NI", None), 0)
    out = capsys.readouterr().out

    assert laser.laser_ao_task is ao_task
    assert "analog setup failed" in out
    assert "-300" in out
    assert "SETUP" in out


def test_set_power_no_analog_task_is_noop(ni_module):
    module, task_factory = ni_module
    do_task = _build_task_mock(name="do_task")
    task_factory.return_value = do_task
    laser = module.NILaser("TestScope", None, _laser_configuration(None, "NI"), 0)

    laser.set_power(55)

    assert laser._current_intensity == 0
    do_task.write.assert_not_called()


def test_set_power_scales_voltage_and_updates_intensity(ni_module):
    module, task_factory = ni_module
    ao_task = _build_task_mock(name="ao_task")
    task_factory.return_value = ao_task
    laser = module.NILaser("TestScope", None, _laser_configuration("NI", None), 0)

    laser.set_power(25.8)

    ao_task.write.assert_called_once_with(1.25, auto_start=True)
    assert laser._current_intensity == 25.8


def test_set_power_handles_daq_error(ni_module):
    module, task_factory = ni_module
    ao_task = _build_task_mock(name="ao_task")
    task_factory.return_value = ao_task
    laser = module.NILaser("TestScope", None, _laser_configuration("NI", None), 0)
    ao_task.write.side_effect = _FakeDaqError("set_power failed")

    with patch.object(module.logger, "exception") as mock_exception:
        laser.set_power(25)

    mock_exception.assert_called_once()
    assert laser._current_intensity == 0


def test_turn_on_without_digital_task_only_sets_power(ni_module):
    module, task_factory = ni_module
    ao_task = _build_task_mock(name="ao_task")
    task_factory.return_value = ao_task
    laser = module.NILaser("TestScope", None, _laser_configuration("NI", None), 0)

    with patch.object(laser, "set_power") as mock_set_power:
        laser.turn_on()

    mock_set_power.assert_called_once_with(0)


def test_turn_on_writes_true_for_digital_port(ni_module):
    module, task_factory = ni_module
    do_task = _build_task_mock(name="do_task")
    task_factory.return_value = do_task
    laser = module.NILaser("TestScope", None, _laser_configuration(None, "NI"), 0)

    laser.turn_on()

    do_task.write.assert_called_once_with(True, auto_start=True)


def test_turn_on_writes_max_voltage_for_analog_port(ni_module):
    module, task_factory = ni_module
    do_task = _build_task_mock(name="do_task")
    task_factory.return_value = do_task
    laser = module.NILaser(
        "TestScope",
        None,
        _laser_configuration(None, "NI", digital_channel="Dev1/ao4"),
        0,
    )

    laser.turn_on()

    do_task.write.assert_called_once_with(5.0, auto_start=True)


def test_turn_on_handles_daq_error(ni_module):
    module, task_factory = ni_module
    do_task = _build_task_mock(name="do_task")
    task_factory.return_value = do_task
    laser = module.NILaser("TestScope", None, _laser_configuration(None, "NI"), 0)
    do_task.write.side_effect = _FakeDaqError("turn_on failed")

    with patch.object(module.logger, "exception") as mock_exception:
        laser.turn_on()

    mock_exception.assert_called_once()


def test_turn_off_restores_intensity_and_writes_false_for_digital_port(ni_module):
    module, task_factory = ni_module
    do_task = _build_task_mock(name="do_task")
    task_factory.return_value = do_task
    laser = module.NILaser("TestScope", None, _laser_configuration(None, "NI"), 0)
    laser._current_intensity = 37

    with patch.object(laser, "set_power") as mock_set_power:
        laser.turn_off()

    mock_set_power.assert_called_once_with(0)
    do_task.write.assert_called_once_with(False, auto_start=True)
    assert laser._current_intensity == 37


def test_turn_off_writes_min_voltage_for_analog_port(ni_module):
    module, task_factory = ni_module
    do_task = _build_task_mock(name="do_task")
    task_factory.return_value = do_task
    laser = module.NILaser(
        "TestScope",
        None,
        _laser_configuration(None, "NI", digital_channel="Dev1/ao6"),
        0,
    )
    laser._current_intensity = 40

    with patch.object(laser, "set_power"):
        laser.turn_off()

    do_task.write.assert_called_once_with(0.0, auto_start=True)
    assert laser._current_intensity == 40


def test_turn_off_handles_daq_error(ni_module):
    module, task_factory = ni_module
    do_task = _build_task_mock(name="do_task")
    task_factory.return_value = do_task
    laser = module.NILaser("TestScope", None, _laser_configuration(None, "NI"), 0)
    do_task.write.side_effect = _FakeDaqError("turn_off failed")

    with patch.object(module.logger, "exception") as mock_exception:
        laser.turn_off()

    mock_exception.assert_called_once()


def test_close_closes_existing_tasks(ni_module):
    module, task_factory = ni_module
    do_task = _build_task_mock(name="do_task")
    ao_task = _build_task_mock(name="ao_task")
    task_factory.side_effect = [do_task, ao_task]
    laser = module.NILaser("TestScope", None, _laser_configuration("NI", "NI"), 0)

    laser.close()

    ao_task.close.assert_called_once_with()
    do_task.close.assert_called_once_with()
    laser.laser_ao_task = None
    laser.laser_do_task = None


def test_close_handles_daq_error(ni_module):
    module, task_factory = ni_module
    do_task = _build_task_mock(name="do_task")
    ao_task = _build_task_mock(name="ao_task")
    ao_task.close.side_effect = _FakeDaqError("close failed")
    task_factory.side_effect = [do_task, ao_task]
    laser = module.NILaser("TestScope", None, _laser_configuration("NI", "NI"), 0)

    with patch.object(module.logger, "exception") as mock_exception:
        laser.close()

    mock_exception.assert_called_once()
    do_task.close.assert_not_called()
    laser.laser_ao_task = None
    laser.laser_do_task = None


def test_del_closes_tasks_when_present(ni_module):
    module, _ = ni_module
    laser = object.__new__(module.NILaser)
    laser.laser_ao_task = MagicMock(name="ao_task")
    laser.laser_do_task = MagicMock(name="do_task")

    laser.__del__()

    laser.laser_ao_task.close.assert_called_once_with()
    laser.laser_do_task.close.assert_called_once_with()
    laser.laser_ao_task = None
    laser.laser_do_task = None


def test_del_logs_exceptions_during_task_close(ni_module):
    module, _ = ni_module
    laser = object.__new__(module.NILaser)
    laser.laser_ao_task = MagicMock(name="ao_task")
    laser.laser_do_task = MagicMock(name="do_task")
    laser.laser_ao_task.close.side_effect = RuntimeError("ao close failed")
    laser.laser_do_task.close.side_effect = RuntimeError("do close failed")

    with patch.object(module.logger, "exception") as mock_exception:
        laser.__del__()

    assert mock_exception.call_count == 2
    laser.laser_ao_task = None
    laser.laser_do_task = None


def test_del_without_tasks_is_noop(ni_module):
    module, _ = ni_module
    laser = object.__new__(module.NILaser)
    laser.laser_ao_task = None
    laser.laser_do_task = None

    laser.__del__()
