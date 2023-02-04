# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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

from aslm.controller.sub_controllers.gui_controller import GUIController
from aslm.view.menus.microscope_setting_popup_window import MicroscopeSettingPopupWindow

import logging
import tkinter

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class MicroscopePopupController(GUIController):
    def __init__(self, view, parent_controller, microscope_info):
        """
        Controller for remote focus parameters.

        Parameters
        ----------
        view : object
            GUI element containing widgets and variables to control. Likely tk.Toplevel-derived.
        parent_controller : ASLM_controller
            The main controller.
        waveform_constants_path : str
            Location of file where remote_focus_dict is read from/saved to.

        Returns
        -------
        None
        """
        super().__init__(view, parent_controller)

        self.view = MicroscopeSettingPopupWindow(view, microscope_info)
        self.widgets = self.view.get_widgets()
        self.variables = self.view.get_variables()
        self.buttons = self.view.get_buttons()

        self.microscope_info = microscope_info
        self.primary_microscope = None

        # add saving function to the function closing the window
        self.view.popup.protocol(
            "WM_DELETE_WINDOW",
            self.exit_func,
        )

        for microscope_name in self.microscope_info:
            self.widgets[microscope_name].widget["values"] = (
                "Primary Microscope",
                "Additional Microscope",
                "Not Use"
            )
            self.widgets[microscope_name].widget.bind("<<ComboboxSelected>>", self.update_microscope_mode(microscope_name))

        # button events
        self.buttons["confirm"].configure(command=self.confirm_microscope_setting)
        self.buttons["cancel"].configure(command=self.exit_func)

    def showup(self):
        """This function will let the popup window show in front."""
        self.view.popup.deiconify()
        # self.view.popup.attributes("-topmost", 1)

    def exit_func(self):
        """Close the window and delete this controller"""
        self.view.popup.dismiss()
        delattr(self.parent_controller, "microscope_popup_controller")

    def update_microscope_mode(self, microscope_name):
        
        def clear_device_info(microscope_name):
            for microscope in self.microscope_info.keys():
                if microscope != microscope_name:
                    for k in self.microscope_info[microscope_name].keys():
                        if self.microscope_info[microscope_name][k] == self.microscope_info[microscope][k]:
                            self.variables[f"{microscope_name} {k}"].set("")

        variable = self.variables[microscope_name]
        microscope_name = microscope_name
        
        def func(*args):
            setting_value = variable.get()
            if setting_value == "Primary Microscope":
                self.primary_microscope = microscope_name
                # check the status of other microscopes
                for microscope in self.microscope_info.keys():
                    if microscope != microscope_name and self.variables[microscope].get() == setting_value:
                        self.variables[microscope].set("Additional Microscope")
                        clear_device_info(microscope)
            elif self.primary_microscope == microscope_name:
                self.primary_microscope = None
        
            if setting_value == "Additional Microscope":
                clear_device_info(microscope_name)
            else:
                # set all the devices to real device
                for k in self.microscope_info[microscope_name]:
                    self.variables[f"{microscope_name} {k}"].set(self.microscope_info[microscope_name][k])

        return func

    def confirm_microscope_setting(self):
        # must have one primary microscope
        if not self.primary_microscope:
            tkinter.messagebox.showerror(
                title="Warning",
                message="There is no Primary Microscope! "
                "Please select one!",
            )
            self.showup()
            return
        # tell the controller to start a new Camera View Window and prepare a virtual microscope
        if self.primary_microscope != self.parent_controller.configuration["experiment"]["MicroscopeState"]["microscope_name"]:
            self.parent_controller.configuration["experiment"]["MicroscopeState"]["microscope_name"] = self.primary_microscope
            zoom = self.parent_controller.configuration["waveform_constants"]["remote_focus_constants"][self.primary_microscope].keys()[0]
            self.parent_controller.configuration["experiment"]["MicroscopeState"]["zoom"] = zoom
            self.parent_controller.resolution_value.set(f"{self.primary_microscope} {zoom}")

        has_multi_cameras = False
        for microscope_name in self.microscope_info.keys():
            if self.variables[microscope_name].get() == "Additional Microscope":
                config = {}
                for k in self.microscope_info[microscope_name].keys():
                    config[k] = self.variables[f"{microscope_name} {k}"].get()
                self.parent_controller.additional_microscopes_configs[microscope_name] = config
                has_multi_cameras = True
            elif microscope_name in self.parent_controller.additional_microscopes_configs:
                del self.parent_controller.additional_microscopes_configs[microscope_name]

        # enable/disable change 'resolution'(microscope) menu if there are multiple cameras running
        # enable primary camera
        for microscope_name in self.microscope_info.keys():
            if microscope_name == self.primary_microscope or not has_multi_cameras:
                # enable
                self.parent_controller.view.menubar.menu_resolution.entryconfig(microscope_name, state="normal")
            else:
                # disable
                self.parent_controller.view.menubar.menu_resolution.entryconfig(microscope_name, state="disabled")

        self.exit_func()
