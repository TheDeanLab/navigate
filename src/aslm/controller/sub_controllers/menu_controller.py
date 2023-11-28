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
import os
import tkinter as tk
from tkinter import messagebox
import subprocess

# Third Party Imports

# Local Imports
from aslm.view.popups.ilastik_setting_popup import ilastik_setting_popup
from aslm.view.popups.help_popup import HelpPopup
from aslm.view.popups.autofocus_setting_popup import AutofocusPopup
from aslm.view.popups.adaptiveoptics_popup import AdaptiveOpticsPopup
from aslm.view.popups.camera_map_setting_popup import CameraMapSettingPopup
from aslm.view.popups.waveform_parameter_popup_window import (
    WaveformParameterPopupWindow,
)
from aslm.view.popups.feature_list_popup import FeatureListPopup
from aslm.controller.sub_controllers.gui_controller import GUIController
from aslm.controller.sub_controllers import (
    AutofocusPopupController,
    IlastikPopupController,
    CameraMapSettingPopupController,
    WaveformPopupController,
    MicroscopePopupController,
    FeaturePopupController,
    HelpPopupController,
    FeatureAdvancedSettingController,
    AdaptiveOpticsPopupController,
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
        """Initialize FakeEvent

        Parameters
        ----------
        char: str
            The character that was pressed.
        keysym: str
            The key that was pressed.
        """
        #: str: The character that was pressed.
        self.char = char
        #: str: The key that was pressed.
        self.keysym = keysym
        #: int: The state of the keyboard.
        self.state = 0


class MenuController(GUIController):
    """Menu controller class."""

    def __init__(self, view, parent_controller=None):
        """Initialize MenuController

        Parameters
        ----------
        view: class
            The view class.
        parent_controller
            The parent controller.
        """
        super().__init__(view, parent_controller)
        #: Controller: The parent controller.
        self.parent_controller = parent_controller
        #: tk.canvas: The view class.
        self.view = view
        #: tkinter.StringVar: Resolution value.
        self.resolution_value = tk.StringVar()
        #: tkinter.IntVar: Feature id value.
        self.feature_id_val = tk.IntVar()
        #: tkinter.IntVar: Disable stage limits.
        self.disable_stage_limits = tk.IntVar()
        #: FakeEvent: Fake event.
        self.fake_event = None
        #: list: List of feature list names.
        self.feature_list_names = []
        #: int: System feature list count.
        self.system_feature_list_count = 0
        #: int: Feature list count.
        self.feature_list_count = 0
        #: str: Feature list file name.
        self.feature_list_file_name = "feature_lists.yaml"

    def initialize_menus(self):
        """Initialize menus
        This function defines all the menus in the menubar

        Each menu item is initialized as a dictionary entry that is associated with
        a list that provides the following parameters:

        Menu item name: name of the menu item. If the name is specified as
        add_separator, then a separator is added to the menu.

        List of parameters:
            Type of entry: standard, checkbutton, radiobutton, cascade
            Function: function to be called when menu item is selected
            Accelerator: keyboard shortcut
            Bindings: keyboard shortcut bindings for Windows
            Bindings: keyboard shortcut bindings for Mac

        Example:
            "Acquire Data": [
                "standard",
                self.acquire_data,
                "Ctrl+Enter",
                "<Control-Return>",
                "<Control_L-Return>",
            ]

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
                "Toggle Save Data": [
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
                "add_separator_1": [None, None, None, None, None],
                "Open Log Files": ["standard", self.open_log_files, None, None, None],
                "Open Configuration Files": [
                    "standard",
                    self.open_configuration_files,
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
                "Rotate Clockwise": [
                    "standard",
                    self.not_implemented,
                    None,
                    None,
                    None,
                ],
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
                    self.parent_controller.multiposition_tab_controller.export_positions,  # noqa: E501
                    None,
                    None,
                    None,
                ],
                "Append Current Position": [
                    "standard",
                    self.parent_controller.multiposition_tab_controller.add_stage_position,  # noqa: E501
                    None,
                    None,
                    None,
                ],
                "Generate Positions": [
                    "standard",
                    self.parent_controller.multiposition_tab_controller.generate_positions,  # noqa: E501
                    None,
                    None,
                    None,
                ],
                "Move to Selected Position": [
                    "standard",
                    self.parent_controller.multiposition_tab_controller.move_to_position,  # noqa: E501
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
            value=1,
            command=self.toggle_stage_limits,
            variable=self.disable_stage_limits,
        )
        self.view.menubar.menu_multi_positions.add_radiobutton(
            label="Enable Stage Limits",
            value=0,
            command=self.toggle_stage_limits,
            variable=self.disable_stage_limits,
        )

        # autofocus menu
        autofocus_menu = {
            self.view.menubar.menu_autofocus: {
                "Perform Autofocus": [
                    "standard",
                    lambda x: self.parent_controller.execute("autofocus"),
                    "Ctrl+Shift+A",
                    "<Control-A>",
                    "<Control_L-A>",
                ],
                "Autofocus Settings": [
                    "standard",
                    self.popup_autofocus_setting,
                    "Ctrl+Alt+Shift+A",
                    "<Control-Alt-A>",
                    "<Command-Alt-Key-A>",
                ],
            }
        }
        self.populate_menu(autofocus_menu)

        # Window menu
        windows_menu = {
            self.view.menubar.menu_window: {
                "Channel Settings": [
                    "standard",
                    lambda event: self.switch_tabs(1),
                    "Ctrl+1",
                    "<Control-Key-1>",
                    "<Control_L-Key-1",
                ],
                "Camera Settings": [
                    "standard",
                    lambda event: self.switch_tabs(2),
                    "Ctrl+2",
                    "<Control-Key-2>",
                    "<Control_L-Key-2",
                ],
                "Stage Control": [
                    "standard",
                    lambda event: self.switch_tabs(3),
                    "Ctrl+3",
                    "<Control-Key-3>",
                    "<Control_L-Key-3",
                ],
                "Multiposition Table": [
                    "standard",
                    lambda event: self.switch_tabs(4),
                    "Ctrl+4",
                    "<Control-Key-4>",
                    "<Control_L-Key-4",
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
            lambda *args: self.parent_controller.execute(
                "resolution", self.resolution_value.get()
            ),
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
        self.feature_list_names = [
            "None",
            "Switch Resolution",
            "Z Stack Acquisition",
            "Threshold",
            "Ilastik Segmentation",
            "Volume Search",
            "Time Series",
            "Decoupled Focus Stage Multiposition",
            "Remove Empty Tiles",
        ]
        self.feature_list_count = len(self.feature_list_names)
        self.system_feature_list_count = self.feature_list_count

        for i in range(self.feature_list_count):
            self.view.menubar.menu_features.add_radiobutton(
                label=self.feature_list_names[i], variable=self.feature_id_val, value=i
            )
        self.feature_id_val.trace_add(
            "write",
            lambda *args: self.parent_controller.execute(
                "load_feature", self.feature_id_val.get()
            ),
        )

        # add adaptive optics as standalone pop-up for now (if mirror is real, otherwise don't)
        if not self.parent_controller.model.active_microscope.mirror.is_synthetic:
            self.view.menubar.menu_features.add_separator()
            self.view.menubar.menu_features.add_command(
                label="Adaptive Optics", command=self.popup_adaptiveoptics
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
            label="Camera offset and variance maps",
            command=self.popup_camera_map_setting,
        )
        self.view.menubar.menu_features.add_command(
            label="Load Customized Feature List", command=self.load_feature_list
        )
        self.view.menubar.menu_features.add_command(
            label="Add Customized Feature List", command=self.popup_feature_list_setting
        )
        self.view.menubar.menu_features.add_command(
            label="Delete Selected Feature List", command=self.delete_feature_list
        )
        self.view.menubar.menu_features.add_command(
            label="Advanced Setting", command=self.popup_feature_advanced_setting
        )
        self.view.menubar.menu_features.add_separator()
        # add feature lists from previous loaded ones
        feature_lists_path = get_aslm_path() + "/feature_lists"
        if not os.path.exists(feature_lists_path):
            os.makedirs(feature_lists_path)
            return
        # get __sequence.yml
        feature_records = load_yaml_file(f"{feature_lists_path}/__sequence.yml")
        if not feature_records:
            return

        for feature in feature_records:
            self.view.menubar.menu_features.add_radiobutton(
                label=feature["feature_list_name"],
                variable=self.feature_id_val,
                value=self.feature_list_count,
            )
            self.feature_list_names.append(feature["feature_list_name"])
            self.feature_list_count += 1

    def toggle_save(self, *args):
        """Toggle save button

        Parameters
        ----------
        args:
            could be tkinter event(Key press event)

        """
        save_data = (
            self.view.settings.channels_tab.stack_timepoint_frame.save_data.get()
        )

        self.parent_controller.channels_tab_controller.timepoint_vals["is_save"].set(
            not save_data
        )
        self.parent_controller.channels_tab_controller.update_save_setting()

    def open_folder(self, path):
        """Open folder in file explorer.

        Parameters
        ----------
        path : str
            Path to folder.
        """
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.check_call(["open", "--", path])
            elif platform.system() == "Windows":  # Windows
                subprocess.check_call(["explorer", path])
            else:
                print("Unsupported platform.")
        except subprocess.CalledProcessError:
            pass

    def open_log_files(self):
        """Open log files folder."""
        path = os.path.join(get_aslm_path(), "logs")
        self.open_folder(path)

    def open_configuration_files(self):
        """Open configuration files folder."""
        path = os.path.join(get_aslm_path(), "config")
        self.open_folder(path)

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
        save_yaml_file("", self.parent_controller.configuration["experiment"], filename)

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
        self.parent_controller.camera_map_popup_controller = (
            CameraMapSettingPopupController(map_popup, self.parent_controller)
        )

    def popup_adaptiveoptics(self):
        if hasattr(self.parent_controller, 'adaptiveoptics_popup_controller'):
            self.parent_controller.ao_popup_controller.showup()
            return
        ao_popup = AdaptiveOpticsPopup(self.view)
        self.parent_controller.ao_popup_controller = AdaptiveOpticsPopupController(
            ao_popup, self.parent_controller
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
        self.parent_controller.help_controller = HelpPopupController(
            help_pop, self.parent_controller
        )

    def toggle_stage_limits(self, *args):
        """Toggle stage limits."""
        if self.disable_stage_limits.get() == 1:
            self.parent_controller.configuration["experiment"]["StageParameters"][
                "limits"
            ] = False
            logger.debug("Disabling stage limits")
            self.parent_controller.execute("stage_limits", False)
        else:
            self.parent_controller.configuration["experiment"]["StageParameters"][
                "limits"
            ] = True
            logger.debug("Enabling stage limits")
            self.parent_controller.execute("stage_limits", True)

    def popup_autofocus_setting(self, *args):
        """Pop up the Autofocus setting window."""
        if hasattr(self.parent_controller, "af_popup_controller"):
            self.parent_controller.af_popup_controller.showup()
            return
        af_popup = AutofocusPopup(self.view)
        self.parent_controller.af_popup_controller = AutofocusPopupController(
            af_popup, self.parent_controller
        )

    def popup_waveform_setting(self):
        if hasattr(self.parent_controller, "waveform_popup_controller"):
            self.parent_controller.waveform_popup_controller.showup()
            return
        waveform_constants_popup = WaveformParameterPopupWindow(
            self.view, self.parent_controller.configuration_controller
        )
        waveform_popup_controller = WaveformPopupController(
            waveform_constants_popup,
            self.parent_controller,
            self.parent_controller.waveform_constants_path,
        )
        waveform_popup_controller.populate_experiment_values()
        self.parent_controller.waveform_popup_controller = waveform_popup_controller

    def popup_microscope_setting(self):
        """Pop up the microscope setting window."""
        if hasattr(self.parent_controller, "microscope_popup_controller"):
            self.parent_controller.microscope_popup_controller.showup()
            return
        microscope_info = self.parent_controller.model.get_microscope_info()
        self.parent_controller.microscope_popup_controller = MicroscopePopupController(
            self.view, self.parent_controller, microscope_info
        )

    def acquire_data(self, *args):
        """Acquire data/Stop acquiring data."""
        self.parent_controller.acquire_bar_controller.launch_popup_window()

    def not_implemented(self, *args):
        """Not implemented."""
        print("Not implemented")

    def stage_movement(self, char):
        """Stage movement.

        Should not be run if we are in a validated combobox, or a validate entry.

        Parameters
        ----------
        char: str
            The character that was pressed.
        """
        try:
            focus = self.parent_controller.view.focus_get()
            if hasattr(focus, "widgetName"):
                freeze_in = ["ttk::entry", "ttk::combobox", "text", "ttk::spinbox"]
                if focus.widgetName in freeze_in:
                    return
            self.fake_event = FakeEvent(char=char)
            self.parent_controller.stage_controller.stage_key_press(self.fake_event)
        except KeyError:
            # Avoids KeyError if the user is in a popdown menu.
            pass

    def switch_tabs(self, tab):
        """Switch tabs."""
        self.parent_controller.view.settings.select(tab - 1)

    def popup_feature_list_setting(self):
        """Show feature list popup window"""
        feature_list_popup = FeatureListPopup(self.view, title="Add New Feature List")
        self.parent_controller.features_popup_controller = FeaturePopupController(
            feature_list_popup, self.parent_controller
        )

    def load_feature_list(self):
        """Load feature lists from a python file"""
        filename = tk.filedialog.askopenfilename(
            defaultextension=".py", filetypes=[("Python files", "*.py")]
        )
        if not filename:
            return
        module = load_module_from_file(filename[filename.rindex("/") + 1 :], filename)
        features = [
            f for f in dir(module) if isinstance(getattr(module, f), FeatureList)
        ]
        feature_lists_path = get_aslm_path() + "/feature_lists"
        feature_list_files = [
            temp
            for temp in os.listdir(feature_lists_path)
            if (temp.endswith(".yml") or temp.endswith(".yaml"))
            and os.path.isfile(os.path.join(feature_lists_path, temp))
        ]
        feature_records = load_yaml_file(f"{feature_lists_path}/__sequence.yml")
        if not feature_records:
            feature_records = []
        added_features = []
        for name in features:
            feature = getattr(module, name)
            feature_list_name = feature.feature_list_name
            if (
                f"{feature_list_name}.yml" in feature_list_files
                or f"{feature_list_name}.yaml" in feature_list_files
            ):
                print(
                    "There is already one feature list named as",
                    feature_list_name,
                    "The new one isn't loaded!",
                )
                continue
            self.view.menubar.menu_features.add_radiobutton(
                label=feature_list_name,
                variable=self.feature_id_val,
                value=self.feature_list_count,
            )
            save_yaml_file(
                feature_lists_path,
                {
                    "module_name": name,
                    "feature_list_name": feature_list_name,
                    "filename": filename,
                },
                f"{'_'.join(feature_list_name.split(' '))}.yml",
            )

            feature_records.append(
                {
                    "feature_list_name": feature_list_name,
                    "yaml_file_name": "_".join(feature_list_name.split(" ")) + ".yml",
                }
            )
            self.feature_list_names.append(feature_list_name)
            self.feature_list_count += 1
            added_features.append(name)

        save_yaml_file(feature_lists_path, feature_records, "__sequence.yml")
        # tell model to add feature lists
        self.parent_controller.model.load_feature_list_from_file(
            filename, added_features
        )

    def add_feature_list(self, feature_list_name, feature_list_str):
        """Add feature list to the software and system yaml files

        Parameters
        ----------
        feature_list_name: str
            feature list name
        feature_list_str: str
            string of a feature list

        Returns
        -------
        result : bool
            True: add feature list successfully
            False: failed
        """
        feature_lists_path = get_aslm_path() + "/feature_lists"
        if os.path.exists(f"{feature_lists_path}/{'_'.join(feature_list_name)}.yml"):
            return False
        self.view.menubar.menu_features.add_radiobutton(
            label=feature_list_name,
            variable=self.feature_id_val,
            value=self.feature_list_count,
        )
        self.feature_list_names.append(feature_list_name)
        self.feature_list_count += 1
        save_yaml_file(
            feature_lists_path,
            {
                "module_name": None,
                "feature_list_name": feature_list_name,
                "feature_list": feature_list_str,
            },
            f"{'_'.join(feature_list_name.split(' '))}.yml",
        )
        feature_records = load_yaml_file(f"{feature_lists_path}/__sequence.yml")
        feature_records.append(
            {
                "feature_list_name": feature_list_name,
                "yaml_file_name": "_".join(feature_list_name.split(" ")) + ".yml",
            }
        )
        # tell model to add feature lists
        self.parent_controller.model.load_feature_list_from_str(feature_list_str)
        # save feature records
        save_yaml_file(feature_lists_path, feature_records, "__sequence.yml")
        return True

    def delete_feature_list(self):
        """Delete a selected customized feature list from the software and system
        yaml file"""
        feature_id = self.feature_id_val.get()
        if feature_id < self.system_feature_list_count:
            messagebox.showerror(
                title="Feature List Error",
                message="Can't delete system feature list or you haven't select any "
                "feature list",
            )
            return

        feature_list_name = self.feature_list_names[feature_id]
        self.view.menubar.menu_features.delete(feature_list_name)

        # remove from yaml file
        feature_lists_path = get_aslm_path() + "/feature_lists"
        feature_records = load_yaml_file(f"{feature_lists_path}/__sequence.yml")
        temp = feature_records[feature_id - self.system_feature_list_count]
        os.remove(f"{feature_lists_path}/{temp['yaml_file_name']}")

        del feature_records[feature_id - self.system_feature_list_count]
        save_yaml_file(feature_lists_path, feature_records, "__sequence.yml")

    def popup_feature_advanced_setting(self):
        """Show feature advanced setting window"""
        self.parent_controller.feature_advanced_setting_controller = (
            FeatureAdvancedSettingController(self.view, self.parent_controller)
        )
