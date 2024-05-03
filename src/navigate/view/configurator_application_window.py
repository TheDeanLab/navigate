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

# Standard Library Imports
import tkinter as tk
from tkinter import ttk, simpledialog
import logging
from pathlib import Path
import importlib

# Third Party Imports

# Local Imports
from navigate.view.custom_widgets.DockableNotebook import DockableNotebook
from navigate.view.custom_widgets.CollapsibleFrame import CollapsibleFrame

# Logger Setup
p = __name__.split(".")[1]

widget_types = {
    "Combobox": ttk.Combobox,
    "Input": ttk.Entry,
    "Spinbox": ttk.Spinbox,
    "Checkbutton": ttk.Checkbutton,
    "Button": ttk.Button
}

variable_types = {
    "string": tk.StringVar,
    "float": tk.DoubleVar,
    "bool": tk.BooleanVar,
    "int": tk.IntVar
}
class ConfigurationAssistantWindow(ttk.Frame):
    def __init__(self, root, *args, **kwargs):
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

        ttk.Frame.__init__(self, self.root, *args, **kwargs)

        #: logging.Logger: The logger for this class
        self.logger = logging.getLogger(p)

        view_directory = Path(__file__).resolve().parent
        try:
            photo_image = view_directory.joinpath("icon", "mic.png")
            self.root.iconphoto(True, tk.PhotoImage(file=photo_image))
        except tk.TclError:
            pass

        self.root.resizable(True, True)
        self.root.geometry("")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        #: ttk.Frame: The top frame of the application
        self.top_frame = ttk.Frame(self.root)

        #: ttk.Frame: The main frame of the application
        self.microscope_frame = ttk.Frame(self.root)

        self.grid(column=0, row=0, sticky=tk.NSEW)
        self.top_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=3, pady=3)
        self.microscope_frame.grid(
            row=1, column=0, columnspan=4, sticky=tk.NSEW, padx=3, pady=3
        )

        #: ttk.Frame: The top frame of the application
        self.top_window = TopWindow(self.top_frame, self.root)


class TopWindow(ttk.Frame):
    """Top Frame for Configuration Assistant.

    This class is the initial window for the configurator application.
    It contains the following:
    - Entry for number of configurations
    - Continue button
    - Cancel button
    """

    def __init__(self, main_frame, root, *args, **kwargs):
        """Initialize Acquire Bar.

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
        ttk.Frame.__init__(self, self.microscope_frame, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        self.add_button = tk.Button(root, text="Add A Microscope")
        self.add_button.grid(row=0, column=0, sticky=tk.NE, padx=3, pady=(10, 1))
        self.add_button.config(width=15)

        self.save_button = tk.Button(root, text="Save")
        self.save_button.grid(row=0, column=1, sticky=tk.NE, padx=3, pady=(10, 1))
        self.save_button.config(width=15)

        #: tk.Button: The button to cancel the application.
        self.cancel_button = tk.Button(root, text="Cancel")
        self.cancel_button.grid(row=0, column=3, sticky=tk.NE, padx=3, pady=(10, 1))
        self.cancel_button.config(width=15)


class MicroscopeWindow(DockableNotebook):
    def __init__(self, frame, root, *args, **kwargs):
        DockableNotebook.__init__(self, frame, root, *args, **kwargs)
        self.grid(row=0, column=0, sticky=tk.NSEW)

        self.menu.delete("Popout Tab")
        self.menu.add_command(label="Rename", command=self.rename_microscope)
        self.menu.add_command(label="Delete", command=self.delete_microscope)

    def rename_microscope(self):
        """Rename microscope"""

        result = simpledialog.askstring("Input", "Enter microscope name:")
        if result:
            tab = self.select()
            tab_name = self.tab(tab)["text"]
            self.tab(tab, text=result)
            self.tab_list.remove(tab_name)
            self.tab_list.append(result)

    def delete_microscope(self):
        tab = self.select()
        tab_name = self.tab(tab)["text"]
        current_tab_index = self.index("current")
        if current_tab_index >= 0:
            self.forget(current_tab_index)
            self.tab_list.remove(tab_name)



class MicroscopeTab(DockableNotebook):
    def __init__(self, parent, name, index, root, *args, **kwargs):

        # Init Frame
        DockableNotebook.__init__(self, parent, root, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        
    def create_hardware_tab(self, name, hardware_widgets, widgets=None, top_widgets=None):
        tab = HardwareTab(name, hardware_widgets, widgets=widgets, top_widgets=top_widgets)
        self.tab_list.append(name)
        self.add(tab, text=name, sticky=tk.NSEW)


class HardwareTab(ttk.Frame):
    def __init__(self, name, hardware_widgets, *args, widgets=None, top_widgets=None, **kwargs):
        # Init Frame
        tk.Frame.__init__(self, *args, **kwargs)
        
        self.name = name

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        self.top_frame = ttk.Frame(self)
        self.top_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=20)
        
        self.hardware_frame = ttk.Frame(self)
        self.hardware_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=20)

        self.bottom_frame = ttk.Frame(self)
        self.bottom_frame.grid(row=2, column=0, sticky=tk.NSEW, padx=20)
        self.frame_row = 0
        self.row_offset = self.frame_row + 1

        self.variables = {}
        self.values_dict = {}
        self.variables_list = []

        self.build_widgets(top_widgets, parent=self.top_frame)

        self.build_widgets(hardware_widgets, parent=self.hardware_frame)

        self.build_widgets(widgets)

    
    def build_hardware_widgets(self, hardware_widgets, frame, direction="vertical"):
        """Build hardware widgets
        
        Parameters
        ----------
        hardware_widgets: dict
            name: (display_name, widget_type, value_type, values, condition)
        """
        if hardware_widgets is None:
            return
        if type(frame) is CollapsibleFrame:
            content_frame = frame.content_frame
        else:
            content_frame = frame
        i = 0
        for k, v in hardware_widgets.items():
            if k == "frame_config":
                continue
            if v[1] == "Label":
                label = ttk.Label(content_frame, text=v[0])
                label.grid(row=i, column=0, sticky=tk.NW, padx=3)
                seperator = ttk.Separator(content_frame)
                seperator.grid(row=i+1, columnspan=2, sticky=tk.NSEW, padx=3)
                i += 2
                continue
            elif v[1] != "Button":
                self.variables[k] = variable_types[v[2]]()
                label_text = v[0] + "  :" if v[0][-1] != ":" else v[0]
                label = ttk.Label(content_frame, text=label_text)
                if direction == "vertical":
                    label.grid(row=i, column=0, sticky=tk.NW, padx=(3, 10), pady=3)
                else:
                    label.grid(row=0, column=i, sticky=tk.NW, padx=(10, 3), pady=3)
                    i += 1
                if v[1] == "Checkbutton":
                    widget = widget_types[v[1]](content_frame, text="", variable=self.variables[k])
                else:
                    widget = widget_types[v[1]](content_frame, textvariable=self.variables[k], width=30)
                if v[1] == "Combobox":
                    if type(v[3]) == list:
                        v[3] = dict([(t, t) for t in v[3]])
                    self.values_dict[k] = v[3]
                    temp = list(v[3].keys())
                    widget.config(values=temp)
                    if v[2] == "bool":
                        widget.set(str(temp[-1]))
                    else:
                        widget.set(temp[-1])
                elif v[1] == "Spinbox":
                    if type(v[3]) != dict:
                        v[3] = {}
                    widget.config(from_=v[3].get("from", 0))
                    widget.config(to=v[3].get("to", 100000))
                    widget.config(increment=v[3].get("step", 1))
                    widget.set(v[3].get("from", 0))
            else:
                widget = ttk.Button(content_frame, text=v[0], command=self.build_event_handler(hardware_widgets, k, frame, self.frame_row))
            if direction == "vertical":
                widget.grid(row=i, column=1, sticky=tk.NSEW, padx=5, pady=3)
            else:
                widget.grid(row=0, column=i, sticky=tk.NW, padx=(10, 3), pady=3)
            i += 1


    def build_widgets(self, widgets, *args, parent=None, **kwargs):
        if not widgets:
            return
        if parent is None:
            parent = self.bottom_frame
        collapsible = False
        title = "Hardware"
        format = None
        temp_ref = None
        if "frame_config" in widgets:
            collapsible = widgets["frame_config"].get("collapsible", False)
            title = widgets["frame_config"].get("title", "Hardware")
            format = widgets["frame_config"].get("format", None)
            temp_ref = widgets["frame_config"].get("ref", None)
        if collapsible:
            self.foldAllFrames()
            frame = CollapsibleFrame(parent=parent, title=title)
            # only display one callapsible frame at a time
            frame.label.bind("<Button-1>", self.create_toggle_function(frame))
        else:
            frame = ttk.Frame(parent)
        frame.grid(row=self.frame_row, column=0, sticky=tk.NSEW, padx=20)
        self.frame_row += 1
        
        ref = None
        direction = "vertical"
        if kwargs:
            ref = kwargs.get("ref", None)
            direction = kwargs.get("direction", "vertical")
        ref = ref or temp_ref
        self.variables = {}
        self.values_dict = {}
        self.variables_list.append((self.variables, self.values_dict, ref, format))
        self.build_hardware_widgets(widgets, frame=frame, direction=direction)

    def foldAllFrames(self, except_frame=None):
        for child in self.hardware_frame.winfo_children():
            if isinstance(child, CollapsibleFrame) and child is not except_frame:
                child.fold()
        for child in self.bottom_frame.winfo_children():
            if isinstance(child, CollapsibleFrame) and child is not except_frame:
                child.fold()

    def create_toggle_function(self, frame):

        def func(event):
            self.foldAllFrames(frame)
            frame.toggle_visibility()
        
        return func

    def build_event_handler(self, hardware_widgets, key, frame, frame_id):
        
        def func(*args, **kwargs):
            v = hardware_widgets[key]
            if "widgets" in v[2]:
                if "parent" in v[2]:
                    parent = self.hardware_frame if v[2]["parent"].startswith("hardware") else None
                else:
                    parent_id = frame.winfo_parent()
                    parent = self.nametowidget(parent_id)
                widgets = hardware_widgets if v[2]["widgets"] == "self" else v[2]["widgets"]
                self.build_widgets(widgets, parent=parent, ref=v[2].get("ref", None), direction=v[2].get("direction", "vertical"))
                # collaps other frame
            elif v[2].get("delete", False):
                frame.grid_remove()
                self.variables_list[frame_id-self.row_offset] = None

        return func
