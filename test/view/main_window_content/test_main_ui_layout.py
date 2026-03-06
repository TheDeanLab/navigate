import tkinter as tk
from tkinter import ttk

from navigate.view.main_window_content.acquire_notebook import AcquireBar
from navigate.view.main_window_content.settings_notebook import SettingsNotebook


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
