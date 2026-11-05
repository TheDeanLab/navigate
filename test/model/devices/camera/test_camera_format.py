"""Camera capabilities must not confuse meaningful bits with storage width."""

import pickle
from dataclasses import asdict

import numpy as np
import pytest

from navigate.model.devices.camera.synthetic import SyntheticCamera


def test_legacy_driver_keeps_uint16_without_claiming_sensor_precision():
    camera = SyntheticCamera.__new__(SyntheticCamera)
    assert camera.get_bit_depth() is None
    capability = camera.get_advanced_setting_capabilities()["bit_depth"]
    assert capability.current_value is None
    assert capability.choices == ()
    assert not capability.writable
    assert capability.reason
    image_format = camera.get_image_format()
    assert image_format.dtype == "uint16"
    assert image_format.bit_depth is None
    assert image_format.bytes_per_pixel == 2
    with pytest.raises(NotImplementedError):
        camera.set_bit_depth(8)


@pytest.mark.parametrize(
    "bits,dtype,size", [(8, "uint8", 1), (12, "uint16", 2), (16, "uint16", 2)]
)
def test_format_keeps_precision_separate_from_storage(bits, dtype, size):
    from navigate.model.devices.camera.format import CameraImageFormat

    image_format = CameraImageFormat.for_bit_depth(bits)
    assert image_format.dtype == dtype
    assert image_format.bit_depth == bits
    assert image_format.bytes_per_pixel == size
    assert pickle.loads(pickle.dumps(image_format)) == image_format
    assert asdict(image_format) == {"dtype": dtype, "bit_depth": bits}


@pytest.mark.parametrize("bits", [0, -1, 17, 8.5, True, "8", float("nan")])
def test_format_rejects_invalid_depth(bits):
    from navigate.model.devices.camera.format import CameraImageFormat

    with pytest.raises((TypeError, ValueError)):
        CameraImageFormat.for_bit_depth(bits)


@pytest.mark.parametrize(
    "dtype,bits", [("uint8", 12), ("int16", 16), ("float32", 16), ("uint16", 0)]
)
def test_format_rejects_unsupported_or_truncating_representation(dtype, bits):
    from navigate.model.devices.camera.format import CameraImageFormat

    with pytest.raises((TypeError, ValueError)):
        CameraImageFormat(dtype=dtype, bit_depth=bits)


def test_numpy_depth_normalizes_for_configuration_serialization():
    from navigate.model.devices.camera.format import CameraImageFormat

    image_format = CameraImageFormat.for_bit_depth(np.int64(12))
    assert type(image_format.bit_depth) is int
