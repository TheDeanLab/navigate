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

from tkinter import ttk

import pytest

pytest.importorskip("pandastable")

from navigate.view.popups.camera_setting_popup import AdvancedCameraSettingPopup
from navigate.view.popups.stages_advanced_popup import AdvancedStageParametersPopup


def test_advanced_camera_setting_popup_uses_typography_styles(tk_root):
    popup = AdvancedCameraSettingPopup(tk_root)
    popup.populate_view({"x": False, "y": True})
    tk_root.update_idletasks()

    assert popup.microscope.label.cget("style") == "Title.TLabel"

    axis_labels = [
        widget
        for widget in popup.column_frames["axis"].winfo_children()
        if isinstance(widget, ttk.Label)
    ]
    assert axis_labels
    assert all(label.cget("style") == "BodyBold.TLabel" for label in axis_labels)

    section_labels = [
        widget
        for widget in popup.camera_control_frame.winfo_children()
        if isinstance(widget, ttk.Label)
        and widget.cget("text")
        in {"Cooling Settings", "Temperature (°C)", "Trigger Source"}
    ]
    assert len(section_labels) == 3
    assert all(label.cget("style") == "Section.TLabel" for label in section_labels)

    popup.popup.destroy()


def test_advanced_stage_popup_uses_typography_styles(tk_root):
    popup = AdvancedStageParametersPopup(tk_root)
    popup.populate_view(
        stages=["x", "y"],
        min_dict={"x": -10, "y": -20},
        max_dict={"x": 10, "y": 20},
        flip_axes={"x": False, "y": True},
        offsets={"x": 0, "y": 0},
        home_dict={"x": None, "y": None},
    )
    tk_root.update_idletasks()

    assert popup.microscope.label.cget("style") == "Title.TLabel"

    stage_labels = [
        widget
        for widget in popup.column_frames["stage"].winfo_children()
        if isinstance(widget, ttk.Label)
    ]
    assert stage_labels
    assert all(label.cget("style") == "BodyBold.TLabel" for label in stage_labels)
    assert popup.stage_limits_enabled.cget("style") == "BodyBold.TCheckbutton"

    popup.popup.destroy()
