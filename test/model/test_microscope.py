# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
#

import pytest
import random


@pytest.fixture(scope="module")
def dummy_microscope(dummy_model):
    from navigate.model.microscope import Microscope
    from navigate.model.device_startup_functions import load_devices

    devices_dict = load_devices(dummy_model.configuration, is_synthetic=True)

    return Microscope(
        dummy_model.active_microscope_name,
        dummy_model.configuration,
        devices_dict,
        is_synthetic=True,
        is_virtual=False,
    )


def test_prepare_acquisition(dummy_microscope):
    waveform_dict = dummy_microscope.prepare_acquisition()

    channels = dummy_microscope.configuration["experiment"]["MicroscopeState"][
        "channels"
    ]

    assert dummy_microscope.current_channel == 0
    assert dummy_microscope.central_focus is None
    assert dummy_microscope.available_channels == list(
        map(
            lambda c: int(c[len("channel_") :]),
            filter(lambda k: channels[k]["is_selected"], channels.keys()),
        )
    )
    assert dummy_microscope.camera.is_acquiring is True
    assert dummy_microscope.shutter.shutter_state is True
    assert isinstance(waveform_dict, dict)
    assert [
        k in waveform_dict.keys()
        for k in ["camera_waveform", "remote_focus_waveform", "galvo_waveform"]
    ]


def test_get_stage_position(dummy_microscope):
    import numpy as np

    pos_dict = {
        f"{k}_abs": v
        for k, v in zip(["x", "y", "z", "theta", "f"], np.random.rand(5) * 100)
    }
    dummy_microscope.move_stage(pos_dict, wait_until_done=True)

    assert dummy_microscope.ask_stage_for_position is True

    stage_dict = dummy_microscope.get_stage_position()

    ret_pos_dict = {}
    for axis in dummy_microscope.stages:
        pos_axis = axis + "_pos"
        temp_pos = dummy_microscope.stages[axis].report_position()
        ret_pos_dict[pos_axis] = temp_pos[pos_axis]

    assert isinstance(stage_dict, dict)
    assert ret_pos_dict == stage_dict

    # Check caching
    stage_dict = dummy_microscope.get_stage_position()
    assert ret_pos_dict == stage_dict
    assert dummy_microscope.ask_stage_for_position is False


def test_prepare_next_channel(dummy_microscope):
    dummy_microscope.prepare_acquisition()

    current_channel = dummy_microscope.available_channels[0]
    channel_key = f"channel_{current_channel}"
    channel_dict = dummy_microscope.configuration["experiment"]["MicroscopeState"][
        "channels"
    ][channel_key]
    channel_dict["defocus"] = random.randint(1, 10)

    dummy_microscope.prepare_next_channel()

    assert dummy_microscope.current_channel == current_channel
    assert dummy_microscope.get_stage_position()["f_pos"] == (
        dummy_microscope.central_focus + channel_dict["defocus"]
    )


def test_calculate_all_waveform(dummy_microscope):
    # set waveform template to default
    dummy_microscope.configuration["experiment"]["MicroscopeState"][
        "waveform_template"
    ] = "Default"
    waveform_dict = dummy_microscope.calculate_all_waveform()
    # verify the waveform lengths
    sweep_times = dummy_microscope.sweep_times
    sample_rate = dummy_microscope.configuration["configuration"]["microscopes"][
        dummy_microscope.microscope_name
    ]["daq"]["sample_rate"]
    for channel_key in sweep_times:
        waveform_length = int(sweep_times[channel_key] * sample_rate)
        assert waveform_dict["camera_waveform"][channel_key].shape == (waveform_length,)
        assert waveform_dict["remote_focus_waveform"][channel_key].shape == (
            waveform_length,
        )
        for i in range(len(waveform_dict["galvo_waveform"])):
            assert waveform_dict["galvo_waveform"][i][channel_key].shape == (
                waveform_length,
            )
