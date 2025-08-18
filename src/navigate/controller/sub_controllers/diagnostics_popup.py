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
import logging
import os
from typing import Optional
from datetime import datetime
import re

# Third Party Imports
import numpy as np
import matplotlib.dates as mdates

# Local Imports
from navigate.view.popups.diagnostics_popup import DiagnosticsPopup
from navigate.log_files.log_functions import load_latest_log_file

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class DiagnosticsPopupController:
    """Controller for the Advanced Stage Parameters popup."""

    def __init__(
        self,
        popup: DiagnosticsPopup,
        parent_controller: "Controller",
        *args,
        **kwargs,
    ) -> None:
        """Initialize the AdvancedStageParametersController class.

        Parameters
        ----------
        root : tk.Tk
            The root window
        popup : DiagnosticsPopup
            The popup window for the diagnostics
        parent_controller : Controller
            The parent controller that manages this popup
        *args
            Variable length argument list
        **kwargs
            Arbitrary keyword arguments
        """

        # Initialize the parent controller
        self.parent_controller = parent_controller

        #: PopUp: Popup window for the stage limits.
        self.view = popup

        # Configure traces for closing the window or pressing escape.
        self.view.popup.protocol("WM_DELETE_WINDOW", self.close_popup)
        self.view.popup.bind("<Escape>", lambda event: self.close_popup())

        # Add trace to self.populate_plots to generate initial data
        self.view.buttons["update"].configure(
            command=self.populate_plots,
        )

        # Initialize plots (empty)
        self.initialize_plots()

    def showup(self) -> None:
        """This function will let the popup window show in front."""
        self.view.popup.deiconify()

    def close_popup(self) -> None:
        """Close the popup window."""
        self.view.popup.destroy()

        if hasattr(self.parent_controller, "diagnostics_controller"):
            del self.parent_controller.diagnostics_controller

        logger.debug("Diagnostics popup closed and sub-controller deleted.")

    def initialize_plots(self):
        """Initialize empty plots with axes but no data."""
        # Y-axis labels for each plot
        y_labels = {
            1: "Frequency",
            2: "FPS",
            3: "MB/s",
            4: "Time (ms)",
            5: "Time (ms)",
            6: "Memory (MB)",
        }

        # Initialize each plot without data
        for i in range(1, 7):
            # Get figure and clear it
            fig = self.view.inputs[f"diagnostics_{i}"]
            ax = fig.axes[0]
            ax.clear()

            # Add labels and grid
            ax.set_xlabel("Time (ms)")
            ax.set_ylabel(y_labels[i])
            ax.grid(True, linestyle="--", alpha=0.7)

            # Set reasonable y limits
            ax.set_ylim(0, 100)

            # Draw the empty canvas
            self.view.inputs[f"canvas_{i}"].draw()
            self.view.inputs[f"canvas_{i}"].get_tk_widget().pack(
                fill="both", expand=True
            )

    def populate_plots(self):
        """Generate and display dummy data for all diagnostic plots."""

        model_log, controller_log = load_latest_log_file()

        # Plot the histogram of the display times from the controller log
        self.plot_display_time_histogram(controller_log)

        # Plot the duration of time necessary to transfer the data between processes.

        #
        # # Generate dummy data
        # time_points = np.linspace(0, 60, 100)  # 60 seconds of data
        #
        # # Different data patterns for each plot
        # data_sets = {
        #     1: 10
        #     + 5 * np.sin(np.linspace(0, 4 * np.pi, 100))
        #     + np.random.normal(0, 1, 100),  # IPC latency
        #     2: 30
        #     + 5 * np.sin(np.linspace(0, 3 * np.pi, 100))
        #     + np.random.normal(0, 2, 100),  # Display FPS
        #     3: 25
        #     + 10 * np.sin(np.linspace(0, 2 * np.pi, 100))
        #     + np.random.normal(0, 3, 100),  # Saving rate
        #     4: 15
        #     + 7 * np.sin(np.linspace(0, 5 * np.pi, 100))
        #     + np.random.normal(0, 1.5, 100),  # Histogram update
        #     5: 50
        #     + 20 * np.sin(np.linspace(0, 2.5 * np.pi, 100))
        #     + np.random.normal(0, 5, 100),  # Processing time
        #     6: np.cumsum(np.random.normal(0, 5, 100))
        #     + 500,  # Memory usage (growing trend)
        # }
        #
        # # Y-axis labels for each plot
        # y_labels = {
        #     1: "Latency (ms)",
        #     2: "FPS",
        #     3: "MB/s",
        #     4: "Time (ms)",
        #     5: "Time (ms)",
        #     6: "Memory (MB)",
        # }
        #
        # # Update each plot
        # for i in range(2, 7):
        #     # Get figure and clear it
        #     fig = self.view.inputs[f"diagnostics_{i}"]
        #     ax = fig.axes[0]
        #     ax.clear()
        #
        #     # Plot the data
        #     ax.plot(time_points, data_sets[i], linewidth=2)
        #
        #     # Add labels and grid
        #     ax.set_xlabel("Time (s)")
        #     ax.set_ylabel(y_labels[i])
        #     ax.grid(True, linestyle="--", alpha=0.7)
        #
        #     # Add some stats
        #     mean_val = np.mean(data_sets[i])
        #     ax.text(
        #         0.05,
        #         0.95,
        #         f"Mean: {mean_val:.2f}",
        #         transform=ax.transAxes,
        #         fontsize=9,
        #         va="top",
        #         bbox=dict(boxstyle="round", alpha=0.1),
        #     )
        #
        #     # Draw the canvas
        #     self.view.inputs[f"canvas_{i}"].draw()
        #     self.view.inputs[f"canvas_{i}"].get_tk_widget().pack(
        #         fill="both", expand=True
        #     )

    @staticmethod
    def extract_display_times(log_content):
        """
        Extract image display times from controller log content.

        Parameters
        ----------
        log_content : list or None
            List of log lines from the controller log

        Returns
        -------
        list
            A list of float values representing display times in seconds
        """

        if not log_content:
            return []

        # Pattern to match display time entries
        pattern = r"camera_view: Displaying image took (\d+\.\d+) seconds"

        # Extract all matching times
        display_times = []
        for line in log_content:
            match = re.search(pattern, line)
            if match:
                display_times.append(float(match.group(1)))

        return display_times

    def plot_display_time_histogram(self, controller_log):
        """
        Create a histogram of image display times with statistics.

        Parameters
        ----------
        controller_log : str
            The content of the controller log file as a string or list of lines
        """

        fig = self.view.inputs[f"diagnostics_1"]
        ax = fig.axes[0]
        ax.clear()

        display_times = self.extract_display_times(controller_log)

        if not display_times:
            ax.text(
                0.5,
                0.5,
                "No display time data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            return

        # Convert to milliseconds for better readability
        display_times_ms = [t * 1000 for t in display_times]

        # Plot histogram
        _, _, _ = ax.hist(
            display_times_ms,
            bins=20,
            alpha=0.7,
            color="skyblue",
            edgecolor="black",
            linewidth=1.2,
        )

        # Calculate statistics
        mean_val = np.mean(display_times_ms)
        std_val = np.std(display_times_ms)

        # Add vertical lines for mean and std dev
        ax.axvline(
            mean_val,
            color="r",
            linestyle="dashed",
            linewidth=2,
            label=f"Mean: {mean_val:.2f} ms",
        )
        ax.axvline(
            mean_val + std_val,
            color="g",
            linestyle="dotted",
            linewidth=2,
            label=f"Mean+StdDev: {mean_val+std_val:.2f} ms",
        )
        ax.axvline(mean_val - std_val, color="g", linestyle="dotted", linewidth=2)

        # Add text with statistics
        stats_text = f"Mean: {mean_val:.2f} ms\nStd Dev: {std_val:.2f} ms\nSamples: {len(display_times_ms)}"
        ax.text(
            0.05,
            0.95,
            stats_text,
            transform=ax.transAxes,
            fontsize=9,
            va="top",
            bbox=dict(boxstyle="round", alpha=0.5),
        )

        # Update labels
        ax.set_xlabel("Time (ms)")
        ax.set_ylabel("Frequency")

        # Add grid
        ax.grid(True, linestyle="--", alpha=0.7)

        # Draw the canvas
        self.view.inputs[f"canvas_1"].draw()
        self.view.inputs[f"canvas_1"].get_tk_widget().pack(fill="both", expand=True)
