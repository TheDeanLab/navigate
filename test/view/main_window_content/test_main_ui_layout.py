import tkinter as tk
from tkinter import ttk

from navigate.view.main_window_content.acquire_notebook import AcquireBar
from navigate.view.main_window_content.settings_notebook import SettingsNotebook
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


def test_acquire_bar_uses_weighted_progress_layout(tk_root):
    host = ttk.Frame(tk_root)
    host.grid(row=0, column=0, sticky=tk.NSEW)

    acquire_bar = AcquireBar(host, tk_root)
    tk_root.update_idletasks()

    assert acquire_bar.grid_info()["sticky"] == "nesw"
    assert acquire_bar.grid_columnconfigure(2)["weight"] == 1
    assert acquire_bar.progBar_frame.grid_columnconfigure(0)["weight"] == 1
    assert acquire_bar.progBar_frame.grid_rowconfigure(1)["weight"] == 1

    host.destroy()


def test_settings_notebook_tabs_use_weighted_main_layout(tk_root):
    host = ttk.Frame(tk_root)
    host.grid(row=0, column=0, sticky=tk.NSEW)

    settings_notebook = SettingsNotebook(host, tk_root)
    tk_root.update_idletasks()

    assert settings_notebook.grid_columnconfigure(0)["weight"] == 1
    assert settings_notebook.grid_rowconfigure(0)["weight"] == 1

    assert settings_notebook.channels_tab.grid_rowconfigure(0)["weight"] == 3
    assert settings_notebook.channels_tab.grid_rowconfigure(3)["weight"] == 1
    assert settings_notebook.camera_settings_tab.grid_columnconfigure(1)["weight"] == 1
    assert settings_notebook.camera_settings_tab.grid_rowconfigure(1)["weight"] == 2
    assert settings_notebook.stage_control_tab.grid_columnconfigure(2)["weight"] == 1
    assert settings_notebook.stage_control_tab.grid_rowconfigure(3)["weight"] == 1
    assert settings_notebook.multiposition_tab.grid_columnconfigure(0)["weight"] == 1
    assert settings_notebook.multiposition_tab.grid_rowconfigure(1)["weight"] == 1

    host.destroy()


def test_channels_tab_forms_use_themed_spacing(tk_root):
    host = ttk.Frame(tk_root)
    host.grid(row=0, column=0, sticky=tk.NSEW)

    settings_notebook = SettingsNotebook(host, tk_root)
    tk_root.update_idletasks()

    stack_frame = settings_notebook.channels_tab.stack_acq_frame
    timepoint_frame = settings_notebook.channels_tab.stack_timepoint_frame
    multipoint_frame = settings_notebook.channels_tab.multipoint_frame
    quick_launch = settings_notebook.channels_tab.quick_launch

    assert _grid_padding_pair(stack_frame.inputs["start_position"].grid_info()["padx"]) == (
        get_theme_padding_px((6, 0))
    )
    assert _grid_padding_pair(stack_frame.inputs["start_position"].grid_info()["pady"]) == (
        get_theme_space_px(2),
        get_theme_space_px(2),
    )
    assert _grid_padding_pair(stack_frame.inputs["z_offset"].grid_info()["pady"]) == (
        get_theme_space_px(5),
        get_theme_space_px(5),
    )
    assert _grid_padding_pair(timepoint_frame.laser_label.grid_info()["padx"]) == (
        get_theme_padding_px((4, 5))
    )
    assert _grid_padding_pair(timepoint_frame.total_time_spinval.grid_info()["pady"]) == (
        get_theme_padding_px((2, 6))
    )
    assert _grid_padding_pair(multipoint_frame.buttons["tiling"].grid_info()["padx"]) == (
        get_theme_padding_px((10, 0))
    )
    assert _grid_padding_pair(
        quick_launch.buttons["waveform_parameters"].grid_info()["padx"]
    ) == get_theme_padding_px((4, 4))

    host.destroy()
