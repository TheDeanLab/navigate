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
import logging
import platform
import threading
import tkinter as tk
from typing import Any, Optional

# Third Party Imports
import numpy as np
from matplotlib.ticker import FuncFormatter

try:
    import cv2
except ImportError:  # pragma: no cover - cv2 is optional at runtime
    cv2 = None

# Local Imports
from navigate.config import update_config_dict
from navigate.model.concurrency.concurrency_tools import SharedNDArray
from navigate.tools.decorators import performance_monitor
from navigate.view.main_window_content.display_notebook import HistogramFrame
from navigate.view.theme import get_theme_color, get_theme_matplotlib_font


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
        self.ax = self.histogram.figure.add_axes([0.01, 0.20, 0.98, 0.79])

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

        #: int: Thread identifier for Tk main-thread checks
        self._main_thread_ident = threading.get_ident()

        #: Optional[str]: Tk after-id for a coalesced histogram redraw
        self._histogram_after_id = None

        #: SharedNDArray: latest frame pending for histogram update
        self._pending_histogram_image = None

        #: bool: Whether the disabled placeholder is already drawn
        self._histogram_disabled_overlay_drawn = False

        #: int: Number of histogram bins
        self._number_bins = 2**10

        #: float: Target TVD approximation accuracy for sample sizing
        self._hist_accuracy = 0.05

        #: bool: Whether this backend supports artist blitting
        self._blit_supported = all(
            hasattr(self.histogram.figure_canvas, method)
            for method in ("copy_from_bbox", "restore_region", "blit")
        )

        #: Any: Cached background region for histogram-axes blitting
        self._histogram_background = None

        #: Any: Stepfilled histogram artist
        self._histogram_artist = None

        #: bool: Whether histogram artist setup is complete
        self._histogram_artist_ready = False

        #: bool: Whether a full redraw is required before next blit
        self._force_full_redraw = True

        #: bool: Whether the last render path used blitting
        self._last_render_used_blit = False

        #: str: Last formatter mode ("linear" or "log")
        self._y_formatter_mode = ""

        #: float | None: Last x-axis lower/upper limits to reduce tiny redraw churn
        self._last_xlim = None
        self._last_ylim = None

        menu_background = get_theme_color("panel_bg", "#1a212b")
        menu_foreground = get_theme_color("text", "#d7dee8")
        menu_disabled_foreground = get_theme_color("muted_text", "#9aa8bb")
        menu_active_background = get_theme_color("accent", "#4b78b8")
        menu_active_foreground = get_theme_color("text", menu_foreground)
        menu_select_color = get_theme_color("accent_hover", menu_active_background)

        #: tk.Menu: Histogram popup menu
        self.menu = tk.Menu(widget, tearoff=0)
        self.menu.configure(
            background=menu_background,
            foreground=menu_foreground,
            disabledforeground=menu_disabled_foreground,
            activebackground=menu_active_background,
            activeforeground=menu_active_foreground,
            selectcolor=menu_select_color,
        )
        self.menu.add_radiobutton(
            label="Log X",
            variable=self.x_axis_var,
            value="log",
            command=self.update_scale,
            selectcolor=menu_select_color,
        )
        self.menu.add_radiobutton(
            label="Linear X",
            variable=self.x_axis_var,
            value="linear",
            command=self.update_scale,
            selectcolor=menu_select_color,
        )
        self.menu.add_separator()
        self.menu.add_radiobutton(
            label="Log Y",
            variable=self.y_axis_var,
            value="log",
            command=self.update_scale,
            selectcolor=menu_select_color,
        )
        self.menu.add_radiobutton(
            label="Linear Y",
            variable=self.y_axis_var,
            value="linear",
            command=self.update_scale,
            selectcolor=menu_select_color,
        )
        self.menu.add_separator()
        self.menu.add_checkbutton(
            label="Enable Histogram",
            variable=self.histogram_enabled,
            onvalue=True,
            offvalue=False,
            command=self.update_experiment,
            selectcolor=menu_select_color,
        )

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

        self.histogram.figure_canvas.mpl_connect("draw_event", self._on_histogram_draw)
        self._initialize_histogram_axes()

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
        scale_changed = self._apply_axis_scale_settings()
        if scale_changed:
            self._invalidate_blit_cache()

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
        if threading.get_ident() != self._main_thread_ident:
            run_on_main = getattr(self.parent_controller, "_run_on_main_thread", None)
            if callable(run_on_main):
                run_on_main(self.populate_histogram, image, wait=False)
            return

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
            if not self._histogram_disabled_overlay_drawn:
                self._clear_histogram()
                self._histogram_disabled_overlay_drawn = True
            return
        if self._histogram_disabled_overlay_drawn:
            # Remove the disabled placeholder overlay and rebuild artists once.
            self._initialize_histogram_axes()
            self._histogram_disabled_overlay_drawn = False
        try:
            self._populate_histogram(image)
        except Exception as exc:
            logger.exception("Histogram update failed: %s", exc)

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
        self._ensure_histogram_artist()

        # Estimate total variation distance.
        required_pixels = self._number_bins / (self._hist_accuracy**2)
        actual_pixels = image.size

        # Downsample data to the required number of pixels to meet accuracy.
        down_sampling_constant = max(1, int(actual_pixels // required_pixels))
        data = image.ravel()
        data = data[::down_sampling_constant]
        if data.size == 0:
            return

        counts, bins, backend = self._calculate_histogram_counts(data)

        plot_counts = np.maximum(counts, 1.0) if self.log_y else counts
        baseline = 1.0 if self.log_y else 0.0
        self._histogram_artist.set_data(
            values=plot_counts, edges=bins, baseline=baseline
        )

        x_minimum = float(bins[0])
        x_maximum = float(bins[-1])
        x_span = max(1.0, x_maximum - x_minimum)
        x_padding = 0.02 * x_span
        x_minimum -= x_padding
        x_maximum += x_padding
        if self.log_x:
            x_minimum = max(1.0, x_minimum)
            if x_maximum <= x_minimum:
                x_maximum = x_minimum + 1.0

        y_minimum = 1.0 if self.log_y else 0.0
        y_maximum = max(float(np.max(plot_counts)) * 1.15, 2.0 if self.log_y else 1.0)

        force_full_redraw = self._force_full_redraw or self._apply_axis_scale_settings()

        new_xlim = (x_minimum, x_maximum)
        if self._limits_need_update(
            self._last_xlim, new_xlim, rel_tol=0.03, abs_tol=1.0
        ):
            self.ax.set_xlim(*new_xlim)
            self._last_xlim = new_xlim
            force_full_redraw = True

        new_ylim = (y_minimum, y_maximum)
        if self._limits_need_update(
            self._last_ylim, new_ylim, rel_tol=0.08, abs_tol=1.0
        ):
            self.ax.set_ylim(*new_ylim)
            self._last_ylim = new_ylim
            force_full_redraw = True

        self._render_histogram(force_full_redraw=force_full_redraw)

    def _clear_histogram(self) -> None:
        """Clear the histogram but keep canvas interactive."""
        body_fontdict = get_theme_matplotlib_font("body")
        self._histogram_artist_ready = False
        self._histogram_artist = None
        self._invalidate_blit_cache()
        self._last_xlim = None
        self._last_ylim = None

        panel_bg = get_theme_color("panel_bg", "white")
        surface_bg = get_theme_color("surface_bg", panel_bg)
        border_color = get_theme_color("border", "none")
        muted_text = get_theme_color("muted_text", "gray")

        if hasattr(self.histogram, "figure"):
            self.histogram.figure.set_facecolor(panel_bg)
        self.ax.cla()
        self.ax.set_facecolor(surface_bg)
        self.ax.text(
            x=0.5,
            y=0.5,
            s="Intensity Histogram Disabled\nRight Click to Enable",
            fontdict={
                **body_fontdict,
                "style": "italic",
                "color": muted_text,
            },
            ha="center",
            va="center",
            bbox=dict(
                facecolor=panel_bg,
                edgecolor=border_color,
                boxstyle="round,pad=0.5",
            ),
            transform=self.ax.transAxes,
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.histogram.figure_canvas.draw()

    def _initialize_histogram_axes(self) -> None:
        """Apply themed axis styling and initialize a persistent stepfilled artist."""
        self.ax.cla()
        self._apply_theme_to_histogram_axes()
        self._apply_axis_scale_settings()
        self._ensure_histogram_artist()
        self._last_xlim = None
        self._last_ylim = None
        self._force_full_redraw = True
        self._invalidate_blit_cache()

    def _apply_theme_to_histogram_axes(self) -> None:
        """Style histogram figure and axes from the active theme palette."""
        panel_bg = get_theme_color("panel_bg", "#1a212b")
        surface_bg = get_theme_color("surface_bg", panel_bg)
        border = get_theme_color("border", "#2f3a4a")
        text = get_theme_color("text", "#d7dee8")
        muted_text = get_theme_color("muted_text", text)

        if hasattr(self.histogram, "figure"):
            self.histogram.figure.set_facecolor(panel_bg)
        self.ax.set_facecolor(surface_bg)
        self.ax.tick_params(
            axis="both",
            which="both",
            direction="out",
            labelsize=8,
            labelleft=False,
            labelright=False,
            reset=True,
            colors=muted_text,
        )
        self.ax.minorticks_on()
        for spine in self.ax.spines.values():
            spine.set_color(border)
        self.ax.grid(True, axis="y", color=border, alpha=0.35, linewidth=0.6)
        self.ax.grid(False, axis="x")
        self.ax.set_axisbelow(True)

    def _apply_axis_scale_settings(self) -> bool:
        """Apply axis scale toggles and formatter; return True when changed."""
        changed = False
        target_xscale = "log" if self.log_x else "linear"
        target_yscale = "log" if self.log_y else "linear"

        if self.ax.get_xscale() != target_xscale:
            self.ax.set_xscale(target_xscale)
            changed = True

        if self.ax.get_yscale() != target_yscale:
            self.ax.set_yscale(target_yscale)
            changed = True

        formatter_mode = "log" if self.log_y else "linear"
        if formatter_mode != self._y_formatter_mode:
            if self.log_y:
                self.ax.yaxis.set_major_formatter(
                    FuncFormatter(
                        lambda val, pos: (
                            f"$10^{{{int(np.log10(val))}}}$" if val > 0 else ""
                        )
                    )
                )
            else:
                self.ax.yaxis.set_major_formatter(
                    FuncFormatter(lambda val, pos: f"{int(val):d}" if val >= 0 else "")
                )
            self._y_formatter_mode = formatter_mode
            changed = True
        self.ax.minorticks_on()
        return changed

    def _ensure_histogram_artist(self) -> None:
        """Create a persistent stepfilled histogram artist when needed."""
        if self._histogram_artist_ready and self._histogram_artist is not None:
            return

        fill_color = get_theme_color("accent", "#4b78b8")
        edges = np.arange(self._number_bins + 1, dtype=np.float64)
        values = np.ones(self._number_bins, dtype=np.float64)
        baseline = 1.0 if self.log_y else 0.0

        self._histogram_artist = self.ax.stairs(
            values,
            edges,
            baseline=baseline,
            fill=True,
            facecolor=fill_color,
            edgecolor=fill_color,
            linewidth=15,
            alpha=1.0,
            antialiased=False,
        )
        self._histogram_artist.set_snap(True)
        self._histogram_artist.set_animated(self._blit_supported)
        self._histogram_artist_ready = True

    def _calculate_histogram_counts(
        self, data: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, str]:
        """Calculate histogram counts using cv2 when available, with numpy fallback."""
        data_min = float(np.min(data))
        data_max = float(np.max(data))
        if not np.isfinite(data_min) or not np.isfinite(data_max):
            data_min, data_max = 0.0, 1.0

        if data_max <= data_min:
            data_max = data_min + 1.0

        # if data_min + self._number_bins >= data_max:
        #     number_bins = max(2, int(data_max - data_min))
        # else:
        #     number_bins = self._number_bins

        if data_max <= self._number_bins:
            number_bins = max(data_max, 2)
        else:
            number_bins = self._number_bins

        number_bins = int(number_bins)
        bins = np.linspace(data_min, data_max, number_bins + 1, dtype=np.float64)

        if cv2 is not None:
            backend = "cv2.calcHist"
            cv_data = data
            if cv_data.dtype not in (np.uint8, np.uint16, np.float32):
                cv_data = cv_data.astype(np.float32, copy=False)
            histogram_range_max = float(np.nextafter(bins[-1], np.inf))
            try:
                counts = cv2.calcHist(
                    [cv_data],
                    [0],
                    None,
                    [number_bins],
                    [bins[0], histogram_range_max],
                )
                return counts.ravel().astype(np.float64, copy=False), bins, backend
            except Exception:
                logger.debug(
                    "cv2.calcHist failed for dtype %s; falling back to numpy.",
                    cv_data.dtype,
                )

        backend = "numpy.histogram"
        counts, _ = np.histogram(data, bins=bins)
        return counts.astype(np.float64, copy=False), bins, backend

    def _render_histogram(self, force_full_redraw: bool = False) -> None:
        """Render histogram using blitting when possible, else fall back to full draw."""
        canvas = self.histogram.figure_canvas
        can_blit = self._blit_supported and self._histogram_artist is not None

        if (
            not can_blit
            or force_full_redraw
            or self._histogram_background is None
            or self._force_full_redraw
        ):
            canvas.draw()
            self._last_render_used_blit = False
            self._force_full_redraw = False
            if can_blit:
                self._histogram_background = canvas.copy_from_bbox(self.ax.bbox)
                canvas.restore_region(self._histogram_background)
                self.ax.draw_artist(self._histogram_artist)
                canvas.blit(self.ax.bbox)
            return

        canvas.restore_region(self._histogram_background)
        self.ax.draw_artist(self._histogram_artist)
        canvas.blit(self.ax.bbox)
        self._last_render_used_blit = True

    def _invalidate_blit_cache(self) -> None:
        """Clear cached background so the next render uses a full draw."""
        self._histogram_background = None
        self._force_full_redraw = True

    def _on_histogram_draw(self, event: Any) -> None:
        """Refresh cached background after full draw events."""
        if not self._blit_supported:
            return
        if (
            event is None
            or getattr(event, "canvas", None) is self.histogram.figure_canvas
        ):
            try:
                self._histogram_background = (
                    self.histogram.figure_canvas.copy_from_bbox(self.ax.bbox)
                )
            except Exception:
                self._histogram_background = None

    @staticmethod
    def _limits_need_update(
        current: Optional[tuple[float, float]],
        target: tuple[float, float],
        rel_tol: float,
        abs_tol: float,
    ) -> bool:
        """Return True when axis limits changed more than tolerance."""
        if current is None:
            return True
        lower_changed = abs(current[0] - target[0]) > max(
            abs_tol, rel_tol * max(1.0, abs(current[0]), abs(target[0]))
        )
        upper_changed = abs(current[1] - target[1]) > max(
            abs_tol, rel_tol * max(1.0, abs(current[1]), abs(target[1]))
        )
        return lower_changed or upper_changed
