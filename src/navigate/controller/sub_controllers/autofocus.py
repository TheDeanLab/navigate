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
import logging

# Third Party Imports
import numpy as np
import matplotlib.ticker as tck
from tkinter import messagebox

# Local Imports
import navigate
from navigate.controller.sub_controllers.gui import GUIController
from navigate.view.popups.autofocus_setting_popup import AutofocusPopup

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class AutofocusPopupController(GUIController):
    """Class creates the popup to configure autofocus parameters."""

    def __init__(
        self,
        view: AutofocusPopup,
        parent_controller: "navigate.controller.controller.Controller",
    ) -> None:
        """
        Parameters
        ----------
        view : AutofocusPopup
            The view of the autofocus popup.
        parent_controller : navigate.controller.controller.Controller
            The parent controller of the autofocus popup.
        """
        super().__init__(view, parent_controller)

        #: dict: The autofocus setting dictionary.
        self.widgets = self.view.get_widgets()

        #: str: The microscope name.
        self.microscope_name = None

        #: dict: The autofocus setting dictionary.
        self.setting_dict = None

        #: object: The autofocus figure.
        self.autofocus_fig = self.view.fig

        #: object: The autofocus coarse plot.
        self.autofocus_coarse = self.view.coarse
        self.populate_experiment_values()

        #: object: The autofocus coarse plot.
        self.coarse_plot = None

        # Dismiss popup.
        self.view.popup.protocol("WM_DELETE_WINDOW", self.close_popup)
        self.view.popup.bind("<Escape>", self.close_popup)

        self.view.autofocus_btn.configure(command=self.start_autofocus)
        self.view.inputs["device"].get_variable().trace_add(
            "write", self.update_device_ref
        )
        self.view.inputs["device_ref"].get_variable().trace_add(
            "write", self.show_autofocus_setting
        )
        for k in self.view.setting_vars:
            self.view.setting_vars[k].trace_add("write", self.update_setting_dict(k))

    def close_popup(self, *_: tuple[str]) -> None:
        """Close the popup window

        Parameters
        ----------
        _ : tuple[str]
            The event arguments.
        """
        # We should add saving function to the function closing the window

        self.view.popup.dismiss()
        delattr(self.parent_controller, "af_popup_controller")

    def populate_experiment_values(self) -> None:
        """Populate Experiment Values

        Populates the experiment values from the experiment settings dictionary
        """
        self.setting_dict = self.parent_controller.configuration["experiment"][
            "AutoFocusParameters"
        ]
        self.microscope_name = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["microscope_name"]

        setting_dict = self.setting_dict[self.microscope_name]

        # Default to stages, if they exist.
        if "stage" in setting_dict:
            device = "stage"
        else:
            device = setting_dict.keys()[0]
        self.widgets["device"].widget["values"] = setting_dict.keys()
        self.widgets["device"].set(device)

        # Default to the f axis, if it exists.
        if "f" in setting_dict[device]:
            device_ref = "f"
        else:
            device_ref = setting_dict[device].keys()[0]
        self.widgets["device_ref"].widget["values"] = setting_dict[device].keys()
        self.widgets["device_ref"].set(device_ref)

        for k in self.view.setting_vars:
            self.view.setting_vars[k].set(setting_dict[device][device_ref][k])

    def showup(self) -> None:
        """Shows the popup window"""
        self.view.popup.deiconify()

    def start_autofocus(self) -> None:
        """Starts the autofocus process."""
        device = self.widgets["device"].widget.get()
        device_ref = self.widgets["device_ref"].widget.get()
        self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "autofocus_device"
        ] = device
        self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "autofocus_device_ref"
        ] = device_ref

        # verify autofocus parameters
        setting_dict = self.setting_dict[self.microscope_name][device][device_ref]
        warning_message = ""
        for k in ["coarse", "fine"]:
            if setting_dict[f"{k}_selected"]:
                try:
                    step = float(setting_dict[f"{k}_step_size"])
                    value = float(setting_dict[f"{k}_range"])
                    if step <= 0 or value < step:
                        warning_message += f"{k} settings are not correct!\n"
                except Exception as e:
                    logger.exception(e)
                    warning_message += f"{k} settings are not correct!\n"
        if warning_message:
            messagebox.showerror(
                title="Navigate",
                message=warning_message,
            )
            return
        self.parent_controller.execute("autofocus", device, device_ref)

    def update_device_ref(self, *_: tuple[str]) -> None:
        """Update device reference name

        Parameters
        ----------
        _: tuple[str]
            The event arguments.
        """
        device = self.widgets["device"].widget.get()
        device_refs = self.setting_dict[self.microscope_name][device].keys()
        self.widgets["device_ref"].widget["values"] = device_refs
        self.widgets["device_ref"].widget.set(device_refs[0])

    def show_autofocus_setting(self, *_: tuple[str]) -> None:
        """Show Autofocus Parameters

        Parameters
        ----------
        _: tuple[str]
            The event arguments.
        """
        device = self.widgets["device"].widget.get()
        device_ref = self.widgets["device_ref"].widget.get()
        setting_dict = self.setting_dict[self.microscope_name]
        for k in self.view.setting_vars:
            self.view.setting_vars[k].set(setting_dict[device][device_ref][k])

    def update_setting_dict(self, parameter: str) -> callable:
        """Show Autofocus Parameters

        Parameters
        ----------
        parameter : str
            The parameter to be updated.

        Returns
        -------
        callable
            The function to update the parameter
        """

        def func(*_: tuple[str]) -> None:
            device = self.widgets["device"].widget.get()
            device_ref = self.widgets["device_ref"].widget.get()
            self.setting_dict[self.microscope_name][device][device_ref][parameter] = (
                self.view.setting_vars[parameter].get()
            )

        return func

    def display_plot(self, data_and_flags: tuple[np.ndarray, bool, bool]) -> None:
        """Displays the autofocus plot

        data : tuple[np.ndarray, bool, bool]
            (data, line_plot, clear_data)
            data: The data to be plotted.
            line_plot:
                If True, the plot will be a line plot.
                If False, the plot will be a scatter plot.
            clear_data:
                If True, the plot will be cleared before plotting.
                If False, the plot will be added to the existing plot.
        """
        # Unpack the data and flags
        data, line_plot, clear_data = data_and_flags
        data = np.asarray(data, dtype=float)

        # Pull current settings for the selected device/ref
        device = self.widgets["device"].widget.get()
        device_ref = self.widgets["device_ref"].widget.get()
        settings = self.setting_dict[self.microscope_name][device][device_ref]

        # Calculate the coarse portion of the data
        coarse_range = float(settings.get("coarse_range", 500))
        coarse_step = float(settings.get("coarse_step_size", 50))
        coarse_steps = int(coarse_range) // int(coarse_step) + 1

        if clear_data:
            self.autofocus_coarse.clear()
            if data.shape[0] > 0:
                self.autofocus_coarse.plot(
                    data[:coarse_steps, 0], data[:coarse_steps, 1], "k."
                )

            # fine segment begins after coarse, not at fine_steps
            if data.shape[0] > coarse_steps:
                self.autofocus_coarse.plot(
                    data[coarse_steps:, 0], data[coarse_steps:, 1], "k."
                )

            if data.size:
                self._plot_maxima(data)

        if line_plot and data.size:
            self.autofocus_coarse.plot(data[:, 0], data[:, 1], "r-")

        self._redraw_plot()

    def _redraw_plot(self):
        # To redraw the plot
        self.autofocus_coarse.set_title("Discrete Cosine Transform", fontsize=18)
        self.autofocus_coarse.set_xlabel("Focus Stage Position", fontsize=16)
        self.autofocus_coarse.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))
        self.autofocus_coarse.yaxis.set_minor_locator(tck.AutoMinorLocator())
        self.autofocus_coarse.xaxis.set_minor_locator(tck.AutoMinorLocator())
        self.autofocus_fig.tight_layout()
        self.autofocus_fig.canvas.draw_idle()

    def _plot_maxima(self, data: np.ndarray) -> None:
        # Plot the maxima
        y_max = np.max(data[:, 1])
        peak_loc = data[np.argmax(data[:, 1]), 0]

        y_axes_limit = self.autofocus_coarse.get_ylim()
        x_axes_limit = self.autofocus_coarse.get_xlim()

        # Vertical Indicator
        self.coarse_plot = self.autofocus_coarse.plot(
            [peak_loc, peak_loc], [y_axes_limit[0], y_axes_limit[1]], "--", color="gray"
        )

        # Horizontal Indicator
        self.coarse_plot = self.autofocus_coarse.plot(
            [x_axes_limit[0], x_axes_limit[1]], [y_max, y_max], "--", color="gray"
        )

    @property
    def custom_events(self) -> dict[str, callable]:
        """dict: Custom events for this controller

        Returns
        -------
        dict[str, callable]
            The custom events for this controller.
        """
        return {"autofocus": self.display_plot}
