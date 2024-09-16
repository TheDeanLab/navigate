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

# Standard library imports
import inspect
import os
import re
from tkinter import filedialog, messagebox

# Third-party imports

# Local application imports
from navigate.model.features import feature_related_functions
from navigate.view.popups.feature_list_popup import FeatureAdvancedSettingPopup
from navigate.tools.file_functions import load_yaml_file, save_yaml_file
from navigate.tools.common_functions import load_module_from_file
from navigate.config.config import get_navigate_path


class FeatureAdvancedSettingController:
    """Controller for feature advanced setting popup window"""

    def __init__(self, parent_view, parent_controller):
        """Initialize the Advanced Setting Controller

        Parameters
        ----------
        parent_view : tkinter.Toplevel
            The parent view of the popup window
        parent_controller : navigate.controller.main_controller.MainController
            The parent controller of the popup window
        """
        self.parent_controller = parent_controller

        # get all feature names
        #: list[str]: A list of all feature names
        self.feature_names = []
        temp = dir(feature_related_functions)
        for t in temp:
            if inspect.isclass(getattr(feature_related_functions, t)):
                self.feature_names.append(t)

        #: FeatureAdvancedSettingPopup: The popup window
        self.popup = FeatureAdvancedSettingPopup(
            parent_view, features=self.feature_names, title="Advanced Setting"
        )
        self.popup.feature_name_widget.widget.bind(
            "<<ComboboxSelected>>", lambda event: self.refresh_popup_window(self.popup)
        )
        self.popup.popup.protocol("WM_DELETE_WINDOW", self.exit_func)

    def refresh_popup_window(self, popup):
        """Refresh the popup window

        Parameters
        ----------
        popup : FeatureAdvancedSettingPopup
            The popup window
        """
        feature_name = popup.feature_name_widget.get()
        new_feature = getattr(feature_related_functions, feature_name)
        # load feature parameter setting
        feature_config_path = (
            f"{get_navigate_path()}/"
            f"feature_lists/feature_parameter_setting"
            f"/{new_feature.__name__}.yml"
        )
        feature_parameter_config = None
        if os.path.exists(feature_config_path):
            feature_parameter_config = load_yaml_file(feature_config_path)
        spec = inspect.getfullargspec(new_feature)
        popup.build_widgets(spec.args[2:], feature_parameter_config)

        # bind events
        for arg_name in popup.inputs.keys():
            self.popup.buttons[arg_name].config(command=self.add_new_row(arg_name))
            for widgets in popup.inputs[arg_name]:
                if widgets:
                    # load button
                    widgets[2].config(
                        command=self.get_function_from_file(
                            arg_name, widgets[0], widgets[1]
                        )
                    )
        if self.popup.save_button:
            self.popup.save_button.config(command=self.save_parameters)

    def get_function_from_file(self, arg_name, ref_widget, value_widget):
        """Get the function from the given file

        Parameters
        ----------
        arg_name : str
            The argument name
        ref_widget : tkinter.Entry
            The reference widget
        value_widget : tkinter.Entry
            The value widget

        Returns
        -------
        function
            The function
        """

        def func():
            """Get the function from the given file"""
            function_name = value_widget.get()
            filename = filedialog.askopenfilename(
                defaultextension=".py", filetypes=[("Python Files", "*.py")]
            )

            # verify if the file has the given function
            if self.is_valid_function(function_name, filename):
                messagebox.showwarning(
                    title="Warning",
                    message="Please enter a valid function name and make "
                    "sure the python file contains this function!",
                )
                return
            value_widget.set(filename)

        return func

    def add_new_row(self, arg_name):
        """Add a new row to the popup window

        Parameters
        ----------
        arg_name : str
            The argument name

        Returns
        -------
        function
            The function
        """

        def func():
            """Add a new row to the popup window"""
            self.popup.add_new_row(arg_name)
            widgets = self.popup.inputs[arg_name][-1]
            widgets[2].config(
                command=self.get_function_from_file(arg_name, widgets[0], widgets[1])
            )

        return func

    def save_parameters(self):
        """Save the parameters to yaml file"""
        unloaded_functions = []
        feature_parameter_config = {}
        for arg_name in self.popup.inputs.keys():
            for row in self.popup.inputs[arg_name]:
                if row and row[0].get().strip():
                    if self.is_valid_function(row[0].get(), row[1].get()):
                        if not feature_parameter_config.get(arg_name, None):
                            feature_parameter_config[arg_name] = {}
                        if row[1].get() == "None":
                            feature_parameter_config[arg_name][row[0].get()] = None
                        else:
                            feature_parameter_config[arg_name][row[0].get()] = row[
                                1
                            ].get()
                    else:
                        unloaded_functions.append(row[0].get())

        # save to yaml file
        parameter_config_path = (
            get_navigate_path() + "/feature_lists/feature_parameter_setting"
        )
        if not os.path.exists(parameter_config_path):
            os.mkdir(parameter_config_path)
        save_yaml_file(
            parameter_config_path,
            feature_parameter_config,
            self.popup.feature_name_widget.get() + ".yml",
        )
        if unloaded_functions:
            if len(unloaded_functions) == 1:
                alert_message = f"Function {unloaded_functions[0]} isn't loaded!"
            else:
                alert_message = (
                    f"Functions {', '.join(unloaded_functions)} are not loaded!"
                )
            messagebox.showwarning(title="Warning", message=alert_message)
        self.popup.popup.attributes("-topmost", 1)

    def exit_func(self):
        """Exit the popup window"""
        self.save_parameters()
        self.popup.popup.dismiss()

    def is_valid_function(self, function_name, filename):
        """Verify if the given function is valid

        Parameters
        ----------
        function_name : str
            The function name
        filename : str
            The file name

        Returns
        -------
        bool
            True if the function is valid, False otherwise
        """
        if function_name and re.match(r"^[a-zA-Z_]\w*$", function_name) and filename:
            if function_name == "None" or filename == "None":
                return True
            module = load_module_from_file(function_name, filename)
            return module and hasattr(module, function_name)
        return False
