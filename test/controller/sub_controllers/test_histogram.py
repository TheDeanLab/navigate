# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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

import importlib.util
from pathlib import Path
import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np


def _install_stub_module(originals: dict[str, object], name: str, **attrs):
    if name not in originals:
        originals[name] = sys.modules.get(name)
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _restore_modules(originals: dict[str, object]) -> None:
    for name, original in originals.items():
        if original is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = original


def _load_histogram_module():
    originals: dict[str, object] = {}
    module_name = "navigate.controller.sub_controllers.histogram_under_test"
    module_path = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "navigate"
        / "controller"
        / "sub_controllers"
        / "histogram.py"
    )

    _install_stub_module(originals, "navigate", __path__=[])
    _install_stub_module(originals, "navigate.model", __path__=[])
    _install_stub_module(originals, "navigate.model.concurrency", __path__=[])
    _install_stub_module(originals, "navigate.controller", __path__=[])
    _install_stub_module(originals, "navigate.controller.sub_controllers", __path__=[])
    _install_stub_module(originals, "navigate.view", __path__=[])
    _install_stub_module(originals, "navigate.view.main_window_content", __path__=[])
    _install_stub_module(originals, "navigate.tools", __path__=[])
    _install_stub_module(
        originals,
        "navigate.model.concurrency.concurrency_tools",
        SharedNDArray=np.ndarray,
    )
    _install_stub_module(
        originals,
        "navigate.view.main_window_content.display_notebook",
        HistogramFrame=object,
    )
    _install_stub_module(
        originals,
        "navigate.view.theme",
        get_theme_color=lambda name, fallback=None: fallback
        if fallback is not None
        else "#000000",
        get_theme_matplotlib_font=lambda name, fallback=None: {
            "family": "TkDefaultFont",
            "size": 10,
            "style": "normal",
            "weight": "normal",
        },
    )
    _install_stub_module(
        originals, "navigate.config", update_config_dict=lambda **kwargs: None
    )

    def _passthrough_performance_monitor(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    _install_stub_module(
        originals,
        "navigate.tools.decorators",
        performance_monitor=_passthrough_performance_monitor,
    )

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)

    if module_name not in originals:
        originals[module_name] = sys.modules.get(module_name)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    finally:
        _restore_modules(originals)

    return module


histogram_module = _load_histogram_module()
HistogramController = histogram_module.HistogramController


def _build_controller(number_bins: int = 8) -> HistogramController:
    controller = HistogramController.__new__(HistogramController)
    controller._number_bins = number_bins
    return controller


def test_calculate_histogram_counts_falls_back_to_numpy(monkeypatch):
    controller = _build_controller(number_bins=8)

    class DummyCV2:
        @staticmethod
        def calcHist(*args, **kwargs):
            raise RuntimeError("simulated cv2 histogram failure")

    monkeypatch.setattr(histogram_module, "cv2", DummyCV2, raising=False)
    data = np.array([0, 1, 1, 2, 3, 3, 3], dtype=np.uint16)
    counts, bins, backend = controller._calculate_histogram_counts(data)

    assert backend == "numpy.histogram"
    assert counts.sum() == data.size
    assert len(bins) == 4


def test_calculate_histogram_counts_uses_cv2(monkeypatch):
    controller = _build_controller(number_bins=6)
    called = {}

    class DummyCV2:
        @staticmethod
        def calcHist(images, channels, mask, bins, ranges):
            called["images"] = images
            called["channels"] = channels
            called["bins"] = bins
            called["ranges"] = ranges
            return np.ones((bins[0], 1), dtype=np.float32)

    monkeypatch.setattr(histogram_module, "cv2", DummyCV2, raising=False)
    data = np.arange(30, dtype=np.uint16)
    counts, bins, backend = controller._calculate_histogram_counts(data)

    assert backend == "cv2.calcHist"
    assert counts.shape == (6,)
    assert float(counts.sum()) == 6.0
    assert called["channels"] == [0]
    assert called["bins"] == [6]
    assert len(bins) == 7


def test_render_histogram_uses_blit_when_background_cached():
    controller = _build_controller()
    controller.ax = MagicMock()
    controller.ax.bbox = object()
    controller._blit_supported = True
    controller._histogram_artist = MagicMock()
    controller._histogram_background = object()
    controller._force_full_redraw = False
    controller._last_render_used_blit = False
    controller.histogram = SimpleNamespace(figure_canvas=MagicMock())

    controller._render_histogram(force_full_redraw=False)

    canvas = controller.histogram.figure_canvas
    canvas.draw.assert_not_called()
    canvas.restore_region.assert_called_once_with(controller._histogram_background)
    controller.ax.draw_artist.assert_called_once_with(controller._histogram_artist)
    canvas.blit.assert_called_once_with(controller.ax.bbox)
    assert controller._last_render_used_blit is True


def test_populate_histogram_redispatches_off_main_thread():
    controller = _build_controller()
    controller._main_thread_ident = 0  # current thread id cannot be zero
    controller.parent_controller = SimpleNamespace(_run_on_main_thread=MagicMock())
    controller._print_performance_trace = MagicMock()
    image = np.zeros((4, 4), dtype=np.uint16)

    controller.populate_histogram(image=image)

    controller.parent_controller._run_on_main_thread.assert_called_once()
    args, kwargs = controller.parent_controller._run_on_main_thread.call_args
    assert args[0] == controller.populate_histogram
    assert np.array_equal(args[1], image)
    assert kwargs == {"wait": False}


def test_flush_pending_histogram_update_reinitializes_after_disabled_overlay():
    controller = _build_controller()
    image = np.zeros((4, 4), dtype=np.uint16)

    controller._histogram_after_id = "after-id"
    controller._pending_histogram_image = image
    controller.histogram_enabled = SimpleNamespace(get=lambda: True)
    controller._histogram_disabled_overlay_drawn = True
    controller._initialize_histogram_axes = MagicMock()
    controller._populate_histogram = MagicMock()

    controller._flush_pending_histogram_update()

    assert controller._histogram_after_id is None
    assert controller._pending_histogram_image is None
    controller._initialize_histogram_axes.assert_called_once_with()
    controller._populate_histogram.assert_called_once_with(image)
    assert controller._histogram_disabled_overlay_drawn is False
