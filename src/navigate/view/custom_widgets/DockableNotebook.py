# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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


class ScrollableContainer(ttk.Frame):
    """ Scrollable container with left/right arrow buttons

    A container frame that holds:
      - A left arrow button
      - A DockableNotebook (scrollable or not)
      - A right arrow button

    If `scrollable=False` is given, this container simply places the
    DockableNotebook without showing arrow buttons or hiding tabs.
    """

    def __init__(self, parent, root, scrollable=False, *args, **kwargs):
        """
        Parameters
        ----------
        parent : tk or ttk container
            The parent widget for this container frame.
        root : tk.Tk
            The root window (used by the DockableNotebook).
        scrollable : bool
            If True, enable tab scrolling (default=False).
        """
        super().__init__(parent, *args, **kwargs)

        self.root = root

        self.notebook = DockableNotebook(self, root)

        self.scrollable = scrollable

        if not self.scrollable:
            self.notebook.grid(row=0, column=0, sticky="nsew")
            self.rowconfigure(0, weight=1)
            self.columnconfigure(0, weight=1)
            return

        self.arrow_frame = ttk.Frame(self)
        self.arrow_frame.grid(row=0, column=0, sticky="w")
        self._left_arrow = ttk.Button(
            self.arrow_frame, text="◀", width=1, command=self._scroll_left
        )
        self._left_arrow.pack(side="left", padx=1, pady=1)

        self._right_arrow = ttk.Button(
            self.arrow_frame, text="▶", width=1, command=self._scroll_right
        )
        self._right_arrow.pack(side="left", padx=1, pady=1)

        self.notebook.grid(row=1, column=0, sticky="nsew")
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Bind events to update arrow states
        self.notebook.bind("<<NotebookTabChanged>>", self._update_scrollable_tabs)
        self.notebook.bind("<Configure>", self._update_scrollable_tabs)

    def _scroll_left(self):
        """
        Move the 'visible window' of tabs one step to the left.
        """
        self.notebook.scroll_left()
        self._update_scrollable_tabs()

    def _scroll_right(self):
        """
        Move the 'visible window' of tabs one step to the right.
        """
        self.notebook.scroll_right()
        self._update_scrollable_tabs()

    def _update_scrollable_tabs(self, event=None):
        """
        Calls the notebook's internal method to recalc visible tabs,
        then updates arrow states.
        """
        self.notebook.update_scrollable_tabs()
        # Example: if the notebook is at the leftmost possible view, disable left arrow
        if self.notebook.at_left_edge:
            self._left_arrow.configure(state="disabled")
        else:
            self._left_arrow.configure(state="normal")

        # If the notebook is at the rightmost possible view, disable right arrow
        if self.notebook.at_right_edge:
            self._right_arrow.configure(state="disabled")
        else:
            self._right_arrow.configure(state="normal")

    def add(self, child, **kwargs):
        """Pass-through to DockableNotebook.add()"""
        return self.notebook.add(child, **kwargs)

    def insert(self, index, child, **kwargs):
        """Pass-through to DockableNotebook.insert()"""
        return self.notebook.insert(index, child, **kwargs)

    def hide(self, tab_id):
        """Pass-through to DockableNotebook.hide()"""
        self.notebook.hide(tab_id)

    def select(self, tab_id=None):
        """Pass-through to DockableNotebook.select()"""
        return self.notebook.select(tab_id)

    def tabs(self):
        """Return all tab IDs"""
        return self.notebook.tabs()

    def index(self, tab_id):
        return self.notebook.index(tab_id)

    @property
    def tab_list(self):
        return self.notebook.tab_list

    def set_tablist(self, tab_list):
        self.notebook.set_tablist(tab_list)



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

        #: list: List of tab variables
        self.tab_list = []

        # Popup setup
        #: tk.Menu: Tkinter menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Popout Tab", command=self.popout)

        # Bindings
        if platform.system() == "Darwin":
            self.bind("<ButtonPress-2>", self.find)
        else:
            self.bind("<ButtonPress-3>", self.find)

        # Internal indexes for scrolling
        self._start_index = 0  # first visible tab index
        self._visible_count = None  # how many tabs can fit at once?

        # Track edges to know when to disable arrow buttons
        self.at_left_edge = True
        self.at_right_edge = False

        # Add your pop-out logic’s Menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Popout Tab", command=self.popout)

        # Bind right-click or middle-click on Mac
        if platform.system() == "Darwin":
            self.bind("<ButtonPress-2>", self._on_tab_rightclick)
        else:
            self.bind("<ButtonPress-3>", self._on_tab_rightclick)

        # Setup grid formatting if needed
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

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

    def _on_tab_rightclick(self, event):
        element = event.widget.identify(event.x, event.y)
        if "label" in element:
            try:
                x, y = self.get_absolute_position()
                self.menu.tk_popup(x, y)
            finally:
                self.menu.grab_release()

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

    def add(self, child, **kwargs):
        """
        Override to recalc scroll positions after new tab is added.
        """
        super().add(child, **kwargs)
        self.update_scrollable_tabs()

    def insert(self, index, child, **kwargs):
        """
        Override to recalc scroll positions after new tab is inserted.
        """
        super().insert(index, child, **kwargs)
        self.update_scrollable_tabs()

    def scroll_left(self):
        """
        Shift the visible tab range to the left (start_index -= 1).
        """
        if self._start_index > 0:
            self._start_index -= 1
        self.update_scrollable_tabs()

    def scroll_right(self):
        """
        Shift the visible tab range to the right (start_index += 1).
        """
        max_index = len(self.tabs()) - 1
        if self._start_index < max_index:
            self._start_index += 1
        self.update_scrollable_tabs()

    def update_scrollable_tabs(self, event=None):
        """
        Hide/show tabs so that only the subset of tabs that fit are visible.
        This is a simplistic approach. You can improve it by measuring actual
        pixel widths and/or the total available space for the tab row.
        """
        all_tabs = self.tabs()
        if not all_tabs:
            return

        # For example, you might guess that each tab's label is about 100 px wide
        # or measure them precisely with winfo_reqwidth. We'll do a rough approach:
        total_width = self.winfo_width()
        if total_width < 1:
            # If not mapped yet, skip
            return

        # In a real approach, you'd measure each tab label's width. For simplicity,
        # assume 120px per tab.
        approx_tab_width = 120
        self._visible_count = max(1, total_width // approx_tab_width)

        # compute end index = start index + how many tabs fit - 1
        end_index = self._start_index + self._visible_count - 1

        # clamp if end_index goes beyond available tabs
        end_index = min(end_index, len(all_tabs) - 1)

        # Hide all tabs, then re-show only the range
        for i, tab_id in enumerate(all_tabs):
            if i < self._start_index or i > end_index:
                self.tab(tab_id, state="hidden")
            else:
                self.tab(tab_id, state="normal")

        # Check if we are at the leftmost edge
        self.at_left_edge = (self._start_index == 0)
        # Check if we are at the rightmost edge
        self.at_right_edge = (end_index == len(all_tabs) - 1)
