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

from unittest.mock import MagicMock, call

from navigate.view import theme


def test_build_palette_applies_typography_overrides():
    gui_settings = {
        "theme": {
            "preset": "classic_night",
            "typography": {
                "title": ["Arial", 16, "bold"],
                "body": ["TkDefaultFont", 11],
                "caption": ["TkDefaultFont", "8", "italic"],
            },
            "spacing": {
                "space_4": "9",
                "padding_button": [12, 6],
                "padding_notebook_tab": 7,
            },
        }
    }

    preset, palette, base_theme, typography, spacing = theme._build_palette(
        gui_settings
    )

    assert preset == "classic_night"
    assert base_theme == "clam"
    assert palette["window_bg"] == "#11161d"
    assert typography["title"] == ("Arial", 16, "bold")
    assert typography["body"] == ("TkDefaultFont", 11)
    assert typography["caption"] == ("TkDefaultFont", 8, "italic")
    assert spacing["space_4"] == 9
    assert spacing["padding_button"] == (12, 6)
    assert spacing["padding_notebook_tab"] == (7, 7)


def test_to_font_tuple_falls_back_for_invalid_values():
    fallback = ("TkDefaultFont", 10)

    assert theme._to_font_tuple(["Avenir", "bad-size"], fallback) == ("Avenir", 10)
    assert theme._to_font_tuple([], fallback) == fallback
    assert theme._to_font_tuple("invalid", fallback) == fallback


def test_get_theme_font_uses_active_tokens_with_fallback(monkeypatch):
    monkeypatch.setattr(
        theme,
        "_ACTIVE_TYPOGRAPHY",
        {"body": ("TkDefaultFont", 10), "title": ("TkDefaultFont", 14, "bold")},
    )

    assert theme.get_theme_font("title") == ("TkDefaultFont", 14, "bold")
    assert theme.get_theme_font("missing", ("Fira Sans", 12)) == ("Fira Sans", 12)


def test_get_theme_spacing_and_padding_use_active_tokens(monkeypatch):
    monkeypatch.setattr(
        theme,
        "_ACTIVE_SPACING",
        {
            "space_4": 8,
            "padding_button": (8, 4),
            "uniform_padding": 6,
        },
    )

    assert theme.get_theme_spacing("space_4") == 8
    assert theme.get_theme_spacing("missing", 5) == 5
    assert theme.get_theme_padding("padding_button") == (8, 4)
    assert theme.get_theme_padding("uniform_padding") == (6, 6)
    assert theme.get_theme_padding("missing", (1, 2, 3, 4)) == (1, 2, 3, 4)


def test_get_theme_space_and_padding_px_use_generated_tokens(monkeypatch):
    monkeypatch.setattr(
        theme,
        "_ACTIVE_SPACING",
        {
            "space_px_5": 7,
            "padding_px_3_4": (9, 10),
        },
    )

    assert theme.get_theme_space_px(5) == 7
    assert theme.get_theme_space_px(11) == 11
    assert theme.get_theme_padding_px((3, 4)) == (9, 10)
    assert theme.get_theme_padding_px((1, 2, 3, 4)) == (1, 2, 3, 4)


def test_get_theme_matplotlib_font_resolves_tk_named_family(monkeypatch):
    monkeypatch.setattr(theme, "_ACTIVE_TYPOGRAPHY", {"body": ("TkDefaultFont", 10)})

    class _ResolvedFont:
        def actual(self, key):
            assert key == "family"
            return "Segoe UI"

    monkeypatch.setattr(theme.tkfont, "nametofont", lambda name: _ResolvedFont())

    fontdict = theme.get_theme_matplotlib_font("body")

    assert fontdict["family"] == "Segoe UI"
    assert fontdict["size"] == 10
    assert fontdict["style"] == "normal"
    assert fontdict["weight"] == "normal"


def test_get_theme_matplotlib_font_uses_sans_serif_when_tk_named_missing(monkeypatch):
    monkeypatch.setattr(theme, "_ACTIVE_TYPOGRAPHY", {"body": ("TkDefaultFont", 10)})
    monkeypatch.setattr(
        theme.tkfont,
        "nametofont",
        lambda name: (_ for _ in ()).throw(theme.tk.TclError("missing")),
    )

    fontdict = theme.get_theme_matplotlib_font("body")

    assert fontdict["family"] == "sans-serif"
    assert fontdict["size"] == 10


def test_get_theme_matplotlib_font_uses_sans_serif_for_private_tk_family(monkeypatch):
    monkeypatch.setattr(theme, "_ACTIVE_TYPOGRAPHY", {"body": ("TkDefaultFont", 10)})

    class _ResolvedFont:
        def actual(self, key):
            assert key == "family"
            return ".AppleSystemUIFont"

    monkeypatch.setattr(theme.tkfont, "nametofont", lambda name: _ResolvedFont())

    fontdict = theme.get_theme_matplotlib_font("body")

    assert fontdict["family"] == "sans-serif"
    assert fontdict["size"] == 10


def test_apply_theme_sets_legible_menu_state_colors(monkeypatch):
    root = MagicMock()
    style = MagicMock()
    style.theme_names.return_value = ("clam",)
    monkeypatch.setattr(theme.ttk, "Style", lambda _root: style)
    monkeypatch.setattr(
        theme, "_apply_rounded_notebook_tabs", lambda *args, **kwargs: None
    )

    _, palette = theme.apply_theme(root)

    assert call("*Menu.SelectColor", palette["text"]) in root.option_add.call_args_list
    assert (
        call("*Menu.DisabledForeground", palette["muted_text"])
        in root.option_add.call_args_list
    )
