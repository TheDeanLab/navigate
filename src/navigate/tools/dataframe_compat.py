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

"""Compatibility helpers for DataFrame operations used by pandastable flows.

The multiposition UI is shared across environments with different pandas versions.
Pandastable still uses APIs removed in pandas 2 (for example ``DataFrame.append``).
These adapters provide stable operations so callers can avoid version-specific
branches at each callsite.
"""

# Standard Library Imports
from __future__ import annotations
from collections.abc import Sequence

# Third Party Imports
import numpy as np
import pandas as pd


def append_dataframe_rows(
    left_df: pd.DataFrame, right_df: pd.DataFrame, ignore_index: bool = True
) -> pd.DataFrame:
    """Append rows while keeping a deterministic, pandas-2-safe column layout.

    Parameters
    ----------
    left_df : pd.DataFrame
        Existing dataframe.
    right_df : pd.DataFrame
        New rows to append.
    ignore_index : bool, optional
        Reset index after concatenation. Defaults to ``True``.

    Returns
    -------
    pd.DataFrame
        Concatenated dataframe with aligned columns.
    """
    ordered_columns = list(left_df.columns)
    ordered_columns.extend([col for col in right_df.columns if col not in left_df])

    if right_df.empty:
        return left_df.reindex(columns=ordered_columns).copy()
    if left_df.empty:
        result = right_df.reindex(columns=ordered_columns)
        return result.reset_index(drop=True) if ignore_index else result.copy()

    return pd.concat(
        [
            left_df.reindex(columns=ordered_columns),
            right_df.reindex(columns=ordered_columns),
        ],
        ignore_index=ignore_index,
    )


def insert_blank_row(df: pd.DataFrame, row_index: int | None) -> pd.DataFrame:
    """Insert a blank row at ``row_index`` using concat instead of append.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    row_index : int | None
        Zero-based insertion point. ``None`` appends at end.

    Returns
    -------
    pd.DataFrame
        Dataframe with an inserted NaN row and reset integer index.
    """
    if row_index is None:
        row_index = len(df)
    row_index = max(0, min(int(row_index), len(df)))

    blank = pd.DataFrame([{col: np.nan for col in df.columns}], columns=df.columns)
    return pd.concat(
        [df.iloc[:row_index], blank, df.iloc[row_index:]], ignore_index=True
    )


def sync_rowcolors_with_dataframe(
    df: pd.DataFrame, rowcolors: pd.DataFrame | None
) -> pd.DataFrame:
    """Align pandastable ``rowcolors`` shape/index with the current dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Current table dataframe.
    rowcolors : pd.DataFrame | None
        Existing rowcolors state.

    Returns
    -------
    pd.DataFrame
        Rowcolors dataframe aligned to ``df``.
    """
    rc = rowcolors.copy() if isinstance(rowcolors, pd.DataFrame) else pd.DataFrame()

    if len(df) == len(rc):
        rc = rc.set_index(df.index, drop=True)
    elif len(df) > len(rc):
        idx = df.index.difference(rc.index)
        rc = pd.concat([rc, pd.DataFrame(index=idx)], axis=0)
        rc = rc.reindex(df.index)
    else:
        idx = rc.index.difference(df.index)
        rc = rc.drop(index=idx)
        rc = rc.reindex(df.index)

    cols_to_drop = list(rc.columns.difference(df.columns))
    if cols_to_drop:
        rc = rc.drop(columns=cols_to_drop)

    cols_to_add: Sequence[str] = list(df.columns.difference(rc.columns))
    for col in cols_to_add:
        rc[col] = np.nan

    return rc.reindex(columns=list(df.columns))
