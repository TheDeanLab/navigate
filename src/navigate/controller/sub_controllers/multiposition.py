# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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
import tkinter as tk
from tkinter import filedialog, messagebox
import logging
import warnings
from typing import Callable

# Third Party Imports
import pandas as pd
import numpy as np
import os
import yaml

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.tools.dataframe_compat import append_dataframe_rows, insert_blank_row
from navigate.tools.file_functions import save_yaml_file
from navigate.tools.multipos_table_tools import update_rowcolors


# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class MultiPositionController(GUIController):
    """Controller for the Multi-Position Acquisition Interface."""

    _hidden_position_columns = ("X_PIXEL", "Y_PIXEL")

    def __init__(self, view, parent_controller=None) -> None:
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
        self.table.loadCSV = self.load_positions
        self.table.exportCSV = self.export_positions
        self.table.insertRow = self.insert_row_func
        self.table.addStagePosition = self.add_stage_position
        self._hidden_position_df = pd.DataFrame(columns=self._hidden_position_columns)

        # Traces
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

    def eliminate_tiles(self) -> None:
        """Eliminate tiles that do not contain tissue."""
        self.parent_controller.execute("eliminate_tiles")

    def _refresh_table_view(self) -> None:
        """Redraw table while filtering known pandastable/pandas deprecation noise."""
        if hasattr(self.table, "apply_theme"):
            self.table.apply_theme(redraw=False)
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r".*convert_dtype parameter is deprecated.*",
                category=FutureWarning,
            )
            self.table.redraw()
            self.table.tableChanged()

    @staticmethod
    def _is_valid_numeric(value: object) -> bool:
        """Return True if value is a finite numeric scalar."""
        return isinstance(value, (int, float, np.integer, np.floating)) and not pd.isna(
            value
        )

    def _normalize_dataframe_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize known column aliases and case."""
        normalized_df = df.copy()
        normalized_df.columns = [str(col).upper() for col in normalized_df.columns]
        stage_axes = self.parent_controller.configuration_controller.stage_axes
        if "theta" in stage_axes:
            if "THETA" not in normalized_df.columns and "R" in normalized_df.columns:
                normalized_df = normalized_df.rename(columns={"R": "THETA"})
            elif "THETA" in normalized_df.columns and "R" in normalized_df.columns:
                normalized_df = normalized_df.drop(columns=["R"])
        return normalized_df

    def _set_dataframe(self, df: pd.DataFrame) -> None:
        """Set visible table data while preserving hidden YAML-only columns."""
        normalized_df = self._normalize_dataframe_columns(df)
        hidden_cols = [
            col for col in self._hidden_position_columns if col in normalized_df.columns
        ]
        self.table.model.df = normalized_df.drop(columns=hidden_cols, errors="ignore")
        self._hidden_position_df = normalized_df[hidden_cols].copy()
        self._sync_hidden_position_df()

    def _sync_hidden_position_df(self) -> None:
        """Keep hidden metadata rows aligned with visible table rows."""
        table_index = self.table.model.df.index
        self._hidden_position_df = self._hidden_position_df.reindex(table_index)
        for col in self._hidden_position_columns:
            if col not in self._hidden_position_df.columns:
                self._hidden_position_df[col] = np.nan
        self._hidden_position_df = self._hidden_position_df[
            list(self._hidden_position_columns)
        ]

    def clear_hidden_position_columns(self) -> None:
        """Clear hidden metadata columns while preserving row alignment."""
        self._hidden_position_df = pd.DataFrame(index=self.table.model.df.index)
        self._sync_hidden_position_df()

    def _get_full_positions_df(self) -> pd.DataFrame:
        """Return visible table data merged with hidden metadata columns."""
        visible_df = self._normalize_dataframe_columns(self.table.model.df)
        self._sync_hidden_position_df()
        hidden_cols = [
            col
            for col in self._hidden_position_columns
            if self._hidden_position_df[col].notna().any()
        ]
        if not hidden_cols:
            return visible_df
        return pd.concat([visible_df, self._hidden_position_df[hidden_cols]], axis=1)

    def set_positions(self, positions: list[list[float]]) -> None:
        """Set positions to multi-position's table

        Parameters
        ----------
        positions : list[list[float]]
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
        first_row = [str(val).upper() for val in positions[0]]
        cmp_header = [axis.upper() in first_row for axis in stage_axes]
        # if positions[0] contains stage-axis headers, then consider it as headers
        # else add headers to the table
        if not all(cmp_header):
            # if the first row contains some headers, update the headers
            if any(cmp_header):
                headers = list(first_row)
                for i, flag in enumerate(cmp_header):
                    if not flag:
                        headers.append(stage_axes[i].upper())
                start_index = 1
            else:
                headers = [axis.upper() for axis in stage_axes]
                start_index = 0
        else:
            headers = list(first_row)
            start_index = 1
        if start_index >= len(positions):
            self._set_dataframe(pd.DataFrame(columns=headers))
            self.table.currentrow = 0
            self._refresh_table_view()
            return
        # if there are some missing headers, add them
        if len(headers) < len(positions[start_index]):
            headers = headers + [
                "col-" + str(i)
                for i in range(len(positions[start_index]) - len(headers))
            ]
        for i, name in enumerate(headers):
            data[name] = list(
                pos[i] if i < len(pos) else np.nan for pos in positions[start_index:]
            )
        self._set_dataframe(pd.DataFrame(data))
        self.table.currentrow = 0
        self._refresh_table_view()

    def get_positions(self) -> list[list[float]]:
        """Return all positions from the Multi-Position Acquisition Interface.

        Returns
        -------
        positions : list[list[float]]
            positions in the format of [[x, y, z, theta, f], ]
        """
        df = self._get_full_positions_df()
        positions = [list(df.columns)]
        stage_axes = self.parent_controller.configuration_controller.stage_axes
        required_headers = [axis.upper() for axis in stage_axes]
        missing_headers = [
            axis for axis in required_headers if axis not in positions[0]
        ]
        if missing_headers:
            logger.warning(
                "Missing required stage headers in multiposition table: %s",
                missing_headers,
            )
            return positions
        axes_index = [positions[0].index(axis) for axis in required_headers]
        rows = df.shape[0]
        for i in range(rows):
            temp = list(df.iloc[i])
            if all(self._is_valid_numeric(temp[axis_idx]) for axis_idx in axes_index):
                positions.append(temp)
        return positions

    def handle_double_click(self, event: tk.Event) -> None:
        """Move to a position within the Multi-Position Acquisition Interface.

        When double-clicked the row head, it will call the parent/central controller
        to move stage and update stage view

        Parameters
        ----------
        event : tk.Event
            The event that triggers the function
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
        try:
            axes_index = [
                df.columns.get_loc(axis)
                for axis in [axis.upper() for axis in stage_axes]
            ]
        except KeyError:
            messagebox.showwarning(
                title="Warning",
                message="The selected position is invalid, can't go to this position!",
            )
            logger.info("position is invalid: missing one or more stage axes")
            return
        # validate position
        # we currently only move to a position doesn't contain nan
        if not all(self._is_valid_numeric(temp[axis_idx]) for axis_idx in axes_index):
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

    def get_position_num(self) -> int:
        """Return the number of positions in the Multi-Position Acquisition Interface.

        Returns
        -------
        int
            number of positions
        """
        return self.table.model.df.shape[0]

    def load_positions(self) -> None:
        """Load a yml or csv file.

        The valid yml/csv file should contain the line of headers: stage axes
        """
        filename = filedialog.askopenfilenames(
            defaultextension=".yml",
            filetypes=(
                ("yml file", "*.yml"),
                ("CSV files", "*.csv"),
                ("Text files", "*.txt"),
            ),
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
        df = self._normalize_dataframe_columns(df)
        stage_axes = self.parent_controller.configuration_controller.stage_axes
        cmp_header = [
            axis in df.columns for axis in [axis.upper() for axis in stage_axes]
        ]
        if not all(cmp_header):
            message = (
                f"The CSV/YAML file isn't correct. \n"
                f"It should contain {[axis.upper() for axis in stage_axes]}"
            )
            messagebox.showwarning(title="Warning", message=message)
            logger.info(message)
            return
        self._set_dataframe(df)
        self.table.currentrow = 0

        # reset index
        self.table.resetColors()
        self._refresh_table_view()

    def export_positions(self) -> None:
        """Export the positions in the Multi-Position Acquisition Interface to a
        yml or csv file.

        This function opens a dialog that let the user input a filename
        Then, it will export positions to that yml/csv file
        """
        filename = filedialog.asksaveasfilename(
            defaultextension=".yml",
            filetypes=(
                ("yml file", "*.yml"),
                ("CSV file", "*.csv"),
                ("Text file", "*.txt"),
            ),
        )

        if not filename:
            return

        if filename.endswith(".yml"):
            file_directory, file_name_only = os.path.split(filename)
            export_df = self._get_full_positions_df()
            data = [export_df.columns.tolist()] + export_df.values.tolist()
            save_yaml_file(
                file_directory=file_directory,
                content_dict=data,
                filename=file_name_only,
            )
            return

        export_df = self._get_full_positions_df()
        export_df.to_csv(filename, index=False)

    def move_to_position(self) -> None:
        """Move to a position within the Multi-Position Acquisition Interface."""
        event = type("MyEvent", (object,), {})
        event.x, event.y = 0, 0
        self.handle_double_click(event)

    def insert_row_func(self) -> None:
        """Insert a row in the Multi-Position Acquisition Interface."""
        self.table.model.df = insert_blank_row(
            self.table.model.df, self.table.currentrow
        )
        if self.table.model.df.shape[0] == 0:
            self.table.currentrow = 0
        elif self.table.currentrow is None:
            self.table.currentrow = self.table.model.df.shape[0] - 1
        else:
            self.table.currentrow = max(
                0, min(int(self.table.currentrow), self.table.model.df.shape[0] - 1)
            )
        self._sync_hidden_position_df()
        update_rowcolors(self.table)
        self._refresh_table_view()

    def add_stage_position(self) -> None:
        """Add the current stage position to the Multi-Position Acquisition Interface.

        This function will get the stage's current position and add it to position list
        """
        position = self.parent_controller.execute("get_stage_position")
        self.append_position(position)

    def append_position(self, position: dict) -> None:
        """Append a position to the Multi-Position Acquisition Interface.

        Parameters
        ----------
        position : dict
            position in the format of {axis: value}
        """
        headers = list(self.table.model.df.columns)
        normalized_position = {
            str(key).lower(): value for key, value in position.items()
        }
        hidden_values = {}

        temp = []
        for col_name in headers:
            if col_name.lower() in normalized_position:
                temp.append(normalized_position[col_name.lower()])
            else:
                temp.append(np.nan)
        for col_name in normalized_position:
            column_name = col_name.upper()
            if column_name in self._hidden_position_columns:
                hidden_values[column_name] = normalized_position[col_name]
                continue
            if column_name not in headers:
                headers.append(column_name)
                temp.append(normalized_position[col_name])

        # temp = list(map(lambda k: position[k], position))
        self.table.model.df = append_dataframe_rows(
            self.table.model.df,
            pd.DataFrame([temp], columns=headers),
            ignore_index=True,
        )
        self.table.currentrow = self.table.model.df.shape[0] - 1
        self._sync_hidden_position_df()
        row_index = self.table.model.df.index[self.table.currentrow]
        for col_name, value in hidden_values.items():
            self._hidden_position_df.at[row_index, col_name] = value
        update_rowcolors(self.table)
        self._refresh_table_view()

    def remove_positions(self, position_flag_list: list[bool]) -> None:
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
    def custom_events(self) -> dict[str, Callable]:
        """Return custom events for the Multi-Position Controller.

        Returns
        -------
        dict[str, Callable]
            Dictionary of custom events with their corresponding functions.
        """
        return {"remove_positions": self.remove_positions}
