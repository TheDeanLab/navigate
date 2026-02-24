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

"""Global GUI theming helpers."""

# Standard Library Imports
from __future__ import annotations
from typing import Any, Union
import tkinter as tk
from tkinter import ttk, font as tkfont

# Third Party Imports
try:
    from PIL import Image, ImageDraw, ImageTk
except ImportError:  # pragma: no cover - optional fallback
    Image = None
    ImageDraw = None
    ImageTk = None

# Local Imports


_DEFAULT_THEME_PRESET = "classic_night"
FontSpec = tuple[Any, ...]
SpacingSpec = Union[int, tuple[int, ...]]

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

_TYPOGRAPHY_PRESETS: dict[str, dict[str, FontSpec]] = {
    "classic_night": {
        "caption": ("TkDefaultFont", 9),
        "body": ("TkDefaultFont", 10),
        "body_bold": ("TkDefaultFont", 10, "bold"),
        "section": ("TkDefaultFont", 12, "bold"),
        "title": ("TkDefaultFont", 14, "bold"),
        "title_italic": ("TkDefaultFont", 14, "italic"),
        "button": ("TkDefaultFont", 10),
        "button_emphasis": ("TkDefaultFont", 12, "bold"),
        "tooltip": ("TkDefaultFont", 9),
        "tooltip_emphasis": ("TkDefaultFont", 9, "bold"),
    }
}

_SPACING_PRESETS: dict[str, dict[str, SpacingSpec]] = {
    "classic_night": {
        "space_0": 0,
        "space_1": 2,
        "space_2": 4,
        "space_3": 6,
        "space_4": 8,
        "space_5": 10,
        "space_6": 12,
        "space_7": 16,
        "space_8": 20,
        "space_9": 24,
        "padding_button": (8, 4),
        "padding_stage_stop_button": (8, 16),
        "padding_stage_home_button": (8, 6),
        "padding_notebook_tab": (10, 4),
    }
}

_ACTIVE_PALETTE: dict[str, str] = dict(_THEME_PRESETS[_DEFAULT_THEME_PRESET])
_ACTIVE_TYPOGRAPHY: dict[str, FontSpec] = dict(
    _TYPOGRAPHY_PRESETS[_DEFAULT_THEME_PRESET]
)
_ACTIVE_SPACING: dict[str, SpacingSpec] = dict(_SPACING_PRESETS[_DEFAULT_THEME_PRESET])
_THEME_IMAGES: dict[str, tk.PhotoImage] = {}


def _to_dict(data: Any) -> dict[str, Any]:
    """Safely convert mapping-like input to a plain dictionary.

    Parameters
    ----------
    data : Any
        Mapping or mapping-proxy input that can be coerced to ``dict``; may be
        ``None``.

    Returns
    -------
    dict[str, Any]
        Normalized dictionary, or an empty dictionary when conversion is not
        possible.
    """
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    try:
        return dict(data)
    except TypeError:
        return {}


def _get_nested(mapping: Any, keys: tuple[str, ...], default: Any) -> Any:
    """Fetch nested values from mapping-like objects.

    Parameters
    ----------
    mapping : Any
        Source mapping or mapping proxy that supports ``get`` or key access.
    keys : tuple[str, ...]
        Ordered path of keys to traverse within the mapping.
    default : Any
        Fallback value returned when traversal fails or yields ``None``.

    Returns
    -------
    Any
        Retrieved value if present; otherwise ``default``.
    """
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


def _to_font_tuple(data: Any, fallback: FontSpec) -> FontSpec:
    """Convert a font specification to a Tk-compatible tuple.

    Parameters
    ----------
    data : Any
        Font representation, typically a list or tuple of ``(family, size, *modifiers)``.
    fallback : FontSpec
        Font tuple used when conversion fails or values are invalid.

    Returns
    -------
    FontSpec
        Valid Tk font tuple with a minimum size of 1.
    """
    if isinstance(data, (list, tuple)) and len(data) >= 2:
        family = str(data[0]) if data[0] else str(fallback[0])
        try:
            size = max(1, int(data[1]))
        except (TypeError, ValueError):
            try:
                size = max(1, int(fallback[1]))
            except (TypeError, ValueError):
                size = 10
        modifiers = tuple(str(item) for item in data[2:] if item not in (None, ""))
        return (family, size, *modifiers)
    return fallback


def _to_nonnegative_int(data: Any) -> int | None:
    """Convert numeric-like input to a nonnegative integer.

    Parameters
    ----------
    data : Any
        Value to convert.

    Returns
    -------
    int or None
        Converted integer when successful; otherwise ``None``.
    """
    if isinstance(data, bool):
        return None
    try:
        return max(0, int(data))
    except (TypeError, ValueError):
        return None


def _to_spacing_tuple(data: Any) -> tuple[int, ...] | None:
    """Convert sequence-like spacing input to a Tk padding tuple.

    Parameters
    ----------
    data : Any
        Sequence-like value expected to contain 1, 2, or 4 numeric entries.

    Returns
    -------
    tuple[int, ...] or None
        Padding tuple or ``None`` when conversion fails.
    """
    if not isinstance(data, (list, tuple)):
        return None
    if len(data) not in (1, 2, 4):
        return None

    values: list[int] = []
    for item in data:
        value = _to_nonnegative_int(item)
        if value is None:
            return None
        values.append(value)

    if len(values) == 1:
        return (values[0], values[0])
    return tuple(values)


def _coerce_spacing_value(data: Any, fallback: SpacingSpec) -> SpacingSpec:
    """Coerce spacing input to match an existing token shape.

    Parameters
    ----------
    data : Any
        Candidate spacing override.
    fallback : SpacingSpec
        Existing token value used to determine the target type.

    Returns
    -------
    SpacingSpec
        Coerced spacing token, or the fallback when conversion fails.
    """
    scalar = _to_nonnegative_int(data)
    if isinstance(fallback, int):
        return fallback if scalar is None else scalar

    if scalar is not None:
        return (scalar,) * len(fallback)

    value = _to_spacing_tuple(data)
    if value is None:
        return fallback
    if len(value) == len(fallback):
        return value
    if len(value) == 2 and len(fallback) == 4:
        return (value[0], value[1], value[0], value[1])
    return fallback


def _parse_spacing_value(data: Any) -> SpacingSpec | None:
    """Parse scalar or tuple spacing values without a typed fallback.

    Parameters
    ----------
    data : Any
        Candidate spacing token value.

    Returns
    -------
    SpacingSpec or None
        Parsed spacing value when valid; otherwise ``None``.
    """
    scalar = _to_nonnegative_int(data)
    if scalar is not None:
        return scalar
    return _to_spacing_tuple(data)


def _safe_style_configure(style: ttk.Style, name: str, **kwargs: Any) -> None:
    """Configure ttk styles while tolerating unsupported options.

    Parameters
    ----------
    style : ttk.Style
        Target ttk style manager.
    name : str
        Style name to configure.
    **kwargs : Any
        Style options forwarded to ``style.configure``; unsupported options are
        ignored.

    Returns
    -------
    None
        This function mutates the ttk style in place.
    """
    for key, value in kwargs.items():
        try:
            style.configure(name, **{key: value})
        except tk.TclError:
            continue


def _safe_style_map(style: ttk.Style, name: str, **kwargs: Any) -> None:
    """Map ttk style states while tolerating unsupported options.

    Parameters
    ----------
    style : ttk.Style
        Target ttk style manager.
    name : str
        Style name to map.
    **kwargs : Any
        State-specific options forwarded to ``style.map``; unsupported options are
        ignored.

    Returns
    -------
    None
        This function mutates the ttk style in place.
    """
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
    """Create and cache a rounded rectangle image for ttk element skins.

    Parameters
    ----------
    root : tk.Tk
        Root window used as the master for generated images.
    image_name : str
        Cache key for the generated ``PhotoImage``.
    fill_color : str
        Fill color for the rounded rectangle.
    border_color : str
        Outline color for the rounded rectangle.
    width : int
        Width of the generated image in pixels.
    height : int
        Height of the generated image in pixels.
    radius : int
        Corner radius of the rounded rectangle.
    border_width : int, optional
        Outline thickness in pixels, by default 1.
    corner_bg : str or None, optional
        Background color to blend corners with; transparent when ``None``.

    Returns
    -------
    tk.PhotoImage or None
        Cached ``PhotoImage`` when PIL is available; otherwise ``None``.
    """
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
    """Install rounded image-backed ttk button styles.

    Parameters
    ----------
    root : tk.Tk
        Root window used for image creation.
    style : ttk.Style
        ttk style manager receiving the new styles.
    panel_bg : str
        Panel background color used to blend disabled states.
    surface_bg : str
        Surface background color for neutral states.
    border : str
        Border color for button outlines.
    text : str
        Foreground color for enabled text.
    muted_text : str
        Foreground color for disabled text.
    accent : str
        Base accent color for emphasized buttons.
    accent_hover : str
        Hover-state accent color.
    accent_pressed : str
        Pressed-state accent color.
    danger : str
        Danger-state accent color.
    success : str
        Success-state accent color.
    radius : int, optional
        Corner radius for rounded buttons, by default 5.

    Returns
    -------
    None
        Styles are added to ``style`` in place.
    """
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
    """Install rounded image-backed ttk notebook tabs.

    Parameters
    ----------
    root : tk.Tk
        Root window used for image creation.
    style : ttk.Style
        ttk style manager receiving the new tab style.
    notebook_bg : str
        Notebook background color for corner blending.
    panel_bg : str
        Panel background color for selected and disabled tabs.
    surface_bg : str
        Surface background color for unselected tabs.
    border : str
        Border color for tab outlines.
    accent_hover : str
        Accent color for active (hover) state.
    muted_text : str
        Foreground color for disabled tabs.
    text : str
        Foreground color for enabled tabs.
    radius : int, optional
        Corner radius for rounded tabs, by default 3.

    Returns
    -------
    None
        Styles are added to ``style`` in place.
    """
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


def _build_palette(
    gui_settings: Any,
) -> tuple[
    str,
    dict[str, str],
    str,
    dict[str, FontSpec],
    dict[str, SpacingSpec],
]:
    """Resolve theme preset and overrides from GUI configuration.

    Parameters
    ----------
    gui_settings : Any
        Nested configuration object containing ``theme`` overrides.

    Returns
    -------
    tuple[str, dict[str, str], str, dict[str, FontSpec], dict[str, SpacingSpec]]
        ``(preset_name, palette, base_theme, typography, spacing)`` reflecting
        merged theme settings.
    """
    theme_settings = _to_dict(_get_nested(gui_settings, ("theme",), {}))
    preset_name = str(theme_settings.get("preset", _DEFAULT_THEME_PRESET))
    base_theme = str(theme_settings.get("ttk_base_theme", "clam"))

    palette = dict(
        _THEME_PRESETS.get(preset_name, _THEME_PRESETS[_DEFAULT_THEME_PRESET])
    )
    palette.update(_to_dict(theme_settings.get("palette")))

    typography = dict(
        _TYPOGRAPHY_PRESETS.get(preset_name, _TYPOGRAPHY_PRESETS[_DEFAULT_THEME_PRESET])
    )
    body_fallback = _TYPOGRAPHY_PRESETS[_DEFAULT_THEME_PRESET]["body"]
    for key, value in _to_dict(theme_settings.get("typography")).items():
        token = str(key)
        typography[token] = _to_font_tuple(value, typography.get(token, body_fallback))

    spacing = dict(
        _SPACING_PRESETS.get(preset_name, _SPACING_PRESETS[_DEFAULT_THEME_PRESET])
    )
    for key, value in _to_dict(theme_settings.get("spacing")).items():
        token = str(key)
        if token in spacing:
            spacing[token] = _coerce_spacing_value(value, spacing[token])
            continue
        parsed_spacing = _parse_spacing_value(value)
        if parsed_spacing is not None:
            spacing[token] = parsed_spacing

    return preset_name, palette, base_theme, typography, spacing


def get_theme_color(name: str, fallback: str | None = None) -> str:
    """Return a named theme color from the active palette.

    Parameters
    ----------
    name : str
        Color token to retrieve.
    fallback : str or None, optional
        Color returned when the token is missing, by default ``None``.

    Returns
    -------
    str
        Resolved color value.
    """
    if name in _ACTIVE_PALETTE:
        return _ACTIVE_PALETTE[name]
    if fallback is not None:
        return fallback
    return _THEME_PRESETS[_DEFAULT_THEME_PRESET].get(name, "#000000")


def get_theme_font(name: str, fallback: FontSpec | None = None) -> FontSpec:
    """Return a named theme font tuple with fallback support.

    Parameters
    ----------
    name : str
        Typography token to retrieve.
    fallback : FontSpec or None, optional
        Font tuple returned when the token is missing, by default ``None``.

    Returns
    -------
    FontSpec
        Resolved font tuple.
    """
    if name in _ACTIVE_TYPOGRAPHY:
        return _ACTIVE_TYPOGRAPHY[name]
    if fallback is not None:
        return fallback
    return _TYPOGRAPHY_PRESETS[_DEFAULT_THEME_PRESET]["body"]


def get_theme_spacing(name: str, fallback: int | None = None) -> int:
    """Return a named spacing token from the active layout scale.

    Parameters
    ----------
    name : str
        Spacing token to retrieve.
    fallback : int or None, optional
        Value returned when the token is missing or non-scalar.

    Returns
    -------
    int
        Resolved spacing value.
    """
    value = _ACTIVE_SPACING.get(name)
    if isinstance(value, int):
        return value
    if fallback is not None:
        return fallback
    default_value = _SPACING_PRESETS[_DEFAULT_THEME_PRESET].get(name)
    return default_value if isinstance(default_value, int) else 0


def get_theme_padding(
    name: str,
    fallback: tuple[int, ...] | None = None,
) -> tuple[int, ...]:
    """Return a named padding token from the active layout system.

    Parameters
    ----------
    name : str
        Padding token to retrieve.
    fallback : tuple[int, ...] or None, optional
        Tuple returned when the token is missing.

    Returns
    -------
    tuple[int, ...]
        Resolved padding tuple.
    """
    value = _ACTIVE_SPACING.get(name)
    if isinstance(value, tuple):
        return value
    if isinstance(value, int):
        return (value, value)
    if fallback is not None:
        return fallback
    default_value = _SPACING_PRESETS[_DEFAULT_THEME_PRESET].get(name)
    if isinstance(default_value, tuple):
        return default_value
    if isinstance(default_value, int):
        return (default_value, default_value)
    return (0, 0)


def get_theme_space_px(value: int, fallback: int | None = None) -> int:
    """Resolve pixel spacing through tokenized lookup.

    Parameters
    ----------
    value : int
        Desired pixel spacing.
    fallback : int or None, optional
        Fallback value when the generated token is missing. When omitted, the
        sanitized ``value`` is used.

    Returns
    -------
    int
        Resolved spacing value.
    """
    normalized = _to_nonnegative_int(value)
    if normalized is None:
        normalized = 0
    fallback_value = _to_nonnegative_int(fallback)
    resolved_fallback = normalized if fallback_value is None else fallback_value
    return get_theme_spacing(f"space_px_{normalized}", resolved_fallback)


def get_theme_padding_px(values: tuple[int, ...]) -> tuple[int, ...]:
    """Resolve pixel padding through tokenized lookup.

    Parameters
    ----------
    values : tuple[int, ...]
        Desired Tk padding tuple of length 1, 2, or 4.

    Returns
    -------
    tuple[int, ...]
        Resolved padding tuple.
    """
    normalized = _to_spacing_tuple(values)
    if normalized is None:
        normalized = (0, 0)
    token = "padding_px_" + "_".join(str(item) for item in normalized)
    return get_theme_padding(token, normalized)


def _resolve_matplotlib_family(family: str) -> str:
    """Resolve Tk named font families to concrete Matplotlib-safe family names.

    Parameters
    ----------
    family : str
        Font family string from theme typography.

    Returns
    -------
    str
        Concrete family name suitable for Matplotlib's font manager.
    """
    if not family:
        return "sans-serif"

    resolved_family = family
    if family.startswith("Tk") and family.endswith("Font"):
        try:
            resolved_family = str(tkfont.nametofont(family).actual("family"))
        except (tk.TclError, RuntimeError, ValueError):
            return "sans-serif"

    # Tk on macOS can resolve to private Cocoa aliases (e.g. ".AppleSystemUIFont")
    # that Matplotlib cannot locate via font_manager.
    if resolved_family.startswith("."):
        return "sans-serif"

    return resolved_family


def get_theme_matplotlib_font(
    name: str, fallback: FontSpec | None = None
) -> dict[str, Any]:
    """Return a Matplotlib-compatible font dictionary from theme typography.

    Parameters
    ----------
    name : str
        Typography token to retrieve.
    fallback : FontSpec or None, optional
        Font tuple used when token is missing.

    Returns
    -------
    dict[str, Any]
        Dictionary with Matplotlib font keys.
    """
    spec = get_theme_font(name, fallback)
    family = _resolve_matplotlib_family(str(spec[0]) if len(spec) >= 1 else "")
    try:
        size = int(spec[1]) if len(spec) >= 2 else 10
    except (TypeError, ValueError):
        size = 10
    modifiers = {str(item).lower() for item in spec[2:] if item not in (None, "")}
    return {
        "family": family,
        "size": max(1, size),
        "style": "italic" if "italic" in modifiers else "normal",
        "weight": "bold" if "bold" in modifiers else "normal",
    }


def apply_theme(root: tk.Tk, gui_settings: Any = None) -> tuple[str, dict[str, str]]:
    """Apply the global ttk/tk theme to the root and all inheriting popups.

    Parameters
    ----------
    root : tk.Tk
        Root Tk instance to style.
    gui_settings : Any, optional
        GUI configuration containing theme overrides, by default ``None``.

    Returns
    -------
    tuple[str, dict[str, str]]
        ``(preset_name, palette)`` describing the applied theme.
    """
    global _ACTIVE_PALETTE, _ACTIVE_TYPOGRAPHY, _ACTIVE_SPACING
    preset_name, palette, preferred_theme, typography, spacing = _build_palette(
        gui_settings
    )
    _ACTIVE_PALETTE = dict(palette)
    _ACTIVE_TYPOGRAPHY = dict(typography)
    _ACTIVE_SPACING = dict(spacing)

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
    font_caption = typography["caption"]
    font_body = typography["body"]
    font_body_bold = typography["body_bold"]
    font_section = typography["section"]
    font_title = typography["title"]
    font_button = typography["button"]
    font_button_emphasis = typography["button_emphasis"]
    button_padding = get_theme_padding("padding_button")
    stage_stop_button_padding = get_theme_padding("padding_stage_stop_button")
    stage_home_button_padding = get_theme_padding("padding_stage_home_button")
    notebook_tab_padding = get_theme_padding("padding_notebook_tab")

    root.configure(bg=window_bg)

    # Tk option db defaults for legacy tk.* widgets and menus.
    root.option_add("*Font", font_body)
    root.option_add("*Background", window_bg)
    root.option_add("*Foreground", text)
    root.option_add("*Canvas.Background", surface_bg)
    root.option_add("*Canvas.HighlightBackground", border)
    root.option_add("*Text.Font", font_body)
    root.option_add("*Text.Background", input_bg)
    root.option_add("*Text.Foreground", text)
    root.option_add("*Text.InsertBackground", text)
    root.option_add("*Listbox.Font", font_body)
    root.option_add("*Listbox.Background", input_bg)
    root.option_add("*Listbox.Foreground", text)
    root.option_add("*Menu.Font", font_body)
    root.option_add("*Menu.Background", panel_bg)
    root.option_add("*Menu.Foreground", text)
    root.option_add("*Menu.ActiveBackground", accent)
    root.option_add("*Menu.ActiveForeground", text)
    root.option_add("*Button.Font", font_button)
    root.option_add("*Button.Background", surface_bg)
    root.option_add("*Button.Foreground", text)
    root.option_add("*Label.Font", font_body)
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
        font=font_body,
    )
    _safe_style_map(
        style,
        ".",
        foreground=[("disabled", muted_text)],
        background=[("disabled", panel_bg)],
    )

    _safe_style_configure(style, "TFrame", background=panel_bg)
    _safe_style_configure(style, "Popup.TFrame", background=panel_bg)
    _safe_style_configure(
        style,
        "TLabel",
        background=panel_bg,
        foreground=text,
        font=font_body,
    )
    _safe_style_configure(style, "Body.TLabel", font=font_body)
    _safe_style_configure(style, "BodyBold.TLabel", font=font_body_bold)
    _safe_style_configure(style, "Caption.TLabel", font=font_caption)
    _safe_style_configure(style, "Section.TLabel", font=font_section)
    _safe_style_configure(style, "Title.TLabel", font=font_title)
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
        font=font_section,
    )
    _safe_style_configure(
        style,
        "Bold.TLabelframe.Label",
        background=panel_bg,
        foreground=text,
        font=font_title,
    )

    _safe_style_configure(
        style,
        "TButton",
        background=surface_bg,
        foreground=text,
        bordercolor=border,
        padding=button_padding,
        font=font_button,
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

    _safe_style_configure(
        style,
        "Accent.TButton",
        background=accent,
        foreground=text,
        font=font_button_emphasis,
    )
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

    _safe_style_configure(
        style,
        "Danger.TButton",
        background=danger,
        foreground=text,
        font=font_button,
    )
    _safe_style_configure(
        style,
        "Success.TButton",
        background=success,
        foreground=text,
        font=font_button,
    )
    _safe_style_configure(
        style,
        "StageStop.Danger.TButton",
        background=danger,
        foreground=text,
        font=font_body_bold,
        padding=stage_stop_button_padding,
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
        font=font_button,
        padding=stage_home_button_padding,
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
        insertcolor=text,
        bordercolor=border,
        font=font_body,
    )
    _safe_style_configure(
        style,
        "TSpinbox",
        fieldbackground=input_bg,
        foreground=text,
        insertcolor=text,
        background=surface_bg,
        bordercolor=border,
        arrowcolor=text,
        font=font_body,
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
        insertcolor=text,
        background=surface_bg,
        arrowcolor=text,
        font=font_body,
    )
    _safe_style_map(
        style,
        "TCombobox",
        fieldbackground=[("readonly", input_bg), ("disabled", panel_bg)],
        selectbackground=[("readonly", accent)],
        selectforeground=[("readonly", text)],
    )

    _safe_style_configure(
        style,
        "TCheckbutton",
        background=panel_bg,
        foreground=text,
        font=font_body,
    )
    _safe_style_configure(
        style,
        "TRadiobutton",
        background=panel_bg,
        foreground=text,
        font=font_body,
    )
    _safe_style_configure(style, "BodyBold.TCheckbutton", font=font_body_bold)

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
        padding=notebook_tab_padding,
        font=font_body_bold,
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
