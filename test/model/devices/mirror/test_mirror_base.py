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

import pytest

from navigate.model.devices.mirror.base import MirrorBase
from navigate.model.devices.mirror.synthetic import SyntheticMirror


@pytest.fixture
def mirror_configuration():
    return {
        "configuration": {
            "microscopes": {
                "scope-a": {
                    "mirror": {
                        "channel": "demo",
                        "flat_value": 0,
                    }
                }
            }
        }
    }


def test_mirror_base_initializes_from_configuration(mirror_configuration):
    controller = object()
    mirror = MirrorBase("scope-a", controller, mirror_configuration)

    assert mirror.configuration is mirror_configuration
    assert mirror.mirror_controller is controller
    assert mirror.mirror_parameters == {"channel": "demo", "flat_value": 0}
    assert mirror.is_synthetic is False
    assert str(mirror) == "MirrorBase"
    assert mirror.__del__() is None


def test_mirror_base_raises_for_unknown_microscope(mirror_configuration):
    with pytest.raises(NameError, match="Microscope missing-scope does not exist."):
        MirrorBase("missing-scope", None, mirror_configuration)


def test_synthetic_mirror_marks_itself_as_synthetic(mirror_configuration):
    mirror = SyntheticMirror("scope-a", "controller", mirror_configuration)

    assert isinstance(mirror, MirrorBase)
    assert mirror.is_synthetic is True
    assert mirror.mirror_controller == "controller"
    assert mirror.flat() is None
    assert mirror.__del__() is None
