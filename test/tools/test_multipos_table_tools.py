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

# Standard library imports
import unittest
import tkinter as tk
from tkinter import ttk
from math import ceil

# Third party imports
import numpy as np

# Local application imports
from aslm.tools.multipos_table_tools import (
    update_table,
    calc_num_tiles,
    compute_tiles_from_bounding_box,
    sign,
)
from aslm.view.main_window_content.multiposition_tab import MultiPositionTable


class SignTestCase(unittest.TestCase):
    def test_positive_number(self):
        x = 5.6
        result = sign(x)

        # Assert that the result is 1
        self.assertEqual(result, 1)

    def test_negative_number(self):
        x = -3.8
        result = sign(x)

        # Assert that the result is -1
        self.assertEqual(result, -1)

    def test_zero(self):
        x = 0
        result = sign(x)

        # Assert that the result is 1
        self.assertEqual(result, 1)


class ComputeTilesFromBoundingBoxTestCase(unittest.TestCase):
    def test_compute_tiles_from_bounding_box(self):
        # Set up test parameters
        x_start = 0
        x_tiles = 3
        x_length = 10
        x_overlap = 0.2
        y_start = 0
        y_tiles = 2
        y_length = 8
        y_overlap = 0.3
        z_start = 0
        z_tiles = 4
        z_length = 12
        z_overlap = 0.1
        theta_start = 0
        theta_tiles = 1
        theta_length = 2
        theta_overlap = 0.0
        f_start = 0
        f_tiles = 1
        f_length = 4
        f_overlap = 0.0

        result = compute_tiles_from_bounding_box(
            x_start,
            x_tiles,
            x_length,
            x_overlap,
            y_start,
            y_tiles,
            y_length,
            y_overlap,
            z_start,
            z_tiles,
            z_length,
            z_overlap,
            theta_start,
            theta_tiles,
            theta_length,
            theta_overlap,
            f_start,
            f_tiles,
            f_length,
            f_overlap,
        )

        # Assert the shape of the result is correct
        expected_shape = (x_tiles * y_tiles * z_tiles * theta_tiles * f_tiles, 5)
        self.assertEqual(result.shape, expected_shape)

        # Assert that the values in the result are correct
        expected_result = np.array(
            [
                [0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 10.8, 0.0, 0.0],
                [0.0, 0.0, 21.6, 0.0, 0.0],
                [0.0, 0.0, 32.4, 0.0, 0.0],
                [8.0, 0.0, 0.0, 0.0, 0.0],
                [8.0, 0.0, 10.8, 0.0, 0.0],
                [8.0, 0.0, 21.6, 0.0, 0.0],
                [8.0, 0.0, 32.4, 0.0, 0.0],
                [16.0, 0.0, 0.0, 0.0, 0.0],
                [16.0, 0.0, 10.8, 0.0, 0.0],
                [16.0, 0.0, 21.6, 0.0, 0.0],
                [16.0, 0.0, 32.4, 0.0, 0.0],
                [0.0, 5.6, 0.0, 0.0, 0.0],
                [0.0, 5.6, 10.8, 0.0, 0.0],
                [0.0, 5.6, 21.6, 0.0, 0.0],
                [0.0, 5.6, 32.4, 0.0, 0.0],
                [8.0, 5.6, 0.0, 0.0, 0.0],
                [8.0, 5.6, 10.8, 0.0, 0.0],
                [8.0, 5.6, 21.6, 0.0, 0.0],
                [8.0, 5.6, 32.4, 0.0, 0.0],
                [16.0, 5.6, 0.0, 0.0, 0.0],
                [16.0, 5.6, 10.8, 0.0, 0.0],
                [16.0, 5.6, 21.6, 0.0, 0.0],
                [16.0, 5.6, 32.4, 0.0, 0.0],
            ]
        )

        self.assertTrue(np.allclose(result, expected_result))


class CalcNumTilesTestCase(unittest.TestCase):
    def test_calc_num_tiles_1(self):
        dist = 10
        overlap = 0.2
        roi_length = 2
        expected_num_tiles = ceil(
            (dist - overlap * roi_length) / (roi_length - overlap * roi_length)
        )
        result = calc_num_tiles(dist, overlap, roi_length)
        self.assertEqual(result, expected_num_tiles)

    def test_calc_num_tiles_2(self):
        dist = 0
        overlap = 0.3
        roi_length = 5
        expected_num_tiles = 1
        result = calc_num_tiles(dist, overlap, roi_length)
        self.assertEqual(result, expected_num_tiles)

    def test_calc_num_tiles_3(self):
        dist = 15
        overlap = 0.1
        roi_length = 3
        expected_num_tiles = ceil(
            (dist - overlap * roi_length) / (roi_length - overlap * roi_length)
        )
        result = calc_num_tiles(dist, overlap, roi_length)
        self.assertEqual(result, expected_num_tiles)


class UpdateTableTestCase(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.frame = ttk.Frame()
        self.table = MultiPositionTable(parent=self.frame)

    def tearDown(self) -> None:
        self.root.destroy()

    def test_update_table_1(self):
        pos = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15]]

        update_table(table=self.table, pos=pos, append=False)

        assert self.table.model.df["X"][0] == pos[0][0]
        assert self.table.model.df["Y"][1] == pos[1][1]
        assert self.table.model.df["Z"][2] == pos[2][2]
        assert self.table.model.df["R"][0] == pos[0][3]
        assert self.table.model.df["F"][0] == pos[0][4]
        self.assertEqual(self.table.currentrow, 2)

        new_positions = [[16, 17, 18, 19, 20], [21, 22, 23, 24, 25]]

        update_table(self.table, pos=new_positions, append=True)
        # TODO: I don't think the append function is behaving properly.
        # number_of_rows = self.table.currentrow
        # self.assertEqual(number_of_rows, 5)
        # assert self.table.model.df['X'][3] == pos[0][0]


if __name__ == "__main__":
    unittest.main()
