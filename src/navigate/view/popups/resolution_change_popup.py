# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Recovery dialog for a cancelled resolution change."""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from navigate.view.custom_widgets.popup import PopUp
from navigate.view.theme import get_theme_padding_px


class ResolutionChangeCancelledPopup:
    """Offer safe stage-position choices after resolution cancellation."""

    def __init__(
        self,
        root: tk.Tk,
        keep_command: Callable[[], None],
        return_command: Callable[[], None],
        return_enabled: bool,
    ) -> None:
        """Create the modal recovery dialog.

        Parameters
        ----------
        root : tk.Tk
            Navigate's main application window.
        keep_command : Callable[[], None]
            Callback that accepts the actual stopped position without moving stages.
        return_command : Callable[[], None]
            Callback that starts the separately cancellable return movement.
        return_enabled : bool
            Whether a complete, limit-validated pre-movement position is available.
        """
        self._keep_command = keep_command
        self._return_command = return_command
        self.popup = PopUp(
            root,
            "Resolution Change Cancelled",
            "560x190+320+180",
            transient=True,
        )
        frame = self.popup.get_frame()
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        message = ttk.Label(
            frame,
            text=(
                "Stage motion was stopped at the position now shown in Navigate. "
                "Keep the stages here, or return them to their positions before "
                "the resolution change. Returning will move the stages again."
            ),
            justify=tk.LEFT,
            wraplength=520,
        )
        message.grid(
            row=0,
            column=0,
            columnspan=2,
            padx=get_theme_padding_px(20),
            pady=get_theme_padding_px((20, 15)),
            sticky=tk.NSEW,
        )

        self.keep_button = ttk.Button(
            frame,
            text="Keep Current Position",
            command=self._keep,
        )
        self.keep_button.grid(
            row=1,
            column=0,
            padx=get_theme_padding_px((20, 10)),
            pady=get_theme_padding_px((0, 20)),
            sticky=tk.EW,
        )

        self.return_button = ttk.Button(
            frame,
            text="Return to Previous Position",
            command=self._return,
            state="normal" if return_enabled else "disabled",
        )
        self.return_button.grid(
            row=1,
            column=1,
            padx=get_theme_padding_px((10, 20)),
            pady=get_theme_padding_px((0, 20)),
            sticky=tk.EW,
        )

        self.popup.protocol("WM_DELETE_WINDOW", self._keep)
        self.popup.bind("<Escape>", self._keep)
        self.keep_button.focus_set()

    def _keep(self, *_args) -> None:
        """Dismiss the dialog before accepting the stopped position."""
        self.popup.dismiss()
        self._keep_command()

    def _return(self, *_args) -> None:
        """Dismiss the modal dialog before starting return motion."""
        self.popup.dismiss()
        self._return_command()
