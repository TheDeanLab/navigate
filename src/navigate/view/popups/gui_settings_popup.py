# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""View for editing active non-theme GUI settings."""

from typing import Any
import tkinter as tk
from tkinter import messagebox, ttk

from navigate.view.custom_widgets.popup import PopUp
from navigate.view.custom_widgets.validation import ValidatedEntry
from navigate.view.theme import get_theme_color, get_theme_space_px


class GuiSettingsPopup:
    """Themed popup that presents GUI settings supplied by its controller."""

    def __init__(self, root: tk.Tk) -> None:
        self.popup = PopUp(
            root,
            name="GUI Settings",
            size="680x520+320+180",
            top=False,
            transient=False,
        )
        self.popup.resizable(tk.TRUE, tk.TRUE)
        self.entries: dict[tuple[str, ...], tuple[tk.StringVar, ValidatedEntry]] = {}
        self.boolean_variables: dict[tuple[str, ...], tk.BooleanVar] = {}

        frame = self.popup.get_frame()
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            frame,
            background=get_theme_color("panel_bg", "#1a212b"),
            highlightthickness=0,
            borderwidth=0,
        )
        self.canvas.grid(
            row=0,
            column=0,
            padx=(get_theme_space_px(8), 0),
            pady=get_theme_space_px(4),
            sticky="nsew",
        )
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        scrollbar.grid(
            row=0,
            column=1,
            padx=(0, get_theme_space_px(8)),
            pady=get_theme_space_px(4),
            sticky="ns",
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.settings_frame = ttk.Frame(self.canvas, style="Popup.TFrame")
        self.settings_frame.columnconfigure(0, weight=1)
        self.window_id = self.canvas.create_window(
            (0, 0), window=self.settings_frame, anchor="nw"
        )
        self.settings_frame.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_settings_frame)

        footer = ttk.Frame(frame, style="Popup.TFrame")
        footer.grid(
            row=1,
            column=0,
            columnspan=2,
            padx=get_theme_space_px(8),
            pady=get_theme_space_px(4),
            sticky="ew",
        )
        footer.grid_anchor("e")
        buttons = ttk.Frame(footer, style="Popup.TFrame")
        buttons.grid(row=0, column=0, sticky="e")
        self.buttons = {
            "apply": ttk.Button(buttons, text="Apply"),
            "close": ttk.Button(buttons, text="Close"),
        }
        self.buttons["apply"].grid(row=0, column=0, padx=get_theme_space_px(3))
        self.buttons["close"].grid(row=0, column=1, padx=get_theme_space_px(3))

    def populate_settings(self, fields: list[dict[str, Any]]) -> None:
        """Create grouped controls from controller-provided field descriptions."""
        for child in self.settings_frame.winfo_children():
            child.destroy()
        self.entries.clear()
        self.boolean_variables.clear()

        groups: dict[str, ttk.LabelFrame] = {}
        group_rows: dict[str, int] = {}
        for field in fields:
            group_name = field["group"]
            if group_name not in groups:
                group_frame = ttk.LabelFrame(self.settings_frame, text=group_name)
                group_frame.columnconfigure(1, weight=1)
                group_frame.grid(
                    row=len(groups),
                    column=0,
                    padx=get_theme_space_px(4),
                    pady=get_theme_space_px(4),
                    sticky="ew",
                )
                groups[group_name] = group_frame
                group_rows[group_name] = 0

            group_frame = groups[group_name]
            row = group_rows[group_name]
            group_rows[group_name] += 1
            ttk.Label(group_frame, text=field["label"]).grid(
                row=row,
                column=0,
                padx=get_theme_space_px(8),
                pady=get_theme_space_px(3),
                sticky="w",
            )

            path = field["path"]
            if field["type"] == "boolean":
                value_var = tk.BooleanVar(value=bool(field["value"]))
                ttk.Checkbutton(group_frame, variable=value_var).grid(
                    row=row,
                    column=1,
                    padx=get_theme_space_px(8),
                    pady=get_theme_space_px(3),
                    sticky="w",
                )
                self.boolean_variables[path] = value_var
                continue

            value_var = tk.StringVar(value=str(field["value"]))
            entry = ValidatedEntry(
                group_frame,
                textvariable=value_var,
                width=34,
                required=True,
                precision="1" if field["type"] == "integer" else "0.000000001",
                min=field["minimum"],
                max="Infinity",
            )
            entry.grid(
                row=row,
                column=1,
                padx=get_theme_space_px(8),
                pady=get_theme_space_px(3),
                sticky="ew",
            )
            self.entries[path] = (value_var, entry)

    def set_status(self, message: str) -> None:
        """Retain the view interface without displaying a footer message."""

    def show_info(self, title: str, message: str) -> None:
        """Show an informational dialog associated with this popup."""
        messagebox.showinfo(title=title, message=message, parent=self.popup)

    def showup(self) -> None:
        """Restore and focus the settings window."""
        self.popup.deiconify()
        self.popup.lift()
        self.popup.focus_force()

    def _update_scroll_region(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_settings_frame(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)
