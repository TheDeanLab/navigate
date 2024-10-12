# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

# Third Party Imports
import numpy as np

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController

# Logger Setup
# p = __name__.split(".")[1]
# logger = logging.getLogger(p)


class HistogramController(GUIController):
    """Histogram controller"""

    def __init__(self, histogram, parent_controller) -> None:
        """Initialize the histogram controller

        Parameters
        ----------
        histogram : HistogramFrame
            Histogram view
        parent_controller : MainController
            Main controller
        """

        #: HistogramFrame: Histogram view
        self.histogram = histogram

        #: MainController: Main controller
        self.parent_controller = parent_controller

        #: FigureBase: The histogram figure.
        self.figure = self.histogram.figure.add_subplot(111)

        # Event Bindings
        widget = self.histogram.figure_canvas.get_tk_widget()

        if platform.system() == "Darwin":
            widget.bind("<Button-2>", self.histogram_popup)
        else:
            widget.bind("<Button-3>", self.histogram_popup)

        # Default axis values
        self.x_axis_var = tk.StringVar(value="linear")
        self.y_axis_var = tk.StringVar(value="linear")

        # #: tk.Menu: Histogram popup menu
        # self.menu = tk.Menu(widget, tearoff=0)
        # self.menu.add_radiobutton(
        #     label="Log X",
        #     variable=self.x_axis_var,
        #     value="log",
        #     command=self.update_scale,
        # )
        # self.menu.add_radiobutton(
        #     label="Linear X",
        #     variable=self.x_axis_var,
        #     value="linear",
        #     command=self.update_scale,
        # )
        # self.menu.add_separator()
        # self.menu.add_radiobutton(
        #     label="Log Y",
        #     variable=self.y_axis_var,
        #     value="log",
        #     command=self.update_scale,
        # )
        # self.menu.add_radiobutton(
        #     label="Linear Y",
        #     variable=self.y_axis_var,
        #     value="linear",
        #     command=self.update_scale,
        # )

        #: bool: Logarithmic X-axis
        self.log_x = False

        #: bool: Logarithmic Y-axis
        self.log_y = True

        self.populate_histogram(image=np.random.normal(100, 20, 1000))

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

    def populate_histogram(self, image: np.ndarray) -> None:
        """Populate the histogram.

        Parameters
        ----------
        image : np.ndarray
            Image data
        """
        data = image.flatten()
        self.figure.clear()
        self.figure.hist(data, color="black", bins=50)

        # Limits
        std_dev = np.std(data)
        xmin, xmax = np.min(data) - std_dev, np.max(data) + std_dev
        xmin = 0 if xmin < 0 else xmin

        # Tick marks.
        num_ticks = 5
        if self.log_x:
            ticks = np.log10(np.logspace(np.log10(xmin), np.log10(xmax), num_ticks))
            self.figure.set_xscale("log", nonpositive="clip", subs=[])
            self.figure.set_xticks(ticks)
            self.figure.set_xticklabels(
                [f"{10**tick:.2f}" for tick in ticks], fontsize=6
            )
        else:
            ticks = np.linspace(xmin, xmax, num_ticks)
            self.figure.set_xticks(ticks)
            self.figure.set_xticklabels([f"{tick:.2f}" for tick in ticks], fontsize=6)

        self.figure.set_xlim([xmin, xmax])
        self.figure.set_xlabel("", fontsize=4)

        # Y-axis
        if self.log_y:
            self.figure.set_yscale("log")

        self.figure.set_ylabel("", fontsize=6)
        self.figure.set_yticks([])

        # Draw the figure

        self.histogram.figure_canvas.draw()
