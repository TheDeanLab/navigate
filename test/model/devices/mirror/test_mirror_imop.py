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
from types import ModuleType

import pytest


@pytest.fixture
def mirror_configuration():
    return {
        "configuration": {
            "microscopes": {
                "scope-a": {
                    "mirror": {
                        "hardware": {
                            "flat_path": "/tmp/fake-flat-path.wcs",
                        }
                    }
                }
            }
        }
    }


@pytest.fixture
def imop_module(monkeypatch):
    fake_imop_api = ModuleType("navigate.model.devices.APIs.imagineoptics.imop")

    class FakeIMOPMirror:
        instances = []

        def __init__(self):
            self.calls = []
            self.modal_coefs = [0.1, 0.2, 0.3]
            self.__class__.instances.append(self)

        def set_flat(self, pos=None, pos_path=None):
            self.calls.append(("set_flat", {"pos": pos, "pos_path": pos_path}))

        def flat(self):
            self.calls.append(("flat", {}))

        def move_absolute_zero(self):
            self.calls.append(("move_absolute_zero", {}))

        def display_modes(self, coefs):
            self.calls.append(("display_modes", {"coefs": coefs}))

        def get_modal_coefs(self):
            self.calls.append(("get_modal_coefs", {}))
            return self.modal_coefs

        def load_wcs(self, path=None, name=None, mode_file=False):
            self.calls.append(
                (
                    "load_wcs",
                    {"path": path, "name": name, "mode_file": mode_file},
                )
            )
            if path is not None:
                return ["path", path]
            return ["name", name]

        def save_wcs(self, path=None, name=None, mode_file=False):
            self.calls.append(
                (
                    "save_wcs",
                    {"path": path, "name": name, "mode_file": mode_file},
                )
            )

    fake_imop_api.IMOP_Mirror = FakeIMOPMirror

    monkeypatch.setitem(
        sys.modules, "navigate.model.devices.APIs.imagineoptics.imop", fake_imop_api
    )

    sys.modules.pop("navigate.model.devices.mirror.imop", None)
    module = importlib.import_module("navigate.model.devices.mirror.imop")
    yield module, FakeIMOPMirror
    sys.modules.pop("navigate.model.devices.mirror.imop", None)


def test_imop_constructor_initializes_controller_and_flattens(
    imop_module, mirror_configuration
):
    module, fake_class = imop_module

    mirror = module.ImagineOpticsMirror("scope-a", fake_class(), mirror_configuration)
    controller = fake_class.instances[0]

    assert mirror.mirror_controller is controller
    assert controller.calls[0] == (
        "set_flat",
        {"pos": None, "pos_path": "/tmp/fake-flat-path.wcs"},
    )
    assert controller.calls[1] == ("flat", {})


def test_imop_constructor_raises_for_unknown_microscope(
    imop_module, mirror_configuration
):
    module, fake_class = imop_module

    with pytest.raises(NameError, match="Microscope missing-scope does not exist."):
        module.ImagineOpticsMirror("missing-scope", None, mirror_configuration)

    assert fake_class.instances == []


def test_imop_forwarders_dispatch_to_controller(imop_module, mirror_configuration):
    module, fake_class = imop_module
    mirror = module.ImagineOpticsMirror("scope-a", fake_class(), mirror_configuration)
    controller = fake_class.instances[0]

    controller.calls.clear()

    mirror.flat()
    mirror.zero_flatness()
    mirror.set_positions_flat([1, 2, 3])
    mirror.display_modes([0.0, 0.5, 1.0])
    modal_coefs = mirror.get_modal_coefs()

    assert modal_coefs == [0.1, 0.2, 0.3]
    assert controller.calls == [
        ("flat", {}),
        ("move_absolute_zero", {}),
        ("set_flat", {"pos": [1, 2, 3], "pos_path": None}),
        ("display_modes", {"coefs": [0.0, 0.5, 1.0]}),
        ("get_modal_coefs", {}),
    ]


def test_imop_wcs_load_and_save_forwarders(imop_module, mirror_configuration):
    module, fake_class = imop_module
    mirror = module.ImagineOpticsMirror("scope-a", fake_class(), mirror_configuration)
    controller = fake_class.instances[0]

    controller.calls.clear()

    loaded_from_path = mirror.set_from_wcs_file(path="/tmp/custom-path.wcs")
    loaded_from_name = mirror.set_from_wcs_file(name="correction-a")
    mirror.save_wcs_file(path="/tmp/save-path.wcs")
    mirror.save_wcs_file(name="correction-b")

    assert loaded_from_path == ["path", "/tmp/custom-path.wcs"]
    assert loaded_from_name == ["name", "correction-a"]
    assert controller.calls == [
        (
            "load_wcs",
            {"path": "/tmp/custom-path.wcs", "name": None, "mode_file": True},
        ),
        ("load_wcs", {"path": None, "name": "correction-a", "mode_file": True}),
        (
            "save_wcs",
            {"path": "/tmp/save-path.wcs", "name": None, "mode_file": True},
        ),
        ("save_wcs", {"path": None, "name": "correction-b", "mode_file": True}),
    ]


def test_imop_destructor_is_error_tolerant_noop(imop_module, mirror_configuration):
    module, fake_class = imop_module
    mirror = module.ImagineOpticsMirror("scope-a", fake_class(), mirror_configuration)

    class ExplodingController:
        def __getattribute__(self, _name):
            raise RuntimeError("should never be touched by __del__")

    mirror.mirror_controller = ExplodingController()

    assert mirror.__del__() is None
