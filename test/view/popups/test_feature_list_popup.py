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

import tkinter as tk
from tkinter import ttk
import pytest

# Local Imports
from navigate.view.popups.feature_list_popup import (
    FeatureCollectionInput,
    FeatureIcon,
    FeatureConfigPopup,
    FeatureListPopup,
)
from navigate.config.configuration_schema import CollectionSpec, SettingSpec
from navigate.view.custom_widgets.validation import ValidatedSpinbox


# @pytest.fixture
# def tk_root():
#     root = tk.Tk()
#     yield root
#     root.destroy()


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
        ("LoopByCount", ["steps"], ["channels"]),
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
        elif type(args_value[i]) in (int, float):
            assert isinstance(w.widget, ValidatedSpinbox)
        else:
            assert isinstance(w.widget, ttk.Entry)

        assert w.get() == str(args_value[i])


def test_feature_config_popup_renders_dynamic_zoom_choices_as_readonly_combobox(
    tk_root,
):
    """Runtime zoom choices render as a non-editable combobox."""
    config_popup = FeatureConfigPopup(
        tk_root,
        ["ChangeResolution"],
        feature_name="ChangeResolution",
        args_name=["zoom_value"],
        args_value=["4x"],
        parameter_schema={
            "zoom_value": SettingSpec(
                str,
                default="4x",
                choices=("1x", "4x", "10x"),
            )
        },
        title="Test",
    )
    tk_root.update()

    zoom_widget = config_popup.inputs_by_name["zoom_value"].widget

    assert isinstance(zoom_widget, ttk.Combobox)
    assert str(zoom_widget["state"]) == "readonly"
    assert zoom_widget["values"] == ("1x", "4x", "10x")
    assert config_popup.inputs_by_name["zoom_value"].get() == "4x"


def test_feature_config_popup_displays_feature_description(tk_root):
    """The parameter editor shows optional feature-level help text."""
    config_popup = FeatureConfigPopup(
        tk_root,
        ["ChangeResolution"],
        feature_name="ChangeResolution",
        args_name=[],
        args_value=[],
        feature_description="Switch to another microscope resolution.",
        title="Test",
    )
    tk_root.update()

    assert (
        config_popup.feature_description.get()
        == "Switch to another microscope resolution."
    )
    assert config_popup.feature_description_widget.winfo_ismapped()

    config_popup.set_feature_description("")
    tk_root.update()

    assert not config_popup.feature_description_widget.winfo_ismapped()


def test_feature_config_popup_renders_single_mapping_collection(tk_root):
    """Single-mapping collections render as grouped feature parameter inputs."""
    config_popup = FeatureConfigPopup(
        tk_root,
        ["Autofocus"],
        feature_name="Autofocus",
        args_name=["scan_settings"],
        args_value=[
            {
                "coarse_selected": False,
                "coarse_range": 250,
                "coarse_step_size": 25,
            }
        ],
        parameter_schema={
            "scan_settings": CollectionSpec(
                item_schema={
                    "coarse_selected": SettingSpec(bool, default=True, label="Coarse"),
                    "coarse_range": SettingSpec(
                        float,
                        default=500,
                        label="Coarse Range",
                        minimum=0,
                        step=1,
                        required=True,
                    ),
                    "coarse_step_size": SettingSpec(
                        float,
                        default=50,
                        label="Coarse Step",
                        minimum=0,
                        step=1,
                        required=True,
                    ),
                },
                storage="single_mapping",
                label="Scan Settings",
            )
        },
        title="Test",
    )
    tk_root.update()

    scan_settings_input = config_popup.inputs_by_name["scan_settings"]

    assert isinstance(scan_settings_input, FeatureCollectionInput)
    assert scan_settings_input.widget["text"] == "Scan Settings"
    assert isinstance(scan_settings_input.widgets["coarse_selected"], ttk.Combobox)
    assert isinstance(scan_settings_input.widgets["coarse_range"], ValidatedSpinbox)
    assert scan_settings_input.get() == {
        "coarse_selected": "False",
        "coarse_range": "250",
        "coarse_step_size": "25",
    }


def test_feature_config_popup_collection_none_option_returns_none(tk_root):
    """Nullable collections render a checkbox that returns None when selected."""
    config_popup = FeatureConfigPopup(
        tk_root,
        ["Autofocus"],
        feature_name="Autofocus",
        args_name=["scan_settings"],
        args_value=[None],
        parameter_schema={
            "scan_settings": CollectionSpec(
                item_schema={
                    "coarse_selected": SettingSpec(bool, default=True, label="Coarse"),
                    "coarse_range": SettingSpec(
                        float,
                        default=500,
                        label="Coarse Range",
                        minimum=0,
                        step=1,
                        required=True,
                    ),
                },
                storage="single_mapping",
                label="Scan Settings",
                none_option_label="Use system default",
            )
        },
        title="Test",
    )
    tk_root.update()

    scan_settings_input = config_popup.inputs_by_name["scan_settings"]

    assert scan_settings_input.default_widget["text"] == "Use system default"
    assert scan_settings_input.use_none.get() is True
    assert scan_settings_input.widgets["coarse_range"]["state"] == tk.DISABLED
    assert scan_settings_input.get() is None

    scan_settings_input.use_none.set(False)
    scan_settings_input.sync_widget_state()

    assert scan_settings_input.widgets["coarse_range"]["state"] == tk.NORMAL
    assert scan_settings_input.get() == {
        "coarse_selected": "True",
        "coarse_range": "500",
    }


def test_feature_config_popup_renders_dict_collection_field_as_text(tk_root):
    """Dict fields render as readable multi-line literals."""

    class ProxyMapping:
        def __init__(self, values):
            self.values = values

        def __repr__(self):
            return "<DictProxy object, typeid 'dict'>"

        def items(self):
            return self.values.items()

    channels = ProxyMapping(
        {
            "channel_1": ProxyMapping(
                {
                    "is_selected": True,
                    "laser": "488nm",
                    "camera_exposure_time": 200.0,
                }
            )
        }
    )
    config_popup = FeatureConfigPopup(
        tk_root,
        ["UpdateExperimentSetting"],
        feature_name="UpdateExperimentSetting",
        args_name=["experiment_parameters"],
        args_value=[{"MicroscopeState.channels": channels}],
        parameter_schema={
            "experiment_parameters": CollectionSpec(
                item_schema={
                    "MicroscopeState.channels": SettingSpec(
                        dict,
                        default={},
                        label="Channels",
                    ),
                },
                storage="single_mapping",
                label="Experiment Parameters",
            )
        },
        title="Test",
    )
    tk_root.update()

    collection_input = config_popup.inputs_by_name["experiment_parameters"]
    channels_widget = collection_input.widgets["MicroscopeState.channels"]
    channels_text = channels_widget.get("1.0", "end-1c")

    assert isinstance(channels_widget, tk.Text)
    assert "'channel_1'" in channels_text
    assert "'laser': '488nm'" in channels_text
    assert "DictProxy object" not in channels_text
    assert collection_input.get()["MicroscopeState.channels"] == channels_text


@pytest.mark.parametrize("title", ["Add Feature List", "Edit Feature Parameters"])
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
