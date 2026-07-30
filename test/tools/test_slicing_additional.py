import pytest

from navigate.tools.slicing import ensure_iter, ensure_slice, key_len


def test_key_len_raises_for_empty_sequences():
    with pytest.raises(IndexError, match="Too few indices."):
        key_len(())


def test_ensure_iter_handles_ellipsis_full_slice_and_clipping():
    assert list(ensure_iter((slice(None), Ellipsis), 0, 3)) == [0, 1, 2]
    assert list(ensure_iter(slice(5, 20, 2), 0, 6)) == [5]
    assert list(ensure_iter(slice(10, 20, 2), 0, 6)) == []
    assert list(ensure_iter(10, 0, 5)) == [4]


def test_ensure_slice_handles_ellipsis_and_default_slice():
    assert ensure_slice((slice(1, 3), Ellipsis), 0) == slice(1, 3, None)
    assert ensure_slice((slice(1, 3), Ellipsis), 1) == slice(None, None, None)
