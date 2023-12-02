""" Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only
(subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

# Standard library imports
from tkinter import filedialog
import logging

# Third-party imports
# from matplotlib.figure import Figure
# from matplotlib.axes import Axes

# Local application imports
from aslm.controller.sub_controllers.gui_controller import GUIController

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class AdaptiveOpticsPopupController(GUIController):
    """Controller for the Adaptive Optics popup window"""

    def __init__(self, view, parent_controller):
        """Initialize the Adaptive Optics popup controller

        Parameters
        ----------
        view : AdaptiveOpticsPopupView
            The view for this controller
        parent_controller : Controller
            The parent controller for this controller
        """
        super().__init__(view, parent_controller)

        self.view.popup.protocol("WM_DELETE_WINDOW", self.view.popup.dismiss)

        self.parent_controller.configuration["experiment"]["AdaptiveOpticsParameters"][
            "HighlightedMode"
        ] = None

        #: list of dicts: list of dicts containing trace data
        self.trace_list = []

        #: dict: dictionary of widgets
        self.widgets = self.view.get_widgets()

        #: dict: dictionary of armed modes
        self.modes_armed = self.view.get_modes_armed()

        #: dict: dictionary of mode labels
        self.mode_labels = self.view.get_labels()

        # TODO: just for testing, remove later...
        #: list: list of cameras
        self.camera_list = self.view.camera_list
        self.camera_list.bind(
            "<<ComboboxSelected>>", lambda evt: self.change_camera(evt)
        )

        #: Figure: figure for mirror plot
        self.fig = self.view.fig

        #: Figure: figure for tony wilson plot
        self.fig_tw = self.view.fig_tw

        #: Figure: figure for peaks plot
        self.peaks_plot = self.view.peaks_plot

        #: Figure: figure for trace plot
        self.trace_plot = self.view.trace_plot

        #: Figure: figure for mirror image
        self.mirror_img = self.view.mirror_img

        #: Figure: figure for coefs bar
        self.coefs_bar = self.view.coefs_bar

        # Trace Events
        self.view.set_button.configure(command=self.set_mirror)
        self.view.flat_button.configure(command=self.flatten_mirror)
        self.view.zero_button.configure(command=self.zero_mirror)
        self.view.clear_button.configure(command=self.clear_all_coefs)
        self.view.save_wcs_button.configure(command=self.save_wcs_file)
        self.view.from_wcs_button.configure(command=self.set_from_wcs_file)
        self.view.select_all_modes.configure(command=self.select_all_modes)
        self.view.deselect_all_modes.configure(command=self.deselect_all_modes)
        self.view.tony_wilson_button.configure(command=self.run_tony_wilson)

        for k in self.modes_armed.keys():
            self.modes_armed[k]["button"].configure(
                command=self.update_experiment_values
            )
            self.mode_labels[k].bind(
                "<Enter>", lambda evt, mode=k: self.set_highlighted_mode(evt, mode)
            )
            self.mode_labels[k].bind(
                "<Leave>", lambda evt: evt.widget.config(background="SystemButtonFace")
            )

        self.populate_experiment_values()

    def change_camera(self, evt):
        """Change the camera to the selected camera

        Parameters
        ----------
        evt : Event
            The event that triggered this function
        """
        cam_id = evt.widget.get().split("_")[-1]
        self.parent_controller.execute("change_camera", int(cam_id))

    def set_highlighted_mode(self, evt, mode):
        """Set the highlighted mode

        Parameters
        ----------
        evt : Event
            The event that triggered this function
        mode : str
            The mode to highlight
        """
        evt.widget.config(background="red")
        self.parent_controller.configuration["experiment"]["AdaptiveOpticsParameters"][
            "HighlightedMode"
        ] = mode
        self.plot_tw_trace()

    def select_all_modes(self):
        """Select all modes"""
        for k in self.modes_armed.keys():
            self.modes_armed[k]["variable"].set(True)

    def deselect_all_modes(self):
        """Deselect all modes"""
        for k in self.modes_armed.keys():
            self.modes_armed[k]["variable"].set(False)

    def populate_experiment_values(self):
        """Populate the experiment values"""
        coefs_dict = self.parent_controller.configuration["experiment"][
            "MirrorParameters"
        ]["modes"]
        tw_param_dict = self.parent_controller.configuration["experiment"][
            "AdaptiveOpticsParameters"
        ]["TonyWilson"]
        for k in coefs_dict.keys():
            self.widgets[k].set(coefs_dict[k])
        for k in tw_param_dict.keys():
            if k == "modes_armed":
                for mode_name in tw_param_dict["modes_armed"].keys():
                    self.modes_armed[mode_name]["variable"].set(
                        tw_param_dict["modes_armed"][mode_name]
                    )
            else:
                if type(self.widgets[k]) == dict:
                    self.widgets[k]["variable"].set(tw_param_dict[k])
                    continue

                self.widgets[k].set(tw_param_dict[k])

    def clear_all_coefs(self):
        """Clear all coefficients"""
        coefs_dict = self.parent_controller.configuration["experiment"][
            "MirrorParameters"
        ]["modes"]
        for k in coefs_dict.keys():
            self.widgets[k].set(0.0)
        self.update_experiment_values()

    def update_experiment_values(self):
        """Update the experiment values"""
        modes_dict = {}
        coef_list = self.get_coef_from_widgets()
        keys = self.view.mode_names
        for i, coef in enumerate(coef_list):
            modes_dict[keys[i]] = coef
        self.parent_controller.configuration["experiment"]["MirrorParameters"][
            "modes"
        ] = modes_dict

        self.parent_controller.configuration["experiment"]["AdaptiveOpticsParameters"][
            "TonyWilson"
        ]["iterations"] = int(self.widgets["iterations"].get())
        self.parent_controller.configuration["experiment"]["AdaptiveOpticsParameters"][
            "TonyWilson"
        ]["steps"] = int(self.widgets["steps"].get())
        self.parent_controller.configuration["experiment"]["AdaptiveOpticsParameters"][
            "TonyWilson"
        ]["amplitude"] = float(self.widgets["amplitude"].get())
        self.parent_controller.configuration["experiment"]["AdaptiveOpticsParameters"][
            "TonyWilson"
        ]["from"] = self.widgets["from"]["variable"].get()
        self.parent_controller.configuration["experiment"]["AdaptiveOpticsParameters"][
            "TonyWilson"
        ]["metric"] = self.widgets["metric"]["variable"].get()

        for k in self.modes_armed.keys():
            self.parent_controller.configuration["experiment"][
                "AdaptiveOpticsParameters"
            ]["TonyWilson"]["modes_armed"][k] = self.modes_armed[k]["variable"].get()

        # print(self.parent_controller.configuration['experiment']['MirrorParameters']['modes'])

    def get_coef_from_widgets(self):
        """Get the coefficients from the widgets

        Returns
        -------
        list
            The coefficients
        """
        coef = []
        for k in self.widgets.keys():
            if k in self.view.mode_names:
                coef.append(float(self.widgets[k].get()))
        return coef

    def set_widgets_from_coef(self, coef):
        """Set the widgets from the coefficients

        Parameters
        ----------
        coef : list
            The coefficients
        """
        if list(coef):
            self.view.set_widgets(coef)
            self.update_experiment_values()

    def flatten_mirror(self):
        """Flatten the mirror"""
        self.parent_controller.execute("flatten_mirror")

    def zero_mirror(self):
        """Zero the mirror"""
        self.parent_controller.execute("zero_mirror")

    def set_mirror(self):
        """Set the mirror"""
        self.update_experiment_values()
        self.parent_controller.execute("set_mirror")

    def save_wcs_file(self):
        """Save the wcs file"""
        wcs_path = filedialog.asksaveasfilename(
            defaultextension=".wcs",
            initialdir="E:\\WaveKitX64\\MirrorFiles",
            filetypes=[("Wavefront File", "*.wcs")],
        )

        self.parent_controller.execute("save_wcs_file", wcs_path)

    def set_from_wcs_file(self):
        """Set the mirror from the wcs file"""
        wcs_path = filedialog.askopenfilename(
            defaultextension=".wcs",
            initialdir="E:\\WaveKitX64\\MirrorFiles",
            filetypes=[("Wavefront File", "*.wcs")],
        )

        self.parent_controller.execute("set_mirror_from_wcs", wcs_path)

    def run_tony_wilson(self):
        """Run the tony wilson routine"""
        self.update_experiment_values()
        self.parent_controller.execute("tony_wilson")

    def showup(self, popup_window=None):
        """Show the popup window."""
        # if popup_window is not None:
        #     self.view = popup_window
        self.view.popup.deiconify()
        self.view.popup.attributes("-topmost", 1)

    def plot_mirror(self, data):
        """Plot the mirror data.

        Parameters
        ----------
        data : dict
            The data to plot
        """

        try:
            self.mirror_img.clear()
            self.mirror_img.imshow(
                data["mirror_img"], cmap="bwr", vmin=-0.25, vmax=0.25
            )
            self.mirror_img.set_title("Mirror Pistons")
        except Exception:
            pass

        try:
            coefs = data["coefs"]
            self.coefs_bar.clear()
            self.coefs_bar.bar(range(len(coefs)), coefs)
            self.coefs_bar.set_title("Current Coefs")
            self.coefs_bar.set_xlabel("coef")
            self.coefs_bar.set_ylabel("amplitude")
        except Exception:
            pass

        # To redraw the plot
        self.fig.tight_layout()
        self.fig.canvas.draw_idle()

    def plot_tonywilson(self, data):
        """Plot the tony wilson data.

        Displays a plot of [focus, entropy] with data from autofocus routine

        Parameters
        ----------
        data : dict
            The data to plot
        """

        try:
            # Plotting data
            self.peaks_plot.clear()
            self.peaks_plot.plot(data["peaks"])
            self.peaks_plot.set_title("Image Metric")
            self.peaks_plot.set_xlabel("iteration")
            self.peaks_plot.set_ylabel(data["metric"])
        except KeyError:
            pass

        try:
            self.trace_list = data["trace"]
        except Exception:
            pass

        self.plot_tw_trace()

    def plot_tw_trace(self):
        """Plot the tony wilson trace data."""
        mode = self.parent_controller.configuration["experiment"][
            "AdaptiveOpticsParameters"
        ]["HighlightedMode"]

        if mode is not None:
            try:
                x = self.trace_list[mode]["x"]
                y = self.trace_list[mode]["y"]
                x_fit = self.trace_list[mode]["x_fit"]
                y_fit = self.trace_list[mode]["y_fit"]

                self.trace_plot.clear()
                self.trace_plot.plot(x, y, "*--")
                self.trace_plot.plot(x_fit, y_fit, color="r")
                self.trace_plot.set_title(f"Mode Fit: {mode}")
                self.trace_plot.set_xlabel("coef")
                self.trace_plot.set_ylabel("metric")
            except Exception:
                pass

        # To redraw the plot
        self.fig_tw.tight_layout()
        self.fig_tw.canvas.draw_idle()
