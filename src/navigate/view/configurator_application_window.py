# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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

# Standard Library Imports
import tkinter as tk
from tkinter import ttk, simpledialog
import logging
from pathlib import Path
from typing import Optional, Callable
import os
from PIL import Image, ImageTk

# Third Party Imports

# Local Imports
from navigate.view.custom_widgets.DockableNotebook import DockableNotebook
from navigate.view.custom_widgets.CollapsibleFrame import CollapsibleFrame
from navigate.view.custom_widgets.common import uniform_grid
from navigate.view.style import apply_styles

# Logger Setup
p = __name__.split(".")[1]

widget_types = {
    "Combobox": ttk.Combobox,
    "Input": ttk.Entry,
    "Spinbox": ttk.Spinbox,
    "Checkbutton": ttk.Checkbutton,
    "Button": ttk.Button,
}

variable_types = {
    "string": tk.StringVar,
    "float": tk.DoubleVar,
    "bool": tk.BooleanVar,
    "int": tk.IntVar,
}


class ConfigurationAssistantWindow(ttk.Frame):
    def __init__(self, root: tk.Tk, *args: list, **kwargs: dict) -> None:
        """Initiates the main application window

        Parameters
        ----------
        root : tk.Tk
            The main window of the application
        *args
            Variable length argument list
        **kwargs
            Arbitrary keyword arguments
        """
        #: tk.Tk: The main window of the application
        self.root = root
        self.root.title("Configuration Assistant")
        self.root.resizable(False, False)
        self.root.geometry("")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        apply_styles(self.root)

        ttk.Frame.__init__(self, self.root, *args, **kwargs)

        #: logging.Logger: The logger for this class
        self.logger = logging.getLogger(p)

        view_directory = Path(__file__).resolve().parent
        try:
            photo_image = view_directory.joinpath("icon", "mic.png")
            self.root.iconphoto(True, tk.PhotoImage(file=photo_image))
        except tk.TclError:
            pass

        #: ttk.Frame: The top frame of the application
        self.top_frame = ttk.Frame(self.root)

        #: ttk.Frame: The main frame of the application
        self.microscope_frame = ttk.Frame(self.root)

        self.top_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=3, pady=3)
        self.microscope_frame.grid(
            row=1, column=0, columnspan=6, sticky=tk.NSEW, padx=3, pady=3
        )

        #: ttk.Frame: The top frame of the application
        self.top_window = TopWindow(self.top_frame, self.root)
        uniform_grid(self.root)


class TopWindow(ttk.Frame):
    """Top Frame for Configuration Assistant.

    This class is the initial window for the configurator application.
    It contains the following:
    - Entry for number of configurations
    - Continue button
    - Cancel button
    """

    def __init__(
        self, main_frame: ttk.Frame, root: tk.Tk, *args: list, **kwargs: dict
    ) -> None:
        """Initialize Top Frame.

        Parameters
        ----------
        main_frame : ttk.Frame
            Window to place widgets in.
        root : tk.Tk
            Root window of the application.
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.
        """

        #: ttk.Frame: The main frame of the application
        self.microscope_frame = main_frame
        super().__init__(root, *args, **kwargs)

        column = 0
        try:
            # Load the logo image
            logo_path = os.path.join(os.path.dirname(__file__), "icon", "mic.png")
            pil_image = Image.open(logo_path)
            resized_image = pil_image.resize((110, 110), Image.Resampling.BILINEAR)

            # Override default style
            style = ttk.Style()
            style.configure("Logo.TLabel", background="#fafafa")

            self.logo_image = ImageTk.PhotoImage(resized_image)
            self.logo_label = ttk.Label(
                root, image=self.logo_image, style="Logo.TLabel"
            )
            self.logo_label.grid(row=0, column=column, sticky=tk.NSEW, padx=3, pady=0)
            column += 1
        except tk.TclError:
            pass

        self.new_button = ttk.Button(root, text="New Configuration")
        self.new_button.grid(row=0, column=column, sticky=tk.EW, padx=3, pady=(10, 1))
        self.new_button.config(width=15)
        column += 1

        self.load_button = ttk.Button(root, text="Load Configuration")
        self.load_button.grid(row=0, column=column, sticky=tk.EW, padx=3, pady=(10, 1))
        self.load_button.config(width=15)
        column += 1

        self.add_button = ttk.Button(root, text="Add A Microscope")
        self.add_button.grid(row=0, column=column, sticky=tk.EW, padx=3, pady=(10, 1))
        self.add_button.config(width=15)
        column += 1

        self.save_button = ttk.Button(root, text="Save")
        self.save_button.grid(row=0, column=column, sticky=tk.EW, padx=3, pady=(10, 1))
        self.save_button.config(width=15)
        column += 1

        self.cancel_button = ttk.Button(root, text="Cancel")
        self.cancel_button.grid(
            row=0, column=column, sticky=tk.EW, padx=3, pady=(10, 1)
        )
        self.cancel_button.config(width=15)

        uniform_grid(self)


class MicroscopeWindow(DockableNotebook):
    def __init__(
        self, frame: ttk.Frame, root: tk.Tk, *args: list, **kwargs: dict
    ) -> None:
        """Initialize Microscope Frame.

        Parameters
        ----------
        main_frame : ttk.Frame
            Window to place widgets in.
        root : tk.Tk
            Root window of the application.
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.
        """

        DockableNotebook.__init__(self, frame, root, *args, **kwargs)
        self.grid(row=0, column=0, sticky=tk.NSEW)
        self.menu.delete("Popout Tab")
        self.menu.add_command(label="Rename", command=self.rename_microscope)
        self.menu.add_command(label="Delete", command=self.delete_microscope)

    def rename_microscope(self) -> None:
        """Rename microscope"""

        if self.selected_tab_id is None:
            return
        result = simpledialog.askstring("Input", "Enter microscope name:")
        if result:
            tab_name = self.tab(self.selected_tab_id, option="text")
            self.tab(self.selected_tab_id, text=result)
            self.tab_list.remove(tab_name)
            self.tab_list.append(result)

    def delete_microscope(self) -> None:
        """Delete selected microscope"""
        if self.selected_tab_id is None:
            return
        tab_name = self.tab(self.selected_tab_id, option="text")
        self.forget(self.selected_tab_id)
        self.tab_list.remove(tab_name)


class MicroscopeTab(DockableNotebook):
    def __init__(
        self, parent: ttk.Frame, root: tk.Tk, *args: list, **kwargs: dict
    ) -> None:
        """Initialize Microscope Tab.

        Parameters
        ----------
        main_frame : ttk.Frame
            Window to place widgets in.
        root : tk.Tk
            Root window of the application.
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.
        """
        DockableNotebook.__init__(self, parent, root, *args, **kwargs)
        uniform_grid(self)

    def create_hardware_tab(
        self,
        name: str,
        hardware_widgets: dict,
        widgets: Optional[dict] = None,
        top_widgets: Optional[dict] = None,
        **kwargs,
    ) -> None:
        """Create hardware tab

        Parameters
        ----------
        name : str
            tab name/hardware name
        hardware_widgets : dict
            hardware widgets dict
        widgets : dict
            constants widgets dict
        top_widgets : dict
            button widgets dict
        *args : list
            Variable length argument list.
        **kwargs : dict
            Arbitrary keyword arguments
        """
        tab = HardwareTab(
            name, hardware_widgets, widgets=widgets, top_widgets=top_widgets, **kwargs
        )

        tab.widgets = hardware_widgets
        self.tab_list.append(tab)
        self.add(tab, text=name, sticky=tk.NSEW)


class HardwareTab(ttk.Frame):
    def __init__(
        self,
        name: str,
        hardware_widgets: dict,
        *args: list,
        widgets: Optional[dict] = None,
        top_widgets: Optional[dict] = None,
        hardware_widgets_value: Optional[list[dict]] = None,
        constants_widgets_value: Optional[list[dict]] = None,
        **kwargs,
    ) -> None:
        """Initialize Microscope Tab.

        Parameters
        ----------
        name : str
            tab name/hardware name
        hardware_widgets : dict
            hardware widgets dict
        widgets : dict
            constants widgets dict
        top_widgets : dict
            button widgets dict
        hardware_widgets_value : list[dict]
           list of values for hardware widgets
        constants_widgets_value : list[dict]
           list of values for constants widgets
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments
        """
        # Init Frame
        ttk.Frame.__init__(self, *args, **kwargs)

        if constants_widgets_value is None:
            constants_widgets_value = [None]

        if hardware_widgets_value is None:
            hardware_widgets_value = [None]

        self.hardware_widgets = hardware_widgets
        self.widgets = widgets
        self.top_widgets = top_widgets
        self.constants_widgets_value = constants_widgets_value
        self.hardware_widgets_value = hardware_widgets_value

        # Configure the frame to expand properly
        self.columnconfigure(index=0, weight=1)
        self.rowconfigure(index=3, weight=1)

        self.name = name
        scroll_frame = ttk.Frame(self)
        scroll_frame.grid(row=3, column=0, sticky=tk.NSEW)

        # Prevent the scroll_frame from resizing to fit contents
        scroll_frame.grid_propagate(False)

        # Set minimum size for scroll_frame
        scroll_frame.grid_rowconfigure(0, weight=1, minsize=400)
        scroll_frame.grid_columnconfigure(0, weight=1, minsize=600)

        # Create canvas with specific dimensions, explicitly define background.
        style = ttk.Style()
        frame_bg = style.lookup(style="TFrame", option="background")
        canvas = tk.Canvas(scroll_frame, height=500, width=600, background=frame_bg)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        canvas.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)

        # Configure grid weights in scroll_frame
        scroll_frame.rowconfigure(0, weight=1)
        scroll_frame.columnconfigure(0, weight=1)

        # Configure content_frame to expand horizontally
        content_frame = ttk.Frame(canvas)
        content_frame.columnconfigure(index=0, weight=1)
        content_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add binding to handle canvas resize and update content_frame width
        def _configure_canvas(event: tk.Event) -> None:
            # Update the width of content_frame to fill canvas
            canvas.itemconfigure("win", width=event.width)

            # Ensure the scroll region is updated
            canvas.configure(scrollregion=canvas.bbox("all"))

        # Add tag to canvas window for easier reference
        canvas.create_window((0, 0), window=content_frame, anchor="nw", tags="win")
        canvas.bind("<Configure>", _configure_canvas)

        self.top_frame = ttk.Frame(content_frame)
        self.top_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=10)

        self.hardware_frame = ttk.Frame(content_frame)
        self.hardware_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=10)

        self.bottom_frame = ttk.Frame(content_frame)
        self.bottom_frame.grid(row=2, column=0, sticky=tk.NSEW, padx=10)

        self.frame_row = 0
        self.row_offset = self.frame_row + 1

        self.variables = {}
        self.values_dict = {}
        self.variables_list = []

        self.build_widgets(top_widgets, parent=self.top_frame)

        for widgets_value in hardware_widgets_value:
            self.build_widgets(
                hardware_widgets,
                parent=self.hardware_frame,
                widgets_value=widgets_value,
            )

        for widgets_value in constants_widgets_value:
            self.build_widgets(widgets, widgets_value=widgets_value)

    def create_hardware_widgets(
        self,
        hardware_widgets: dict,
        frame: ttk.Frame,
        direction: Optional[str] = "vertical",
        synthetic: Optional[bool] = False,
    ) -> None:
        """Create UI widgets for hardware configuration.

        Parameters
        ----------
        hardware_widgets : dict
            Dictionary where keys are setting names and values are tuples
            containing (display_name, widget_type, value_type, values, info, default).
        frame : ttk.Frame
            The parent frame to which widgets are added.
        direction : str, optional
            Layout direction: "vertical" or "horizontal", by default "vertical".
        synthetic : bool, optional
            If True, only create the first widget and return, by default False.
        """
        if hardware_widgets is None:
            return

        content_frame = (
            frame.content_frame if isinstance(frame, CollapsibleFrame) else frame
        )
        row_index = 0

        for key, config in hardware_widgets.items():
            if key == "frame_config":
                continue

            display_name, widget_type, value_type = config[0], config[1], config[2]
            values = config[3] if len(config) > 3 else None
            info_text = config[4] if len(config) > 4 else None
            default_value = config[5] if len(config) > 5 else None

            if widget_type == "Label":
                row_index = self._create_section_label(
                    content_frame, display_name, row_index
                )
                continue

            if widget_type == "Button":
                widget = self._create_button_widget(
                    content_frame, display_name, hardware_widgets, key, frame
                )
            else:
                widget, label = self._create_labeled_input_widget(
                    content_frame,
                    key,
                    display_name,
                    widget_type,
                    value_type,
                    values,
                    default_value,
                    direction,
                    row_index,
                )

            self._place_widget(widget, direction, row_index, is_info=False)

            if info_text:
                self._place_info_label(content_frame, info_text, direction, row_index)

            if row_index == 0 and synthetic:
                return
            row_index += 1

    @staticmethod
    def _create_section_label(parent: ttk.Frame, text: str, row_index: int) -> int:
        """Create a section label and separator in the widget layout.

        Parameters
        ----------
        parent : ttk.Frame
            The parent frame to which the label and separator are added.
        text : str
            The text for the section label.
        row_index : int
            The current row index for placing the label and separator.

        Returns
        -------
        int
            The updated row index after adding the label and separator.
        """
        label = ttk.Label(parent, text=text)
        label.grid(row=row_index, column=0, sticky=tk.NW, padx=3)

        separator = ttk.Separator(parent)
        separator.grid(row=row_index + 1, columnspan=2, sticky=tk.NSEW, padx=3)

        return row_index + 2

    def _create_button_widget(
        self,
        parent: ttk.Frame,
        text: str,
        widgets_dict: dict,
        key: str,
        frame: ttk.Frame,
    ) -> ttk.Button:
        """Create a button widget.

        Parameters
        ----------
        parent : ttk.Frame
            The parent frame to which the button is added.
        text : str
            The text for the button.
        widgets_dict : dict
            Dictionary containing the button's configuration.
        key : str
            The key for the button in the widgets_dict.
        frame : ttk.Frame
            The parent frame for the button.

        Returns
        -------
        ttk.Button
            The created button widget.
        """

        return ttk.Button(
            parent,
            text=text,
            command=self.build_event_handler(widgets_dict, key, frame, self.frame_row),
        )

    def _create_labeled_input_widget(
        self,
        parent: ttk.Frame,
        key: str,
        label_text: str,
        widget_type: str,
        value_type: str,
        values: dict,
        default_value: str,
        direction: str,
        row_index: int,
    ) -> tuple:
        """Create a labeled input widget (Checkbutton, Entry, Combobox, Spinbox).

        Parameters
        ----------
        parent : tk.Frame
            The parent frame to which the widget and label are added.
        key : str
            The key for the widget in the widgets_dict.
        label_text : str
            The text for the label.
        widget_type : str
            The type of widget to create (Checkbutton, Entry, Combobox, Spinbox).
        value_type : str
            The type of value the widget will hold (string, float, bool, int).
        values : dict
            The values for the widget (e.g., options for Combobox).
        default_value : str
            The default value for the widget.
        direction : str
            The layout direction: "vertical" or "horizontal".
        row_index : int
            The current row index for placing the widget and label.

        Returns
        -------
        tuple
            The widget and associated label.
        """
        self.variables[key] = variable_types[value_type]()
        label_text = label_text if label_text.endswith(":") else label_text + " :"
        label = ttk.Label(parent, text=label_text)

        if direction == "vertical":
            label.grid(row=row_index, column=0, sticky=tk.NW, padx=(3, 10), pady=3)
        else:
            label.grid(row=0, column=row_index, sticky=tk.NW, padx=(5, 3), pady=3)

        if widget_type == "Checkbutton":
            widget = widget_types[widget_type](
                parent, text="", variable=self.variables[key]
            )
        else:
            widget = widget_types[widget_type](
                parent, textvariable=self.variables[key], width=30
            )

        if widget_type == "Combobox":
            self._configure_combobox(widget, key, values, value_type)
        elif widget_type == "Spinbox":
            self._configure_spinbox(widget, values)

        if default_value is not None:
            self.variables[key].set(str(default_value))

        return widget, label

    def _configure_combobox(
        self, widget: ttk.Combobox, key: str, values: dict, value_type: str
    ) -> None:
        """Configure a combobox widget.

        Parameters
        ----------
        widget : ttk.Combobox
            The combobox widget to configure.
        key : str
            The key for the combobox in the widgets_dict.
        values : dict
            The values for the combobox options.
        value_type : str
            The type of value the combobox will hold (string, float, bool, int).
        """
        if isinstance(values, list):
            values = {v: v for v in values}
        self.values_dict[key] = values
        options = list(values.keys())

        widget.config(values=options)
        widget.state(["!disabled", "readonly"])
        widget.set(str(options[-1]) if value_type == "bool" else options[-1])

        # Add binding for device type changes
        if key.endswith("/type") or key == "type":
            widget.bind(
                "<<ComboboxSelected>>", lambda e: self._on_device_type_changed(e, key)
            )

    def _on_device_type_changed(self, event, key):
        """Handle device type change event.

        Parameters
        ----------
        event : tk.Event
            The event that triggered this callback.
        key : str
            The key of the combobox that changed.
        """
        # Get the selected device type
        event_widget = event.widget
        selected_value = event_widget.get()
        is_virtual = "Virtual Device" in selected_value

        # Determine which widgets to rebuild
        if key.startswith("hardware/"):
            # For hardware/type fields, rebuild entire hardware section
            self.variables_list = [
                vl for vl in self.variables_list if vl[2] != "hardware"
            ]

            # Clear hardware frame
            for widget in list(self.hardware_frame.winfo_children()):
                widget.destroy()

            # Rebuild hardware widgets
            self.build_widgets(
                self.hardware_widgets, parent=self.hardware_frame, synthetic=is_virtual
            )
        else:
            # For nested device types, find the appropriate frame to rebuild
            # (like zoom, galvo, or laser components)
            current_frame = event_widget.master
            while current_frame is not None:
                # Find the nearest parent frame or collapsible frame
                if (
                    isinstance(current_frame, (ttk.Frame, CollapsibleFrame))
                    and current_frame != event_widget.master
                ):
                    # Found a suitable parent frame
                    break
                current_frame = current_frame.master

            if current_frame is None or current_frame == self:
                # Fallback to rebuilding the entire hardware section
                for widget in list(self.hardware_frame.winfo_children()):
                    widget.destroy()
                self.build_widgets(
                    self.hardware_widgets,
                    parent=self.hardware_frame,
                    synthetic=is_virtual,
                )
            else:
                # Create a parent frame to replace the one we're rebuilding
                parent = current_frame.master

                if parent is not None:
                    # Remember the grid options
                    grid_info = current_frame.grid_info()

                    # Remove old frame but don't destroy until we're done with it
                    current_frame.grid_forget()

                    # Create a new frame in the same position
                    new_frame = ttk.Frame(parent)
                    new_frame.grid(**grid_info)

                    # For complex widgets or Lasers which might have list structure
                    if key == "type" or key.endswith("/type"):
                        # Find appropriate configuration to rebuild
                        for (
                            hardware_key,
                            widgets_config,
                        ) in self.hardware_widgets.items():
                            if hardware_key == key or hardware_key.endswith("/" + key):
                                if isinstance(widgets_config, dict):
                                    self.build_widgets(widgets_config, parent=new_frame)
                                elif isinstance(widgets_config, list):
                                    # Handle special case for lasers or complex widgets
                                    self.build_widgets(
                                        widgets_config[0], parent=new_frame
                                    )
                                break

                    # Now destroy the old frame
                    current_frame.destroy()

    @staticmethod
    def _configure_spinbox(widget: ttk.Spinbox, values: dict) -> None:
        """Configure a spinbox widget with range and increment.

        Parameters
        ----------
        widget : ttk.Spinbox
            The spinbox widget to configure.
        values : dict
            The values for the spinbox range and increment.
        """

        if not isinstance(values, dict):
            values = {}
        widget.config(
            from_=values.get("from", 0),
            to=values.get("to", 100000),
            increment=values.get("step", 1),
        )
        widget.set(values.get("from", 0))

    @staticmethod
    def _place_widget(
        widget: ttk.Widget,
        direction: str,
        row_index: int,
        is_info: Optional[bool] = False,
    ) -> None:
        """Place a widget in the grid layout based on direction and type.

        Parameters
        ----------
        widget : ttk.Widget
            The widget to place in the grid.
        direction : str
            The layout direction: "vertical" or "horizontal".
        row_index : int
            The current row index for placing the widget.
        is_info : bool
            Whether the widget is an info/help label.
        """
        column = 2 if is_info else 1
        row = row_index if direction == "vertical" else 0
        padx = (10, 10) if is_info else (10, 3)
        pady = 3 if direction == "vertical" else (3, 0)
        sticky = tk.NW if is_info else tk.NSEW

        widget.grid(row=row, column=column, sticky=sticky, padx=padx, pady=pady)

    def _place_info_label(
        self, parent: ttk.Frame, info_text: str, direction: str, row_index: int
    ) -> None:
        """Place an info/help label next to the widget.

        Parameters
        ----------
        parent : ttk.Frame
            The parent frame to which the info label is added.
        info_text : str
            The text for the info/help label.
        direction : str
            The layout direction: "vertical" or "horizontal".
        """
        info_label = ttk.Label(parent, text=info_text)
        self._place_widget(info_label, direction, row_index, is_info=True)

    def build_widgets(
        self,
        widgets: dict,
        parent: Optional[ttk.Frame] = None,
        widgets_value: Optional[dict] = None,
        synthetic: Optional[bool] = False,
        **kwargs: dict,
    ) -> None:
        """
        Build widgets for the UI.

        Parameters
        ----------
        widgets : dict
            Dictionary containing widget configurations.
        parent : Optional[ttk.Frame], optional
            Parent frame to place the widgets, by default None.
        widgets_value : Optional[dict], optional
            Dictionary containing initial values for the widgets, by default None.
        synthetic : bool, optional
            If True, only create the first widget and return, by default False.
        **kwargs : dict
            Additional keyword arguments, such as `ref` (reference name) or `direction`
            (layout direction, e.g., "vertical").
        """
        if not widgets:
            return

        if parent is None:
            parent = self.bottom_frame

        # Extract frame configuration
        collapsible, title, frame_format, ref, direction = self.extract_frame_config(
            widgets, kwargs
        )

        # Create the frame
        frame = self.create_frame(parent, collapsible, title)

        # Initialize variables
        self.initialize_variables(ref, frame_format)

        # Create hardware widgets
        self.create_hardware_widgets(
            widgets, frame=frame, direction=direction, synthetic=synthetic
        )

        # Set widget values
        self.set_widget_values(widgets_value)

    def set_widget_values(self, widgets_value: Optional[dict] = None) -> None:
        """Set values for widgets if widgets_value is provided.

        Parameters
        ----------
        widgets_value : dict
            Dictionary containing widget values.
        """

        if widgets_value:
            for k, v in widgets_value.items():
                if k in self.variables:
                    self.variables[k].set(v)

    def initialize_variables(self, ref: str, widget_format):
        """Initialize variables and values dictionary for the widgets.

        Parameters
        ----------
        ref : str
            Reference name for the widgets.
        widget_format : str
            Format for the widgets.
        """
        self.variables = {}
        self.values_dict = {}
        self.variables_list.append(
            (self.variables, self.values_dict, ref, widget_format)
        )

    @staticmethod
    def extract_frame_config(widgets: dict, kwargs: dict) -> tuple:
        """Extract frame configuration from widgets and kwargs.

        Parameters
        ----------
        widgets : dict
            Widget configuration dictionary.
        kwargs : dict
            Arbitrary keyword arguments.

        Returns
        -------
        tuple
            A tuple containing the frame configuration parameters:
            collapsible (bool), title (str), frame_format (str), ref (str), direction
            (str).
        """
        collapsible = False
        title = "Hardware"
        frame_format = None
        temp_ref = None
        direction = "vertical"

        if "frame_config" in widgets:
            collapsible = widgets["frame_config"].get("collapsible", False)
            title = widgets["frame_config"].get("title", "Hardware")
            frame_format = widgets["frame_config"].get("format", None)
            temp_ref = widgets["frame_config"].get("ref", None)
            direction = widgets["frame_config"].get("direction", "vertical")

        ref = kwargs.get("ref", None) or temp_ref
        direction = kwargs.get("direction", direction)

        return collapsible, title, frame_format, ref, direction

    def create_frame(
        self, parent: ttk.Frame, collapsible: bool, title: str
    ) -> ttk.Frame:
        """Create a frame (collapsible or regular) and place it in the grid.

        Parameters
        ----------
        parent : ttk.Frame
            The parent frame to which the new frame is added.
        collapsible : bool
            Whether the frame should be collapsible.
        title : str
            The title for the frame if it is collapsible.

        Returns
        -------
        tk.Frame
            The created frame.
        """
        if collapsible:
            self.fold_all_frames()
            frame = CollapsibleFrame(parent=parent, title=title)
            frame.label.bind("<Button-1>", self.create_toggle_function(frame))
        else:
            frame = ttk.Frame(parent)

        frame.grid(row=self.frame_row, column=0, sticky=tk.NSEW, padx=20)
        self.frame_row += 1
        return frame

    def fold_all_frames(self, except_frame: Optional[tk.Frame] = None) -> None:
        """Fold all collapsible frames except one frame

        Parameters
        ----------
        except_frame : Optional[tk.Frame]
            the unfold frame
        """
        for child in self.hardware_frame.winfo_children():
            if isinstance(child, CollapsibleFrame) and child is not except_frame:
                child.fold()
        for child in self.bottom_frame.winfo_children():
            if isinstance(child, CollapsibleFrame) and child is not except_frame:
                child.fold()

    def create_toggle_function(self, frame: tk.Frame) -> Callable[..., None]:
        """Toggle collapsible frame

        Parameters
        ----------
        frame : tk.Frame
            the frame to toggle
        """

        def func(event):
            self.fold_all_frames(frame)
            frame.toggle_visibility()

        return func

    def build_event_handler(
        self, hardware_widgets: dict, key: str, frame: ttk.Frame, frame_id: int
    ) -> Callable[..., None]:
        """Build button event handler

        Parameters
        ----------
        hardware_widgets : dict
            widget dict containing the button
        key : str
            reference of the button
        frame : tk.Frame
            the frame to put/delete widgets
        frame_id : int
            index of the frame

        Returns
        -------
        func : Callable
            event handler function
        """

        def func(*args, **kwargs):
            v = hardware_widgets[key]
            if "widgets" in v[2]:
                if "parent" in v[2]:
                    parent = (
                        self.hardware_frame
                        if v[2]["parent"].startswith("hardware")
                        else None
                    )
                else:
                    parent_id = frame.winfo_parent()
                    parent = self.nametowidget(parent_id)
                widgets = (
                    hardware_widgets if v[2]["widgets"] == "self" else v[2]["widgets"]
                )
                self.build_widgets(
                    widgets,
                    parent=parent,
                    ref=v[2].get("ref", None),
                    direction=v[2].get("direction", "vertical"),
                )
                # collapse other frame
            elif v[2].get("delete", False):
                frame.grid_remove()
                self.variables_list[frame_id - self.row_offset] = None

        return func
