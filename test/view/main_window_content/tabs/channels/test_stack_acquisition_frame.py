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

import tkinter as tk

import pytest

from navigate.view.main_window_content.channels_tab import (
    ChannelsTab,
    StackAcquisitionFrame,
)
from navigate.view.theme import get_theme_space_px


def test_absolute_preview_uses_vectors_without_loading_an_image(monkeypatch) -> None:
    """The idle view uses the animation's outline and needs no image resource."""
    root = tk.Tk()
    try:

        def unexpected_image(*args, **kwargs):
            raise AssertionError("Stack previews must not load bitmap images")

        monkeypatch.setattr(tk, "PhotoImage", unexpected_image)
        frame = StackAcquisitionFrame(root)
        frame.draw_absolute_stack(300, 100)
        root.update_idletasks()
        canvas = frame.idle_schematic
        assert len(canvas.find_withtag("stack_outline")) == 3
        assert canvas.itemcget("idle_top", "text") == "300 µm"
        assert canvas.itemcget("idle_bottom", "text") == "100 µm"
        frame.draw_absolute_stack(-90, 90, "theta")
        assert canvas.itemcget("idle_top", "text") == "90 °"
        assert canvas.itemcget("idle_bottom", "text") == "-90 °"
    finally:
        root.destroy()


@pytest.mark.parametrize("scaling", [1.0, 2.0])
def test_stack_modes_and_focus_ramp_preserve_compact_layout(scaling: float) -> None:
    """Mode toggles retain every control's footprint, including inactive fields."""
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", scaling)
        tab = ChannelsTab(root)
        tab.grid(sticky="nsew")
        frame = tab.stack_acq_frame
        frame.create_additional_stack_widgets(["z", "f"], {})
        root.update_idletasks()
        size = (frame.winfo_reqwidth(), frame.winfo_reqheight())
        for relative, ramp, editable in (
            (False, False, True),
            (True, False, True),
            (True, True, True),
            (True, False, True),
            (False, True, True),
            (False, True, False),
            (True, True, False),
            (False, False, True),
        ):
            frame.configure_position_mode(relative, ramp, editable)
            root.update_idletasks()
            current = (frame.winfo_reqwidth(), frame.winfo_reqheight())
            assert current == size
            assert frame.relative_controls.winfo_manager() == "grid"
            for endpoint in ("start", "end"):
                focus = frame.inputs[f"{endpoint}_focus"]
                button = frame.buttons[f"set_{endpoint}"]
                assert focus.winfo_manager() == button.winfo_manager() == "grid"
                expected_focus = (
                    "normal" if editable and (not relative or ramp) else "disabled"
                )
                assert str(focus.widget.cget("state")) == expected_focus
                assert button.instate(["disabled"]) == relative

        # The schematic must not stretch individual device rows, even when the
        # surrounding application allocates more space than the panel requests.
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        root.geometry(f"{tab.winfo_reqwidth() + 100}x{tab.winfo_reqheight() + 100}")
        root.update_idletasks()
        assert frame.winfo_height() == frame.winfo_reqheight()
        devices = [
            frame.inputs[name] for name in ("z_device", "f_device", "cycling", "speed")
        ]
        for above, below in zip(devices, devices[1:]):
            assert above.winfo_height() == above.winfo_reqheight()
            gap = below.winfo_rooty() - above.winfo_rooty() - above.winfo_height()
            assert 0 <= gap <= 2 * get_theme_space_px(5)
    finally:
        root.destroy()
