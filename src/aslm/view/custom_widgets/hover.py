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
import logging

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class hover(object):
    """Hover that allows for information to be displayed additionally without
    interrupting the GUI

    Each instance of hover is intended to be an attribute of a tk or ttk widget
    (see validated fields or hovermixins), and by default is set only to show error
    messages

    In this case, the parent widget is the Stage Control GUI y position label.
    To instantiate the description, widget.hover.setdescription("Y position of the
    stage")

    Please note: when dealing with LabelInput widgets, be sure to use
    LabelInput.widget.hover.setdescription(), which will target the specific widget
    and not the LabelInput frame

    Examples of proper usage are within stage_control_tab.py for both LabelInput and
    regular usage

    Parameters
    ----------
    widget  : bound widget.
        The widget to which the hover instance is bound, usually the one on which
        information is being provided
    text    : str variable
        Text to be displayed when the hover is shown (default set to None so the hover
        will not show at all)
    type    : str variable
        Represents the current state of the hover and whether it is in use at any given
        moment

    Attributes
    ----------
    widget  : bound widget
        The widget to which the hover instance is bound, usually the one on which
        information is being provided
    tipwindow   : tk.Toplevel
        The window that is displayed when the hover is shown
    id  : int
        The id of the hover
    x   : int
        The x coordinate of the hover
    y   : int
        The y coordinate of the hover
    text    : str
        Text to be displayed when the hover is shown
    description : str
        Text to be displayed when the hover is shown as a description
    type    : str
        Represents the current state of the hover and whether it is in use at any given
        moment

    Methods
    -------
    get_type()
        Getter for the type
    hide()
        Event handler to hide the hover
    hidetip()
        Hides the hover
    setdescription(text)
        Setter for description text
    show()
        Event handler to show the hover
    showtip(text)
        Shows the hover
    update_type(newtype)
        Setter for the type
    """

    def __init__(self, widget=None, text=None, type="free"):
        """Constructor for the Hover

        Initializes attributes and binds events
        """
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self.text = text
        self.description = None
        self.type = type

        # define event handling for showing and hiding the hover
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)
        widget.bind("<ButtonPress>", self.hide)

    # Sets a description for the widget to appear when hovered over
    # If text=None, no description hover will be shown at all
    def setdescription(self, text):
        """Setter for description text

        Parameters
        ----------
        text    : str
            Text to be displayed when hover is shown as a description

        Returns
        -------
        None
        """
        self.description = text

    # Event handlers
    def show(self, event):
        """Event handler to show the hover

        Parameters
        ----------
        event   : event
            The event instance

        Returns
        -------
        None
        """
        if self.type == "free" and self.description is not None:
            self.type = "description"
            self.showtip(self.description)

    def hide(self, event):
        """Event handler to hide the hover

        Parameters
        ----------
        event   : event
            The event instance

        Returns
        -------
        None
        """
        if self.type == "description":
            self.hidetip()

    def update_type(self, newtype):
        """Setter for the type

        Parameters
        ----------
        newtype : str
            The new state of the hover

        Returns
        -------
        None
        """
        self.type = newtype.lower()

    def get_type(self):
        """Getter for the type

        Parameters
        ----------
        None

        Returns
        -------
        type    : str
            The current state of the hover
        """
        return self.type

    def showtip(self, text):
        """Displays the hover

        Parameters
        ----------
        text    :str
            The text to be displayed on the hover

        Returns
        -------
        None
        """
        self.text = text
        if self.tipwindow or not self.text:
            return

        # set format of hover by type
        if self.type.lower() == "description":
            background = "#ffffe0"
            relief = tk.SOLID
            font = ("tahoma", "8", "normal")
            x = self.widget.winfo_rootx() + self.widget.winfo_width()
            y = self.widget.winfo_rooty() + self.widget.winfo_height()

        elif self.type.lower() == "error":
            background = "#ff5d66"
            relief = (tk.RIDGE,)
            font = ("comic sans", "8", "normal")
            x = self.widget.winfo_rootx()
            y = self.widget.winfo_rooty() + self.widget.winfo_height()

        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background=background,
            relief=relief,
            borderwidth=1,
            font=font,
        )
        label.pack(ipadx=1)

    def seterror(self, text):
        """Setter for the error message

        Parameters
        ----------
        error    : str
            Error message to be displayed

        Returns
        -------
        None
        """
        self.type = "error"
        self.showtip(text)

    def hidetip(self):
        """Hides the hover and resets type

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.type = "free"
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
