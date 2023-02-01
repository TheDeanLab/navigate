# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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

import tkinter as tk
from tkinter import ttk
from aslm.view.custom_widgets.popup import PopUp


import logging


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class HelpPopup:
    """
    #### Class creates the popup that provides list of hot keys.
    """

    def __init__(self, root, *args, **kwargs):
        # Creating popup window with this name and size/placement, PopUp is a
        # Toplevel window
        self.popup = PopUp(root, "Help", "+320+180", top=False, transient=False)

        # Creating content frame
        content_frame = self.popup.get_frame()

        # Formatting
        tk.Grid.columnconfigure(content_frame, "all", weight=1)
        tk.Grid.rowconfigure(content_frame, "all", weight=1)

        """Creating the widgets for the popup"""
        # Dictionary for all the variables
        self.inputs = {}

        # Label Lists
        text = [
            "Left Click: Toggles cross-hair on image",
            "Right Click: Brings up popup window to select Move Here and Reset Display options",
            "Mouse Wheel: Digitally zoom in or out on image based on scroll direction",
            "Double Click Row Header: Moves stage to the position given by the row",
            "Control + 1, 2, 3 or 4: Changes to selected tab",
            "This is where all the basic usage instructions will go",
        ]

        # Titles
        basic_title = ttk.Labelframe(content_frame, text="Basic Operating Info")
        hotkey_title = ttk.Labelframe(content_frame, text="Hotkeys")
        cam_view = ttk.Labelframe(hotkey_title, text="Camera View")
        multitable = ttk.Labelframe(hotkey_title, text="Multiposition Table")
        main_win = ttk.Labelframe(hotkey_title, text="Main Window")

        # Text for Basic Operations
        basic = ttk.Label(basic_title, text=text[5])

        # Text for CameraView
        left = ttk.Label(cam_view, text=text[0])
        right = ttk.Label(cam_view, text=text[1])
        mousewheel = ttk.Label(cam_view, text=text[2])

        # Text for MultiTable
        double_click = ttk.Label(multitable, text=text[3])

        # Text for Main Window
        switch_tab = ttk.Label(main_win, text=text[4])

        # Gridding Titles
        basic_title.grid(row=0, column=0, sticky=(tk.NSEW), padx=5, pady=5)
        hotkey_title.grid(row=1, column=0, sticky=(tk.NSEW), padx=5, pady=5)

        # Gridding subtitles
        cam_view.grid(row=0, column=0, sticky=(tk.NSEW), padx=5, pady=5)
        multitable.grid(row=1, column=0, sticky=(tk.NSEW), padx=5, pady=5)
        main_win.grid(row=2, column=0, sticky=(tk.NSEW), padx=5, pady=5)

        # Gridding text
        left.grid(row=0, column=0, sticky=(tk.NSEW), padx=5, pady=5)
        right.grid(row=1, column=0, sticky=(tk.NSEW), padx=5, pady=5)
        mousewheel.grid(row=2, column=0, sticky=(tk.NSEW), padx=5, pady=5)

        double_click.grid(row=0, column=0, sticky=(tk.NSEW), padx=5, pady=5)

        switch_tab.grid(row=0, column=0, sticky=(tk.NSEW), padx=5, pady=5)

        basic.grid(row=0, column=0, sticky=(tk.NSEW), padx=5, pady=5)

    def get_widgets(self):
        return self.inputs
