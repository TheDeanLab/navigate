# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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
from collections.abc import Mapping
from pprint import pformat
import tkinter as tk
from tkinter import ttk

# Local Imports
from navigate.view.custom_widgets.popup import PopUp
from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput
from navigate.view.configurator_application_window import ConfiguratorTooltip
from navigate.view.custom_widgets.validation import ValidatedSpinbox
from navigate.config.configuration_schema import CollectionSpec, SettingSpec
from navigate.model.features.parameter_tools import infer_feature_parameter_spec
from navigate.view.theme import get_theme_padding_px, get_theme_space_px


class FeatureCollectionInput:
    """Fixed mapping editor used for structured feature parameters."""

    def __init__(self, parent, name, spec, value=None):
        """Create a fixed mapping input from a ``CollectionSpec``."""
        self.spec = spec
        self.frame = ttk.LabelFrame(
            parent,
            text=spec.label or name.replace("_", " ").title(),
            padding=get_theme_padding_px((6, 6)),
        )
        self.label = self.frame
        self.widgets = {}
        self.variables = {}
        values = value if isinstance(value, dict) else {}

        for row, (field_name, field_spec) in enumerate(spec.item_schema.items()):
            label = ttk.Label(
                self.frame,
                text=(field_spec.label or field_name.replace("_", " ").title()) + ":",
                width=18,
            )
            label.grid(
                row=row,
                column=0,
                sticky=tk.W,
                padx=get_theme_space_px(3),
                pady=get_theme_padding_px((1, 1)),
            )
            if field_spec.help_text:
                ConfiguratorTooltip(label, field_spec.help_text)

            variable = self.create_variable(field_spec, values.get(field_name))
            self.variables[field_name] = variable
            widget = self.create_widget(row, field_spec, variable)
            self.widgets[field_name] = widget

    def create_variable(self, spec, value):
        """Create a Tk variable suitable for a collection field."""
        value = spec.default if value is None else value
        if spec.value_type is bool:
            if isinstance(value, str):
                value = value.strip() == "True"
            return tk.StringVar(value=str(bool(value)))
        if spec.value_type is dict:
            return tk.StringVar(value=self.format_mapping_value(value))
        return tk.StringVar(value="" if value is None else str(value))

    @classmethod
    def format_mapping_value(cls, value):
        """Return a readable literal for nested mapping-like values."""
        if value is None:
            return ""
        return pformat(cls.to_plain_value(value), width=88)

    @classmethod
    def to_plain_value(cls, value):
        """Convert proxy mappings and nested containers to built-in values."""
        if isinstance(value, Mapping) or (
            hasattr(value, "items") and callable(value.items)
        ):
            return {key: cls.to_plain_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls.to_plain_value(item) for item in value]
        if isinstance(value, tuple):
            return tuple(cls.to_plain_value(item) for item in value)
        return value

    def create_widget(self, row, spec, variable):
        """Render one collection field."""
        grid_options = {
            "row": row,
            "column": 1,
            "sticky": tk.EW,
            "padx": get_theme_space_px(3),
            "pady": get_theme_padding_px((1, 1)),
        }
        if spec.value_type is bool:
            widget = ttk.Combobox(
                self.frame,
                textvariable=variable,
                values=("True", "False"),
                state="readonly",
                width=18,
            )
        elif spec.choices is not None:
            widget = ttk.Combobox(
                self.frame,
                textvariable=variable,
                values=spec.choices,
                state="readonly",
                width=18,
            )
        elif spec.value_type in (int, float):
            lower_bound = (
                spec.minimum
                if spec.minimum is not None
                else (
                    spec.exclusive_minimum
                    if spec.exclusive_minimum is not None
                    else -1000000
                )
            )
            widget = ValidatedSpinbox(
                self.frame,
                textvariable=variable,
                width=18,
                from_=lower_bound,
                to=1000000 if spec.maximum is None else spec.maximum,
                increment=(
                    (0.1 if spec.value_type is float else 1)
                    if spec.step is None
                    else spec.step
                ),
                required=spec.required,
                value_type=spec.value_type,
            )
        elif spec.value_type is dict:
            widget = tk.Text(
                self.frame,
                width=56,
                height=7,
                wrap=tk.NONE,
            )
            widget.insert("1.0", variable.get())
        else:
            widget = ttk.Entry(self.frame, textvariable=variable, width=20)
        widget.grid(**grid_options)
        return widget

    @property
    def widget(self):
        """Expose the container through the same attribute as ``LabelInput``."""
        return self.frame

    def grid(self, *args, **kwargs):
        """Delegate geometry management to the collection frame."""
        self.frame.grid(*args, **kwargs)

    def get(self):
        """Return the collection as a field mapping."""
        values = {}
        for field_name, variable in self.variables.items():
            widget = self.widgets[field_name]
            if isinstance(widget, tk.Text):
                values[field_name] = widget.get("1.0", "end-1c")
            else:
                values[field_name] = variable.get()
        return values

    def set(self, value):
        """Set collection values from a mapping."""
        if not isinstance(value, dict):
            return
        for field_name, field_value in value.items():
            if field_name in self.variables:
                field_spec = self.spec.item_schema[field_name]
                if field_spec.value_type is bool:
                    if isinstance(field_value, str):
                        field_value = field_value.strip() == "True"
                    else:
                        field_value = bool(field_value)
                if field_spec.value_type is dict:
                    text = self.format_mapping_value(field_value)
                    self.variables[field_name].set(text)
                    widget = self.widgets[field_name]
                    if isinstance(widget, tk.Text):
                        widget.delete("1.0", tk.END)
                        widget.insert("1.0", text)
                    continue
                self.variables[field_name].set(str(field_value))


class FeatureIcon(ttk.Button):
    """Feature Icon Widget"""

    def __init__(self, parent, feature_name="", set_bg=False):
        """Initialize the Feature Icon Widget

        Parameters
        ----------
        parent : tk.Frame
            Parent frame of the widget
        feature_name : str
            Name of the feature
        """
        ttk.Button.__init__(self, parent, text=feature_name)

        if set_bg:
            self.configure(style="Danger.TButton")

        self.configure(padding=get_theme_padding_px((10, 20)))


class FeatureConfigPopup:
    """Feature Config Popup Widget"""

    def __init__(
        self,
        root,
        *args,
        features=[],
        palette_features=None,
        feature_name="",
        args_name=[],
        args_value=[],
        **kwargs,
    ):
        """Initialize the Feature Config Popup Widget

        Parameters
        ----------
        root : tk.Tk
            Root window of the application
        *args : list
            List of arguments
        features : list
            List of features
        palette_features : list, optional
            Feature names displayed in the left-side palette
        feature_name : str
            Name of the feature
        args_name : list
            List of arguments name
        args_value : list
            List of arguments value
        """
        # Support the legacy positional ``features`` argument as well as the
        # keyword form used by the controller.
        if not features and args:
            features = args[0]
        if palette_features is None:
            palette_features = features

        # Creating popup window with this name and size/placement,

        #: PopUp: Popup window
        self.popup = PopUp(
            root, kwargs["title"], "+320+180", top=False, transient=False
        )
        self.popup.resizable(tk.TRUE, tk.TRUE)

        # Creating content frame and feature node palette
        content_frame = self.popup.get_frame()
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        outer_frame = ttk.Frame(content_frame)
        outer_frame.grid(row=0, column=0, sticky=tk.NSEW)
        outer_frame.columnconfigure(1, weight=1)
        outer_frame.rowconfigure(0, weight=1)

        palette = ttk.LabelFrame(outer_frame, text="Feature Nodes", padding=10)
        palette.grid(row=0, column=0, sticky=tk.NS, padx=(0, 12))
        palette.rowconfigure(0, weight=1)
        palette.columnconfigure(0, weight=1)

        palette_canvas = tk.Canvas(
            palette, width=150, height=380, highlightthickness=0, borderwidth=0
        )
        palette_scrollbar = ttk.Scrollbar(
            palette, orient="vertical", command=palette_canvas.yview
        )
        palette_canvas.configure(yscrollcommand=palette_scrollbar.set)
        palette_canvas.grid(row=0, column=0, sticky=tk.NS)
        palette_scrollbar.grid(row=0, column=1, sticky=tk.NS, padx=(6, 0))

        #: ttk.Frame: Container for the feature node palette buttons.
        self.palette_items = ttk.Frame(palette_canvas)
        palette_window = palette_canvas.create_window(
            (0, 0), window=self.palette_items, anchor="nw"
        )
        palette_canvas.bind(
            "<Configure>",
            lambda event: palette_canvas.itemconfigure(
                palette_window, width=event.width
            ),
        )
        self.palette_items.bind(
            "<Configure>",
            lambda _event: palette_canvas.configure(
                scrollregion=palette_canvas.bbox("all")
            ),
        )
        self.palette_buttons = {}
        for feature in palette_features:
            button = ttk.Button(self.palette_items, text=feature)
            button.pack(fill="x", padx=5, pady=3)
            self.palette_buttons[feature] = button

        # Creating configuration content frame
        content_frame = ttk.Frame(outer_frame)
        content_frame.grid(row=0, column=1, sticky=tk.NSEW)
        content_frame.columnconfigure(0, weight=1)

        #: list: List of input widgets
        self.inputs = []

        #: LabelInput: Feature name widget
        self.feature_name_widget = LabelInput(
            parent=content_frame,
            label="Feature Name",
            label_args={"width": 20},
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            input_args={"width": 30, "state": "readonly"},
        )
        self.feature_name_widget.grid(
            row=0,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )
        self.feature_name_widget.set(feature_name)
        self.feature_name_widget.set_values(features)

        separator = ttk.Separator(content_frame)
        separator.grid(row=1, column=0, sticky=tk.NSEW, pady=get_theme_space_px(10))

        #: tk.StringVar: Feature description displayed above parameter inputs.
        self.feature_description = tk.StringVar()
        self.feature_description_widget = ttk.Label(
            content_frame,
            textvariable=self.feature_description,
            wraplength=520,
            justify=tk.LEFT,
        )
        self.feature_description_widget.grid(
            row=2,
            column=0,
            sticky=tk.EW,
            padx=get_theme_space_px(30),
            pady=get_theme_padding_px((0, 10)),
        )
        self.set_feature_description(kwargs.get("feature_description", ""))

        #: ttk.Frame: Parameter frame
        self.parameter_frame = ttk.Frame(content_frame)
        self.parameter_frame.grid(
            row=3,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(30),
            pady=get_theme_space_px(30),
        )

        row = 4
        if "true" in kwargs:
            self.preview_btn_true = ttk.Button(content_frame, text="Preview (True)")
            self.preview_btn_true.grid(row=row, column=0, sticky=tk.NSEW)
            separator = ttk.Separator(content_frame)
            separator.grid(
                row=row + 1,
                column=0,
                sticky=tk.NSEW,
                pady=get_theme_padding_px((0, 10)),
            )
            self.feature_list_true_frame = FeatureListFrame(content_frame)
            self.feature_list_true_frame.grid(row=row + 2, column=0, sticky=tk.NSEW)
            row += 3

        if "false" in kwargs:
            self.preview_btn_false = ttk.Button(content_frame, text="Preview (False)")
            self.preview_btn_false.grid(row=row, column=0, sticky=tk.NSEW)
            separator = ttk.Separator(content_frame)
            separator.grid(
                row=row + 1,
                column=0,
                sticky=tk.NSEW,
                pady=get_theme_padding_px((0, 10)),
            )
            self.feature_list_false_frame = FeatureListFrame(content_frame)
            self.feature_list_false_frame.grid(row=row + 2, column=0, sticky=tk.NSEW)

        self.build_widgets(
            args_name,
            args_value,
            kwargs.get("parameter_config", {}),
            kwargs.get("parameter_schema", {}),
        )

    def set_feature_description(self, description):
        """Set the feature-level description shown in the parameter editor."""
        description = description or ""
        self.feature_description.set(description)
        if description:
            self.feature_description_widget.grid()
        else:
            self.feature_description_widget.grid_remove()

    def build_widgets(
        self,
        args_name,
        args_value,
        parameter_config=None,
        parameter_schema=None,
    ):
        """Build widgets for the popup

        Parameters
        ----------
        args_name : list
            List of arguments name
        args_value : list
            List of arguments value
        parameter_config : dict
            Dictionary of parameter configuration
        parameter_schema : dict
            Dictionary of feature parameter schema definitions
        """
        #: list: List of input widgets
        self.inputs = []
        #: list: List of input widgets type
        self.inputs_type = []
        #: list: List of parameter schema definitions
        self.parameter_specs = []
        #: list: Parameter names in the same order as the input widgets
        self.parameter_names = []
        #: dict: Parameter inputs keyed by constructor argument name
        self.inputs_by_name = {}
        #: dict: Parameter positions keyed by constructor argument name
        self.parameter_index_by_name = {}

        for child in self.parameter_frame.winfo_children():
            child.destroy()

        args_value = [] if args_value is None else list(args_value)
        parameter_schema = parameter_schema or {}

        for i, arg_name in enumerate(args_name):
            arg_value = args_value[i] if i < len(args_value) else None
            arg_spec = parameter_schema.get(arg_name) or infer_feature_parameter_spec(
                arg_value
            )
            if isinstance(arg_spec, CollectionSpec):
                temp = FeatureCollectionInput(
                    self.parameter_frame,
                    arg_name,
                    arg_spec,
                    arg_value,
                )
                self.inputs.append(temp)
                self.inputs_type.append(dict)
                self.parameter_specs.append(arg_spec)
                self.parameter_names.append(arg_name)
                self.inputs_by_name[arg_name] = temp
                self.parameter_index_by_name[arg_name] = i
                temp.grid(
                    row=i + 2,
                    column=0,
                    sticky=tk.NSEW,
                    padx=get_theme_space_px(30),
                    pady=get_theme_space_px(10),
                )
                if arg_spec.help_text:
                    ConfiguratorTooltip(temp.label, arg_spec.help_text)
                continue

            arg_input_class = ttk.Entry
            arg_input_var = tk.StringVar
            input_args = {"width": 30}
            values = None
            if arg_spec.value_type is bool:
                arg_input_class = ttk.Combobox
                values = ["True", "False"]
            elif parameter_config is not None and arg_name in parameter_config:
                arg_input_class = ttk.Combobox
                values = list(parameter_config[arg_name].keys())
            elif arg_spec.choices is not None:
                arg_input_class = ttk.Combobox
                values = list(arg_spec.choices)
            elif arg_spec.value_type in (int, float):
                lower_bound = (
                    arg_spec.minimum
                    if arg_spec.minimum is not None
                    else (
                        arg_spec.exclusive_minimum
                        if arg_spec.exclusive_minimum is not None
                        else -1000000
                    )
                )
                arg_input_class = ValidatedSpinbox
                input_args = {
                    "width": 30,
                    "from_": lower_bound,
                    "to": 1000000 if arg_spec.maximum is None else arg_spec.maximum,
                    "increment": (
                        (0.1 if arg_spec.value_type is float else 1)
                        if arg_spec.step is None
                        else arg_spec.step
                    ),
                    "required": arg_spec.required,
                    "value_type": arg_spec.value_type,
                }

            temp = LabelInput(
                parent=self.parameter_frame,
                label=(arg_spec.label or arg_name) + ":",
                label_args={"padding": (2, 5, 5, 0), "width": 20},
                input_class=arg_input_class,
                input_var=arg_input_var(),
                input_args=input_args,
            )

            self.inputs.append(temp)
            self.inputs_type.append(arg_spec.value_type)
            self.parameter_specs.append(arg_spec)
            self.parameter_names.append(arg_name)
            self.inputs_by_name[arg_name] = temp
            self.parameter_index_by_name[arg_name] = i
            temp.grid(
                row=i + 2,
                column=0,
                sticky=tk.NSEW,
                padx=get_theme_space_px(30),
                pady=get_theme_space_px(10),
            )
            if arg_spec.help_text:
                ConfiguratorTooltip(temp.label, arg_spec.help_text)
            if arg_input_class is ttk.Combobox:
                temp.set_values(values)
                temp.widget.config(state="readonly")
            display_value = (
                "" if arg_value is None and not arg_spec.required else arg_value
            )
            temp.set(str(display_value))

    def get_widgets(self):
        """Get widgets

        Returns
        -------
        list
            List of input widgets
        """
        return self.inputs


class FeatureListPopup:
    """Feature List Popup Widget"""

    def __init__(self, root, *args, **kwargs):
        """Initialize the Feature List Popup Widget

        Parameters
        ----------
        root : tk.Tk
            Root window of the application
        *args : list
            List of arguments
        **kwargs : dict
            Dictionary of keyword arguments
        """
        # Creating popup window with this name and size/placement,
        # PopUp is a Toplevel window
        #: PopUp: Popup window
        self.popup = PopUp(
            root, kwargs["title"], "+500+360", top=False, transient=False
        )
        self.popup.resizable(tk.TRUE, tk.TRUE)
        self.popup.grid_columnconfigure(0, weight=1)
        self.popup.grid_rowconfigure(0, weight=1)
        #: bool: Flag to indicate if the popup is for adding new list
        self.add_new_list_flag = False
        if kwargs["title"].startswith("Add"):
            self.add_new_list_flag = True

        # Creating content frame
        content_frame = self.popup.get_frame()
        content_frame.grid_columnconfigure(0, weight=1)

        #: dict: Dictionary of input widgets
        self.inputs = {}
        self.inputs["feature_list_name"] = LabelInput(
            parent=content_frame,
            label="Feature List Name",
            input_class=ttk.Entry,
            input_var=tk.StringVar(),
            input_args={"width": 50},
        )

        self.inputs["feature_list_name"].grid(
            row=0,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )
        self.inputs["feature_list_name"].grid_columnconfigure(0, weight=0)
        self.inputs["feature_list_name"].grid_columnconfigure(1, weight=1)
        self.inputs["feature_list_name"].grid_rowconfigure(0, weight=1)

        separator = ttk.Separator(content_frame)
        separator.grid(
            row=2,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )

        outer_frame = ttk.Frame(content_frame)
        content_frame.grid_rowconfigure(3, weight=1)
        outer_frame.grid(row=3, column=0, sticky=tk.NSEW)
        outer_frame.columnconfigure(1, weight=1)
        outer_frame.rowconfigure(0, weight=1)

        # feature nodes palette
        palette = ttk.LabelFrame(outer_frame, text="Feature Nodes", padding=10)
        palette.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        palette.rowconfigure(0, weight=1)
        palette.columnconfigure(1, weight=1)

        palette_canvas = tk.Canvas(
            palette, width=150, height=380, highlightthickness=0, borderwidth=0
        )
        scrollbar = ttk.Scrollbar(
            palette, orient="vertical", command=palette_canvas.yview
        )
        palette_canvas.configure(yscrollcommand=scrollbar.set)
        palette_canvas.grid(row=0, column=0, sticky="ns")
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))

        self.palette_items = ttk.Frame(palette_canvas)
        palette_window = palette_canvas.create_window(
            (0, 0), window=self.palette_items, anchor="nw"
        )
        palette_canvas.bind(
            "<Configure>",
            lambda e: palette_canvas.itemconfig(palette_window, width=e.width),
        )
        self.palette_items.bind(
            "<Configure>",
            lambda e: palette_canvas.configure(scrollregion=palette_canvas.bbox("all")),
        )

        board_content_frame = ttk.Frame(outer_frame)
        board_content_frame.grid(row=0, column=1, sticky="nsew")
        board_content_frame.columnconfigure(0, weight=1)
        board_content_frame.rowconfigure(0, weight=1)

        board_box = ttk.LabelFrame(board_content_frame, text="Feature List", padding=10)
        board_box.grid(row=0, column=0, sticky="nsew")
        board_box.columnconfigure(0, weight=1)
        board_box.rowconfigure(1, weight=1)
        label = ttk.Label(
            board_box,
            text="Drag feature nodes from the left panel to this board to create a feature list.",
        )
        label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.board_canvas = tk.Canvas(board_box, highlightthickness=0, borderwidth=0)
        self.board_canvas.configure(takefocus=True)
        self.board_canvas.grid(row=1, column=0, sticky="nsew")
        board_scrollbar = ttk.Scrollbar(
            board_box, orient="horizontal", command=self.board_canvas.xview
        )
        board_scrollbar.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        self.board_canvas.configure(xscrollcommand=board_scrollbar.set)

        self.feature_view_frame = ttk.Frame(self.board_canvas)
        self.board_window = self.board_canvas.create_window(
            (0, 0), window=self.feature_view_frame, anchor="nw"
        )

        self.marker = tk.Frame(
            self.feature_view_frame, background="#2878d4", width=3, height=30
        )

        separator = ttk.Separator(board_content_frame)
        separator.grid(
            row=4,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )
        self.inputs["content"] = tk.Text(board_content_frame, width=100, height=10)
        self.inputs["content"].grid(
            row=5,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(10),
            pady=get_theme_space_px(3),
        )

        #: dict: Dictionary of buttons
        self.buttons = {}
        button_frame = ttk.Frame(content_frame)
        button_frame.grid(row=6, column=0, sticky=tk.NSEW)
        self.buttons["preview"] = ttk.Button(button_frame, text="Preview")
        self.buttons["preview"].grid(
            row=0, column=0, padx=get_theme_space_px(3), pady=get_theme_space_px(3)
        )
        if self.add_new_list_flag:
            self.buttons["add"] = ttk.Button(button_frame, text="Add")
            self.buttons["add"].grid(
                row=0, column=1, padx=get_theme_space_px(3), pady=get_theme_space_px(3)
            )
        else:
            self.buttons["confirm"] = ttk.Button(button_frame, text="Confirm")
            self.buttons["confirm"].grid(
                row=0, column=1, padx=get_theme_space_px(3), pady=get_theme_space_px(3)
            )
        self.buttons["cancel"] = ttk.Button(button_frame, text="Cancel")
        self.buttons["cancel"].grid(
            row=0,
            column=2,
            sticky=tk.SE,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )


class FeatureListFrame(ttk.Frame):
    """Feature list graph frame"""

    def __init__(self, root, *args, width=800, height=200, **kwargs):
        super().__init__(root)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.board_canvas = tk.Canvas(
            self, width=width, height=height, highlightthickness=0, borderwidth=0
        )
        self.board_canvas.configure(takefocus=True)
        self.board_canvas.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar = ttk.Scrollbar(
            self, orient="horizontal", command=self.board_canvas.xview
        )
        scrollbar.grid(row=1, column=0, sticky=tk.EW, pady=(6, 0))
        self.board_canvas.configure(xscrollcommand=scrollbar.set)

        self.feature_view_frame = ttk.Frame(self.board_canvas)
        self.board_window = self.board_canvas.create_window(
            (0, 0), window=self.feature_view_frame, anchor="nw"
        )
        self.marker = tk.Frame(
            self.feature_view_frame, background="#2878d4", width=3, height=30
        )

        self.content = tk.Text(self, width=100, height=5)
        self.content.grid(
            row=2,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(10),
            pady=get_theme_space_px(3),
        )


class FeatureAdvancedSettingPopup:
    """Feature Advanced Setting Popup Widget"""

    def __init__(
        self,
        root,
        *args,
        features=[],
        feature_name="",
        args_name=[],
        args_default_value=[],
        **kwargs,
    ):
        """Initialize the Feature Advanced Setting Popup Widget

        Parameters
        ----------
        root : tk.Tk
            Root window of the application
        features : list
            List of features
        feature_name : str
            Name of the feature
        args_name : list
            List of arguments name
        args_default_value : list
            List of arguments default value
        """
        # Creating popup window with this name and size/placement,
        # PopUp is a Toplevel window
        #: PopUp: Popup window
        self.popup = PopUp(
            root, kwargs["title"], "+320+180", top=False, transient=False
        )
        # Creating content frame
        content_frame = self.popup.get_frame()

        #: dict: Dictionary of input widgets
        self.inputs = {}
        #: dict: Dictionary of buttons
        self.buttons = {}

        self.feature_name_widget = LabelInput(
            parent=content_frame,
            label="Feature Name",
            label_args={"width": 20},
            input_class=ttk.Combobox,
            input_var=tk.StringVar(),
            input_args={"width": 30, "state": "readonly"},
        )
        self.feature_name_widget.grid(
            row=0,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )
        self.feature_name_widget.set(feature_name)
        self.feature_name_widget.set_values(features)

        separator = ttk.Separator(content_frame)
        separator.grid(row=1, column=0, sticky=tk.NSEW, pady=get_theme_space_px(10))

        #: ttk.Frame: Parameter frame
        self.parameter_frame = ttk.Frame(content_frame)
        self.parameter_frame.grid(
            row=2,
            column=0,
            sticky=tk.NSEW,
            padx=get_theme_space_px(30),
            pady=get_theme_space_px(30),
        )
        #: dict: Dictionary of argument frames
        self.arg_frames = {}

    def build_widgets(self, args_name, parameter_config=None):
        """Build widgets for the popup

        Parameters
        ----------
        args_name : list
            List of arguments name
        parameter_config : dict
            Dictionary of parameter configuration
        """
        #: dict: Dictionary of input widgets
        self.inputs = {}
        #: dict: Dictionary of buttons
        self.buttons = {}
        #: dict: Dictionary of argument frames
        self.arg_frames = {}

        for child in self.parameter_frame.winfo_children():
            child.destroy()
        self.save_button = None

        row_id = 0
        for _, arg_name in enumerate(args_name):
            # ref_value, value, delete button, load button
            self.inputs[arg_name] = []
            arg_label = ttk.Label(self.parameter_frame, text=arg_name + ":")
            arg_label.grid(row=row_id, column=0, sticky=tk.NW)
            row_id += 1
            arg_frame = ttk.Frame(self.parameter_frame)
            arg_frame.grid(row=row_id, column=0, sticky=tk.NSEW)
            row_id += 1
            self.arg_frames[arg_name] = arg_frame
            if parameter_config is not None and arg_name in parameter_config:
                for k, v in parameter_config[arg_name].items():
                    self.add_new_row(arg_name, k, v)
            add_button = ttk.Button(self.parameter_frame, text="Add")
            add_button.grid(
                row=row_id,
                column=0,
                sticky=tk.NW,
                padx=get_theme_space_px(3),
                pady=get_theme_space_px(3),
            )
            self.buttons[arg_name] = add_button
            row_id += 1
            separator = ttk.Separator(self.parameter_frame)
            separator.grid(
                row=row_id, column=0, sticky=tk.NSEW, pady=get_theme_space_px(10)
            )
            row_id += 1

        if len(args_name) > 1:
            save_button = ttk.Button(self.parameter_frame, text="Save")
            save_button.grid(
                row=row_id,
                column=0,
                sticky=tk.NE,
                padx=get_theme_space_px(3),
                pady=get_theme_space_px(3),
            )
            #: ttk.Button: Save button
            self.save_button = save_button

    def add_new_row(self, arg_name, k="", v=""):
        """Add new row to the popup

        Parameters
        ----------
        arg_name : str
            Name of the argument
        k : str
            Name of the function
        v : str
            Value of the function
        """
        r = len(self.inputs[arg_name])
        arg_frame = self.arg_frames[arg_name]
        ref_value_entry = LabelInput(
            parent=arg_frame,
            label="Function Name",
            input_class=ttk.Entry,
            input_var=tk.StringVar(),
            input_args={"width": 50},
        )
        ref_value_entry.grid(
            row=r,
            column=1,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )
        ref_value_entry.set(k)
        value_entry = LabelInput(
            parent=arg_frame,
            label="Value",
            input_class=ttk.Entry,
            input_var=tk.StringVar(),
            input_args={"width": 50},
        )
        value_entry.grid(
            row=r,
            column=2,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )
        value_entry.set(v)
        load_button = ttk.Button(arg_frame, text="Load")
        load_button.grid(
            row=r,
            column=3,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )
        delete_button = ttk.Button(arg_frame, text="Delete")
        delete_button.grid(
            row=r,
            column=4,
            sticky=tk.NSEW,
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(3),
        )
        delete_button.config(command=self.delete_row(arg_name, r))
        self.inputs[arg_name].append(
            (ref_value_entry, value_entry, load_button, delete_button)
        )

    def delete_row(self, arg_name, r):
        """Delete row from the popup

        Parameters
        ----------
        arg_name : str
            Name of the argument
        r : int
            Row number
        """

        def func():
            """Function to delete row from the popup

            Returns
            -------
            func
                Function to delete row from the popup
            """
            for w in self.inputs[arg_name][r]:
                w.grid_remove()
            self.inputs[arg_name][r] = None

        return func
