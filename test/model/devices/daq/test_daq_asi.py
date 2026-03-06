# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
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
from unittest.mock import patch

import pytest


MODULE_PATH = "navigate.model.devices.daq.asi"
TIGER_MODULE_PATH = "navigate.model.devices.APIs.asi.asi_tiger_controller"


class _FakeTigerController:
    default_is_open = True

    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.connect_calls = 0
        self._is_open = type(self).default_is_open

    def connect_to_serial(self):
        self.connect_calls += 1

    def is_open(self):
        return self._is_open


class _FakeDictProxy(dict):
    pass


class _FakeListProxy(list):
    pass


class _FakeASIDevice:
    def __init__(self):
        self.setup_control_loop_calls = []
        self.setup_z_stage_calls = []
        self.logic_on_calls = []
        self.logic_off_calls = []
        self.wait_for_loop_calls = 0
        self.raise_on_logic_on = False
        self.raise_on_logic_off = False
        self.axis_addr = {"Z": 1, "F": 2}

    def setup_control_loop(self, *args):
        self.setup_control_loop_calls.append(args)

    def setup_z_stage(self, axis, address, step):
        self.setup_z_stage_calls.append((axis, address, step))

    def get_axis_addr(self):
        return self.axis_addr

    def logic_cell_on(self, cell):
        if self.raise_on_logic_on:
            raise RuntimeError("logic on failed")
        self.logic_on_calls.append(cell)

    def logic_cell_off(self, cell):
        if self.raise_on_logic_off:
            raise RuntimeError("logic off failed")
        self.logic_off_calls.append(cell)

    def wait_for_loop(self):
        self.wait_for_loop_calls += 1


@pytest.fixture
def asi_module(monkeypatch):
    _FakeTigerController.default_is_open = True
    fake_tiger_module = types.ModuleType(TIGER_MODULE_PATH)
    fake_tiger_module.TigerController = _FakeTigerController
    monkeypatch.setitem(sys.modules, TIGER_MODULE_PATH, fake_tiger_module)

    sys.modules.pop(MODULE_PATH, None)
    module = importlib.import_module(MODULE_PATH)
    module = importlib.reload(module)

    monkeypatch.setattr(module, "DictProxy", _FakeDictProxy)
    monkeypatch.setattr(module, "ListProxy", _FakeListProxy)
    return module


def _build_configuration(galvo_container="list"):
    base_galvos = [
        {"phase": 0.0, "waveform": "sawtooth", "hardware": {"axis": "X"}},
        {"phase": 3.14159265, "waveform": "sine", "hardware": {"axis": "Y"}},
    ]
    if galvo_container == "list":
        galvo_config = _FakeListProxy(base_galvos)
    elif galvo_container == "dict":
        galvo_config = _FakeDictProxy(base_galvos[0])
    else:
        galvo_config = base_galvos

    return {
        "waveform_constants": {
            "other_constants": {"camera_delay": 5, "remote_focus_delay": 8},
            "galvo_constants": {
                "Galvo 0": {"ScopeA": {"1x": {"frequency": 2, "rising_ramp": 50}}},
                "Galvo 1": {"ScopeA": {"1x": {"frequency": 4, "rising_ramp": 40}}},
            },
        },
        "experiment": {
            "MicroscopeState": {
                "microscope_name": "ScopeA",
                "zoom": "1x",
                "start_position": 0.0,
                "end_position": 10.0,
                "step_size": 1.0,
                "number_z_steps": 10,
                "primary_z_axis": "z",
                "start_focus": 1.0,
                "end_focus": 3.0,
                "primary_f_axis": "f",
            }
        },
        "configuration": {
            "microscopes": {
                "ScopeA": {
                    "daq": {"sample_rate": 1000},
                    "galvo": galvo_config,
                    "remote_focus": {"hardware": {"axis": "A"}},
                    "stage": {
                        "hardware": [{"axes": ["z", "f"], "axes_mapping": ["Z", "F"]}]
                    },
                }
            }
        },
    }


def _build_initialized_asi(asi_module, galvo_container="list"):
    hardware = _FakeASIDevice()
    daq = asi_module.ASIDaq(
        microscope_name="ScopeA",
        device_connection=hardware,
        configuration=_build_configuration(galvo_container),
        device_id=1,
    )
    daq.exposure_times = {"channel_1": 0.02}
    daq.sweep_times = {"channel_1": 0.05}
    return daq, hardware


def test_connect_success(asi_module):
    tiger = asi_module.ASIDaq.connect(port="COM5", baudrate=9600)

    assert isinstance(tiger, _FakeTigerController)
    assert tiger.port == "COM5"
    assert tiger.baudrate == 9600
    assert tiger.connect_calls == 1


def test_connect_raises_when_not_open(asi_module):
    _FakeTigerController.default_is_open = False

    with patch.object(asi_module.logger, "error") as mock_error:
        with pytest.raises(Exception, match="ASI DAQ connection failed."):
            asi_module.ASIDaq.connect(port="COM5")

    mock_error.assert_called_once_with("ASI DAQ connection failed.")


def test_initialize_with_list_proxy_builds_outputs_and_axis_map(asi_module):
    daq, hardware = _build_initialized_asi(asi_module, galvo_container="list")

    assert daq.analog_outputs == {"galvo 0": "X", "galvo 1": "Y", "remote_focus": "A"}
    assert daq.phases == [0.0, 3.14159265]
    assert daq.axis_map == {"z": "Z", "f": "F"}
    assert hardware.setup_control_loop_calls[0] == (
        [200],
        0,
        0,
        100,
        120,
        daq.analog_outputs,
    )


def test_initialize_with_dict_proxy_wraps_single_galvo(asi_module):
    daq, _ = _build_initialized_asi(asi_module, galvo_container="dict")

    assert len(daq.galvos) == 1
    assert daq.analog_outputs["galvo 0"] == "X"
    assert "galvo 1" not in daq.analog_outputs


def test_initialize_raises_for_unexpected_galvo_type(asi_module):
    with pytest.raises(TypeError, match="Unexpected type for galvos"):
        asi_module.ASIDaq(
            microscope_name="ScopeA",
            device_connection=_FakeASIDevice(),
            configuration=_build_configuration(galvo_container="bad"),
            device_id=1,
        )


def test_prepare_acquisition_default_control_loop(asi_module):
    daq, hardware = _build_initialized_asi(asi_module)

    daq.prepare_acquisition("channel_1")

    control_loop_call = hardware.setup_control_loop_calls[-1]
    assert len(control_loop_call) == 6
    assert len(control_loop_call[0]) == 2
    assert control_loop_call[1] == 5.0
    assert control_loop_call[2] == 8.0
    assert control_loop_call[3] == 20.0
    assert control_loop_call[4] == 50.0
    assert control_loop_call[5] == daq.analog_outputs
    assert daq.current_channel_key == "channel_1"
    assert daq.is_updating_analog_task is False


def test_prepare_acquisition_single_mode_uses_one_step(asi_module):
    daq, hardware = _build_initialized_asi(asi_module)
    daq.single = True

    daq.prepare_acquisition("channel_1")

    control_loop_call = hardware.setup_control_loop_calls[-1]
    assert len(control_loop_call) == 7
    assert control_loop_call[-1] == 1


def test_prepare_acquisition_zstack_sets_stage_and_focus_steps(asi_module):
    daq, hardware = _build_initialized_asi(asi_module)
    daq.zstack = True

    daq.prepare_acquisition("channel_1")

    assert hardware.setup_z_stage_calls == [("Z", 1, 10), ("F", 2, 2)]
    control_loop_call = hardware.setup_control_loop_calls[-1]
    assert len(control_loop_call) == 7
    assert control_loop_call[-1] == 10


def test_prepare_acquisition_zstack_skips_focus_when_no_focus_delta(asi_module):
    daq, hardware = _build_initialized_asi(asi_module)
    daq.zstack = True
    daq.configuration["experiment"]["MicroscopeState"]["start_focus"] = 2.0
    daq.configuration["experiment"]["MicroscopeState"]["end_focus"] = 2.0

    daq.prepare_acquisition("channel_1")

    assert hardware.setup_z_stage_calls == [("Z", 1, 10)]


def test_run_acquisition_triggers_logic_and_waits_for_zstack(asi_module):
    daq, hardware = _build_initialized_asi(asi_module)
    daq.zstack = True

    daq.run_acquisition()

    assert hardware.logic_on_calls == ["1"]
    assert hardware.wait_for_loop_calls == 1


def test_run_acquisition_handles_logic_errors(asi_module):
    daq, hardware = _build_initialized_asi(asi_module)
    hardware.raise_on_logic_on = True

    with patch.object(asi_module.logger, "error") as mock_error:
        daq.run_acquisition()

    mock_error.assert_called_once()


def test_stop_acquisition_turns_off_logic_cells(asi_module):
    daq, hardware = _build_initialized_asi(asi_module)

    daq.stop_acquisition()

    assert hardware.logic_on_calls == ["8"]
    assert hardware.logic_off_calls == ["1"]


def test_stop_acquisition_handles_exceptions(asi_module):
    daq, hardware = _build_initialized_asi(asi_module)
    hardware.raise_on_logic_on = True

    daq.stop_acquisition()

    assert hardware.logic_off_calls == []


def test_wait_acquisition_done_is_noop(asi_module):
    daq, _ = _build_initialized_asi(asi_module)

    assert daq.wait_acquisition_done() is None
