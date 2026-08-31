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

# Standard library imports
from dataclasses import replace
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import inspect
import os
import platform

# Third party imports
from PIL import Image, ImageTk

# Local application imports
from navigate.view.popups.feature_list_popup import FeatureIcon, FeatureConfigPopup
from navigate.view.custom_widgets.ArrowLabel import ArrowLabel
from navigate.controller.sub_controllers.gui import GUIController
from navigate.tools.image import create_arrow_image
from navigate.tools.file_functions import load_yaml_file, save_yaml_file
from navigate.model.features.feature_related_functions import (
    convert_str_to_feature_list,
    convert_feature_list_to_str,
)
from navigate.model.features import feature_related_functions
from navigate.model.features.common_features import PrepareNextChannel
from navigate.model.devices.configuration_schema import CollectionSpec, SettingSpec
from navigate.model.features.base import is_feature_class
from navigate.controller.sub_controllers.autofocus import AutofocusPopupController
from navigate.model.features.parameter_tools import (
    coerce_feature_parameter,
    infer_feature_parameter_spec,
)
from navigate.config.config import get_navigate_path


class FeaturePopupController(GUIController):
    """Controller for feature list popup"""

    def __init__(
        self,
        view,
        parent_controller,
        feature_list_id=0,
        persist_feature_list_edits=False,
    ):
        """Initialize the controller

        Parameters
        ----------
        view : navigate.view.popups.feature_list_popup.FeatureListPopup
            The view of the controller
        parent_controller : navigate.controller.main_controller.MainController
            The parent controller
        feature_list_id : int, optional
            The id of the feature list, by default 0
        persist_feature_list_edits : bool, optional
            Persist confirmed edits to an internal feature-list record. Acquisition
            configuration remains runtime-only by default.
        """
        super().__init__(view, parent_controller)

        #: int: The id of the feature in the feature list.
        self.feature_list_id = feature_list_id

        #: bool: Whether confirmed edits should be persisted to the feature-list YAML.
        self.persist_feature_list_edits = persist_feature_list_edits

        #: list: The list of feature names.
        self.features = []

        #: list: The list of feature structure.
        self.feature_structure = []

        self.feature_list_graph_controller = FeatureListGraphController(
            self.view.feature_view_frame,
            self.view.inputs["content"],
            self.view.buttons["preview"],
            self.view.palette_items,
            self.view.board_canvas,
            self.view.board_window,
            self.view.marker,
            configuration_controller=getattr(
                self.parent_controller,
                "configuration_controller",
                None,
            ),
        )

        if "add" in self.view.buttons:
            self.view.buttons["add"].configure(command=self.add_feature_list)
            self.view.popup.protocol("WM_DELETE_WINDOW", self.exit_func)
            self.view.buttons["cancel"].configure(command=self.exit_func)
            self.feature_list_graph_controller.update([{"name": PrepareNextChannel}])
        elif "confirm" in self.view.buttons:
            self.view.buttons["confirm"].configure(command=self.update_feature_list)
            self.view.popup.protocol("WM_DELETE_WINDOW", self.cancel_acquisition)
            self.view.buttons["cancel"].configure(command=self.cancel_acquisition)

        # Dismiss popup.
        self.view.popup.bind("<Escape>", self.exit_func)

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
        self.view.inputs["feature_list_name"].set(
            self.parent_controller.menu_controller.feature_list_names[feature_list_id]
        )
        self.view.inputs["feature_list_name"].widget["state"] = "disabled"
        self.feature_list_graph_controller.update(feature_list_content)

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

        if self.persist_feature_list_edits:
            (
                feature_list_config,
                yaml_file_name,
            ) = self.parent_controller.menu_controller._get_custom_feature_list_record(
                self.feature_list_id
            )
            if feature_list_config is None or yaml_file_name is None:
                messagebox.showerror(
                    title="Feature List Error",
                    message="The selected feature-list record is missing or invalid.",
                )
                return
            if feature_list_config["module_name"] is not None:
                messagebox.showerror(
                    title="Feature List Error",
                    message=(
                        "This feature list is provided by Python code or a plugin "
                        "and cannot be edited in the visual editor."
                    ),
                )
                return

            feature_lists_path = get_navigate_path() + "/feature_lists"
            feature_list_name = feature_list_config["feature_list_name"]
            if not save_yaml_file(
                feature_lists_path,
                {
                    "module_name": None,
                    "feature_list_name": feature_list_name,
                    "feature_list": feature_list_content,
                },
                yaml_file_name,
            ):
                messagebox.showerror(
                    title="Feature List Error",
                    message="The feature list could not be saved. No changes applied.",
                )
                return

        self.parent_controller.execute(
            "load_feature", self.feature_list_id, feature_list_content
        )
        #: bool: Whether the acquisition should start.
        self.start_acquisiton_flag = True
        self.close_child_popups()
        self.view.popup.dismiss()

    def verify_feature_list(self):
        """Verify the feature list

        Returns
        -------
        feature_list : list
            The feature list
        """
        content = self.view.inputs["content"].get("1.0", "end-1c")
        return verify_feature_list(content)

    def exit_func(self, *args):
        """Exit the popup"""
        self.close_child_popups()
        self.view.popup.dismiss()
        delattr(self.parent_controller, "features_popup_controller")

    def cancel_acquisition(self):
        """Cancel the acquisition"""
        self.start_acquisiton_flag = False
        self.close_child_popups()
        self.view.popup.dismiss()

    def close_child_popups(self):
        """Close child config popups"""
        for popup in self.feature_list_graph_controller.child_popups:
            popup.popup.dismiss()


class FeatureListGraphController:
    CHIP_GAP = 10
    MICROSCOPE_DYNAMIC_SOURCE = "microscopes"
    ZOOM_DYNAMIC_SOURCE = "zoom_values"
    STAGE_AXIS_DYNAMIC_SOURCE = "stage_axes"
    CHANNEL_DYNAMIC_SOURCE = "channels"
    AUTOFOCUS_CALIBRATION_ACTION_DYNAMIC_SOURCE = "autofocus_calibration_actions"
    MICROSCOPE_STATE_DYNAMIC_SOURCE = "microscope_state"

    def __init__(
        self,
        feature_list_view,
        feature_content_view,
        preview_btn,
        palette_items=None,
        board_canvas=None,
        board_window=None,
        marker=None,
        child_popups=None,
        configuration_controller=None,
    ):
        """Initialize feature list window

        Parameters
        ----------
        feature_list_view : frame
            feature list graph view
        feature_content_view : text
            feature list content
        preview_btn : button
            preview button
        child_popups : list
            list of child config popup windows
        """
        self.feature_list_view = feature_list_view
        self.feature_content_view = feature_content_view
        self.preview_btn = preview_btn
        self.palette_items = palette_items
        self.board_canvas = board_canvas
        self.board_window = board_window
        self.marker = marker
        self.configuration_controller = configuration_controller

        self.feature_list = None
        self.features = []
        self.feature_structure = []
        self.feature_list_graph_controllers_true = {}
        self.feature_list_graph_controllers_false = {}

        # get all feature names
        #: list: The list of feature names.
        self.feature_names = []
        temp = dir(feature_related_functions)
        for t in temp:
            feature = getattr(feature_related_functions, t)
            if is_feature_class(feature):
                self.feature_names.append(t)

        # initialize the feature nodes
        self.chips = []
        self.chip_positions = []
        self.selected_chips = []
        self.drag_name = None
        self.drag_chip = None
        self.drag_start = None
        self.drag_window = None
        self.insert_index = None
        self.branch_drag_start = None
        self.branch_drag_target = None
        self.branch_drag_targets = []
        self.branch_drag_window = None
        self.selected_branch_palette_button = None
        if self.palette_items is not None:
            for feature_name in self.feature_names:
                feature_icon = ttk.Button(self.palette_items, text=feature_name)
                feature_icon.pack(pady=5, padx=5, fill="x")
                feature_icon.bind(
                    "<ButtonPress-1>",
                    lambda event, n=feature_name: self.start_palette_drag(event, n),
                )
                feature_icon.bind("<B1-Motion>", self.drag_motion)
                feature_icon.bind("<ButtonRelease-1>", self.finish_drag)

        # event
        self.preview_btn.configure(command=self.draw_feature_list_graph)
        if self.board_canvas is not None:
            self.board_canvas.bind("<Configure>", lambda _event: self.layout_chips())
            self.board_canvas.bind("<Button-1>", lambda _event: self.clear_selection())
            self.feature_list_view.bind(
                "<Button-1>", lambda _event: self.clear_selection()
            )

        # popups
        self.child_popups = [] if child_popups is None else child_popups

    @staticmethod
    def get_feature_parameter_schema(feature_class):
        """Return schema metadata for a feature constructor."""
        return getattr(feature_class, "parameter_schema", {}) or {}

    def microscope_choices(self):
        """Return microscope names from the loaded configuration."""
        configuration_controller = getattr(self, "configuration_controller", None)
        if configuration_controller is None:
            return ()
        try:
            return tuple(configuration_controller.microscope_list)
        except (AttributeError, KeyError, TypeError):
            return ()

    def default_microscope_choice(self, choices):
        """Return the active microscope or first configured microscope."""
        configuration_controller = getattr(self, "configuration_controller", None)
        active = getattr(configuration_controller, "microscope_name", None)
        if active in choices:
            return active
        return choices[0] if choices else None

    def zoom_choices(self, microscope_name):
        """Return zoom names for one configured microscope."""
        configuration_controller = getattr(self, "configuration_controller", None)
        if configuration_controller is None or not microscope_name:
            return ()
        try:
            return tuple(configuration_controller.get_zoom_value_list(microscope_name))
        except (AttributeError, KeyError, TypeError):
            pass

        try:
            microscope = configuration_controller.configuration["configuration"][
                "microscopes"
            ][microscope_name]
            zoom_config = microscope.get("zoom", {})
            for key in ("position", "pixel_size"):
                if isinstance(zoom_config.get(key), dict):
                    return tuple(zoom_config[key].keys())
        except (AttributeError, KeyError, TypeError):
            pass
        return ()

    def stage_axis_choices(self):
        """Return all stage axes configured by any loaded microscope."""
        configuration_controller = getattr(self, "configuration_controller", None)
        configuration = getattr(configuration_controller, "configuration", None)
        try:
            microscopes = configuration["configuration"]["microscopes"]
        except (KeyError, TypeError):
            return ()

        axes = []
        for microscope in microscopes.values():
            stage = microscope.get("stage", {})
            hardware_entries = stage.get("hardware", [])
            if isinstance(hardware_entries, dict):
                hardware_entries = [hardware_entries]
            for hardware in hardware_entries:
                for axis in hardware.get("axes", []):
                    if axis not in axes:
                        axes.append(axis)
        return tuple(axes)

    def channel_choices(self):
        """Return channel keys from GUI channel count."""
        configuration_controller = getattr(self, "configuration_controller", None)
        configuration = getattr(configuration_controller, "configuration", None)
        try:
            channel_count = int(configuration["gui"]["channel_settings"]["count"])
        except (KeyError, TypeError, ValueError):
            return ()
        return tuple(f"channel_{index}" for index in range(1, channel_count + 1))

    def microscope_state_values(self):
        """Return currently loaded experiment MicroscopeState values."""
        configuration_controller = getattr(self, "configuration_controller", None)
        configuration = getattr(configuration_controller, "configuration", None)
        try:
            microscope_state = configuration["experiment"]["MicroscopeState"]
        except (KeyError, TypeError):
            return {}
        return dict(microscope_state)

    @staticmethod
    def stage_axis_offset_spec(axis):
        """Return a float setting spec for one stage-axis offset."""
        return SettingSpec(
            float,
            default=0,
            label=axis.upper() if len(axis) == 1 else axis.title(),
            help_text=f"Additional {axis}-axis position offset.",
            step=0.01,
        )

    @staticmethod
    def autofocus_calibration_action_choices():
        """Return displayed autofocus calibration action labels."""
        return tuple(AutofocusPopupController.CALIBRATION_ACTIONS.keys())

    @staticmethod
    def autofocus_calibration_action_choice_values():
        """Return displayed action labels mapped to internal action values."""
        return dict(AutofocusPopupController.CALIBRATION_ACTIONS)

    @staticmethod
    def autofocus_calibration_action_display_value(action_value):
        """Return the display label for an internal autofocus action value."""
        for label, value in AutofocusPopupController.CALIBRATION_ACTIONS.items():
            if action_value == value:
                return label
        return action_value

    def apply_dynamic_parameter_choices(
        self,
        args_name,
        args_value,
        parameter_specs,
        feature=None,
    ):
        """Add runtime microscope and zoom choices to feature parameter specs."""
        microscope_choices = self.microscope_choices()

        args_value = list(args_value)
        parameter_specs = dict(parameter_specs)

        for index, arg_name in enumerate(args_name):
            spec = parameter_specs[arg_name]
            if isinstance(spec, CollectionSpec):
                continue
            if spec.dynamic_source != self.MICROSCOPE_DYNAMIC_SOURCE:
                continue
            if not microscope_choices:
                continue
            parameter_specs[arg_name] = replace(spec, choices=microscope_choices)
            if args_value[index] not in microscope_choices:
                args_value[index] = self.default_microscope_choice(microscope_choices)

        for index, arg_name in enumerate(args_name):
            spec = parameter_specs[arg_name]
            if isinstance(spec, CollectionSpec):
                continue
            if spec.dynamic_source != self.ZOOM_DYNAMIC_SOURCE:
                continue
            microscope_parameter = spec.depends_on
            if microscope_parameter is None or microscope_parameter not in args_name:
                continue
            microscope_index = args_name.index(microscope_parameter)
            microscope_name = args_value[microscope_index]
            choices = self.zoom_choices(microscope_name)
            parameter_specs[arg_name] = replace(spec, choices=choices)
            if choices and args_value[index] not in choices:
                args_value[index] = choices[0]
            elif not choices:
                args_value[index] = ""

        dynamic_choice_sources = {
            self.STAGE_AXIS_DYNAMIC_SOURCE: self.stage_axis_choices(),
            self.CHANNEL_DYNAMIC_SOURCE: self.channel_choices(),
            self.AUTOFOCUS_CALIBRATION_ACTION_DYNAMIC_SOURCE: (
                self.autofocus_calibration_action_choices()
            ),
        }
        for index, arg_name in enumerate(args_name):
            spec = parameter_specs[arg_name]
            if isinstance(spec, CollectionSpec):
                continue
            choices = dynamic_choice_sources.get(spec.dynamic_source)
            if choices is None:
                continue
            choice_values = (
                self.autofocus_calibration_action_choice_values()
                if spec.dynamic_source
                == self.AUTOFOCUS_CALIBRATION_ACTION_DYNAMIC_SOURCE
                else spec.choice_values
            )
            parameter_specs[arg_name] = replace(
                spec,
                choices=choices,
                choice_values=choice_values,
            )
            if spec.dynamic_source == self.AUTOFOCUS_CALIBRATION_ACTION_DYNAMIC_SOURCE:
                args_value[index] = self.autofocus_calibration_action_display_value(
                    args_value[index]
                )
            if choices and args_value[index] not in choices:
                args_value[index] = choices[0]

        for index, arg_name in enumerate(args_name):
            spec = parameter_specs[arg_name]
            if not isinstance(spec, CollectionSpec):
                continue
            if spec.dynamic_source != self.STAGE_AXIS_DYNAMIC_SOURCE:
                continue
            axes = self.stage_axis_choices()
            if not axes:
                continue
            item_schema = {axis: self.stage_axis_offset_spec(axis) for axis in axes}
            parameter_specs[arg_name] = replace(spec, item_schema=item_schema)
            if not isinstance(args_value[index], dict):
                args_value[index] = {}
            args_value[index] = {
                axis: args_value[index].get(axis, item_schema[axis].default)
                for axis in item_schema
            }

        microscope_state = self.microscope_state_values()
        for index, arg_name in enumerate(args_name):
            spec = parameter_specs[arg_name]
            if not isinstance(spec, CollectionSpec):
                continue
            if spec.dynamic_source != self.MICROSCOPE_STATE_DYNAMIC_SOURCE:
                continue
            item_schema = {}
            for field_name, field_spec in spec.item_schema.items():
                microscope_state_key = field_name.split(".", 1)[-1]
                item_schema[field_name] = replace(
                    field_spec,
                    default=microscope_state.get(
                        microscope_state_key,
                        field_spec.default,
                    ),
                )
            parameter_specs[arg_name] = replace(spec, item_schema=item_schema)
            if not isinstance(args_value[index], dict):
                args_value[index] = {}
            has_saved_args = (
                feature is not None
                and "args" in feature
                and index < len(feature["args"])
                and isinstance(feature["args"][index], dict)
            )
            saved_values = args_value[index] if has_saved_args else {}
            args_value[index] = {
                field_name: saved_values.get(
                    field_name,
                    field_spec.default,
                )
                for field_name, field_spec in item_schema.items()
            }

        return args_value, parameter_specs

    def get_feature_parameter_values(self, feature_class, feature=None):
        """Return constructor parameter names, values, and merged specs."""
        spec = inspect.getfullargspec(feature_class)
        args_name = spec.args[2:]
        defaults = list(spec.defaults or ())
        required_count = len(args_name) - len(defaults)
        if len(defaults) < len(args_name):
            defaults = [None] * (len(args_name) - len(defaults)) + defaults
        schema = FeatureListGraphController.get_feature_parameter_schema(feature_class)
        parameter_specs = {}
        for index, arg_name in enumerate(args_name):
            default = defaults[index] if index < len(defaults) else None
            parameter_specs[arg_name] = schema.get(
                arg_name,
                (
                    SettingSpec(str, default=None, required=True)
                    if index < required_count
                    else infer_feature_parameter_spec(default)
                ),
            )
        args_value = [
            (
                {
                    field_name: field_spec.default
                    for field_name, field_spec in parameter_specs[
                        arg_name
                    ].item_schema.items()
                }
                if isinstance(parameter_specs[arg_name], CollectionSpec)
                else (
                    parameter_specs[arg_name].default
                    if isinstance(parameter_specs[arg_name], SettingSpec)
                    else defaults[index]
                )
            )
            for index, arg_name in enumerate(args_name)
        ]
        if feature is not None and "args" in feature:
            for index, value in enumerate(feature["args"]):
                if index >= len(args_value):
                    break
                args_value[index] = value
        args_value, parameter_specs = self.apply_dynamic_parameter_choices(
            args_name,
            args_value,
            parameter_specs,
            feature,
        )
        return args_name, args_value, parameter_specs

    def refresh_linked_zoom_choices(
        self,
        popup,
        zoom_parameter_name,
        microscope_parameter_name,
        reset_invalid=True,
    ):
        """Refresh a zoom combobox after its microscope selection changes."""
        microscope_widget = popup.inputs_by_name.get(microscope_parameter_name)
        zoom_widget = popup.inputs_by_name.get(zoom_parameter_name)
        if microscope_widget is None or zoom_widget is None:
            return

        choices = self.zoom_choices(microscope_widget.get())
        zoom_widget.set_values(choices)
        current_value = zoom_widget.get()
        if reset_invalid and current_value not in choices:
            zoom_widget.set(choices[0] if choices else "")

        zoom_index = popup.parameter_index_by_name[zoom_parameter_name]
        popup.parameter_specs[zoom_index] = replace(
            popup.parameter_specs[zoom_index],
            choices=choices,
        )

    def bind_dynamic_parameter_choices(self, popup):
        """Link runtime microscope comboboxes to their dependent zoom comboboxes."""

        def refresh_zoom(zoom_parameter_name, microscope_parameter_name):
            self.refresh_linked_zoom_choices(
                popup,
                zoom_parameter_name,
                microscope_parameter_name,
                reset_invalid=True,
            )

        for zoom_parameter_name in popup.parameter_names:
            zoom_index = popup.parameter_index_by_name[zoom_parameter_name]
            zoom_spec = popup.parameter_specs[zoom_index]
            if isinstance(zoom_spec, CollectionSpec):
                continue
            if zoom_spec.dynamic_source != self.ZOOM_DYNAMIC_SOURCE:
                continue
            microscope_parameter_name = zoom_spec.depends_on
            if microscope_parameter_name is None:
                continue
            microscope_widget = popup.inputs_by_name.get(microscope_parameter_name)
            if microscope_widget is None or not isinstance(
                microscope_widget.widget, ttk.Combobox
            ):
                continue
            microscope_widget.widget.bind(
                "<<ComboboxSelected>>",
                lambda _event, z=zoom_parameter_name, m=microscope_parameter_name: refresh_zoom(
                    z, m
                ),
                add="+",
            )
            self.refresh_linked_zoom_choices(
                popup,
                zoom_parameter_name,
                microscope_parameter_name,
            )

    def update(self, feature_list_content):
        """Update feature list window

        Parameters
        ----------
        feature_list_content : list
            The feature list
        """
        self.feature_list = None
        self.features = []
        self.feature_structure = []
        self.feature_list_graph_controllers_true = {}
        self.feature_list_graph_controllers_false = {}

        if feature_list_content in (["break"], ["continue"]):
            feature_list_content = feature_list_content[0]
        elif type(feature_list_content) == list:
            feature_list_content = convert_feature_list_to_str(feature_list_content)
        self.feature_content_view.delete("1.0", tk.END)
        self.feature_content_view.insert("1.0", feature_list_content)
        self.draw_feature_list_graph(new_list_flag=True)

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
            elif temp == "break" or temp == "continue":
                self.features.append(temp)
                self.feature_structure.append(len(self.features) - 1)
            else:
                self.feature_structure.append("(")
                self.flatten_feature_list(temp)
        self.feature_structure.append(")")

    def get_feature_content(self):
        """Get feature list content

        Returns
        -------
        content : str
            feature list content
        """
        content = self.feature_content_view.get("1.0", "end-1c")
        return content

    def update_feature_content(self):
        """Update feature content"""
        self.feature_content_view.delete("1.0", tk.END)
        self.feature_content_view.insert("1.0", self.build_feature_list_text())

    def draw_feature_list_graph(self, new_list_flag=True):
        """Draw the feature list graph

        Parameters
        ----------
        new_list_flag : bool, optional
            Whether the feature list is new, by default True
        """
        if new_list_flag:
            feature_list = verify_feature_list(self.get_feature_content())
            if not feature_list:
                return
            # flatten feature list
            self.features = []
            self.feature_structure = []
            self.flatten_feature_list(feature_list)
            self.feature_structure.pop()

        self.chips = []
        self.chip_positions = []
        self.selected_chips = []
        for child in self.feature_list_view.winfo_children():
            # The insertion marker belongs to the board and must survive a
            # redraw.  All feature widgets are recreated below from the model.
            if child is not self.marker:
                child.destroy()

        l = len(self.features) - 1  # noqa
        feature_icon_width = 228
        al_width = 104
        for i, feature in enumerate(self.features):
            if type(feature) == str:
                btn = FeatureIcon(self.feature_list_view, feature)
                flag = False
            else:
                flag = True
                is_decistion_btn = "true" in feature or "false" in feature
                btn = FeatureIcon(
                    self.feature_list_view,
                    feature["name"].__name__,
                    set_bg=is_decistion_btn,
                )
                if self.board_canvas is None:
                    btn.bind("<Button-1>", self.show_config_popup(i))
                else:
                    # A click opens its configuration; a drag changes its order.
                    btn.bind(
                        "<Shift-ButtonPress-1>",
                        lambda event, chip=btn: self.toggle_selection(chip),
                    )
                    btn.bind("<Shift-ButtonRelease-1>", lambda _event: "break")
                    btn.bind(
                        "<ButtonPress-1>",
                        lambda event, chip=btn: self.handle_chip_press(event, chip),
                    )
                    btn.bind("<B1-Motion>", self.drag_motion)
                    btn.bind("<ButtonRelease-1>", self.finish_drag)

            btn.grid(row=0, column=i * 2, sticky="", pady=(30, 0))
            btn["width"] = 20
            self.chips.append(btn)

            # Right-Click Bindings
            if platform.system() == "Darwin":
                btn.bind("<ButtonPress-2>", self.show_menu(i, flag))
            else:
                btn.bind("<Button-3>", self.show_menu(i, flag))

            if i == 0:
                self.feature_list_view.update()
                feature_icon_width = btn.winfo_width()
            if i < l:
                al = ArrowLabel(
                    self.feature_list_view,
                    xys=[(0, 20), (40, 20)],
                    direction="right",
                    image_width=40,
                    image_height=40,
                )
                al.grid(row=0, column=i * 2 + 1, sticky="", pady=(30, 0))
                if i == 0:
                    self.feature_list_view.update()
                    al_width = al.winfo_width()
        # draw loop arrows
        image_width = feature_icon_width * (l + 1) + al_width * l
        image_height = self.calculate_arrow_image_height()
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
                if len(stack) < 2:
                    stack.pop()
                    continue
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
            al = tk.Label(self.feature_list_view, image=self.image)
            al.grid(row=1, column=0, columnspan=2 * l + 1, sticky="ew")

        self.layout_chips()

    def show_config_popup(self, idx):
        """Show the feature configuration popup

        Parameters
        ----------
        idx : int
            The index of the feature

        Returns
        -------
        func : function
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
            args_name, args_value, parameter_schema = self.get_feature_parameter_values(
                feature["name"],
                feature,
            )
            kwargs = {}
            if "true" in feature:
                kwargs["true"] = True
            if "false" in feature:
                kwargs["false"] = True
            popup = FeatureConfigPopup(
                self.feature_list_view,
                features=self.feature_names,
                palette_features=(
                    self.feature_names + ["Break", "Continue"]
                    if "true" in feature or "false" in feature
                    else self.feature_names
                ),
                feature_name=feature["name"].__name__,
                args_name=args_name,
                args_value=args_value,
                title="Feature Parameters",
                parameter_config=feature_parameter_config,
                parameter_schema=parameter_schema,
                **kwargs,
            )
            self.bind_dynamic_parameter_choices(popup)
            popup.feature_name_widget.widget.bind(
                "<<ComboboxSelected>>", lambda event: refresh_parameters(popup)
            )

            popup.popup.protocol(
                "WM_DELETE_WINDOW", lambda: update_feature_parameters(popup)
            )

            if "true" in feature:
                self.feature_list_graph_controllers_true[idx] = (
                    FeatureListGraphController(
                        popup.feature_list_true_frame.feature_view_frame,
                        popup.feature_list_true_frame.content,
                        popup.preview_btn_true,
                        None,
                        popup.feature_list_true_frame.board_canvas,
                        popup.feature_list_true_frame.board_window,
                        popup.feature_list_true_frame.marker,
                        self.child_popups,
                        self.configuration_controller,
                    )
                )
                self.feature_list_graph_controllers_true[idx].update(feature["true"])
            if "false" in feature:
                self.feature_list_graph_controllers_false[idx] = (
                    FeatureListGraphController(
                        popup.feature_list_false_frame.feature_view_frame,
                        popup.feature_list_false_frame.content,
                        popup.preview_btn_false,
                        None,
                        popup.feature_list_false_frame.board_canvas,
                        popup.feature_list_false_frame.board_window,
                        popup.feature_list_false_frame.marker,
                        self.child_popups,
                        self.configuration_controller,
                    )
                )
                self.feature_list_graph_controllers_false[idx].update(feature["false"])

            branch_controllers = [
                controller
                for controller in (
                    self.feature_list_graph_controllers_true.get(idx),
                    self.feature_list_graph_controllers_false.get(idx),
                )
                if controller is not None
            ]
            for feature_name, button in popup.palette_buttons.items():
                button.bind(
                    "<ButtonPress-1>",
                    lambda event, name=feature_name: self.start_branch_palette_drag(
                        event, name, branch_controllers
                    ),
                )
                button.bind("<B1-Motion>", self.branch_palette_drag_motion)
                button.bind(
                    "<ButtonRelease-1>",
                    lambda event, name=feature_name: self.finish_branch_palette_drag(
                        event,
                        name,
                        lambda selected_name: select_palette_feature(
                            popup, selected_name
                        ),
                    ),
                )

            # save the popup reference
            self.child_popups.append(popup)

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
            args_name, args_value, parameter_schema = self.get_feature_parameter_values(
                new_feature
            )
            popup.build_widgets(
                args_name,
                args_value,
                feature_parameter_config,
                parameter_schema,
            )
            self.bind_dynamic_parameter_choices(popup)

        def select_palette_feature(popup, feature_name):
            """Select a feature from the popup's feature node palette."""
            if feature_name not in self.feature_names:
                return
            popup.feature_name_widget.set(feature_name)
            refresh_parameters(popup)

        def update_feature_parameters(popup):
            """Update the feature parameters

            Parameters
            ----------
            popup : navigate.view.popups.feature_list_popup.FeatureConfigPopup
                The feature configuration popup
            """
            widgets = popup.get_widgets()
            feature_name = popup.feature_name_widget.get()
            feature["name"] = getattr(feature_related_functions, feature_name)
            # if new feature doesn't have any parameters
            if "args" in feature and len(widgets) == 0:
                del feature["args"]
            if len(widgets) > 0:
                feature["args"] = []
                for i, widget in enumerate(widgets):
                    arg_name = inspect.getfullargspec(feature["name"]).args[i + 2]
                    parameter_spec = popup.parameter_specs[i]
                    try:
                        feature["args"].append(
                            coerce_feature_parameter(
                                arg_name,
                                widget.get(),
                                parameter_spec,
                            )
                        )
                    except ValueError as error:
                        messagebox.showerror(
                            title="Update Feature Parameter Error",
                            message=str(error),
                        )
                        return
            if "true" in feature:
                feature["true"] = convert_str_to_feature_list(
                    self.feature_list_graph_controllers_true[idx].get_feature_content()
                )
            if "false" in feature:
                feature["false"] = convert_str_to_feature_list(
                    self.feature_list_graph_controllers_false[idx].get_feature_content()
                )
            # update text
            self.update_feature_content()
            popup.popup.dismiss()
            self.draw_feature_list_graph(False)

        return func

    def show_menu(self, idx, flag=True):
        """Show the popup menu

        Parameters
        ----------
        idx : int
            The index of the feature
        flag : bool, optional
            Whether the feature is a decision node, by default True

        Returns
        -------
        func : function
            The function to show the popup menu
        """

        def func(event):
            """The function to show the popup menu"""
            popup_menu = tk.Menu(self.feature_list_view, tearoff=0)
            chip = self.chips[idx] if idx < len(self.chips) else None
            selected_chips = list(self.selected_chips)
            show_group_menu = len(selected_chips) > 1 and chip in selected_chips
            if show_group_menu:
                popup_menu.add_command(
                    label="Group Selected Features",
                    command=lambda chips=selected_chips: group_selected_features(chips),
                )
            else:
                self.clear_selection()
            if self.get_group_bounds(idx) is not None:
                popup_menu.add_command(
                    label="Ungroup",
                    command=lambda: ungroup_feature(idx),
                )
            popup_menu.add_command(label="Delete", command=lambda: delete_feature(idx))
            if flag:
                popup_menu.add_command(
                    label="Insert Before", command=lambda: insert_before(idx)
                )
                popup_menu.add_command(
                    label="Insert After", command=lambda: insert_after(idx)
                )

                feature = self.features[idx]
                if feature and "true" not in feature and "false" not in feature:
                    popup_menu.add_command(
                        label="Turn into Decision Node",
                        command=lambda: turn_into_decision_node(idx),
                    )
                elif feature and ("true" in feature or "false" in feature):
                    popup_menu.add_command(
                        label="Turn into Normal Node",
                        command=lambda: turn_into_normal_node(idx),
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
            self.update_feature_content()
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
            self.update_feature_content()
            self.draw_feature_list_graph(False)

        def insert_after(idx):
            """Insert the feature after the current feature

            Parameters
            ----------
            idx : int
                The index of the feature
            """
            self.features.insert(
                idx,
                (
                    dict(self.features[idx])
                    if type(self.features[idx]) == dict
                    else self.features[idx]
                ),
            )
            i = self.feature_structure.index(idx)
            for _, c in enumerate(self.feature_structure):
                if type(c) == int and c > idx:
                    self.feature_structure[_] = c + 1
            self.feature_structure.insert(i + 1, idx + 1)

            # update text
            self.update_feature_content()
            self.draw_feature_list_graph(False)

        def turn_into_decision_node(idx):
            """Turn the feature into a decision node

            Parameters
            ----------
            idx : int
                The index of the feature
            """
            feature = self.features[idx]
            if type(feature) == str:
                self.features[idx] = {
                    "name": getattr(feature_related_functions, feature)
                }
            if "true" not in self.features[idx]:
                self.features[idx]["true"] = []
            if "false" not in self.features[idx]:
                self.features[idx]["false"] = []

            # update text
            self.update_feature_content()
            self.draw_feature_list_graph(False)

        def turn_into_normal_node(idx):
            """Turn the feature into a normal node

            Parameters
            ----------
            idx : int
                The index of the feature
            """
            feature = self.features[idx]
            if type(feature) == dict:
                if "true" in feature:
                    del self.features[idx]["true"]
                if "false" in feature:
                    del self.features[idx]["false"]

            # update text
            self.update_feature_content()
            self.draw_feature_list_graph(False)

        def group_selected_features(chips_to_group):
            """Move selected feature nodes together at the first selected position."""
            selected_indexes = [
                index for index, chip in enumerate(self.chips) if chip in chips_to_group
            ]
            if len(selected_indexes) < 2:
                return

            # sort selected indexes
            selected_indexes.sort()

            start_index = self.feature_structure.index(selected_indexes[0])
            end_index = self.feature_structure.index(selected_indexes[-1])

            if not self.is_valid_grouping(start_index, end_index):
                messagebox.showerror(
                    title="Feature Group Error",
                    message=(
                        "The selected features overlap an existing group or "
                        "share its final node and cannot be grouped together."
                    ),
                )
                return

            self.feature_structure.insert(start_index, "(")
            self.feature_structure.insert(end_index + 2, ")")

            self.update_feature_content()
            self.draw_feature_list_graph(False)

        def ungroup_feature(idx):
            """Remove the innermost group containing the selected feature."""
            bounds = self.get_group_bounds(idx)
            if bounds is None:
                return
            start_index, end_index = bounds
            del self.feature_structure[end_index]
            del self.feature_structure[start_index]

            self.update_feature_content()
            self.draw_feature_list_graph(False)

        return func

    def calculate_arrow_image_height(self):
        """Calculate the height of the arrow image

        Returns
        -------
        image_height : int
            The height of the arrow image
        """
        image_height = 0
        h = 0
        for c in self.feature_structure:
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
        content : str
            The feature list text
        """
        if (
            len(self.features) == 1
            and type(self.features[0]) is str
            and self.features[0] in {"break", "continue"}
        ):
            return self.features[0]

        content = "["
        for c in self.feature_structure:
            if c == "(":
                content += "("
                continue
            elif c == ")":
                content += ")"
            else:
                feature = self.features[c]
                if type(feature) is str:
                    content += f'"{feature}",'
                    continue
                content += "{" + f'"name": {feature["name"].__name__}, '
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
                    content += f'"args": ({arg_str}),'
                # "true"
                if "true" in feature:
                    content += (
                        f'"true": {convert_feature_list_to_str(feature["true"])},'
                    )
                # "false"
                if "false" in feature:
                    content += (
                        f'"false": {convert_feature_list_to_str(feature["false"])},'
                    )
                content += "}"
            content += ","
        content += "]"
        return content

    def start_drag(self, event, name, chip=None):
        self.drag_name = name
        self.drag_chip = chip
        self.drag_window = tk.Toplevel(self.feature_list_view)
        self.drag_window.overrideredirect(True)
        self.drag_window.attributes("-topmost", True)
        ttk.Label(self.drag_window, text=name, padding=(12, 7), relief="solid").pack()
        self.drag_start = (event.x_root, event.y_root)
        self.move_drag_window(event.x_root, event.y_root)

    def start_palette_drag(self, event, name):
        self.clear_selection()
        return self.start_drag(event, name)

    def start_branch_palette_drag(self, event, name, branch_controllers):
        """Start dragging a configuration-palette item to a branch board."""
        previous_button = self.selected_branch_palette_button
        if (
            previous_button is not None
            and previous_button is not event.widget
            and previous_button.winfo_exists()
        ):
            previous_button.state(["!pressed"])
        self.selected_branch_palette_button = event.widget
        self.branch_drag_start = (event.x_root, event.y_root)
        self.branch_drag_target = None
        self.branch_drag_targets = branch_controllers
        self.branch_drag_window = tk.Toplevel(self.feature_list_view)
        self.branch_drag_window.overrideredirect(True)
        self.branch_drag_window.attributes("-topmost", True)
        ttk.Label(
            self.branch_drag_window, text=name, padding=(12, 7), relief="solid"
        ).pack()
        self.move_branch_drag_window(event.x_root, event.y_root)

    def move_branch_drag_window(self, root_x, root_y):
        """Move the configuration-palette drag preview."""
        if self.branch_drag_window:
            self.branch_drag_window.geometry(f"+{root_x + 12}+{root_y + 12}")

    def branch_palette_drag_motion(self, event):
        """Show an insertion marker on the branch board below the pointer."""
        if self.branch_drag_start is None:
            return "break"
        self.move_branch_drag_window(event.x_root, event.y_root)
        target = next(
            (
                controller
                for controller in self.branch_drag_targets
                if controller.board_point(event) is not None
            ),
            None,
        )
        if (
            target is not self.branch_drag_target
            and self.branch_drag_target is not None
        ):
            self.branch_drag_target.marker.place_forget()
        self.branch_drag_target = target
        if target is not None:
            point = target.board_point(event)
            target.show_marker(target.index_at(*point))
        return "break"

    def finish_branch_palette_drag(self, event, name, on_click):
        """Insert a palette feature into the branch receiving the drop."""
        if self.branch_drag_window:
            self.branch_drag_window.destroy()
        self.branch_drag_window = None
        moved = self.branch_drag_start is not None and (
            abs(event.x_root - self.branch_drag_start[0]) >= 5
            or abs(event.y_root - self.branch_drag_start[1]) >= 5
        )
        target = self.branch_drag_target
        release_target = next(
            (
                controller
                for controller in self.branch_drag_targets
                if controller.board_point(event) is not None
            ),
            None,
        )
        if target is not None and target is not release_target:
            target.marker.place_forget()
        target = release_target
        if moved and target is not None:
            point = target.board_point(event)
            if point is not None:
                target.insert_feature(target.index_at(*point), name)
                target.update_feature_content()
                target.draw_feature_list_graph(False)
        elif not moved:
            on_click(name)

        if target is not None:
            target.marker.place_forget()
        self.branch_drag_start = None
        self.branch_drag_target = None
        self.branch_drag_targets = []
        return "break"

    def move_drag_window(self, root_x, root_y):
        if self.drag_window:
            self.drag_window.geometry(f"+{root_x + 12}+{root_y + 12}")

    def drag_motion(self, event):
        if not self.drag_name or self.board_canvas is None:
            return "break"
        self.move_drag_window(event.x_root, event.y_root)
        point = self.board_point(event)
        if point:
            x, y = point
            self.insert_index = self.index_at(x, y)
            self.show_marker(self.insert_index)
        else:
            self.insert_index = None
            if self.marker is not None:
                self.marker.place_forget()

    def finish_drag(self, event):
        if self.drag_window:
            self.drag_window.destroy()
        self.drag_window = None
        point = self.board_point(event)
        was_click = (
            self.drag_chip is not None
            and self.drag_start is not None
            and (
                abs(event.x_root - self.drag_start[0]) < 5
                and abs(event.y_root - self.drag_start[1]) < 5
            )
        )
        if was_click:
            self.show_config_popup(self.chips.index(self.drag_chip))(event)
        elif self.drag_name and point:
            index = self.index_at(*point)
            if self.drag_chip is None:
                self.insert_feature(index, self.drag_name)
            else:
                self.move_feature(self.chips.index(self.drag_chip), index)
            self.update_feature_content()
            self.draw_feature_list_graph(False)
        self.drag_name = None
        self.drag_chip = None
        self.drag_start = None
        self.insert_index = None
        if self.marker is not None:
            self.marker.place_forget()
        return "break"

    def board_point(self, event):
        """Return the mouse position in the horizontally scrolling board."""
        if self.board_canvas is None:
            return None
        view_x = event.x_root - self.board_canvas.winfo_rootx()
        view_y = event.y_root - self.board_canvas.winfo_rooty()
        if not (
            0 <= view_x <= self.board_canvas.winfo_width()
            and 0 <= view_y <= self.board_canvas.winfo_height()
        ):
            return None
        return self.board_canvas.canvasx(view_x), self.board_canvas.canvasy(view_y)

    def handle_chip_press(self, event, chip):
        self.board_canvas.focus_set()
        if event.state & 0x0001:
            return self.toggle_selection(chip)
        self.clear_selection()
        return self.start_drag(event, chip.cget("text"), chip)

    def toggle_selection(self, chip):
        """Toggle a feature node in the current Shift-click selection."""
        if chip in self.selected_chips:
            self.selected_chips.remove(chip)
        else:
            self.selected_chips.append(chip)
        self.refresh_chip_styles()
        return "break"

    def refresh_chip_styles(self):
        """Render selected feature nodes using the ttk pressed state."""
        for chip in self.chips:
            chip.state(["pressed"] if chip in self.selected_chips else ["!pressed"])

    def clear_selection(self):
        """Clear the selected feature nodes."""
        if self.selected_chips:
            self.selected_chips.clear()
            self.refresh_chip_styles()

    def get_group_bounds(self, feature_index):
        """Return the innermost parenthesis pair enclosing a feature index."""
        feature_position = self.feature_structure.index(feature_index)
        open_groups = []
        for position, value in enumerate(self.feature_structure[:feature_position]):
            if value == "(":
                open_groups.append(position)
            elif value == ")" and open_groups:
                open_groups.pop()

        if not open_groups:
            return None

        start_index = open_groups[-1]
        depth = 0
        for position in range(start_index, len(self.feature_structure)):
            value = self.feature_structure[position]
            if value == "(":
                depth += 1
            elif value == ")":
                depth -= 1
                if depth == 0:
                    return start_index, position
        return None

    def is_valid_grouping(self, start_index, end_index):
        """Return whether a new group can be inserted without overlap."""

        def nesting_depth_before(position):
            depth = 0
            for value in self.feature_structure[:position]:
                if value == "(":
                    depth += 1
                elif value == ")":
                    depth -= 1
            return depth

        group_boundaries_match = nesting_depth_before(
            start_index
        ) == nesting_depth_before(end_index + 1)
        last_node_already_ends_group = (
            end_index + 1 < len(self.feature_structure)
            and self.feature_structure[end_index + 1] == ")"
        )
        return group_boundaries_match and not last_node_already_ends_group

    def layout_chips(self):
        if self.board_canvas is None or self.board_canvas.winfo_width() <= 1:
            return
        self.chip_positions = []
        for chip in self.chips:
            chip.update_idletasks()
            self.chip_positions.append(
                (
                    chip.winfo_x(),
                    chip.winfo_y(),
                    chip.winfo_width(),
                    chip.winfo_height(),
                )
            )
        content_width = max(
            self.board_canvas.winfo_width(), self.feature_list_view.winfo_reqwidth()
        )
        content_height = max(
            self.board_canvas.winfo_height(), self.feature_list_view.winfo_reqheight()
        )
        self.board_canvas.itemconfigure(
            self.board_window, width=content_width, height=content_height
        )
        self.board_canvas.configure(scrollregion=(0, 0, content_width, content_height))

    def index_at(self, x, y):
        if not self.chip_positions:
            return 0
        for index, (left, top, width, height) in enumerate(self.chip_positions):
            if y < top + height and (y < top or x < left + width // 2):
                return index
        return len(self.chip_positions)

    def show_marker(self, index):
        if self.marker is None:
            return
        if index >= len(self.chip_positions):
            if self.chip_positions:
                left, top, width, height = self.chip_positions[-1]
                self.marker.place(
                    x=left + width + self.CHIP_GAP // 2,
                    y=top + 3,
                    height=height - 6,
                )
            else:
                self.marker.place(x=self.CHIP_GAP, y=self.CHIP_GAP, height=30)
            return
        left, top, _width, height = self.chip_positions[index]
        self.marker.place(x=left - self.CHIP_GAP // 2, y=top + 3, height=height - 6)

    def insert_feature(self, index, feature_name):
        """Insert a palette feature at its displayed position.

        parameters
        ----------
        index : int
            The index of the feature.
        feature_name : str
            The name of the feature to insert.
        """
        feature = (
            feature_name.lower()
            if feature_name in {"Break", "Continue"}
            else {"name": getattr(feature_related_functions, feature_name)}
        )
        if type(feature) is str:
            # Break and continue are terminal branch nodes.  They replace the
            # entire branch rather than becoming one item in a feature list.
            self.features = [feature]
            self.feature_structure = [0]
            return
        if (
            len(self.features) == 1
            and type(self.features[0]) is str
            and self.features[0] in {"break", "continue"}
        ):
            # A normal feature starts a new branch, replacing its terminal node.
            self.features = []
            self.feature_structure = []
            index = 0
        structure_index = (
            self.feature_structure.index(index)
            if index < len(self.features)
            else len(self.feature_structure)
        )
        if index >= 1:
            pre_structure_index = self.feature_structure.index(index - 1)
            if pre_structure_index + 1 < structure_index:
                while (
                    pre_structure_index + 1 < len(self.feature_structure)
                    and self.feature_structure[pre_structure_index + 1] == ")"
                ):
                    pre_structure_index += 1
                structure_index = pre_structure_index + 1

        for structure_pos, value in enumerate(self.feature_structure):
            if type(value) is int and value >= index:
                self.feature_structure[structure_pos] += 1
        self.features.insert(index, feature)
        self.feature_structure.insert(structure_index, index)

    def move_feature(self, old_index, new_index):
        """Move a feature and its structure entry to the drop position."""
        destination = new_index - 1 if new_index > old_index else new_index
        if old_index == destination:
            return

        old_order = list(range(len(self.features)))
        moved_identity = old_order.pop(old_index)
        old_order.insert(destination, moved_identity)

        new_structure = list(self.feature_structure)
        new_structure.remove(moved_identity)
        successor = (
            old_order[destination + 1] if destination + 1 < len(old_order) else None
        )
        if successor is None:
            new_structure.append(moved_identity)
        else:
            new_structure.insert(new_structure.index(successor), moved_identity)

        # A group must contain at least two direct elements.  Moving an item out
        # of a group can leave a one-item loop behind and cause errors; remove all one-item group.
        grouped_structure = [[]]
        for token in new_structure:
            if token == "(":
                grouped_structure.append([])
            elif token == ")" and len(grouped_structure) > 1:
                group = grouped_structure.pop()
                if len(group) == 1:
                    grouped_structure[-1].extend(group)
                else:
                    grouped_structure[-1].append(group)
            else:
                grouped_structure[-1].append(token)

        def flatten_structure(group):
            flattened = []
            for token in group:
                if type(token) is list:
                    flattened.extend(["(", *flatten_structure(token), ")"])
                else:
                    flattened.append(token)
            return flattened

        new_structure = flatten_structure(grouped_structure[0])

        new_index_by_identity = {
            identity: index for index, identity in enumerate(old_order)
        }
        self.features = [self.features[identity] for identity in old_order]
        self.feature_structure = [
            new_index_by_identity[token] if type(token) is int else token
            for token in new_structure
        ]


def verify_feature_list(content):
    """Verify if feature list is valid

    Parameters
    ----------
    content : str
        The feature list content

    Returns
    -------
    feature list : list
        feature list
    """
    feature_list_content = "".join(content.split("\n"))
    if feature_list_content in ["break", '"break"', "'break'"]:
        return ["break"]
    if feature_list_content in ["continue", '"continue"', "'continue'"]:
        return ["continue"]
    feature_list = convert_str_to_feature_list(feature_list_content)
    if feature_list is None:
        messagebox.showerror(
            title="Feature List Error",
            message="There is something wrong for this feature "
            "list, please verify there is no "
            "spelling error!",
        )
    return feature_list
