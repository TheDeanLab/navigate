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

# Standard Library Imports
import tkinter as tk
from tkinter import ttk
import logging
from typing import Callable, Iterable, Dict, Any, Optional

# Third Party Imports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Local Imports
from navigate.view.custom_widgets.DockableNotebook import DockableNotebook
from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from navigate.view.custom_widgets.validation import ValidatedSpinbox
from navigate.view.custom_widgets.common import CommonMethods, uniform_grid
from navigate.view.theme import get_theme_font, get_theme_space_px

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def _space(px: int) -> int:
    """Resolve spacing through the active GUI theme token map."""
    return get_theme_space_px(px, px)


class CameraNotebook(DockableNotebook):
    """This class is the notebook that holds the camera view and waveform settings
    tabs."""

    def __init__(
        self, frame: ttk.Frame, *args: Iterable, **kwargs: Dict[str, Any]
    ) -> None:
        """Init function for the CameraNotebook class.

        Parameters
        ----------
        frame : ttk.Frame
            The frame that will hold the notebook.
        *args : Iterable
            Variable length argument list.
        **kwargs : Dict[str, Any]
            Arbitrary keyword arguments.
        """
        # Init notebook
        DockableNotebook.__init__(self, frame, *args, **kwargs)

        # Putting notebook 2 into top right frame
        self.grid(row=0, column=0, sticky=tk.NSEW)

        #: CameraTab: The camera tab.
        self.camera_tab = CameraTab(self)

        #: MIPTab: The maximum intensity projection tab.
        self.mip_tab = MIPTab(self)

        #: WaveformTab: The waveform settings tab.
        self.waveform_tab = WaveformTab(self)

        # Set tab list
        tab_list = [self.camera_tab, self.mip_tab, self.waveform_tab]
        self.set_tablist(tab_list)
        self.add(self.camera_tab, text="Camera", sticky=tk.NSEW)
        self.add(self.mip_tab, text="MIP", sticky=tk.NSEW)
        self.add(self.waveform_tab, text="Waveforms", sticky=tk.NSEW)

        uniform_grid(self)


class MIPTab(tk.Frame):
    """MipTab class."""

    def __init__(
        self, cam_wave: CameraNotebook, *args: Iterable, **kwargs: Dict[str, Any]
    ) -> None:
        """Initialize the MIPTab class.

        Parameters
        ----------
        cam_wave : CameraNotebook
            The frame that will hold the camera tab.
        *args : Iterable
            Variable length argument list.
        **kwargs : Dict[str, Any]
            Arbitrary keyword arguments.
        """
        #  Init Frame
        tk.Frame.__init__(self, cam_wave, *args, **kwargs)

        #: int: The index of the tab.
        self.index = 1

        #: Bool: The docked flag.
        self.is_docked = True

        #: ttk.Frame: The frame that will hold the camera image.
        self.cam_image = ttk.Frame(self)
        self.cam_image.grid(row=0, column=0, rowspan=3, sticky=tk.NSEW)

        #: bool: The docked flag.
        self.is_docked = True

        #: int: The width of the canvas.
        self.canvas_width = 512

        #: int: The height of the canvas.
        self.canvas_height = 512

        #: tk.Canvas: The canvas that will hold the camera image.
        self.canvas = tk.Canvas(
            self.cam_image, width=self.canvas_width, height=self.canvas_height
        )
        outer_pad = _space(5)
        self.canvas.grid(
            row=0, column=0, sticky=tk.NSEW, padx=outer_pad, pady=outer_pad
        )

        #: matplotlib.figure.Figure: The figure that will hold the camera image.
        self.matplotlib_figure = Figure(figsize=(6.0, 6.0), tight_layout=True)

        #:  FigureCanvasTkAgg: The canvas that will hold the camera image.
        self.matplotlib_canvas = FigureCanvasTkAgg(self.matplotlib_figure, self.canvas)

        #: DisplayModeFrame: The frame that controls single-channel vs overlay display.
        self.display_mode = DisplayModeFrame(self)
        self.display_mode.grid(
            row=0, column=1, sticky=tk.NSEW, padx=outer_pad, pady=outer_pad
        )

        #: IntensityFrame: The frame that will hold the scale settings/palette color.
        self.lut = IntensityFrame(self)
        self.lut.grid(row=1, column=1, sticky=tk.NSEW, padx=outer_pad, pady=outer_pad)

        #: RenderFrame: The frame that will hold the live display functionality.
        self.render = MipRenderFrame(self)
        self.render.grid(
            row=2, column=1, sticky=tk.NSEW, padx=outer_pad, pady=outer_pad
        )

        uniform_grid(self)


class CameraTab(tk.Frame):
    """CameraTab class."""

    def __init__(
        self, cam_wave: CameraNotebook, *args: Iterable, **kwargs: Dict[str, Any]
    ) -> None:
        """Initialize the CameraTab class.

        Parameters
        ----------
        cam_wave : CameraNotebook
            The frame that will hold the camera tab.
        *args : Iterable
            Variable length argument list.
        **kwargs : Dict[str, Any]
            Arbitrary keyword arguments.
        """
        #  Init Frame
        tk.Frame.__init__(self, cam_wave, *args, **kwargs)

        #: int: The index of the tab.
        self.index = 0

        #: ttk.Frame: The frame that will hold the camera image.
        self.cam_image = ttk.Frame(self)
        self.cam_image.grid(row=0, column=0, sticky=tk.NSEW)
        self.display_setting = ttk.Frame(self)
        self.display_setting.grid(row=0, column=1, sticky=tk.NSEW)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        #: bool: The docked flag.
        self.is_docked = True

        #: int: The width of the canvas.
        self.canvas_width = 512

        #: int: The height of the canvas.
        self.canvas_height = 512

        #: tk.Canvas: The canvas that will hold the camera image.
        self.canvas = tk.Canvas(
            self.cam_image, width=self.canvas_width, height=self.canvas_height
        )
        outer_pad = _space(5)
        self.canvas.grid(
            row=0, column=0, sticky=tk.NSEW, padx=outer_pad, pady=outer_pad
        )

        #: matplotlib.figure.Figure: The figure that will hold the camera image.
        self.matplotlib_figure = Figure(figsize=[6, 6], tight_layout=True)

        #: FigureCanvasTkAgg: The canvas that will hold the camera image.
        self.matplotlib_canvas = FigureCanvasTkAgg(self.matplotlib_figure, self.canvas)

        #: tk.Scale: The slider that will hold the slice index.
        self.slider = tk.Scale(
            self.cam_image,
            from_=0,
            to=200,
            tickinterval=20,
            orient=tk.HORIZONTAL,
            showvalue=0,
            label="Slice",
        )
        self.slider.configure(state="disabled", font=get_theme_font("caption"))
        self.slider.grid(
            row=1, column=0, sticky=tk.NSEW, padx=outer_pad, pady=outer_pad
        )
        self.slider.grid_remove()

        #: HistogramFrame: The frame that will hold the histogram.
        self.histogram = HistogramFrame(self)
        self.histogram.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky=tk.NSEW,
            padx=outer_pad,
            pady=outer_pad,
        )

        #: IntensityFrame: The frame that will hold the scale settings/palette color.
        self.display_mode = DisplayModeFrame(self.display_setting)
        self.display_mode.grid(
            row=0, column=1, sticky=tk.NSEW, padx=outer_pad, pady=outer_pad
        )

        #: IntensityFrame: The frame that will hold the scale settings/palette color.
        self.lut = IntensityFrame(self.display_setting)
        self.lut.grid(row=1, column=1, sticky=tk.NSEW, padx=outer_pad, pady=outer_pad)

        #: MetricsFrame: The frame that will hold the camera selection and counts.
        self.image_metrics = MetricsFrame(self.display_setting)
        self.image_metrics.grid(
            row=2, column=1, sticky=tk.NSEW, padx=outer_pad, pady=outer_pad
        )

        #: RenderFrame: The frame that will hold the live display functionality.
        self.live_frame = RenderFrame(self.display_setting)
        self.live_frame.grid(
            row=3, column=1, sticky=tk.NSEW, padx=outer_pad, pady=outer_pad
        )


class HistogramFrame(ttk.Labelframe):
    """This class is the frame that holds the histogram."""

    def __init__(
        self, camera_tab: CameraTab, *args: Iterable, **kwargs: Dict[str, Any]
    ) -> None:
        """Initialize the HistogramFrame class.

        Parameters
        ----------
        camera_tab : CameraTab
            The frame that will hold the histogram.
        *args : Iterable
            Variable length argument list.
        **kwargs : dict
            Arbitrary keyword arguments.
        """

        text_label = "Intensity Histogram"
        ttk.Labelframe.__init__(self, camera_tab, text=text_label, *args, **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        #: ttk.Frame: The frame for the histogram.
        self.frame = ttk.Frame(self)
        self.frame.grid(
            row=0,
            column=0,
            sticky=tk.NSEW,
            padx=_space(0),
            pady=_space(0),
        )
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        #: matplotlib.figure.Figure: The figure for the histogram.
        self.figure = Figure(figsize=(1, 1))

        #: FigureCanvasTkAgg: The canvas for the histogram.
        self.figure_canvas = FigureCanvasTkAgg(self.figure, self.frame)
        self.figure_canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)
        self._last_resize_pixels = (0, 0)
        self.frame.bind("<Configure>", self._resize_figure_to_frame)

    def _resize_figure_to_frame(self, event: tk.Event) -> None:
        """Resize the embedded Matplotlib figure to fill the frame area."""
        width = int(getattr(event, "width", 0))
        height = int(getattr(event, "height", 0))
        if width <= 1 or height <= 1:
            return
        if self._last_resize_pixels == (width, height):
            return

        self._last_resize_pixels = (width, height)
        dpi = float(self.figure.get_dpi()) or 100.0
        self.figure.set_size_inches(width / dpi, height / dpi, forward=False)
        self.figure_canvas.draw_idle()


class DisplayModeFrame(ttk.Labelframe, CommonMethods):
    """Display mode controls for single-channel or overlay rendering."""

    def __init__(
        self, camera_tab: CameraTab, *args: Iterable, **kwargs: Dict[str, Any]
    ) -> None:
        text_label = "Display Mode"
        ttk.Labelframe.__init__(self, camera_tab, text=text_label, *args, **kwargs)

        self.inputs = {
            "mode": LabelInput(
                parent=self,
                label="Mode",
                input_class=ttk.Combobox,
                input_var=tk.StringVar(),
                input_args={"width": 9},
            )
        }
        self.inputs["mode"].widget["values"] = ("Single", "Overlay")
        self.inputs["mode"].set("Single")
        self.inputs["mode"].widget.state(["!disabled", "readonly"])
        compact_pad = _space(3)
        self.inputs["mode"].grid(
            row=0, column=0, sticky=tk.NSEW, padx=compact_pad, pady=compact_pad
        )

        uniform_grid(self)


class RenderFrame(ttk.Labelframe):
    """This class is the frame that holds the live display functionality."""

    def __init__(
        self, camera_tab: CameraTab, *args: Iterable, **kwargs: Dict[str, Any]
    ) -> None:
        """Initialize the RenderFrame class.

        Parameters
        ----------
        camera_tab : CameraTab
            The frame that will hold the live display functionality.
        *args : Iterable
            Variable length argument list.
        **kwargs : Dict[str, Any]
            Arbitrary keyword arguments.
        """
        # Init Frame
        text_label = "Image Display"
        ttk.Labelframe.__init__(self, camera_tab, text=text_label, *args, **kwargs)

        #: tk.StringVar: The variable that holds the live display functionality.
        self.live_var = tk.StringVar()

        #: ttk.Combobox: The combobox that holds the live display functionality.
        self.live = ttk.Combobox(self, textvariable=self.live_var, width=6)
        self.live["values"] = ("Live", "Slice")
        self.live.set("Live")
        self.live.grid(row=0, column=0, sticky=tk.W)
        self.live.state(["!disabled", "readonly"])

        self.channel_var = tk.StringVar()
        self.channel = ttk.Combobox(self, textvariable=self.channel_var, width=6)
        self.channel["values"] = "CH1"
        self.channel.set("CH1")
        self.channel.grid(row=1, column=0, sticky=tk.W)
        self.channel.state(["disabled", "readonly"])

        uniform_grid(self)


class MipRenderFrame(ttk.Labelframe, CommonMethods):
    """This class is the frame that holds the live display functionality."""

    def __init__(
        self, camera_tab: CameraTab, *args: Iterable, **kwargs: Dict[str, Any]
    ) -> None:
        """Initialize the MipRenderFrame class.

        Parameters
        ----------
        camera_tab : CameraTab
            The frame that will hold the MIP display functionality.
        *args : Iterable
            Variable length argument list.
        **kwargs : Dict[str, Any]
            Arbitrary keyword arguments.
        """
        # Init Frame
        text_label = "Image Display"
        ttk.Labelframe.__init__(self, camera_tab, text=text_label, *args, **kwargs)

        # Label Strings
        perspective = f"{'Perspective':<11}"
        channel = f"{'Channel':>13}"

        #: dict: The dictionary that holds the widgets.
        self.inputs = {
            "perspective": LabelInput(
                parent=self,
                label=perspective,
                input_class=ttk.Combobox,
                input_var=tk.StringVar(),
                input_args={"width": 5},
            ),
            "channel": LabelInput(
                parent=self,
                label=channel,
                input_class=ttk.Combobox,
                input_var=tk.StringVar(),
                input_args={"width": 5},
            ),
        }
        self.inputs["perspective"].widget.state(["!disabled", "readonly"])
        self.inputs["channel"].widget.state(["!disabled", "readonly"])
        compact_pad = _space(3)
        self.inputs["perspective"].grid(
            row=0, column=0, sticky=tk.EW, padx=compact_pad, pady=compact_pad
        )
        self.inputs["channel"].grid(
            row=1, column=0, sticky=tk.EW, padx=compact_pad, pady=compact_pad
        )
        self.columnconfigure(0, weight=1)

        uniform_grid(self)


class WaveformTab(tk.Frame):
    """This class is the frame that holds the waveform tab."""

    def __init__(
        self, camera_tab: CameraTab, *args: Iterable, **kwargs: Dict[str, Any]
    ) -> None:
        """Initialize the WaveformTab class.

        Parameters
        ----------
        camera_tab : CameraTab
            The frame that will hold the waveform tab.
        *args : Iterable
            Variable length argument list.
        **kwargs : Dict[str, Any]
            Arbitrary keyword arguments.

        """
        # Init Frame
        tk.Frame.__init__(self, camera_tab, *args, **kwargs)

        #: int: The index of the tab.
        self.index = 2

        #: bool: The popup flag.
        self.is_docked = True

        #: ttk.Frame: The frame that will hold the waveform plots.
        self.waveform_plots = ttk.Frame(self)
        self.waveform_plots.grid(row=0, column=0, sticky=tk.NSEW)

        #: matplotlib.figure.Figure: The figure that will hold the waveform plots.
        self.fig = Figure(figsize=(6, 6), dpi=100)

        #: FigureCanvasTkAgg: The canvas that will hold the waveform plots.
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.waveform_plots)
        self.canvas.draw()

        #: WaveformSettingsFrame: The frame that will hold the waveform settings.
        self.waveform_settings = WaveformSettingsFrame(self)
        outer_pad = _space(5)
        self.waveform_settings.grid(
            row=1, column=0, sticky=tk.NSEW, padx=outer_pad, pady=outer_pad
        )

        uniform_grid(self)


class WaveformSettingsFrame(ttk.Labelframe, CommonMethods):
    """This class is the frame that holds the waveform settings."""

    def __init__(
        self, waveform_tab: WaveformTab, *args: Iterable, **kwargs: Dict[str, Any]
    ) -> None:
        """Initialize the WaveformSettingsFrame class.

        Parameters
        ----------
        waveform_tab : WaveformTab
            The frame that will hold the waveform settings.
        *args : Iterable
            Variable length argument list.
        **kwargs : Dict[str, Any]
            Arbitrary keyword arguments.
        """
        # Init Frame
        text_label = "Settings"
        ttk.Labelframe.__init__(self, waveform_tab, text=text_label, *args, **kwargs)

        #: dict: The dictionary that holds the widgets.
        self.inputs = {
            "sample_rate": LabelInput(
                parent=self,
                label="Sample rate",
                input_class=ttk.Spinbox,
                input_var=tk.IntVar(),
                input_args={"from_": 1, "to": 2**16 - 1, "increment": 1, "width": 5},
            )
        }

        compact_pad = _space(3)
        self.inputs["sample_rate"].grid(
            row=0, column=0, sticky=tk.NSEW, padx=compact_pad, pady=compact_pad
        )

        self.inputs["waveform_template"] = LabelInput(
            parent=self,
            label="Waveform Template",
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            input_args={"width": 20},
        )
        self.inputs["waveform_template"].grid(
            row=0, column=1, sticky=tk.NSEW, padx=compact_pad, pady=compact_pad
        )

        uniform_grid(self)


class MetricsFrame(ttk.Labelframe, CommonMethods):
    """This class is the frame that holds the image metrics."""

    def __init__(
        self, camera_tab: CameraTab, *args: Iterable, **kwargs: Dict[str, Any]
    ) -> None:
        """Initialize the MetricsFrame class.

        Parameters
        ----------
        camera_tab : CameraTab
            The frame that will hold the image metrics.
        *args : Iterable
            Variable length argument list.
        **kwargs : Dict[str, Any]
            Arbitrary keyword arguments.
        """
        text_label = "Image Metrics"
        ttk.Labelframe.__init__(self, camera_tab, text=text_label, *args, **kwargs)

        #: dict: The dictionary that holds the widgets.
        self.inputs = {}

        #: list: The list of labels for the widgets.
        self.labels = ["Frames to Avg", "Image Max Counts", "Channel"]

        #: list: The list of names for the widgets.
        self.names = ["Frames", "Image", "Channel"]

        # Loop for widgets
        outer_pad = _space(5)
        compact_pad = _space(3)
        for i in range(len(self.labels)):
            if i == 0:
                self.inputs[self.names[i]] = LabelInput(
                    parent=self,
                    label=self.labels[i],
                    input_class=ValidatedSpinbox,
                    input_var=tk.IntVar(),
                    input_args={"from_": 1, "to": 32, "increment": 1, "width": 5},
                    label_pos="top",
                )
                self.inputs[self.names[i]].grid(
                    row=i,
                    column=0,
                    sticky=tk.NSEW,
                    padx=outer_pad,
                    pady=compact_pad,
                )
            if i > 0:
                self.inputs[self.names[i]] = LabelInput(
                    parent=self,
                    label=self.labels[i],
                    input_class=ttk.Entry,
                    input_var=tk.IntVar(),
                    input_args={"width": 5, "state": "disabled"},
                    label_pos="top",
                )
                self.inputs[self.names[i]].grid(
                    row=i,
                    column=0,
                    sticky=tk.NSEW,
                    padx=outer_pad,
                    pady=compact_pad,
                )
                self.inputs[self.names[i]].configure(width=5)

        uniform_grid(self)


class IntensityFrame(ttk.Labelframe, CommonMethods):
    """This class is the frame that holds the intensity controls."""

    def __init__(
        self, camera_tab: CameraTab, *args: Iterable, **kwargs: Dict[str, Any]
    ) -> None:
        """Initialize the IntensityFrame class.

         Parameters
        ----------
        camera_tab : CameraTab
            The frame that will hold the intensity controls.
        *args : tuple
            Variable length argument list.
        **kwargs : dict
            Arbitrary keyword arguments.
        """
        # Init Frame
        text_label = "LUT"
        ttk.Labelframe.__init__(self, camera_tab, text=text_label, *args, **kwargs)

        #: dict: The dictionary that holds the single-channel widgets.
        self.inputs: Dict[str, Any] = {}
        #: dict: Channel-specific compact control states keyed by channel name.
        self._multichannel_channel_states: Dict[str, Dict[str, Any]] = {}
        #: Optional[Callable[[str, str], None]]: Callback for per-channel control changes.
        self._multichannel_on_change: Optional[Callable[[str, str], None]] = None
        #: bool: Guard to prevent recursive callbacks while synchronizing control values.
        self._multichannel_syncing = False
        #: bool: Whether channel selector should expose concrete channels (Overlay mode).
        self._multichannel_overlay_mode = False
        #: list[str]: Active acquisition channels for compact controls.
        self._multichannel_channels: list[str] = []
        #: str: Label used for the disabled aggregate selector in single mode.
        self._all_channels_label = "All"
        self._active_multichannel_channel = tk.StringVar()
        self._active_multichannel_lut = tk.StringVar()
        self._active_multichannel_visible = tk.BooleanVar(value=True)
        self._active_multichannel_autoscale = tk.BooleanVar(value=True)
        self._active_multichannel_min = tk.IntVar(value=0)
        self._active_multichannel_max = tk.IntVar(value=2**16 - 1)
        self._active_multichannel_alpha = tk.DoubleVar(value=100.0)
        self._active_multichannel_gamma = tk.DoubleVar(value=1.0)
        dense_pad = _space(2)
        compact_pad = _space(3)

        self.single_channel_frame = ttk.Frame(self)
        self.single_channel_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.multichannel_frame = ttk.Frame(self)
        self.multichannel_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.multichannel_frame.grid_remove()

        ttk.Label(self.multichannel_frame, text="Channel").grid(
            row=0, column=0, sticky=tk.W, padx=dense_pad, pady=dense_pad
        )
        self._multichannel_channel_widget = ttk.Combobox(
            self.multichannel_frame,
            textvariable=self._active_multichannel_channel,
            width=9,
            state="disabled",
        )
        self._multichannel_channel_widget.grid(
            row=0, column=1, sticky=tk.EW, padx=dense_pad, pady=dense_pad
        )

        ttk.Label(self.multichannel_frame, text="LUT").grid(
            row=1, column=0, sticky=tk.W, padx=dense_pad, pady=dense_pad
        )
        self._multichannel_lut_widget = ttk.Combobox(
            self.multichannel_frame,
            textvariable=self._active_multichannel_lut,
            width=9,
            state="readonly",
            values=self.multichannel_color_labels,
        )
        self._multichannel_lut_widget.grid(
            row=1, column=1, sticky=tk.EW, padx=dense_pad, pady=dense_pad
        )

        ttk.Label(self.multichannel_frame, text="Visible").grid(
            row=2, column=0, sticky=tk.W, padx=dense_pad, pady=dense_pad
        )
        self._multichannel_visible_widget = ttk.Checkbutton(
            self.multichannel_frame,
            variable=self._active_multichannel_visible,
        )
        self._multichannel_visible_widget.grid(
            row=2, column=1, sticky=tk.W, padx=dense_pad, pady=dense_pad
        )

        ttk.Label(self.multichannel_frame, text="Alpha").grid(
            row=3, column=0, sticky=tk.W, padx=dense_pad, pady=dense_pad
        )
        self._multichannel_alpha_widget = ttk.Scale(
            self.multichannel_frame,
            variable=self._active_multichannel_alpha,
            from_=0.0,
            to=100.0,
            orient=tk.HORIZONTAL,
        )
        self._multichannel_alpha_widget.grid(
            row=3, column=1, sticky=tk.EW, padx=dense_pad, pady=dense_pad
        )

        ttk.Label(self.multichannel_frame, text="Gamma").grid(
            row=4, column=0, sticky=tk.W, padx=dense_pad, pady=dense_pad
        )
        self._multichannel_gamma_widget = ttk.Spinbox(
            self.multichannel_frame,
            textvariable=self._active_multichannel_gamma,
            from_=0.0,
            to=2.0,
            increment=0.01,
            width=9,
        )
        self._multichannel_gamma_widget.grid(
            row=4, column=1, sticky=tk.EW, padx=dense_pad, pady=dense_pad
        )

        ttk.Label(self.multichannel_frame, text="Autoscale").grid(
            row=5, column=0, sticky=tk.W, padx=dense_pad, pady=dense_pad
        )
        self._multichannel_autoscale_widget = ttk.Checkbutton(
            self.multichannel_frame,
            variable=self._active_multichannel_autoscale,
        )
        self._multichannel_autoscale_widget.grid(
            row=5, column=1, sticky=tk.W, padx=dense_pad, pady=dense_pad
        )

        ttk.Label(self.multichannel_frame, text="Min Counts").grid(
            row=6, column=0, sticky=tk.W, padx=dense_pad, pady=dense_pad
        )
        self._multichannel_min_widget = ttk.Spinbox(
            self.multichannel_frame,
            textvariable=self._active_multichannel_min,
            from_=0,
            to=2**16 - 1,
            increment=1,
            width=9,
        )
        self._multichannel_min_widget.grid(
            row=6, column=1, sticky=tk.EW, padx=dense_pad, pady=dense_pad
        )

        ttk.Label(self.multichannel_frame, text="Max Counts").grid(
            row=7, column=0, sticky=tk.W, padx=dense_pad, pady=dense_pad
        )
        self._multichannel_max_widget = ttk.Spinbox(
            self.multichannel_frame,
            textvariable=self._active_multichannel_max,
            from_=0,
            to=2**16 - 1,
            increment=1,
            width=9,
        )
        self._multichannel_max_widget.grid(
            row=7, column=1, sticky=tk.EW, padx=dense_pad, pady=dense_pad
        )

        self._multichannel_channel_widget.bind(
            "<<ComboboxSelected>>",
            self._on_multichannel_channel_selected,
        )
        self._multichannel_lut_widget.bind(
            "<<ComboboxSelected>>",
            lambda *_: self._on_multichannel_value_changed("lut"),
        )
        self._active_multichannel_visible.trace_add(
            "write", lambda *_: self._on_multichannel_value_changed("visible")
        )
        self._active_multichannel_alpha.trace_add(
            "write", lambda *_: self._on_multichannel_value_changed("alpha")
        )
        self._active_multichannel_gamma.trace_add(
            "write", lambda *_: self._on_multichannel_value_changed("gamma")
        )
        self._active_multichannel_autoscale.trace_add(
            "write", lambda *_: self._on_multichannel_value_changed("autoscale")
        )
        self._active_multichannel_min.trace_add(
            "write", lambda *_: self._on_multichannel_value_changed("min")
        )
        self._active_multichannel_max.trace_add(
            "write", lambda *_: self._on_multichannel_value_changed("max")
        )

        #: list: The list of LUTs for the image display.
        self.color_labels = [
            "Gray",
            "Gradient",
            "Rainbow",
            "SNR",
        ]

        #: list: The list of maplotlib LUT names.
        self.color_values = [
            "gist_gray",
            "plasma",
            "afmhot",
            "RdBu_r",
        ]

        #: tk.StringVar: The variable that holds the LUT.
        row = 0
        self.color = tk.StringVar()
        for i in range(len(self.color_labels)):
            self.inputs[self.color_labels[i]] = LabelInput(
                parent=self.single_channel_frame,
                label=self.color_labels[i],
                input_class=ttk.Radiobutton,
                input_var=self.color,
                input_args={"value": self.color_values[i]},
            )
            self.inputs[self.color_labels[i]].grid(
                row=row, column=0, sticky=tk.W, pady=compact_pad
            )
            row += 1

        #: tk.BooleanVar: The variable that holds the flip xy flag.
        self.transpose = tk.BooleanVar()

        #: str: The name of the flip xy flag.
        self.trans = "Flip XY"
        self.inputs[self.trans] = LabelInput(
            parent=self.single_channel_frame,
            label=self.trans,
            input_class=ttk.Checkbutton,
            input_var=self.transpose,
        )
        self.inputs[self.trans].grid(row=row, column=0, sticky=tk.W, pady=compact_pad)
        row += 1

        #: tk.BooleanVar: The variable that holds the autoscale flag.
        self.autoscale = tk.BooleanVar()

        #: str: The name of the autoscale flag.
        self.auto = "Autoscale"

        #: list: The list of min and max counts.
        self.minmax = ["Min Counts", "Max Counts"]

        #: list: The list of min and max names.
        self.minmax_names = ["Min", "Max"]
        self.inputs[self.auto] = LabelInput(
            parent=self.single_channel_frame,
            label=self.auto,
            input_class=ttk.Checkbutton,
            input_var=self.autoscale,
        )
        self.inputs[self.auto].grid(row=row, column=0, sticky=tk.W, pady=compact_pad)
        row += 1

        # Max and Min Counts
        for i in range(len(self.minmax)):
            self.inputs[self.minmax_names[i]] = LabelInput(
                parent=self.single_channel_frame,
                label=self.minmax[i],
                input_class=ttk.Spinbox,
                input_var=tk.IntVar(),
                input_args={"from_": 1, "to": 2**16 - 1, "increment": 1, "width": 5},
            )
            self.inputs[self.minmax_names[i]].grid(
                row=row,
                column=0,
                sticky=tk.W,
                padx=compact_pad,
                pady=compact_pad,
            )
            row += 1

        uniform_grid(self.single_channel_frame)
        uniform_grid(self.multichannel_frame)
        uniform_grid(self)
        # Default to the compact LUT editor from startup, before acquisition begins.
        self.set_multichannel_controls_visible(True)

    @property
    def multichannel_color_labels(self):
        """Standard ImageJ-like colors for multichannel overlays."""
        return (
            "Green",
            "Red",
            "Magenta",
            "Cyan",
            "Yellow",
            "Blue",
            "Orange",
            "Gray",
        )

    def set_multichannel_controls_visible(self, visible: bool) -> None:
        """Toggle between single-channel and multichannel control groups."""
        if visible:
            self.single_channel_frame.grid_remove()
            self.multichannel_frame.grid()
        else:
            self.multichannel_frame.grid_remove()
            self.single_channel_frame.grid()

    def configure_multichannel_controls(
        self,
        channels: Iterable[str],
        default_luts: Iterable[str],
        on_change: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        """Configure compact per-channel controls for multichannel display."""
        channels = list(channels)
        default_luts = list(default_luts)
        self._multichannel_channels = channels
        self._multichannel_on_change = on_change
        if len(channels) == 0:
            self._multichannel_channel_widget["values"] = ()
            self._active_multichannel_channel.set("")
            self._multichannel_channel_widget.configure(state="disabled")
            return

        self._multichannel_syncing = True
        try:
            for index, channel in enumerate(channels):
                defaults = {
                    "lut_name": (
                        default_luts[index]
                        if index < len(default_luts)
                        else self.multichannel_color_labels[
                            index % len(self.multichannel_color_labels)
                        ]
                    ),
                    "autoscale": True,
                    "min_counts": 0.0,
                    "max_counts": float(2**16 - 1),
                    "visible": True,
                    "alpha": 1.0,
                    "gamma": 1.0,
                }
                cached = self._multichannel_channel_states.get(channel, {})
                merged = defaults.copy()
                merged.update(cached)
                self._multichannel_channel_states[channel] = merged
        finally:
            self._multichannel_syncing = False

        self.set_multichannel_channel_selector_mode(
            overlay_mode=self._multichannel_overlay_mode,
            channels=channels,
        )

    def set_multichannel_channel_selector_mode(
        self,
        overlay_mode: bool,
        channels: Optional[Iterable[str]] = None,
    ) -> None:
        """Configure channel selector behavior for single vs overlay display mode.

        Parameters
        ----------
        overlay_mode : bool
            When True, the selector is enabled and channel names are listed. When
            False, the selector is disabled and set to ``"All"``.
        channels : Optional[Iterable[str]]
            Optional explicit channel list. If None, uses the currently cached list.
        """
        if channels is not None:
            self._multichannel_channels = list(channels)
        else:
            self._multichannel_channels = list(self._multichannel_channels)
        self._multichannel_overlay_mode = bool(overlay_mode)

        if len(self._multichannel_channels) == 0:
            self._multichannel_channel_widget["values"] = ()
            self._active_multichannel_channel.set("")
            self._multichannel_channel_widget.configure(state="disabled")
            return

        self._multichannel_syncing = True
        try:
            if self._multichannel_overlay_mode and len(self._multichannel_channels) > 1:
                self._multichannel_channel_widget["values"] = (
                    self._multichannel_channels
                )
                self._multichannel_channel_widget.configure(state="readonly")
                active_channel = self._active_multichannel_channel.get()
                if active_channel not in self._multichannel_channels:
                    self._active_multichannel_channel.set(
                        self._multichannel_channels[0]
                    )
            else:
                self._multichannel_channel_widget["values"] = (
                    self._all_channels_label,
                )
                self._multichannel_channel_widget.configure(state="disabled")
                self._active_multichannel_channel.set(self._all_channels_label)
        finally:
            self._multichannel_syncing = False

        self._load_active_multichannel_values()
        self._set_multichannel_minmax_state()

    def _on_multichannel_channel_selected(self, *_args) -> None:
        self._load_active_multichannel_values()
        self._notify_multichannel_change("channel")

    def _notify_multichannel_change(self, field: str) -> None:
        channel = self._active_multichannel_channel.get()
        if self._multichannel_on_change is None or not channel:
            return
        if channel == self._all_channels_label:
            for selected_channel in self._multichannel_channels:
                self._multichannel_on_change(selected_channel, field)
            return
        self._multichannel_on_change(channel, field)

    def _on_multichannel_value_changed(self, field: str) -> None:
        if self._multichannel_syncing:
            return
        self._store_active_multichannel_values()
        if field == "autoscale":
            self._set_multichannel_minmax_state()
        self._notify_multichannel_change(field)

    def _safe_get_float(self, tk_var: Any, fallback: float) -> float:
        """Read a Tk variable as float while tolerating transient invalid edits."""
        try:
            return float(tk_var.get())
        except (tk.TclError, TypeError, ValueError):
            return float(fallback)

    def _safe_get_bool(self, tk_var: Any, fallback: bool) -> bool:
        """Read a Tk variable as bool while tolerating transient invalid edits."""
        try:
            value = tk_var.get()
        except (tk.TclError, TypeError, ValueError):
            return bool(fallback)

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in ("", "none"):
                return bool(fallback)
            if normalized in ("0", "false", "off", "no"):
                return False
            if normalized in ("1", "true", "on", "yes"):
                return True
        return bool(value)

    def _safe_get_string(self, tk_var: Any, fallback: str) -> str:
        """Read a Tk variable as string while tolerating transient invalid edits."""
        try:
            return str(tk_var.get())
        except (tk.TclError, TypeError, ValueError):
            return str(fallback)

    def _store_active_multichannel_values(self) -> None:
        channel = self._safe_get_string(self._active_multichannel_channel, "")
        if not channel:
            return
        targets = (
            list(self._multichannel_channels)
            if channel == self._all_channels_label
            else [channel]
        )
        for target_channel in targets:
            state = self._multichannel_channel_states.setdefault(target_channel, {})
            lut_name = self._safe_get_string(
                self._active_multichannel_lut,
                str(state.get("lut_name", "Green")),
            ).strip()
            state["lut_name"] = (
                lut_name if lut_name else str(state.get("lut_name", "Green"))
            )
            state["autoscale"] = self._safe_get_bool(
                self._active_multichannel_autoscale,
                bool(state.get("autoscale", True)),
            )
            state["min_counts"] = self._safe_get_float(
                self._active_multichannel_min,
                float(state.get("min_counts", 0.0)),
            )
            state["max_counts"] = self._safe_get_float(
                self._active_multichannel_max,
                float(state.get("max_counts", float(2**16 - 1))),
            )
            state["visible"] = self._safe_get_bool(
                self._active_multichannel_visible,
                bool(state.get("visible", True)),
            )
            state["alpha"] = max(
                0.0,
                min(
                    1.0,
                    self._safe_get_float(
                        self._active_multichannel_alpha,
                        float(state.get("alpha", 1.0)) * 100.0,
                    )
                    / 100.0,
                ),
            )
            state["gamma"] = max(
                0.0,
                min(
                    2.0,
                    self._safe_get_float(
                        self._active_multichannel_gamma,
                        float(state.get("gamma", 1.0)),
                    ),
                ),
            )

    def _load_active_multichannel_values(self) -> None:
        channel = self._active_multichannel_channel.get()
        source_channel = channel
        if channel == self._all_channels_label and self._multichannel_channels:
            source_channel = self._multichannel_channels[0]
        state = self._multichannel_channel_states.get(source_channel, {})
        if not state:
            return
        self._multichannel_syncing = True
        try:
            self._active_multichannel_lut.set(state.get("lut_name", "Green"))
            self._active_multichannel_autoscale.set(bool(state.get("autoscale", True)))
            self._active_multichannel_min.set(int(state.get("min_counts", 0.0)))
            self._active_multichannel_max.set(
                int(state.get("max_counts", float(2**16 - 1)))
            )
            self._active_multichannel_visible.set(bool(state.get("visible", True)))
            self._active_multichannel_alpha.set(float(state.get("alpha", 1.0)) * 100.0)
            self._active_multichannel_gamma.set(
                max(0.0, min(2.0, float(state.get("gamma", 1.0))))
            )
        finally:
            self._multichannel_syncing = False
        self._set_multichannel_minmax_state()

    def _set_multichannel_minmax_state(self) -> None:
        autoscale_enabled = self._safe_get_bool(
            self._active_multichannel_autoscale,
            True,
        )
        state = "disabled" if autoscale_enabled else "normal"
        self._multichannel_min_widget["state"] = state
        self._multichannel_max_widget["state"] = state

    def get_multichannel_widgets(self) -> Dict[str, Dict[str, Any]]:
        """Return channel-mapped compact control state."""
        return self._multichannel_channel_states

    def get_multichannel_channel_state(self, channel: str) -> Dict[str, Any]:
        """Return current settings for one channel."""
        self._store_active_multichannel_values()
        state = self._multichannel_channel_states.get(channel)
        if state is None:
            return {}
        return state.copy()

    def set_multichannel_channel_state(
        self, channel: str, state: Dict[str, Any]
    ) -> None:
        """Populate controls for one channel from cached state."""
        merged = self._multichannel_channel_states.get(channel, {}).copy()
        merged.update(state)
        self._multichannel_channel_states[channel] = merged
        if channel == self._active_multichannel_channel.get():
            self._load_active_multichannel_values()

    def get_multichannel_active_channel(self) -> str:
        """Return the currently selected channel in compact multichannel controls."""
        self._store_active_multichannel_values()
        channel = self._active_multichannel_channel.get()
        if channel == self._all_channels_label and self._multichannel_channels:
            return self._multichannel_channels[0]
        return channel
