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
from datetime import datetime
import re
from tkinter import filedialog
from typing import Optional, Iterable

from PIL import ImageGrab

# Third Party Imports
import numpy as np

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

        # Add trace to save a screenshot of the popup
        self.view.buttons["save_image"].configure(command=self.capture_image)

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

    def capture_image(self) -> None:

        # Create default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"diagnostics_{timestamp}.png"

        # Set default directory to user's home directory
        default_dir = os.path.expanduser("~")

        # Open file dialog
        file_path = filedialog.asksaveasfilename(
            initialdir=default_dir,
            initialfile=default_filename,
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )

        # If user cancels, return without saving
        if not file_path:
            return

        # Make sure that the save dialog has time to close before capturing the screenshot
        self.view.popup.after(100, lambda: self._take_screenshot(file_path))

    def _take_screenshot(self, file_path: str) -> None:
        """Capture a screenshot of the diagnostics popup and save it to the specified file path.

        Parameters
        ----------
        file_path : str
            The path where the screenshot will be saved.
        """
        # Get the window geometry
        x = self.view.diagnostics_frame.winfo_rootx()
        y = self.view.diagnostics_frame.winfo_rooty()
        width = self.view.diagnostics_frame.winfo_width()
        height = self.view.diagnostics_frame.winfo_height()
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        screenshot.save(file_path)
        logger.info(f"Diagnostics screenshot saved to: {file_path}")

    def initialize_plots(self) -> None:
        """Initialize empty plots with axes but no data."""
        # Initialize each plot without data
        for i in range(1, 8):
            # Get figure and clear it
            fig = self.view.inputs[f"diagnostics_{i}"]
            ax = fig.axes[0]
            ax.clear()

            # Add labels and grid
            ax.set_xlabel("Time (ms)")
            ax.grid(True, linestyle="--", alpha=0.7)

            # Set reasonable y limits
            ax.set_ylim(0, 100)

            # Draw the empty canvas
            self.view.inputs[f"canvas_{i}"].draw()
            self.view.inputs[f"canvas_{i}"].get_tk_widget().pack(
                fill="both", expand=True
            )

    def populate_plots(self) -> None:
        """Generate and display dummy data for all diagnostic plots."""

        model_log, controller_log, performance_log = load_latest_log_file()

        # Plot the time necessary to acquire a new image.
        pattern = r"model: New image acquired in (\d+\.\d+) seconds"
        times = self.extract_times(model_log, pattern)
        self.plot_histogram(panel=1, times=times, title="Image Acquisition Time")

        # Plot the histogram of the display times from the controller log
        pattern = r"camera_view: Displaying image took (\d+\.\d+) seconds"
        times = self.extract_times(controller_log, pattern)
        self.plot_histogram(panel=2, times=times, title="Image Display Times")

        # Plot the histogram of the times necessary to populate the histogram.
        pattern = r"histogram: Histogram populated in (\d+\.\d+) seconds"
        times = self.extract_times(controller_log, pattern)
        self.plot_histogram(panel=3, times=times, title="Histogram Population Times")

        # Plot the time to move the z and f stages during a z-stack.
        pattern = (
            r"common_features: Z- and F-position move duration: (\d+\.\d+) seconds"
        )
        times = self.extract_times(model_log, pattern)
        self.plot_histogram(panel=4, times=times, title="Z/F Stage Move Duration")

        # Plot the time necessary to get stage positions.
        pattern = r"model: Stage positions got in (\d+\.\d+) seconds"
        times = self.extract_times(model_log, pattern)
        self.plot_histogram(panel=5, times=times, title="Get Stage Positions Time")

        # Plot the time necessary to turn on/off lasers and send out triggers.
        # The time should closely match the waveform length (exposure time + delay).
        pattern = r"model: DAQ sending out triggers in (\d+\.\d+) seconds"
        times = self.extract_times(model_log, pattern)
        self.plot_histogram(panel=6, times=times, title="DAQ Trigger Time")

        # Plot the time necessary to perform all serial communications.
        times = self.extract_times(performance_log)
        self.plot_histogram(panel=7, times=times, title="Serial Communication Time")

    @staticmethod
    def extract_times(log_content: list, pattern: str = "") -> list:
        """
        Extract image display times from controller log content.

        Parameters
        ----------
        log_content : list or None
            List of log lines from the controller log
        pattern : str
            Regular expression pattern to match display time entries.
            If empty, it assumes JSON format.

        Returns
        -------
        times : list or None
            A list of float values representing times in seconds.
            Returns None if no times are found.
        """

        if not log_content:
            return None

        if isinstance(log_content[0], dict):
            # JSON formatted log exists as a dictionary.
            durations = [entry['duration_ns'] * 1e-9 for entry in log_content]
            return durations if len(durations) > 0 else None

        # Standard logs exist as a list of strings.
        times = []
        for line in log_content:
            match = re.search(pattern, line)
            if match:
                times.append(float(match.group(1)))

        return times if len(times) > 0 else None

    def plot_histogram(self, panel: int, times: Optional[Iterable], title="") -> None:
        """
        Create a histogram of image display times with statistics.

        Parameters
        ----------
        panel : int
            The panel number to plot the histogram on (1-6)
        times : Optional[Iterable]
            A list of times in seconds to plot
        title : str
            The title for the plot. If empty, a default title will be used.
        """
        # add a new figure if necessary
        if f"canvas_{panel}" not in self.view.inputs:
            self.view.add_plot_figure(title)

        fig = self.view.inputs[f"diagnostics_{panel}"]
        ax = fig.axes[0]
        ax.clear()

        if times is None:
            ax.text(
                0.5,
                0.5,
                "No data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            self.view.inputs[f"canvas_{panel}"].draw()
            self.view.inputs[f"canvas_{panel}"].get_tk_widget().pack(
                fill="both", expand=True
            )
            return

        # Convert to milliseconds for better readability
        times_ms = [t * 1000 for t in times]

        # Plot histogram
        _, _, _ = ax.hist(
            times_ms,
            bins=20,
            alpha=0.7,
            color="skyblue",
            edgecolor="black",
            linewidth=1.2,
        )

        # Calculate statistics
        mean_val = np.mean(times_ms)
        std_val = np.std(times_ms)

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

        # Add text with statistics as a title
        stats_text = (
            f"Mean: {mean_val:.2f} ms."
            f"Std Dev: {std_val:.2f} ms."
            f"N: {len(times_ms)}"
        )
        ax.set_title(stats_text, fontsize=9)

        # Update labels
        ax.set_xlabel("Time (ms)")
        ax.set_ylabel("Frequency")

        # Add grid
        ax.grid(True, linestyle="--", alpha=0.7)

        # Draw the canvas
        self.view.inputs[f"canvas_{panel}"].draw()
        self.view.inputs[f"canvas_{panel}"].get_tk_widget().pack(
            fill="both", expand=True
        )
