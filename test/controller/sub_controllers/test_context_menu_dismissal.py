"""X11 popup menus must keep receiving outside clicks until dismissed."""

from types import SimpleNamespace
import tkinter as tk

import pytest

from navigate.controller.sub_controllers.camera_view import (
    CameraViewController,
    MIPViewController,
)
from navigate.controller.sub_controllers.histogram import HistogramController


@pytest.fixture(params=[CameraViewController, MIPViewController, HistogramController])
def popup(request):
    """Exercise each production handler with a real menu and no microscope."""
    root = tk.Tk()
    if root.tk.call("tk", "windowingsystem") != "x11":
        root.destroy()
        pytest.skip("X11 popup grab behavior")
    root.geometry("500x350+0+0")
    canvas = tk.Canvas(root)
    canvas.pack(fill="both", expand=True)
    controller = request.param.__new__(request.param)
    controller.menu = tk.Menu(canvas, tearoff=0)
    controller.menu.add_command(label="Probe")
    controller.canvas_width = 500
    controller.canvas_height = 350
    controller.get_absolute_position = lambda: (100, 100)
    handler = (
        controller.histogram_popup
        if isinstance(controller, HistogramController)
        else controller.popup_menu
    )
    event = SimpleNamespace(x=100, y=100, x_root=100, y_root=100)
    root.update()
    root.focus_force()
    root.update()
    try:
        yield root, controller.menu, lambda: handler(event)
    finally:
        root.tk.call("tk::MenuUnpost", str(controller.menu))
        root.destroy()


def test_popup_keeps_grab_until_escape(popup):
    """Releasing the grab on return from tk_popup loses outside-click delivery."""
    root, menu, open_menu = popup
    open_menu()
    root.update()
    assert menu.winfo_ismapped()
    assert root.grab_current() == menu
    assert menu.grab_status() == "global"

    menu.event_generate("<Escape>")
    root.update()
    assert not menu.winfo_ismapped()
    assert root.grab_current() is None


def test_posting_error_does_not_leave_a_grab(popup, monkeypatch):
    """A failed popup must still release any grab acquired while posting."""
    root, menu, open_menu = popup
    post = menu.tk_popup

    def failed_post(*args):
        post(*args)
        raise tk.TclError("popup failed after acquiring a grab")

    monkeypatch.setattr(menu, "tk_popup", failed_post)
    with pytest.raises(tk.TclError, match="popup failed"):
        open_menu()
    assert root.grab_current() is None
