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
import tkinter as tk

# Third Party Imports

# Local Imports
from navigate.view.configurator_application_window import ConfigurationAssistantWindow
from navigate.view.configurator_application_window import (
    MicroscopeTab,
    MicroscopeWindow,
)

# Logger Setup
import logging

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Configurator:
    """Navigate Configurator"""

    def __init__(self, root, splash_screen):
        """Initiates the configurator application window.

        Parameters
        ----------
        root : tk.Tk
            The main window of the application
        splash_screen : SplashScreen
            The splash screen of the application
        """
        self.root = root

        # Show the splash screen for 1 second and then destroy it.
        # sleep(1)
        splash_screen.destroy()
        self.root.deiconify()
        self.view = ConfigurationAssistantWindow(root)

        self.view.top_window.continue_button.config(command=self.on_continue)
        self.view.top_window.cancel_button.config(command=self.on_cancel)

    def on_cancel(self):
        """Closes the window and exits the program"""
        self.root.destroy()
        exit()

    def on_continue(self):
        """Evaluate the number of configurations and create the configuration window"""
        try:
            num_configs = int(self.view.top_window.num_configs_entry.get())
            self.create_config_window(num_configs)
        except ValueError:
            print("Please enter a valid number")

    def create_config_window(self, num_configs):
        """Creates the configuration window tabs."""

        self.view.microscope_window = MicroscopeWindow(
            self.view.microscope_frame, self.view.root
        )

        # Initialize and set the tab list
        tab_list = []
        self.view.microscope_window.set_tablist(tab_list)

        for attr in dir(self.view.microscope_window):
            if attr.startswith("microscope_tab_"):
                # Delete the tab.
                self.view.microscope_window.forget(
                    getattr(self.view.microscope_window, attr)
                )
                delattr(self.view.microscope_window, attr)

        # Create the tabs
        for i in range(num_configs):
            tab_name = f"Microscope {i}"
            setattr(
                self.view.microscope_window,
                f"microscope_tab_{i}",
                MicroscopeTab(self.view.microscope_window, name=tab_name, index=i),
            )
            tab_list.append(getattr(self.view.microscope_window, f"microscope_tab_{i}"))

        self.view.microscope_window.set_tablist(tab_list)

        # Adding tabs to self notebook
        for i in range(num_configs):
            self.view.microscope_window.add(
                getattr(self.view.microscope_window, f"microscope_tab_{i}"),
                text=f"Microscope {i}",
                sticky=tk.NSEW,
            )
