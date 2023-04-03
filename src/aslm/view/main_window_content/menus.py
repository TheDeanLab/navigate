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

from tkinter import Menu

import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


#  Menubar class
class Menubar(Menu):
    """Menu bar class for ASLM GUI

    Parameters
    ----------
    window : tkinter.Tk
        Parent window for menu bar
    *args : list
        List of arguments
    **kwargs : dict
        Dictionary of arguments

    Attributes
    ----------
    opsystem : str
        Operating system of parent window
    menu_file : tkinter.Menu
        File menu
    menu_multi_positions : tkinter.Menu
        Multi-Position menu
    menu_resolution : tkinter.Menu
        Resolution menu
    menu_autofocus : tkinter.Menu
        Autofocus menu
    menu_features : tkinter.Menu
        Add-on Features menu
    menu_help : tkinter.Menu
        Help menu
    menu_debug : tkinter.Menu
        Debug menu
    """

    def __init__(self, window, *args, **kwargs):
        #  Init Menu with parent
        Menu.__init__(self, window, *args, **kwargs)

        #  Creates operating system attribute
        self.opsystem = window.tk.call("tk", "windowingsystem")

        #  Prevents menu from tearing off bar
        window.option_add("*tearOff", False)

        #  Linking menu to option of parent to this menu class
        window["menu"] = self

        #  File Menu
        self.menu_file = Menu(self)
        self.add_cascade(menu=self.menu_file, label="File")

        #  Resolution Menu
        self.menu_resolution = Menu(self)
        self.add_cascade(menu=self.menu_resolution, label="Microscope Settings")

        #  Multi-Position Menu
        self.menu_multi_positions = Menu(self)
        self.add_cascade(menu=self.menu_multi_positions, label="Multi-Position")

        # Autofocus Menu
        self.menu_autofocus = Menu(self)
        self.add_cascade(menu=self.menu_autofocus, label="Autofocus")

        # Add-on Features menu
        self.menu_features = Menu(self)
        self.add_cascade(menu=self.menu_features, label="Features")

        # Help Menu
        self.menu_help = Menu(self)
        self.add_cascade(menu=self.menu_help, label="Help")

