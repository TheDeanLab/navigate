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

# Standard library imports
import tkinter as tk
from tkinter import ttk
import logging
import platform

# Third party imports

# Local application imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class DockableNotebook(ttk.Notebook):
    """Dockable Notebook that allows for tabs to be popped out into a separate
    windows by right clicking on the tab. The tab must be selected before right
    clicking.

    Parameters
    ----------
    parent: Tk parent widget.
        The parent widget being passed down for hierarchy and organization.
        Typically a ttk.Frame or tk.Frame.
    root : Tk top-level widget.
        Tk.tk GUI instance.
    *args :
        Options for the ttk.Notebook class
    **kwargs:
        Keyword options for the ttk.Notebook class

    Attributes
    ----------
    root : Tk top-level widget.
        Tk.tk GUI instance.
    tab_list : list
        List of tab variables
    menu : Tk Menu
        Menu that pops up when right-clicking on a tab

    Methods
    -------
    set_tablist(tab_list)
        Setter for tab list
    get_absolute_position()
        This helps the popup menu appear where the mouse is right clicked.
    find(event)
        Will check if the proper widget element in the event is what we expect.
        In this case its checking that the the label in the tab has been selected.
    dismiss()
        Dismisses the popup menu
    popout()
        Gets the currently selected tab, the tabs name and checks if the tab name is
        in the tab list.
    """

    def __init__(self, parent, root, *args, **kwargs):
        ttk.Notebook.__init__(self, parent, *args, **kwargs)
        self.root = root
        self.tab_list = []

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Popup setup
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Popout Tab", command=self.popout)

        # Bindings
        if platform.system() == "Darwin":
            self.bind("<ButtonPress-2>", self.find)
        else:
            self.bind("<ButtonPress-3>", self.find)

    def set_tablist(self, tab_list):
        """Setter for tab list

        Parameters
        ----------
        tab_list: list
            List of tab variables


        """
        self.tab_list = tab_list

    def get_absolute_position(self):
        """Get absolute position of mouse.

        This helps the popup menu appear where the mouse is right clicked.

        Returns
        -------
        x, y: integers
            Coordinates to be used (x, y)
        """
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        return x, y

    def find(self, event):
        """Find the widget that was clicked on.

        Will check if the proper widget element in the event is what we expect.

        In this case its checking that the label in the tab has been selected.
        It then gets the proper position and calls the popup.

        Parameters
        ----------
        event: Tkinter event
            Holds information about the event that was triggered and caught by Tkinters
            event system


        """
        element = event.widget.identify(event.x, event.y)
        if "label" in element:
            try:
                x, y = self.get_absolute_position()
                self.menu.tk_popup(x, y)
            finally:
                self.menu.grab_release()

    def popout(self):
        """Popout the currently selected tab.

        Gets the currently selected tab, the tabs name and checks if the tab name is
        in the tab list. If the tab is in the list, its removed from the list,
        hidden, and then passed to a new Top Level window.




        """
        # Get ref to correct tab to popout
        tab = self.select()
        tab_text = self.tab(tab)["text"]
        for tab_name in self.tab_list:
            if tab_text == self.tab(tab_name)["text"]:
                tab = tab_name
                self.tab_list.remove(tab_name)
        self.hide(tab)
        self.root.wm_manage(tab)

        # self.root.wm_title(tab, tab_text)
        tk.Wm.title(tab, tab_text)
        tk.Wm.protocol(tab, "WM_DELETE_WINDOW", lambda: self.dismiss(tab, tab_text))
        if tab_text == "Camera View":
            tk.Wm.minsize(tab, 663, 597)
            tab.is_docked = False
        elif tab_text == "Waveform Settings":
            tab.is_docked = False

    def dismiss(self, tab, tab_text):
        """Dismisses the popup menu

        This function is called when the top level that the tab was originally passed to
        has been closed. The window manager releases control and then the tab is
        added back to its original ttk.Notebook.

        Parameters
        ----------
        tab: Tkinter tab (path to widget represented as a str)
            The tab that was popped out, this reference to the dismiss function is
            associated with this tab
        tab_text: string
            Name of the tab as it appears in the GUI


        """
        self.root.wm_forget(tab)
        tab.grid(row=0, column=0)
        if self.index("end") - 1 > tab.index:
            self.insert(tab.index, tab)
        else:
            self.insert("end", tab)
        self.tab(tab, text=tab_text)
        self.tab_list.append(tab)
        if tab_text == "Camera View":
            tab.canvas.configure(width=512, height=512)
            tab.is_docked = True
        elif tab_text == "Waveform Settings":
            tab.is_docked = True
