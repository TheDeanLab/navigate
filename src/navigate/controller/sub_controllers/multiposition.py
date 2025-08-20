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
import numpy as np
import os
import yaml

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.tools.file_functions import (
    load_yaml_file,
    save_yaml_file,
)


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
        stage_axes = self.parent_controller.configuration_controller.stage_axes
        data = {}
        if len(positions) == 0:
            # add current stage position to the table
            stage_position = self.parent_controller.configuration["experiment"][
                "StageParameters"
            ]
            # get the current stage position
            positions = [[stage_position[axis] for axis in stage_axes]]
        # check if the positions contain the headers (column names)
        cmp_header = [axis.upper() in positions[0] for axis in stage_axes]
        # if positions[0] contains ["X", "Y", "Z", "R", "F"], then consider it as headers
        # else add headers to the table
        if not all(cmp_header):
            # if the first row contains some headers, update the headers
            if any(cmp_header):
                headers = positions[0]
                for i, flag in enumerate(cmp_header):
                    if not flag:
                        headers.append(stage_axes[i].upper())
                start_index = 1
            else:
                headers = [axis.upper() for axis in stage_axes]
                start_index = 0
        else:
            headers = positions[0]
            start_index = 1
        # if there are some missing headers, add them
        if len(headers) < len(positions[start_index]):
            headers = headers + ["col-" + str(i) for i in range(len(positions[start_index]) - len(headers))]
        for i, name in enumerate(headers):
            data[name] = list(pos[i] if i < len(pos) else np.nan for pos in positions[start_index:])
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
        positions = [list(self.table.model.df.columns)]
        stage_axes = self.parent_controller.configuration_controller.stage_axes
        axes_index = []
        for axis in stage_axes:
            if axis.upper() in positions[0]:
                axes_index.append(positions[0].index(axis.upper()))
        # axes_index = [positions[0].index(axis) for axis in [axis.upper() for axis in stage_axes]]
        rows = self.table.model.df.shape[0]
        for i in range(rows):
            temp = list(self.table.model.df.iloc[i])
            if (
                len(
                    list(
                        filter(
                            lambda v: isinstance(v, (float, int)) and not math.isnan(v),
                            [temp[i] for i in axes_index],
                        )
                    )
                )
                == len(axes_index)
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
        stage_axes = self.parent_controller.configuration_controller.stage_axes
        axes_index = [df.columns.get_loc(axis) for axis in [axis.upper() for axis in stage_axes]]
        # validate position
        # we currently only move to a position doesn't contain nan
        if len(list(filter(lambda v: isinstance(v, (float, int)) and not math.isnan(v), [temp[i] for i in axes_index]))) != len(stage_axes):
            messagebox.showwarning(
                title="Warning",
                message="The selected position is invalid, can't go to this position!",
            )
            logger.info("position is invalid")
            return
        position = {}
        for i, axis in enumerate(stage_axes):
            position[axis] = temp[axes_index[i]]
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
        """Load a yml or csv file.

        The valid yml/csv file should contain the line of headers: stage axes
        """
        filename = filedialog.askopenfilenames(
            defaultextension=".yml",
            filetypes=(("yml file", "*.yml"),("CSV files", "*.csv"), ("Text files", "*.txt")),
        )
        if not filename:
            return
        if filename[0].endswith(".yml"):
            # Load YAML/JSON file
            with open(filename[0], "r") as f:
                data = yaml.safe_load(f)  # works because YAML supports JSON too
            # First row is header, rest are data
            df = pd.DataFrame(data[1:], columns=data[0])
        else:
            df = pd.read_csv(filename[0])
        # validate the csv/yml file
        df.columns = map(lambda v: v.upper(), df.columns)
        stage_axes = self.parent_controller.configuration_controller.stage_axes
        cmp_header = [axis in df.columns for axis in [axis.upper() for axis in stage_axes]]
        if not all(cmp_header):
            messagebox.showwarning(
                title="Warning",
                message=f"The csv/yml file isn't right, it should contain {[axis.upper() for axis in stage_axes]}",
            )
            logger.info(f"The csv/yml file isn't right, it should contain {[axis.upper() for axis in stage_axes]}")
            return
        self.table.model.df = df
        self.table.currentrow = 0
        # reset index
        self.table.resetColors()
        self.table.redraw()
        self.table.tableChanged()
        self.show_verbose_info("loaded csv/yml file", filename)

    def export_positions(self):
        """Export the positions in the Multi-Position Acquisition Interface to a
        yml or csv file.

        This function opens a dialog that let the user input a filename
        Then, it will export positions to that yml/csv file
        """
        filename = filedialog.asksaveasfilename(
            defaultextension=".yml",
            filetypes=(("yml file", "*.yml"),("CSV file", "*.csv"), ("Text file", "*.txt")),
        )
        if not filename:
            return
        if filename.endswith(".yml"):
            file_directory, file_name_only = os.path.split(filename)
            data = [self.table.model.df.columns.tolist()] + self.table.model.df.values.tolist()
            save_yaml_file(
                file_directory=file_directory,
                content_dict=data,
                filename=file_name_only,
            )
            self.show_verbose_info("exporting yml file", filename)
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
        headers = list(self.table.model.df.columns)

        temp = []
        for col_name in headers:
            if col_name.lower() in position:
                temp.append(position[col_name.lower()])
            else:
                temp.append(np.nan)
        for col_name in position:
            if col_name.upper() not in headers:
                headers.append(col_name.upper())
                temp.append(position[col_name])

        # update the column headers
        self.table.model.df = self.table.model.df.reindex(columns=headers)

        # temp = list(map(lambda k: position[k], position))
        self.table.model.df = self.table.model.df.append(
            pd.DataFrame([temp], columns=headers), ignore_index=True
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
