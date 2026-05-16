# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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
from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, Union
import tkinter as tk
from tkinter import ttk

# Local Imports
from navigate.view.theme import get_theme_padding, get_theme_spacing

# Third Party Imports


GridAxisOptions = Dict[str, int]
GridAxisSpec = Optional[Union[int, GridAxisOptions]]
GridConfig = Optional[Union[int, Tuple[GridAxisSpec, ...], Dict[int, GridAxisSpec]]]
SpacingArg = Optional[Union[int, str, Tuple[Union[int, str], ...]]]


def uniform_grid(cls: Any) -> None:
    """This function is used to equally distribute the columns and rows of a
    tkinter frame.

    Parameters
    ----------
    cls : tk.Frame or ttk.Frame
        The class that is to be distributed.
    """
    cols, rows = cls.grid_size()
    for col in range(cols):
        cls.grid_columnconfigure(col, weight=1)
    for row in range(rows):
        cls.grid_rowconfigure(row, weight=1)


def _resolve_spacing(value: SpacingArg) -> int | tuple[int, ...] | None:
    """Resolve a spacing token or literal to a Tk-compatible padding value."""
    if value is None:
        return None
    if isinstance(value, str):
        if value.startswith("padding_"):
            return get_theme_padding(value)
        return get_theme_spacing(value)
    if isinstance(value, tuple):
        resolved: list[int] = []
        for item in value:
            if isinstance(item, str):
                resolved.append(get_theme_spacing(item))
            else:
                resolved.append(int(item))
        return tuple(resolved)
    return int(value)


def themed_grid(
    widget: Any,
    *,
    sticky: str | None = tk.NSEW,
    padx: SpacingArg = None,
    pady: SpacingArg = None,
    **kwargs: Any,
) -> None:
    """Grid a widget using theme token names for spacing."""
    grid_kwargs = dict(kwargs)
    if sticky is not None:
        grid_kwargs["sticky"] = sticky

    resolved_padx = _resolve_spacing(padx)
    if resolved_padx is not None:
        grid_kwargs["padx"] = resolved_padx

    resolved_pady = _resolve_spacing(pady)
    if resolved_pady is not None:
        grid_kwargs["pady"] = resolved_pady

    widget.grid(**grid_kwargs)


def _iter_grid_specs(specs: GridConfig) -> list[tuple[int, dict[str, int]]]:
    """Normalize grid configuration input into Tk configure calls."""
    if specs is None:
        return []
    if isinstance(specs, int):
        return [(index, {"weight": 1}) for index in range(specs)]

    if isinstance(specs, dict):
        items = specs.items()
    else:
        items = enumerate(specs)

    normalized: list[tuple[int, dict[str, int]]] = []
    for index, spec in items:
        if spec is None:
            continue
        if isinstance(spec, int):
            normalized.append((index, {"weight": spec}))
        else:
            normalized.append((index, dict(spec)))
    return normalized


def configure_grid(
    widget: Any,
    *,
    columns: GridConfig = None,
    rows: GridConfig = None,
) -> None:
    """Configure grid weights and minsizes with a compact declarative syntax."""
    for index, options in _iter_grid_specs(columns):
        widget.grid_columnconfigure(index, **options)
    for index, options in _iter_grid_specs(rows):
        widget.grid_rowconfigure(index, **options)


class CommonMethods:
    """This class is a collection of common methods for handling variables, widgets,
    and buttons.
    """

    def get_variables(self) -> Dict[str, Any]:
        """This function returns a dictionary of all the variables that are tied to
        each  widget name.

        The key is the widget name, value is the variable associated.

        Returns
        -------
        variables : dict
            The dictionary that holds the variables.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get()
        return variables

    def get_widgets(self) -> Dict[str, Any]:
        """This function returns the dictionary that holds the widgets.

        The key is the widget name, value is the LabelInput class that has all the data.

        Returns
        -------
        widgets : dict
            The dictionary that holds the widgets.
        """
        return self.inputs

    def get_buttons(self) -> Dict[str, ttk.Button]:
        """Get the buttons of the popup

        This function returns the dictionary that holds the buttons.
        The key is the button name, value is the button.

        Returns
        -------
        buttons : Dict[str, ttk.Button]
            Dictionary of all the buttons
        """
        return self.buttons
