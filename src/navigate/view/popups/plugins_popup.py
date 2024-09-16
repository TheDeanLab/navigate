# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
import logging
from tkinter import ttk
import tkinter as tk

# Third Party Imports

# Local Imports
from navigate.view.custom_widgets.popup import PopUp

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class PluginsPopup:
    """Class creates the popup to uninstall plugins."""

    def __init__(self, root, *args, **kwargs):
        """Initialize the PluginsPopup class

        Parameters
        ----------
        root : tk.Tk
            The root window
        *args
            Variable length argument list
        **kwargs
            Arbitrary keyword arguments
        """
        # Creating popup window with this name and size/placement, PopUp is a Toplevel
        # window
        #: PopUp: The popup window
        self.popup = PopUp(root, "Plugins", "+320+180", transient=True)

        # Storing the content frame of the popup, this will be the parent of the widgets
        content_frame = self.popup.get_frame()

        # Formatting
        tk.Grid.columnconfigure(content_frame, "all", weight=1)
        tk.Grid.rowconfigure(content_frame, "all", weight=1)

        # Dictionary for all the variables
        #: dict: Variable
        self.variables = {}

        label = ttk.Label(content_frame, text="Plugin Name", width=30)
        label.grid(row=0, column=1, padx=(30, 10), sticky=tk.NE)

        label = ttk.Label(content_frame, text="Location", width=60)
        label.grid(row=0, column=2, sticky=tk.NE)

        separator = ttk.Separator(content_frame)
        separator.grid(row=1, columnspan=3, sticky=tk.NSEW)

        self.plugins_frame = ttk.Frame(content_frame)
        self.plugins_frame.grid(row=2, columnspan=3, sticky=tk.NSEW)

        self.uninstall_btn = ttk.Button(content_frame, text="Uninstall")
        self.uninstall_btn.grid(row=3, column=2, sticky=tk.NE)

    def build_widgets(self, plugin_config):
        """List all plugins"""
        self.variables = []
        for child in self.plugins_frame.winfo_children():
            child.destroy()

        for i, plugin_name in enumerate(plugin_config.keys()):
            var = tk.StringVar()
            check = ttk.Checkbutton(
                self.plugins_frame, variable=var, onvalue=plugin_name, offvalue=""
            )
            check.grid(row=i, column=0, sticky=tk.NW)
            label = ttk.Label(self.plugins_frame, text=plugin_name)
            label.grid(row=i, column=1, padx=(5, 10), sticky=tk.NSEW)
            label = ttk.Label(self.plugins_frame, text=plugin_config[plugin_name])
            label.grid(row=i, column=2, sticky=tk.NSEW)
            self.variables.append(var)
