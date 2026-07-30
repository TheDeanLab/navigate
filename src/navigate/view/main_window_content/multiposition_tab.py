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

# Standard Library Imports
import tkinter as tk
from tkinter import ttk
import logging
from contextlib import contextmanager
from typing import Any

# Third Party Imports
import pandas as pd
from pandastable import Table, Menu, RowHeader, ColumnHeader
from pandastable.headers import IndexHeader
from pandastable import images as pt_images

# Local Imports
from navigate.tools.dataframe_compat import (
    insert_blank_row,
    sync_rowcolors_with_dataframe,
)
from navigate.view.custom_widgets.common import configure_grid, themed_grid
from navigate.view.theme import get_theme_color, get_theme_font

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def _safe_widget_configure(widget: Any, **kwargs: Any) -> None:
    """Configure a Tk widget while ignoring unsupported options."""

    for key, value in kwargs.items():
        try:
            widget.configure(**{key: value})
        except (tk.TclError, AttributeError):
            continue


@contextmanager
def _bind_pandastable_image_master(master: Any):
    """Ensure pandastable icon images are created in the current Tk interpreter."""

    original_photo_image = pt_images.tk.PhotoImage

    def _photo_image_with_master(*args: Any, **kwargs: Any):
        kwargs.setdefault("master", master)
        return original_photo_image(*args, **kwargs)

    pt_images.tk.PhotoImage = _photo_image_with_master
    try:
        yield
    finally:
        pt_images.tk.PhotoImage = original_photo_image


class MultiPositionTab(tk.Frame):
    """MultiPositionTab

    MultiPositionTab is a tab in the main window that allows the user to
    create and run multipoint experiments."""

    def __init__(self, setntbk, *args, **kwargs):
        """Initialize the MultiPositionTab

        Parameters
        ----------
        setntbk : ttk.Notebook
            The notebook that contains the settings tab.
        *args : tuple
            Variable length argument list.
        **kwargs : dict
            Arbitrary keyword arguments.
        """
        # Init Frame
        super().__init__(setntbk, *args, **kwargs)

        #: The index of the tab in the notebook
        self.index = 3

        #: MultiPointFrame: The frame that contains the widgets for the multipoint
        # experiment settings.
        self.tiling_buttons = MultiPointFrame(self)
        themed_grid(
            self.tiling_buttons,
            row=0,
            column=0,
            sticky=tk.EW,
            padx="layout_panel_gap",
            pady=("layout_panel_gap", "layout_section_gap"),
        )

        #: MultiPointList: The frame that contains the widgets for the multipoint
        # experiment settings.
        self.multipoint_list = MultiPointList(self)
        themed_grid(
            self.multipoint_list,
            row=1,
            column=0,
            sticky=tk.NSEW,
            padx="layout_panel_gap",
            pady=("layout_section_gap", "layout_panel_gap"),
        )

        configure_grid(self, columns={0: 1}, rows={0: 0, 1: 1})


class MultiPointFrame(ttk.Labelframe):
    """MultiPointFrame

    MultiPointFrame is a frame that contains the widgets for the multipoint
    experiment settings."""

    def __init__(self, settings_tab, *args, **kwargs):
        """Initialize the MultiPointFrame

        Parameters
        ----------
        settings_tab : tk.Frame
            The frame that contains the settings tab.
        *args : tuple
            Variable length argument list.
        **kwargs : dict
            Arbitrary keyword arguments.

        """
        text_label = "Multi-Position Acquisition"
        super().__init__(settings_tab, text=text_label, *args, **kwargs)

        #: dict: A dictionary of all the widgets that are tied to each widget name.
        self.buttons = {
            "tiling": ttk.Button(self, text="Launch Tiling Wizard"),
            "save_data": ttk.Button(self, text="Save Positions to Disk"),
            "load_data": ttk.Button(self, text="Load Positions from Disk"),
            "eliminate_tiles": ttk.Button(self, text="Eliminate Empty Positions"),
        }
        counter = 0
        for key, button in self.buttons.items():
            if counter == 0:
                row, column = 0, 0
            elif counter == 1:
                row, column = 1, 0
            elif counter == 2:
                row, column = 1, 1
            else:
                row, column = 0, 1

            themed_grid(
                button,
                row=row,
                column=column,
                sticky=tk.NSEW,
                padx="space_2",
                pady="space_2",
            )
            counter += 1

        configure_grid(self, columns={0: 1, 1: 1}, rows={0: 1, 1: 1})

    def get_variables(self):
        """Returns a dictionary of all the variables that are tied to each widget name.

        The key is the widget name, value is the variable associated.

        Returns
        -------
        dict
            A dictionary of all the variables that are tied to each widget name.
        """
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get_variable()
        return variables

    def get_widgets(self):
        """Returns a dictionary of all the widgets that are tied to each widget name.

        The key is the widget name, value is the LabelInput class that has all the data.

        Returns
        -------
        inputs : dict
            A dictionary of all the widgets that are tied to each widget name.
        """
        return self.inputs


class MultiPointList(ttk.Frame):
    """MultiPointList

    MultiPointList is a frame that contains the widgets for the multipoint
    experiment settings. uses Pandastable for embedding an interactive list within a
    tk Frame. https://pandastable.readthedocs.io/en/latest/
    """

    def __init__(self, settings_tab, *args, **kwargs):
        """Initialize the MultiPointList

        Parameters
        ----------
        settings_tab : tk.Frame
            The frame that contains the settings tab.
        *args : tuple
            Variable length argument list.
        **kwargs : dict
            Arbitrary keyword arguments.
        """
        super().__init__(settings_tab, *args, **kwargs)

        df = pd.DataFrame({"X": [0], "Y": [0], "Z": [0], "THETA": [0], "F": [0]})

        #: MultiPositionTable: The PandasTable instance that is being used.
        self.pt = MultiPositionTable(self, showtoolbar=False, showstatusbar=True)
        self.pt.show()
        self.pt.model.df = df
        configure_grid(self, columns={0: 0, 1: 1}, rows={0: 0, 1: 1, 2: 0})

    def get_table(self):
        """Returns a reference to multipoint table dataframe.

        Parameters
        ----------
        self : object
            Multipoint List instance

        Returns
        -------
        self.pt: MultiPositionTable
            Reference to table data as dataframe
        """
        return self.pt


class MultiPositionRowHeader(RowHeader):
    """MultiPositionRowHeader

    MultiPositionRowHeader is a class that inherits from RowHeader. It is used to
    customize the row header for the multipoint table.
    """

    def __init__(self, parent=None, table=None, width=50):
        """Initialize the MultiPositionRowHeader

        Parameters
        ----------
        parent : tk.Frame
            The frame that contains the settings tab.
        table : PandasTable
            The PandasTable instance that is being used.
        width : int
            The width of the row header.
        """
        super().__init__(parent, table, width)
        self.color = get_theme_color("surface_bg", "gray75")

    def redraw(self, align="w", showkeys=False):
        """Redraw row header and apply themed colors."""
        super().redraw(align=align, showkeys=showkeys)
        border_color = get_theme_color("border", "gray50")
        text_color = get_theme_color("text", "black")
        try:
            self.itemconfigure("rowheader", fill=self.color, outline=border_color)
            self.itemconfigure("text", fill=text_color, font=self.table.thefont)
        except tk.TclError:
            pass

    def drawRect(self, row=None, tag=None, color=None, outline=None, delete=1):
        """Draw a row-selection rectangle using themed colors."""
        if tag is None:
            tag = "rect"
        if color is None:
            color = get_theme_color("accent", "#0099CC")
        if outline is None:
            outline = get_theme_color("border", "gray25")
        if delete == 1:
            self.delete(tag)
        inset = getattr(self, "inset", 1)
        _, y1, _, y2 = self.table.getCellCoords(row, 0)
        self.create_rectangle(
            inset,
            y1 + inset,
            self.width - inset,
            y2,
            fill=color,
            outline=outline,
            width=0,
            tag=tag,
        )
        self.lift("text")

    def popupMenu(self, event, rows=None, cols=None, outside=None):
        """Add right click behaviour for row header

        Parameters
        ----------
        event : tk.Event
            The event that triggers the popup menu.
        rows : list
            The list of rows that are selected.
        cols : list
            The list of columns that are selected.
        outside : bool
            Whether the popup menu is triggered outside the table.

        Returns
        -------
        popupmenu : tk.Menu
            The popup menu.
        """

        defaultactions = {
            "Sort by index": lambda: self.table.sortTable(index=True),
            "Reset index": lambda: self.table.resetIndex(),
            "Toggle index": lambda: self.toggleIndex(),
            "Copy index to column": lambda: self.table.copyIndex(),
            "Rename index": lambda: self.table.renameIndex(),
            "Sort columns by row": lambda: self.table.sortColumnIndex(),
            "Select All": self.table.selectAll,
            "Insert New Position": self.table.insertRow,
            "Add Current Position": self.table.addStagePosition,
            "Add New Position(s)": lambda: self.table.addRows(),
            "Delete Position(s)": lambda: self.table.deleteRow(),
            "Duplicate Row(s)": lambda: self.table.duplicateRows(),
            "Set Row Color": lambda: self.table.setRowColors(cols="all"),
        }
        main = [
            "Insert New Position",
            "Add Current Position",
            "Add New Position(s)",
            "Delete Position(s)",
        ]

        popupmenu = Menu(self, tearoff=0)

        def popupFocusOut(event):
            popupmenu.unpost()

        for action in main:
            popupmenu.add_command(label=action, command=defaultactions[action])

        popupmenu.bind("<FocusOut>", popupFocusOut)
        popupmenu.focus_set()
        popupmenu.post(event.x_root, event.y_root)
        # applyStyle(popupmenu)
        return popupmenu


class MultiPositionColumnHeader(ColumnHeader):
    """MultiPositionColumnHeader

    MultiPositionColumnHeader is a class that inherits from ColumnHeader. It is used to
    customize the column header for the multipoint table.
    """

    def __init__(self, parent=None, table=None, bg=None):
        """Initialize the MultiPositionColumnHeader

        Parameters
        ----------
        parent : tk.Frame
            The frame that contains the settings tab.
        table : PandasTable
            The PandasTable instance that is being used.
        bg : str
            The background color of the column header.
        """

        if bg is None:
            bg = get_theme_color("surface_bg", "gray25")
        super().__init__(parent, table, bg)
        self.thefont = get_theme_font("body_bold")
        self.colselectedcolor = get_theme_color("accent", "#0099CC")

    def redraw(self, align="w"):
        """Redraw column header and apply themed line/text colors."""
        super().redraw(align=align)
        border_color = get_theme_color("border", "gray25")
        text_color = get_theme_color("text", "white")
        try:
            self.itemconfigure("gridline", fill=border_color)
            self.itemconfigure("text", fill=text_color, font=self.thefont)
        except tk.TclError:
            pass

    def drawRect(self, col, tag=None, color=None, outline=None, delete=1):
        """Draw selected column rectangle using themed colors."""
        if tag is None:
            tag = "rect"
        if color is None:
            color = self.colselectedcolor
        if outline is None:
            outline = get_theme_color("border", "gray25")
        if delete == 1:
            self.delete(tag)
        x1, y1, x2, _ = self.table.getCellCoords(0, col)
        self.create_rectangle(
            x1,
            y1 - 1,
            x2,
            self.height,
            fill=color,
            outline=outline,
            width=1,
            tag=tag,
        )
        self.lower(tag)

    def popupMenu(self, event):
        """Add left and right click behaviour for column header

        Parameters
        ----------
        event : tk.Event
            The event that triggers the popup menu.

        Returns
        -------
        popupmenu : tk.Menu
            The popup menu.
        """

        df = self.table.model.df
        if len(df.columns) == 0:
            return

        multicols = self.table.multiplecollist
        colnames = list(df.columns[multicols])[:4]
        colnames = [str(i)[:20] for i in colnames]
        if len(colnames) > 2:
            colnames = ",".join(colnames[:2]) + "+%s others" % str(len(colnames) - 2)
        else:
            colnames = ",".join(colnames)
        popupmenu = Menu(self, tearoff=0)

        def popupFocusOut(event):
            """Unpost the popup menu"""
            popupmenu.unpost()

        popupmenu.add_command(
            label="Sort by " + colnames + " \u2193",
            command=lambda: self.table.sortTable(
                columnIndex=multicols, ascending=[0 for i in multicols]
            ),
        )
        popupmenu.add_command(
            label="Sort by " + colnames + " \u2191",
            command=lambda: self.table.sortTable(
                columnIndex=multicols, ascending=[1 for i in multicols]
            ),
        )
        popupmenu.add_command(label="Rename", command=self.renameColumn)
        popupmenu.add_command(label="Add", command=self.table.addColumn)
        popupmenu.add_command(label="Delete Column(s)", command=self.table.deleteColumn)

        popupmenu.bind("<FocusOut>", popupFocusOut)
        popupmenu.focus_set()
        popupmenu.post(event.x_root, event.y_root)
        # applyStyle(popupmenu)
        return popupmenu


class MultiPositionIndexHeader(IndexHeader):
    """Theme-aware top-left corner header for the multiposition table."""

    def __init__(self, parent=None, table=None, bg=None):
        if bg is None:
            bg = get_theme_color("surface_bg", "gray75")
        super().__init__(parent=parent, table=table)
        border_color = get_theme_color("border", "gray50")
        _safe_widget_configure(
            self,
            bg=bg,
            highlightbackground=border_color,
            highlightcolor=border_color,
        )


class MultiPositionTable(Table):
    """MultiPositionTable

    MultiPositionTable is a class that inherits from Table. It is used to
    customize the table for the multipoint table.
    """

    def __init__(self, parent=None, **kwargs):
        """Initialize the MultiPositionTable

        Parameters
        ----------
        parent : tk.Frame
            The frame that contains the settings tab.
        **kwargs : dict
            Arbitrary keyword arguments.
        """

        super().__init__(parent, width=400, height=500, columns=4, **kwargs)

        self.loadCSV = None
        self.exportCSV = None
        self.insertRow = None
        self.addStagePosition = None

    def update_rowcolors(self) -> None:
        """Keep rowcolors aligned with table data across pandas versions."""
        self.rowcolors = sync_rowcolors_with_dataframe(
            self.model.df, getattr(self, "rowcolors", None)
        )

    def addRow(self) -> None:
        """Insert a blank row without using deprecated pandas append APIs."""
        row = self.getSelectedRow()
        if row is None:
            row = self.model.df.shape[0]

        self.model.df = insert_blank_row(self.model.df, row)
        self.currentrow = max(0, min(int(row), self.model.df.shape[0] - 1))
        self.update_rowcolors()
        self.redraw()
        self.tableChanged()

    def apply_theme(self, redraw=True):
        """Apply active Navigate theme tokens to pandastable surfaces."""
        panel_bg = get_theme_color("panel_bg", "#1a212b")
        surface_bg = get_theme_color("surface_bg", "gray25")
        input_bg = get_theme_color("input_bg", "white")
        border = get_theme_color("border", "gray50")
        text = get_theme_color("text", "black")
        muted_text = get_theme_color("muted_text", text)
        accent = get_theme_color("accent", "#0099CC")
        accent_hover = get_theme_color("accent_hover", accent)
        accent_pressed = get_theme_color("accent_pressed", accent_hover)

        self.thefont = get_theme_font("body")
        self.textcolor = text
        self.bgcolor = input_bg
        self.cellbackgr = input_bg
        self.grid_color = border
        self.rowselectedcolor = accent
        self.colselectedcolor = accent
        self.multipleselectioncolor = accent_pressed
        self.colheadercolor = surface_bg
        self.rowheadercolor = surface_bg

        _safe_widget_configure(self.parentframe, bg=panel_bg)
        _safe_widget_configure(
            self,
            bg=input_bg,
            highlightbackground=border,
            highlightcolor=border,
        )

        if hasattr(self, "rowheader") and self.rowheader is not None:
            self.rowheader.color = surface_bg
            _safe_widget_configure(
                self.rowheader,
                bg=surface_bg,
                highlightbackground=border,
                highlightcolor=border,
            )

        if hasattr(self, "colheader") and self.colheader is not None:
            self.colheader.bgcolor = surface_bg
            self.colheader.colselectedcolor = accent
            self.colheader.thefont = get_theme_font("body_bold")
            _safe_widget_configure(
                self.colheader,
                bg=surface_bg,
                highlightbackground=border,
                highlightcolor=border,
            )

        if hasattr(self, "rowindexheader") and self.rowindexheader is not None:
            _safe_widget_configure(
                self.rowindexheader,
                bg=surface_bg,
                highlightbackground=border,
                highlightcolor=border,
            )

        statusbar = getattr(self, "statusbar", None)
        if statusbar is not None:
            _safe_widget_configure(statusbar, bg=panel_bg)
            caption_font = get_theme_font("caption")
            for name in ("label", "queryvar", "plotvar", "rowsvar"):
                widget = getattr(statusbar, name, None)
                if widget is not None:
                    _safe_widget_configure(
                        widget, bg=panel_bg, fg=muted_text, font=caption_font
                    )
            if getattr(statusbar, "label", None) is not None:
                _safe_widget_configure(statusbar.label, fg=text)

        if redraw:
            self.redraw()

    def resized(self, event):
        """Guard resize redraws against transient column-index mismatches."""
        try:
            super().resized(event)
        except IndexError:
            logger.debug("Retrying multiposition resize redraw after IndexError.")
            self.after_idle(self._safe_redraw_visible)

    def _safe_redraw_visible(self):
        """Retry visible redraw safely after resize-related races."""
        try:
            self.redrawVisible()
        except IndexError:
            logger.debug("Skipping multiposition redraw due to transient IndexError.")

    def show(self, callback=None):
        """Show the table

        Parameters
        ----------
        callback : function
            The function that is called when the table is shown.
        """
        # Pandastable creates statusbar icon PhotoImage objects without explicit
        # masters. In multi-root test sessions this can bind icons to another Tk
        # interpreter and later raise: image "pyimage..." doesn't exist.
        with _bind_pandastable_image_master(self.parentframe):
            super().show(callback)

        try:
            self.rowheader.destroy()
            self.colheader.destroy()
            self.rowindexheader.destroy()
        except AttributeError:
            pass

        #: MultiPositionRowHeader: The row header for the table.
        self.rowheader = MultiPositionRowHeader(self.parentframe, self)
        self.rowheader.grid(row=1, column=0, rowspan=1, sticky="news")

        column_header_bg = getattr(
            self, "colheadercolor", get_theme_color("surface_bg", "gray25")
        )
        #: MultiPositionColumnHeader: The column header for the table.
        self.colheader = MultiPositionColumnHeader(
            self.parentframe, self, bg=column_header_bg
        )
        self.colheader.grid(row=0, column=1, rowspan=1, sticky="news")
        self.tablecolheader = self.colheader

        row_index_header_bg = getattr(
            self, "rowheadercolor", get_theme_color("surface_bg", "gray75")
        )
        #: MultiPositionIndexHeader: The index header for the table.
        self.rowindexheader = MultiPositionIndexHeader(
            self.parentframe, self, bg=row_index_header_bg
        )
        self.rowindexheader.grid(row=0, column=0, rowspan=1, sticky="news")

        self.apply_theme(redraw=False)

    def popupMenu(self, event, rows=None, cols=None, outside=None):
        """Add right click behaviour for table

        Parameters
        ----------
        event : tk.Event
            The event that triggers the popup menu.
        rows : list
            The list of rows that are selected.
        cols : list
            The list of columns that are selected.
        outside : bool
            Whether the popup menu is triggered outside the table.

        Returns
        -------
        popupmenu : tk.Menu
            The popup menu.
        """
        popupmenu = Menu(self, tearoff=0)

        def popupFocusOut(event):
            popupmenu.unpost()

        popupmenu.add_command(label="Load Positions from Disk", command=self.loadCSV)
        popupmenu.add_command(label="Save Positions to Disk", command=self.exportCSV)
        popupmenu.bind("<FocusOut>", popupFocusOut)
        popupmenu.focus_set()
        popupmenu.post(event.x_root, event.y_root)
        return popupmenu
