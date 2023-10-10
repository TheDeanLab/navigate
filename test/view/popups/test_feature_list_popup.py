# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Standard Library Imports
import tkinter as tk
from tkinter import ttk
import pytest

# Local Imports
from aslm.view.popups.feature_list_popup import (
    FeatureIcon,
    FeatureConfigPopup,
    FeatureListPopup,
)


@pytest.fixture
def tk_root():
    root = tk.Tk()
    yield root
    root.destroy()


def test_feature_icon(tk_root):
    feature_icon = FeatureIcon(tk_root, "A Test Feature")
    assert isinstance(feature_icon, FeatureIcon)
    assert feature_icon["text"] == "A Test Feature"


@pytest.mark.parametrize(
    "feature_name, args_name, args_value",
    [
        ("PrepareNextChannel", [], []),
        (
            "ZStackAcquisition",
            ["get_origin", "saving_flag", "saving_dir"],
            [False, False, "z-stack"],
        ),
        ("ChangeResolution", ["resolution_mode", "zoom_value"], ["high", "N/A"]),
        ("LoopByCount", ["steps"], [1]),
        ("LoopByCount", ["steps"], ["experiment.MicroscopeState.selected_channels"]),
    ],
)
def test_feature_config_popup(feature_name, args_name, args_value, tk_root):
    features = [
        "PrepareNextChannel",
        "ZStackAcquisition",
        "ChangeResolution",
        "LoopByCount",
    ]
    config_popup = FeatureConfigPopup(
        tk_root,
        features,
        feature_name=feature_name,
        args_name=args_name,
        args_value=args_value,
        title="Test",
    )
    tk_root.update()
    assert config_popup.feature_name_widget.get() == feature_name
    widgets = config_popup.get_widgets()
    assert len(widgets) == len(args_name)
    for i, w in enumerate(widgets):
        assert w.label["text"] == args_name[i] + ":"
        if type(args_value[i]) is bool:
            assert isinstance(w.widget, ttk.Combobox)
            assert w.widget["values"] == ("True", "False")
        else:
            assert isinstance(w.widget, ttk.Entry)

        assert w.get() == str(args_value[i])


@pytest.mark.parametrize("title", [("Add Feature List"), ("Edit Feature Parameters")])
def test_feature_list_popup(title, tk_root):
    feature_list_popup = FeatureListPopup(tk_root, title=title)
    tk_root.update()

    assert len(feature_list_popup.inputs.keys()) == 2
    assert "feature_list_name" in feature_list_popup.inputs
    assert "content" in feature_list_popup.inputs

    assert len(feature_list_popup.buttons.keys()) == 3
    assert "preview" in feature_list_popup.buttons
    assert "cancel" in feature_list_popup.buttons
    assert feature_list_popup.buttons["preview"]["text"] == "Preview"
    assert feature_list_popup.buttons["cancel"]["text"] == "Cancel"

    if title.startswith("Add"):
        assert "add" in feature_list_popup.buttons
        assert feature_list_popup.buttons["add"]["text"] == "Add"
    else:
        assert "confirm" in feature_list_popup.buttons
        assert feature_list_popup.buttons["confirm"]["text"] == "Confirm"
