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
from pandastable import Table, Menu, RowHeader, ColumnHeader
import tkinter as tk
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Multi_Position_RowHeader(RowHeader):
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


class Multi_Position_ColumnHeader(ColumnHeader):
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


class Multi_Position_Table(Table):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, width=400, height=500, columns=4, **kwargs)

        self.loadCSV = None
        self.exportCSV = None
        self.insertRow = None
        self.generatePositions = None
        self.addStagePosition = None

    def show(self, callback=None):
        super().show(callback)

        # Formatting
        tk.Grid.columnconfigure(self, "all", weight=1)
        tk.Grid.rowconfigure(self, "all", weight=1)

        self.rowheader = Multi_Position_RowHeader(self.parentframe, self)
        self.rowheader.grid(row=1, column=0, rowspan=1, sticky="news")

        self.tablecolheader = Multi_Position_ColumnHeader(
            self.parentframe, self, bg=self.colheadercolor
        )
        self.tablecolheader.grid(row=0, column=1, rowspan=1, sticky="news")

    def popupMenu(self, event, rows=None, cols=None, outside=None):
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
