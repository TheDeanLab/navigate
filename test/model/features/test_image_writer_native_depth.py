"""Verify the acquisition writer uses confirmed camera format, not saved requests."""

from queue import Queue
from types import SimpleNamespace

import numpy as np
import pytest
import tifffile

from navigate.model.devices.camera.format import CameraImageFormat
from navigate.model.features.image_writer import ImageWriter


@pytest.mark.parametrize("depth", [8, 12, 16])
def test_image_writer_saves_confirmed_native_depth(tmp_path, monkeypatch, depth):
    fmt = CameraImageFormat.for_bit_depth(depth)
    frames = np.array([0, 1, 127, 128, 254, (1 << depth) - 1], dtype=fmt.dtype).reshape(
        1, 2, 3
    )
    configuration = {
        "configuration": {
            "microscopes": {
                "scope": {"camera": {}, "stage": {}, "zoom": {"pixel_size": {"1x": 1}}}
            }
        },
        "experiment": {
            "MicroscopeState": {
                "microscope_name": "scope",
                "zoom": "1x",
                "step_size": 1,
                "timepoint_interval": 0,
                "image_mode": "single",
                "timepoints": 1,
                "channels": {"channel_1": {"is_selected": True}},
                "is_multiposition": False,
                "stack_cycling_mode": "per_stack",
            },
            "CameraParameters": {
                "scope": {"img_x_pixels": 3, "img_y_pixels": 2, "bit_depth": 16}
            },
            "Saving": {"file_type": "TIFF", "save_directory": str(tmp_path)},
        },
    }
    model = SimpleNamespace(
        configuration=configuration,
        data_buffer=frames,
        number_of_frames=1,
        active_microscope_name="scope",
        active_microscope=SimpleNamespace(current_channel=0),
        get_camera_image_format=lambda name: fmt,
        data_buffer_positions=np.zeros((1, 5)),
        asi=False,
        imaging_mode="single",
        event_queue=Queue(),
        stop_acquisition=False,
    )
    monkeypatch.setattr(
        "navigate.model.features.image_writer.shutil.disk_usage",
        lambda path: (10**12, 0, 10**12),
    )
    writer = ImageWriter(model)
    try:
        assert writer.data_source.dtype == fmt.dtype
        assert writer.data_source.significant_bits == depth
        assert writer.data_source.nbytes == frames.nbytes
        writer.save_image([0])
        assert not model.stop_acquisition
        assert writer.mip.dtype == frames.dtype
        np.testing.assert_array_equal(writer.mip[0], frames[0])
    finally:
        writer.close()
    np.testing.assert_array_equal(
        tifffile.imread(writer.data_source.file_name[0]), frames[0]
    )
