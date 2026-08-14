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

# Standard Library Imports
import tkinter as tk
from tkinter import ttk
from typing import Optional

# Local Imports
from navigate.view.theme import get_theme_color, get_theme_padding_px, get_theme_space_px


class ConfigurationAssistantWindow(ttk.Frame):
    """Passive main window for the configurator."""

    def __init__(self, root: tk.Tk, *args, **kwargs) -> None:
        self.root = root
        self.root.title("New Configuration Assistant")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        super().__init__(root, *args, **kwargs)
        self.grid(row=0, column=0, sticky=tk.NSEW)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.top_frame = ttk.Frame(self)
        self.top_frame.grid(row=0, column=0, sticky=tk.EW, padx=get_theme_space_px(3), pady=get_theme_space_px(3))
        self.top_frame.columnconfigure(0, weight=1)
        self.top_window = TopWindow(self.top_frame)
        self.top_window.grid(row=0, column=0, sticky=tk.EW)

        self.microscope_frame = ttk.Frame(self)
        self.microscope_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=get_theme_space_px(3), pady=get_theme_padding_px((3, 0)))
        ttk.Style().configure("Configurator.TRadiobutton", font="TkDefaultFont")

        self.configuration_frame = ttk.Frame(self)
        self.configuration_frame.grid(row=2, column=0, sticky=tk.NSEW, padx=get_theme_space_px(3), pady=get_theme_padding_px((0, 3)))
        self.configuration_frame.columnconfigure(0, weight=0, minsize=300)
        self.configuration_frame.columnconfigure(1, weight=1)
        self.configuration_frame.rowconfigure(0, weight=1)

        self.devices_frame = DevicesFrame(self.configuration_frame)
        self.devices_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.device_info_frame = DeviceInfoFrame(self.configuration_frame)
        self.device_info_frame.grid(row=0, column=1, sticky=tk.NSEW)


class TopWindow(ttk.Frame):
    """Static top-row controls."""

    def __init__(self, parent: ttk.Frame, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.columnconfigure(0, weight=1)
        options = {"sticky": tk.NE, "padx": get_theme_space_px(3), "pady": get_theme_padding_px((10, 1))}
        self.microscopes_label = ttk.Label(self, text="Microscopes", font=("TkDefaultFont", 16, "bold"))
        self.microscopes_label.grid(row=0, column=0, sticky=tk.W)
        self.new_button = ttk.Button(self, text="New Configuration", width=12)
        self.new_button.grid(row=0, column=1, **options)
        self.load_button = ttk.Button(self, text="Load Configuration", width=12)
        self.load_button.grid(row=0, column=2, **options)
        self.add_button = ttk.Button(self, text="Add A Microscope", width=12)
        self.add_button.grid(row=0, column=3, **options)
        self.save_button = ttk.Button(self, text="Save", width=12)
        self.save_button.grid(row=0, column=4, **options)
        self.cancel_button = ttk.Button(self, text="Cancel", width=12)
        self.cancel_button.grid(row=0, column=5, **options)


class DevicesFrame(ttk.LabelFrame):
    """Static Devices-panel controls."""

    def __init__(self, parent: ttk.Frame, *args, **kwargs) -> None:
        super().__init__(parent, text="", width=300, height=200, *args, **kwargs)
        self.grid_propagate(False)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        _configure_treeview_style("Devices.Treeview")
        self.devices_label = ttk.Label(self, text="Devices", font="TkDefaultFont")
        self.devices_label.grid(row=0, column=0, sticky=tk.W, padx=get_theme_space_px(3), pady=get_theme_space_px(3))
        self.edit_button = ttk.Button(self, text="Edit", width=5)
        self.edit_button.grid(row=0, column=1, sticky=tk.E, padx=get_theme_space_px(3), pady=get_theme_space_px(3))
        self.delete_button = ttk.Button(self, text="×", width=3, style="Danger.TButton")
        self.delete_button.grid(row=0, column=2, sticky=tk.E, padx=get_theme_space_px(3), pady=get_theme_space_px(3))
        self.device_list = ttk.Treeview(self, show="tree", selectmode="browse", style="Devices.Treeview")
        self.device_list.grid(row=1, column=0, columnspan=3, sticky=tk.NSEW, padx=get_theme_space_px(3), pady=get_theme_padding_px((0, 3)))
        self.add_button = ttk.Button(self, text="Add", width=5)
        self.add_button.grid(row=2, column=0, sticky=tk.W, padx=get_theme_space_px(3), pady=get_theme_space_px(3))


class DeviceInfoFrame(ttk.LabelFrame):
    """Static Device Info panel shell."""

    def __init__(self, parent: ttk.Frame, *args, **kwargs) -> None:
        super().__init__(parent, text="", *args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        _configure_entry_style("DeviceInfo.TEntry")
        self.device_info_label = ttk.Label(self, text="Device Info", font="TkDefaultFont")
        self.device_info_label.grid(row=0, column=0, sticky=tk.W, padx=get_theme_space_px(3), pady=get_theme_space_px(3))
        self.settings_canvas = tk.Canvas(self, background=get_theme_color("input_bg"), highlightthickness=0)
        self.settings_canvas.grid(row=2, column=0, sticky=tk.NSEW, padx=get_theme_space_px(3), pady=get_theme_padding_px((0, 3)))
        self.settings_frame = ttk.Frame(self.settings_canvas)
        self.settings_frame.columnconfigure(0, minsize=170)
        self.settings_frame.columnconfigure(1, weight=1, minsize=160)
        self.settings_window = self.settings_canvas.create_window((0, 0), anchor=tk.NW, window=self.settings_frame)
        self.horizontal_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.horizontal_scrollbar.grid(row=3, column=0, sticky=tk.EW, padx=get_theme_space_px(3), pady=get_theme_padding_px((0, 3)))


class AddDeviceDialog(tk.Toplevel):
    """Passive three-column device-selection dialog."""

    def __init__(self, parent: tk.Misc, title: str, action_text: str) -> None:
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.geometry("900x480")
        self.minsize(720, 360)
        self.configure(background=get_theme_color("panel_bg"))
        _configure_treeview_style("AddDevice.Treeview")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        content = ttk.Frame(self, padding=get_theme_padding_px((3, 3)))
        content.grid(row=0, column=0, sticky=tk.NSEW)
        content.rowconfigure(0, weight=1)
        for column in range(3):
            content.columnconfigure(column, weight=1, uniform="add-device-columns")
        self.categories_list = self._create_list_column(content, 0, "Device Categories")
        self.manufacturers_list = self._create_list_column(content, 1, "Manufacturer")
        self.models_list = self._create_list_column(content, 2, "Model")
        actions = ttk.Frame(self)
        actions.grid(row=1, column=0, sticky=tk.E, padx=get_theme_space_px(3), pady=get_theme_space_px(3))
        self.action_button = ttk.Button(actions, text=action_text, width=8)
        self.action_button.grid(row=0, column=0)

    @staticmethod
    def _create_list_column(parent: ttk.Frame, column: int, title: str) -> ttk.Treeview:
        frame = ttk.LabelFrame(parent, text=title)
        frame.grid(row=0, column=column, sticky=tk.NSEW, padx=get_theme_padding_px((1 if column else 0, 1 if column < 2 else 0)))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        tree = ttk.Treeview(frame, show="tree", selectmode="browse", style="AddDevice.Treeview")
        tree.grid(row=0, column=0, sticky=tk.NSEW, padx=get_theme_space_px(3), pady=get_theme_space_px(3))
        return tree


class RenameMicroscopeDialog(tk.Toplevel):
    """Passive rename dialog."""

    def __init__(self, parent: tk.Misc, current_name: str) -> None:
        super().__init__(parent)
        self.title("Rename Microscope")
        self.transient(parent)
        self.resizable(False, False)
        self.configure(background=get_theme_color("panel_bg"))
        _configure_entry_style("RenameMicroscope.TEntry")
        content = ttk.Frame(self, padding=get_theme_padding_px((3, 3)))
        content.grid(row=0, column=0, sticky=tk.NSEW)
        content.columnconfigure(0, weight=1)
        ttk.Label(content, text="Microscope name:").grid(row=0, column=0, sticky=tk.W, pady=get_theme_padding_px((0, 1)))
        self.name_var = tk.StringVar(master=self, value=current_name)
        self.name_entry = ttk.Entry(content, textvariable=self.name_var, style="RenameMicroscope.TEntry", width=30)
        self.name_entry.grid(row=1, column=0, sticky=tk.EW)
        actions = ttk.Frame(content)
        actions.grid(row=2, column=0, sticky=tk.E, pady=get_theme_padding_px((3, 0)))
        self.ok_button = ttk.Button(actions, text="OK", width=8)
        self.ok_button.grid(row=0, column=0, padx=get_theme_padding_px((0, 1)))
        self.cancel_button = ttk.Button(actions, text="Cancel", width=8)
        self.cancel_button.grid(row=0, column=1)


class ConfiguratorTooltip:
    """Small themed tooltip for configurator setting labels."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.window: Optional[tk.Toplevel] = None
        self.after_id: Optional[str] = None
        widget.bind("<Enter>", self.schedule)
        widget.bind("<Leave>", self.hide)
        widget.bind("<ButtonPress>", self.hide)

    def schedule(self, _event: tk.Event) -> None:
        """Show the tooltip after a brief hover delay."""
        self.after_id = self.widget.after(500, self.show)

    def show(self) -> None:
        """Create the tooltip beside the label."""
        self.after_id = None
        if self.window is not None or not self.widget.winfo_exists():
            return
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.wm_geometry(
            "+{}+{}".format(
                self.widget.winfo_rootx(),
                self.widget.winfo_rooty() + self.widget.winfo_height() + 6,
            )
        )
        self.window.configure(background=get_theme_color("tooltip_description_bg"))
        tk.Label(
            self.window,
            text=self.text,
            justify=tk.LEFT,
            background=get_theme_color("tooltip_description_bg"),
            foreground=get_theme_color("tooltip_text"),
            padx=get_theme_space_px(3),
            pady=get_theme_space_px(2),
            wraplength=320,
        ).pack()

    def hide(self, _event: Optional[tk.Event] = None) -> None:
        """Cancel a scheduled tooltip and close a visible tooltip."""
        if self.after_id is not None:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.window is not None:
            self.window.destroy()
            self.window = None


def _configure_treeview_style(style_name: str) -> None:
    """Apply Navigate's dark colors to a Treeview style."""
    style = ttk.Style()
    text = get_theme_color("text")
    style.configure(style_name, background=get_theme_color("input_bg"), fieldbackground=get_theme_color("input_bg"), foreground=text, font="TkDefaultFont")
    style.map(style_name, background=[("selected", get_theme_color("accent"))], foreground=[("selected", text)])


def _configure_entry_style(style_name: str) -> None:
    """Apply Navigate's flat dark style to entries."""
    background = get_theme_color("input_bg")
    text = get_theme_color("text")
    ttk.Style().configure(style_name, fieldbackground=background, foreground=text, insertcolor=text, bordercolor=background, lightcolor=background, darkcolor=background, font="TkDefaultFont")
