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
#

# Third Party Imports
import pytest

# Local Imports
from navigate.view.popups.microscope_setting_popup_window import (
    MicroscopeSettingPopupWindow,
)


@pytest.fixture
def microscope_info():
    return {
        "Mesoscale": {
            "camera": "Hamamatsu ORCA-Lightning",
            "remote_focus": "NI",
        },
        "Nanoscale": {
            "camera": "Photometrics Iris 15",
            "galvo": "NI",
        },
    }


@pytest.fixture
def popup(tk_root, microscope_info):
    return MicroscopeSettingPopupWindow(
        tk_root,
        microscope_info,
    )


def test_labels_include_each_device_once(popup):
    assert popup.labels == [
        "Microscope Name",
        "Camera",
        "Remote Focus",
        "Galvo",
        "Zoom Value",
        "Setting",
    ]


def test_device_widgets_show_configuration_values(popup):
    assert popup.inputs["Mesoscale camera"].get() == "Hamamatsu ORCA-Lightning"
    assert popup.inputs["Mesoscale remote_focus"].get() == "NI"
    assert popup.inputs["Mesoscale galvo"].get() == ""
    assert popup.inputs["Nanoscale camera"].get() == "Photometrics Iris 15"
    assert popup.inputs["Nanoscale remote_focus"].get() == ""
    assert popup.inputs["Nanoscale galvo"].get() == "NI"

    for microscope_name in ("Mesoscale", "Nanoscale"):
        for device_name in ("camera", "remote_focus", "galvo"):
            assert (
                str(popup.inputs[f"{microscope_name} {device_name}"].widget["state"])
                == "disabled"
            )


def test_zoom_and_setting_controls_align_with_labels(popup):
    for microscope_name in ("Mesoscale", "Nanoscale"):
        assert popup.inputs[f"{microscope_name}_zoom_value"].grid_info()[
            "row"
        ] == popup.labels.index("Zoom Value")
        assert popup.inputs[microscope_name].grid_info()["row"] == popup.labels.index(
            "Setting"
        )
        assert (
            str(popup.inputs[f"{microscope_name}_zoom_value"].widget["state"])
            == "readonly"
        )


def test_microscopes_are_displayed_in_separate_columns(popup):
    microscope_frames = popup.microscopes_frame.winfo_children()

    assert [frame.grid_info()["column"] for frame in microscope_frames] == [0, 1]
    assert [frame.winfo_children()[0]["text"] for frame in microscope_frames] == [
        "Mesoscale",
        "Nanoscale",
    ]


def test_getters_expose_widgets_variables_and_buttons(popup):
    assert popup.get_widgets() is popup.inputs
    assert popup.get_buttons() is popup.buttons
    assert set(popup.get_variables()) == set(popup.inputs)
    assert all(
        variable is popup.inputs[name].get_variable()
        for name, variable in popup.get_variables().items()
    )
    assert popup.buttons["confirm"]["text"] == "Confirm"
    assert popup.buttons["cancel"]["text"] == "Cancel"
