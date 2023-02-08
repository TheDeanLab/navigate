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
#
import pytest


@pytest.fixture
def dummy_zoom(dummy_model):
    from aslm.model.devices.zoom.zoom_base import ZoomBase

    return ZoomBase(dummy_model.active_microscope_name, None, dummy_model.configuration)


def test_zoom_base_attributes(dummy_zoom):

    assert hasattr(dummy_zoom, "zoomdict")
    assert hasattr(dummy_zoom, "zoomvalue")

    assert hasattr(dummy_zoom, "set_zoom") and callable(getattr(dummy_zoom, "set_zoom"))
    assert hasattr(dummy_zoom, "move") and callable(getattr(dummy_zoom, "move"))
    assert hasattr(dummy_zoom, "read_position") and callable(
        getattr(dummy_zoom, "read_position")
    )


def test_build_stage_dict(dummy_zoom):
    import random

    a, b, c = random.randint(1, 1000), random.randint(1, 1000), random.randint(1, 1000)
    dummy_zoom.configuration["stage_positions"] = {
        "BABB": {"f": {"0.63x": a, "1x": b, "2x": c}}
    }
    dummy_zoom.build_stage_dict()

    assert dummy_zoom.stage_offsets["BABB"]["f"]["0.63x"]["0.63x"] == 0
    assert dummy_zoom.stage_offsets["BABB"]["f"]["0.63x"]["1x"] == b - a
    assert dummy_zoom.stage_offsets["BABB"]["f"]["0.63x"]["2x"] == c - a
    assert dummy_zoom.stage_offsets["BABB"]["f"]["1x"]["0.63x"] == a - b
    assert dummy_zoom.stage_offsets["BABB"]["f"]["1x"]["1x"] == 0
    assert dummy_zoom.stage_offsets["BABB"]["f"]["1x"]["2x"] == c - b
    assert dummy_zoom.stage_offsets["BABB"]["f"]["2x"]["0.63x"] == a - c
    assert dummy_zoom.stage_offsets["BABB"]["f"]["2x"]["1x"] == b - c
    assert dummy_zoom.stage_offsets["BABB"]["f"]["2x"]["2x"] == 0


def test_set_zoom(dummy_zoom):
    for zoom in dummy_zoom.zoomdict.keys():
        dummy_zoom.set_zoom(zoom)
        assert dummy_zoom.zoomvalue == zoom

    try:
        dummy_zoom.set_zoom("not_a_zoom")
        assert False
    except ValueError:
        assert True
