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

import numpy as np
import pytest


MODULE_PATH = "navigate.model.devices.daq.ni"
NIDAQMX_MODULE_PATH = "nidaqmx"
NIDAQMX_CONSTANTS_PATH = "nidaqmx.constants"
NIDAQMX_TASK_PATH = "nidaqmx.task"
NIDAQMX_SYSTEM_PATH = "nidaqmx.system"


class _FakeDaqError(Exception):
    pass


class _FakeAcquisitionType:
    FINITE = "finite"


class _FakeLineGrouping:
    CHAN_FOR_ALL_LINES = "chan_for_all_lines"


class _FakeDIChannels:
    def __init__(self):
        self.calls = []

    def add_di_chan(self, channel):
        self.calls.append(channel)


class _FakeCOChannels:
    def __init__(self):
        self.calls = []

    def add_co_pulse_chan_time(self, channel, high_time, low_time, initial_delay):
        self.calls.append(
            {
                "channel": channel,
                "high_time": high_time,
                "low_time": low_time,
                "initial_delay": initial_delay,
            }
        )


class _FakeDOChannels:
    def __init__(self):
        self.calls = []

    def add_do_chan(self, channel, line_grouping=None):
        self.calls.append({"channel": channel, "line_grouping": line_grouping})


class _FakeAOChannels:
    def __init__(self):
        self.calls = []

    def add_ao_voltage_chan(self, channel):
        self.calls.append(channel)


class _FakeTiming:
    def __init__(self):
        self.implicit_calls = []
        self.sample_clock_calls = []

    def cfg_implicit_timing(self, sample_mode, samps_per_chan):
        self.implicit_calls.append(
            {"sample_mode": sample_mode, "samps_per_chan": samps_per_chan}
        )

    def cfg_samp_clk_timing(self, rate, sample_mode, samps_per_chan):
        self.sample_clock_calls.append(
            {
                "rate": rate,
                "sample_mode": sample_mode,
                "samps_per_chan": samps_per_chan,
            }
        )


class _FakeStartTrigger:
    def __init__(self):
        self.cfg_calls = []
        self.retriggerable = None

    def cfg_dig_edge_start_trig(self, source):
        self.cfg_calls.append(source)


class _FakeTriggers:
    def __init__(self):
        self.start_trigger = _FakeStartTrigger()


class _FakeTask:
    def __init__(self, read_sequence=None):
        self.di_channels = _FakeDIChannels()
        self.co_channels = _FakeCOChannels()
        self.do_channels = _FakeDOChannels()
        self.ao_channels = _FakeAOChannels()
        self.timing = _FakeTiming()
        self.triggers = _FakeTriggers()
        self.write_calls = []
        self.read_sequence = list(
            read_sequence if read_sequence is not None else [True]
        )
        self.wait_calls = []
        self.register_done_event_calls = []
        self.start_calls = 0
        self.stop_calls = 0
        self.close_calls = 0
        self.is_done = True
        self.wait_exception = None
        self.stop_exception = None
        self.close_exception = None
        self.start_exception = None
        self.write_exception = None
        self.register_exception = None

    def write(self, data, auto_start=False):
        if self.write_exception:
            raise self.write_exception
        self.write_calls.append({"data": np.asarray(data), "auto_start": auto_start})

    def read(self):
        value = self.read_sequence[0]
        if len(self.read_sequence) > 1:
            self.read_sequence.pop(0)
        return value

    def start(self):
        if self.start_exception:
            raise self.start_exception
        self.start_calls += 1

    def stop(self):
        if self.stop_exception:
            raise self.stop_exception
        self.stop_calls += 1

    def close(self):
        if self.close_exception:
            raise self.close_exception
        self.close_calls += 1

    def wait_until_done(self, timeout=None):
        self.wait_calls.append(timeout)
        if self.wait_exception:
            raise self.wait_exception

    def is_task_done(self):
        return self.is_done

    def register_done_event(self, callback):
        self.register_done_event_calls.append(callback)
        if self.register_exception:
            raise self.register_exception


class _TaskFactory:
    def __init__(self):
        self.created = []
        self.queued = []

    def queue(self, task):
        self.queued.append(task)

    def __call__(self):
        task = self.queued.pop(0) if self.queued else _FakeTask()
        self.created.append(task)
        return task


class _FakeLock:
    def __init__(self, locked=False):
        self._locked = locked
        self.acquire_calls = 0
        self.release_calls = 0

    def acquire(self):
        self.acquire_calls += 1
        self._locked = True

    def release(self):
        self.release_calls += 1
        self._locked = False

    def locked(self):
        return self._locked


class _FakeResettableDevice:
    def __init__(self, name, raise_reset=False):
        self.name = name
        self.raise_reset = raise_reset
        self.reset_calls = 0

    def reset_device(self):
        self.reset_calls += 1
        if self.raise_reset:
            raise RuntimeError("reset failed")


class _FakeSystem:
    devices = []

    @staticmethod
    def local():
        return types.SimpleNamespace(devices=_FakeSystem.devices)


@pytest.fixture
def ni_module(monkeypatch):
    task_factory = _TaskFactory()

    nidaqmx_module = types.ModuleType(NIDAQMX_MODULE_PATH)
    nidaqmx_module.Task = task_factory
    nidaqmx_module.DaqError = _FakeDaqError
    nidaqmx_module.errors = types.SimpleNamespace(DaqError=_FakeDaqError)

    constants_module = types.ModuleType(NIDAQMX_CONSTANTS_PATH)
    constants_module.AcquisitionType = _FakeAcquisitionType
    constants_module.LineGrouping = _FakeLineGrouping

    task_module = types.ModuleType(NIDAQMX_TASK_PATH)

    system_module = types.ModuleType(NIDAQMX_SYSTEM_PATH)
    system_module.System = _FakeSystem

    nidaqmx_module.constants = constants_module
    nidaqmx_module.task = task_module
    nidaqmx_module.system = system_module

    monkeypatch.setitem(sys.modules, NIDAQMX_MODULE_PATH, nidaqmx_module)
    monkeypatch.setitem(sys.modules, NIDAQMX_CONSTANTS_PATH, constants_module)
    monkeypatch.setitem(sys.modules, NIDAQMX_TASK_PATH, task_module)
    monkeypatch.setitem(sys.modules, NIDAQMX_SYSTEM_PATH, system_module)

    _FakeSystem.devices = []
    sys.modules.pop(MODULE_PATH, None)
    module = importlib.import_module(MODULE_PATH)
    module = importlib.reload(module)
    return module, task_factory, _FakeSystem


def _build_configuration():
    return {
        "waveform_constants": {"other_constants": {"camera_delay": 5}},
        "waveform_templates": {
            "Default": {"repeat": 1, "expand": 1},
            "FromState": {"repeat": "repeat_key", "expand": "expand_key"},
        },
        "experiment": {
            "MicroscopeState": {
                "microscope_name": "ScopeA",
                "waveform_template": "Default",
                "repeat_key": 3,
                "expand_key": 2,
                "channels": {"channel_1": {"is_selected": True}},
            }
        },
        "configuration": {
            "microscopes": {
                "ScopeA": {
                    "daq": {
                        "sample_rate": 100,
                        "trigger_source": "/ScopeA/PFI0",
                        "camera_trigger_out_line": "Dev1/ctr0",
                        "master_trigger_out_line": "Dev1/port0/line0",
                        "trigger_reset_count": 2,
                        "laser_port_switcher": "Dev1/port1/line0",
                        "laser_switch_state": True,
                    }
                },
                "ScopeB": {
                    "daq": {
                        "sample_rate": 200,
                        "trigger_source": "/ScopeB/PFI0",
                        "camera_trigger_out_line": "Dev2/ctr0",
                        "master_trigger_out_line": "Dev2/port0/line0",
                        "trigger_reset_count": 3,
                        "laser_port_switcher": "Dev2/port1/line0",
                        "laser_switch_state": False,
                    }
                },
            }
        },
    }


def _build_ni_daq(module):
    daq = module.NIDAQ(_build_configuration())
    daq.sweep_times = {"channel_1": 0.1}
    daq.exposure_times = {"channel_1": 0.05}
    return daq


def test_initialize_daq_ni_defaults(ni_module):
    module, _, _ = ni_module
    daq = _build_ni_daq(module)

    assert str(daq) == "NIDAQ"
    assert daq.sample_rate == 100
    assert daq.trigger_mode == "self-trigger"
    assert daq.trigger_count == 0


def test_initialize_daq_ni_loads_active_scope_trigger_reset_count(ni_module):
    module, _, _ = ni_module
    daq = _build_ni_daq(module)

    assert daq.trigger_reset_count == 2


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        (500, 500),
        ("500", 500),
        (0, None),
        ("0", None),
        ("", None),
        (None, None),
        (-1, None),
        (True, None),
        (1.9, None),
        (float("inf"), None),
        ("invalid", None),
    ],
)
def test_enable_microscope_normalizes_trigger_reset_count(
    ni_module, raw_value, expected
):
    module, _, _ = ni_module
    configuration = _build_configuration()
    configuration["configuration"]["microscopes"]["ScopeA"]["daq"][
        "trigger_reset_count"
    ] = raw_value
    daq = module.NIDAQ(configuration)

    daq.enable_microscope("ScopeA")

    assert daq.trigger_reset_count == expected


def test_enable_microscope_refreshes_active_scope_trigger_reset_count(ni_module):
    module, _, _ = ni_module
    configuration = _build_configuration()
    daq = module.NIDAQ(configuration)
    configuration["configuration"]["microscopes"]["ScopeA"]["daq"][
        "trigger_reset_count"
    ] = 10

    daq.enable_microscope("ScopeA")

    assert daq.trigger_reset_count == 10


def test_wait_for_external_trigger_without_channel_returns_false(ni_module):
    module, _, _ = ni_module
    assert module.NIDAQ.wait_for_external_trigger("") is False


def test_wait_for_external_trigger_detects_trigger(ni_module, monkeypatch):
    module, task_factory, _ = ni_module
    task = _FakeTask(read_sequence=[False, False, True])
    task_factory.queue(task)
    monkeypatch.setattr(module.time, "sleep", lambda *_: None)

    result = module.NIDAQ.wait_for_external_trigger(
        trigger_channel="Dev1/PFI0", wait_internal=0.01, timeout=0.5
    )

    assert result is True
    assert task.di_channels.calls == ["Dev1/PFI0"]
    assert task.stop_calls == 1
    assert task.close_calls == 1


def test_wait_for_external_trigger_times_out(ni_module, monkeypatch):
    module, task_factory, _ = ni_module
    task = _FakeTask(read_sequence=[False])
    task_factory.queue(task)
    monkeypatch.setattr(module.time, "sleep", lambda *_: None)

    result = module.NIDAQ.wait_for_external_trigger(
        trigger_channel="Dev1/PFI1", wait_internal=0.01, timeout=0.02
    )

    assert result is False
    assert task.stop_calls == 1
    assert task.close_calls == 1


def test_restart_analog_task_callback_restarts_task(ni_module):
    module, _, _ = ni_module
    task = _FakeTask()
    callback = module.NIDAQ.restart_analog_task_callback_func(task)

    status = callback(None, 7, None)

    assert status == 7
    assert task.stop_calls == 1
    assert task.start_calls == 1


def test_restart_analog_task_callback_handles_exception(ni_module):
    module, _, _ = ni_module
    task = _FakeTask()
    task.stop_exception = RuntimeError("stop failed")
    callback = module.NIDAQ.restart_analog_task_callback_func(task)

    status = callback(None, 3, None)

    assert status == 3
    assert task.start_calls == 0


def test_create_camera_task_with_analog_outputs(ni_module):
    module, task_factory, _ = ni_module
    daq = _build_ni_daq(module)
    daq.analog_outputs = {"Dev1/ao0": {"waveform": {"channel_1": np.arange(10)}}}
    camera_task = _FakeTask()
    task_factory.queue(camera_task)

    daq.create_camera_task("channel_1")

    pulse_call = camera_task.co_channels.calls[0]
    assert pulse_call["channel"] == "Dev1/ctr0"
    assert pulse_call["high_time"] == pytest.approx(0.004)
    assert pulse_call["low_time"] == pytest.approx(0.096)
    assert pulse_call["initial_delay"] == pytest.approx(0.005)
    assert camera_task.timing.implicit_calls[0]["samps_per_chan"] == 1


def test_create_camera_task_without_analog_single_repeat(ni_module):
    module, task_factory, _ = ni_module
    daq = _build_ni_daq(module)
    daq.analog_outputs = {}
    daq.waveform_repeat_num = 1
    daq.waveform_expand_num = 1
    camera_task = _FakeTask()
    task_factory.queue(camera_task)

    daq.create_camera_task("channel_1")

    pulse_call = camera_task.co_channels.calls[0]
    assert pulse_call["high_time"] == pytest.approx(0.095)
    assert pulse_call["low_time"] == pytest.approx(0.004)
    assert camera_task.timing.implicit_calls[0]["samps_per_chan"] == 1


def test_create_camera_task_without_analog_multiple_repeats(ni_module):
    module, task_factory, _ = ni_module
    daq = _build_ni_daq(module)
    daq.analog_outputs = {}
    daq.waveform_repeat_num = 2
    daq.waveform_expand_num = 1
    camera_task = _FakeTask()
    task_factory.queue(camera_task)

    daq.create_camera_task("channel_1")

    pulse_call = camera_task.co_channels.calls[0]
    assert pulse_call["high_time"] == pytest.approx(0.096)
    assert pulse_call["low_time"] == pytest.approx(0.004)
    assert camera_task.timing.implicit_calls[0]["samps_per_chan"] == 2


def test_create_master_trigger_task(ni_module):
    module, task_factory, _ = ni_module
    daq = _build_ni_daq(module)
    master_task = _FakeTask()
    task_factory.queue(master_task)

    daq.create_master_trigger_task()

    assert daq.master_trigger_task is master_task
    assert master_task.do_channels.calls[0]["channel"] == "Dev1/port0/line0"
    assert (
        master_task.do_channels.calls[0]["line_grouping"]
        == module.nidaqmx.constants.LineGrouping.CHAN_FOR_ALL_LINES
    )


def test_create_analog_output_tasks_uses_expand_and_board_grouping(ni_module):
    module, task_factory, _ = ni_module
    daq = _build_ni_daq(module)
    daq.sample_rate = 10
    daq.waveform_expand_num = 2
    daq.waveform_repeat_num = 2
    daq.sweep_times = {"channel_1": 0.5}
    daq.analog_outputs = {
        "Dev1/ao0": {
            "waveform": {"channel_1": np.array([1, 2, 3, 4, 5])},
            "trigger_source": "/Dev1/PFI0",
            "sample_rate": 10,
            "samples": 5,
        },
        "Dev1/ao1": {
            "waveform": {"channel_1": np.arange(10) + 10},
            "trigger_source": "/Dev1/PFI0",
            "sample_rate": 10,
            "samples": 10,
        },
        "Dev2/ao0": {
            "waveform": {"channel_1": np.arange(10) + 20},
            "trigger_source": "/Dev2/PFI0",
            "sample_rate": 10,
            "samples": 10,
        },
    }
    task_factory.queue(_FakeTask())
    task_factory.queue(_FakeTask())

    daq.create_analog_output_tasks("channel_1")

    assert daq.n_sample == 5
    assert set(daq.analog_output_tasks.keys()) == {"Dev1", "Dev2"}
    np.testing.assert_array_equal(
        daq.analog_outputs["Dev1/ao0"]["waveform"]["channel_1"],
        np.array([1, 2, 3, 4, 5, 1, 2, 3, 4, 5]),
    )

    dev1_written = daq.analog_output_tasks["Dev1"].write_calls[0]["data"]
    dev2_written = daq.analog_output_tasks["Dev2"].write_calls[0]["data"]
    assert dev1_written.shape == (2, 10)
    assert dev2_written.shape == (10,)
    assert (
        daq.analog_output_tasks["Dev1"].timing.sample_clock_calls[0]["samps_per_chan"]
        == 20
    )


def test_prepare_acquisition_sets_up_tasks_and_releases_lock(ni_module):
    module, task_factory, _ = ni_module
    daq = _build_ni_daq(module)
    daq.analog_outputs = {
        "Dev1/ao0": {
            "waveform": {"channel_1": np.arange(10)},
            "trigger_source": "/Dev1/PFI0",
            "sample_rate": 100,
            "samples": 10,
        }
    }
    daq.wait_to_run_lock.acquire()
    task_factory.queue(_FakeTask())  # camera
    task_factory.queue(_FakeTask())  # analog
    task_factory.queue(_FakeTask())  # master

    daq.prepare_acquisition("channel_1")

    assert daq.current_channel_key == "channel_1"
    assert daq.waveform_repeat_num == 1
    assert daq.waveform_expand_num == 1
    assert daq.trigger_mode == "self-trigger"
    assert not daq.wait_to_run_lock.locked()
    assert (
        daq.camera_trigger_task.triggers.start_trigger.cfg_calls[-1] == "/ScopeA/PFI0"
    )
    assert (
        daq.analog_output_tasks["Dev1"].triggers.start_trigger.cfg_calls[-1]
        == "/ScopeA/PFI0"
    )


def test_set_external_trigger_self_trigger_handles_task_exceptions(ni_module):
    module, task_factory, _ = ni_module
    daq = _build_ni_daq(module)
    daq.camera_trigger_task = _FakeTask()
    daq.camera_trigger_task.stop_exception = RuntimeError("camera stop failed")
    analog_task = _FakeTask()
    analog_task.stop_exception = RuntimeError("analog stop failed")
    analog_task.register_exception = RuntimeError("register failed")
    daq.analog_output_tasks = {"Dev1": analog_task}
    task_factory.queue(_FakeTask())  # master trigger task

    daq.set_external_trigger(None)

    assert daq.trigger_mode == "self-trigger"
    assert daq.master_trigger_task is not None
    assert (
        daq.camera_trigger_task.triggers.start_trigger.cfg_calls[-1] == "/ScopeA/PFI0"
    )
    assert analog_task.triggers.start_trigger.cfg_calls[-1] == "/ScopeA/PFI0"
    assert analog_task.register_done_event_calls[0] is None
    daq.camera_trigger_task.stop_exception = None
    analog_task.stop_exception = None
    daq.camera_trigger_task = None
    daq.master_trigger_task = None
    daq.analog_output_tasks = {}


def test_set_external_trigger_external_mode_reconfigures_tasks(ni_module):
    module, _, _ = ni_module
    daq = _build_ni_daq(module)
    daq.master_trigger_task = _FakeTask()
    daq.camera_trigger_task = _FakeTask()
    analog_task = _FakeTask()
    daq.analog_output_tasks = {"Dev1": analog_task}

    daq.set_external_trigger("/External/PFI7")

    assert daq.trigger_mode == "external-trigger"
    assert daq.external_trigger == "/External/PFI7"
    assert daq.master_trigger_task is None
    assert (
        daq.camera_trigger_task.triggers.start_trigger.cfg_calls[-1] == "/External/PFI7"
    )
    assert daq.camera_trigger_task.triggers.start_trigger.retriggerable is False
    assert analog_task.triggers.start_trigger.cfg_calls[-1] == "/External/PFI7"
    assert analog_task.register_done_event_calls[0] is None
    assert callable(analog_task.register_done_event_calls[1])


def test_run_acquisition_starts_tasks_and_writes_master_trigger(ni_module):
    module, _, _ = ni_module
    daq = _build_ni_daq(module)
    camera_task = _FakeTask()
    analog_task = _FakeTask()
    master_task = _FakeTask()
    fake_lock = _FakeLock()
    daq.camera_trigger_task = camera_task
    daq.analog_output_tasks = {"Dev1": analog_task}
    daq.master_trigger_task = master_task
    daq.wait_to_run_lock = fake_lock
    daq.is_updating_analog_task = True
    calls = {"wait": 0}
    daq.wait_acquisition_done = lambda: calls.__setitem__("wait", calls["wait"] + 1)

    daq.run_acquisition(wait_until_done=True)

    assert fake_lock.acquire_calls == 1
    assert fake_lock.release_calls == 1
    assert camera_task.start_calls == 1
    assert analog_task.start_calls == 1
    assert master_task.write_calls[0]["data"].tolist() == [
        False,
        True,
        True,
        True,
        False,
    ]
    assert master_task.write_calls[0]["auto_start"] is True
    assert calls["wait"] == 1
    assert daq.trigger_count == 1


def test_run_acquisition_skips_starts_when_camera_task_not_done(ni_module):
    module, _, _ = ni_module
    daq = _build_ni_daq(module)
    camera_task = _FakeTask()
    camera_task.is_done = False
    analog_task = _FakeTask()
    daq.camera_trigger_task = camera_task
    daq.analog_output_tasks = {"Dev1": analog_task}
    daq.trigger_mode = "external-trigger"

    daq.run_acquisition(wait_until_done=False)

    assert camera_task.start_calls == 0
    assert analog_task.start_calls == 0
    assert daq.trigger_count == 1


def test_wait_acquisition_done_stops_all_tasks(ni_module):
    module, _, _ = ni_module
    daq = _build_ni_daq(module)
    camera_task = _FakeTask()
    analog_task = _FakeTask()
    master_task = _FakeTask()
    daq.camera_trigger_task = camera_task
    daq.analog_output_tasks = {"Dev1": analog_task}
    daq.master_trigger_task = master_task
    daq.trigger_mode = "self-trigger"

    daq.wait_acquisition_done()

    assert camera_task.wait_calls == [10000]
    assert analog_task.wait_calls == [None]
    assert analog_task.stop_calls == 1
    assert camera_task.stop_calls == 1
    assert master_task.stop_calls == 1


def test_wait_acquisition_done_handles_errors_and_reset_cycle(ni_module):
    module, _, _ = ni_module
    daq = _build_ni_daq(module)
    camera_task = _FakeTask()
    camera_task.wait_exception = RuntimeError("wait failed")
    daq.camera_trigger_task = camera_task
    daq.master_trigger_task = _FakeTask()
    daq.trigger_mode = "self-trigger"
    daq.trigger_reset_count = 1
    daq.trigger_count = 1
    daq.current_channel_key = "channel_1"
    calls = {"stop": 0, "prepare": 0}
    daq.stop_acquisition = lambda: calls.__setitem__("stop", calls["stop"] + 1)
    daq.prepare_acquisition = lambda channel: calls.__setitem__(
        "prepare", calls["prepare"] + (1 if channel == "channel_1" else 0)
    )

    daq.wait_acquisition_done()

    assert calls["stop"] == 1
    assert calls["prepare"] == 1


def test_stop_acquisition_closes_tasks_and_calls_reset(ni_module):
    module, _, _ = ni_module
    daq = _build_ni_daq(module)
    daq.camera_trigger_task = _FakeTask()
    daq.master_trigger_task = _FakeTask()
    daq.analog_output_tasks = {"Dev1": _FakeTask(), "Dev2": _FakeTask()}
    daq.trigger_mode = "self-trigger"
    daq.wait_to_run_lock.acquire()
    daq.trigger_reset_count = 1
    daq.trigger_count = 1
    calls = {"reset": 0}
    daq.reset = lambda: calls.__setitem__("reset", calls["reset"] + 1)

    daq.stop_acquisition()

    assert daq.camera_trigger_task.stop_calls == 1
    assert daq.camera_trigger_task.close_calls == 1
    assert daq.master_trigger_task.stop_calls == 1
    assert daq.master_trigger_task.close_calls == 1
    assert daq.analog_output_tasks == {}
    assert calls["reset"] == 1
    assert daq.trigger_count == 0
    assert not daq.wait_to_run_lock.locked()


def test_stop_acquisition_handles_missing_or_invalid_tasks(ni_module):
    module, _, _ = ni_module
    daq = _build_ni_daq(module)
    daq.camera_trigger_task = None
    daq.analog_output_tasks = {}

    daq.stop_acquisition()

    assert daq.analog_output_tasks == {}


def test_enable_microscope_switches_scope_and_laser_task(ni_module):
    module, task_factory, _ = ni_module
    daq = _build_ni_daq(module)
    daq.analog_outputs = {"Dev1/ao0": {"waveform": {"channel_1": np.arange(5)}}}
    daq.analog_output_tasks = {"Dev1": _FakeTask()}
    existing_switch_task = _FakeTask()
    daq.laser_switching_task = existing_switch_task
    new_switch_task = _FakeTask()
    task_factory.queue(new_switch_task)

    daq.enable_microscope("ScopeB")

    assert daq.microscope_name == "ScopeB"
    assert daq.sample_rate == 200
    assert daq.trigger_reset_count == 3
    assert daq.analog_outputs == {}
    assert daq.analog_output_tasks == {}
    assert existing_switch_task.close_calls == 1
    assert new_switch_task.do_channels.calls[0]["channel"] == "Dev2/port1/line0"
    assert new_switch_task.write_calls[0]["data"].item() is False


def test_enable_microscope_without_laser_switch_settings_is_noop(ni_module):
    module, _, _ = ni_module
    config = _build_configuration()
    config["configuration"]["microscopes"]["ScopeA"]["daq"].pop("laser_port_switcher")
    config["configuration"]["microscopes"]["ScopeA"]["daq"].pop("laser_switch_state")
    daq = module.NIDAQ(config)

    daq.enable_microscope("ScopeA")

    assert daq.sample_rate == 100
    assert daq.laser_switching_task is None


def test_update_analog_task_returns_false_for_missing_or_busy(ni_module):
    module, _, _ = ni_module
    daq = _build_ni_daq(module)

    assert daq.update_analog_task("Dev1") is False

    daq.analog_output_tasks["Dev1"] = _FakeTask()
    daq.is_updating_analog_task = True
    assert daq.update_analog_task("Dev1") is False


def test_update_analog_task_success_writes_new_waveforms(ni_module):
    module, _, _ = ni_module
    daq = _build_ni_daq(module)
    daq.current_channel_key = "channel_1"
    daq.n_sample = 4
    daq.wait_to_run_lock = _FakeLock()
    daq.analog_outputs = {
        "Dev1/ao0": {"waveform": {"channel_1": np.array([1, 2, 3, 4, 5])}},
        "Dev1/ao1": {"waveform": {"channel_1": np.array([6, 7, 8, 9, 10])}},
    }
    board_task = _FakeTask()
    daq.analog_output_tasks = {"Dev1": board_task}

    result = daq.update_analog_task("Dev1")

    assert result is True
    assert board_task.wait_calls == [1.0]
    assert board_task.stop_calls == 1
    assert board_task.write_calls[0]["data"].shape == (2, 4)
    assert daq.wait_to_run_lock.acquire_calls == 1
    assert daq.wait_to_run_lock.release_calls == 1
    assert daq.is_updating_analog_task is False


def test_update_analog_task_recreates_tasks_when_update_fails(ni_module):
    module, _, _ = ni_module
    daq = _build_ni_daq(module)
    daq.current_channel_key = "channel_1"
    daq.n_sample = 4
    daq.wait_to_run_lock = _FakeLock()
    daq.analog_outputs = {
        "Dev1/ao0": {"waveform": {"channel_1": np.array([1, 2, 3, 4, 5])}}
    }
    failing_task = _FakeTask()
    failing_task.wait_exception = RuntimeError("wait failed")
    other_task = _FakeTask()
    daq.analog_output_tasks = {"Dev1": failing_task, "Dev2": other_task}
    calls = {"create": 0}
    daq.create_analog_output_tasks = lambda key: calls.__setitem__(
        "create", calls["create"] + (1 if key == "channel_1" else 0)
    )

    result = daq.update_analog_task("Dev1")

    assert result is True
    assert calls["create"] == 1
    assert failing_task.stop_calls == 1
    assert failing_task.close_calls == 1
    assert other_task.stop_calls == 1
    assert other_task.close_calls == 1
    assert daq.is_updating_analog_task is False


def test_reset_clears_tasks_and_resets_devices(ni_module):
    module, _, fake_system = ni_module
    daq = _build_ni_daq(module)
    daq.analog_output_tasks = {"Dev1": _FakeTask(), "Dev2": _FakeTask()}
    daq.camera_trigger_task = _FakeTask()
    daq.master_trigger_task = _FakeTask()
    dev1 = _FakeResettableDevice("Dev1")
    dev2 = _FakeResettableDevice("Dev2", raise_reset=True)
    fake_system.devices = [dev1, dev2]

    daq.reset(device_name="Dev1")
    daq.reset()

    assert dev1.reset_calls == 2
    assert dev2.reset_calls == 1
    assert daq.analog_output_tasks == {}
    assert not hasattr(daq, "camera_trigger_task")
    assert not hasattr(daq, "master_trigger_task")
    daq.camera_trigger_task = None
    daq.master_trigger_task = None


def test_del_closes_all_tasks_and_handles_stop_errors(ni_module):
    module, _, _ = ni_module
    daq = _build_ni_daq(module)
    camera = _FakeTask()
    camera.stop_exception = RuntimeError("stop failed")
    master = _FakeTask()
    laser = _FakeTask()
    analog = _FakeTask()
    daq.camera_trigger_task = camera
    daq.master_trigger_task = master
    daq.laser_switching_task = laser
    daq.analog_output_tasks = {"Dev1": analog}
    calls = {"count": 0}

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            module.logger,
            "exception",
            lambda *_: calls.__setitem__("count", calls["count"] + 1),
        )
        daq.__del__()

    assert calls["count"] == 1
    assert master.stop_calls == 1
    assert master.close_calls == 1
    assert laser.stop_calls == 1
    assert laser.close_calls == 1
    assert analog.stop_calls == 1
    assert analog.close_calls == 1
    daq.camera_trigger_task = None
    daq.master_trigger_task = None
    daq.laser_switching_task = None
    daq.analog_output_tasks = {}
