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

from unittest.mock import patch

import numpy as np
import pytest

import navigate.model.devices.galvo.base as galvo_base_module
from navigate.model.devices.galvo.synthetic import SyntheticGalvo


def build_base_configuration(
    *,
    waveform="sawtooth",
    galvo_factor="none",
    amplitude="1.0",
    offset="0.0",
    frequency="2.0",
    rising_ramp="50",
    phase=0.0,
    max_voltage=5.0,
    min_voltage=-5.0,
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
                                "max": max_voltage,
                                "min": min_voltage,
                                "channel": "Dev1/ao0",
                                "axis": "B",
                            },
                            "waveform": waveform,
                            "phase": phase,
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
                "Galvo 0": {"TestScope": {"1x": galvo_parameters}},
            },
        },
    }


def build_synthetic_galvo(configuration):
    return SyntheticGalvo(
        microscope_name="TestScope",
        device_connection=None,
        configuration=configuration,
        device_id=0,
    )


def default_timing():
    exposure_times = {"channel_1": 0.2, "channel_2": 0.2}
    sweep_times = {"channel_1": 0.2, "channel_2": 0.2}
    return exposure_times, sweep_times


def test_adjust_applies_channel_factor_override():
    config = build_base_configuration(
        galvo_factor="channel",
        max_voltage=10,
        min_voltage=-10,
        channel_overrides={"Channel 1": {"amplitude": "3.0", "offset": "1.5"}},
    )
    galvo = build_synthetic_galvo(config)
    exposure_times, sweep_times = default_timing()

    with patch(
        "navigate.model.devices.galvo.base.sawtooth",
        side_effect=lambda **kwargs: np.array(
            [kwargs["amplitude"], kwargs["offset"]], dtype=float
        ),
    ) as mock_sawtooth:
        waveforms = galvo.adjust(exposure_times, sweep_times)

    assert mock_sawtooth.call_args_list[0].kwargs["amplitude"] == pytest.approx(3.0)
    assert mock_sawtooth.call_args_list[0].kwargs["offset"] == pytest.approx(1.5)
    assert mock_sawtooth.call_args_list[1].kwargs["amplitude"] == pytest.approx(1.0)
    assert mock_sawtooth.call_args_list[1].kwargs["offset"] == pytest.approx(0.0)
    assert set(waveforms.keys()) == {"channel_1", "channel_2"}


@pytest.mark.parametrize(
    "waveform, function_name",
    [
        ("quadratic", "quadratic"),
        ("centered_cubic", "centered_cubic"),
    ],
)
def test_adjust_dispatches_curved_waveforms(waveform, function_name):
    config = build_base_configuration(
        waveform=waveform,
        max_voltage=10,
        min_voltage=-10,
        channel_2_selected=False,
    )
    galvo = build_synthetic_galvo(config)
    exposure_times, sweep_times = default_timing()

    with patch(
        f"navigate.model.devices.galvo.base.{function_name}",
        return_value=np.array([0.1, 0.2], dtype=float),
    ) as mock_waveform:
        waveforms = galvo.adjust(exposure_times, sweep_times)

    mock_waveform.assert_called_once()
    assert waveforms["channel_1"].tolist() == [0.1, 0.2]


def test_adjust_applies_laser_factor_override_for_sine():
    config = build_base_configuration(
        waveform="sine",
        galvo_factor="laser",
        max_voltage=10,
        min_voltage=-10,
        phase=1.23,
        laser_overrides={"488": {"amplitude": "2.5", "offset": "-0.4"}},
    )
    galvo = build_synthetic_galvo(config)
    exposure_times, sweep_times = default_timing()

    with patch(
        "navigate.model.devices.galvo.base.sine_wave",
        side_effect=lambda **kwargs: np.array(
            [kwargs["amplitude"], kwargs["offset"], kwargs["phase"]], dtype=float
        ),
    ) as mock_sine_wave:
        waveforms = galvo.adjust(exposure_times, sweep_times)

    assert mock_sine_wave.call_args_list[0].kwargs["amplitude"] == pytest.approx(2.5)
    assert mock_sine_wave.call_args_list[0].kwargs["offset"] == pytest.approx(-0.4)
    assert mock_sine_wave.call_args_list[0].kwargs["phase"] == pytest.approx(1.23)
    assert mock_sine_wave.call_args_list[1].kwargs["amplitude"] == pytest.approx(1.0)
    assert mock_sine_wave.call_args_list[1].kwargs["offset"] == pytest.approx(0.0)
    assert set(waveforms.keys()) == {"channel_1", "channel_2"}


@pytest.mark.parametrize(
    "amplitude, source_wave",
    [
        (1.0, np.array([0.25, 0.9, -0.1], dtype=float)),
        (-1.0, np.array([0.25, -0.9, 0.4], dtype=float)),
    ],
)
def test_adjust_halfsaw_uses_expected_extreme(amplitude, source_wave):
    config = build_base_configuration(
        waveform="halfsaw",
        amplitude=str(amplitude),
        offset="0.5",
        max_voltage=10,
        min_voltage=-10,
        channel_2_selected=False,
    )
    galvo = build_synthetic_galvo(config)
    exposure_times, sweep_times = default_timing()

    with patch("navigate.model.devices.galvo.base.sawtooth", return_value=source_wave):
        waveforms = galvo.adjust(exposure_times, sweep_times)

    assert waveforms["channel_1"][0] == pytest.approx(-0.5)
    assert waveforms["channel_1"][1] == pytest.approx(source_wave[1])


def test_adjust_pulse_waveform_respects_camera_delay_and_clears_final_sample():
    config = build_base_configuration(
        waveform="pulse",
        amplitude="1.0",
        offset="0.0",
        max_voltage=10,
        min_voltage=-10,
        channel_2_selected=False,
    )
    config["waveform_constants"]["other_constants"]["camera_delay"] = "10"
    config["configuration"]["microscopes"]["TestScope"]["daq"]["sample_rate"] = 1000
    waveform_constants = config.pop("waveform_constants")
    galvo = build_synthetic_galvo(config)
    config["waveform_constants"] = waveform_constants

    waveforms = galvo.adjust(
        exposure_times={"channel_1": 0.2},
        sweep_times={"channel_1": 0.1},
    )

    waveform = waveforms["channel_1"]
    high_indices = np.flatnonzero(waveform > 0.5)
    assert waveform.shape == (100,)
    assert high_indices[0] == 10
    assert high_indices[-1] == 98
    assert len(high_indices) == 89
    assert waveform[-1] == 0


def test_adjust_unknown_waveform_sets_channel_to_none():
    config = build_base_configuration(waveform="banana", channel_2_selected=False)
    galvo = build_synthetic_galvo(config)
    exposure_times, sweep_times = default_timing()

    with patch("builtins.print") as mock_print:
        waveforms = galvo.adjust(exposure_times, sweep_times)

    assert waveforms == {"channel_1": None}
    mock_print.assert_called_with(
        "Unknown Galvo waveform specified in configuration file."
    )


def test_adjust_returns_none_on_invalid_waveform_constants():
    config = build_base_configuration(
        amplitude="not-a-number", channel_2_selected=False
    )
    galvo = build_synthetic_galvo(config)
    exposure_times, sweep_times = default_timing()

    with patch.object(galvo_base_module.logger, "debug") as mock_debug:
        result = galvo.adjust(exposure_times, sweep_times)

    assert result is None
    mock_debug.assert_called_once()


def test_adjust_clips_waveform_to_voltage_limits():
    config = build_base_configuration(
        max_voltage=0.25,
        min_voltage=-0.25,
        channel_2_selected=False,
    )
    galvo = build_synthetic_galvo(config)
    exposure_times, sweep_times = default_timing()

    with patch(
        "navigate.model.devices.galvo.base.sawtooth",
        return_value=np.array([1.0, -1.0, 0.1], dtype=float),
    ):
        waveforms = galvo.adjust(exposure_times, sweep_times)

    assert np.allclose(waveforms["channel_1"], np.array([0.25, -0.25, 0.1]))


def test_adjust_resets_existing_waveforms_when_no_channels_selected():
    config = build_base_configuration(
        channel_1_selected=False, channel_2_selected=False
    )
    galvo = build_synthetic_galvo(config)
    galvo.waveform_dict = {"stale_channel": np.array([1.0], dtype=float)}
    exposure_times, sweep_times = default_timing()

    waveforms = galvo.adjust(exposure_times, sweep_times)

    assert waveforms == {"stale_channel": None}
