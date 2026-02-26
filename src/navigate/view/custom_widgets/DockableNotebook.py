# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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
    windows by right-clicking on the tab. The tab must be selected before
    right-clicking.
    """

    def __init__(self, parent, root, *args, **kwargs):
        """Initialize Dockable Notebook

        Parameters
        ----------
        parent: Tk parent widget.
            The parent widget being passed down for hierarchy and organization.
            Typically, a ttk.Frame or tk.Frame.
        root : Tk top-level widget.
            Tk.tk GUI instance.
        *args :
            Options for the ttk.Notebook class
        **kwargs:
            Keyword options for the ttk.Notebook class
        """
        super().__init__(parent, *args, **kwargs)

        #: tk.Tk: Tkinter root
        self.root = root

        #: int: Selected tab id where user right-clicked.
        self.selected_tab_id = None

        #: list: List of tab variables
        self.tab_list = []

        #: tk.Menu: Tkinter menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Popout Tab", command=self.popout)

        # Bindings
        if platform.system() == "Darwin":
            self.bind("<ButtonPress-2>", self.find)
        else:
            self.bind("<ButtonPress-3>", self.find)

    def set_tablist(self, tab_list: list) -> None:
        """Setter for tab list

        Parameters
        ----------
        tab_list: list
            The list of tab variables
        """
        self.tab_list = tab_list

    def get_absolute_position(self) -> tuple:
        """Get absolute position of mouse.

        This helps the popup menu appear where the mouse is right-clicked.

        Returns
        -------
        x, y: integers
            Coordinates to be used (x, y)
        """
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        return x, y

    def find(self, event: tk.Event) -> None:
        """Find the widget that was clicked on.

        Will check if the proper widget element in the event is what we expect.

        In this case its checking that the label in the tab has been selected.
        It then gets the proper position and calls the popup.

        Parameters
        ----------
        event: tk.Event
            Tkinter event object
        """
        element = event.widget.identify(event.x, event.y)
        self.selected_tab_id = self.index(f"@{event.x},{event.y}")  # Add this line
        if "label" in element:
            try:
                x, y = self.get_absolute_position()
                self.menu.tk_popup(x, y)
            finally:
                self.menu.grab_release()

    def popout(self) -> None:
        """Popout the currently selected tab.

        Gets the currently selected tab, the tabs name and checks if the tab name is
        in the tab list. If the tab is in the list, it's removed from the list,
        hidden, and then passed to a new Top Level window.
        """
        # Get ref to correct tab to popout
        if self.selected_tab_id is None:
            return

        # Get the selected tab's text. e.g., "Camera", "MIP", "Waveforms".
        selected_text: str = self.tab(self.selected_tab_id, "text")

        # Check if the selected tab is in the tab list
        tab_widget = None
        for t in self.tab_list:
            if self.tab(t, "text") == selected_text:
                tab_widget: tk.Frame = t
                break

        # If the tab is not in the list, return
        if not tab_widget:
            return

        # Save the original index and the tab's text
        tab_widget._original_index = self.selected_tab_id
        tab_widget._saved_text: str = selected_text
        tab_widget.is_docked = False

        # Remove the tab from the notebook
        if tab_widget in self.tab_list:
            self.tab_list.remove(tab_widget)
        self.hide(tab_widget)
        self.root.wm_manage(tab_widget)

        tk.Wm.title(tab_widget, selected_text)
        tk.Wm.protocol(tab_widget, "WM_DELETE_WINDOW", lambda: self.dismiss(tab_widget))

        if selected_text == "Camera View":
            tk.Wm.minsize(tab_widget, 663, 597)

    def dismiss(self, tab_widget):
        """Dismiss the popout window.

        This is called when the popout window is closed.
        It destroys the popout window and re‐inserts the tab into the notebook.

        Parameters
        ----------
        tab_widget : ttk.Frame
            The tab widget to be dismissed.
        """
        popout = getattr(tab_widget, "_popout_window", None)
        if popout:
            popout.destroy()
            del tab_widget._popout_window
        else:
            # If we used wm_manage successfully, then do wm_forget
            self.root.wm_forget(tab_widget)

        # Then remove it from any geometry manager just in case
        tab_widget.grid_forget()
        tab_widget.pack_forget()

        # Retrieve the original index and the saved text
        original_index = getattr(tab_widget, "_original_index", None)
        saved_text = getattr(tab_widget, "_saved_text", "Untitled")
        tab_widget.is_docked = True

        if original_index is not None:
            current_count = self.index("end")
            if original_index >= current_count:
                original_index = "end"

            self.insert(original_index, tab_widget)

        else:
            self.add(tab_widget)

        self.tab(tab_widget, text=saved_text)
        self.tab_list.append(tab_widget)

        # Restore the tab's docked state
        if saved_text == "Camera View":
            if hasattr(tab_widget, "canvas"):
                tab_widget.canvas.configure(width=512, height=512)
            tab_widget.is_docked = True
        elif saved_text == "Waveform Settings":
            tab_widget.is_docked = True

        # Select tab in main window
        self.select(tab_widget)
