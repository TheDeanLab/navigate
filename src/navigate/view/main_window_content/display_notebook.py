# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
from tkinter import ttk, Grid
import logging
from typing import Iterable, Dict, Any

# Third Party Imports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Local Imports
from navigate.view.custom_widgets.DockableNotebook import DockableNotebook
from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from navigate.view.custom_widgets.common import CommonMethods

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


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
        self.grid(row=0, column=0)

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

        #: Bool: The popup flag.
        self.is_popup = False

        #: Bool: The docked flag.
        self.is_docked = True

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        #: ttk.Frame: The frame that will hold the camera image.
        self.cam_image = ttk.Frame(self)
        self.cam_image.grid(row=0, column=0, rowspan=3, sticky=tk.NSEW)

        #: bool: The popup flag.
        self.is_popup = False

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
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5)

        #: matplotlib.figure.Figure: The figure that will hold the camera image.
        self.matplotlib_figure = Figure(figsize=[6, 6], tight_layout=True)

        #:  FigureCanvasTkAgg: The canvas that will hold the camera image.
        self.matplotlib_canvas = FigureCanvasTkAgg(self.matplotlib_figure, self.canvas)

        #: IntensityFrame: The frame that will hold the scale settings/palette color.
        self.lut = IntensityFrame(self)
        self.lut.grid(row=0, column=1, sticky=tk.NSEW, padx=5, pady=5)

        #: RenderFrame: The frame that will hold the live display functionality.
        self.render = MipRenderFrame(self)
        self.render.grid(row=1, column=1, sticky=tk.NSEW, padx=5, pady=5)


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

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        #: ttk.Frame: The frame that will hold the camera image.
        self.cam_image = ttk.Frame(self)
        self.cam_image.grid(row=0, column=0, rowspan=3, sticky=tk.NSEW)

        #: bool: The popup flag.
        self.is_popup = False

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
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5)

        #: matplotlib.figure.Figure: The figure that will hold the camera image.
        self.matplotlib_figure = Figure(figsize=[6, 6], tight_layout=True)

        #: FigureCanvasTkAgg: The canvas that will hold the camera image.
        self.matplotlib_canvas = FigureCanvasTkAgg(self.matplotlib_figure, self.canvas)

        #: IntensityFrame: The frame that will hold the scale settings/palette color.
        self.lut = IntensityFrame(self)
        self.lut.grid(row=0, column=1, sticky=tk.NSEW, padx=5, pady=5)

        #: tk.Scale: The slider that will hold the slice index.
        self.slider = tk.Scale(
            self,
            from_=0,
            to=200,
            tickinterval=20,
            orient=tk.HORIZONTAL,
            showvalue=0,
            label="Slice",
        )
        self.slider.configure(state="disabled")
        self.slider.grid(row=3, column=0, sticky=tk.NSEW, padx=5, pady=5)
        self.slider.grid_remove()

        #: HistogramFrame: The frame that will hold the histogram.
        self.histogram = HistogramFrame(self)
        self.histogram.grid(row=4, column=0, sticky=tk.NSEW, padx=5, pady=5)

        #: MetricsFrame: The frame that will hold the camera selection and counts.
        self.image_metrics = MetricsFrame(self)
        self.image_metrics.grid(row=1, column=1, sticky=tk.NSEW, padx=5, pady=5)

        #: RenderFrame: The frame that will hold the live display functionality.
        self.live_frame = RenderFrame(self)
        self.live_frame.grid(row=2, column=1, sticky=tk.NSEW, padx=5, pady=5)


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

        #: ttk.Frame: The frame for the histogram.
        self.frame = ttk.Frame(self)
        self.frame.grid(row=4, column=0, sticky=tk.NSEW, padx=5, pady=5)

        #: tk.Canvas: The canvas for the histogram.
        self.canvas = tk.Canvas(self.frame, width=512, height=512 // 6)
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5)

        #: matplotlib.figure.Figure: The figure for the histogram.
        self.figure = Figure(figsize=(3, 1))

        #: FigureCanvasTkAgg: The canvas for the histogram.
        self.figure_canvas = FigureCanvasTkAgg(self.figure, self.frame)
        self.figure_canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)


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

        # Formatting
        Grid.columnconfigure(self, "all", weight=1)
        Grid.rowconfigure(self, "all", weight=1)

        #: tk.StringVar: The variable that holds the live display functionality.
        self.live_var = tk.StringVar()

        #: ttk.Combobox: The combobox that holds the live display functionality.
        self.live = ttk.Combobox(self, textvariable=self.live_var, width=6)
        self.live["values"] = ("Live", "Slice")
        self.live.set("Live")
        self.live.grid(row=0, column=0)
        self.live.state(["!disabled", "readonly"])

        self.channel_var = tk.StringVar()
        self.channel = ttk.Combobox(self, textvariable=self.channel_var, width=6)
        self.channel["values"] = "CH1"
        self.channel.set("CH1")
        self.channel.grid(row=1, column=0)
        self.channel.state(["disabled", "readonly"])


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

        # Formatting
        Grid.columnconfigure(self, "all", weight=1)
        Grid.rowconfigure(self, "all", weight=1)

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
        self.inputs["perspective"].grid(row=0, column=0, sticky=tk.EW, padx=3, pady=3)
        self.inputs["channel"].grid(row=1, column=0, sticky=tk.EW, padx=3, pady=3)
        self.columnconfigure(0, weight=1)


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

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

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
        self.waveform_settings.grid(row=1, column=0, sticky=tk.NSEW, padx=5, pady=5)


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

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

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

        self.inputs["sample_rate"].grid(row=0, column=0, sticky=tk.NSEW, padx=3, pady=3)

        self.inputs["waveform_template"] = LabelInput(
            parent=self,
            label="Waveform Template",
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            input_args={"width": 20},
        )
        self.inputs["waveform_template"].grid(
            row=0, column=1, sticky=tk.NSEW, padx=3, pady=3
        )


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
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        #: dict: The dictionary that holds the widgets.
        self.inputs = {}

        #: list: The list of labels for the widgets.
        self.labels = ["Frames to Avg", "Image Max Counts", "Channel"]

        #: list: The list of names for the widgets.
        self.names = ["Frames", "Image", "Channel"]

        # Loop for widgets
        for i in range(len(self.labels)):
            if i == 0:
                self.inputs[self.names[i]] = LabelInput(
                    parent=self,
                    label=self.labels[i],
                    input_class=ttk.Spinbox,
                    input_var=tk.IntVar(),
                    input_args={"from_": 1, "to": 32, "increment": 1, "width": 5},
                    label_pos="top",
                )
                self.inputs[self.names[i]].grid(
                    row=i, column=0, sticky=tk.NSEW, padx=5, pady=3
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
                    row=i, column=0, sticky=tk.NSEW, padx=5, pady=3
                )
                self.inputs[self.names[i]].configure(width=5)


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

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        #: dict: The dictionary that holds the widgets.
        self.inputs = {}

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
        self.color = tk.StringVar()
        for i in range(len(self.color_labels)):
            self.inputs[self.color_labels[i]] = LabelInput(
                parent=self,
                label=self.color_labels[i],
                input_class=ttk.Radiobutton,
                input_var=self.color,
                input_args={"value": self.color_values[i]},
            )
            self.inputs[self.color_labels[i]].grid(
                row=i, column=0, sticky=tk.NSEW, pady=3
            )

        #: tk.BooleanVar: The variable that holds the flip xy flag.
        self.transpose = tk.BooleanVar()

        #: str: The name of the flip xy flag.
        self.trans = "Flip XY"
        self.inputs[self.trans] = LabelInput(
            parent=self,
            label=self.trans,
            input_class=ttk.Checkbutton,
            input_var=self.transpose,
        )
        self.inputs[self.trans].grid(
            row=len(self.color_labels), column=0, sticky=tk.NSEW, pady=3
        )

        #: tk.BooleanVar: The variable that holds the autoscale flag.
        self.autoscale = tk.BooleanVar()

        #: str: The name of the autoscale flag.
        self.auto = "Autoscale"

        #: list: The list of min and max counts.
        self.minmax = ["Min Counts", "Max Counts"]

        #: list: The list of min and max names.
        self.minmax_names = ["Min", "Max"]
        self.inputs[self.auto] = LabelInput(
            parent=self,
            label=self.auto,
            input_class=ttk.Checkbutton,
            input_var=self.autoscale,
        )
        self.inputs[self.auto].grid(
            row=len(self.color_labels) + 1, column=0, sticky=tk.NSEW, pady=3
        )

        # Max and Min Counts
        for i in range(len(self.minmax)):
            self.inputs[self.minmax_names[i]] = LabelInput(
                parent=self,
                label=self.minmax[i],
                input_class=ttk.Spinbox,
                input_var=tk.IntVar(),
                input_args={"from_": 1, "to": 2**16 - 1, "increment": 1, "width": 5},
            )
            self.inputs[self.minmax_names[i]].grid(
                row=i + len(self.color_labels) + 2,
                column=0,
                sticky=tk.NSEW,
                padx=3,
                pady=3,
            )
