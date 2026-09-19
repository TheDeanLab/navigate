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

import importlib
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "navigate.model.devices.galvo.asi"
TIGER_MODULE_PATH = "navigate.model.devices.APIs.asi.asi_tiger_controller"


class _ImportTigerController:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self._open = False

    def connect_to_serial(self):
        self._open = True

    def is_open(self):
        return self._open


@pytest.fixture
def asi_module(monkeypatch):
    tiger_module = types.ModuleType(TIGER_MODULE_PATH)
    tiger_module.TigerController = _ImportTigerController

    monkeypatch.setitem(sys.modules, TIGER_MODULE_PATH, tiger_module)

    sys.modules.pop(MODULE_PATH, None)
    module = importlib.import_module(MODULE_PATH)
    module = importlib.reload(module)
    return module


def build_asi_configuration(
    *,
    waveform="sawtooth",
    galvo_factor="none",
    amplitude="1.0",
    offset="0.0",
    frequency="2.0",
    rising_ramp="50",
    channel_1_selected=True,
    channel_2_selected=True,
    channel_overrides=None,
    laser_overrides=None,
):
    galvo_parameters = {
        "amplitude": amplitude,
        "offset": offset,
        "rising_ramp": rising_ramp,
        "frequency": frequency,
    }
    if channel_overrides:
        galvo_parameters.update(channel_overrides)
    if laser_overrides:
        galvo_parameters.update(laser_overrides)

    return {
        "configuration": {
            "microscopes": {
                "TestScope": {
                    "galvo": [
                        {
                            "hardware": {
                                "max": 5.0,
                                "min": -5.0,
                                "channel": "Dev1/ao0",
                                "axis": "B",
                            },
                            "waveform": waveform,
                            "phase": 0.25,
                        }
                    ],
                    "daq": {
                        "sample_rate": 100,
                        "trigger_source": "/Dev1/PFI0",
                    },
                }
            }
        },
        "experiment": {
            "MicroscopeState": {
                "microscope_name": "TestScope",
                "zoom": "1x",
                "channels": {
                    "channel_1": {"is_selected": channel_1_selected, "laser": "488"},
                    "channel_2": {"is_selected": channel_2_selected, "laser": "561"},
                },
            }
        },
        "waveform_constants": {
            "other_constants": {
                "camera_delay": "0",
                "galvo_factor": galvo_factor,
            },
            "galvo_constants": {
                "Galvo 0": {
                    "TestScope": {
                        "1x": galvo_parameters,
                    }
                },
            },
        },
    }


def build_asi_galvo(module, configuration=None, controller=None):
    if configuration is None:
        configuration = build_asi_configuration()
    if controller is None:
        controller = MagicMock(name="TigerController")
        controller.is_open.return_value = True
    galvo = module.ASIGalvo("TestScope", controller, configuration, device_id=0)
    return galvo, controller


def default_timing():
    exposure_times = {"channel_1": 0.2, "channel_2": 0.2}
    sweep_times = {"channel_1": 0.2, "channel_2": 0.2}
    return exposure_times, sweep_times


def test_init_and_str(asi_module):
    galvo, controller = build_asi_galvo(asi_module)

    assert str(galvo) == "GalvoASI"
    assert galvo.galvo is controller
    assert galvo.axis == "B"

    galvo.close = lambda: None


def test_connect_success(asi_module):
    tiger = MagicMock(name="TigerController")
    tiger.is_open.return_value = True

    with patch.object(asi_module, "TigerController", return_value=tiger) as tiger_cls:
        result = asi_module.ASIGalvo.connect("COM7", baudrate=57600, timeout=0.1)

    assert result is tiger
    tiger_cls.assert_called_once_with("COM7", 57600)
    tiger.connect_to_serial.assert_called_once_with()


def test_connect_failure_raises(asi_module):
    tiger = MagicMock(name="TigerController")
    tiger.is_open.return_value = False

    with patch.object(asi_module, "TigerController", return_value=tiger):
        with patch.object(asi_module.logger, "error") as mock_error:
            with pytest.raises(Exception, match="ASI stage connection failed"):
                asi_module.ASIGalvo.connect("COM8")

    mock_error.assert_called_once_with("ASI stage connection failed.")


def test_adjust_sawtooth_rounds_invalid_duty_cycle(asi_module):
    configuration = build_asi_configuration(
        waveform="sawtooth",
        galvo_factor="channel",
        rising_ramp="63",
        frequency="2.0",
        channel_2_selected=False,
        channel_overrides={"Channel 1": {"amplitude": "2.0", "offset": "0.5"}},
    )
    galvo, _ = build_asi_galvo(asi_module, configuration=configuration)
    exposure_times, sweep_times = default_timing()

    with patch.object(galvo, "sawtooth") as mock_sawtooth:
        with patch("builtins.print"):
            galvo.adjust(exposure_times, sweep_times)

    mock_sawtooth.assert_called_once_with(0.1, 2.0, 0.5, 50)
    assert (
        configuration["waveform_constants"]["galvo_constants"]["Galvo 0"]["TestScope"][
            "1x"
        ]["rising ramp"]
        == 50
    )

    galvo.close = lambda: None


def test_adjust_sine_uses_laser_factor_and_zero_frequency_period(asi_module):
    configuration = build_asi_configuration(
        waveform="sine",
        galvo_factor="laser",
        frequency="0",
        channel_2_selected=False,
        laser_overrides={"488": {"amplitude": "3.0", "offset": "-0.2"}},
    )
    galvo, _ = build_asi_galvo(asi_module, configuration=configuration)
    exposure_times, sweep_times = default_timing()

    with patch.object(galvo, "sine_wave") as mock_sine_wave:
        galvo.adjust(exposure_times, sweep_times)

    mock_sine_wave.assert_called_once_with(0.2, 3.0, -0.2)

    galvo.close = lambda: None


def test_adjust_unknown_waveform_prints_message(asi_module):
    configuration = build_asi_configuration(waveform="banana", channel_2_selected=False)
    galvo, _ = build_asi_galvo(asi_module, configuration=configuration)
    exposure_times, sweep_times = default_timing()

    with patch.object(galvo, "sawtooth") as mock_sawtooth:
        with patch.object(galvo, "sine_wave") as mock_sine_wave:
            with patch("builtins.print") as mock_print:
                result = galvo.adjust(exposure_times, sweep_times)

    assert result is None
    mock_sawtooth.assert_not_called()
    mock_sine_wave.assert_not_called()
    mock_print.assert_called_with("Unknown Galvo waveform specified in configuration file.")

    galvo.close = lambda: None


def test_adjust_returns_none_on_invalid_waveform_constants(asi_module):
    configuration = build_asi_configuration(
        amplitude="not-a-number",
        channel_2_selected=False,
    )
    galvo, _ = build_asi_galvo(asi_module, configuration=configuration)
    exposure_times, sweep_times = default_timing()

    with patch.object(asi_module.logger, "debug") as mock_debug:
        result = galvo.adjust(exposure_times, sweep_times)

    assert result is None
    mock_debug.assert_called_once()

    galvo.close = lambda: None


@pytest.mark.parametrize(
    "duty_cycle, expected_waveform_id, expected_amplitude, expected_period",
    [
        (0, 128, -2000.0, 11),
        (50, 129, 2000.0, 12),
        (100, 128, 2000.0, 11),
    ],
)
def test_sawtooth_encodes_commands(
    asi_module,
    duty_cycle,
    expected_waveform_id,
    expected_amplitude,
    expected_period,
):
    galvo, controller = build_asi_galvo(asi_module)

    galvo.sawtooth(period=0.011, amplitude=2.0, offset=0.5, duty_cycle=duty_cycle)

    controller.single_axis_waveform.assert_called_once_with(
        "B",
        expected_waveform_id,
        expected_amplitude,
        500.0,
        expected_period,
    )
    controller.single_axis_mode.assert_called_once_with("B", 4)

    galvo.close = lambda: None


def test_sine_wave_encodes_commands(asi_module):
    galvo, controller = build_asi_galvo(asi_module)

    galvo.sine_wave(period=0.011, amplitude=1.5, offset=-0.25)

    controller.single_axis_waveform.assert_called_once_with("B", 131, 1500.0, -250.0, 11)
    controller.single_axis_mode.assert_called_once_with("B", 4)

    galvo.close = lambda: None


def test_turn_off_sets_single_axis_mode_zero(asi_module):
    galvo, controller = build_asi_galvo(asi_module)

    galvo.turn_off()

    controller.single_axis_mode.assert_called_once_with("B", 0)

    galvo.close = lambda: None


def test_close_turns_off_and_disconnects_when_open(asi_module):
    galvo, controller = build_asi_galvo(asi_module)
    controller.is_open.return_value = True

    with patch.object(galvo, "turn_off") as mock_turn_off:
        galvo.close()

    mock_turn_off.assert_called_once_with()
    controller.disconnect_from_serial.assert_called_once_with()

    galvo.close = lambda: None


def test_close_is_noop_when_controller_not_open(asi_module):
    galvo, controller = build_asi_galvo(asi_module)
    controller.is_open.return_value = False

    with patch.object(galvo, "turn_off") as mock_turn_off:
        galvo.close()

    mock_turn_off.assert_not_called()
    controller.disconnect_from_serial.assert_not_called()

    galvo.close = lambda: None


def test_del_calls_close(asi_module):
    galvo, _ = build_asi_galvo(asi_module)

    with patch.object(galvo, "close") as mock_close:
        galvo.__del__()

    mock_close.assert_called_once_with()

    galvo.close = lambda: None
