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

"""Global GUI theming helpers."""

# Standard Library Imports
from __future__ import annotations
from typing import Any
import tkinter as tk
from tkinter import ttk

# Third Party Imports
try:
    from PIL import Image, ImageDraw, ImageTk
except ImportError:  # pragma: no cover - optional fallback
    Image = None
    ImageDraw = None
    ImageTk = None

# Local Imports


_DEFAULT_THEME_PRESET = "classic_night"

_THEME_PRESETS: dict[str, dict[str, str]] = {
    "classic_night": {
        "window_bg": "#11161d",
        "panel_bg": "#1a212b",
        "surface_bg": "#202938",
        "input_bg": "#121923",
        "border": "#2f3a4a",
        "text": "#d7dee8",
        "muted_text": "#9aa8bb",
        "accent": "#4b78b8",
        "accent_hover": "#5a88c9",
        "accent_pressed": "#3f679d",
        "danger": "#b84a4a",
        "success": "#4f8a5b",
        "tooltip_description_bg": "#283243",
        "tooltip_error_bg": "#b84a4a",
        "tooltip_text": "#d7dee8",
    }
}

_ACTIVE_PALETTE: dict[str, str] = dict(_THEME_PRESETS[_DEFAULT_THEME_PRESET])
_THEME_IMAGES: dict[str, tk.PhotoImage] = {}


def _to_dict(data: Any) -> dict[str, Any]:
    """Safely convert manager-proxy mappings and plain mappings to dict."""
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    try:
        return dict(data)
    except TypeError:
        return {}


def _get_nested(mapping: Any, keys: tuple[str, ...], default: Any) -> Any:
    """Fetch nested values from plain dicts or manager-proxy dicts."""
    current = mapping
    for key in keys:
        if current is None:
            return default
        if hasattr(current, "get"):
            current = current.get(key)
        else:
            try:
                current = current[key]
            except (TypeError, KeyError):
                return default
    return default if current is None else current


def _safe_style_configure(style: ttk.Style, name: str, **kwargs: Any) -> None:
    """Configure style keys while tolerating platform-specific unsupported options."""
    for key, value in kwargs.items():
        try:
            style.configure(name, **{key: value})
        except tk.TclError:
            continue


def _safe_style_map(style: ttk.Style, name: str, **kwargs: Any) -> None:
    """Map style keys while tolerating platform-specific unsupported options."""
    for key, value in kwargs.items():
        try:
            style.map(name, **{key: value})
        except tk.TclError:
            continue


def _rounded_photo(
    root: tk.Tk,
    image_name: str,
    fill_color: str,
    border_color: str,
    *,
    width: int,
    height: int,
    radius: int,
    border_width: int = 1,
    corner_bg: str | None = None,
) -> tk.PhotoImage | None:
    """Create and cache a rounded rectangle image for ttk element skins."""
    if Image is None or ImageDraw is None or ImageTk is None:
        return None

    if corner_bg is None:
        background_rgba = (0, 0, 0, 0)
    else:
        # Normalize color through PIL parser to support named/hex colors.
        background_rgba = Image.new("RGBA", (1, 1), corner_bg).getpixel((0, 0))

    image = Image.new("RGBA", (width, height), background_rgba)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (0, 0, width - 1, height - 1),
        radius=max(1, radius),
        fill=fill_color,
        outline=border_color,
        width=max(1, border_width),
    )
    photo = ImageTk.PhotoImage(image, master=root)
    _THEME_IMAGES[image_name] = photo
    return photo


def _apply_rounded_button_styles(
    root: tk.Tk,
    style: ttk.Style,
    *,
    panel_bg: str,
    surface_bg: str,
    border: str,
    text: str,
    muted_text: str,
    accent: str,
    accent_hover: str,
    accent_pressed: str,
    danger: str,
    success: str,
    radius: int = 5,
) -> None:
    """Install rounded image-backed ttk button styles."""
    if Image is None:
        return

    button_h = 32
    button_w = 56
    border_w = 1

    button_states = {
        "neutral": (
            surface_bg,
            accent_hover,
            accent_pressed,
            panel_bg,
        ),
        "accent": (
            accent,
            accent_hover,
            accent_pressed,
            panel_bg,
        ),
        "danger": (
            danger,
            accent_hover,
            accent_pressed,
            panel_bg,
        ),
        "success": (
            success,
            accent_hover,
            accent_pressed,
            panel_bg,
        ),
    }

    def build_element(
        element_prefix: str, fills: tuple[str, str, str, str]
    ) -> str | None:
        normal_fill, active_fill, pressed_fill, disabled_fill = fills
        normal = _rounded_photo(
            root,
            f"{element_prefix}_normal",
            normal_fill,
            border,
            width=button_w,
            height=button_h,
            radius=radius,
            border_width=border_w,
            corner_bg=panel_bg,
        )
        active = _rounded_photo(
            root,
            f"{element_prefix}_active",
            active_fill,
            border,
            width=button_w,
            height=button_h,
            radius=radius,
            border_width=border_w,
            corner_bg=panel_bg,
        )
        pressed = _rounded_photo(
            root,
            f"{element_prefix}_pressed",
            pressed_fill,
            border,
            width=button_w,
            height=button_h,
            radius=radius,
            border_width=border_w,
            corner_bg=panel_bg,
        )
        disabled = _rounded_photo(
            root,
            f"{element_prefix}_disabled",
            disabled_fill,
            border,
            width=button_w,
            height=button_h,
            radius=radius,
            border_width=border_w,
            corner_bg=panel_bg,
        )
        if not all([normal, active, pressed, disabled]):
            return None

        element_name = f"{element_prefix}.border"
        try:
            style.element_create(
                element_name,
                "image",
                normal,
                ("disabled", disabled),
                ("pressed", pressed),
                ("active", active),
                border=radius + 2,
                sticky="nsew",
            )
        except tk.TclError:
            # Element may already exist if theme is reapplied.
            try:
                style.element_names().index(element_name)
                return element_name
            except ValueError:
                return None
        return element_name

    created_elements: dict[str, str] = {}
    for key, fills in button_states.items():
        element = build_element(f"rounded_button_{key}", fills)
        if element is not None:
            created_elements[key] = element

    def apply_layout(style_name: str, element_key: str) -> None:
        if element_key not in created_elements:
            return
        try:
            style.layout(
                style_name,
                [
                    (
                        created_elements[element_key],
                        {
                            "sticky": "nsew",
                            "children": [
                                (
                                    "Button.padding",
                                    {
                                        "sticky": "nsew",
                                        "children": [
                                            ("Button.label", {"sticky": "nsew"})
                                        ],
                                    },
                                )
                            ],
                        },
                    )
                ],
            )
        except tk.TclError:
            return

    apply_layout("TButton", "neutral")
    apply_layout("Accent.TButton", "accent")
    apply_layout("Danger.TButton", "danger")
    apply_layout("Success.TButton", "success")
    apply_layout("StageStop.Danger.TButton", "danger")
    apply_layout("StageHome.Success.TButton", "success")

    _safe_style_map(
        style,
        "TButton",
        foreground=[("disabled", muted_text), ("!disabled", text)],
    )
    _safe_style_map(
        style,
        "Accent.TButton",
        foreground=[("disabled", muted_text), ("!disabled", text)],
    )
    _safe_style_map(
        style,
        "Danger.TButton",
        foreground=[("disabled", muted_text), ("!disabled", text)],
    )
    _safe_style_map(
        style,
        "Success.TButton",
        foreground=[("disabled", muted_text), ("!disabled", text)],
    )


def _apply_rounded_notebook_tabs(
    root: tk.Tk,
    style: ttk.Style,
    *,
    notebook_bg: str,
    panel_bg: str,
    surface_bg: str,
    border: str,
    accent_hover: str,
    muted_text: str,
    text: str,
    radius: int = 3,
) -> None:
    """Install rounded image-backed ttk notebook tabs."""
    if Image is None:
        return

    tab_w = 78
    tab_h = 20
    border_w = 1

    normal = _rounded_photo(
        root,
        "rounded_tab_normal",
        surface_bg,
        border,
        width=tab_w,
        height=tab_h,
        radius=radius,
        border_width=border_w,
        corner_bg=notebook_bg,
    )
    selected = _rounded_photo(
        root,
        "rounded_tab_selected",
        panel_bg,
        border,
        width=tab_w,
        height=tab_h,
        radius=radius,
        border_width=border_w,
        corner_bg=notebook_bg,
    )
    active = _rounded_photo(
        root,
        "rounded_tab_active",
        accent_hover,
        border,
        width=tab_w,
        height=tab_h,
        radius=radius,
        border_width=border_w,
        corner_bg=notebook_bg,
    )
    disabled = _rounded_photo(
        root,
        "rounded_tab_disabled",
        panel_bg,
        border,
        width=tab_w,
        height=tab_h,
        radius=radius,
        border_width=border_w,
        corner_bg=notebook_bg,
    )
    if not all([normal, selected, active, disabled]):
        return

    element_name = "RoundedNotebookTab.border"
    try:
        style.element_create(
            element_name,
            "image",
            normal,
            ("disabled", disabled),
            ("selected", selected),
            ("active", active),
            border=radius + 2,
            sticky="nsew",
        )
    except tk.TclError:
        # Element may already exist if theme is reapplied.
        if element_name not in style.element_names():
            return
    try:
        style.layout(
            "TNotebook.Tab",
            [
                (
                    element_name,
                    {
                        "sticky": "nsew",
                        "children": [
                            (
                                "Notebook.padding",
                                {
                                    "side": "top",
                                    "sticky": "nsew",
                                    "children": [
                                        ("Notebook.label", {"sticky": "nsew"})
                                    ],
                                },
                            )
                        ],
                    },
                )
            ],
        )
        _safe_style_map(
            style,
            "TNotebook.Tab",
            foreground=[
                ("disabled", muted_text),
                ("selected", text),
                ("!disabled", text),
            ],
        )
    except tk.TclError:
        return


def _build_palette(gui_settings: Any) -> tuple[str, dict[str, str], str]:
    """Resolve preset + overrides from gui configuration."""
    theme_settings = _to_dict(_get_nested(gui_settings, ("theme",), {}))
    preset_name = str(theme_settings.get("preset", _DEFAULT_THEME_PRESET))
    base_theme = str(theme_settings.get("ttk_base_theme", "clam"))

    palette = dict(
        _THEME_PRESETS.get(preset_name, _THEME_PRESETS[_DEFAULT_THEME_PRESET])
    )
    palette.update(_to_dict(theme_settings.get("palette")))

    return preset_name, palette, base_theme


def get_theme_color(name: str, fallback: str | None = None) -> str:
    """Return a named theme color from active palette with fallback."""
    if name in _ACTIVE_PALETTE:
        return _ACTIVE_PALETTE[name]
    if fallback is not None:
        return fallback
    return _THEME_PRESETS[_DEFAULT_THEME_PRESET].get(name, "#000000")


def apply_theme(root: tk.Tk, gui_settings: Any = None) -> tuple[str, dict[str, str]]:
    """Apply the global ttk/tk theme to the root and all inheriting popups."""
    global _ACTIVE_PALETTE
    preset_name, palette, preferred_theme = _build_palette(gui_settings)
    _ACTIVE_PALETTE = dict(palette)

    style = ttk.Style(root)
    available = style.theme_names()
    theme_name = preferred_theme if preferred_theme in available else "clam"
    if theme_name not in available:
        theme_name = style.theme_use()
    style.theme_use(theme_name)

    window_bg = palette["window_bg"]
    panel_bg = palette["panel_bg"]
    surface_bg = palette["surface_bg"]
    input_bg = palette["input_bg"]
    border = palette["border"]
    text = palette["text"]
    muted_text = palette["muted_text"]
    accent = palette["accent"]
    accent_hover = palette["accent_hover"]
    accent_pressed = palette["accent_pressed"]
    danger = palette["danger"]
    success = palette["success"]

    root.configure(bg=window_bg)

    # Tk option db defaults for legacy tk.* widgets and menus.
    root.option_add("*Background", window_bg)
    root.option_add("*Foreground", text)
    root.option_add("*Canvas.Background", surface_bg)
    root.option_add("*Canvas.HighlightBackground", border)
    root.option_add("*Text.Background", input_bg)
    root.option_add("*Text.Foreground", text)
    root.option_add("*Text.InsertBackground", text)
    root.option_add("*Listbox.Background", input_bg)
    root.option_add("*Listbox.Foreground", text)
    root.option_add("*Menu.Background", panel_bg)
    root.option_add("*Menu.Foreground", text)
    root.option_add("*Menu.ActiveBackground", accent)
    root.option_add("*Menu.ActiveForeground", text)
    root.option_add("*Button.Background", surface_bg)
    root.option_add("*Button.Foreground", text)
    root.option_add("*Label.Background", window_bg)
    root.option_add("*Label.Foreground", text)

    # Global ttk defaults.
    _safe_style_configure(
        style,
        ".",
        background=panel_bg,
        foreground=text,
        bordercolor=border,
        troughcolor=surface_bg,
        lightcolor=border,
        darkcolor=border,
        focuscolor=border,
    )
    _safe_style_map(
        style,
        ".",
        foreground=[("disabled", muted_text)],
        background=[("disabled", panel_bg)],
    )

    _safe_style_configure(style, "TFrame", background=panel_bg)
    _safe_style_configure(style, "Popup.TFrame", background=panel_bg)
    _safe_style_configure(style, "TLabel", background=panel_bg, foreground=text)
    _safe_style_configure(
        style,
        "TLabelframe",
        background=panel_bg,
        foreground=text,
        bordercolor=border,
    )
    _safe_style_configure(
        style,
        "TLabelframe.Label",
        background=panel_bg,
        foreground=text,
    )
    _safe_style_configure(
        style,
        "Bold.TLabelframe.Label",
        background=panel_bg,
        foreground=text,
    )

    _safe_style_configure(
        style,
        "TButton",
        background=surface_bg,
        foreground=text,
        bordercolor=border,
        padding=(8, 4),
    )
    _safe_style_map(
        style,
        "TButton",
        background=[
            ("disabled", panel_bg),
            ("pressed", accent_pressed),
            ("active", accent_hover),
        ],
        foreground=[("disabled", muted_text)],
    )

    _safe_style_configure(style, "Accent.TButton", background=accent, foreground=text)
    _safe_style_map(
        style,
        "Accent.TButton",
        background=[
            ("disabled", panel_bg),
            ("pressed", accent_pressed),
            ("active", accent_hover),
            ("!disabled", accent),
        ],
        foreground=[("disabled", muted_text), ("!disabled", text)],
    )

    _safe_style_configure(style, "Danger.TButton", background=danger, foreground=text)
    _safe_style_configure(style, "Success.TButton", background=success, foreground=text)
    _safe_style_configure(
        style,
        "StageStop.Danger.TButton",
        background=danger,
        foreground=text,
        font=("TkDefaultFont", 10, "bold"),
        padding=(8, 16),
    )
    _safe_style_map(
        style,
        "StageStop.Danger.TButton",
        background=[
            ("disabled", panel_bg),
            ("pressed", accent_pressed),
            ("active", accent_hover),
            ("!disabled", danger),
        ],
        foreground=[("disabled", muted_text), ("!disabled", text)],
    )
    _safe_style_configure(
        style,
        "StageHome.Success.TButton",
        background=success,
        foreground=text,
        padding=(8, 6),
    )
    _safe_style_map(
        style,
        "StageHome.Success.TButton",
        background=[
            ("disabled", panel_bg),
            ("pressed", accent_pressed),
            ("active", accent_hover),
            ("!disabled", success),
        ],
        foreground=[("disabled", muted_text), ("!disabled", text)],
    )

    # Use image-backed rounded elements where available.
    _apply_rounded_button_styles(
        root,
        style,
        panel_bg=panel_bg,
        surface_bg=surface_bg,
        border=border,
        text=text,
        muted_text=muted_text,
        accent=accent,
        accent_hover=accent_hover,
        accent_pressed=accent_pressed,
        danger=danger,
        success=success,
    )

    _safe_style_configure(
        style,
        "TEntry",
        fieldbackground=input_bg,
        foreground=text,
        bordercolor=border,
    )
    _safe_style_configure(
        style,
        "TSpinbox",
        fieldbackground=input_bg,
        foreground=text,
        background=surface_bg,
        bordercolor=border,
        arrowcolor=text,
    )
    _safe_style_map(
        style,
        "TSpinbox",
        fieldbackground=[("readonly", input_bg), ("disabled", panel_bg)],
        foreground=[("disabled", muted_text), ("!disabled", text)],
    )
    _safe_style_configure(
        style,
        "TCombobox",
        fieldbackground=input_bg,
        foreground=text,
        background=surface_bg,
        arrowcolor=text,
    )
    _safe_style_map(
        style,
        "TCombobox",
        fieldbackground=[("readonly", input_bg), ("disabled", panel_bg)],
        selectbackground=[("readonly", accent)],
        selectforeground=[("readonly", text)],
    )

    _safe_style_configure(style, "TCheckbutton", background=panel_bg, foreground=text)
    _safe_style_configure(style, "TRadiobutton", background=panel_bg, foreground=text)

    _safe_style_configure(
        style,
        "TNotebook",
        background=window_bg,
        bordercolor=border,
    )
    _safe_style_configure(
        style,
        "TNotebook.Tab",
        background=surface_bg,
        foreground=text,
        padding=(10, 4),
    )
    _safe_style_map(
        style,
        "TNotebook.Tab",
        background=[("selected", panel_bg), ("active", accent_hover)],
        foreground=[("disabled", muted_text), ("selected", text)],
    )
    _apply_rounded_notebook_tabs(
        root,
        style,
        notebook_bg=window_bg,
        panel_bg=panel_bg,
        surface_bg=surface_bg,
        border=border,
        accent_hover=accent_hover,
        muted_text=muted_text,
        text=text,
    )

    _safe_style_configure(
        style,
        "Horizontal.TProgressbar",
        troughcolor=surface_bg,
        background=accent,
    )
    _safe_style_configure(
        style,
        "Vertical.TProgressbar",
        troughcolor=surface_bg,
        background=accent,
    )

    return preset_name, palette
