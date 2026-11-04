"""Opt-in camera-only capture; does not start microscope/illumination devices.

Set NAVIGATE_DCAM_SERIAL to the intended serial before running with
``pytest -m hardware``. NAVIGATE_DCAM_OUTPUT optionally selects an artifact folder.
"""

from contextlib import contextmanager
import json
import os
import time
from ctypes import byref, c_double
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pytest
import tifffile


@contextmanager
def native_handle(api: Any) -> Iterator[Any]:
    """Open a temporary native handle, balancing registration on every exit."""
    api.camReg.regCamera()
    opened = api.DCAMDEV_OPEN()
    try:
        assert api.dcamdev_open(byref(opened)) > 0
        yield opened.hdcam
    finally:
        try:
            if opened.hdcam:
                assert api.dcamdev_close(opened.hdcam) > 0
        finally:
            api.camReg.unregCamera()


@contextmanager
def preserve_settings(
    api: Any, properties: dict[str, int]
) -> Iterator[dict[str, float]]:
    """Snapshot before connection and restore even if the wrapper cannot construct."""
    original = {}
    with native_handle(api) as handle:
        for name, prop in properties.items():
            value = c_double()
            assert api.dcamprop_getvalue(handle, prop, byref(value)) > 0, name
            original[name] = value.value
    try:
        yield original
    finally:
        # The wrapper must be closed before opening this restoration handle.
        errors = []
        with native_handle(api) as handle:
            for name, value in original.items():
                if api.dcamprop_setvalue(handle, properties[name], value) <= 0:
                    errors.append(name)
                    continue
                restored = c_double()
                status = api.dcamprop_getvalue(
                    handle, properties[name], byref(restored)
                )
                if status <= 0 or not np.isclose(restored.value, value):
                    errors.append(name)
        assert not errors, f"Failed to restore settings: {errors}"


def read_property(camera: Any, prop: int) -> float:
    """Reject the wrapper's failure sentinel before comparing numeric properties."""
    value = camera.prop_getvalue(prop)
    assert value is not False, f"Could not read property {prop:#x}"
    return value


@pytest.mark.hardware
def test_software_triggered_frame(tmp_path: Path) -> None:
    """Connect through navigate, capture a real frame, and restore settings."""
    expected_serial = os.environ.get("NAVIGATE_DCAM_SERIAL")
    if not expected_serial:
        pytest.skip("Set NAVIGATE_DCAM_SERIAL to explicitly select a physical camera")

    from navigate.model.devices.APIs.hamamatsu import HamamatsuAPI as api
    from navigate.model.devices.camera.hamamatsu import HamamatsuBase

    # Numeric IDs below are from Hamamatsu DCAM-SDK4 dcamprop.h.
    settings = {
        "sensor_mode": (api.property_dict["sensor_mode"], 1.0),
        "image_pixeltype": (0x00420270, 2.0),  # DCAM_PIXELTYPE_MONO16
        "trigger_source": (api.property_dict["trigger_source"], 3.0),
        "exposure_time": (api.property_dict["exposure_time"], 0.01),
    }
    properties = {name: prop for name, (prop, _) in settings.items()}
    # DCAM.__init__ disables subarray mode. Restore it last, after sensor mode.
    properties["subarray_mode"] = api.property_dict["subarray_mode"]
    with preserve_settings(api, properties) as original:
        camera = HamamatsuBase.connect(0)
        capture_attempted = False
        try:
            assert camera._serial_number == expected_serial
            for name, (prop, value) in settings.items():
                assert camera.prop_setvalue(prop, value), name

            width = int(camera.get_property_value("image_width"))
            height = int(camera.get_property_value("image_height"))
            assert width > 0 and height > 0
            # Reject layouts that cannot fit the contiguous uint16 buffer.
            assert read_property(camera, 0x00420360) == 2  # BUFFER_PIXELTYPE
            assert read_property(camera, 0x00420330) == width * 2  # BUFFER_ROWBYTES
            assert read_property(camera, 0x00420340) == width * height * 2
            assert read_property(camera, 0x00420350) == 0  # BUFFER_TOPOFFSETBYTES
            frames = [np.full((height, width), 65535, dtype=np.uint16)]
            capture_attempted = True
            assert camera.start_acquisition(frames, 1)
            camera.fire_software_trigger()
            deadline = time.monotonic() + 10
            indices = []
            while not indices and time.monotonic() < deadline:
                indices = camera.get_frames()
            assert indices == [0], "No completed frame received within 10 seconds"
            assert camera.stop_acquisition()
            capture_attempted = False
            frame = frames[0].copy()
            assert np.any(frame != 65535), "Camera did not replace sentinel data"

            output = Path(os.environ.get("NAVIGATE_DCAM_OUTPUT", tmp_path))
            output.mkdir(parents=True, exist_ok=True)
            image_path = output / "orca-quest2-frame.tif"
            tifffile.imwrite(image_path, frame, photometric="minisblack")
            np.testing.assert_array_equal(tifffile.imread(image_path), frame)
            metadata = {
                "serial": camera._serial_number,
                "shape": list(frame.shape),
                "dtype": str(frame.dtype),
                "exposure_seconds": camera.get_property_value("exposure_time"),
                "trigger_source": camera.get_property_value("trigger_source"),
                "frame_indices": indices,
                "minimum": int(frame.min()),
                "maximum": int(frame.max()),
                "mean": float(frame.mean()),
                "standard_deviation": float(frame.std()),
                "original_settings": original,
            }
        finally:
            # Keep frame buffers alive until native capture stops and device closes.
            try:
                if capture_attempted:
                    camera.stop_acquisition()
            finally:
                camera.dev_close()
    assert api.camReg.numCameras == 0
    metadata["settings_restored"] = True
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))
    print(f"Image saved to {image_path}")
