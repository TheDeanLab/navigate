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
import logging
import tkinter

# Third Party Imports

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.view.popups.microscope_setting_popup_window import (
    MicroscopeSettingPopupWindow,
)

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class MicroscopePopupController(GUIController):
    """Controller for the microscope setting popup window."""

    def __init__(self, view, parent_controller, microscope_info):
        """Initialize the MicroscopePopupController.

        Parameters
        ----------
        view : object
            GUI element containing widgets and variables to control.
            Likely tk.Toplevel-derived.
        parent_controller : Navigate_controller
            The main controller.
        microscope_info : dict
            A dictionary containing the information of the microscopes.

        """
        super().__init__(view, parent_controller)

        #: tk.Toplevel-derived: The popup window.
        self.view = MicroscopeSettingPopupWindow(view, microscope_info)

        #: dict: A dictionary containing the widgets.
        self.widgets = self.view.get_widgets()

        #: dict: A dictionary containing the variables.
        self.variables = self.view.get_variables()

        #: dict: A dictionary containing the buttons.
        self.buttons = self.view.get_buttons()

        #: dict: A dictionary containing the microscope information.
        self.microscope_info = microscope_info

        #: str: The name of the primary microscope.
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
                "Not Use",
            )
            self.widgets[microscope_name].widget.bind(
                "<<ComboboxSelected>>", self.update_microscope_mode(microscope_name)
            )

        # button events
        self.buttons["confirm"].configure(command=self.confirm_microscope_setting)
        self.buttons["cancel"].configure(command=self.exit_func)

    def showup(self):
        """This function will let the popup window show in front."""
        self.view.popup.deiconify()
        # self.view.popup.attributes("-topmost", 1)

    def exit_func(self):
        """Close the window and delete this controller."""
        self.view.popup.dismiss()
        delattr(self.parent_controller, "microscope_popup_controller")

    def update_microscope_mode(self, microscope_name):
        """Update the microscope mode.

        Parameters
        ----------
        microscope_name : str
            The name of the microscope.

        Returns
        -------
        func
            A function to update the microscope mode.
        """

        def clear_device_info(microscope_name):
            for microscope in self.microscope_info.keys():
                if microscope != microscope_name:
                    for k in self.microscope_info[microscope_name].keys():
                        if (
                            self.microscope_info[microscope_name][k]
                            == self.microscope_info[microscope].get(k, "")
                        ):
                            self.variables[f"{microscope_name} {k}"].set("")

        variable = self.variables[microscope_name]
        microscope_name = microscope_name

        def func(*args):
            """Update the microscope mode.

            Parameters
            ----------
            *args : list
                The arguments.
            """
            setting_value = variable.get()
            if setting_value == "Primary Microscope":
                self.primary_microscope = microscope_name
                # check the status of other microscopes
                for microscope in self.microscope_info.keys():
                    if (
                        microscope != microscope_name
                        and self.variables[microscope].get() == setting_value
                    ):
                        self.variables[microscope].set("Additional Microscope")
                        clear_device_info(microscope)
            elif self.primary_microscope == microscope_name:
                self.primary_microscope = None

            if setting_value == "Additional Microscope":
                clear_device_info(microscope_name)
            else:
                # set all the devices to real device
                for k in self.microscope_info[microscope_name]:
                    self.variables[f"{microscope_name} {k}"].set(
                        self.microscope_info[microscope_name][k]
                    )

        return func

    def confirm_microscope_setting(self):
        """Confirm the microscope settings."""
        # must have one primary microscope
        if not self.primary_microscope:
            tkinter.messagebox.showerror(
                title="Warning",
                message="There is no Primary Microscope! " "Please select one!",
            )
            self.showup()
            return
        # tell the controller to start a new Camera View Window and prepare a virtual
        # microscope
        if (
            self.primary_microscope
            != self.parent_controller.configuration["experiment"]["MicroscopeState"][
                "microscope_name"
            ]
        ):
            self.parent_controller.configuration["experiment"]["MicroscopeState"][
                "microscope_name"
            ] = self.primary_microscope
            zoom = self.parent_controller.configuration["waveform_constants"][
                "remote_focus_constants"
            ][self.primary_microscope].keys()[0]
            self.parent_controller.configuration["experiment"]["MicroscopeState"][
                "zoom"
            ] = zoom
            self.parent_controller.menu_controller.resolution_value.set(
                f"{self.primary_microscope} {zoom}"
            )

        has_multi_cameras = False
        for microscope_name in self.microscope_info.keys():
            if self.variables[microscope_name].get() == "Additional Microscope":
                config = {}
                for k in self.microscope_info[microscope_name].keys():
                    config[k] = self.variables[f"{microscope_name} {k}"].get()
                self.parent_controller.additional_microscopes_configs[
                    microscope_name
                ] = config
                has_multi_cameras = True
            elif (
                microscope_name in self.parent_controller.additional_microscopes_configs
            ):
                del self.parent_controller.additional_microscopes_configs[
                    microscope_name
                ]

        # enable/disable change 'resolution'(microscope) menu if there are multiple
        # cameras running
        # enable primary camera
        for microscope_name in self.microscope_info.keys():
            if microscope_name == self.primary_microscope or not has_multi_cameras:
                # enable
                self.parent_controller.view.menubar.menu_resolution.entryconfig(
                    microscope_name, state="normal"
                )
                # disable camera setting menu item
                self.parent_controller.view.menubar.menu_resolution.entryconfig(
                    f"{microscope_name} Camera Setting", state="disabled"
                )
                controller_name = f"{microscope_name.lower()}_camera_setting_controller"
                if hasattr(self.parent_controller, controller_name):
                    camera_setting_controller = getattr(self.parent_controller, controller_name)
                    camera_setting_controller.popup.popup.dismiss()
                    delattr(self.parent_controller, controller_name)
            else:
                # disable
                self.parent_controller.view.menubar.menu_resolution.entryconfig(
                    microscope_name, state="disabled"
                )
                # enable camera setting menu item
                self.parent_controller.view.menubar.menu_resolution.entryconfig(
                    f"{microscope_name} Camera Setting", state="normal"
                )

        self.exit_func()
