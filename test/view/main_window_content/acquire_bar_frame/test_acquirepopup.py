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

import gc
import threading
import tkinter as tk
from tkinter import ttk
import weakref

import pytest
from navigate.view.popups.acquire_popup import AcquirePopUp


def test_acquirepopup_uses_ttk_controls(tk_root):
    """Acquire popup widgets should use styled ttk controls."""
    acq_pop = AcquirePopUp(tk_root)
    tk_root.update_idletasks()

    assert isinstance(acq_pop.buttons["Cancel"], ttk.Button)
    assert isinstance(acq_pop.buttons["Done"], ttk.Button)

    assert isinstance(acq_pop.inputs["root_directory"].label, ttk.Label)
    assert isinstance(acq_pop.inputs["root_directory"].widget, ttk.Entry)
    assert isinstance(acq_pop.inputs["solvent"].widget, ttk.Combobox)
    assert isinstance(acq_pop.inputs["file_type"].widget, ttk.Combobox)

    assert isinstance(acq_pop.tab_frame.inputs["misc"].master, ttk.Frame)
    assert isinstance(acq_pop.tab_frame.inputs["shear_data"], ttk.Frame)
    assert isinstance(acq_pop.tab_frame.inputs["shear_data"].widget, ttk.Checkbutton)
    assert isinstance(
        acq_pop.tab_frame.inputs["lateral_down_sample"].widget,
        ttk.Combobox,
    )

    acq_pop.popup.destroy()


@pytest.mark.parametrize("close_method", ["destroy", "dismiss", "window_manager"])
def test_acquirepopup_releases_variables_on_tk_thread(
    tk_root, monkeypatch, close_method
):
    """Destroyed save dialogs must not leave Tk cleanup to worker collection."""
    main = threading.get_ident()
    finalized = []
    owned = {}
    original = tk.Variable.__del__

    def finalize(variable):
        if str(variable) in owned:
            finalized.append(threading.get_ident())
            if threading.get_ident() != main:
                return  # Record failures without calling Tcl from the worker.
        original(variable)

    monkeypatch.setattr(tk.Variable, "__del__", finalize)
    popup = AcquirePopUp(
        tk_root,
        {
            "experiment": {
                "MicroscopeState": {
                    "channels": {
                        "channel_1": {"is_selected": True, "laser": "488nm"},
                        "channel_2": {"is_selected": True, "laser": "488nm"},
                    }
                }
            }
        },
    )

    def descendants(widget):
        yield widget
        for child in widget.winfo_children():
            yield from descendants(child)

    widgets = list(descendants(popup.popup))
    for widget in widgets:
        for attribute in ("variable", "error"):
            variable = getattr(widget, attribute, None)
            if isinstance(variable, tk.Variable):
                owned[str(variable)] = weakref.ref(variable)
    del widget, variable
    # Match the controller's file-type trace, which captures its own variable.
    file_type = popup.inputs["file_type"].get_variable()
    file_type.trace_add("write", lambda *args, value=file_type: value.get())
    del file_type
    assert owned

    if close_method == "window_manager":
        popup.popup.tk.call(popup.popup.protocol("WM_DELETE_WINDOW"))
    else:
        getattr(popup.popup, close_method)()
    pending = [popup, widgets]
    del popup, widgets
    gc.collect()
    worker = threading.Thread(target=lambda: (pending.clear(), gc.collect()))
    worker.start()
    worker.join(timeout=2)
    assert not worker.is_alive()
    assert all(ref() is None for ref in owned.values())
    assert finalized and set(finalized) == {main}
