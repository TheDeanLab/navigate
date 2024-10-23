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


# Standard library imports
import tkinter as tk
from tkinter import ttk

# Third party imports
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Local application imports
from navigate.view.custom_widgets.popup import PopUp
from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput

import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ScrollFrame(ttk.Frame):
    """Scrollable Frame"""

    def __init__(self, parent):
        """Initialize ScrollFrame

        Parameters
        ----------
        parent : tk.Frame
            Parent frame
        """
        tk.Frame.__init__(self, parent)
        #: tk.Canvas: Canvas
        self.canvas = tk.Canvas(self, borderwidth=1)

        #: tk.Frame: Frame
        self.frame = tk.Frame(self.canvas)

        #: tk.Scrollbar: Vertical Scrollbar
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        self.canvas.configure(yscrollcommand=self.vsb.set, width=200)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="y", expand=False)
        self.canvas.create_window(
            0, 0, window=self.frame, anchor="nw", tags="self.frame"
        )
        self.frame.bind("<Configure>", self.onFrameConfigure)

    def onFrameConfigure(self, event):
        """Reset the scroll region to encompass the inner frame.

        Parameters
        ----------
        event : tk.Event
            Event
        """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


class AdaptiveOpticsPopup:
    """Adaptive Optics Popup"""

    def __init__(self, root, *args, **kwargs):
        """Initialize AdaptiveOpticsPopup

        Creating popup window with this name and size/placement, PopUp is a
        Toplevel window

        Parameters
        ----------
        root : tk.Tk
            Root window
        """
        #: PopUp: Popup
        self.popup = PopUp(
            root, "Adaptive Optics", "1100x550+320+180", top=False, transient=False
        )

        #: list: List of mode names
        self.mode_names = [
            "Vert. Tilt",
            "Horz. Tilt",
            "Defocus",
            "Vert. Asm.",
            "Oblq. Asm.",
            "Vert. Coma",
            "Horz. Coma",
            "3rd Spherical",
            "Vert. Tre.",
            "Horz. Tre.",
            "Vert. 5th Asm.",
            "Oblq. 5th Asm.",
            "Vert. 5th Coma",
            "Horz. 5th Coma",
            "5th Spherical",
            "Vert. Tetra.",
            "Oblq. Tetra.",
            "Vert. 7th Tre.",
            "Horz. 7th Tre.",
            "Vert. 7th Asm.",
            "Oblq. 7th Asm.",
            "Vert. 7th Coma",
            "Horz. 7th Coma",
            "7th Spherical",
            "Vert. Penta.",
            "Horz. Penta.",
            "Vert. 9th Tetra.",
            "Oblq. 9th Tetra.",
            "Vert. 9th Tre.",
            "Horz. 9th Tre.",
            "Vert. 9th Asm.",
            "Oblq. 9th Asm.",
        ]

        #: int: Number of modes
        self.n_modes = 32  # TODO: Don't hardcode... Get from exp file!

        content_frame = self.popup.get_frame()

        """Creating the widgets for the popup"""
        #: dict: Dictionary of all the variables
        self.inputs = {}

        #: dict: Dictionary of all the armed modes
        self.modes_armed = {}

        #: dict: Dictionary of all the mode labels
        self.mode_labels = {}

        #: ttk.Notebook: Notebook
        self.ao_notebook = ttk.Notebook(master=content_frame)
        self.ao_notebook.grid(row=0, column=2, rowspan=2)

        #: ttk.Frame: Tony Wilson Tab
        self.tab_tw = ttk.Frame(master=self.ao_notebook)
        self.ao_notebook.add(self.tab_tw, text="Tony Wilson")

        #: ttk.Frame: CNN-AO Tab
        self.tab_cnn = ttk.Frame(master=self.ao_notebook)
        self.ao_notebook.add(self.tab_cnn, text="CNN-AO")

        #: ttk.Frame: Tony Wilson Widget Frame
        tw_widget_frame = ttk.Frame(master=self.tab_tw)
        tw_widget_frame.grid(row=0, column=1)

        #: ttk.Label: Label Frames
        self.inputs["iterations"] = LabelInput(
            tw_widget_frame,
            label="Iterations:",
            label_pos="top",
            input_args={"width": 15},
        )
        self.inputs["iterations"].grid(row=0, column=1, pady=5)
        self.inputs["steps"] = LabelInput(
            tw_widget_frame, label="Steps:", label_pos="top", input_args={"width": 15}
        )
        self.inputs["steps"].grid(row=1, column=1, pady=5)
        self.inputs["amplitude"] = LabelInput(
            tw_widget_frame,
            label="Amplitude:",
            label_pos="top",
            input_args={"width": 15},
        )
        self.inputs["amplitude"].grid(row=2, column=1, pady=5)

        tw_start_from_var = tk.StringVar()
        ttk.Label(tw_widget_frame, text="Start from:").grid(row=3, column=1)
        tw_start_from_combo = ttk.Combobox(
            tw_widget_frame, textvariable=tw_start_from_var, width=20
        )
        tw_start_from_combo["values"] = ("flat", "current")
        tw_start_from_combo.state(["readonly"])
        tw_start_from_combo.grid(row=4, column=1, pady=5)
        tw_start_from_combo.current(0)
        self.inputs["from"] = {
            "button": tw_start_from_combo,
            "variable": tw_start_from_var,
        }

        tw_metric_var = tk.StringVar()
        ttk.Label(tw_widget_frame, text="Image metric:").grid(row=5, column=1)
        tw_metric_combo = ttk.Combobox(
            tw_widget_frame, textvariable=tw_metric_var, width=20
        )
        tw_metric_combo["values"] = (
            "Pixel Max",
            "Pixel Average",
            "DCT Shannon Entropy",
        )
        tw_metric_combo.state(["readonly"])
        tw_metric_combo.grid(row=6, column=1, pady=5)
        tw_metric_combo.current(0)
        self.inputs["metric"] = {"button": tw_metric_combo, "variable": tw_metric_var}

        tw_fitfunc_var = tk.StringVar()
        ttk.Label(tw_widget_frame, text="Fit func:").grid(row=7, column=1)
        tw_fitfunc_combo = ttk.Combobox(
            tw_widget_frame, textvariable=tw_fitfunc_var, width=20
        )
        tw_fitfunc_combo["values"] = (
            "poly",
            "gauss",
        )
        tw_fitfunc_combo.state(["readonly"])
        tw_fitfunc_combo.grid(row=8, column=1, pady=5)
        tw_fitfunc_combo.current(0)
        self.inputs["fitfunc"] = {
            "button": tw_fitfunc_combo,
            "variable": tw_fitfunc_var,
        }

        #: ttk.Button: Tony Wilson Button
        self.tony_wilson_button = ttk.Button(tw_widget_frame, text="RUN", width=15)
        self.tony_wilson_button.grid(row=9, column=1, pady=5)

        control_frame = ttk.Frame(content_frame)
        control_frame.grid(row=0, column=0)

        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0)

        #: ttk.Button: Set Button
        self.set_button = ttk.Button(button_frame, text="Set", width=15)
        self.set_button.grid(row=0, column=0, pady=5)

        #: ttk.Button: Flat Button
        self.flat_button = ttk.Button(button_frame, text="Flat", width=15)
        self.flat_button.grid(row=1, column=0, pady=5)

        #: ttk.Button: Zero Button
        self.zero_button = ttk.Button(button_frame, text="Zero", width=15)
        self.zero_button.grid(row=2, column=0, pady=5)

        #: ttk.Button: Clear Button
        self.clear_button = ttk.Button(button_frame, text="Clear All", width=15)
        self.clear_button.grid(row=3, column=0, pady=5)

        #: ttk.Button: Save Button
        self.save_wcs_button = ttk.Button(button_frame, text="Save WCS File", width=15)
        self.save_wcs_button.grid(row=0, column=1, pady=5)

        #: ttk.Button: Load Button
        self.from_wcs_button = ttk.Button(button_frame, text="From WCS File", width=15)
        self.from_wcs_button.grid(row=1, column=1, pady=5)

        #: ttk.Button: Select All Button
        self.select_all_modes = ttk.Button(button_frame, text="Select All", width=15)
        self.select_all_modes.grid(row=2, column=1, pady=5)

        #: ttk.Button: Deselect All Button
        self.deselect_all_modes = ttk.Button(
            button_frame, text="Deselect All", width=15
        )
        self.deselect_all_modes.grid(row=3, column=1, pady=5)

        scroll = ScrollFrame(control_frame)

        for i in range(self.n_modes):
            mode_name = self.mode_names[i]

            self.mode_labels[mode_name] = ttk.Label(
                scroll.frame, text=self.mode_names[i]
            )
            self.mode_labels[mode_name].grid(row=i, column=0)

            mode_check_var = tk.BooleanVar()
            mode_check_var.set(False)
            mode_check = ttk.Checkbutton(scroll.frame, variable=mode_check_var)
            mode_check.grid(row=i, column=1)
            self.modes_armed[mode_name] = {
                "button": mode_check,
                "variable": mode_check_var,
            }

            self.inputs[mode_name] = LabelInput(scroll.frame, input_args={"width": 10})
            self.inputs[mode_name].set(0.0)
            self.inputs[mode_name].grid(row=i, column=2)

        scroll.grid(row=1, column=0)

        save_frame = ttk.Frame(control_frame)
        save_frame.grid(row=2, column=0)

        # ttk.Checkbutton: save detailed report at the end
        save_report_var = tk.BooleanVar()
        save_report_check = ttk.Checkbutton(save_frame, variable=save_report_var)
        save_report_check.grid(row=0, column=0)
        self.inputs["save_report"] = {
            "button": save_report_check,
            "variable": save_report_var,
        }
        ttk.Label(save_frame, text="Save detailed report?").grid(row=0, column=1)

        #: ttk.Frame: Plot Frame
        self.plot_frame = ttk.Frame(master=content_frame)
        self.plot_frame.grid(row=0, column=1, rowspan=2)

        #: matplotlib.figure.Figure: Figure
        self.fig = Figure(figsize=(3, 5), dpi=100)

        #: matplotlib.axes.Axes: Mirror Image
        self.mirror_img = self.fig.add_subplot(211)

        #: matplotlib.axes.Axes: Coefficients Bar
        self.coefs_bar = self.fig.add_subplot(212)
        self.fig.tight_layout()

        canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(
            row=0, column=0, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5)
        )

        #: matplotlib.figure.Figure: Figure
        self.fig_tw = Figure(figsize=(4, 5), dpi=100)

        #: matplotlib.axes.Axes: Peaks Plot
        self.peaks_plot = self.fig_tw.add_subplot(211)

        #: matplotlib.axes.Axes: Trace Plot
        self.trace_plot = self.fig_tw.add_subplot(212)
        self.fig_tw.tight_layout()

        canvas = FigureCanvasTkAgg(self.fig_tw, master=self.tab_tw)
        canvas.draw()
        canvas.get_tk_widget().grid(
            row=0, column=0, sticky=tk.NSEW, padx=(5, 5), pady=(5, 5)
        )

        camera_var = tk.StringVar()
        #: ttk.Combobox: Camera List
        self.camera_list = ttk.Combobox(master=self.tab_cnn, textvariable=camera_var)
        # self.camera_list["values"] = ("cam_0", "cam_1")
        self.camera_list.grid(row=0, column=0, padx=10, pady=10)
        # self.camera_list.current(0)

    def onFrameConfigure(self, event):
        """Reset the scroll region to encompass the inner frame.

        Parameters
        ----------
        event : tk.Event
            Event
        """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def get_widgets(self):
        """Get widgets

        Returns
        -------
        dict
            Dictionary of widgets
        """
        return self.inputs

    def get_labels(self):
        """Get labels

        Returns
        -------
        dict
            Dictionary of labels
        """
        return self.mode_labels

    def get_modes_armed(self):
        """Get armed modes

        Returns
        -------
        dict
            Dictionary of armed modes
        """
        return self.modes_armed

    def set_widgets(self, coefs):
        """Set widgets

        Parameters
        ----------
        coefs : list
            List of coefficients
        """
        for i, c in enumerate(coefs):
            self.inputs[self.mode_names[i]].set(c)
