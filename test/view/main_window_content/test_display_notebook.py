from types import SimpleNamespace
from unittest.mock import MagicMock
import tkinter as tk

from navigate.view.main_window_content.display_notebook import (
    HistogramFrame,
    IntensityFrame,
)


class _MockTkVar:
    """Minimal mock of Tk variable objects used in IntensityFrame tests."""

    def __init__(self, value=None, *, raises: bool = False):
        self.value = value
        self.raises = raises

    def get(self):
        if self.raises:
            raise tk.TclError('expected floating-point number but got ""')
        return self.value


def _build_intensity_frame_state() -> IntensityFrame:
    """Construct an IntensityFrame instance for pure state-method testing."""
    frame = IntensityFrame.__new__(IntensityFrame)
    frame._all_channels_label = "All"
    frame._multichannel_channels = ["CH1", "CH2"]
    frame._multichannel_channel_states = {
        "CH1": {
            "lut_name": "Green",
            "autoscale": True,
            "min_counts": 10.0,
            "max_counts": 1000.0,
            "visible": True,
            "alpha": 0.7,
            "gamma": 1.4,
        }
    }
    frame._active_multichannel_channel = _MockTkVar("CH1")
    frame._active_multichannel_lut = _MockTkVar("Magenta")
    frame._active_multichannel_autoscale = _MockTkVar(False)
    frame._active_multichannel_min = _MockTkVar(12)
    frame._active_multichannel_max = _MockTkVar(1200)
    frame._active_multichannel_visible = _MockTkVar(False)
    frame._active_multichannel_alpha = _MockTkVar(50.0)
    frame._active_multichannel_gamma = _MockTkVar(1.1)
    frame._multichannel_min_widget = {}
    frame._multichannel_max_widget = {}
    return frame


def test_resize_figure_to_frame_updates_size_and_draw():
    frame = HistogramFrame.__new__(HistogramFrame)
    frame.figure = MagicMock()
    frame.figure.get_dpi.return_value = 100.0
    frame.figure_canvas = MagicMock()
    frame._last_resize_pixels = (0, 0)

    event = SimpleNamespace(width=400, height=120)
    HistogramFrame._resize_figure_to_frame(frame, event)

    frame.figure.set_size_inches.assert_called_once_with(4.0, 1.2, forward=False)
    frame.figure_canvas.draw_idle.assert_called_once_with()
    assert frame._last_resize_pixels == (400, 120)


def test_resize_figure_to_frame_ignores_tiny_or_duplicate_resize():
    frame = HistogramFrame.__new__(HistogramFrame)
    frame.figure = MagicMock()
    frame.figure.get_dpi.return_value = 100.0
    frame.figure_canvas = MagicMock()
    frame._last_resize_pixels = (400, 120)

    tiny_event = SimpleNamespace(width=1, height=100)
    HistogramFrame._resize_figure_to_frame(frame, tiny_event)

    duplicate_event = SimpleNamespace(width=400, height=120)
    HistogramFrame._resize_figure_to_frame(frame, duplicate_event)

    frame.figure.set_size_inches.assert_not_called()
    frame.figure_canvas.draw_idle.assert_not_called()
    assert frame._last_resize_pixels == (400, 120)


def test_store_active_multichannel_values_tolerates_empty_gamma() -> None:
    frame = _build_intensity_frame_state()
    frame._active_multichannel_gamma = _MockTkVar(raises=True)

    IntensityFrame._store_active_multichannel_values(frame)

    state = frame._multichannel_channel_states["CH1"]
    assert state["gamma"] == 1.4
    assert state["alpha"] == 0.5
    assert state["min_counts"] == 12.0
    assert state["max_counts"] == 1200.0


def test_store_active_multichannel_values_tolerates_empty_numeric_widgets() -> None:
    frame = _build_intensity_frame_state()
    frame._active_multichannel_min = _MockTkVar(raises=True)
    frame._active_multichannel_max = _MockTkVar(raises=True)
    frame._active_multichannel_alpha = _MockTkVar(raises=True)
    frame._active_multichannel_gamma = _MockTkVar(raises=True)

    IntensityFrame._store_active_multichannel_values(frame)

    state = frame._multichannel_channel_states["CH1"]
    assert state["min_counts"] == 10.0
    assert state["max_counts"] == 1000.0
    assert state["alpha"] == 0.7
    assert state["gamma"] == 1.4


def test_set_multichannel_minmax_state_tolerates_invalid_autoscale_var() -> None:
    frame = _build_intensity_frame_state()
    frame._active_multichannel_autoscale = _MockTkVar(raises=True)

    IntensityFrame._set_multichannel_minmax_state(frame)

    assert frame._multichannel_min_widget["state"] == "disabled"
    assert frame._multichannel_max_widget["state"] == "disabled"


def test_flip_xy_control_is_attached_to_compact_lut_frame(tk_root) -> None:
    frame = IntensityFrame(tk_root)
    tk_root.update_idletasks()

    assert frame.inputs["Flip XY"].master == frame.multichannel_frame
    assert frame.inputs["Flip XY"].label.cget("text") == "Flip XY"
    assert frame._multichannel_visible_input.master == frame.multichannel_frame
    assert frame._multichannel_visible_input.label.cget("text") == "Visible"
    assert frame._multichannel_visible_widget.master == frame._multichannel_visible_input
    assert frame._multichannel_visible_widget.cget("text") == ""
    assert frame._multichannel_autoscale_input.master == frame.multichannel_frame
    assert frame._multichannel_autoscale_input.label.cget("text") == "Autoscale"
    assert (
        frame._multichannel_autoscale_widget.master
        == frame._multichannel_autoscale_input
    )
    assert frame._multichannel_autoscale_widget.cget("text") == ""
    assert frame.multichannel_frame.winfo_manager() == "grid"
    assert frame.single_channel_frame.winfo_manager() == ""
