# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
from tkinter import filedialog
import math
import logging

# Third Party Imports
import pandas as pd
from pandastable import TableModel

# Local Imports
from aslm.controller.sub_controllers.gui_controller import GUIController


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
        self.table.generatePositions = self.generate_positions
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
        print(
            "TODO: Implement feature that goes to the middle position of each tile, "
            "evaluates whether or not it consists of tissue, and if not, remove it."
        )

    def set_positions(self, positions):
        """Set positions to multi-position's table

        Parameters
        ----------
        positions : dict
            positions to be set

        Example
        -------
        >>>    positions = {
        >>>    0: {'x': 0, 'y': 0, 'z': 0, 'theta': 0, 'f': 0},
        >>>    1: {'x': 1, 'y': 1, 'z': 1, 'theta': 1, 'f': 1},
        >>>    2: {'x': 2, 'y': 2, 'z': 2, 'theta': 2, 'f': 2}}
        >>>    set_positions(positions)
        """
        axis_dict = {"x": "X", "y": "Y", "z": "Z", "theta": "R", "f": "F"}
        data = {}

        for name in axis_dict:
            data[axis_dict[name]] = list(pos[name] for pos in positions)
        self.table.model.df = pd.DataFrame(data)
        self.table.redraw()
        self.show_verbose_info("loaded new positions")

    def get_positions(self):
        """Return all positions from the Multi-Position Acquisition Interface.

        Returns
        -------
        dict
            positions in the format of {index: {axis: value}}

        Example
        -------
        >>> get_positions()
        """
        axis_dict = {"X": "x", "Y": "y", "Z": "z", "R": "theta", "F": "f"}
        positions = []
        rows = self.table.model.df.shape[0]
        for i in range(rows):
            temp = list(self.table.model.df.iloc[i])
            if (
                len(
                    list(filter(lambda v: type(v) == float and not math.isnan(v), temp))
                )
                == 5
            ):
                temp = dict(self.table.model.df.iloc[i])
                positions.append({})
                for k in axis_dict:
                    positions[i][axis_dict[k]] = temp[k]
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
        rowclicked = self.table.get_row_clicked(event)
        df = self.table.model.df
        temp = list(df.loc[rowclicked])
        # validate position
        if list(filter(lambda v: type(v) != int and type(v) != float, temp)):
            #  TODO: show error: position is invalid
            print("position is invalid")
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

        Example
        -------
        >>> get_position_num()
        """
        return self.table.model.df.shape[0]

    def load_positions(self):
        """Load a csv file.

        The valid csv file should contain the line of headers ['X', 'Y', 'Z', 'R', 'F']

        Example
        -------
        >>> load_positions()
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
            #  TODO: show error message
            print("The csv file isn't right, it should contain [X, Y, Z, R, F]")
            logger.info("The csv file isn't right, it should contain [X, Y, Z, R, F]")
            return
        model = TableModel(dataframe=df)
        self.table.updateModel(model)
        self.table.redraw()
        self.show_verbose_info("loaded csv file", filename)

    def export_positions(self):
        """Export the positions in the Multi-Position Acquisition Interface to a
        csv file.

        This function opens a dialog that let the user input a filename
        Then, it will export positions to that csv file

        Example
        -------
        >>> export_positions()
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
        """Move to a position within the Multi-Position Acquisition Interface.

        Example
        -------
        >>> move_to_position()
        """
        event = type("MyEvent", (object,), {})
        event.x, event.y = 0, 0
        self.handle_double_click(event)

    def insert_row_func(self):
        """Insert a row in the Multi-Position Acquisition Interface.

        Example
        -------
        >>> insert_row_func()
        """
        self.table.model.addRow(self.table.currentrow)
        self.table.update_rowcolors()
        self.table.redraw()
        self.table.tableChanged()
        self.show_verbose_info("insert a row before current row")

    def generate_positions(self):
        """Generate positions in the Multi-Position Acquisition Interface.

        This function opens a dialog to let the user input start and end position
        Then it will generate positions for the user.

        Example
        -------
        >>> generate_positions()
        """
        pass

    def add_stage_position(self):
        """Add the current stage position to the Multi-Position Acquisition Interface.

        This function will get the stage's current position,
        Then add it to position list

        Example
        -------
        >>> add_stage_position()
        """
        position = self.parent_controller.execute("get_stage_position")
        self.append_position(position)

    def append_position(self, position):
        """Append a position to the Multi-Position Acquisition Interface.

        Parameters
        ----------
        position : dict
            position in the format of {axis: value}

        Example
        -------
        >>> append_position(position)
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
