"""Advanced laser settings and readbacks."""

import tkinter as tk
from tkinter import ttk

from navigate.view.custom_widgets.popup import PopUp
from navigate.view.theme import get_theme_space_px


class AdvancedLaserSettingPopup:
    """Nonmodal settings view; all hardware interactions belong to the model.

    Parameters
    ----------
    root : tkinter.Misc
        Application window owning this popup.
    """

    def __init__(self, root: tk.Misc) -> None:
        #: PopUp: Nonmodal advanced settings window.
        self.popup = PopUp(
            root, "Advanced Laser Settings", "+320+180", top=False, transient=False
        )
        frame = self.popup.content_frame
        frame.columnconfigure(1, weight=1)
        pad = get_theme_space_px(6)
        #: dict: Tk variables read and updated only on the main thread.
        self.variables = {}
        #: dict: Selection widgets.
        self.inputs = {}
        #: dict: Action buttons.
        self.buttons = {}
        for row, (key, label) in enumerate(
            (
                ("microscope", "Microscope"),
                ("laser", "Laser"),
                ("mode", "Modulation mode"),
            )
        ):
            self.variables[key] = tk.StringVar(frame)
            ttk.Label(frame, text=label).grid(
                row=row, column=0, padx=pad, pady=pad, sticky="w"
            )
            self.inputs[key] = ttk.Combobox(
                frame, textvariable=self.variables[key], state="readonly", width=32
            )
            self.inputs[key].grid(row=row, column=1, padx=pad, pady=pad, sticky="ew")
        self.buttons["apply"] = ttk.Button(frame, text="Apply mode")
        self.buttons["apply"].grid(row=2, column=2, padx=pad, pady=pad)
        fields = (
            ("connection", "Connection"),
            ("device_identity", "Device"),
            ("power_source", "Channel power source"),
            ("limits", "Internal power limits"),
            ("reference", "100% channel power"),
            ("current_mode", "Confirmed mode"),
            ("acquisition_mode", "Next acquisition mode"),
            ("setpoint", "Internal power setpoint"),
            ("measured", "Reported output power"),
            ("emission", "Emission enabled"),
            ("read_at", "Last read (UTC)"),
        )
        for row, (key, label) in enumerate(fields, start=3):
            self.variables[key] = tk.StringVar(frame, value="Unknown")
            ttk.Label(frame, text=label).grid(
                row=row, column=0, padx=pad, pady=pad, sticky="w"
            )
            ttk.Label(
                frame,
                textvariable=self.variables[key],
                wraplength=get_theme_space_px(360),
            ).grid(row=row, column=1, columnspan=2, padx=pad, pady=pad, sticky="w")
        self.variables["status"] = tk.StringVar(frame)
        ttk.Label(
            frame,
            textvariable=self.variables["status"],
            wraplength=get_theme_space_px(530),
        ).grid(row=14, column=0, columnspan=3, padx=pad, pady=pad, sticky="w")
        ttk.Label(
            frame,
            text="Mode changes apply for this session. Set channel power in Channels.\nReadbacks are at the laser; sample power may differ.",
            wraplength=get_theme_space_px(530),
        ).grid(row=15, column=0, columnspan=3, padx=pad, pady=pad, sticky="w")
        self.buttons["refresh"] = ttk.Button(frame, text="Refresh")
        self.buttons["refresh"].grid(row=16, column=1, padx=pad, pady=pad, sticky="e")
        self.buttons["close"] = ttk.Button(frame, text="Close")
        self.buttons["close"].grid(row=16, column=2, padx=pad, pady=pad)
