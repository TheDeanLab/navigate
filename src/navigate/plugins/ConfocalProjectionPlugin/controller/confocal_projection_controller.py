# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
#

import tkinter as tk

from navigate.controller.sub_controllers.gui_controller import GUIController

class ConfocalProjectionController(GUIController):

    def __init__(self, view, parent_controller=None):

        super().__init__(view, parent_controller)

        # Get Widgets from confocal_projection_settings in view
        #: dict: The widgets in the confocal projection settings frame.
        self.conpro_acq_widgets = self.view.get_widgets()
        #: dict: The values in the confocal projection settings frame.
        self.conpro_acq_vals = self.view.get_variables()

        # laser/stack cycling event binds
        self.conpro_acq_widgets["cycling"].widget["values"] = ["Per Plane", "Per Stack"]
        self.conpro_acq_vals["cycling"].trace_add("write", self.update_cycling_setting)

        # confocal-projection setting variables

        # confocal-projection event binds
        self.conpro_acq_vals["scanrange"].trace_add("write", self.update_scanrange)
        self.conpro_acq_vals["n_plane"].trace_add("write", self.update_plane_number)
        self.conpro_acq_vals["offset_start"].trace_add(
            "write", self.update_offset_start
        )
        self.conpro_acq_vals["offset_end"].trace_add("write", self.update_offset_end)

        self.populate_experiment_setting()

    def populate_experiment_setting(self):
        self.microscope_state_dict = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]

        for _ in ["scanrange", "n_plane", "offset_start", "offset_end"]:
            self.set_widget_value(_)

        cycling = "Per Stack" if self.microscope_state_dict["conpro_cycling_mode"] == "per_stack" else "Per Plane"
        self.conpro_acq_vals["cycling"].set(cycling)

    
    def update_scanrange(self, *args):
        """Update scan range value in the controller

        Parameters
        ----------
        *args
            Not used

        Examples
        --------
        >>> self.update_scanrange()
        """
        try:
            scanrange = float(self.conpro_acq_vals["scanrange"].get())
        except tk._tkinter.TclError:
            scanrange = 0
        self.microscope_state_dict["scanrange"] = scanrange

    def update_plane_number(self, *args):
        """Update plane number value in the controller

        Parameters
        ----------
        *args
            Not used

        Examples
        --------
        >>> self.update_plane_number()
        """
        try:
            n_plane = float(self.conpro_acq_vals["n_plane"].get())
        except tk._tkinter.TclError:
            n_plane = 1
        self.microscope_state_dict["n_plane"] = n_plane
        # logger.info(f"Controller updated plane number: {n_plane}")

    def update_offset_start(self, *args):
        """Update offset start value in the controller

        Parameters
        ----------
        *args
            Not used

        Examples
        --------
        >>> self.update_offset_start()
        """
        try:
            offset_start = float(self.conpro_acq_vals["offset_start"].get())
        except tk._tkinter.TclError:
            offset_start = 0
        self.microscope_state_dict["offset_start"] = offset_start
        # logger.info(f"Controller updated offset start: {offset_start}")

    def update_offset_end(self, *args):
        """Update offset end value in the controller

        Parameters
        ----------
        *args
            Not used

        Examples
        --------
        >>> self.update_offset_end()
        """
        try:
            offset_end = float(self.conpro_acq_vals["offset_end"].get())
        except tk._tkinter.TclError:
            offset_end = 0
        self.microscope_state_dict["offset_end"] = offset_end
        # logger.info(f"Controller updated offset end: {offset_end}")

    def update_cycling_setting(self, *args):
        self.microscope_state_dict["conpro_cycling_mode"] = (
            "per_stack"
            if self.conpro_acq_vals["cycling"].get() == "Per Stack"
            else "per_plane"
        )

    def set_widget_value(self, widget_name):
        try:
            widget_value = float(self.microscope_state_dict[widget_name])
        except:
            widget_value = 0

        self.conpro_acq_vals[widget_name].set(widget_value)