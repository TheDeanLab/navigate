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

# Standard library imports
import tkinter as tk
from tkinter import messagebox
import inspect
import json
import os

# Third party imports
from PIL import Image, ImageTk

# Local application imports
from navigate.view.popups.feature_list_popup import FeatureIcon, FeatureConfigPopup
from navigate.view.custom_widgets.ArrowLabel import ArrowLabel
from navigate.controller.sub_controllers.gui_controller import GUIController
from navigate.tools.image import create_arrow_image
from navigate.tools.file_functions import load_yaml_file
from navigate.model.features.feature_related_functions import (
    convert_str_to_feature_list,
)
from navigate.model.features import feature_related_functions
from navigate.config.config import get_navigate_path


class FeaturePopupController(GUIController):
    """Controller for feature list popup"""

    def __init__(self, view, parent_controller, feature_list_id=0):
        """Initialize the controller

        Parameters
        ----------
        view : navigate.view.popups.feature_list_popup.FeatureListPopup
            The view of the controller
        parent_controller : navigate.controller.main_controller.MainController
            The parent controller
        feature_list_id : int, optional
            The id of the feature list, by default 0
        """
        super().__init__(view, parent_controller)
        #: int: The id of the feature in the feature list.
        self.feature_list_id = feature_list_id
        #: list: The list of feature names.
        self.features = []
        #: list: The list of feature structure.
        self.feature_structure = []

        self.view.buttons["preview"].configure(command=self.draw_feature_list_graph)
        if "add" in self.view.buttons:
            self.view.buttons["add"].configure(command=self.add_feature_list)
            self.view.popup.protocol("WM_DELETE_WINDOW", self.exit_func)
            self.view.buttons["cancel"].configure(command=self.exit_func)
        elif "confirm" in self.view.buttons:
            self.view.buttons["confirm"].configure(command=self.update_feature_list)
            self.view.popup.protocol("WM_DELETE_WINDOW", self.cancel_acquisition)
            self.view.buttons["cancel"].configure(command=self.cancel_acquisition)

        # get all feature names
        #: list: The list of feature names.
        self.feature_names = []
        temp = dir(feature_related_functions)
        for t in temp:
            if inspect.isclass(getattr(feature_related_functions, t)):
                self.feature_names.append(t)

    def populate_feature_list(self, feature_list_id):
        """Populate the feature list

        Parameters
        ----------
        feature_list_id : int
            The id of the feature list
        """
        self.feature_list_id = feature_list_id
        feature_list_content = self.parent_controller.model.get_feature_list(
            feature_list_id
        )
        self.view.inputs["content"].delete("1.0", tk.END)
        self.view.inputs["content"].insert("1.0", feature_list_content)
        self.view.inputs["feature_list_name"].set(
            self.parent_controller.menu_controller.feature_list_names[feature_list_id]
        )
        self.view.inputs["feature_list_name"].widget["state"] = "disabled"
        self.draw_feature_list_graph()

    def draw_feature_list_graph(self, new_list_flag=True):
        """Draw the feature list graph

        Parameters
        ----------
        new_list_flag : bool, optional
            Whether the feature list is new, by default True
        """
        if new_list_flag:
            feature_list = self.verify_feature_list()
            if not feature_list:
                return
            # flatten feature list
            self.features = []
            self.feature_structure = []
            self.flatten_feature_list(feature_list)
            self.feature_structure.pop()

        feature_list_view = self.view.feature_view_frame
        for child in feature_list_view.winfo_children():
            child.destroy()

        l = len(self.features) - 1  # noqa
        feature_icon_width = 228
        al_width = 104
        for i, feature in enumerate(self.features):
            btn = FeatureIcon(feature_list_view, feature["name"].__name__)
            btn.grid(row=0, column=i * 2, sticky="", pady=(30, 0))
            btn["width"] = 20
            # left click
            btn.bind("<Button-1>", self.show_config_popup(i))
            # right click
            btn.bind("<Button-3>", self.show_menu(i))
            if i == 0:
                feature_list_view.update()
                feature_icon_width = btn.winfo_width()
            if i < l:
                al = ArrowLabel(
                    feature_list_view,
                    xys=[(0, 20), (40, 20)],
                    direction="right",
                    image_width=40,
                    image_height=40,
                )
                al.grid(row=0, column=i * 2 + 1, sticky="", pady=(30, 0))
                if i == 0:
                    feature_list_view.update()
                    al_width = al.winfo_width()
        # draw loop arrows
        image_width = feature_icon_width * (l + 1) + al_width * l
        image_height = self.calculate_arrow_image_height(self.feature_structure)
        arrow_height = 50
        stack = []
        arrow_image = None
        space = 30
        end_pos = 0

        for c in self.feature_structure:
            if c == "(":
                if len(stack) > 0 and type(stack[-1]) is int:
                    stack.pop()
                stack.append("(")
            elif c == ")":
                # assert there is already at least one '('
                p, loops, start_pos, arrow_height = stack[-2]
                pre = stack[-1]
                if loops - 1 == 0:
                    stack.pop()
                    stack.pop()
                    stack.append(pre)
                else:
                    stack[-2] = (p, loops - 1, start_pos - space, arrow_height)
                # draw arrow
                arrow_image = create_arrow_image(
                    xys=[
                        (end_pos, 0),
                        (end_pos, arrow_height),
                        (start_pos, arrow_height),
                        (start_pos, 0),
                    ],
                    image_width=image_width,
                    image_height=image_height,
                    direction="up",
                    image=arrow_image,
                )
                # update arrow height
                for i in range(len(stack)):
                    if type(stack[i]) == tuple:
                        p, loops, start_pos, arrow_height = stack[i]
                        stack[i] = (p, loops, start_pos, arrow_height + 20)
            elif type(c) is int:
                if len(stack) > 0 and type(stack[-1]) is int:
                    stack[-1] = c
                else:
                    loops = 0
                    while len(stack) > 0 and stack[-1] == "(":
                        loops += 1
                        stack.pop()
                    if loops > 0:
                        stack.append(
                            (
                                c,
                                loops,
                                c * (feature_icon_width + al_width)
                                + feature_icon_width // 2
                                + (loops // 2) * space,
                                50,
                            )
                        )
                    else:
                        stack.append(c)
                end_pos = c * (feature_icon_width + al_width) + feature_icon_width // 2
        if arrow_image:
            image_gif = arrow_image.convert("P", palette=Image.ADAPTIVE)
            #: ImageTk.PhotoImage: The image of the feature list graph.
            self.image = ImageTk.PhotoImage(image_gif)
            al = tk.Label(feature_list_view, image=self.image)
            al.grid(row=1, column=0, columnspan=2 * l + 1, sticky="ew")

    def flatten_feature_list(self, feature_list):
        """Flatten the feature list

        Parameters
        ----------
        feature_list : list
            The feature list

        """
        for temp in feature_list:
            if type(temp) is dict:
                self.features.append(temp)
                self.feature_structure.append(len(self.features) - 1)
            else:
                self.feature_structure.append("(")
                self.flatten_feature_list(temp)
        self.feature_structure.append(")")

    def calculate_arrow_image_height(self, feature_structure):
        """Calculate the height of the arrow image

        Parameters
        ----------
        feature_structure : list
            The feature structure

        Returns
        -------
        int
            The height of the arrow image
        """
        image_height = 0
        h = 0
        for c in feature_structure:
            if c == "(":
                h += 20
                image_height = max(h, image_height)
            elif c == ")":
                h -= 20
        return image_height + 100

    def build_feature_list_text(self):
        """Build the feature list text

        Returns
        -------
        str
            The feature list text
        """
        content = "["
        for c in self.feature_structure:
            if c == "(":
                content += "("
                continue
            elif c == ")":
                content += ")"
            else:
                feature = self.features[c]
                content += "{" + f'"name": {feature["name"].__name__}'
                if "args" in feature:
                    arg_str = ""
                    for a in feature["args"]:
                        if a is None:
                            arg_str += "None"
                        elif type(a) is bool:
                            arg_str += str(a)
                        elif type(a) is int or type(a) is float:
                            arg_str += str(a)
                        elif type(a) is dict:
                            arg_str += str(a)
                        else:
                            try:
                                float(a)
                                arg_str += a
                            except (ValueError, TypeError):
                                arg_str += f'"{a}"'
                        arg_str += ","
                    content += f', "args": ({arg_str})'
                content += "}"
            content += ","
        content += "]"
        return content

    def show_config_popup(self, idx):
        """Show the feature configuration popup

        Parameters
        ----------
        idx : int
            The index of the feature

        Returns
        -------
        func
            The function to show the feature configuration popup
        """
        feature = self.features[idx]

        def func(event):
            """The function to show the feature configuration popup"""
            # load feature parameter setting
            feature_config_path = (
                f"{get_navigate_path()}/"
                f"feature_lists/feature_parameter_setting"
                f"/{feature['name'].__name__}.yml"
            )
            feature_parameter_config = None
            if os.path.exists(feature_config_path):
                feature_parameter_config = load_yaml_file(feature_config_path)
            spec = inspect.getfullargspec(feature["name"])
            if spec.defaults:
                args_value = list(spec.defaults)
            else:
                args_value = spec.defaults
            if "args" in feature:
                for i, a in enumerate(feature["args"]):
                    args_value[i] = a
            popup = FeatureConfigPopup(
                self.view.popup,
                features=self.feature_names,
                feature_name=feature["name"].__name__,
                args_name=spec.args[2:],
                args_value=args_value,
                title="Feature Parameters",
                parameter_config=feature_parameter_config,
            )
            popup.feature_name_widget.widget.bind(
                "<<ComboboxSelected>>", lambda event: refresh_parameters(popup)
            )

            popup.popup.protocol(
                "WM_DELETE_WINDOW", lambda: update_feature_parameters(popup)
            )

        def refresh_parameters(popup):
            """Refresh the feature parameters

            Parameters
            ----------
            popup : navigate.view.popups.feature_list_popup.FeatureConfigPopup
                The feature configuration popup
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
            popup.build_widgets(spec.args[2:], spec.defaults, feature_parameter_config)

        def update_feature_parameters(popup):
            """Update the feature parameters

            Parameters
            ----------
            popup : navigate.view.popups.feature_list_popup.FeatureConfigPopup
                The feature configuration popup

            Returns
            -------
            func
                The function to update the feature parameters
            """
            widgets = popup.get_widgets()
            feature_name = popup.feature_name_widget.get()
            feature["name"] = getattr(feature_related_functions, feature_name)
            if len(widgets) > 0:
                feature["args"] = [w.get() for w in widgets]
                for i, a in enumerate(feature["args"]):
                    if a == "True":
                        feature["args"][i] = True
                    elif a == "False":
                        feature["args"][i] = False
                    elif popup.inputs_type[i] is float:
                        feature["args"][i] = float(a)
                    elif popup.inputs_type[i] is dict:
                        feature["args"][i] = json.loads(a.replace("'", '"'))
                    elif a == "None":
                        feature["args"][i] = None
            # update text
            self.view.inputs["content"].delete("1.0", tk.END)
            self.view.inputs["content"].insert("1.0", self.build_feature_list_text())
            popup.popup.dismiss()
            self.draw_feature_list_graph(False)

        return func

    def show_menu(self, idx):
        """Show the popup menu

        Parameters
        ----------
        idx : int
            The index of the feature

        Returns
        -------
        func
            The function to show the popup menu
        """

        def func(event):
            """The function to show the popup menu"""
            popup_menu = tk.Menu(self.view.popup, tearoff=0)
            popup_menu.add_command(label="Delete", command=lambda: delete_feature(idx))
            popup_menu.add_command(
                label="Insert Before", command=lambda: insert_before(idx)
            )
            popup_menu.add_command(
                label="Insert After", command=lambda: insert_after(idx)
            )
            popup_menu.post(event.x_root, event.y_root)

        def delete_feature(idx):
            """Delete the feature

            Parameters
            ----------
            idx : int
                The index of the feature
            """
            del self.features[idx]
            i = self.feature_structure.index(idx)
            del self.feature_structure[i]
            for _, c in enumerate(self.feature_structure):
                if type(c) == int and c > idx:
                    self.feature_structure[_] -= 1

            # delete ()
            pre_count = 0
            for _ in range(i - 1, -1, -1):
                if self.feature_structure[_] == "(":
                    del self.feature_structure[_]
                    pre_count += 1
                else:
                    break
            stack = []
            if (
                pre_count == 0
                and i < len(self.feature_structure)
                and self.feature_structure[i] == ")"
            ):
                del self.feature_structure[i]
                for _ in range(i - 1, -1, -1):
                    if self.feature_structure[_] == ")":
                        stack.append(_)
                    elif self.feature_structure[_] == "(":
                        if len(stack) > 0:
                            stack.pop()
                        else:
                            del self.feature_structure[_]
                            break
            else:
                i = i - pre_count
                while pre_count > 0:
                    if self.feature_structure[i] == "(":
                        stack.append(i)
                        i += 1
                    elif self.feature_structure[i] == ")":
                        if len(stack) > 0:
                            stack.pop()
                            i += 1
                        else:
                            del self.feature_structure[i]
                            pre_count -= 1
                    else:
                        i += 1
                    if i >= len(self.feature_structure):
                        break

            # update text
            self.view.inputs["content"].delete("1.0", tk.END)
            self.view.inputs["content"].insert("1.0", self.build_feature_list_text())
            self.draw_feature_list_graph(False)

        def insert_before(idx):
            """Insert the feature before the current feature

            Parameters
            ----------
            idx : int
                The index of the feature
            """
            self.features.insert(idx, dict(self.features[idx]))
            i = self.feature_structure.index(idx)
            for _, c in enumerate(self.feature_structure):
                if type(c) == int and c >= idx:
                    self.feature_structure[_] = c + 1
            self.feature_structure.insert(i, idx)

            # update text
            self.view.inputs["content"].delete("1.0", tk.END)
            self.view.inputs["content"].insert("1.0", self.build_feature_list_text())
            self.draw_feature_list_graph(False)

        def insert_after(idx):
            """Insert the feature after the current feature

            Parameters
            ----------
            idx : int
                The index of the feature

            Returns
            -------
            func
                The function to insert the feature after the current feature
            """
            self.features.insert(idx + 1, dict(self.features[idx]))
            i = self.feature_structure.index(idx)
            for _, c in enumerate(self.feature_structure):
                if type(c) == int and c > idx:
                    self.feature_structure[_] = c + 1
            self.feature_structure.insert(i + 1, idx + 1)

            # update text
            self.view.inputs["content"].delete("1.0", tk.END)
            self.view.inputs["content"].insert("1.0", self.build_feature_list_text())
            self.draw_feature_list_graph(False)

        return func

    def add_feature_list(self):
        """Add the feature list"""
        if not self.verify_feature_list():
            return
        content = self.view.inputs["content"].get("1.0", "end-1c")
        feature_list_content = "".join(content.split("\n"))
        feature_list_name = self.view.inputs["feature_list_name"].get()
        if not feature_list_name:
            messagebox.showerror(
                title="Feature List Error",
                message="Please enter a name for this feature list!",
            )
            return
        if not self.parent_controller.menu_controller.add_feature_list(
            feature_list_name, feature_list_content
        ):
            messagebox.showerror(
                title="Feature List Error",
                message="Please enter a new list name! "
                "The one you entered has been exist!",
            )
        else:
            self.exit_func()

    def update_feature_list(self):
        """Update the feature list"""
        if not self.verify_feature_list():
            return
        content = self.view.inputs["content"].get("1.0", "end-1c")
        feature_list_content = "".join(content.split("\n"))
        self.parent_controller.execute(
            "load_feature", self.feature_list_id, feature_list_content
        )
        #: bool: Whether the acquisition should start.
        self.start_acquisiton_flag = True
        self.view.popup.dismiss()

    def verify_feature_list(self):
        """Verify the feature list

        Returns
        -------
        feature_list : list
            The feature list
        """
        content = self.view.inputs["content"].get("1.0", "end-1c")
        feature_list_content = "".join(content.split("\n"))
        feature_list = convert_str_to_feature_list(feature_list_content)
        if feature_list is None:
            messagebox.showerror(
                title="Feature List Error",
                message="There is something wrong for this feature "
                "list, please verify there is no "
                "spelling error!",
            )
        return feature_list

    def exit_func(self):
        """Exit the popup"""
        self.view.popup.dismiss()
        delattr(self.parent_controller, "features_popup_controller")

    def cancel_acquisition(self):
        """Cancel the acquisition"""
        self.start_acquisiton_flag = False
        self.view.popup.dismiss()
