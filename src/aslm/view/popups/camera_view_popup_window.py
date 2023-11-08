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
from aslm.view.custom_widgets.popup import PopUp
from aslm.view.main_window_content.display_notebook import CameraTab

# p = __name__.split(".")[1]
# logger = logging.getLogger(p)


class CameraViewPopupWindow:
    """Popup window with waveform parameters for galvos, remote focusing, etc.

    Parameters
    ----------
    root : tkinter.Tk
        The root window that the popup will be attached to.
    microscope_name : str
        The name of the microscope that the popup is for.
    *args
        Variable length argument list.
    **kwargs
        Arbitrary keyword arguments.

    Attributes
    ----------
    popup : PopUp
        The popup window that will be created.
    inputs : dict
        Dictionary of all the input widgets.
    buttons : dict
        Dictionary of all the buttons.
    camera_view : CameraTab
        The camera view tab.

    Methods
    -------
    get_variables()
        Returns a dictionary of all the variables that are tied to each widget name.
    get_widgets()
        Returns the dictionary that holds the input widgets.
    get_buttons()
        Returns the dictionary that holds the buttons.
    """

    def __init__(self, root, microscope_name, *args, **kwargs):
        # Creating popup window with this name and size/placement, PopUp is a
        # Toplevel window
        self.popup = PopUp(
            root,
            f"{microscope_name} Additional Camera View",
            "+320+180",
            top=False,
            transient=False,
        )
        self.popup.resizable(tk.TRUE, tk.TRUE)

        # Storing the content frame of the popup, this will be the parent of
        # the widgets
        content_frame = self.popup.get_frame()
        content_frame.columnconfigure(0, pad=5)
        content_frame.columnconfigure(1, pad=5)
        content_frame.rowconfigure(0, pad=5)
        content_frame.rowconfigure(1, pad=5)
        content_frame.rowconfigure(2, pad=5)

        # Formatting
        tk.Grid.columnconfigure(content_frame, "all", weight=1)
        tk.Grid.rowconfigure(content_frame, "all", weight=1)

        """Creating the widgets for the popup"""
        # Dictionary for all the variables
        self.inputs = {}
        self.buttons = {}

        self.camera_view = CameraTab(content_frame)
        self.camera_view.is_popup = True
        self.camera_view.is_docked = False
        self.camera_view.grid(row=0, column=0, sticky=tk.NSEW)

    # Getters
    def get_variables(self):
        """Get the variables tied to the widgets.

        This function returns a dictionary of all the variables that are tied to each
        widget name.

        The key is the widget name, value is the variable associated.



        Returns
        -------
        dict
            Dictionary of all the variables that are tied to each widget name.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get_variable()
        return variables

    def get_widgets(self):
        """Get the dictionary that holds the input widgets.

        This function returns the dictionary that holds the input widgets.
        The key is the widget name, value is the LabelInput class that has all the data.



        Returns
        -------
        dict
            Dictionary that holds the input widgets.
        """
        return self.inputs

    def get_buttons(self):
        """Get the dictionary that holds the buttons.

        This function returns the dictionary that holds the buttons.
        The key is the button name, value is the button.



        Returns
        -------
        dict
            Dictionary that holds the buttons.
        """
        return self.buttons
