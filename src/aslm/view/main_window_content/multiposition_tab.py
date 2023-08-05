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
from tkinter import ttk
import logging

# Third Party Imports
import pandas as pd
from pandastable import Table, Menu, RowHeader, ColumnHeader

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class MultiPositionTab(tk.Frame):
    """MultiPositionTab

    MultiPositionTab is a tab in the main window that allows the user to
    create and run multipoint experiments.

    Parameters
    ----------
    setntbk : Notebook
        The notebook that contains the tab.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    index : int
        The index of the tab in the notebook.
    multipoint_list : MultiPointList
        The multipoint_list object that contains the list of multipoint
        experiments.

    Methods
    -------
    None
    """

    def __init__(self, setntbk, *args, **kwargs):
        # Init Frame
        tk.Frame.__init__(self, setntbk, *args, **kwargs)

        self.index = 3

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Tiling Buttons
        self.tiling_buttons = MultiPointFrame(self)
        self.tiling_buttons.grid(
            row=0, column=0, columnspan=3, sticky=tk.NSEW, padx=10, pady=10
        )

        # Multipoint List
        self.multipoint_list = MultiPointList(self)
        self.multipoint_list.grid(
            row=6, column=0, columnspan=3, sticky=tk.NSEW, padx=10, pady=10
        )


class MultiPointFrame(ttk.Labelframe):
    """MultiPointFrame

    MultiPointFrame is a frame that contains the widgets for the multipoint
    experiment settings.

    Parameters
    ----------
    settings_tab : tk.Frame
        The frame that contains the settings tab.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    buttons : dict
        A dictionary of all the buttons that are tied to each widget name.
        The key is the widget name, value is the button associated.

    Methods
    -------
    get_variables()
        This function returns a dictionary of all the
        variables that are tied to each widget name.
        The key is the widget name,
        value is the variable associated.
    get_widgets()
        This function returns a dictionary of all the
        widgets that are tied to each widget name.
        The key is the widget name,
        value is the widget associated.
    """

    def __init__(self, settings_tab, *args, **kwargs):
        text_label = "Multi-Position Acquisition"
        ttk.Labelframe.__init__(self, settings_tab, text=text_label, *args, **kwargs)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        # Tiling Wizard Button
        self.buttons = {
            "tiling": ttk.Button(self, text="Launch Tiling Wizard"),
            "save_data": ttk.Button(self, text="Save Positions to Disk"),
            "load_data": ttk.Button(self, text="Load Positions from Disk"),
        }
        column = 0
        for key, button in self.buttons.items():
            button.grid(row=0, column=column, sticky=tk.NSEW, padx=(4, 1), pady=(4, 6))
            column += 1

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
        dict
            A dictionary of all the widgets that are tied to each widget name.
        """
        return self.inputs


class MultiPointList(ttk.Frame):
    """MultiPointList

    MultiPointList is a frame that contains the widgets for the multipoint
    experiment settings. uses Pandastable for embedding an interactive list within a
    tk Frame. https://pandastable.readthedocs.io/en/latest/

    Parameters
    ----------
    settings_tab : tk.Frame
        The frame that contains the settings tab.
    *args : tuple
        Variable length argument list.
    **kwargs : dict
        Arbitrary keyword arguments.

    Attributes
    ----------
    laser_label : ttk.Label
        The label for the laser checkbox.
    on_off : tk.BooleanVar
        The variable that holds the state of the laser checkbox.
    save_check : ttk.Checkbutton
        The checkbox that enables or disables the laser.

    Methods
    -------
    get_variables()
        This function returns a dictionary of all the
        variables that are tied to each widget name.
        The key is the widget name,
        value is the variable associated.
    get_widgets()
        This function returns a dictionary of all the
        widgets that are tied to each widget name.
        The key is the widget name,
        value is the widget associated.
    """

    def __init__(self, settings_tab, *args, **kwargs):
        # Init Frame
        ttk.Frame.__init__(self, settings_tab, *args, **kwargs)

        df = pd.DataFrame({"X": [0], "Y": [0], "Z": [0], "R": [0], "F": [0]})
        self.pt = MultiPositionTable(self, showtoolbar=False)
        self.pt.show()
        self.pt.model.df = df

    def get_table(self):
        """Returns a reference to multipoint table dataframe.

        Parameters
        ----------
        self : object
            Multipoint List instance


        Returns
        -------
        self.pt.model.df: Pandas DataFrame
            Reference to table data as dataframe
        """
        return self.pt


class MultiPositionRowHeader(RowHeader):
    """MultiPositionRowHeader

    MultiPositionRowHeader is a class that inherits from RowHeader. It is used to
    customize the row header for the multipoint table.

    Parameters
    ----------
    parent : tk.Frame
        The frame that contains the settings tab.
    table : PandasTable
        The PandasTable instance that is being used.
    width : int
        The width of the row header.

    Methods
    -------
    popupMenu(event, rows=None, cols=None, outside=None)
        This function creates a popup menu for the row header.
    toggleIndex()
        This function toggles the index column.
    """

    def __init__(self, parent=None, table=None, width=50):
        super().__init__(parent, table, width)

    def popupMenu(self, event, rows=None, cols=None, outside=None):
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

    Parameters
    ----------
    parent : tk.Frame
        The frame that contains the settings tab.
    table : PandasTable
        The PandasTable instance that is being used.
    bg : str
        The background color of the column header.

    Attributes
    ----------
    None

    Methods
    -------
    popupMenu(event)
        This function creates a popup menu for the column header.
    """

    def __init__(self, parent=None, table=None, bg="gray25"):
        super().__init__(parent, table, bg)

    def popupMenu(self, event):
        """Add left and right click behaviour for column header"""

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
        popupmenu.bind("<FocusOut>", popupFocusOut)
        popupmenu.focus_set()
        popupmenu.post(event.x_root, event.y_root)
        # applyStyle(popupmenu)
        return popupmenu


class MultiPositionTable(Table):
    """MultiPositionTable

    MultiPositionTable is a class that inherits from Table. It is used to
    customize the table for the multipoint table.

    Parameters
    ----------
    parent : tk.Frame
        The frame that contains the settings tab.
    **kwargs : dict
        Keyword arguments for the Table class.

    Attributes
    ----------
    loadCSV : tk.Button
        The button that loads a CSV file.
    exportCSV : tk.Button
        The button that exports the table to a CSV file.
    insertRow : tk.Button
        The button that inserts a new row.
    generatePositions : tk.Button
        The button that generates positions.
    addStagePosition : tk.Button
        The button that adds the current stage position.

    Methods
    -------
    show(callback=None)
        This function shows the table.
    """

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, width=400, height=500, columns=4, **kwargs)

        self.loadCSV = None
        self.exportCSV = None
        self.insertRow = None
        self.generatePositions = None
        self.addStagePosition = None

    def show(self, callback=None):
        """Show the table

        Parameters
        ----------
        callback : function
            The function that is called when the table is shown.

        Returns
        -------
        None
        """
        super().show(callback)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        self.rowheader = MultiPositionRowHeader(self.parentframe, self)
        self.rowheader.grid(row=1, column=0, rowspan=1, sticky="news")

        self.tablecolheader = MultiPositionColumnHeader(
            self.parentframe, self, bg=self.colheadercolor
        )
        self.tablecolheader.grid(row=0, column=1, rowspan=1, sticky="news")

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

        popupmenu.add_command(label="Import Text/csv", command=self.loadCSV)
        popupmenu.add_command(label="Export", command=self.exportCSV)
        popupmenu.add_command(label="Generate Position", command=self.generatePositions)
        popupmenu.bind("<FocusOut>", popupFocusOut)
        popupmenu.focus_set()
        popupmenu.post(event.x_root, event.y_root)
        return popupmenu
