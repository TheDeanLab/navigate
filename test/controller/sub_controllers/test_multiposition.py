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
#

# Standard library imports

# Third party imports
import pytest
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

# Local application imports
from navigate.controller.sub_controllers.multiposition import MultiPositionController


@pytest.fixture
def multiposition_controller(dummy_controller):
    # Create a copy/clone of the dummy_controller to avoid side effects
    isolated_controller = MagicMock()
    isolated_controller.configuration = dummy_controller.configuration

    # Create a mock pt attribute for the multiposition_tab
    isolated_controller.view.settings.multiposition_tab.pt = MagicMock()
    isolated_controller.view.settings.multiposition_tab.pt.model = MagicMock()
    isolated_controller.view.settings.multiposition_tab.pt.model.df = pd.DataFrame()

    # Add other required mock attributes and methods
    isolated_controller.view.settings.multiposition_tab.pt.redraw = MagicMock()
    isolated_controller.view.settings.multiposition_tab.pt.tableChanged = MagicMock()
    isolated_controller.view.settings.multiposition_tab.pt.resetColors = MagicMock()
    isolated_controller.view.settings.multiposition_tab.pt.update_rowcolors = (
        MagicMock()
    )

    # Mock the master and tiling buttons
    isolated_controller.view.settings.multiposition_tab.master = MagicMock()
    isolated_controller.view.settings.multiposition_tab.master.tiling_buttons = (
        MagicMock()
    )
    isolated_controller.view.settings.multiposition_tab.master.tiling_buttons.buttons = {
        "tiling": MagicMock(),
        "save_data": MagicMock(),
        "load_data": MagicMock(),
        "eliminate_tiles": MagicMock(),
    }

    # This is the important part - configure the stage axes
    isolated_controller.configuration_controller = MagicMock()
    isolated_controller.configuration_controller.stage_axes = [
        "x",
        "y",
        "z",
        "theta",
        "f",
    ]

    return MultiPositionController(
        isolated_controller.view.settings.multiposition_tab, isolated_controller
    )


@patch("navigate.controller.sub_controllers.multiposition.filedialog.askopenfilenames")
@patch("navigate.controller.sub_controllers.multiposition.yaml.safe_load")
@patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="dummy content")
def test_load_positions_yaml(
    mock_file, mock_safe_load, mock_askopen, multiposition_controller
):
    """Test loading positions from YAML"""
    controller = multiposition_controller
    table = controller.table

    mock_askopen.return_value = ("dummy_file.yml",)
    mock_safe_load.return_value = [
        ["X", "Y", "Z", "THETA", "F"],
        [0, 0, 0, 0, 0],
        [100, 200, 300, 400, 500],
    ]

    controller.load_positions()

    mock_file.assert_called_once_with("dummy_file.yml", "r")

    expected = pd.DataFrame(
        [[0, 0, 0, 0, 0], [100, 200, 300, 400, 500]],
        columns=["X", "Y", "Z", "THETA", "F"],
    )
    pd.testing.assert_frame_equal(table.model.df, expected)


@patch("navigate.controller.sub_controllers.multiposition.filedialog.askopenfilenames")
@patch("navigate.controller.sub_controllers.multiposition.pd.read_csv")
def test_load_positions_csv(mock_read_csv, mock_askopen, multiposition_controller):
    """Test loading positions from CSV"""
    controller = multiposition_controller
    table = controller.table

    mock_askopen.return_value = ("dummy_file.csv",)
    mock_read_csv.return_value = pd.DataFrame(
        {"X": [1, 2], "Y": [3, 4], "Z": [5, 6], "THETA": [0, 0], "F": [0, 0]}
    )

    controller.load_positions()

    expected = pd.DataFrame(
        {"X": [1, 2], "Y": [3, 4], "Z": [5, 6], "THETA": [0, 0], "F": [0, 0]}
    )
    pd.testing.assert_frame_equal(table.model.df, expected)


@patch("navigate.controller.sub_controllers.multiposition.filedialog.asksaveasfilename")
@patch("navigate.controller.sub_controllers.multiposition.save_yaml_file")
def test_export_positions_yaml(mock_save_yaml, mock_asksave, multiposition_controller):
    """Test exporting positions to YAML"""
    controller = multiposition_controller
    table = controller.table

    table.model.df = pd.DataFrame(
        {"X": [1, 2], "Y": [3, 4], "Z": [5, 6], "THETA": [0, 0], "F": [0, 0]}
    )
    mock_asksave.return_value = "/tmp/output.yml"

    controller.export_positions()
    mock_save_yaml.assert_called_once()


@patch("navigate.controller.sub_controllers.multiposition.filedialog.asksaveasfilename")
def test_export_positions_csv(mock_asksave, multiposition_controller):
    """Test exporting positions to CSV"""
    controller = multiposition_controller
    export_df = MagicMock()
    controller._get_full_positions_df = MagicMock(return_value=export_df)

    mock_asksave.return_value = "/tmp/output.csv"

    controller.export_positions()
    export_df.to_csv.assert_called_once_with("/tmp/output.csv", index=False)


@patch("navigate.controller.sub_controllers.multiposition.filedialog.askopenfilenames")
def test_load_positions_empty_file_selection(mock_askopen, multiposition_controller):
    controller = multiposition_controller
    mock_askopen.return_value = ()

    controller.load_positions()

    assert controller.table.model.df.empty


@patch("navigate.controller.sub_controllers.multiposition.filedialog.askopenfilenames")
@patch("navigate.controller.sub_controllers.multiposition.pd.read_csv")
@patch("navigate.controller.sub_controllers.multiposition.messagebox.showwarning")
def test_load_positions_invalid_header_warns_and_returns(
    mock_showwarning, mock_read_csv, mock_askopen, multiposition_controller
):
    controller = multiposition_controller
    mock_askopen.return_value = ("dummy_file.csv",)
    mock_read_csv.return_value = pd.DataFrame({"BAD": [1], "COLUMNS": [2]})

    controller.load_positions()

    mock_showwarning.assert_called_once()
    assert controller.table.model.df.empty


@patch("navigate.controller.sub_controllers.multiposition.filedialog.asksaveasfilename")
def test_export_positions_empty_filename_returns(mock_asksave, multiposition_controller):
    controller = multiposition_controller
    controller.table.model.df = pd.DataFrame({"X": [1]})
    controller.table.model.df.to_csv = MagicMock()
    mock_asksave.return_value = ""

    controller.export_positions()

    controller.table.model.df.to_csv.assert_not_called()


def test_set_positions_empty_defaults_to_stage_position(multiposition_controller):
    controller = multiposition_controller
    stage_axes = controller.parent_controller.configuration_controller.stage_axes
    stage_params = controller.parent_controller.configuration["experiment"]["StageParameters"]

    stage_params["x"] = 11.0
    stage_params["y"] = 22.0
    stage_params["z"] = 33.0
    stage_params["theta"] = 44.0
    stage_params["f"] = 55.0

    controller.set_positions([])

    assert list(controller.table.model.df.columns) == [axis.upper() for axis in stage_axes]
    assert controller.table.model.df.iloc[0].tolist() == [
        stage_params[axis] for axis in stage_axes
    ]


def test_set_positions_partial_header_and_extra_column(multiposition_controller):
    controller = multiposition_controller
    positions = [["X"], [1, 2, 3, 4, 5, 6]]

    controller.set_positions(positions)

    assert list(controller.table.model.df.columns) == [
        "X",
        "Y",
        "Z",
        "THETA",
        "F",
        "COL-0",
    ]
    assert controller.table.model.df.iloc[0].tolist() == [1, 2, 3, 4, 5, 6]


@patch("navigate.controller.sub_controllers.multiposition.messagebox.showwarning")
def test_handle_double_click_invalid_position_shows_warning(
    mock_showwarning, multiposition_controller
):
    controller = multiposition_controller
    controller.parent_controller.execute = MagicMock()
    controller.table.model.df = pd.DataFrame(
        {"X": [1.0], "Y": [float("nan")], "Z": [3.0], "THETA": [4.0], "F": [5.0]}
    )
    controller.table.get_row_clicked = MagicMock(return_value=0)

    controller.handle_double_click(MagicMock())

    mock_showwarning.assert_called_once()
    controller.parent_controller.execute.assert_not_called()


def test_handle_double_click_out_of_range_returns(multiposition_controller):
    controller = multiposition_controller
    controller.parent_controller.execute = MagicMock()
    controller.table.model.df = pd.DataFrame(
        {"X": [1.0], "Y": [2.0], "Z": [3.0], "THETA": [4.0], "F": [5.0]}
    )
    controller.table.get_row_clicked = MagicMock(return_value=5)

    controller.handle_double_click(MagicMock())

    controller.parent_controller.execute.assert_not_called()


def test_handle_double_click_valid_position_executes_move(multiposition_controller):
    controller = multiposition_controller
    controller.parent_controller.execute = MagicMock()
    controller.table.model.df = pd.DataFrame(
        {"X": [1.0], "Y": [2.0], "Z": [3.0], "THETA": [4.0], "F": [5.0]}
    )
    controller.table.get_row_clicked = MagicMock(return_value=0)

    controller.handle_double_click(MagicMock())

    controller.parent_controller.execute.assert_called_once_with(
        "move_stage_and_update_info",
        {"x": 1.0, "y": 2.0, "z": 3.0, "theta": 4.0, "f": 5.0},
    )


def test_move_to_position_builds_event_and_delegates(multiposition_controller):
    controller = multiposition_controller
    controller.handle_double_click = MagicMock()

    controller.move_to_position()

    controller.handle_double_click.assert_called_once()
    event = controller.handle_double_click.call_args.args[0]
    assert event.x == 0
    assert event.y == 0


@patch("navigate.controller.sub_controllers.multiposition.update_rowcolors")
def test_insert_row_func_updates_rowcolors(mock_update_rowcolors, multiposition_controller):
    controller = multiposition_controller
    controller.table.currentrow = 3
    controller.table.model.addRow = MagicMock()

    controller.insert_row_func()

    controller.table.model.addRow.assert_called_once_with(3)
    mock_update_rowcolors.assert_called_once_with(controller.table)
    controller.table.redraw.assert_called()
    controller.table.tableChanged.assert_called()


def test_add_stage_position_uses_parent_stage_position(multiposition_controller):
    controller = multiposition_controller
    stage_pos = {"x": 1, "y": 2, "z": 3, "theta": 4, "f": 5}
    controller.parent_controller.execute = MagicMock(return_value=stage_pos)
    controller.append_position = MagicMock()

    controller.add_stage_position()

    controller.parent_controller.execute.assert_called_once_with("get_stage_position")
    controller.append_position.assert_called_once_with(stage_pos)


@patch("navigate.controller.sub_controllers.multiposition.update_rowcolors")
def test_append_position_adds_columns_and_row(mock_update_rowcolors, multiposition_controller):
    controller = multiposition_controller
    controller.table.model.df = pd.DataFrame(columns=["X", "Y"])

    controller.append_position({"x": 1.0, "y": 2.0, "z": 3.0})

    assert list(controller.table.model.df.columns) == ["X", "Y", "Z"]
    assert controller.table.model.df.iloc[0].tolist() == [1.0, 2.0, 3.0]
    assert controller.table.currentrow == 0
    mock_update_rowcolors.assert_called_once_with(controller.table)


def test_remove_positions_filters_using_flags(multiposition_controller):
    controller = multiposition_controller
    controller.get_positions = MagicMock(
        return_value=[["X", "Y"], [1, 2], [3, 4], [5, 6]]
    )
    controller.set_positions = MagicMock()

    controller.remove_positions([True, False, True])

    controller.set_positions.assert_called_once_with([["X", "Y"], [3, 4], [5, 6]])


def test_custom_events_maps_remove_positions(multiposition_controller):
    controller = multiposition_controller
    events = controller.custom_events

    assert "remove_positions" in events
    assert events["remove_positions"] == controller.remove_positions
