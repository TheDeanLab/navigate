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

# Standard Library Imports

# Third Party Imports

# Local Imports

# src/navigate/view/styles.py
from tkinter import ttk

# Color Theme Constants
LIGHT_0 = "#fafafa"  # (250,250,250)
LIGHT_1 = "#e4e5f1"  # (228,229,241)
LIGHT_2 = "#d2d3db"  # (210,211,219)
LIGHT_3 = "#9394a5"  # (147,148,165)
LIGHT_4 = "#484b6a"  # (72,75,106)


def apply_styles(root=None):
    """Apply application-wide styling to all ttk widgets"""
    if root:
        root.configure(bg=LIGHT_0)

    style = ttk.Style()
    style.theme_use("default")
    style.configure(".", background=LIGHT_1)
    style.configure("TFrame", background=LIGHT_1)

    # Style for Buttons
    style.configure(
        "TButton",
        background=LIGHT_2,
        foreground="black",
    )

    # Pressed
    style.map(
        "TButton",
        background=[
            ("active", LIGHT_3),
            ("pressed", LIGHT_3),
        ],
        relief=[("pressed", "sunken")],
    )

    # Clicked
    style.map("TButton", background=[("active", LIGHT_4)])

    # Style for Labels
    style.configure("TLabel", background=LIGHT_1, foreground="black", padding=[5, 2])

    # Style the notebooks and their tabs
    style.configure("TNotebook", background=LIGHT_0)
    style.configure(
        "TNotebook.Tab", background=LIGHT_2, foreground="black", padding=[10, 4]
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", LIGHT_4), ("active", LIGHT_4)],
        foreground=[("selected", "black")],
        expand=[("selected", [1, 1, 1, 0])],
    )

    # Style for Combobox
    style.configure(
        "TCombobox",
        background=LIGHT_0,
        foreground="black",
        fieldbackground=LIGHT_0,
        bordercolor=LIGHT_3,
        arrowcolor=LIGHT_4,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", LIGHT_0), ("disabled", LIGHT_1)],
        selectbackground=[("readonly", LIGHT_4)],
        selectforeground=[("readonly", "white")],
        background=[("active", LIGHT_3), ("pressed", LIGHT_3)],
        arrowcolor=[("disabled", LIGHT_3)],
    )

    # Style for Spinbox
    style.configure(
        "TSpinbox",
        background=LIGHT_0,
        foreground="black",
        fieldbackground=LIGHT_0,
        bordercolor=LIGHT_3,
        arrowcolor=LIGHT_4,
    )
    style.map(
        "TSpinbox",
        fieldbackground=[("readonly", LIGHT_0), ("disabled", LIGHT_1)],
        selectbackground=[("readonly", LIGHT_4)],
        selectforeground=[("readonly", "white")],
        background=[("active", LIGHT_3), ("pressed", LIGHT_3)],
        arrowcolor=[("disabled", LIGHT_3)],
    )

    # Style for Entry widgets
    style.configure(
        "TEntry", fieldbackground=LIGHT_0, foreground="black", bordercolor=LIGHT_3
    )
    style.map(
        "TEntry",
        fieldbackground=[("disabled", LIGHT_1)],
        bordercolor=[("focus", LIGHT_4)],
    )

    # Style for Checkbutton
    style.configure("TCheckbutton", background=LIGHT_1, foreground="black")
    style.map(
        "TCheckbutton",
        background=[("active", LIGHT_1)],
        indicatorcolor=[("selected", LIGHT_4), ("active", LIGHT_3)],
    )

    # Style for Scrollbar
    style.configure(
        "TScrollbar",
        background=LIGHT_1,
        arrowcolor=LIGHT_4,
        bordercolor=LIGHT_3,
        troughcolor=LIGHT_0,
    )
    style.map(
        "TScrollbar", background=[("active", LIGHT_2)], arrowcolor=[("active", LIGHT_4)]
    )

    # Style for Separator
    style.configure("TSeparator", background=LIGHT_3)

    # Style for Canvas - used in scrollable areas
    if root:
        root.option_add("*Canvas.background", LIGHT_0)

    # Style for CollapsibleFrame elements
    style.configure("Collapsible.TFrame", background=LIGHT_1)
    style.configure(
        "Collapsible.TLabel", background=LIGHT_2, foreground="black", padding=[5, 5]
    )

    return style
