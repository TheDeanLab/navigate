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
from aslm.view.popups.autofocus_setting_popup import AutofocusPopup
from aslm.view.popups.camera_map_setting_popup import CameraMapSettingPopup
from aslm.view.popups.waveform_parameter_popup_window import WaveformParameterPopupWindow
from aslm.view.popups.feature_list_popup import FeatureListPopup
from aslm.controller.sub_controllers.gui_controller import GUIController
from aslm.controller.sub_controllers import (
    AutofocusPopupController,
    IlastikPopupController,
    CameraMapSettingPopupController,
    WaveformPopupController,
    MicroscopePopupController,
    FeaturePopupController,
    HelpPopupController
)
from aslm.tools.file_functions import save_yaml_file, load_yaml_file
from aslm.tools.decorators import FeatureList
from aslm.tools.common_functions import load_module_from_file
from aslm.config.config import get_aslm_path


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class FakeEvent:
    """Fake event class for keyboard shortcuts"""

    def __init__(self, char=None, keysym=None):
        self.char = char
        self.keysym = keysym
        self.state = 0


class MenuController(GUIController):
    def __init__(self, view, parent_controller=None):
        super().__init__(view, parent_controller)
        self.parent_controller = parent_controller
        self.view = view
        self.resolution_value = tk.StringVar()
        self.feature_id_val = tk.IntVar(0)
        self.disable_stage_limits = tk.IntVar(0)
        self.save_data = False
        self.feature_list_count = 0
        self.feature_list_file_name = "feature_lists.yaml"

    def initialize_menus(self):
        """Initialize menus
        This function defines all the menus in the menubar

        Parameters
        ----------
        None

        Returns
        -------
        configuration_controller : class
            Camera view sub-controller.

        """

        # File Menu
        file_menu = {
            self.view.menubar.menu_file: {
                "New Experiment": [
                    "standard",
                    self.new_experiment,
                    "Ctrl+Shift+N",
                    "<Control-N>",
                    "<Control_L-N>",
                ],
                "Load Experiment": [
                    "standard",
                    self.load_experiment,
                    "Ctrl+Shift+O",
                    "<Control-O>",
                    "<Control_L-O>",
                ],
                "Save Experiment": [
                    "standard",
                    self.save_experiment,
                    "Ctrl+Shift+S",
                    "<Control-S>",
                    "<Control_L-S>",
                ],
                "add_separator": [None],
                "Save Data": [
                    "standard",
                    self.toggle_save,
                    "Ctrl+s",
                    "<Control-s>",
                    "<Control_L-s>",
                ],
                "Acquire Data": [
                    "standard",
                    self.acquire_data,
                    "Ctrl+Enter",
                    "<Control-Return>",
                    "<Control_L-Return>",
                ],
                "Load Images": ["standard", self.load_images, None, None, None],
                "Unload Images": [
                    "standard",
                    lambda: self.parent_controller.model.load_images(None),
                    None,
                    None,
                    None,
                ],
            }
        }
        self.populate_menu(file_menu)

        # Stage Control Menu
        # Most bindings are implemented in the keystroke_controller.
        # Accelerators added here to communicate them to users. Could move those key
        # bindings here? Not sure...
        stage_control_menu = {
            self.view.menubar.menu_multi_positions: {
                "Move Up": [
                    "standard",
                    lambda *args: self.stage_movement("w"),
                    "w",
                    "<Key-w>",
                    "<Key-w>",
                ],
                "Move Down": [
                    "standard",
                    lambda *args: self.stage_movement("s"),
                    "s",
                    "<Key-s>",
                    "<Key-s>",
                ],
                "Move Left": [
                    "standard",
                    lambda *args: self.stage_movement("a"),
                    "a",
                    "<Key-a>",
                    "<Key-a>",
                ],
                "Move Right": [
                    "standard",
                    lambda *args: self.stage_movement("d"),
                    "d",
                    "<Key-d>",
                    "<Key-d>",
                ],
                "Move In": ["standard", self.not_implemented, None, None, None],
                "Move Out": ["standard", self.not_implemented, None, None, None],
                "Move Focus Up": ["standard", self.not_implemented, None, None, None],
                "Move Focus Down": ["standard", self.not_implemented, None, None, None],
                "Rotate Clockwise": ["standard", self.not_implemented, None, None, None],
                "Rotate Counter-Clockwise": [
                    "standard",
                    self.not_implemented,
                    None,
                    None,
                    None,
                ],
                "add_separator": ["standard", None, None, None, None],
                "Launch Tiling Wizard": [
                    "standard",
                    self.parent_controller.channels_tab_controller.launch_tiling_wizard,
                    None,
                    None,
                    None,
                ],
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
        self.populate_menu(stage_control_menu)
        self.view.menubar.menu_multi_positions.add_radiobutton(
            label="Disable Stage Limits",
            value=0,
            command=self.toggle_stage_limits,
            variable=self.disable_stage_limits,
        )
        self.view.menubar.menu_multi_positions.add_radiobutton(
            label="Enable Stage Limits",
            value=1,
            command=self.toggle_stage_limits,
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
                    self.popup_autofocus_setting,
                    "Ctrl+Shift+A",
                    "<Control-A>",
                    "<Control_L-A>",
                ],
            }
        }
        self.populate_menu(autofocus_menu)

        # Window menu
        windows_menu = {
            self.view.menubar.menu_window: {
                "Channel Settings": [
                    "standard",
                    lambda: self.switch_tabs(1),
                    "Ctrl+1",
                    "<Control-1>",
                    "<Control_L-1",
                ],
                "Camera Settings": [
                    "standard",
                    lambda: self.switch_tabs(2),
                    "Ctrl+2",
                    "<Control-2>",
                    "<Control_L-2",
                ],
                "Stage Control": [
                    "standard",
                    lambda: self.switch_tabs(2),
                    "Ctrl+3",
                    "<Control-3>",
                    "<Control_L-3",
                ],
                "Multiposition Table": [
                    "standard",
                    lambda: self.switch_tabs(4),
                    "Ctrl+4",
                    "<Control-4>",
                    "<Control_L-4",
                ],
                "add_separator": ["standard", None, None, None, None],
                "Popout Camera Display": [
                    "standard",
                    self.not_implemented,
                    None,
                    None,
                    None,
                ],
                "Help": ["standard", self.popup_help, None, None, None],
            }
        }
        self.populate_menu(windows_menu)

        # Zoom menu
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
            lambda *args: self.parent_controller.execute("resolution", self.resolution_value.get()),
        )

        configuration_dict = {
            self.view.menubar.menu_resolution: {
                "add_separator": [None, None, None, None, None],
                "Waveform Parameters": [
                    "standard",
                    self.popup_waveform_setting,
                    None,
                    None,
                    None,
                ],
                "Configure Microscope": [
                    "standard",
                    self.popup_microscope_setting,
                    None,
                    None,
                    None,
                ],
            }
        }
        self.populate_menu(configuration_dict)

        # add-on features
        feature_list = [
            "None",
            "Switch Resolution",
            "Z Stack Acquisition",
            "Threshold",
            "Ilastik Segmentation",
            "Volume Search",
            "Time Series",
            "Decoupled Focus Stage Multiposition",
        ]
        self.feature_list_count = len(feature_list)
        for i in range(self.feature_list_count):
            self.view.menubar.menu_features.add_radiobutton(
                label=feature_list[i], variable=self.feature_id_val, value=i
            )
        self.feature_id_val.trace_add(
            "write",
            lambda *args: self.parent_controller.execute("load_feature", self.feature_id_val.get()),
        )
        self.view.menubar.menu_features.add_separator()
        self.view.menubar.menu_features.add_command(
            label="Ilastik Settings", command=self.popup_ilastik_setting
        )
        # disable ilastik menu
        self.view.menubar.menu_features.entryconfig(
            "Ilastik Segmentation", state="disabled"
        )
        self.view.menubar.menu_features.add_command(
            label="Camera offset and variance maps", command=self.popup_camera_map_setting
        )
        self.view.menubar.menu_features.add_command(
            label="Load Customized Feature List",
            command=self.load_feature_list
        )
        self.view.menubar.menu_features.add_command(
            label="Add Customized Feature List",
            command=self.popup_feature_list_setting
        )
        self.view.menubar.menu_features.add_separator()
        # add feature lists from previous loaded ones
        feature_list_path = get_aslm_path() + "/config/" + self.feature_list_file_name
        feature_records = load_yaml_file(feature_list_path)
        if feature_records:
            for feature in feature_records:
                self.view.menubar.menu_features.add_radiobutton(
                    label=feature["feature_list_name"], variable=self.feature_id_val, value=self.feature_list_count
                )
                self.feature_list_count += 1


    def populate_menu(self, menu_dict):
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

    def new_experiment(self, *args):
        """Create a new experiment file."""
        self.parent_controller.populate_experiment_setting(
            self.parent_controller.default_experiment_file
        )

    def load_experiment(self, *args):
        """Load an experiment file."""
        filename = tk.filedialog.askopenfilename(
            defaultextension=".yml", filetypes=[("Yaml files", "*.yml *.yaml")]
        )
        if not filename:
            return
        self.parent_controller.populate_experiment_setting(filename)

    def save_experiment(self, *args):
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

    def load_images(self):
        """Load images from a file."""
        filenames = tk.filedialog.askopenfilenames(
            defaultextension=".tif", filetypes=[("tiff files", "*.tif *.tiff")]
        )
        if not filenames:
            return
        self.parent_controller.model.load_images(filenames)

    def popup_camera_map_setting(self):
        """Pop up the Camera Map setting window."""
        if hasattr(self.parent_controller, "camera_map_popup_controller"):
            self.parent_controller.camera_map_popup_controller.showup()
            return
        map_popup = CameraMapSettingPopup(self.view)
        self.parent_controller.camera_map_popup_controller = CameraMapSettingPopupController(
            map_popup, self.parent_controller
        )

    def popup_ilastik_setting(self):
        """Pop up the Ilastik setting window."""
        ilastik_popup_window = ilastik_setting_popup(self.view)
        ilastik_url = self.parent_controller.configuration["rest_api_config"][
            "Ilastik"
        ]["url"]
        if hasattr(self.parent_controller, "ilastik_controller"):
            self.parent_controller.ilastik_controller.showup(ilastik_popup_window)
        else:
            self.parent_controller.ilastik_controller = IlastikPopupController(
                ilastik_popup_window, self.parent_controller, ilastik_url
            )

    def popup_help(self):
        """Pop up the help window."""
        if hasattr(self.parent_controller, "help_controller"):
            self.parent_controller.help_controller.showup()
            return
        help_pop = HelpPopup(self.view)
        self.parent_controller.help_controller = HelpPopupController(help_pop, self.parent_controller)

    def toggle_stage_limits(self, *args):
        """Toggle stage limits."""
        if self.disable_stage_limits.get() == 1:
            logger.debug("Disabling stage limits")
            self.parent_controller.execute("stage_limits", True)
        else:
            logger.debug("Enabling stage limits")
            self.parent_controller.execute("stage_limits", False)

    def popup_autofocus_setting(self, *args):
        """Pop up the Autofocus setting window."""
        if hasattr(self.parent_controller, "af_popup_controller"):
            self.parent_controller.af_popup_controller.showup()
            return
        af_popup = AutofocusPopup(self.view)
        self.parent_controller.af_popup_controller = AutofocusPopupController(af_popup, self.parent_controller)

    def popup_waveform_setting(self):
        if hasattr(self.parent_controller, "waveform_popup_controller"):
            self.parent_controller.waveform_popup_controller.showup()
            return
        waveform_constants_popup = WaveformParameterPopupWindow(
            self.view, self.parent_controller.configuration_controller
        )
        waveform_popup_controller = WaveformPopupController(
            waveform_constants_popup, self.parent_controller, self.parent_controller.waveform_constants_path
        )
        waveform_popup_controller.populate_experiment_values()
        self.parent_controller.waveform_popup_controller = waveform_popup_controller

    def popup_microscope_setting(self):
        """Pop up the microscope setting window.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if hasattr(self.parent_controller, "microscope_popup_controller"):
            self.parent_controller.microscope_popup_controller.showup()
            return
        microscope_info = self.parent_controller.model.get_microscope_info()
        self.parent_controller.microscope_popup_controller = MicroscopePopupController(
            self.view, self.parent_controller, microscope_info
        )
    
    def toggle_save(self, *args):
        """Save the data."""
        self.save_data = not self.save_data
        self.parent_controller.execute("set_save", self.save_data)

    def acquire_data(self, *args):
        """Acquire data/Stop acquiring data."""
        self.parent_controller.acquire_bar_controller.launch_popup_window()

    def not_implemented(self, *args):
        """Not implemented."""
        print("Not implemented")

    def stage_movement(self, char):
        """Stage movement."""
        fake_event = FakeEvent(char=char)
        self.parent_controller.stage_controller.stage_key_press(fake_event)

    def switch_tabs(self, tab):
        """Switch tabs."""
        self.parent_controller.view.settings.select(tab - 1)


    def popup_feature_list_setting(self):
        feature_list_popup = FeatureListPopup(self.view, title="This is a test!")
        self.parent_controller.features_popup_controller = FeaturePopupController(feature_list_popup, self.parent_controller)

    def load_feature_list(self):
        filename = tk.filedialog.askopenfilename(
            defaultextension=".py", filetypes=[("Python files", "*.py")]
        )
        if not filename:
            return
        module = load_module_from_file(filename[filename.rindex("/")+1:], filename)
        features = [f for f in dir(module) if isinstance(getattr(module, f), FeatureList)]
        config_path = get_aslm_path() + "/config"
        feature_records = load_yaml_file(f"{config_path}/{self.feature_list_file_name}")
        if not feature_records:
            feature_records = []
        added_features = []
        for name in features:
            feature = getattr(module, name)
            feature_list_name = feature.feature_list_name
            add_flag = True
            for i, item in enumerate(feature_records):
                if item["feature_list_name"] == feature_list_name:
                    print("There is already one feature list named as", \
                          feature_list_name, \
                          "The new one isn't loaded!")
                    add_flag = False
                    break
            if add_flag:
                self.view.menubar.menu_features.add_radiobutton(
                    label=feature_list_name, variable=self.feature_id_val, value=self.feature_list_count
                )
                feature_records.append({
                    "module_name": name,
                    "feature_list_name": feature_list_name,
                    "filename": filename
                })
                self.feature_list_count += 1
                added_features.append(name)
        # tell model to add feature lists
        self.parent_controller.model.load_feature_list_from_file(filename, added_features)
        # save feature records
        save_yaml_file(config_path, feature_records, self.feature_list_file_name)
