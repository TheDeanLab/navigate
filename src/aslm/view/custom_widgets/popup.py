# ASLM Model Waveforms

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
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

# https://stackoverflow.com/questions/28560209/transient-input-window
# Above link is a resource for using popups. Some helpful tips of an easy way to access the data inputted by a user into the popup
# Also discusses transience of a popup (whether you can click out of the popup)

## goal of this class is to create a generic popup that can be used for any purpose

# Class that handles the dialog box that has all the user entry stuff when you press the Acquisition button
class PopUp(tk.Toplevel):
    def __init__(self, root, name, size, top=True, transient=True, *args, **kwargs):
        """
        #### Creates the popup window based on the root window being passed, title that you want the window to have and the size of the window.
        Some important things to consider:

        - Root has to be the main application window to work

        - Name has to be a string

        - Size also has to be a string in the format '600x400+320+180'

        - 600x400 represents the pixel size

        - +320 means 320 pixels from left edge, +180 means 180 pixels from top edge.

        - If a '-' is used insetead of '+' it will be from the opposite edge.

        - Top is a boolean that if true means popup will always be on top of other windows

        - Transient is a boolean that if true means the main app will not be usable until popup is closed

        - The parent frame for any widgets you add to the popup will be retrieved with the get_frame() function
        """
        tk.Toplevel.__init__(self)
        # This starts the popup window config, and makes sure that any child widgets can be resized with the window
        self.title(name)
        self.geometry(
            size
        )  # 300x200 pixels, first +320 means 320 pixels from left edge, +180 means 180 pixels from top edge
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.resizable(tk.FALSE, tk.FALSE)  # Makes it so user cannot resize
        if top == True:
            self.attributes("-topmost", 1)  # Makes it be on top of mainapp when called

        self.protocol("WM_DELETE_WINDOW", self.dismiss)  # Intercepting close button

        # Checks if you want transience
        if transient == True:
            self.transient(root)  # Prevents clicking outside of window
            self.wait_visibility()  # Can't grab until window appears, so we wait
            self.grab_set()  # Ensures any input goes to this window

        # Putting popup frame into toplevel window
        self.content_frame = ttk.Frame(self)
        self.content_frame.grid(row=0, column=0, sticky=(tk.NSEW))

    # Catching close buttons/destroying window procedures
    # Dismiss function for destroying window when done

    def showup(self):
        """Display popup as top-level window."""
        self.deiconify()
        self.attributes("-topmost", 1)

    def dismiss(self):
        """
        Releases control back to main window from popup
        """
        self.grab_release()  # Ensures input can be anywhere now
        self.destroy()

    # Function so that popup entries can have a parent frame
    def get_frame(self):
        return self.content_frame
