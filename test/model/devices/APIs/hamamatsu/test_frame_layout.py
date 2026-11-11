"""DCAM byte layouts are validated before any camera can write memory."""

import numpy as np
import pytest


@pytest.mark.parametrize(
    "pixel_type,dtype,itemsize", [(1, np.uint8, 1), (2, np.uint16, 2)]
)
def test_padded_rows_and_top_offset_preserve_pixels(pixel_type, dtype, itemsize):
    from navigate.model.devices.APIs.hamamatsu.frame_layout import DCAMFrameLayout

    layout = DCAMFrameLayout(
        3, 2, pixel_type, 4 * itemsize, 12 * itemsize, 2 * itemsize
    )
    buffer = np.full(layout.frame_bytes, 0xAA, dtype=np.uint8)
    view = layout.view(buffer)
    pattern = np.array([[0, 1, 255], [4, 5, 6]], dtype=dtype)
    view[:] = pattern
    assert view.dtype == dtype
    assert view.strides == (4 * itemsize, itemsize)
    np.testing.assert_array_equal(view, pattern)
    assert np.all(buffer[: 2 * itemsize] == 0xAA)


@pytest.mark.parametrize(
    "values",
    [
        (3, 2, 3, 6, 12, 0),
        (3, 2, 5, 6, 12, 0),
        (3, 2, 2, 5, 12, 0),
        (3, 2, 2, 6, 11, 0),
        (3, 2, 2, 6, 12, 1),
        (0, 2, 2, 6, 12, 0),
        (3, 2, 2, -6, 12, 0),
        (3, 2, 2, 6, 12, -1),
        (3, 2, 2, 6.5, 13, 0),
    ],
)
def test_unsupported_or_inconsistent_layout_is_rejected(values):
    from navigate.model.devices.APIs.hamamatsu.frame_layout import DCAMFrameLayout

    with pytest.raises(ValueError):
        DCAMFrameLayout(*values)
