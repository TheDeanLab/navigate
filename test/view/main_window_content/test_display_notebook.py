from types import SimpleNamespace
from unittest.mock import MagicMock

from navigate.view.main_window_content.display_notebook import HistogramFrame


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
