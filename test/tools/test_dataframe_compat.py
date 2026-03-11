import pandas as pd

from navigate.tools.dataframe_compat import (
    append_dataframe_rows,
    insert_blank_row,
    sync_rowcolors_with_dataframe,
)


def test_append_dataframe_rows_aligns_columns_and_order():
    left = pd.DataFrame({"X": [1], "Y": [2]})
    right = pd.DataFrame({"Y": [20], "Z": [30], "X": [10]})

    result = append_dataframe_rows(left, right, ignore_index=True)

    assert list(result.columns) == ["X", "Y", "Z"]
    assert result.loc[0, "X"] == 1
    assert result.loc[0, "Y"] == 2
    assert pd.isna(result.loc[0, "Z"])
    assert result.iloc[1].tolist() == [10, 20, 30]


def test_append_dataframe_rows_handles_empty_inputs():
    left = pd.DataFrame(columns=["X", "Y"])
    right = pd.DataFrame({"X": [1], "Y": [2]})

    result = append_dataframe_rows(left, right)

    pd.testing.assert_frame_equal(result, right.reset_index(drop=True))


def test_insert_blank_row_clamps_index_and_preserves_columns():
    df = pd.DataFrame({"X": [1, 2], "Y": [3, 4]})

    result = insert_blank_row(df, 99)

    assert result.shape == (3, 2)
    assert result.iloc[2].isna().all()
    assert list(result.columns) == ["X", "Y"]


def test_sync_rowcolors_with_dataframe_aligns_index_and_columns():
    df = pd.DataFrame({"X": [1, 2], "Y": [3, 4]}, index=[10, 11])
    rowcolors = pd.DataFrame({"Y": ["a"], "Z": ["b"]}, index=[10])

    result = sync_rowcolors_with_dataframe(df, rowcolors)

    assert list(result.index) == [10, 11]
    assert list(result.columns) == ["X", "Y"]
    assert result.loc[10, "Y"] == "a"
    assert pd.isna(result.loc[10, "X"])
    assert pd.isna(result.loc[11, "X"])
