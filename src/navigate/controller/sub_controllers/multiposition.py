# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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
from tkinter import filedialog, messagebox
import math
import logging

# Third Party Imports
import pandas as pd

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class MultiPositionController(GUIController):
    """Controller for the Multi-Position Acquisition Interface."""

    def __init__(self, view, parent_controller=None):
        """Initialize the Multi-Position Acquisition Interface.

        Parameters
        ----------
        view : MultiPositionView
            view for the Multi-Position Acquisition Interface
        parent_controller : Controller, optional
            parent controller, by default None
        """
        super().__init__(view, parent_controller)
        #: MultiPositionTable: Multi-Position Acquisition Interface
        self.table = self.view.pt

        # self.table.rowheader.bind("<Double-Button-1>", self.handle_double_click)
        self.table.loadCSV = self.load_positions
        self.table.exportCSV = self.export_positions
        self.table.insertRow = self.insert_row_func
        self.table.addStagePosition = self.add_stage_position

        self.view.master.tiling_buttons.buttons["tiling"].config(
            command=self.parent_controller.channels_tab_controller.launch_tiling_wizard
        )

        self.view.master.tiling_buttons.buttons["save_data"].config(
            command=self.export_positions
        )

        self.view.master.tiling_buttons.buttons["load_data"].config(
            command=self.load_positions
        )

        self.view.master.tiling_buttons.buttons["eliminate_tiles"].config(
            command=self.eliminate_tiles
        )

    def eliminate_tiles(self):
        """Eliminate tiles that do not contain tissue."""
        self.parent_controller.execute("eliminate_tiles")

    def set_positions(self, positions):
        """Set positions to multi-position's table

        Parameters
        ----------
        positions : [[]]
            positions to be set
        """
        axis_dict = {"x": "X", "y": "Y", "z": "Z", "theta": "R", "f": "F"}
        data = {}

        for i, name in enumerate(axis_dict.keys()):
            data[axis_dict[name]] = list(pos[i] for pos in positions)
        self.table.model.df = pd.DataFrame(data)
        self.table.currentrow = 0
        self.table.redraw()
        self.table.tableChanged()
        self.show_verbose_info("loaded new positions")

    def get_positions(self):
        """Return all positions from the Multi-Position Acquisition Interface.

        Returns
        -------
        list
            positions in the format of [[x, y, z, theta, f], ]
        """
        positions = []
        rows = self.table.model.df.shape[0]
        for i in range(rows):
            temp = list(self.table.model.df.iloc[i])
            if (
                len(
                    list(
                        filter(
                            lambda v: type(v) in (float, int) and not math.isnan(v),
                            temp,
                        )
                    )
                )
                == 5
            ):
                positions.append(temp)
        return positions

    def handle_double_click(self, event):
        """Move to a position within the Multi-Position Acquisition Interface.

        When double-clicked the row head, it will call the parent/central controller
        to move stage and update stage view

        Parameters
        ----------
        event : tkinter event
            event that triggers the function
        """
        # it is calculated based on the GUI position
        rowclicked = self.table.get_row_clicked(event)
        # make sure a valid row is clicked
        if rowclicked >= self.table.model.df.shape[0]:
            return
        df = self.table.model.df
        # df.loc uses key index
        # df.iloc uses position index
        temp = list(df.iloc[rowclicked])
        # validate position
        if list(filter(lambda v: type(v) != int and type(v) != float, temp)):
            messagebox.showwarning(
                title="Warning",
                message="The selected position is invalid, can't go to this position!",
            )
            logger.info("position is invalid")
            return
        position = {
            "x": temp[0],
            "y": temp[1],
            "z": temp[2],
            "theta": temp[3],
            "f": temp[4],
        }
        self.parent_controller.execute("move_stage_and_update_info", position)
        self.show_verbose_info("move stage to", position)

    def get_position_num(self):
        """Return the number of positions in the Multi-Position Acquisition Interface.

        Returns
        -------
        int
            number of positions
        """
        return self.table.model.df.shape[0]

    def load_positions(self):
        """Load a csv file.

        The valid csv file should contain the line of headers ['X', 'Y', 'Z', 'R', 'F']
        """
        filename = filedialog.askopenfilenames(
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("Text files", "*.txt")),
        )
        if not filename:
            return
        df = pd.read_csv(filename[0])
        # validate the csv file
        df.columns = map(lambda v: v.upper(), df.columns)
        cmp_header = df.columns == ["X", "Y", "Z", "R", "F"]
        if not cmp_header.all():
            messagebox.showwarning(
                title="Warning",
                message="The csv file isn't right, it should contain [X, Y, Z, R, F]",
            )
            logger.info("The csv file isn't right, it should contain [X, Y, Z, R, F]")
            return
        self.table.model.df = df
        self.table.currentrow = 0
        # reset index
        self.table.resetColors()
        self.table.redraw()
        self.table.tableChanged()
        self.show_verbose_info("loaded csv file", filename)

    def export_positions(self):
        """Export the positions in the Multi-Position Acquisition Interface to a
        csv file.

        This function opens a dialog that let the user input a filename
        Then, it will export positions to that csv file
        """
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("CSV file", "*.csv"), ("Text file", "*.txt")),
        )
        if not filename:
            return
        self.table.model.df.to_csv(filename, index=False)
        self.show_verbose_info("exporting csv file", filename)

    def move_to_position(self):
        """Move to a position within the Multi-Position Acquisition Interface."""
        event = type("MyEvent", (object,), {})
        event.x, event.y = 0, 0
        self.handle_double_click(event)

    def insert_row_func(self):
        """Insert a row in the Multi-Position Acquisition Interface."""
        self.table.model.addRow(self.table.currentrow)
        self.table.update_rowcolors()
        self.table.redraw()
        self.table.tableChanged()
        self.show_verbose_info("insert a row before current row")

    def add_stage_position(self):
        """Add the current stage position to the Multi-Position Acquisition Interface.

        This function will get the stage's current position,
        Then add it to position list
        """
        position = self.parent_controller.execute("get_stage_position")
        self.append_position(position)

    def append_position(self, position):
        """Append a position to the Multi-Position Acquisition Interface.

        Parameters
        ----------
        position : dict
            position in the format of {axis: value}
        """
        temp = list(map(lambda k: position[k], position))
        self.table.model.df = self.table.model.df.append(
            pd.DataFrame([temp], columns=list("XYZRF")), ignore_index=True
        )
        self.table.currentrow = self.table.model.df.shape[0] - 1
        self.table.update_rowcolors()
        self.table.redraw()
        self.table.tableChanged()
        self.show_verbose_info("add current stage position to position list")

    def remove_positions(self, position_flag_list):
        """Remove positions according to position_flag_list

        Parameters
        ----------
        position_flag_list : list[bool]
            False: the position should be removed
            True: the position should be kept
        """
        positions = self.get_positions()
        l = len(position_flag_list)  # noqa
        new_positions = [
            p for i, p in enumerate(positions) if (i >= l or position_flag_list[i])
        ]
        self.set_positions(new_positions)

    @property
    def custom_events(self):
        """Return custom events for the Multi-Position Controller."""
        return {"remove_positions": self.remove_positions}
