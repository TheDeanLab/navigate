# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
import pytest
import numpy as np

# Local Imports


def test_remote_focus_base_init():
    from navigate.model.devices.remote_focus.remote_focus_base import RemoteFocusBase
    from navigate.model.dummy import DummyModel

    model = DummyModel()
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    RemoteFocusBase(microscope_name, None, model.configuration)


@pytest.mark.parametrize("smoothing", [0] + list(np.random.rand(5) * 100))
def test_remote_focus_base_adjust(smoothing):
    from navigate.model.devices.remote_focus.remote_focus_base import RemoteFocusBase
    from navigate.model.dummy import DummyModel

    model = DummyModel()
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    microscope_state = model.configuration["experiment"]["MicroscopeState"]

    waveform_constants = model.configuration["waveform_constants"]
    imaging_mode = microscope_state["microscope_name"]
    zoom = microscope_state["zoom"]
    for channel_key in microscope_state["channels"].keys():
        # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
        channel = microscope_state["channels"][channel_key]

        # Only proceed if it is enabled in the GUI
        if channel["is_selected"] is True:
            laser = channel["laser"]
            waveform_constants["remote_focus_constants"][imaging_mode][zoom][laser][
                "percent_smoothing"
            ] = smoothing
            channel["camera_exposure_time"] = np.random.rand() * 150 + 50

    rf = RemoteFocusBase(microscope_name, None, model.configuration)

    # exposure_times = {
    #     k: v["camera_exposure_time"] / 1000
    #     for k, v in microscope_state["channels"].items()
    # }
    # sweep_times = {
    #     k: 2 * v["camera_exposure_time"] / 1000
    #     for k, v in microscope_state["channels"].items()
    # }

    (
        exposure_times,
        sweep_times,
    ) = model.active_microscope.calculate_exposure_sweep_times()

    waveform_dict = rf.adjust(exposure_times, sweep_times)

    for k, v in waveform_dict.items():
        try:
            channel = microscope_state["channels"][k]
            if not channel["is_selected"]:
                continue
            assert np.all(v <= rf.remote_focus_max_voltage)
            assert np.all(v >= rf.remote_focus_min_voltage)
            assert len(v) == int(sweep_times[k] * rf.sample_rate)
        except KeyError:
            # The channel doesn't exist. Points to an issue in how waveform dict
            # is created.
            continue
