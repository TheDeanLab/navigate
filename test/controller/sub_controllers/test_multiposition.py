# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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
    table = controller.table

    df = pd.DataFrame(
        {"X": [1, 2], "Y": [3, 4], "Z": [5, 6], "THETA": [0, 0], "F": [0, 0]}
    )
    table.model.df = df
    table.model.df.to_csv = MagicMock()

    mock_asksave.return_value = "/tmp/output.csv"

    controller.export_positions()
    table.model.df.to_csv.assert_called_once_with("/tmp/output.csv", index=False)
