"""Verify layout conversion at the native attach/transfer boundary."""

import ctypes

import numpy as np
import pytest

from navigate.model.devices.camera.format import CameraImageFormat
from test.model.devices.APIs.hamamatsu.test_hamamatsu_platform import load_api


@pytest.fixture
def capture(monkeypatch):
    api, _ = load_api(monkeypatch)
    camera = api.DCAM.__new__(api.DCAM)
    camera._DCAM__hdcam = ctypes.c_void_p(123)
    camera._DCAM__hdcamwait = 0
    props = {
        "image_width": 3,
        "image_height": 2,
        "buffer_pixel_type": 2,
        "buffer_row_bytes": 8,
        "buffer_frame_bytes": 20,
        "buffer_top_offset": 2,
    }
    camera.get_property_value = lambda name: props[name]
    addresses = []

    def attach(handle, param):
        addresses.extend(param._obj.buffer[i] for i in range(param._obj.buffercount))
        return 1

    monkeypatch.setattr(api, "dcambuf_attach", attach)
    monkeypatch.setattr(api, "dcamcap_start", lambda *args: 1)
    monkeypatch.setattr(api, "dcamcap_stop", lambda *args: 1)
    monkeypatch.setattr(api, "dcambuf_release", lambda *args: 1)
    monkeypatch.setattr(api, "dcamwait_start", lambda *args: 1)

    def transfer(handle, param):
        param._obj.nNewestFrameIndex = 0
        param._obj.nFrameCount = 1
        return 1

    monkeypatch.setattr(api, "dcamcap_transferinfo", transfer)
    yield camera, props, addresses
    camera._DCAM__hdcam = 0


@pytest.mark.parametrize("bits,native_type", [(8, 2), (None, 1), (12, 2)])
def test_padded_capture_normalizes_without_rescaling(capture, bits, native_type):
    camera, props, addresses = capture
    props["buffer_pixel_type"] = native_type
    fmt = CameraImageFormat.for_bit_depth(bits) if bits else CameraImageFormat()
    output = np.zeros((2, 3), dtype=fmt.dtype)
    camera.configure_frame_format(fmt)
    assert camera.start_acquisition([output], 1)
    raw = (ctypes.c_uint8 * props["buffer_frame_bytes"]).from_address(addresses[0])
    native = np.ndarray(
        (2, 3),
        dtype="uint8" if native_type == 1 else "uint16",
        buffer=raw,
        offset=2,
        strides=(8, 1 if native_type == 1 else 2),
    )
    pattern = np.array([[0, 1, 127], [128, 254, 255]], dtype=fmt.dtype)
    native[:] = pattern
    assert camera.get_frames() == [0]
    np.testing.assert_array_equal(output, pattern)
    camera.stop_acquisition()


def test_matching_tightly_packed_format_attaches_shared_buffer_directly(capture):
    camera, props, addresses = capture
    props.update(
        buffer_pixel_type=1,
        buffer_row_bytes=3,
        buffer_frame_bytes=6,
        buffer_top_offset=0,
    )
    camera.configure_frame_format(CameraImageFormat.for_bit_depth(8))
    output = np.zeros((2, 3), np.uint8)
    assert camera.start_acquisition([output], 1)
    assert addresses == [output.ctypes.data]
    camera.stop_acquisition()


def test_wrong_destination_dtype_is_rejected_before_native_attach(capture):
    camera, _, addresses = capture
    camera.configure_frame_format(CameraImageFormat.for_bit_depth(8))
    with pytest.raises(ValueError, match="buffer|dtype|format"):
        camera.start_acquisition([np.zeros((2, 3), np.uint16)], 1)
    assert not addresses


def test_out_of_range_native_counts_are_not_silently_truncated(capture):
    camera, props, addresses = capture
    camera.configure_frame_format(CameraImageFormat.for_bit_depth(8))
    output = np.zeros((2, 3), np.uint8)
    camera.start_acquisition([output], 1)
    raw = (ctypes.c_uint8 * props["buffer_frame_bytes"]).from_address(addresses[0])
    np.ndarray((2, 3), dtype=np.uint16, buffer=raw, offset=2, strides=(8, 2))[:] = 256
    with pytest.raises(RuntimeError, match="range|precision|alignment"):
        camera.get_frames()
    assert not output.any()


def test_native_container_must_hold_reported_precision(capture):
    camera, props, addresses = capture
    props["buffer_pixel_type"] = 1
    with pytest.raises(ValueError, match="precision|depth"):
        camera.configure_frame_format(CameraImageFormat.for_bit_depth(16))
    assert not addresses


def test_direct_mono16_cannot_claim_twelve_bits_for_larger_counts(capture):
    camera, props, addresses = capture
    props.update(buffer_row_bytes=6, buffer_frame_bytes=12, buffer_top_offset=0)
    camera.configure_frame_format(CameraImageFormat.for_bit_depth(12))
    output = np.zeros((2, 3), np.uint16)
    camera.start_acquisition([output], 1)
    assert addresses == [output.ctypes.data]
    output[:] = 4096
    with pytest.raises(RuntimeError, match="precision|range|alignment"):
        camera.get_frames()
