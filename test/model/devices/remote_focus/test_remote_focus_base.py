# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

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

# Standard Library Imports

# Third Party Imports
import numpy as np

# Local Imports


def test_remote_focus_base_init():
    from aslm.model.devices.remote_focus.remote_focus_base import RemoteFocusBase
    from aslm.model.dummy import DummyModel

    model = DummyModel()
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    RemoteFocusBase(microscope_name, None, model.configuration)


def test_remote_focus_base_adjust():
    import random

    from aslm.model.devices.remote_focus.remote_focus_base import RemoteFocusBase
    from aslm.model.dummy import DummyModel

    model = DummyModel()
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    rf = RemoteFocusBase(microscope_name, None, model.configuration)

    waveform_dict = rf.adjust(random.random())

    for k, v in waveform_dict.items():
        try:
            channel = model.configuration["experiment"]["MicroscopeState"]["channels"][
                k
            ]
            if not channel["is_selected"]:
                continue
            assert np.all(v <= rf.etl_max_voltage)
            assert np.all(v >= rf.etl_min_voltage)
        except KeyError:
            # The channel doesn't exist. Points to an issue in how waveform dict is created.
            continue


def test_remote_focus_base_functions():
    from aslm.model.devices.remote_focus.remote_focus_base import RemoteFocusBase
    from aslm.model.dummy import DummyModel

    model = DummyModel()
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    rf = RemoteFocusBase(microscope_name, None, model.configuration)

    funcs = ["prepare_task", "start_task", "stop_task", "close_task"]
    args = [["channel_dummy"], None, None, None]

    for f, a in zip(funcs, args):
        if a is not None:
            getattr(rf, f)(*a)
        else:
            getattr(rf, f)()
