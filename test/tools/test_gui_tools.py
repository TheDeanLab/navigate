import importlib
import sys
from types import SimpleNamespace
from unittest.mock import Mock


def _import_gui_with_fake_mss(monkeypatch):
    class FakeScreenshot:
        size = (3, 2)
        rgb = b"0123456789abcdef12"

    class FakeMSSContext:
        def __init__(self):
            self.grab_calls = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def grab(self, region):
            self.grab_calls.append(region)
            return FakeScreenshot()

    fake_context = FakeMSSContext()
    fake_mss_module = SimpleNamespace(mss=lambda: fake_context)
    monkeypatch.setitem(sys.modules, "mss", fake_mss_module)
    sys.modules.pop("navigate.tools.gui", None)
    module = importlib.import_module("navigate.tools.gui")
    return module, fake_context


def test_capture_region_uses_mss_and_saves_image(monkeypatch):
    gui_module, fake_context = _import_gui_with_fake_mss(monkeypatch)
    fake_image = Mock()
    frombytes = Mock(return_value=fake_image)
    monkeypatch.setattr(gui_module.Image, "frombytes", frombytes)

    gui_module.capture_region(10.8, 20.2, 30.9, 40.1, "out.png")

    assert fake_context.grab_calls == [
        {"left": 10, "top": 20, "width": 30, "height": 40}
    ]
    frombytes.assert_called_once_with("RGB", (3, 2), b"0123456789abcdef12")
    fake_image.save.assert_called_once_with("out.png")


def test_tk_window_bbox_applies_padding(monkeypatch):
    class FakeWin:
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

    win = FakeWin()
    gui_module, _ = _import_gui_with_fake_mss(monkeypatch)
    bbox = gui_module.tk_window_bbox(win, pad=5)

    assert win.updated is True
    assert bbox == (95, 195, 310, 410)
