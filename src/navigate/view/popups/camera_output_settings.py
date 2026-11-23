"""Hamamatsu timing-output editor; editing never communicates with hardware."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Any

from navigate.model.devices.camera.hamamatsu_outputs import applicable, FIELDS, SHARED
from navigate.tools.common_functions import copy_proxy_object
from navigate.view.theme import get_theme_color

FIELD_LABELS = {
    "kind": "Output function",
    "source": "Reference signal",
    "polarity": "Polarity",
    "active": "Active behavior",
    "delay_s": "Delay (seconds)",
    "pulse_width_s": "Pulse duration (seconds)",
    "base_sensor": "Base sensor",
    "pre_hsync_count": "Pre-Hsync pulses",
    "channel_sync": "Channel synchronization",
    "programmable_start": "Programmable start",
}


class CameraOutputSettings(ttk.LabelFrame):
    """Edit independent physical connectors, with one explicit application action."""

    def __init__(self, parent: tk.Misc, command: Callable[[], None]) -> None:
        super().__init__(parent, text="Hamamatsu Timing Outputs")
        self.command = command
        self.fields = {}
        self.caps = {}
        self.busy = True
        self.dirty = False
        self.edited = False
        self.saved = {}
        self._layout = None
        self._populating = False
        self._range_labels = {}
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.status = tk.StringVar()
        status_frame = ttk.Frame(self)
        status_frame.grid(row=1, column=0, sticky="ew", padx=8)
        status_frame.columnconfigure(0, weight=1)
        self.status_text = tk.Text(
            status_frame,
            width=46,
            height=3,
            wrap="word",
            font="TkDefaultFont",
            background=get_theme_color("panel_bg", "#1a212b"),
            foreground=get_theme_color("text", "white"),
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            state="disabled",
            takefocus=False,
        )
        self.status_text.grid(row=0, column=0, sticky="ew")
        scrollbar = ttk.Scrollbar(
            status_frame, orient="vertical", command=self.status_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.status_text.configure(yscrollcommand=scrollbar.set)
        self.status.trace_add("write", self._display_status)
        self.apply_button = ttk.Button(self, text="Apply Outputs", command=command)
        self.apply_button.grid(row=2, column=0, sticky="e", padx=8, pady=8)
        ttk.Label(
            self,
            text="Vsync is readout start. Outputs are electrical control signals.\nChanges apply while stopped; switching is not guaranteed glitch-free.",
            wraplength=370,
        ).grid(row=3, column=0, padx=8, pady=8, sticky="w")

    def populate(
        self, capabilities: dict, saved: Optional[dict] = None, busy: bool = False
    ) -> None:
        """Refresh existing controls, rebuilding only when available fields change."""
        self.caps = capabilities
        self.busy = busy or bool(capabilities.get("reason"))
        self.dirty = False
        self.edited = False
        saved = saved or {}
        self.saved = copy_proxy_object(saved)
        groups = dict(capabilities.get("connectors", {}))
        if any(c.get("available") for c in capabilities.get("shared", {}).values()):
            groups["shared"] = capabilities["shared"]
        groups = {
            number: {name: cap for name, cap in fields.items() if cap.get("available")}
            for number, fields in groups.items()
        }
        layout = tuple((number, tuple(fields)) for number, fields in groups.items())
        if layout != self._layout:
            self._build_controls(groups)
            self._layout = layout
        # Traces distinguish user edits from confirmed model readbacks. Update all
        # values before evaluating dependencies between function/source and timing.
        self._populating = True
        try:
            self._refresh_controls(groups, saved)
        finally:
            self._populating = False
        self.status.set(
            capabilities.get("reason")
            or (
                "Saved selections differ from the camera. Apply Outputs to restore them."
                if self.dirty
                else "Read from camera. Apply Outputs updates the experiment; Save also stores camera defaults."
            )
        )
        self.lock(self.busy)

    def _build_controls(self, groups: dict) -> None:
        """Build the available connector fields, retaining the selected connector."""
        selected = self.notebook.select()
        selected_label = self.notebook.tab(selected, "text") if selected else None
        for child in self.notebook.winfo_children():
            child.destroy()
        self.fields = {}
        self._range_labels = {}
        for number, fields in groups.items():
            frame = ttk.Frame(self.notebook)
            label = "Shared" if number == "shared" else f"TIMING {number}"
            self.notebook.add(frame, text=label)
            if label == selected_label:
                self.notebook.select(frame)
            for row, (name, cap) in enumerate(fields.items()):
                ttk.Label(frame, text=FIELD_LABELS[name]).grid(
                    row=row * 2, column=0, sticky="w", padx=5, pady=4
                )
                variable = tk.StringVar()
                widget = (
                    ttk.Combobox(
                        frame,
                        textvariable=variable,
                        width=25,
                    )
                    if (SHARED if number == "shared" else FIELDS)[name][1] is not None
                    else ttk.Entry(frame, textvariable=variable, width=27)
                )
                widget.grid(row=row * 2, column=1, padx=5, pady=4)
                self.fields[number, name] = (widget, variable, cap)
                if isinstance(widget, ttk.Entry) and not isinstance(
                    widget, ttk.Combobox
                ):
                    label = ttk.Label(frame)
                    label.grid(row=row * 2 + 1, column=1, sticky="w", padx=5)
                    self._range_labels[number, name] = label
                variable.trace_add("write", self._changed)

    def _refresh_controls(self, groups: dict, saved: dict) -> None:
        """Update values, choices and ranges without replacing widgets or variables."""
        for number, fields in groups.items():
            stored = (
                saved.get("shared", {})
                if number == "shared"
                else saved.get("connectors", {}).get(number, {})
            )
            for name, cap in fields.items():
                widget, variable, _ = self.fields[number, name]
                self.fields[number, name] = (widget, variable, cap)
                choices = cap.get("choices", {})
                if isinstance(widget, ttk.Combobox):
                    widget.configure(values=list(choices.values()))
                current = cap.get("current")
                if name in stored:
                    if (number == "shared" or applicable(name, stored)) and stored[
                        name
                    ] != current:
                        self.dirty = True
                    current = stored[name]
                variable.set(
                    choices.get(current, str(current))
                    if current is not None
                    else "Unknown"
                )
                if (number, name) in self._range_labels:
                    self._range_labels[number, name].configure(
                        text=f"Range {cap.get('minimum'):g} to {cap.get('maximum'):g}; step {cap.get('step'):g}",
                    )

    def _display_status(self, *args: str) -> None:
        """Keep status geometry fixed and allow scrolling through long errors."""
        self.status_text.configure(state="normal")
        self.status_text.delete("1.0", "end")
        self.status_text.insert("1.0", self.status.get())
        self.status_text.configure(state="disabled")
        self.status_text.yview_moveto(0)

    def _changed(self, *args: str) -> None:
        if self._populating:
            return
        self.dirty = True
        self.edited = True
        self.status.set("Unapplied output changes.")
        self.lock(self.busy)

    def _value(self, number: str, name: str) -> Any:
        _, variable, cap = self.fields[number, name]
        text = variable.get()
        if text == "Unknown" and cap.get("current") is None:
            return None
        choices = cap.get("choices", {})
        if (SHARED if number == "shared" else FIELDS)[name][1] is not None:
            return next((v for v, label in choices.items() if label == text), None)
        try:
            return float(text)
        except ValueError:
            raise ValueError(
                f"TIMING {number}: enter a number for {FIELD_LABELS[name]}."
            )

    def selection(self) -> dict:
        """Return the draft; the model validates every value again."""
        result = copy_proxy_object(self.saved) or {"version": 1, "connectors": {}}
        for number, name in self.fields:
            value = self._value(number, name)
            if value is None:
                continue
            target = (
                result.setdefault("shared", {})
                if number == "shared"
                else result["connectors"].setdefault(number, {})
            )
            target[name] = value
        return result

    def lock(self, busy: bool = True) -> None:
        """Disable writes while capture or another camera transaction owns the device."""
        self.busy = busy
        for (number, name), (widget, _, cap) in self.fields.items():
            selected = {
                key: self._value(number, key)
                for key in ("kind", "source")
                if (number, key) in self.fields
            }
            enabled = (
                not busy
                and cap.get("writable")
                and (number == "shared" or applicable(name, selected))
            )
            widget.configure(
                state=(
                    ("readonly" if isinstance(widget, ttk.Combobox) else "normal")
                    if enabled
                    else "disabled"
                )
            )
        self.apply_button.configure(
            state="normal" if not busy and self.fields else "disabled"
        )
