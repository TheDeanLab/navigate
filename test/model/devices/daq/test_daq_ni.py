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

# Standard Library Imports

# Third Party Imports
import numpy as np
import pytest

# Local Imports


@pytest.mark.hardware
def test_initialize_daq_ni():
    from navigate.model.devices.daq.ni import NIDAQ
    from test.model.dummy import DummyModel

    model = DummyModel()
    daq = NIDAQ(model.configuration)
    daq.camera_trigger_task = None


@pytest.mark.hardware
def test_daq_ni_functions():
    from navigate.model.devices.daq.ni import NIDAQ
    from test.model.dummy import DummyModel

    model = DummyModel()
    daq = NIDAQ(model.configuration)
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]

    funcs = [
        "enable_microscope",
        "prepare_acquisition",
        "run_acquisition",
        "stop_acquisition",
    ]
    args = [
        [microscope_name],
        [list(daq.waveform_dict.keys())[0]],
        None,
        None,
    ]

    for f, a in zip(funcs, args):
        if a is not None:
            getattr(daq, f)(*a)
        else:
            getattr(daq, f)()


class _FakeAOChannels:
    def __init__(self):
        self.add_ao_voltage_chan_calls = []

    def add_ao_voltage_chan(self, channel):
        self.add_ao_voltage_chan_calls.append(channel)


class _FakeTiming:
    def __init__(self):
        self.cfg_samp_clk_timing_calls = []

    def cfg_samp_clk_timing(self, rate, sample_mode, samps_per_chan):
        self.cfg_samp_clk_timing_calls.append(
            {
                "rate": rate,
                "sample_mode": sample_mode,
                "samps_per_chan": samps_per_chan,
            }
        )


class _FakeTask:
    def __init__(self):
        self.ao_channels = _FakeAOChannels()
        self.timing = _FakeTiming()
        self.write_calls = []

    def write(self, data):
        self.write_calls.append(np.asarray(data))

    def stop(self):
        pass

    def close(self):
        pass


def test_create_analog_output_tasks_uses_channel_sweep_time(monkeypatch):
    from navigate.model.devices.daq.ni import NIDAQ
    from test.model.dummy import DummyModel

    model = DummyModel()
    daq = NIDAQ(model.configuration)
    daq.sample_rate = 10
    daq.sweep_times = {"channel_1": 0.7}
    daq.waveform_repeat_num = 1
    daq.waveform_expand_num = 1
    daq.analog_outputs = {
        "PXI6259/ao0": {
            "sample_rate": 5000,
            "samples": 2,
            "trigger_source": "/PXI6259/PFI0",
            "waveform": {"channel_1": np.arange(7)},
        },
        "PXI6259/ao1": {
            "sample_rate": 2000,
            "samples": 2,
            "trigger_source": "/PXI6259/PFI0",
            "waveform": {"channel_1": np.arange(7) + 10},
        },
    }
    monkeypatch.setattr("navigate.model.devices.daq.ni.nidaqmx.Task", _FakeTask)

    daq.create_analog_output_tasks("channel_1")

    assert daq.n_sample == 7
    task = daq.analog_output_tasks["PXI6259"]
    timing_call = task.timing.cfg_samp_clk_timing_calls[0]
    assert timing_call["rate"] == daq.sample_rate
    assert timing_call["samps_per_chan"] == 7
    assert task.write_calls[0].shape == (2, 7)


def test_create_analog_output_tasks_expands_based_on_waveform_length(monkeypatch):
    from navigate.model.devices.daq.ni import NIDAQ
    from test.model.dummy import DummyModel

    model = DummyModel()
    daq = NIDAQ(model.configuration)
    daq.sample_rate = 10
    daq.sweep_times = {"channel_1": 0.5}
    daq.waveform_repeat_num = 1
    daq.waveform_expand_num = 2
    daq.analog_outputs = {
        "PXI6259/ao0": {
            "sample_rate": 5000,
            "samples": 999,
            "trigger_source": "/PXI6259/PFI0",
            "waveform": {"channel_1": np.array([1, 2, 3, 4, 5])},
        },
        "PXI6259/ao1": {
            "sample_rate": 2000,
            "samples": 999,
            "trigger_source": "/PXI6259/PFI0",
            "waveform": {
                "channel_1": np.array(
                    [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
                ),
            },
        },
    }
    monkeypatch.setattr("navigate.model.devices.daq.ni.nidaqmx.Task", _FakeTask)

    daq.create_analog_output_tasks("channel_1")

    expected_waveform = np.array([1, 2, 3, 4, 5, 1, 2, 3, 4, 5])
    np.testing.assert_array_equal(
        daq.analog_outputs["PXI6259/ao0"]["waveform"]["channel_1"],
        expected_waveform,
    )
    task = daq.analog_output_tasks["PXI6259"]
    assert task.write_calls[0].shape == (2, 10)
