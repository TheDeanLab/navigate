# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Third Party Imports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Local Imports
from aslm.view.custom_widgets.DockableNotebook import DockableNotebook
from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class CameraNotebook(DockableNotebook):
    """This class is the notebook that holds the camera view and waveform settings tabs.

    Parameters
    ----------
    frame_top_right : tk.Frame
        The frame that will hold the notebook.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    camera_tab : CameraTab
        The camera tab.
    waveform_tab : WaveformTab
        The waveform settings tab.

    Methods
    -------
    set_tablist(tab_list)
        Sets the tab list.
    add(tab, text, sticky)
        Adds a tab to the notebook.
    """

    def __init__(self, frame_top_right, *args, **kwargs):
        # Init notebook
        DockableNotebook.__init__(self, frame_top_right, *args, **kwargs)

        # Putting notebook 2 into top right frame
        self.grid(row=0, column=0)

        # Creating the camera tab
        self.camera_tab = CameraTab(self)

        # Creating the waveform settings tab
        self.waveform_tab = WaveformTab(self)

        # Tab list
        tab_list = [self.camera_tab, self.waveform_tab]
        self.set_tablist(tab_list)

        # Adding tabs to self notebook
        self.add(self.camera_tab, text="Camera View", sticky=tk.NSEW)
        self.add(self.waveform_tab, text="Waveform Settings", sticky=tk.NSEW)


class CameraTab(tk.Frame):
    """This class is the camera tab.

    Parameters
    ----------
    cam_wave : tk.Frame
        The frame that will hold the camera tab.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    index : int
        The index of the current frame.
    cam_image : ttk.Frame
        The frame that will hold the camera image.
    canvas : tk.Canvas
        The canvas that will hold the matplotlib figure.
    matplotlib_figure : matplotlib.figure.Figure
        The matplotlib figure that will hold the camera image.
    matplotlib_canvas : matplotlib.backends.backend_tkagg.FigureCanvasTkAgg
        The matplotlib canvas that will hold the camera image.

    Methods
    -------
    None

    """

    def __init__(self, cam_wave, *args, **kwargs):
        #  Init Frame
        tk.Frame.__init__(self, cam_wave, *args, **kwargs)

        self.index = 0

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        #  Frame that will hold camera image
        self.cam_image = ttk.Frame(self)
        self.cam_image.grid(row=0, column=0, rowspan=3, sticky=tk.NSEW)

        # Frame for the Waveforms
        self.canvas_width, self.canvas_height = 512, 512
        self.canvas = tk.Canvas(
            self.cam_image, width=self.canvas_width, height=self.canvas_height
        )
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5)
        self.matplotlib_figure = Figure(figsize=[6, 6], tight_layout=True)
        self.matplotlib_canvas = FigureCanvasTkAgg(self.matplotlib_figure, self.canvas)

        #  Frame for scale settings/palette color
        self.scale_palette = IntensityFrame(self)
        self.scale_palette.grid(row=0, column=1, sticky=tk.NSEW, padx=5, pady=5)

        # Slider
        self.slider = tk.Scale(
            self,
            from_=0,
            to=200,
            tickinterval=20,
            orient=tk.HORIZONTAL,
            showvalue=0,
            label="Slice Index",
        )
        self.slider.configure(state="disabled")  # 'normal'
        self.slider.grid(row=3, column=0, sticky=tk.NSEW, padx=5, pady=5)

        #  Frame for camera selection and counts
        self.image_metrics = MetricsFrame(self)
        self.image_metrics.grid(row=1, column=1, sticky=tk.NSEW, padx=5, pady=5)

        # Frame for controlling the live display functionality.
        self.live_frame = RenderFrame(self)
        self.live_frame.grid(row=2, column=1, sticky=tk.NSEW, padx=5, pady=5)


class RenderFrame(ttk.Labelframe):
    """This class is the frame that holds the live display functionality.

    Parameters
    ----------
    cam_view : tk.Frame
        The frame that will hold the live display functionality.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    live_var : tk.StringVar
        The variable that holds the live display functionality.
    live : ttk.Combobox
        The combobox that holds the live display functionality.

    Methods
    -------
    get_variables()
        Returns the variables.
    get_widgets()
        Returns the widgets.
    """

    def __init__(self, cam_view, *args, **kwargs):

        # Init Frame
        text_label = "Image Display"
        ttk.Labelframe.__init__(self, cam_view, text=text_label, *args, **kwargs)

        # Formatting
        Grid.columnconfigure(self, "all", weight=1)
        Grid.rowconfigure(self, "all", weight=1)

        self.live_var = tk.StringVar()
        self.live = ttk.Combobox(
            self, textvariable=self.live_var, state="readonly", width=6
        )
        self.live["values"] = (
            "Live",
            "XY Slice",
            "YZ Slice",
            "ZY Slice",
            "XY MIP",
            "YZ MIP",
            "ZY MIP",
        )
        self.live.set("Live")
        self.live.grid(row=0, column=0)
        self.live.state = "readonly"

    def get_variables(self):
        """Function to get the variables.

        The key is the widget name, value is the variable associated.

        Parameters
        ----------
        None

        Returns
        -------
        variables : dict
            The dictionary that holds the variables.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get()
        return variables

    def get_widgets(self):
        """Function to get the widgets.

        The key is the widget name, value is the LabelInput class that has all the data.

        Parameters
        ----------
        None

        Returns
        -------
        self.inputs : dict
            The dictionary that holds the widgets.
        """
        return self.inputs


class WaveformTab(tk.Frame):
    """This class is the frame that holds the waveform tab.

    Parameters
    ----------
    cam_wave : tk.Frame
        The frame that will hold the waveform tab.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    index : int
        The index of the tab.
    waveform_plots : ttk.Frame
        The frame that will hold the waveform plots.
    fig : matplotlib.figure.Figure
        The figure that will hold the waveform plots.
    canvas : matplotlib.backends.backend_tkagg.FigureCanvasTkAgg
        The canvas that will hold the waveform plots.
    waveform_settings : WaveformSettingsFrame
        The frame that will hold the waveform settings.

    Methods
    -------
    None
    """

    def __init__(self, cam_wave, *args, **kwargs):
        # Init Frame
        tk.Frame.__init__(self, cam_wave, *args, **kwargs)

        self.index = 1

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        self.waveform_plots = ttk.Frame(self)
        self.waveform_plots.grid(row=0, column=0, sticky=tk.NSEW)

        self.fig = Figure(figsize=(6, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.waveform_plots)
        self.canvas.draw()

        self.waveform_settings = WaveformSettingsFrame(self)
        self.waveform_settings.grid(row=1, column=0, sticky=tk.NSEW, padx=5, pady=5)


class WaveformSettingsFrame(ttk.Labelframe):
    """This class is the frame that holds the waveform settings.

    Parameters
    ----------
    wav_view : tk.Frame
        The frame that will hold the waveform settings.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    inputs : dict
        The dictionary that holds the widgets.

    Methods
    -------
    get_variables()
        Returns the variables.
    get_widgets()
        Returns the widgets.
    """

    def __init__(self, wav_view, *args, **kwargs):
        # Init Frame
        text_label = "Settings"
        ttk.Labelframe.__init__(self, wav_view, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Dictionary for widgets
        self.inputs = {}

        self.inputs["sample_rate"] = LabelInput(
            parent=self,
            label="Sample rate",
            input_class=ttk.Spinbox,
            input_var=tk.IntVar(),
            input_args={"from_": 1, "to": 2**16 - 1, "increment": 1, "width": 5},
        )
        self.inputs["sample_rate"].grid(row=0, column=0, sticky=tk.NSEW, padx=3, pady=3)

        self.inputs["waveform_template"] = LabelInput(
            parent=self,
            label="Waveform Template",
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            input_args={"width": 20},
        )
        self.inputs["waveform_template"].grid(row=0, column=1, sticky=tk.NSEW, padx=3, pady=3)

    def get_variables(self):
        """Function to get the variables.

        Parameters
        ----------
        None

        Returns
        -------
        variables : dict
            The dictionary that holds the variables.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get()
        return variables

    def get_widgets(self):
        """Function to get the widgets.

        Parameters
        ----------
        None

        Returns
        -------
        self.inputs : dict
            The dictionary that holds the widgets.
        """
        return self.inputs


class MetricsFrame(ttk.Labelframe):
    """This class is the frame that holds the image metrics.

    Parameters
    ----------
    cam_view : tk.Frame
        The frame that will hold the image metrics.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    inputs : dict
        The dictionary that holds the widgets.
    self.labels : list
        The list of labels for the widgets.
    self.names : list
        The list of names for the widgets.

    Methods
    -------
    get_variables()
        Returns the variables.
    get_widgets()
        Returns the widgets.
    """

    def __init__(self, cam_view, *args, **kwargs):
        # Init Labelframe
        text_label = "Image Metrics"
        ttk.Labelframe.__init__(self, cam_view, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Dictionary for widgets
        self.inputs = {}

        # Labels and names
        self.labels = ["Frames to Avg", "Image Max Counts", "Channel"]
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
                    row=i, column=0, sticky=(tk.NSEW), padx=5, pady=3
                )
            if i > 0:
                self.inputs[self.names[i]] = LabelInput(
                    parent=self,
                    label=self.labels[i],
                    input_class=ttk.Entry,
                    input_var=tk.IntVar(),
                    input_args={"width": 5},
                    label_pos="top",
                )
                self.inputs[self.names[i]].grid(
                    row=i, column=0, sticky=(tk.NSEW), padx=5, pady=3
                )
                self.inputs[self.names[i]].configure(width=5)

    def get_variables(self):
        """This function returns a dictionary of all the variables that are tied to
        each  widget name.

        The key is the widget name, value is the variable associated.

        Parameters
        ----------
        None

        Returns
        -------
        variables : dict
            The dictionary that holds the variables.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get()
        return variables

    def get_widgets(self):
        """This function returns the dictionary that holds the widgets.

        The key is the widget name, value is the LabelInput class that has all the data.

        Parameters
        ----------
        None

        Returns
        -------
        self.inputs : dict
            The dictionary that holds the widgets.
        """
        return self.inputs


class IntensityFrame(ttk.Labelframe):
    """This class is the frame that holds the intensity controls.

    Parameters
    ----------
    cam_view : tk.Frame
        The frame that will hold the intensity controls.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    inputs : dict
        The dictionary that holds the widgets.
    self.labels : list
        The list of labels for the widgets.
    self.color_labels : list
        The list of human-readable names for the color maps.
    self.color_values : list
        The list of matplotlib cmap names for the color maps.
    self.transpose : bool
        The transpose flag for the image.
    self.flip : bool
        The flip flag for the image.
    self.autoscale : bool
        The autoscale flag for the image.
    self.auto : bool
        The auto flag for the image.
    self.minmax : list
        The list of human-readable names for the min/max widgets.
    self.minmax_names : list
        Labels for the min/max widgets.

    Methods
    -------
    get_variables()
        Returns the variables.
    get_widgets()
        Returns the widgets.
    """

    def __init__(self, cam_view, *args, **kwargs):
        # Init Frame
        text_label = "LUT"
        ttk.Labelframe.__init__(self, cam_view, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Dictionary for widgets
        self.inputs = {}

        # LUT Radio buttons - Gray is default
        self.color_labels = [
            "Gray",
            "Gradient",
            "Rainbow",
            "SNR",
        ]  # Human-readable names
        self.color_values = [
            "gist_gray",
            "plasma",
            "afmhot",
            "RdBu_r",
        ]  # maplotlib cmap names
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

        # Flip xy
        self.transpose = tk.BooleanVar()
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

        # Autoscale
        self.autoscale = tk.BooleanVar()
        self.auto = "Autoscale"
        self.minmax = ["Min Counts", "Max Counts"]
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

    def get_variables(self):
        """This function returns a dictionary of all the variables that are tied to
        each  widget name.

        The key is the widget name, value is the variable associated.

        Parameters
        ----------
        None

        Returns
        -------
        variables : dict
            The dictionary that holds the variables.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get()
        return variables

    def get_widgets(self):
        """This function returns the dictionary that holds the widgets.

        The key is the widget name, value is the LabelInput class that has all the data.

        Parameters
        ----------
        None

        Returns
        -------
        self.inputs : dict
            The dictionary that holds the widgets.
        """
        return self.inputs
