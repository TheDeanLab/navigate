import numpy as np
import pytest


def test_data_source_mode():
    from navigate.model.data_sources.data_source import DataSource

    ds = DataSource()

    # set read and write

    with pytest.raises(NotImplementedError):
        ds.mode = "r"
        assert ds.mode == "r"

    ds.mode = "w"
    assert ds.mode == "w"

    # set unknown mode, default to read
    with pytest.raises(NotImplementedError):
        ds.mode = "goblin"
        assert ds.mode == "r"


def test_data_source_cztp_indices():
    import itertools
    from navigate.model.data_sources.data_source import DataSource

    MAX = 25

    ds = DataSource()

    ds.shape_c = np.random.randint(1, MAX)
    ds.shape_z = 1
    ds.shape_t = np.random.randint(1, MAX)
    ds.positions = np.random.randint(1, MAX)
    n_inds = ds.shape_c * ds.shape_z * ds.shape_t * ds.positions

    print(f"n_inds : {n_inds}")

    cztp_inds = itertools.product(
        range(ds.positions), range(ds.shape_z), range(ds.shape_t), range(ds.shape_c)
    )

    for i, inds in zip(range(n_inds), cztp_inds):
        c, z, t, p = ds._cztp_indices(i, False)
        pt, zt, tt, ct = inds
        assert c == ct
        assert z == zt
        assert t == tt
        assert p == pt

    print(
        f"Shape (XYCZTP): {ds.shape} {ds.positions} "
        f"Final (CZTP): {ds._cztp_indices(n_inds-1, False)}"
    )

    ds.shape_z = np.random.randint(2, MAX)
    n_inds = ds.shape_c * ds.shape_z * ds.shape_t * ds.positions

    cztp_inds = itertools.product(
        range(ds.positions), range(ds.shape_t), range(ds.shape_z), range(ds.shape_c)
    )

    for i, inds in zip(range(n_inds), cztp_inds):
        c, z, t, p = ds._cztp_indices(i, False)
        pt, tt, zt, ct = inds
        assert c == ct
        assert z == zt
        assert t == tt
        assert p == pt

    print(
        f"Shape (XYCZTP): {ds.shape} {ds.positions} "
        f"Final (CZTP): {ds._cztp_indices(n_inds-1, False)}"
    )

    cztp_inds = itertools.product(
        range(ds.positions), range(ds.shape_t), range(ds.shape_c), range(ds.shape_z)
    )

    for i, inds in zip(range(n_inds), cztp_inds):
        c, z, t, p = ds._cztp_indices(i, True)
        pt, tt, ct, zt = inds
        assert c == ct
        assert z == zt
        assert t == tt
        assert p == pt

    print(
        f"Shape (XYCZTP): {ds.shape} {ds.positions} "
        f"Final (CZTP): {ds._cztp_indices(n_inds-1, False)}"
    )

    # assert False
