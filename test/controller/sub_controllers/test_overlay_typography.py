# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
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

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

pytest.importorskip("pandastable")

from navigate.controller.sub_controllers.camera_view import MIPViewController
from navigate.controller.sub_controllers.histogram import HistogramController


def test_mip_clear_uses_theme_typography(monkeypatch):
    controller = MIPViewController.__new__(MIPViewController)
    controller.canvas = MagicMock()
    controller.canvas_width = 512
    controller.canvas_height = 384
    controller.tk_image = "image"

    monkeypatch.setattr(
        "navigate.controller.sub_controllers.camera_view.get_theme_font",
        lambda name, fallback=None: ("TkDefaultFont", 14, "italic"),
    )
    monkeypatch.setattr(
        "navigate.controller.sub_controllers.camera_view.get_theme_color",
        lambda name, fallback=None: "#8c96a7",
    )

    controller._clear_mip()

    controller.canvas.delete.assert_called_once_with("all")
    assert controller.tk_image is None
    controller.canvas.create_text.assert_called_once()
    args, kwargs = controller.canvas.create_text.call_args
    assert args[:2] == (controller.canvas_width // 2, controller.canvas_height // 2)
    assert kwargs["font"] == ("TkDefaultFont", 14, "italic")
    assert kwargs["fill"] == "#8c96a7"


def test_histogram_clear_uses_theme_typography(monkeypatch):
    controller = HistogramController.__new__(HistogramController)
    controller.ax = MagicMock()
    controller.ax.transAxes = object()
    controller.histogram = SimpleNamespace(figure_canvas=MagicMock())

    monkeypatch.setattr(
        "navigate.controller.sub_controllers.histogram.get_theme_matplotlib_font",
        lambda name, fallback=None: {
            "family": "Segoe UI",
            "size": 10,
            "style": "normal",
            "weight": "normal",
        },
    )

    def fake_color(name, fallback=None):
        palette = {
            "muted_text": "#9aa8bb",
            "panel_bg": "#1a212b",
            "border": "#2f3a4a",
        }
        if name in palette:
            return palette[name]
        if fallback is not None:
            return fallback
        return "#000000"

    monkeypatch.setattr(
        "navigate.controller.sub_controllers.histogram.get_theme_color",
        fake_color,
    )

    controller._clear_histogram()

    controller.ax.cla.assert_called_once()
    controller.ax.text.assert_called_once()
    _, kwargs = controller.ax.text.call_args
    assert kwargs["fontdict"]["family"] == "Segoe UI"
    assert kwargs["fontdict"]["size"] == 10
    assert kwargs["fontdict"]["style"] == "italic"
    assert kwargs["fontdict"]["weight"] == "normal"
    assert kwargs["fontdict"]["color"] == "#9aa8bb"
    assert kwargs["bbox"]["facecolor"] == "#1a212b"
    assert kwargs["bbox"]["edgecolor"] == "#2f3a4a"
    controller.ax.set_xticks.assert_called_once_with([])
    controller.ax.set_yticks.assert_called_once_with([])
    controller.histogram.figure_canvas.draw.assert_called_once()
