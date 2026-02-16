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
import tkinter as tk
from tkinter import ttk
import logging

# Third Party Imports
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as tck

from navigate.view.custom_widgets.hover import HoverCheckButton

# Local Imports
from navigate.view.custom_widgets.popup import PopUp
from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from navigate.view.custom_widgets.validation import ValidatedSpinbox
from navigate.view.theme import get_theme_color, get_theme_font

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class AutofocusPopup:
    """Class creates the popup to configure autofocus parameters."""

    def __init__(self, root, *args, **kwargs):
        """Initialize the AutofocusPopup class.

        Parameters
        ----------
        root : tk.Tk
            Root window.
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.
        """
        #: PopUp: The autofocusing popup window
        self.popup = PopUp(
            root, "Autofocus Settings", "+320+180", top=False, transient=False
        )

        #: dict: Dictionary of all the input widgets.
        self.inputs = {}

        #: dict: Dictionary of all the setting variables.
        self.setting_vars = {}

        # Creating content frame
        content_frame = self.popup.get_frame()

        for c in range(3):
            content_frame.grid_columnconfigure(c, weight=1)
        content_frame.grid_rowconfigure(3, weight=1)

        # Section 1.
        device_frame = ttk.Labelframe(
            content_frame, text="Device Type and Focusing Axis", labelanchor="n"
        )
        ttk.Style().configure(
            "Bold.TLabelframe.Label", font=get_theme_font("title")
        )
        device_frame.configure(style="Bold.TLabelframe")
        device_frame.grid(
            row=0, column=0, columnspan=3, sticky=tk.NSEW, padx=10, pady=(5, 10)
        )

        self.inputs["device"] = LabelInput(
            parent=device_frame,
            label="Device Type:",
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            input_args={"width": 20, "state": "readonly"},
            label_args={"padding": (0, 0, 10, 0)},
        )
        self.inputs["device"].grid(row=0, column=0, pady=6, padx=10, sticky=tk.W)

        self.inputs["device_ref"] = LabelInput(
            parent=device_frame,
            label="Focusing Axis:",
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            input_args={"width": 20, "state": "readonly"},
            label_args={"padding": (0, 0, 10, 0)},
        )
        self.inputs["device_ref"].grid(row=0, column=1, pady=6, padx=10, sticky=tk.W)

        # Section 2.
        scan_frame = ttk.Labelframe(
            content_frame,
            text="Scan Parameters",
            labelanchor="n",
            style="Bold.TLabelframe",
        )
        scan_frame.grid(
            row=1, column=0, columnspan=3, sticky=tk.NSEW, padx=10, pady=(0, 10)
        )

        for c in range(3):
            scan_frame.grid_columnconfigure(c, weight=1)
        starting_row_id = 0

        title_labels = [
            "",
            "Range  (" + "\N{GREEK SMALL LETTER MU}" + "m)",
            "Step Size  (" + "\N{GREEK SMALL LETTER MU}" + "m)",
        ]
        for i in range(3):
            title = ttk.Label(scan_frame, text=title_labels[i], padding=(2, 5, 0, 0))
            title.grid(row=starting_row_id, column=i, sticky=tk.EW)

        setting_names = ["coarse", "fine", "robust_fit"]
        setting_labels = ["Coarse", "Fine", "Inverse Power Tent Fit"]
        hover_text = [
            "Performs a broad autofocus scan centered on the current position. \n"
            "The system evaluates focus values from current position – (range / 2) to "
            "current position + (range / 2), using the specified step size. \n"
            "If 'Fine' is also selected, the result of the coarse search is used as "
            "the center point for a more precise fine scan.",
            "Performs a refined secondary autofocus scan around the best focus found "
            "during the coarse search. \nThe fine scan covers a smaller region, "
            "e.g., from the coarse peak position – (fine range / 2) to the coarse peak "
            "position + (fine range / 2) "
            "using the finer step size defined in this section. \nThis step provides "
            "sub-micron precision in determining the optimal focal plane.",
            "Fits an inverse power tent curve to estimate the peak focus value. "
            "Results can improve accuracy but may be unstable in noisy data.",
        ]

        for i in range(2):
            variable = tk.BooleanVar(value=False)
            widget = HoverCheckButton(
                scan_frame, text=setting_labels[i], variable=variable
            )
            widget.hover.setdescription(hover_text[i])
            widget.grid(
                row=i + 1 + starting_row_id,
                column=0,
                sticky=tk.W,
                padx=5,
                pady=(8 if i == 0 else 6, 4),
            )
            self.setting_vars[setting_names[i] + "_selected"] = variable

            # Column 1 - Ranges
            widget = LabelInput(
                parent=scan_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
                input_args={"from_": 0.0, "to": 50000},
            )
            widget.grid(
                row=i + 1 + starting_row_id,
                column=1,
                sticky=tk.EW,
                padx=(0, 8),
                pady=(6, 4),
            )
            self.inputs[setting_names[i] + "_range"] = widget
            self.setting_vars[setting_names[i] + "_range"] = widget.get_variable()

            # Column 2 - Step Sizes
            widget = LabelInput(
                parent=scan_frame,
                input_class=ValidatedSpinbox,
                input_var=tk.StringVar(),
                input_args={"from_": 0.0, "to": 50000},
            )
            widget.grid(
                row=i + 1 + starting_row_id,
                column=2,
                sticky=tk.EW,
                padx=(0, 8),
                pady=(6, 4),
            )
            self.inputs[setting_names[i] + "_step_size"] = widget
            self.setting_vars[setting_names[i] + "_step_size"] = widget.get_variable()

        # Section 3.
        options_frame = ttk.Labelframe(
            content_frame,
            text="Curve Fitting and Statistical Tests",
            labelanchor="n",
            style="Bold.TLabelframe",
        )
        options_frame.grid(
            row=2, column=0, columnspan=3, sticky=tk.NSEW, padx=10, pady=(0, 10)
        )
        for c in range(3):
            options_frame.grid_columnconfigure(c, weight=1)

        variable = tk.BooleanVar(value=False)
        robust_fit = HoverCheckButton(
            options_frame, text=setting_labels[2], variable=variable
        )
        robust_fit.grid(row=0, column=0, sticky=tk.W, padx=6, pady=6)
        self.setting_vars["robust_fit"] = variable
        robust_fit.hover.setdescription(
            "Fit the data with an inverse power tent to identify the ideal focus."
        )

        variable = tk.BooleanVar(value=False)
        spline_fit = HoverCheckButton(
            options_frame, text="Spline Fit", variable=variable
        )
        spline_fit.grid(row=0, column=1, sticky=tk.W, padx=6, pady=6)
        self.setting_vars["spline_fit"] = variable
        spline_fit.hover.setdescription(
            "Fit the data with a spline to identify the ideal focus."
        )

        variable = tk.BooleanVar(value=False)
        test_significance = HoverCheckButton(
            options_frame, text="Test Significance", variable=variable
        )
        test_significance.grid(row=0, column=2, sticky=tk.W, padx=6, pady=6)
        self.setting_vars["test_significance"] = variable
        test_significance.hover.setdescription(
            "Only accept focus positions that provide a statistically significant "
            "response. \nSignificance defined as the mean + 2 standard deviations."
        )

        # Section 4. Autofocus Button
        style = ttk.Style()
        try:
            # Make it bolder/bigger with extra padding
            style.configure(
                "Accent.TButton",
                font=get_theme_font("button_emphasis"),
                padding=(14, 8),
            )
            theme = style.theme_use()
            if theme not in ("aqua", "vista", "xpnative"):
                style.map(
                    "Accent.TButton",
                    foreground=[
                        ("pressed", get_theme_color("text", "white")),
                        ("active", get_theme_color("text", "white")),
                    ],
                    background=[
                        ("pressed", get_theme_color("accent_pressed", "#2c6be0")),
                        ("active", get_theme_color("accent_hover", "#3478f6")),
                        ("!disabled", get_theme_color("accent", "#3478f6")),
                    ],
                )
        except tk.TclError:
            pass
        button_bar = ttk.Frame(content_frame)
        button_bar.grid(
            row=3, column=0, columnspan=3, sticky=tk.NSEW, padx=10, pady=(0, 6)
        )

        self.autofocus_btn = ttk.Button(
            button_bar, text="▶ Start Autofocus", style="Accent.TButton", width=18
        )
        self.autofocus_btn.pack(pady=(4, 6), anchor="center")
        button_bar.grid_columnconfigure(0, weight=1)

        # Plot
        plot_label_size = int(get_theme_font("body")[1])
        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.coarse = self.fig.add_subplot(111)
        self.coarse.set_ylabel("Discrete Cosine Transform", fontsize=plot_label_size)
        self.coarse.set_xlabel("Focus Stage Position", fontsize=plot_label_size)
        self.coarse.yaxis.set_minor_locator(tck.AutoMinorLocator())
        self.coarse.xaxis.set_minor_locator(tck.AutoMinorLocator())

        self.fig.tight_layout()
        canvas = FigureCanvasTkAgg(self.fig, master=content_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(
            row=4,
            column=0,
            columnspan=3,
            sticky=tk.NSEW,
            padx=10,
            pady=(0, 10),
        )

        # Allow the plot row to stretch
        content_frame.grid_rowconfigure(4, weight=1)

    def get_widgets(self):
        """Returns the dictionary of input widgets.

        Returns
        -------
        dict
            Dictionary of all the input widgets.
        """
        return self.inputs


if __name__ == "__main__":
    # Launch the popup
    root = tk.Tk()
    AutofocusPopup(root=root)
    root.mainloop()
