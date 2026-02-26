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

# Standard library imports
from typing import Any
import tkinter as tk

# Third-party imports

# Local imports
from navigate.view.theme import get_theme_color


class CollapsibleFrame(tk.Frame):
    """A frame that can be expanded or collapsed via its header label."""

    def __init__(
        self, parent: tk.Widget, title: str = "", *args: Any, **kwargs: Any
    ) -> None:
        """Create a collapsible frame widget.

        Parameters
        ----------
        parent : tk.Widget
            Parent widget that will contain this frame.
        title : str, optional
            Header text shown on the collapsible bar, by default "".
        *args : Any
            Positional arguments forwarded to ``tk.Frame``.
        **kwargs : Any
            Keyword arguments forwarded to ``tk.Frame``.

        Returns
        -------
        None
            The widget is initialized in place.
        """
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.title: str = title
        self.visible: bool = False

        # Create a label to act as a title/header
        self.label = tk.Label(
            self,
            text=self.title,
            bg=get_theme_color("surface_bg", "lightgrey"),
            fg=get_theme_color("text", "black"),
            relief="raised",
            padx=5,
        )
        self.label.grid(row=0, column=0, sticky=tk.NSEW)

        # Create a frame to hold the contents of the collapsible frame
        self.content_frame: tk.Frame = tk.Frame(
            self,
            bg=get_theme_color("panel_bg", self.cget("bg")),
        )
        self.toggle_visibility()

        self.label.bind("<Button-1>", lambda event: self.toggle_visibility())

    def toggle_visibility(self) -> None:
        """Toggle the visibility of the content frame.

        Returns
        -------
        None
            The widget state is updated in place.
        """
        if self.visible:
            self.label["text"] = self.title + " " + "\u25bc"
            self.content_frame.grid_forget()  # Hide the content frame
            self.visible = False
        else:
            self.label["text"] = self.title + " " + "\u25b2"
            self.content_frame.grid(
                row=1, column=0, sticky=tk.NSEW
            )  # Show the content frame
            self.visible = True

    def fold(self) -> None:
        """Collapse the content frame if it is currently visible.

        Returns
        -------
        None
            The widget state is updated in place.
        """
        if self.visible:
            self.toggle_visibility()
