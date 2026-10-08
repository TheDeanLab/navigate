from types import SimpleNamespace

import pandas as pd
import pytest

from navigate.tools.multipos_table_tools import (
    calc_num_tiles,
    compute_tiles_from_bounding_box,
    update_rowcolors,
    write_to_csv_file,
)


def test_compute_tiles_from_bounding_box_supports_additional_axes():
    axes, tiles = compute_tiles_from_bounding_box(
        x_start=0,
        x_tiles=1,
        x_length=10,
        y_start=0,
        y_tiles=1,
        y_length=10,
        z_start=0,
        z_tiles=1,
        z_length=10,
        theta_start=0,
        theta_tiles=1,
        theta_length=1,
        f_start=0,
        f_tiles=1,
        f_length=2,
        overlap=0.5,
        phi_start=1,
        phi_tiles=3,
        phi_length=2,
        incomplete_start=99,  # ignored: missing *_tiles/*_length
    )

    assert axes == ["x", "y", "z", "theta", "f", "phi"]
    assert tiles.shape == (3, 6)
    assert list(tiles[:, 5]) == [1, 2, 3]


def test_compute_tiles_from_bounding_box_clamps_non_positive_additional_tiles():
    axes, tiles = compute_tiles_from_bounding_box(
        x_start=0,
        x_tiles=1,
        x_length=1,
        y_start=0,
        y_tiles=1,
        y_length=1,
        z_start=0,
        z_tiles=1,
        z_length=1,
        theta_start=0,
        theta_tiles=1,
        theta_length=1,
        f_start=0,
        f_tiles=1,
        f_length=1,
        overlap=0.2,
        lambda_start=7,
        lambda_tiles=0,
        lambda_length=5,
    )

    assert axes[-1] == "lambda"
    assert tiles.shape == (1, 6)
    assert tiles[0, 5] == 7


@pytest.mark.parametrize(
    "dist, overlap, roi_length",
    [
        (0, 0.5, 100),
        (10, 0.2, 0),
        (10, 1.0, 100),
    ],
)
def test_calc_num_tiles_boundary_conditions(dist, overlap, roi_length):
    assert calc_num_tiles(dist, overlap, roi_length) == 1


class _TableFallback:
    def __init__(self, df, rowcolors):
        self.model = SimpleNamespace(df=df)
        self.rowcolors = rowcolors

    def update_rowcolors(self):
        raise AttributeError("DataFrame object has no attribute append")


class _TableNative:
    def __init__(self):
        self.model = SimpleNamespace(df=pd.DataFrame({"A": [1]}))
        self.rowcolors = pd.DataFrame({"A": ["red"]})
        self.used_native = False

    def update_rowcolors(self):
        self.used_native = True


def test_update_rowcolors_prefers_native_method_when_available():
    table = _TableNative()
    original = table.rowcolors.copy()

    update_rowcolors(table)

    assert table.used_native is True
    pd.testing.assert_frame_equal(table.rowcolors, original)


def test_update_rowcolors_fallback_same_length_adjusts_columns_and_index():
    table = _TableFallback(
        df=pd.DataFrame({"A": [1, 2], "B": [3, 4]}, index=[10, 11]),
        rowcolors=pd.DataFrame({"B": ["red", "blue"], "C": ["x", "y"]}, index=[0, 1]),
    )

    update_rowcolors(table)

    assert list(table.rowcolors.index) == [10, 11]
    assert set(table.rowcolors.columns) == {"A", "B"}
    assert table.rowcolors["A"].isna().all()


def test_update_rowcolors_fallback_adds_missing_rows():
    table = _TableFallback(
        df=pd.DataFrame({"A": [1, 2, 3]}, index=[0, 1, 2]),
        rowcolors=pd.DataFrame({"A": ["red"]}, index=[0]),
    )

    update_rowcolors(table)

    assert list(table.rowcolors.index) == [0, 1, 2]


def test_update_rowcolors_fallback_drops_extra_rows():
    table = _TableFallback(
        df=pd.DataFrame({"A": [1]}, index=[5]),
        rowcolors=pd.DataFrame({"A": ["red", "blue"]}, index=[5, 6]),
    )

    update_rowcolors(table)

    assert list(table.rowcolors.index) == [5]


def test_update_rowcolors_re_raises_unrelated_attribute_errors():
    class _TableBadAttribute:
        def __init__(self):
            self.model = SimpleNamespace(df=pd.DataFrame({"A": [1]}))
            self.rowcolors = pd.DataFrame({"A": ["red"]})

        def update_rowcolors(self):
            raise AttributeError("different attribute error")

    with pytest.raises(AttributeError):
        update_rowcolors(_TableBadAttribute())


def test_update_rowcolors_fallback_on_drop_type_error():
    class _TableDropTypeError:
        def __init__(self):
            self.model = SimpleNamespace(df=pd.DataFrame({"A": [1, 2]}, index=[0, 1]))
            self.rowcolors = pd.DataFrame({"A": ["red"]}, index=[0])

        def update_rowcolors(self):
            raise TypeError("drop() takes from 1 to 2 positional arguments")

    table = _TableDropTypeError()
    update_rowcolors(table)

    assert list(table.rowcolors.index) == [0, 1]
    assert list(table.rowcolors.columns) == ["A"]


def test_write_to_csv_file_success_and_failure(tmp_path):
    success_file = tmp_path / "positions.csv"
    positions = [[1, 2, 3, 4, 5], [10, 20, 30, 40, 50]]

    assert write_to_csv_file(positions, str(success_file)) is True
    content = success_file.read_text().strip().splitlines()
    assert content[0] == "X,Y,Z,THETA,F"
    assert content[1] == "1,2,3,4,5"
    assert content[2] == "10,20,30,40,50"

    missing_parent = tmp_path / "does_not_exist" / "positions.csv"
    assert write_to_csv_file(positions, str(missing_parent)) is False
