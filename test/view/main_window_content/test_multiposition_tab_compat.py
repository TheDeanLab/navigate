from types import SimpleNamespace
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
