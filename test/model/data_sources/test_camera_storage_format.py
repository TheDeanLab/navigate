"""All image writers preserve normalized camera values and meaningful precision."""

import json
import xml.etree.ElementTree as ET

import h5py
import numpy as np
import pytest
import tifffile
import zarr

from navigate.model.data_sources import get_data_source
from navigate.model.devices.camera.format import CameraImageFormat


@pytest.fixture(
    params=[
        ("TIFF", ".tif"),
        ("OME-TIFF", ".ome.tif"),
        ("H5", ".h5"),
        ("N5", ".n5"),
        ("OME-Zarr", ".zarr"),
    ]
)
def storage(request, tmp_path):
    kind, extension = request.param
    source = get_data_source(kind)(str(tmp_path / ("image" + extension)))
    source.metadata.shape_x = 3
    source.metadata.shape_y = 2
    source.metadata._configuration = {
        "experiment": {
            "MicroscopeState": {"zoom": "1x", "timepoint_interval": 0},
            "CameraParameters": {"camera": {"camera_exposure_time": 1}},
        },
        "configuration": {
            "microscopes": {"camera": {"zoom": {"pixel_size": {"1x": 1}}}}
        },
    }
    source.metadata.active_microscope = "camera"
    source.set_metadata({"z": 2})
    yield kind, source
    if getattr(source, "image", None) is not None:
        source.close()


@pytest.mark.parametrize("depth", [None, 8, 12, 16])
def test_native_depth_round_trip(storage, depth):
    kind, source = storage
    fmt = (
        CameraImageFormat.for_bit_depth(depth)
        if depth is not None
        else CameraImageFormat()
    )
    source.set_image_format(fmt)
    assert source.dtype == fmt.dtype
    assert source.significant_bits == depth
    assert source.nbytes == 12 * fmt.bytes_per_pixel
    pattern = np.array(
        [0, 1, 127, 128, 254, (1 << (depth or 16)) - 1], dtype=fmt.dtype
    ).reshape(2, 3)
    frames = np.stack([pattern, pattern[:, ::-1]])
    for frame in frames:
        source.write(frame, x=0, y=0, z=0, theta=0, f=0)
    source.close()
    if kind in ("TIFF", "OME-TIFF"):
        filename = source.file_name[0]
        with tifffile.TiffFile(filename) as image:
            restored = image.asarray()
            if kind == "OME-TIFF":
                pixels = ET.fromstring(image.ome_metadata).find("{*}Image/{*}Pixels")
                assert pixels.get("Type") == fmt.dtype
                assert pixels.get("SignificantBits") == (str(depth) if depth else None)
            else:
                assert (
                    json.loads(image.pages[0].description).get("camera_bit_depth")
                    == depth
                )
    elif kind == "H5":
        filename = source.file_name
        with h5py.File(filename, "r") as image:
            restored = image["t00000/s00/0/cells"][:]
            assert image.attrs.get("camera_bit_depth") == depth
    else:
        filename = source.file_name
        store = (
            zarr.N5Store(filename) if kind == "N5" else zarr.storage.FSStore(filename)
        )
        image = zarr.open_group(store, mode="r")
        restored = (
            image["setup0/timepoint0/s0"][:] if kind == "N5" else image["p0_0"][0, 0]
        )
        assert image.attrs.get("camera_bit_depth") == depth
        store.close()
    assert restored.dtype == np.dtype(fmt.dtype)
    np.testing.assert_array_equal(restored, frames)
    reopened = get_data_source(kind)(filename, "r")
    try:
        assert reopened.dtype == fmt.dtype
        assert reopened.significant_bits == depth
        assert (reopened.shape_y, reopened.shape_x) == (2, 3)
        if kind not in ("TIFF", "OME-TIFF"):
            np.testing.assert_array_equal(
                reopened.get_slice(slice(None), slice(None), 0, slice(None)), frames
            )
    finally:
        reopened.close()


def test_writer_rejects_dtype_changes_before_writing(storage):
    _, source = storage
    source.set_image_format(CameraImageFormat.for_bit_depth(8))
    source.write(np.zeros((2, 3), dtype=np.uint8), x=0, y=0, z=0, theta=0, f=0)
    with pytest.raises(ValueError, match="format|dtype"):
        source.write(np.full((2, 3), 1024, dtype=np.uint16))
    assert source._current_frame == 1
    with pytest.raises(RuntimeError):
        source.set_image_format(CameraImageFormat.for_bit_depth(16))


def test_confirmed_scan_correction_metadata_round_trip(storage):
    kind, source = storage
    settings = {"scan_speed": 2, "defect_correction": 1, "hot_pixel_correction": 3}
    source.set_camera_settings(settings)
    settings["scan_speed"] = 999
    source.write(np.zeros((2, 3), dtype=np.uint16), x=0, y=0, z=0, theta=0, f=0)
    source.write(np.ones((2, 3), dtype=np.uint16), x=0, y=0, z=0, theta=0, f=0)
    source.close()
    expected = {"scan_speed": 2, "defect_correction": 1, "hot_pixel_correction": 3}
    if kind in ("TIFF", "OME-TIFF"):
        with tifffile.TiffFile(source.file_name[0]) as image:
            if kind == "TIFF":
                assert (
                    json.loads(image.pages[0].description)["camera_settings"]
                    == expected
                )
            else:
                entries = ET.fromstring(image.ome_metadata).findall(
                    "{*}StructuredAnnotations/{*}MapAnnotation/{*}Value/{*}M"
                )
                assert {e.get("K"): int(e.text) for e in entries} == expected
    elif kind == "H5":
        with h5py.File(source.file_name, "r") as image:
            assert {key: image.attrs["camera_" + key] for key in expected} == expected
    else:
        store = (
            zarr.N5Store(source.file_name)
            if kind == "N5"
            else zarr.storage.FSStore(source.file_name)
        )
        image = zarr.open_group(store, mode="r")
        assert {key: image.attrs["camera_" + key] for key in expected} == expected
        store.close()
