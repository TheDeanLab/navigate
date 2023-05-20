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
import platform
import tkinter as tk

# Third Party Imports

# Local Imports
from aslm.view.popups.ilastik_setting_popup import ilastik_setting_popup
from aslm.view.popups.help_popup import HelpPopup
from aslm.view.popups.camera_map_setting_popup import CameraMapSettingPopup
from aslm.controller.sub_controllers.gui_controller import GUIController
from aslm.controller.sub_controllers.help_popup_controller import HelpPopupController
from aslm.controller.sub_controllers import (
    IlastikPopupController,
    CameraMapSettingPopupController,
)
from aslm.tools.file_functions import save_yaml_file


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class MenuController(GUIController):
    def __init__(self, view, parent_controller=None):
        super().__init__(view, parent_controller)
        self.parent_controller = parent_controller
        self.view = view
        self.resolution_value = tk.StringVar()
        self.feature_id_val = tk.IntVar(0)
        self.disable_stage_limits = tk.IntVar(0)

    def initialize_menus(self, is_synthetic_hardware=False):
        """Initialize menus
        This function defines all the menus in the menubar

        Parameters
        ----------
        is_synthetic_hardware : bool
            If True, then the hardware is simulated.
            If False, then the hardware is real.

        Returns
        -------
        configuration_controller : class
            Camera view sub-controller.

        """

        def new_experiment(*args):
            """Create a new experiment file."""
            self.parent_controller.populate_experiment_setting(
                self.default_experiment_file
            )

        def load_experiment(*args):
            """Load an experiment file."""
            filename = tk.filedialog.askopenfilename(
                defaultextension=".yml", filetypes=[("Yaml files", "*.yml *.yaml")]
            )
            if not filename:
                return
            self.parent_controller.populate_experiment_setting(filename)

        def save_experiment(*args):
            """Save an experiment file.

            Updates model.experiment and saves it to file.
            """
            if not self.parent_controller.update_experiment_setting():
                tk.messagebox.showerror(
                    title="Warning",
                    message="Incorrect/missing settings. "
                    "Cannot save current experiment file.",
                )
                return
            filename = tk.filedialog.asksaveasfilename(
                defaultextension=".yml", filetypes=[("Yaml file", "*.yml *.yaml")]
            )
            if not filename:
                return
            save_yaml_file(
                "", self.parent_controller.configuration["experiment"], filename
            )

        def load_images():
            """Load images from a file."""
            filenames = tk.filedialog.askopenfilenames(
                defaultextension=".tif", filetypes=[("tiff files", "*.tif *.tiff")]
            )
            if not filenames:
                return
            self.model.load_images(filenames)

        def popup_camera_map_setting():
            """Pop up the Camera Map setting window."""
            if hasattr(self, "camera_map_popup_controller"):
                self.camera_map_popup_controller.showup()
                return
            map_popup = CameraMapSettingPopup(self.view)
            self.camera_map_popup_controller = CameraMapSettingPopupController(
                map_popup, self
            )

        def popup_ilastik_setting():
            """Pop up the Ilastik setting window."""
            ilastik_popup_window = ilastik_setting_popup(self.view)
            ilastik_url = self.parent_controller.configuration["rest_api_config"][
                "Ilastik"
            ]["url"]
            if hasattr(self, "ilastik_controller"):
                self.ilastik_controller.showup(ilastik_popup_window)
            else:
                self.ilastik_controller = IlastikPopupController(
                    ilastik_popup_window, self, ilastik_url
                )

        def popup_help():
            """Pop up the help window."""
            if hasattr(self, "help_controller"):
                self.help_controller.showup()
                return
            help_pop = HelpPopup(self.view)
            self.help_controller = HelpPopupController(help_pop, self)

        def toggle_stage_limits(*args):
            """Toggle stage limits."""
            if self.disable_stage_limits.get() == 1:
                print("Enabling stage limits")
            else:
                print("Disabling stage limits")

            # if self.disable_stage_limits.get():
            #     print("Disabling stage limits")
            #     self.parent_controller.execute("disable_stage_limits", False)
            # else:
            #     print("Enabling stage limits")
            #     self.parent_controller.execute("disable_stage_limits", True)
            #
            # self.disable_stage_limits.set(not self.disable_stage_limits.get())

        def populate_menu(menu_dict):
            """Populate the menus from a dictionary.

            Parameters
            ----------
            menu_dict : dict
                menu_dict = {
                    Menu object: {
                        "Menu String Entry": [
                            entry_type (standard, radio),
                            Command,
                            Accelerator,
                            Windows Keystroke,
                            Apple Keystroke",
                ],
                ....

            """
            for menu in menu_dict:
                menu_items = menu_dict[menu]
                for label in menu_items:
                    if "add_separator" in label:
                        menu.add_separator()
                    else:
                        if "standard" in menu_items[label][0]:
                            if menu_items[label][1] is None:
                                # Command not passed, accelerator provided for
                                # informational purposes only.
                                menu.add_command(
                                    label=label, accelerator=menu_items[label][2]
                                )
                            else:
                                # If the command is provided, it is assumed that you
                                # should also bind that command to the accelerator.
                                menu.add_command(
                                    label=label,
                                    command=menu_items[label][1],
                                    accelerator=menu_items[label][2],
                                )
                                if platform.platform() == "Darwin":
                                    # Account for OS specific keystrokes
                                    menu.bind_all(
                                        menu_items[label][4], menu_items[label][1]
                                    )
                                else:
                                    menu.bind_all(
                                        menu_items[label][3], menu_items[label][1]
                                    )
                        elif "radio" in menu_items[label][0]:
                            if menu_items[label][1] is None:
                                # Command not passed, accelerator provided for
                                # informational purposes only.
                                menu.add_radiobutton(
                                    label=label, accelerator=menu_items[label][2]
                                )
                            else:
                                # If the command is provided, it is assumed that you
                                # should also bind that command to the accelerator.
                                menu.add_radiobutton(
                                    label=label,
                                    command=menu_items[label][0],
                                    accelerator=menu_items[label][1],
                                )
                                if platform.platform() == "Darwin":
                                    menu.bind_all(
                                        menu_items[label][4], menu_items[label][1]
                                    )
                                else:
                                    menu.bind_all(
                                        menu_items[label][3], menu_items[label][1]
                                    )

        # File Menu
        file_menu = {
            self.view.menubar.menu_file: {
                "New Experiment": [
                    "standard",
                    new_experiment,
                    "Ctrl+Shift+N",
                    "<Control-N>",
                    "<Control_L-N>",
                ],
                "Load Experiment": [
                    "standard",
                    load_experiment,
                    "Ctrl+Shift+O",
                    "<Control-O>",
                    "<Control_L-O>",
                ],
                "Save Experiment": [
                    "standard",
                    save_experiment,
                    "Ctrl+Shift+S",
                    "<Control-S>",
                    "<Control_L-S>",
                ],
                "add_separator": [None],
                "Save Data": [
                    "standard",
                    lambda x: self.parent_controller.execute("set_save"),
                    "Ctrl+s",
                    "<Control-s>",
                    "<Control_L-s>",
                ],
                "Load Images": ["standard", load_images, None, None, None],
                "Unload Images": [
                    "standard",
                    self.parent_controller.model.load_images(None),
                    None,
                    None,
                    None,
                ],
            }
        }
        populate_menu(file_menu)

        # Stage Control Menu
        # Most bindings are implemented in the keystroke_controller.
        # Accelerators added here to communicate them to users. Could move those key
        # bindings here? Not sure...
        stage_control_menu = {
            self.view.menubar.menu_multi_positions: {
                "Move Up": [
                    "standard",
                    lambda e: self.parent_controller.stage_controller.stage_key_press,
                    "w",
                    "<Key-w>",
                    "<Key-w>",
                ],
                "Move Down": [
                    "standard",
                    self.parent_controller.stage_controller.stage_key_press,
                    "s",
                    "<Key-s>",
                    "<Key-s>",
                ],
                "Move Left": [
                    "standard",
                    self.parent_controller.stage_controller.stage_key_press,
                    "a",
                    "<Key-a>",
                    "<Key-a>",
                ],
                "Move Right": [
                    "standard",
                    self.parent_controller.stage_controller.stage_key_press,
                    "d",
                    "<Key-d>",
                    "<Key-d>",
                ],
                "Move In": ["standard", None, "q", "<Key-q>", "<Key-q>"],
                "Move Out": ["standard", None, "e", "<Key-e>", "<Key-e>"],
                "Move Focus Up": ["standard", None, "r", "<Key-r>", "<Key-r>"],
                "Move Focus Down": ["standard", None, "f", "<Key-f>", "<Key-f>"],
                "Rotate Clockwise": ["standard", None, "z", "<Key-z>", "<Key-z>"],
                "Rotate Counter-Clockwise": [
                    "standard",
                    None,
                    "x",
                    "<Key-x>",
                    "<Key-x>",
                ],
                "add_separator": ["standard", None, None, None, None],
                "Launch Tiling Wizard": ["standard", None, None, None, None],
                "Load Positions": [
                    "standard",
                    self.parent_controller.multiposition_tab_controller.load_positions,
                    None,
                    None,
                    None,
                ],
                "Export Positions": [
                    "standard",
                    self.parent_controller.multiposition_tab_controller.export_positions,
                    None,
                    None,
                    None,
                ],
                "Append Current Position": [
                    "standard",
                    self.parent_controller.multiposition_tab_controller.add_stage_position,
                    None,
                    None,
                    None,
                ],
                "Generate Positions": [
                    "standard",
                    self.parent_controller.multiposition_tab_controller.generate_positions,
                    None,
                    None,
                    None,
                ],
                "Move to Selected Position": [
                    "standard",
                    self.parent_controller.multiposition_tab_controller.move_to_position,
                    None,
                    None,
                    None,
                ],
                "add_separator_1": [None, None, None, None, None],
            },
        }
        populate_menu(stage_control_menu)
        self.view.menubar.menu_multi_positions.add_radiobutton(
            label="Disable Stage Limits",
            value=0,
            command=toggle_stage_limits,
            variable=self.disable_stage_limits,
        )
        self.view.menubar.menu_multi_positions.add_radiobutton(
            label="Enable Stage Limits",
            value=1,
            command=toggle_stage_limits,
            variable=self.disable_stage_limits,
        )
        self.disable_stage_limits.set(1)

        # autofocus menu
        autofocus_menu = {
            self.view.menubar.menu_autofocus: {
                "Perform Autofocus": [
                    "standard",
                    lambda x: self.parent_controller.execute("autofocus"),
                    "Ctrl+A",
                    "<Control-a>",
                    "<Control_L-a>",
                ],
                "Autofocus Settings": [
                    "standard",
                    self.parent_controller.popup_autofocus_setting,
                    "Ctrl+Shift+A",
                    "<Control-A>",
                    "<Control_L-A>",
                ],
            }
        }
        populate_menu(autofocus_menu)

        # Resolution menu
        windows_menu = {
            self.view.menubar.menu_window: {
                "Channel Settings": [
                    "standard",
                    None,
                    "Ctrl+1",
                    "<Control-1>",
                    "<Control_L-1",
                ],
                "Camera Settings": [
                    "standard",
                    None,
                    "Ctrl+2",
                    "<Control-2>",
                    "<Control_L-2",
                ],
                "Stage Control": [
                    "standard",
                    None,
                    "Ctrl+3",
                    "<Control-3>",
                    "<Control_L-3",
                ],
                "Multiposition Table": [
                    "standard",
                    None,
                    "Ctrl+4",
                    "<Control-4>",
                    "<Control_L-4",
                ],
                "add_separator": ["standard", None, None, None, None],
                "Popout Camera Display": ["standard", None, None, None, None],
                "Help": ["standard", popup_help, None, None, None],
            }
        }
        populate_menu(windows_menu)

        # Zoom Menu
        for microscope_name in self.parent_controller.configuration["configuration"][
            "microscopes"
        ].keys():
            zoom_positions = self.parent_controller.configuration["configuration"][
                "microscopes"
            ][microscope_name]["zoom"]["position"]
            if len(zoom_positions) > 1:
                sub_menu = tk.Menu(self.view.menubar.menu_resolution)
                self.view.menubar.menu_resolution.add_cascade(
                    menu=sub_menu, label=microscope_name
                )
                for res in zoom_positions.keys():
                    sub_menu.add_radiobutton(
                        label=res,
                        variable=self.resolution_value,
                        value=f"{microscope_name} {res}",
                    )
            else:
                self.view.menubar.menu_resolution.add_radiobutton(
                    label=microscope_name,
                    variable=self.resolution_value,
                    value=f"{microscope_name} {zoom_positions.keys()[0]}",
                )
        self.resolution_value.trace_add(
            "write",
            lambda *args: self.execute("resolution", self.resolution_value.get()),
        )

        configuration_dict = {
            self.view.menubar.menu_resolution: {
                "add_separator": [None, None, None, None, None],
                "Waveform Parameters": [
                    "standard",
                    self.parent_controller.popup_waveform_setting,
                    None,
                    None,
                    None,
                ],
                "Configure Microscope": [
                    "standard",
                    self.parent_controller.popup_microscope_setting,
                    None,
                    None,
                    None,
                ],
            }
        }
        populate_menu(configuration_dict)

        # add-on features
        feature_list = [
            "None",
            "Switch Resolution",
            "Z Stack Acquisition",
            "Threshold",
            "Ilastik Segmentation",
            "Volume Search",
            "Time Series",
        ]
        for i in range(len(feature_list)):
            self.view.menubar.menu_features.add_radiobutton(
                label=feature_list[i], variable=self.feature_id_val, value=i
            )
        self.feature_id_val.trace_add(
            "write",
            lambda *args: self.execute("load_feature", self.feature_id_val.get()),
        )
        self.view.menubar.menu_features.add_separator()
        self.view.menubar.menu_features.add_command(
            label="Ilastik Settings", command=popup_ilastik_setting
        )
        # disable ilastik menu
        self.view.menubar.menu_features.entryconfig(
            "Ilastik Segmentation", state="disabled"
        )
        self.view.menubar.menu_features.add_command(
            label="Camera offset and variance maps", command=popup_camera_map_setting
        )
