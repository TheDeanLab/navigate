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
from tkinter import Menu
import logging

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


#  Menubar class
class Menubar(Menu):
    """Menu bar class for GUI"""

    def __init__(self, window, *args, **kwargs):
        """Initialize the menu bar class.


        Parameters
        ----------
        window : tkinter.Tk
            Parent window for menu bar
        *args : list
            List of arguments
        **kwargs : dict
            Dictionary of arguments

        """

        #  Init Menu with parent
        Menu.__init__(self, window, *args, **kwargs)

        #: str: Operating system of computer
        self.opsystem = window.tk.call("tk", "windowingsystem")

        #  Prevents menu from tearing off bar
        window.option_add("*tearOff", False)

        #  Linking menu to option of parent to this menu class
        window["menu"] = self

        #: Menu: File Menu
        self.menu_file = Menu(self)
        self.add_cascade(menu=self.menu_file, label="File")

        #: Menu: Microscope Configuration Menu
        self.menu_resolution = Menu(self)
        self.add_cascade(menu=self.menu_resolution, label="Microscope Configuration")

        #: Menu: Stage Control Menu
        self.menu_multi_positions = Menu(self)
        self.add_cascade(menu=self.menu_multi_positions, label="Stage Control")

        #: Menu: Autofocus Menu
        self.menu_autofocus = Menu(self)
        self.add_cascade(menu=self.menu_autofocus, label="Autofocus")

        #: Menu: Features Menu
        self.menu_features = Menu(self)
        self.add_cascade(menu=self.menu_features, label="Features")

        #: Menu: Plugins Menu
        self.menu_plugins = Menu(self)
        self.add_cascade(menu=self.menu_plugins, label="Plugins")

        #: Menu: Window Menu
        self.menu_window = Menu(self)
        self.add_cascade(menu=self.menu_window, label="Window")
