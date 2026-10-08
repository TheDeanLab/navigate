from types import MethodType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd

from navigate.view.main_window_content import multiposition_tab
from navigate.view.main_window_content.multiposition_tab import MultiPositionTable


def test_update_rowcolors_uses_dataframe_compat_alignment():
    table = SimpleNamespace(
        model=SimpleNamespace(df=pd.DataFrame({"X": [1, 2]}, index=[10, 11])),
        rowcolors=pd.DataFrame({"Y": ["red"]}, index=[10]),
    )

    MultiPositionTable.update_rowcolors(table)

    assert list(table.rowcolors.index) == [10, 11]
    assert list(table.rowcolors.columns) == ["X"]
    assert table.rowcolors["X"].isna().all()


def test_add_row_inserts_blank_row_and_refreshes():
    table = SimpleNamespace(
        model=SimpleNamespace(df=pd.DataFrame({"X": [1.0, 2.0], "Y": [3.0, 4.0]})),
        currentrow=0,
        getSelectedRow=MagicMock(return_value=1),
        update_rowcolors=MagicMock(),
        redraw=MagicMock(),
        tableChanged=MagicMock(),
    )

    MultiPositionTable.addRow(table)

    assert table.model.df.shape == (3, 2)
    assert table.model.df.iloc[1].isna().all()
    assert table.currentrow == 1
    table.update_rowcolors.assert_called_once()
    table.redraw.assert_called_once()
    table.tableChanged.assert_called_once()


def test_bind_pandastable_image_master_injects_master():
    recorded_kwargs = {}

    def _photo_image_stub(*_args, **kwargs):
        recorded_kwargs.clear()
        recorded_kwargs.update(kwargs)
        return "img"

    with patch.object(
        multiposition_tab.pt_images.tk,
        "PhotoImage",
        side_effect=_photo_image_stub,
    ):
        local_master = object()
        with multiposition_tab._bind_pandastable_image_master(local_master):
            multiposition_tab.pt_images.tk.PhotoImage(file="icon.gif")
            assert recorded_kwargs["master"] is local_master

            explicit_master = object()
            multiposition_tab.pt_images.tk.PhotoImage(
                file="icon.gif", master=explicit_master
            )
            assert recorded_kwargs["master"] is explicit_master


def test_shift_click_seeds_selection_anchor_when_table_startrow_is_none():
    table = object.__new__(MultiPositionTable)
    table.startrow = None
    table.endrow = None
    table.startcol = None
    table.endcol = None
    table.currentrow = 1
    table.currentcol = 0
    table.rows = 4
    table.cols = 3
    table.multiplerowlist = []
    table.multiplecollist = []
    table.rowheader = SimpleNamespace(drawSelectedRows=MagicMock())
    table.get_row_clicked = MethodType(lambda self, event: 2, table)
    table.get_col_clicked = MethodType(lambda self, event: 1, table)
    table.drawMultipleRows = MagicMock()
    table.drawMultipleCells = MagicMock()
    table.delete = MagicMock()

    MultiPositionTable.handle_left_shift_click(table, SimpleNamespace())

    assert table.startrow == 1
    assert table.startcol == 0
    assert table.endrow == 2
    assert table.endcol == 1
    assert table.multiplerowlist == [1, 2]
    assert table.multiplecollist == [0, 1]
