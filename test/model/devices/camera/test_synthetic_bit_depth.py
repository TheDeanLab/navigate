"""Synthetic data exercises depth changes without a native camera driver."""

import numpy as np
import pytest

from navigate.model.devices.camera.synthetic import SyntheticCamera


@pytest.fixture
def camera():
    configuration = {
        "configuration": {
            "microscopes": {
                "scope": {
                    "camera": {
                        "hardware": {"serial_number": "synthetic"},
                        "x_pixels": 3,
                        "y_pixels": 2,
                    }
                }
            }
        },
        "experiment": {"CameraParameters": {"scope": {}}},
    }
    return SyntheticCamera("scope", None, configuration)


@pytest.mark.parametrize(
    "bits,dtype,expected",
    [
        (8, np.uint8, [0, 1, 255, 255, 255, 255]),
        (12, np.uint16, [0, 1, 255, 256, 4095, 4095]),
        (16, np.uint16, [0, 1, 255, 256, 4095, 65535]),
    ],
)
def test_synthetic_frames_preserve_values_at_selected_depth(
    camera, bits, dtype, expected
):
    assert camera.set_bit_depth(bits) == bits
    buffers = [np.zeros((2, 3), dtype=dtype)]
    camera.initialize_image_series(buffers, 1)
    camera.random_image = False
    camera.tif_images = [
        [np.array([0, 1, 255, 256, 4095, 65535], dtype=np.uint16).reshape(2, 3)]
    ]
    camera.generate_new_frame()
    np.testing.assert_array_equal(buffers[0], np.array(expected).reshape(2, 3))
    with pytest.raises(RuntimeError, match="acquisition"):
        camera.set_bit_depth(8)
    camera.close_image_series()


def test_synthetic_rejects_mismatched_buffer_before_acquiring(camera):
    camera.set_bit_depth(8)
    with pytest.raises(ValueError, match="buffer"):
        camera.initialize_image_series([np.zeros((2, 3), dtype=np.uint16)], 1)
    assert not camera.is_acquiring


def test_synthetic_rejects_unadvertised_depth(camera):
    with pytest.raises(ValueError):
        camera.set_bit_depth(10)
    assert camera.get_bit_depth() == 16


def test_model_can_unload_images_after_buffer_geometry_changes(camera):
    from types import SimpleNamespace
    from navigate.model.model import Model

    model = Model.__new__(Model)
    model.active_microscope = SimpleNamespace(camera=camera)
    model.data_buffer = [np.zeros((1, 2), dtype=np.uint16)]
    model.number_of_frames = 1
    model.load_images(None)
    assert camera.random_image
    assert not camera.is_acquiring
    assert camera.data_buffer is None


def test_unknown_sensor_mode_reports_validation_error_without_changing_settings(camera):
    camera.set_sensor_mode("Light-Sheet")
    with pytest.raises(ValueError, match="Unsupported synthetic sensor mode"):
        camera.set_sensor_mode("test")
    assert camera.get_advanced_setting("sensor_mode") == 12
    assert camera.get_advanced_setting("scan_speed") == 2
