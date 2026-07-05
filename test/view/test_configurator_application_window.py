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

from tkinter import ttk

from navigate.view.custom_widgets.CollapsibleFrame import CollapsibleFrame
from navigate.view.configurator_application_window import ConfigurationAssistantWindow
from navigate.view.configurator_application_window import HardwareTab
from navigate.view.theme import get_theme_padding_px, get_theme_space_px


def _grid_padding_pair(value):
    text = str(value).strip()
    if text.startswith("(") and text.endswith(")"):
        parts = [int(part.strip()) for part in text[1:-1].split(",") if part.strip()]
    else:
        parts = [int(part) for part in text.split()]
    if len(parts) == 1:
        return (parts[0], parts[0])
    return tuple(parts)


def test_configurator_top_window_uses_ttk_buttons(tk_root):
    view = ConfigurationAssistantWindow(tk_root)
    tk_root.update_idletasks()

    top = view.top_window

    assert isinstance(top.new_button, ttk.Button)
    assert isinstance(top.load_button, ttk.Button)
    assert isinstance(top.add_button, ttk.Button)
    assert isinstance(top.save_button, ttk.Button)
    assert isinstance(top.cancel_button, ttk.Button)

    top.new_button.destroy()
    top.load_button.destroy()
    top.add_button.destroy()
    top.save_button.destroy()
    top.cancel_button.destroy()
    view.destroy()


def test_configurator_window_uses_themed_spacing(tk_root):
    view = ConfigurationAssistantWindow(tk_root)
    tk_root.update_idletasks()

    assert _grid_padding_pair(view.top_frame.grid_info()["padx"]) == (
        get_theme_space_px(3),
        get_theme_space_px(3),
    )
    assert _grid_padding_pair(view.microscope_frame.grid_info()["pady"]) == (
        get_theme_space_px(3),
        get_theme_space_px(3),
    )
    assert _grid_padding_pair(view.top_window.new_button.grid_info()["pady"]) == (
        get_theme_padding_px((10, 1))
    )

    view.top_window.new_button.destroy()
    view.top_window.load_button.destroy()
    view.top_window.add_button.destroy()
    view.top_window.save_button.destroy()
    view.top_window.cancel_button.destroy()
    view.destroy()


def test_collapsible_frame_header_uses_themed_spacing(tk_root):
    frame = CollapsibleFrame(tk_root, title="Hardware")
    frame.grid(row=0, column=0, sticky="nsew")
    tk_root.update_idletasks()

    assert int(frame.label.cget("padx")) == get_theme_space_px(5)

    frame.destroy()


def test_hardware_tab_stores_wizard_metadata(tk_root):
    metadata = {
        "device_field": "hardware/type",
        "steps": ["Device Type", "Timing"],
        "fields": {
            "hardware/type": {"step": "Device Type", "importance": "required"},
            "delay": {"step": "Timing", "importance": "recommended"},
        },
    }
    widgets = {
        "hardware/type": [
            "Device Type",
            "Combobox",
            "string",
            {"Virtual": "Synthetic"},
            None,
        ],
        "delay": ["Delay", "Spinbox", "float", {"from": 0, "to": 10}, None],
    }

    tab = HardwareTab("Camera", widgets, root=tk_root, wizard_metadata=metadata)
    tk_root.update_idletasks()

    assert tab.wizard_metadata == metadata
    assert tab.wizard_steps == ["Device Type", "Timing"]
    assert tab.current_step.get() == "Device Type"

    tab.destroy()


def test_hardware_tab_builds_wizard_shell(tk_root):
    metadata = {
        "steps": ["Device Type", "Timing"],
        "fields": {
            "hardware/type": {"step": "Device Type", "importance": "required"},
            "delay": {"step": "Timing", "importance": "recommended"},
        },
    }
    widgets = {
        "hardware/type": [
            "Device Type",
            "Combobox",
            "string",
            {"Virtual": "Synthetic"},
            None,
        ],
        "delay": ["Delay", "Spinbox", "float", {"from": 0, "to": 10}, None],
    }

    tab = HardwareTab("Camera", widgets, root=tk_root, wizard_metadata=metadata)
    tk_root.update_idletasks()

    assert isinstance(tab.step_frame, ttk.Frame)
    assert isinstance(tab.field_frame, ttk.Frame)
    assert isinstance(tab.help_frame, ttk.Frame)
    assert len(tab.step_buttons) == 2
    assert "Device Type" in tab.step_buttons
    assert "Timing" in tab.step_buttons

    tab.destroy()


def test_hardware_tab_filters_fields_by_step_and_advanced_mode(tk_root):
    metadata = {
        "device_field": "hardware/type",
        "steps": ["Device Type", "Connection"],
        "fields": {
            "hardware/type": {"step": "Device Type", "importance": "required"},
            "hardware/camera_connection": {
                "step": "Connection",
                "importance": "advanced",
                "applies_to": ["Photometrics Iris 15B"],
            },
        },
    }
    widgets = {
        "hardware/type": [
            "Device Type",
            "Combobox",
            "string",
            {"Photometrics Iris 15B": "Photometrics", "Virtual Device": "Synthetic"},
            None,
        ],
        "hardware/camera_connection": [
            "Camera Connection",
            "Input",
            "string",
            None,
            "Photometrics Iris 15B only",
        ],
    }

    tab = HardwareTab("Camera", widgets, root=tk_root, wizard_metadata=metadata)
    tk_root.update_idletasks()

    assert tab.field_rows["hardware/type"].winfo_ismapped()
    assert not tab.field_rows["hardware/camera_connection"].winfo_ismapped()

    tab.select_wizard_step("Connection")
    tk_root.update_idletasks()
    assert not tab.field_rows["hardware/camera_connection"].winfo_ismapped()

    tab.advanced_mode.set(True)
    tab.refresh_wizard_visibility()
    tk_root.update_idletasks()
    assert tab.field_rows["hardware/camera_connection"].winfo_ismapped()

    tab.destroy()
