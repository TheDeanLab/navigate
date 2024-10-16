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
from tkinter import NSEW

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.tools.waveform_template_funcs import get_waveform_template_parameters

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class WaveformTabController(GUIController):
    """Controller for the waveform tab"""

    def __init__(self, view, parent_controller=None):
        """Initialize the waveform tab controller

        Parameters
        ----------
        view : navigate.view.waveform_tab.WaveformTab
            View for the waveform tab
        parent_controller : navigate.controller.main_controller.MainController
            Parent controller for the waveform tab
        """
        super().__init__(view, parent_controller)

        #: dict: Dictionary of remote focus waveforms
        self.remote_focus_waveform = 0

        #: dict: Dictionary of laser waveforms
        self.laser_ao_waveforms = 0

        self.initialize_plots()

        microscope_name = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["microscope_name"]
        self.view.waveform_settings.inputs["sample_rate"].set(
            self.parent_controller.configuration["configuration"]["microscopes"][
                microscope_name
            ]["daq"]["sample_rate"]
        )
        self.update_sample_rate()
        self.view.waveform_settings.inputs["sample_rate"].get_variable().trace_add(
            "write", self.update_sample_rate
        )
        self.view.waveform_settings.inputs["waveform_template"].widget["values"] = list(
            self.parent_controller.configuration["waveform_templates"].keys()
        )
        self.view.waveform_settings.inputs["waveform_template"].set("Default")
        self.view.waveform_settings.inputs["waveform_template"].widget.bind(
            "<<ComboboxSelected>>", self.update_waveform_template
        )

        self.view.master.bind("<<NotebookTabChanged>>", self.plot_waveforms)

    def update_sample_rate(self, *args):
        """Update the sample rate in the waveform settings

        Parameters
        ----------
        *args : tuple
            Unused
        """

        sample_rate = self.view.waveform_settings.inputs["sample_rate"].get()
        if sample_rate == "":
            return
        microscope_name = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["microscope_name"]
        self.parent_controller.configuration["configuration"]["microscopes"][
            microscope_name
        ]["daq"]["sample_rate"] = int(sample_rate)

        #: int: Sample rate of the waveforms
        self.sample_rate = int(sample_rate)

    def update_waveform_template(self, *args):
        """Update waveform template selection

        Parameters
        ----------
        *args : tuple
            Unused
        """
        self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "waveform_template"
        ] = self.view.waveform_settings.inputs["waveform_template"].get()

        event = type("MyEvent", (object,), {})
        self.plot_waveforms(event)

    def update_waveforms(self, waveform_dict):
        """Update the waveforms in the waveform tab

        Parameters
        ----------
        waveform_dict : dict
            Dictionary of waveforms
        """
        #: dict: Dictionary of waveforms
        self.waveform_dict = waveform_dict
        event = type("MyEvent", (object,), {})
        self.plot_waveforms(event)

    def initialize_plots(self):
        """Initialize the plots in the waveform tab."""
        self.view.plot_etl = self.view.fig.add_subplot(211)
        self.view.plot_galvo = self.view.fig.add_subplot(212)
        self.view.canvas.get_tk_widget().grid(
            row=5, column=0, columnspan=3, sticky=NSEW, padx=(5, 5), pady=(5, 5)
        )

    def plot_waveforms(self, event):
        """Plot the waveforms in the waveform tab

        Parameters
        ----------
        event : Tkinter event
            Tkinter event
        """
        parent_notebook = self.view.master

        try:
            current_tab = parent_notebook.select()
        except Exception:  # noqa
            return

        if (
            self.view.is_docked
            and parent_notebook.tab(current_tab, "text") != "Waveforms"
        ):
            return
        self.view.plot_etl.clear()
        self.view.plot_galvo.clear()

        waveform_template_name = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ].get("waveform_template", "Default")
        repeat_num, expand_num = get_waveform_template_parameters(
            waveform_template_name,
            self.parent_controller.configuration["waveform_templates"],
            self.parent_controller.configuration["experiment"]["MicroscopeState"],
        )

        last_etl = 0
        last_galvo = 0
        last_camera = 0
        max_galvo_waveform = 0
        min_galvo_waveform = 1000000
        max_camera_waveform = 0
        min_camera_waveform = 1000000
        max_remote_focus_waveform = 0
        min_remote_focus_waveform = 1000000
        # two pass
        for k in self.waveform_dict["camera_waveform"].keys():
            remote_focus_waveform = self.waveform_dict["remote_focus_waveform"][k]
            if remote_focus_waveform is None:
                continue
            max_remote_focus_waveform = np.maximum(
                max_remote_focus_waveform, np.max(remote_focus_waveform)
            )
            min_remote_focus_waveform = np.minimum(
                min_remote_focus_waveform, np.min(remote_focus_waveform)
            )
            camera_waveform = self.waveform_dict["camera_waveform"][k]
            max_camera_waveform = np.maximum(
                max_camera_waveform, np.max(camera_waveform)
            )
            min_camera_waveform = np.minimum(
                min_camera_waveform, np.min(camera_waveform)
            )
            for galvo_waveform in self.waveform_dict["galvo_waveform"]:
                max_galvo_waveform = np.maximum(
                    max_galvo_waveform, np.max(galvo_waveform[k])
                )
                min_galvo_waveform = np.minimum(
                    min_galvo_waveform, np.min(galvo_waveform[k])
                )

        true_max = np.maximum(max_remote_focus_waveform, max_galvo_waveform)
        true_min = np.minimum(min_remote_focus_waveform, min_galvo_waveform)
        if true_max == true_min:
            scale = 1
            true_min = 0
        else:
            scale = (true_max - true_min) / (max_camera_waveform - min_camera_waveform)

        for k in sorted(self.waveform_dict["camera_waveform"].keys()):
            if self.waveform_dict["remote_focus_waveform"][k] is None:
                continue
            remote_focus_waveform = self.waveform_dict["remote_focus_waveform"][k]

            galvo_waveform_list = []
            for galvo_waveform in self.waveform_dict["galvo_waveform"]:
                if galvo_waveform[k] is None:
                    continue
                max_galvo_waveform = np.maximum(
                    max_galvo_waveform, np.max(galvo_waveform[k])
                )
                min_galvo_waveform = np.minimum(
                    min_galvo_waveform, np.min(galvo_waveform[k])
                )
                galvo_waveform_list += [galvo_waveform[k]]

            camera_waveform = (
                scale * self.waveform_dict["camera_waveform"][k] + true_min
            )

            waveform_repeat_total_num = repeat_num * expand_num

            channel_index = k[-1]
            label = "CH" + channel_index

            self.view.plot_etl.plot(
                np.arange(len(remote_focus_waveform) * waveform_repeat_total_num)
                / self.sample_rate
                + last_etl,
                np.hstack([remote_focus_waveform] * waveform_repeat_total_num),
                label=label,
            )
            # ax = self.view.plot_galvo.axis
            for i, galvo_waveform in enumerate(galvo_waveform_list):
                label = label + " G" + str(i)
                self.view.plot_galvo.plot(
                    np.arange(len(galvo_waveform) * waveform_repeat_total_num)
                    / self.sample_rate
                    + last_galvo,
                    np.hstack([galvo_waveform] * waveform_repeat_total_num),
                    label=label,
                )
            self.view.plot_etl.plot(
                np.arange(len(camera_waveform) * waveform_repeat_total_num)
                / self.sample_rate
                + last_camera,
                np.hstack([camera_waveform] * waveform_repeat_total_num),
                c="k",
                linestyle="--",
            )
            self.view.plot_galvo.plot(
                np.arange(len(camera_waveform) * waveform_repeat_total_num)
                / self.sample_rate
                + last_camera,
                np.hstack([camera_waveform] * waveform_repeat_total_num),
                c="k",
                linestyle="--",
            )
            last_etl += (
                len(remote_focus_waveform)
                * waveform_repeat_total_num
                / self.sample_rate
            )
            last_galvo += (
                len(galvo_waveform) * waveform_repeat_total_num / self.sample_rate
            )
            last_camera += (
                len(camera_waveform) * waveform_repeat_total_num / self.sample_rate
            )

        self.view.plot_etl.set_title("Remote Focus Waveform")
        self.view.plot_galvo.set_title("Galvo Waveform")

        self.view.plot_etl.set_xlabel("Duration (s)")
        self.view.plot_galvo.set_xlabel("Duration (s)")

        self.view.plot_etl.set_ylabel("Amplitude")
        self.view.plot_galvo.set_ylabel("Amplitude")

        self.view.plot_etl.legend()
        self.view.plot_galvo.legend()

        self.view.fig.tight_layout()

        self.view.canvas.draw_idle()

    def set_mode(self, mode):
        """Set the mode of the waveform tab

        Parameters
        ----------
        mode : str
            Mode to set the waveform tab to
        """
        state = "normal" if mode == "stop" else "disabled"
        self.view.waveform_settings.inputs["waveform_template"].widget["state"] = state

    def set_waveform_template(self, template_name):
        """Set the waveform template name

        Parameters
        ----------
        template_name : str
            Set the waveform template name
        """
        self.view.waveform_settings.inputs["waveform_template"].set(template_name)
        self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "waveform_template"
        ] = template_name

    @property
    def custom_events(self):
        """Custom events for the waveform tab"""
        return {"waveform": self.update_waveforms}
