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
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

def _import_gui_module(monkeypatch):
    fake_mss_module = ModuleType("mss")
    fake_mss_module.mss = lambda: None
    monkeypatch.setitem(sys.modules, "mss", fake_mss_module)

    import navigate.tools.gui as gui_module

    return importlib.reload(gui_module)


def test_capture_region_uses_int_bbox_and_saves_image(monkeypatch, tmp_path):
    gui = _import_gui_module(monkeypatch)
    captured = {}

    class FakeMss:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def grab(self, bbox):
            captured["bbox"] = bbox
            return SimpleNamespace(size=(2, 3), rgb=b"abcdef")

    image_obj = MagicMock()
    frombytes = MagicMock(return_value=image_obj)

    monkeypatch.setattr(gui, "mss", lambda: FakeMss())
    monkeypatch.setattr(gui.Image, "frombytes", frombytes)

    out_path = tmp_path / "capture.png"
    gui.capture_region(10.9, 20.1, 30.7, 40.5, out_path)

    assert captured["bbox"] == {"left": 10, "top": 20, "width": 30, "height": 40}
    frombytes.assert_called_once_with("RGB", (2, 3), b"abcdef")
    image_obj.save.assert_called_once_with(out_path)


def test_tk_window_bbox_applies_padding_and_updates_window(monkeypatch):
    gui = _import_gui_module(monkeypatch)

    class FakeWindow:
        def __init__(self):
            self.updated = False

        def update_idletasks(self):
            self.updated = True

        def winfo_rootx(self):
            return 100

        def winfo_rooty(self):
            return 200

        def winfo_width(self):
            return 300

        def winfo_height(self):
            return 400

    win = FakeWindow()
    bbox = gui.tk_window_bbox(win, pad=5)

    assert win.updated is True
    assert bbox == (95, 195, 310, 410)
