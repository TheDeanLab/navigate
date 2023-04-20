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

# Third Party Imports
import numpy as np
import matplotlib.ticker as tck

# Local Imports
from aslm.controller.sub_controllers.gui_controller import GUIController
from aslm.tools.common_functions import combine_funcs


import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class AutofocusPopupController(GUIController):
    """Class creates the popup to configure autofocus parameters.

    Parameters
    ----------
    view : aslm.view.popups.autofocus_setting_popup.AutofocusPopup
        The view of the autofocus popup.
    parent_controller : aslm.controller.main_controller.MainController
        The parent controller of the autofocus popup.

    Attributes
    ----------
    widgets : dict
        Dictionary of widgets in the autofocus popup.
    autofocus_fig : matplotlib.figure.Figure
        The figure for the autofocus plot.
    autofocus_coarse : matplotlib.axes.Axes
        The coarse autofocus plot.
    autofocus_fine : matplotlib.axes.Axes
        The fine autofocus plot.
    coarse_plot : matplotlib.lines.Line2D
        The coarse autofocus plot line.
    fine_plot : matplotlib.lines.Line2D
        The fine autofocus plot line.

    Methods
    -------
    populate_experiment_values()
        Populates the autofocus popup with the current experiment values.
    update_experiment_values()
        Updates the experiment values with the values in the autofocus popup.
    start_autofocus()
        Starts the autofocus process.
    display_plot(data)
        Displays the autofocus plot.
    showup()
        Shows the autofocus popup.
    """

    def __init__(self, view, parent_controller):
        super().__init__(view, parent_controller)

        self.widgets = self.view.get_widgets()
        self.autofocus_fig = self.view.fig
        self.autofocus_coarse = self.view.coarse
        # self.autofocus_fine = self.view.fine
        self.populate_experiment_values()
        self.coarse_plot = None
        # self.fine_plot = None
        self.setting_dict = self.parent_controller.configuration["experiment"][
            "AutoFocusParameters"
        ]

        # add saving function to the function closing the window
        exit_func = combine_funcs(
            self.update_experiment_values,
            self.view.popup.dismiss,
            lambda: delattr(self.parent_controller, "af_popup_controller"),
        )
        self.view.popup.protocol("WM_DELETE_WINDOW", exit_func)
        self.view.autofocus_btn.configure(command=self.start_autofocus)

    def populate_experiment_values(self):
        """Populate Experiment Values

        Populates the experiment values from the experiment settings dictionary

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.setting_dict = self.parent_controller.configuration["experiment"][
            "AutoFocusParameters"
        ]
        # show the value
        for k in self.widgets:
            self.widgets[k].set(self.setting_dict[k])
        self.view.stage_vars[0].set(self.setting_dict.get("coarse_selected", True))
        self.view.stage_vars[1].set(self.setting_dict.get("fine_selected", True))
        self.view.stage_vars[2].set(self.setting_dict.get("robust_fit", True))

    def update_experiment_values(self):
        """Update Experiment Values

        Updates the experiment values from the experiment settings dictionary

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        for k in self.widgets:
            self.setting_dict[k] = self.widgets[k].get()
        self.setting_dict["coarse_selected"] = self.view.stage_vars[0].get()
        self.setting_dict["fine_selected"] = self.view.stage_vars[1].get()
        self.setting_dict["robust_fit"] = self.view.stage_vars[2].get()

    def showup(self):
        """Shows the popup window

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.view.popup.deiconify()
        self.view.popup.attributes("-topmost", 1)

    def start_autofocus(self):
        """Starts the autofocus process

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.update_experiment_values()
        self.parent_controller.execute("autofocus")

    def display_plot(self, data, line_plot=False, clear_data=True):
        """Displays the autofocus plot

        data : numpy.ndarray
            The data to be plotted.
        line_plot : bool
            If True, the plot will be a line plot.
            If False, the plot will be a scatter plot.
        clear_data : bool
            If True, the plot will be cleared before plotting.
            If False, the plot will be added to the existing plot.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        data = np.asarray(data)
        coarse_range = self.setting_dict.get("coarse_range", 500)
        coarse_step = self.setting_dict.get("coarse_step_size", 50)
        fine_range = self.setting_dict.get("fine_range", 50)
        fine_step = self.setting_dict.get("fine_step_size", 5)

        # Calculate the coarse portion of the data
        coarse_steps = int(coarse_range) // int(coarse_step) + 1
        fine_steps = int(fine_range) // int(fine_step) + 1

        if line_plot is True:
            marker = "r-"
        else:
            marker = "k."

        if clear_data is True:
            self.autofocus_coarse.clear()

        # Plotting coarse data
        self.coarse_plot = self.autofocus_coarse.plot(
            data[:coarse_steps, 0], data[:coarse_steps, 1], marker
        )

        # Plotting fine data
        self.coarse_plot = self.autofocus_coarse.plot(
            data[fine_steps:, 0], data[fine_steps:, 1], marker
        )

        # To redraw the plot
        self.autofocus_coarse.set_title("Discrete Cosine Transform", fontsize=18)
        self.autofocus_coarse.set_xlabel("Focus Stage Position", fontsize=16)
        self.autofocus_coarse.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))
        self.autofocus_coarse.yaxis.set_minor_locator(tck.AutoMinorLocator())
        self.autofocus_coarse.xaxis.set_minor_locator(tck.AutoMinorLocator())
        self.autofocus_fig.tight_layout()
        self.autofocus_fig.canvas.draw_idle()
