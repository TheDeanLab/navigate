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
import platform
import tkinter as tk
from typing import Any
import logging

# Third Party Imports
import numpy as np
from matplotlib.ticker import FuncFormatter

# Local Imports
from navigate.model.concurrency.concurrency_tools import SharedNDArray
from navigate.view.main_window_content.display_notebook import HistogramFrame
from navigate.view.theme import get_theme_color, get_theme_matplotlib_font
from navigate.config import update_config_dict
from navigate.tools.decorators import performance_monitor


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class HistogramController:
    """Histogram controller"""

    def __init__(self, histogram: HistogramFrame, parent_controller: Any) -> None:
        """Initialize the histogram controller

        Parameters
        ----------
        histogram : HistogramFrame
            Histogram view
        parent_controller : Any
            Main controller.
        """

        #: HistogramFrame: Histogram view
        self.histogram = histogram

        #: MainController: Main controller
        self.parent_controller = parent_controller

        #: FigureBase: The histogram figure.
        self.ax = self.histogram.figure.add_axes([0.075, 0.25, 0.88, 0.65])
        self.ax.tick_params(
            axis="both", which="both", direction="inout", labelsize=8, reset=True
        )

        # Event Bindings
        widget = self.histogram.figure_canvas.get_tk_widget()

        if platform.system() == "Darwin":
            widget.bind("<Button-2>", self.histogram_popup)
        else:
            widget.bind("<Button-3>", self.histogram_popup)

        # Default axis values
        self.x_axis_var = tk.StringVar(value="linear")
        self.y_axis_var = tk.StringVar(value="log")

        #: bool: Histogram enabled
        self.histogram_enabled = tk.BooleanVar()

        #: bool: Logarithmic X-axis
        self.log_x = False

        #: bool: Logarithmic Y-axis
        self.log_y = True

        #: tk.Menu: Histogram popup menu
        self.menu = tk.Menu(widget, tearoff=0)
        self.menu.add_radiobutton(
            label="Log X",
            variable=self.x_axis_var,
            value="log",
            command=self.update_scale,
        )
        self.menu.add_radiobutton(
            label="Linear X",
            variable=self.x_axis_var,
            value="linear",
            command=self.update_scale,
        )
        self.menu.add_separator()
        self.menu.add_radiobutton(
            label="Log Y",
            variable=self.y_axis_var,
            value="log",
            command=self.update_scale,
        )
        self.menu.add_radiobutton(
            label="Linear Y",
            variable=self.y_axis_var,
            value="linear",
            command=self.update_scale,
        )
        self.menu.add_separator()
        self.menu.add_checkbutton(
            label="Enable Histogram",
            variable=self.histogram_enabled,
            onvalue=True,
            offvalue=False,
            command=self.update_experiment,
        )

        #: Optional[str]: Tk after-id for a coalesced histogram redraw
        self._histogram_after_id = None
        #: SharedNDArray: latest frame pending for histogram update
        self._pending_histogram_image = None

        # Default location for communicating with the plugin in the model.
        if "histogram" not in self.parent_controller.configuration["gui"].keys():
            update_config_dict(
                manager=self.parent_controller.manager,
                parent_dict=self.parent_controller.configuration["gui"],
                config_name="histogram",
                new_config={"enabled": True},
            )

        # Set histogram according to the experiment.yaml file. If disabled, stays disabled upon restart.
        self.histogram_enabled.set(
            self.parent_controller.configuration["gui"]["histogram"].get(
                "enabled", True
            )
        )

    def update_experiment(self) -> None:
        """Update the experiment.yaml file. Also communicate any changes to the menu
        controller."""
        # Get the state of the histogram enabled variable.
        histogram_state = self.histogram_enabled.get()

        # Update the experiment.yaml file.
        self.parent_controller.configuration["gui"]["histogram"][
            "enabled"
        ] = histogram_state

        # Communicate changes to the menu controller.
        self.parent_controller.menu_controller.histogram_enabled.set(histogram_state)

    def update_scale(self) -> None:
        """Update the scale of the histogram"""
        self.log_x = self.x_axis_var.get() == "log"
        self.log_y = self.y_axis_var.get() == "log"

    def histogram_popup(self, event: tk.Event) -> None:
        """Histogram popup menu

        Parameters
        ----------
        event : tk.Event
            Event
        """
        try:
            self.menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.menu.grab_release()

    def populate_histogram(self, image: SharedNDArray) -> None:
        """Populate the histogram on the Tk thread.

        Parameters
        ----------
        image : SharedNDArray
            Image data
        """
        self._pending_histogram_image = image
        if self._histogram_after_id is not None:
            return

        widget = self.histogram.figure_canvas.get_tk_widget()
        self._histogram_after_id = widget.after_idle(
            self._flush_pending_histogram_update
        )

    def _flush_pending_histogram_update(self) -> None:
        """Render the latest queued histogram update."""
        self._histogram_after_id = None
        image = self._pending_histogram_image
        self._pending_histogram_image = None
        if image is None:
            return
        if not self.histogram_enabled.get():
            self._clear_histogram()
            return
        self._populate_histogram(image)

    @performance_monitor(prefix="Histogram")
    def _populate_histogram(self, image: SharedNDArray) -> None:
        """Populate the histogram

        We continue to reduce the size of the histogram to make it more efficient.
        To estimate a distribution within ±ε accuracy in total variation distance (
        TVD), you typically need O(B / ε²) samples, where B is the number of
        histogram bins, and ε is the desired accuracy.

        Parameters
        ----------
        image : SharedNDArray
            Image Data
        """

        # Estimate total variation distance.
        number_bins = 20
        accuracy = 0.05  # 5% accuracy in histogram.
        required_pixels = number_bins / (accuracy**2)
        actual_pixels = image.size

        # Downsample data to the required number of pixels to meet accuracy.
        down_sampling_constant = max(1, int(actual_pixels // required_pixels))
        data = image.flatten()
        data = data[::down_sampling_constant]

        # Plot histogram.
        self.ax.cla()
        counts, bins = np.histogram(data, bins=number_bins)
        self.ax.bar(bins[:-1], counts, width=np.diff(bins), color="black", align="edge")

        x_maximum = np.max(data) + np.std(data)
        x_minimum = np.min(data) - np.std(data)
        x_minimum = 1 if x_minimum < 1 else x_minimum
        y_maximum = 10**6 // down_sampling_constant

        self.ax.set_xlim(x_minimum, x_maximum)
        self.ax.set_ylim(1, y_maximum)

        if self.log_y:
            self.ax.set_yscale("log")

        if self.log_x:
            self.ax.set_xscale("log")

        self.ax.yaxis.set_major_formatter(
            FuncFormatter(
                lambda val, pos: f"$10^{{{int(np.log10(val))}}}$" if val > 0 else ""
            )
        )
        self.histogram.figure_canvas.draw()

    def _clear_histogram(self) -> None:
        """Clear the histogram but keep canvas interactive."""
        body_fontdict = get_theme_matplotlib_font("body")
        self.ax.cla()
        self.ax.text(
            x=0.5,
            y=0.5,
            s="Intensity Histogram Disabled\nRight Click to Enable",
            fontdict={
                **body_fontdict,
                "style": "italic",
                "color": get_theme_color("muted_text", "gray"),
            },
            ha="center",
            va="center",
            bbox=dict(
                facecolor=get_theme_color("panel_bg", "white"),
                edgecolor=get_theme_color("border", "none"),
                boxstyle="round,pad=0.5",
            ),
            transform=self.ax.transAxes,
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.histogram.figure_canvas.draw()
