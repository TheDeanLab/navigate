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
from aslm.view.popups.waveform_parameter_popup_window import (
    WaveformParameterPopupWindow,
)
from aslm.view.popups.autofocus_setting_popup import AutofocusPopup
from aslm.view.popups.ilastik_setting_popup import ilastik_setting_popup
from aslm.view.popups.help_popup import HelpPopup
from aslm.view.popups.camera_map_setting_popup import CameraMapSettingPopup
from aslm.controller.sub_controllers.gui_controller import GUIController
from aslm.controller.sub_controllers.help_popup_controller import HelpPopupController
from aslm.controller.sub_controllers import (
    IlastikPopupController,
    CameraMapSettingPopupController,
    AutofocusPopupController,
    WaveformPopupController,
    MicroscopePopupController,
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

        def popup_waveform_setting():
            if hasattr(self, "waveform_popup_controller"):
                self.waveform_popup_controller.showup()
                return
            waveform_constants_popup = WaveformParameterPopupWindow(
                self.view, self.configuration_controller
            )
            self.waveform_popup_controller = WaveformPopupController(
                waveform_constants_popup, self, self.waveform_constants_path
            )

            self.waveform_popup_controller.populate_experiment_values()

        def popup_microscope_setting():
            """Pop up the microscope setting window.

            Parameters
            ----------
            None

            Returns
            -------
            None
            """
            if hasattr(self, "microscope_popup_controller"):
                self.microscope_popup_controller.showup()
                return
            microscope_info = self.model.get_microscope_info()
            self.microscope_popup_controller = MicroscopePopupController(
                self.view, self, microscope_info
            )

        def popup_autofocus_setting(*args):
            """Pop up the Autofocus setting window."""
            if hasattr(self, "af_popup_controller"):
                self.af_popup_controller.showup()
                return
            af_popup = AutofocusPopup(self.view)
            self.af_popup_controller = AutofocusPopupController(af_popup, self)

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

        def add_menu_item(
            menu,
            menu_entry,
            command,
            accelerator=None,
            event_binding=None,
            underline=None,
        ):
            """Add a menu item to a menu.

            Parameters
            ----------
            menu : class
                Menu class.
            menu_entry : str
                Menu item label.
            command : function
                Function to be called when the menu item is clicked.
            accelerator : str
                Keyboard shortcut for the menu item.
            event_binding : str
                Event binding for the menu item.
            underline : int
                Index of the character to underline in the menu item label.

            Returns
            -------
            None
            """
            if menu_entry == "add_separator":
                menu.add_separator()
                return

            if platform.platform() == "Darwin":
                accelerator = accelerator.replace("Ctrl", "Command")

            menu.add_command(
                label=label,
                command=command,
                accelerator=accelerator,
                underline=underline,
            )

            menu.bind_all(accelerator, command)

        menus_dict = {
            self.view.menubar.menu_file: {
                "New Experiment": [
                    new_experiment,
                    "Ctrl+Shift+N",
                    "<Control-N>",
                    "<Control_L-N>",
                ],
                "Load Experiment": [
                    load_experiment,
                    "Ctrl+Shift+O",
                    "<Control-O>",
                    "<Control_L-O>",
                ],
                "Save Experiment": [
                    save_experiment,
                    "Ctrl+Shift+S",
                    "<Control-S>",
                    "<Control_L-S>",
                ],
                "add_separator": [None],
                "Save Data": [None, "Ctrl+s", "<Control-s>", "<Control_L-s>"],
            },
            self.view.menubar.menu_multi_positions: {
                "Move Up (X)": [None, "w", "<Key-w>", "<Key-w>"],
                "Move Down (X)": [None, "s", "<Key-s>", "<Key-s>"],
                "Move Left (Y)": [None, "a", "<Key-a>", "<Key-a>"],
                "Move Right (Y)": [None, "d", "<Key-d>", "<Key-d>"],
                "Move In (Z)": [None, "q", "<Key-q>", "<Key-q>"],
                "Move Out (Z)": [None, "e", "<Key-e>", "<Key-e>"],
                "Move Focus Up (F)": [None, "r", "<Key-r>", "<Key-r>"],
                "Move Focus Down (F)": [None, "f", "<Key-f>", "<Key-f>"],
                "Rotate Clockwise (R)": [None, "z", "<Key-z>", "<Key-z>"],
                "Rotate Counter-Clockwise (R)": [None, "x", "<Key-x>", "<Key-x>"],
                "add_separator": [None],
                "Launch Tiling Wizard": [None, None, None, None],
                "Load Positions": [
                    self.parent_controller.multiposition_tab_controller.load_positions,
                    None,
                    None,
                    None,
                ],
                "Export Positions": [
                    self.parent_controller.multiposition_tab_controller.export_positions,
                    None,
                    None,
                    None,
                ],
                "Append Current Position": [
                    self.parent_controller.multiposition_tab_controller.add_stage_position,
                    None,
                    None,
                    None,
                ],
                "Generate Positions": [
                    self.parent_controller.multiposition_tab_controller.generate_positions,
                    None,
                    None,
                    None,
                ],
                "Move to Selected Position": [
                    self.parent_controller.multiposition_tab_controller.move_to_position,
                    None,
                    None,
                    None,
                ],
            },
        }
        for menu in menus_dict:
            menu_items = menus_dict[menu]
            for label in menu_items:
                if label == "add_separator":
                    menu.add_separator()
                else:
                    menu.add_command(
                        label=label,
                        command=menu_items[label][0],
                        accelerator=menu_items[label][1],
                    )
                    if platform.platform() == "Darwin":
                        menu.bind_all(menu_items[label][3], menu_items[label][0])
                    else:
                        menu.bind_all(menu_items[label][2], menu_items[label][0])

        # load images from disk in synthetic hardware
        if is_synthetic_hardware:
            self.view.menubar.menu_file.add_separator()
            self.view.menubar.menu_file.add_command(
                label="Load Images", command=load_images
            )
            self.view.menubar.menu_file.add_command(
                label="Unload Images", command=lambda: self.model.load_images(None)
            )

        # add resolution menu
        self.resolution_value = tk.StringVar()
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

        # event binding
        self.resolution_value.trace_add(
            "write",
            lambda *args: self.execute("resolution", self.resolution_value.get()),
        )

        # add separator
        self.view.menubar.menu_resolution.add_separator()

        # waveform popup
        self.view.menubar.menu_resolution.add_command(
            label="Waveform Parameters", command=popup_waveform_setting
        )
        # microscope setting popup
        self.view.menubar.menu_resolution.add_command(
            label="Configure Microscopes", command=popup_microscope_setting
        )

        # autofocus menu
        self.view.menubar.menu_autofocus.add_command(
            label="Perform Autofocus",
            command=lambda: self.execute("autofocus"),
            accelerator="Ctrl+A",
        )
        self.view.menubar.menu_autofocus.add_command(
            label="Autofocus Settings",
            command=popup_autofocus_setting,
            accelerator="Ctrl+Shift+A",
        )

        if platform.platform == "darwin":
            self.view.bind_all("<Control_L-a>", lambda event: self.execute("autofocus"))
            self.view.bind_all("<Control_L-A>", popup_autofocus_setting)
        else:
            self.view.bind_all("<Control-a>", lambda event: self.execute("autofocus"))
            self.view.bind_all("<Control-A>", popup_autofocus_setting)

        # Window Menu
        self.view.menubar.menu_window.add_command(
            label="Channel Settings", accelerator="Ctrl+1"
        )
        self.view.menubar.menu_window.add_command(
            label="Camera Settings", accelerator="Ctrl+2"
        )
        self.view.menubar.menu_window.add_command(
            label="Stage Control", accelerator="Ctrl+3"
        )
        self.view.menubar.menu_window.add_command(
            label="Multiposition Table", accelerator="Ctrl+4"
        )
        self.view.menubar.menu_window.add_separator()
        self.view.menubar.menu_window.add_command(label="Popout Camera Display")

        # Help menu
        self.view.menubar.menu_help.add_command(label="Help", command=popup_help)

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
        self.feature_id_val = tk.IntVar(0)
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
