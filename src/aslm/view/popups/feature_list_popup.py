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

# Standard Library Imports
import tkinter as tk
from tkinter import ttk, Grid

# Local Imports
from aslm.view.custom_widgets.popup import PopUp
from aslm.view.custom_widgets.LabelInputWidgetFactory import LabelInput

class FeatureIcon(ttk.Button):
    def __init__(self, parent, feature_name=""):
        ttk.Button.__init__(self, parent, text=feature_name)
        self.configure(padding=(50, 50))


class FeatureConfigPopup:
    def __init__(self, root, *args, features=[], feature_name="", args_name=[], args_value=[], **kwargs):
        # Creating popup window with this name and size/placement,
        # PopUp is a Toplevel window
        self.popup = PopUp(
            root, kwargs["title"], "+320+180", top=False, transient=False
        )
        # Change background of popup window to white
        self.popup.configure(bg="white")

        # Creating content frame
        content_frame = self.popup.get_frame()

        self.inputs = {}

        self.feature_name_widget = LabelInput(
            parent=content_frame,
            label="Feature Name",
            label_args={"width": 20},
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            input_args={"width": 30, "state": "readonly"},
        )
        self.feature_name_widget.grid(row=0, column=0, sticky=tk.NSEW, padx=3, pady=3)
        self.feature_name_widget.set(feature_name)
        self.feature_name_widget.set_values(features)

        separator = ttk.Separator(content_frame)
        separator.grid(row=1, column=0, sticky=tk.NSEW, pady=10)

        self.parameter_frame = ttk.Frame(content_frame)
        self.parameter_frame.grid(row=2, column=0, sticky=tk.NSEW, padx=30, pady=30)
        
        self.build_widgets(args_name, args_value, kwargs.get("parameter_config", {}))

    def build_widgets(self, args_name, args_value, parameter_config=None):
        self.inputs = []
        self.inputs_type = []

        for child in self.parameter_frame.winfo_children():
            child.destroy()

        for i, arg_name in enumerate(args_name):
            arg_input_class = ttk.Entry
            arg_input_var = tk.StringVar
            if type(args_value[i]) is bool:
                arg_input_class = ttk.Combobox
                values = ["True", "False"]
            elif parameter_config is not None and arg_name in parameter_config:
                arg_input_class = ttk.Combobox
                values = list(parameter_config[arg_name].keys())

            temp = LabelInput(
                parent=self.parameter_frame,
                label=arg_name+":",
                label_args={"padding": (2, 5, 5, 0), "width": 20},
                input_class=arg_input_class,
                input_var=arg_input_var(),
                input_args={"width": 30},
            )

            self.inputs.append(temp)
            self.inputs_type.append(type(args_value[i]))
            temp.grid(row=i+2, column=0, sticky=tk.NSEW, padx=30, pady=10)
            if arg_input_class is ttk.Combobox:
                temp.set_values(values)
            temp.set(str(args_value[i]))

    def get_widgets(self):
        return self.inputs


class FeatureListPopup:
    def __init__(self, root, *args, **kwargs):
        # Creating popup window with this name and size/placement,
        # PopUp is a Toplevel window
        self.popup = PopUp(
            root, kwargs["title"], "+320+180", top=False, transient=False
        )
        # Change background of popup window to white
        self.popup.configure(bg="white")
        self.add_new_list_flag = False
        if kwargs["title"].startswith("Add"):
            self.add_new_list_flag = True

        # Creating content frame
        content_frame = self.popup.get_frame()

        self.inputs = {}
        self.inputs["feature_list_name"] = LabelInput(
            parent=content_frame,
            label="Feature List Name",
            input_class=ttk.Entry,
            input_var=tk.StringVar(),
            input_args={"width": 50},
        )

        self.inputs["feature_list_name"].grid(row=0, column=0, sticky=tk.NSEW, padx=3, pady=3)

        separator = ttk.Separator(content_frame)
        separator.grid(row=2, column=0, sticky=tk.NSEW, padx=3, pady=3)

        scroll_frame = ttk.Frame(content_frame)
        scroll_frame.grid(row=3, column=0, sticky=tk.NSEW)
        canvas = tk.Canvas(scroll_frame, width=500, height=350)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="horizon", command=canvas.xview)
        self.feature_view_frame = ttk.Frame(canvas)

        self.feature_view_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.feature_view_frame, anchor="nw")

        canvas.configure(xscrollcommand=scrollbar.set)

        canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="bottom", fill="x")


        separator = ttk.Separator(content_frame)
        separator.grid(row=4, column=0, sticky=tk.NSEW, padx=3, pady=3)
        self.inputs["content"] = tk.Text(content_frame, width=100, height=10)
        self.inputs["content"].grid(row=5, column=0, sticky=tk.NSEW, padx=10, pady=3)

        self.buttons = {}
        button_frame = ttk.Frame(content_frame)
        button_frame.grid(row=6, column=0, sticky=tk.NSEW)
        self.buttons["preview"] = ttk.Button(button_frame, text="Preview")
        self.buttons["preview"].grid(row=0, column=0, padx=3, pady=3)
        if self.add_new_list_flag:
            self.buttons["add"] = ttk.Button(button_frame, text="Add")
            self.buttons["add"].grid(row=0, column=1, padx=3, pady=3)
        else:
            self.buttons["confirm"] = ttk.Button(button_frame, text="Confirm")
            self.buttons["confirm"].grid(row=0, column=1, padx=3, pady=3)
        self.buttons["cancel"] = ttk.Button(button_frame, text="Cancel")
        self.buttons["cancel"].grid(row=0, column=2, sticky=tk.SE, padx=3, pady=3)
