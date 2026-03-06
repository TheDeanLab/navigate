import importlib
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "navigate.model.devices.laser.asi"
TIGER_MODULE_PATH = "navigate.model.devices.APIs.asi.asi_tiger_controller"


class _FakeTigerController:
    default_is_open = True

    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.connect_calls = 0
        self.disconnect_calls = 0
        self.setup_calls = []
        self.move_calls = []
        self.logic_on_calls = []
        self.logic_off_calls = []
        self._is_open = type(self).default_is_open

    def connect_to_serial(self):
        self.connect_calls += 1

    def is_open(self):
        return self._is_open

    def disconnect_from_serial(self):
        self.disconnect_calls += 1

    def setup_laser(self, axis):
        self.setup_calls.append(axis)

    def move_axis(self, axis, value):
        self.move_calls.append((axis, value))

    def logic_card_on(self, axis):
        self.logic_on_calls.append(axis)

    def logic_card_off(self, axis):
        self.logic_off_calls.append(axis)


@pytest.fixture
def asi_module(monkeypatch):
    _FakeTigerController.default_is_open = True
    tiger_module = types.ModuleType(TIGER_MODULE_PATH)
    tiger_module.TigerController = _FakeTigerController

    monkeypatch.setitem(sys.modules, TIGER_MODULE_PATH, tiger_module)

    sys.modules.pop(MODULE_PATH, None)
    module = importlib.import_module(MODULE_PATH)
    module = importlib.reload(module)
    return module


def _laser_configuration(
    analog_type=None,
    digital_type=None,
    analog_axis="X",
    digital_axis="Y",
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
                                    "axis": analog_axis,
                                    "min": 0.0,
                                    "max": 3.0,
                                }
                            },
                            "onoff": {
                                "hardware": {
                                    "type": digital_type,
                                    "axis": digital_axis,
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


def test_init_is_case_insensitive_for_mixed_modulation(asi_module):
    device_connection = MagicMock()
    laser = asi_module.ASILaser(
        "TestScope",
        device_connection,
        _laser_configuration(analog_type="asi", digital_type="AsI"),
        0,
    )

    assert str(laser) == "ASILaser"
    assert laser.modulation_type == "mixed"
    assert laser.laser_min_ao == 0.0
    assert laser.laser_max_ao == 3.0
    assert laser.analog_axis == "X"
    assert laser.laser_min_do == 0.0
    assert laser.laser_max_do == 5.0
    assert laser.digital_axis == "Y"


def test_init_analog_only_initializes_analog_properties(asi_module):
    device_connection = MagicMock()
    laser = asi_module.ASILaser(
        "TestScope",
        device_connection,
        _laser_configuration(analog_type="ASI", digital_type=None),
        0,
    )

    assert laser.modulation_type == "analog"
    assert laser.laser_max_ao == 3.0
    assert laser.analog_axis == "X"
    assert laser.digital_axis is None


def test_init_digital_only_initializes_digital_properties(asi_module):
    device_connection = MagicMock()
    laser = asi_module.ASILaser(
        "TestScope",
        device_connection,
        _laser_configuration(analog_type=None, digital_type="ASI"),
        0,
    )

    assert laser.modulation_type == "digital"
    assert laser.laser_max_do == 5.0
    assert laser.digital_axis == "Y"
    assert laser.analog_axis is None


def test_init_raises_for_unrecognized_modulation_type(asi_module):
    with patch.object(asi_module.ASILaser, "__del__", lambda self: None):
        with pytest.raises(ValueError, match="Laser modulation type not recognized."):
            asi_module.ASILaser(
                "TestScope",
                MagicMock(),
                _laser_configuration(analog_type="NI", digital_type="NI"),
                0,
            )


def test_connect_success(asi_module):
    controller = asi_module.ASILaser.connect(port="COM7", baudrate=9600)

    assert isinstance(controller, _FakeTigerController)
    assert controller.port == "COM7"
    assert controller.baudrate == 9600
    assert controller.connect_calls == 1


def test_connect_raises_when_connection_not_open(asi_module):
    _FakeTigerController.default_is_open = False

    with patch.object(asi_module.logger, "error") as mock_error:
        with pytest.raises(Exception, match="ASI stage connection failed."):
            asi_module.ASILaser.connect(port="COM5")

    mock_error.assert_called_once_with("ASI stage connection failed.")


def test_set_power_mixed_calls_setup_and_move_with_clamp(asi_module):
    device_connection = MagicMock()
    laser = asi_module.ASILaser(
        "TestScope",
        device_connection,
        _laser_configuration(analog_type="ASI", digital_type="ASI"),
        0,
    )

    laser.set_power(150)

    device_connection.setup_laser.assert_called_once_with("Y")
    device_connection.move_axis.assert_called_once_with("X", 3000.0)
    assert laser._current_intensity == 150


def test_set_power_analog_only_updates_axis_without_setup_laser(asi_module):
    device_connection = MagicMock()
    laser = asi_module.ASILaser(
        "TestScope",
        device_connection,
        _laser_configuration(analog_type="ASI", digital_type=None),
        0,
    )

    laser.set_power(25)

    device_connection.setup_laser.assert_not_called()
    device_connection.move_axis.assert_called_once_with("X", 750.0)
    assert laser._current_intensity == 25


def test_set_power_digital_only_calls_setup_without_axis_move(asi_module):
    device_connection = MagicMock()
    laser = asi_module.ASILaser(
        "TestScope",
        device_connection,
        _laser_configuration(analog_type=None, digital_type="ASI"),
        0,
    )

    laser.set_power(80)

    device_connection.setup_laser.assert_called_once_with("Y")
    device_connection.move_axis.assert_not_called()
    assert laser._current_intensity == 0


def test_turn_on_for_each_modulation_type(asi_module):
    mixed_laser = asi_module.ASILaser(
        "TestScope",
        MagicMock(),
        _laser_configuration(analog_type="ASI", digital_type="ASI"),
        0,
    )
    mixed_laser._current_intensity = 40
    with patch.object(mixed_laser, "set_power") as mixed_set_power:
        mixed_laser.turn_on()
    mixed_set_power.assert_called_once_with(40)
    mixed_laser.laser.logic_card_on.assert_called_once_with("Y")

    analog_laser = asi_module.ASILaser(
        "TestScope",
        MagicMock(),
        _laser_configuration(analog_type="ASI", digital_type=None),
        0,
    )
    analog_laser._current_intensity = 55
    with patch.object(analog_laser, "set_power") as analog_set_power:
        analog_laser.turn_on()
    analog_set_power.assert_called_once_with(55)
    analog_laser.laser.logic_card_on.assert_not_called()

    digital_laser = asi_module.ASILaser(
        "TestScope",
        MagicMock(),
        _laser_configuration(analog_type=None, digital_type="ASI"),
        0,
    )
    with patch.object(digital_laser, "set_power") as digital_set_power:
        digital_laser.turn_on()
    digital_set_power.assert_not_called()
    digital_laser.laser.logic_card_on.assert_called_once_with("Y")


def test_turn_off_for_each_modulation_type(asi_module):
    mixed_laser = asi_module.ASILaser(
        "TestScope",
        MagicMock(),
        _laser_configuration(analog_type="ASI", digital_type="ASI"),
        0,
    )
    mixed_laser._current_intensity = 65
    with patch.object(mixed_laser, "set_power") as mixed_set_power:
        mixed_laser.turn_off()
    mixed_set_power.assert_called_once_with(0)
    mixed_laser.laser.logic_card_off.assert_called_once_with("Y")
    assert mixed_laser._current_intensity == 65

    analog_laser = asi_module.ASILaser(
        "TestScope",
        MagicMock(),
        _laser_configuration(analog_type="ASI", digital_type=None),
        0,
    )
    analog_laser._current_intensity = 70
    with patch.object(analog_laser, "set_power") as analog_set_power:
        analog_laser.turn_off()
    analog_set_power.assert_called_once_with(0)
    analog_laser.laser.logic_card_off.assert_not_called()
    assert analog_laser._current_intensity == 70

    digital_laser = asi_module.ASILaser(
        "TestScope",
        MagicMock(),
        _laser_configuration(analog_type=None, digital_type="ASI"),
        0,
    )
    with patch.object(digital_laser, "set_power") as digital_set_power:
        digital_laser.turn_off()
    digital_set_power.assert_not_called()
    digital_laser.laser.logic_card_off.assert_called_once_with("Y")


def test_close_turns_off_and_disconnects_when_port_is_open(asi_module):
    device_connection = MagicMock()
    device_connection.is_open.return_value = True
    laser = asi_module.ASILaser(
        "TestScope",
        device_connection,
        _laser_configuration(analog_type="ASI", digital_type="ASI"),
        0,
    )

    with patch.object(laser, "turn_off") as mock_turn_off:
        laser.close()

    mock_turn_off.assert_called_once_with()
    device_connection.disconnect_from_serial.assert_called_once_with()


def test_close_is_noop_when_port_is_closed(asi_module):
    device_connection = MagicMock()
    device_connection.is_open.return_value = False
    laser = asi_module.ASILaser(
        "TestScope",
        device_connection,
        _laser_configuration(analog_type="ASI", digital_type="ASI"),
        0,
    )

    with patch.object(laser, "turn_off") as mock_turn_off:
        laser.close()

    mock_turn_off.assert_not_called()
    device_connection.disconnect_from_serial.assert_not_called()


def test_del_calls_close(asi_module):
    laser = object.__new__(asi_module.ASILaser)
    laser.laser = MagicMock()
    laser.laser.is_open.return_value = False

    with patch.object(laser, "close") as mock_close:
        laser.__del__()

    mock_close.assert_called_once_with()
