"""Image consumers preserve native camera precision and byte layout."""

import numpy as np
import pytest

from navigate.controller.sub_controllers.camera_view import (
    SpooledImageLoader,
    MIPViewController,
)


@pytest.mark.parametrize(
    "dtype,values",
    [
        (np.uint8, [0, 1, 127, 128, 254, 255]),
        (np.uint16, [0, 1, 255, 256, 4095, 65535]),
    ],
)
def test_spooled_frames_round_trip_native_dtype(tmp_path, monkeypatch, dtype, values):
    monkeypatch.setattr(
        SpooledImageLoader, "get_default_directory", staticmethod(lambda: str(tmp_path))
    )
    loader = SpooledImageLoader(channels=2, size_y=2, size_x=3)
    frame = np.array(values, dtype=dtype).reshape(2, 3)
    loader.save_image(frame, 0, 0)
    loader.save_image(frame[:, ::-1], 1, 1)
    for channel, index, expected in [(0, 0, frame), (1, 1, frame[:, ::-1])]:
        restored = loader.load_image(channel, index)
        assert restored.dtype == dtype
        np.testing.assert_array_equal(restored, expected)


def test_spooled_stack_rejects_dtype_change(tmp_path, monkeypatch):
    monkeypatch.setattr(
        SpooledImageLoader, "get_default_directory", staticmethod(lambda: str(tmp_path))
    )
    loader = SpooledImageLoader(1, 2, 3)
    loader.save_image(np.ones((2, 3), np.uint8), 0, 0)
    with pytest.raises(ValueError, match="dtype"):
        loader.save_image(np.ones((2, 3), np.uint16), 0, 1)


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16])
def test_mip_buffers_follow_incoming_dtype(dtype):
    controller = MIPViewController.__new__(MIPViewController)
    controller.number_of_channels = 1
    controller.number_of_slices = 2
    frame = np.arange(6, dtype=dtype).reshape(2, 3)
    actual = controller._ensure_mip_buffers_compatible(frame)
    assert actual.dtype == dtype
    for array in (
        controller.xy_mip,
        controller.zy_mip,
        controller.zx_mip,
        controller._zy_reduce_buf,
        controller._zx_reduce_buf,
    ):
        assert array.dtype == dtype
