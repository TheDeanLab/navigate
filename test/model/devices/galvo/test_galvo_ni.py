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

MODULE_PATH = "navigate.model.devices.galvo.ni"
NIDAQMX_MODULE_PATH = "nidaqmx"


def build_ni_configuration():
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
                            "waveform": "sawtooth",
                            "phase": 0.25,
                        }
                    ],
                    "daq": {
                        "sample_rate": 100,
                        "trigger_source": "/Dev1/PFI0",
                    },
                    "camera": {"delay": 0},
                }
            }
        },
        "experiment": {
            "MicroscopeState": {
                "microscope_name": "TestScope",
                "zoom": "1x",
                "channels": {
                    "channel_1": {"is_selected": True, "laser": "488"},
                },
            }
        },
        "waveform_constants": {
            "other_constants": {"galvo_factor": "none"},
            "galvo_constants": {
                "Galvo 0": {
                    "TestScope": {
                        "1x": {
                            "amplitude": "1.0",
                            "offset": "0.0",
                            "rising_ramp": "50",
                            "frequency": "1.0",
                        }
                    }
                },
            },
        },
    }


@pytest.fixture
def ni_module(monkeypatch):
    task_factory = MagicMock(name="TaskFactory")

    nidaqmx_module = types.ModuleType(NIDAQMX_MODULE_PATH)
    nidaqmx_module.Task = task_factory

    monkeypatch.setitem(sys.modules, NIDAQMX_MODULE_PATH, nidaqmx_module)

    sys.modules.pop(MODULE_PATH, None)
    module = importlib.import_module(MODULE_PATH)
    module = importlib.reload(module)
    return module, task_factory


def build_galvo(module):
    configuration = build_ni_configuration()
    daq = types.SimpleNamespace(analog_outputs={})
    galvo = module.NIGalvo("TestScope", daq, configuration, device_id=0)
    return galvo, daq


def test_init_and_str(ni_module):
    module, _ = ni_module
    galvo, _ = build_galvo(module)

    assert str(galvo) == "GalvoNI"
    assert galvo.trigger_source == "/Dev1/PFI0"
    assert galvo.galvo_id == 0

    galvo.turn_off = lambda: None


def test_adjust_updates_daq_outputs(ni_module):
    module, _ = ni_module
    galvo, daq = build_galvo(module)

    exposure_times = {"channel_1": 0.2}
    sweep_times = {"channel_1": 0.2}

    with patch.object(
        module.GalvoBase,
        "adjust",
        return_value={"channel_1": [1.0, 2.0, 3.0]},
    ) as mock_adjust:
        waveform_dict = galvo.adjust(exposure_times, sweep_times)

    mock_adjust.assert_called_once()
    assert waveform_dict == {"channel_1": [1.0, 2.0, 3.0]}
    assert daq.analog_outputs["Dev1/ao0"] == {
        "trigger_source": "/Dev1/PFI0",
        "waveform": {"channel_1": [1.0, 2.0, 3.0]},
    }

    galvo.turn_off = lambda: None


def test_turn_off_writes_zero_and_closes_task(ni_module):
    module, task_factory = ni_module
    galvo, _ = build_galvo(module)

    task = MagicMock(name="Task")
    task_factory.return_value = task

    galvo.turn_off()

    task.ao_channels.add_ao_voltage_chan.assert_called_once_with("Dev1/ao0")
    task.write.assert_called_once_with([0], auto_start=True)
    task.stop.assert_called_once_with()
    task.close.assert_called_once_with()

    galvo.turn_off = lambda: None


def test_turn_off_logs_exceptions(ni_module):
    module, task_factory = ni_module
    galvo, _ = build_galvo(module)

    task_factory.side_effect = RuntimeError("task creation failed")

    with patch.object(module.logger, "exception") as mock_exception:
        galvo.turn_off()

    mock_exception.assert_called_once()

    galvo.turn_off = lambda: None


def test_del_calls_turn_off(ni_module):
    module, _ = ni_module
    galvo, _ = build_galvo(module)

    with patch.object(galvo, "turn_off") as mock_turn_off:
        galvo.__del__()

    mock_turn_off.assert_called_once_with()
    galvo.turn_off = lambda: None
