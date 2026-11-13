"""Saved batches retain the confirmed camera settings of their own segment."""

import json
from pathlib import Path
from queue import Queue
from types import MethodType, SimpleNamespace
import xml.etree.ElementTree as ET

import h5py
import numpy as np
import pytest
import tifffile
import zarr

from navigate.model.devices.camera.synthetic import SyntheticCamera
from navigate.model.features.image_writer import ImageWriter
from navigate.model.microscope import Microscope
from navigate.model.model import Model


@pytest.fixture
def acquisition(tmp_path, monkeypatch):
    model = Model.__new__(Model)
    model.configuration = {
        "configuration": {
            "microscopes": {
                name: {
                    "camera": {
                        "x_pixels": 3,
                        "hardware": {"serial_number": "segmentation-synthetic"},
                        "y_pixels": 2,
                        "supported_readout_directions": ["Top-to-Bottom"],
                    },
                    "stage": {},
                    "zoom": {"pixel_size": {"1x": 1}},
                }
                for name in ("scope", "aux")
            }
        },
        "experiment": {
            "MicroscopeState": {
                "microscope_name": "scope",
                "zoom": "1x",
                "step_size": 1,
                "timepoint_interval": 0,
                "image_mode": "z-stack",
                "number_z_steps": 2,
                "timepoints": 2,
                "channels": {"channel_1": {"is_selected": True}},
                "is_multiposition": False,
                "stack_cycling_mode": "per_stack",
            },
            "CameraParameters": {
                name: {
                    "img_x_pixels": 3,
                    "img_y_pixels": 2,
                    "bit_depth": 16,
                    "sensor_mode": "Normal",
                    "scan_speed": 1,
                    "camera_exposure_time": 1,
                }
                for name in ("scope", "aux")
            },
            "Saving": {"file_type": "TIFF", "save_directory": str(tmp_path)},
        },
    }
    model.active_microscope_name = "scope"
    model.microscopes = {}
    model.virtual_microscopes = {}
    for name in ("scope", "aux"):
        camera = SyntheticCamera(name, None, model.configuration)
        scope = SimpleNamespace(
            configuration=model.configuration,
            microscope_name=name,
            camera=camera,
            current_channel=0,
            set_camera_trigger_mode=lambda: None,
            set_camera_roi_and_binning=lambda: True,
        )
        scope.set_camera_sensor_mode = lambda s=scope: s.camera.set_sensor_mode(
            model.configuration["experiment"]["CameraParameters"][s.microscope_name][
                "sensor_mode"
            ]
        )
        scope.configure_camera = MethodType(Microscope.configure_camera, scope)
        scope.configure_camera()
        model.microscopes[name] = scope
    model.active_microscope = model.microscopes["scope"]
    model.data_buffer = np.arange(24, dtype=np.uint16).reshape(4, 2, 3)
    model.data_buffer_positions = np.zeros((4, 5))
    model.number_of_frames = 4
    model.asi = False
    model.imaging_mode = "z-stack"
    model.event_queue = Queue()
    model.stop_acquisition = False
    monkeypatch.setattr(
        "navigate.model.features.image_writer.shutil.disk_usage",
        lambda path: (10**12, 0, 10**12),
    )
    return model


def read_saved(source, kind):
    """Read the saved first stack and scan/correction metadata from disk."""
    if kind in ("TIFF", "OME-TIFF"):
        with tifffile.TiffFile(source.file_name[0]) as image:
            pixels = image.asarray()
            if kind == "TIFF":
                settings = json.loads(image.pages[0].description).get(
                    "camera_settings", {}
                )
            else:
                entries = ET.fromstring(image.ome_metadata).findall(
                    "{*}StructuredAnnotations/{*}MapAnnotation/{*}Value/{*}M"
                )
                settings = {entry.get("K"): int(entry.text) for entry in entries}
    else:
        if kind == "H5":
            image = h5py.File(source.file_name, "r")
            pixels = image["t00000/s00/0/cells"][:]
        else:
            store = (
                zarr.N5Store(source.file_name)
                if kind == "N5"
                else zarr.storage.FSStore(source.file_name)
            )
            image = zarr.open_group(store, mode="r")
            pixels = (
                image["setup0/timepoint0/s0"][:]
                if kind == "N5"
                else image["p0_0"][0, 0]
            )
        settings = {
            name: image.attrs["camera_" + name]
            for name in ("scan_speed", "defect_correction", "hot_pixel_correction")
            if "camera_" + name in image.attrs
        }
        if kind == "H5":
            image.close()
        else:
            store.close()
    return pixels, settings


def set_sensor_mode(model, name, mode):
    parameters = model.configuration["experiment"]["CameraParameters"][name]
    parameters["sensor_mode"] = mode
    parameters["scan_speed"] = 1
    model.microscopes[name].configure_camera()


@pytest.mark.parametrize("kind", ["TIFF", "OME-TIFF", "H5", "N5", "OME-Zarr"])
@pytest.mark.parametrize("name,subdir", [("scope", ""), ("aux", "additional/aux")])
def test_settings_changes_preserve_each_segment(acquisition, kind, name, subdir):
    model = acquisition
    model.configuration["experiment"]["Saving"]["file_type"] = kind
    writer = ImageWriter(model, microscope_name=name, sub_dir=subdir)
    base = Path(writer.save_directory)
    try:
        original = writer.data_source
        writer.save_image([0])
        # A pending UI request is not a confirmed camera change.
        model.configuration["experiment"]["CameraParameters"][name]["scan_speed"] = 2
        writer.save_image([1])
        assert writer.data_source is original
        set_sensor_mode(model, name, "Light-Sheet")
        assert model.get_camera_settings_metadata(name)["scan_speed"] == 2
        writer.save_image([2, 3])
        light_sheet = writer.data_source
        assert light_sheet is not original
        assert Path(writer.save_directory) == base / "camera-settings-001"
        before = {p: p.read_bytes() for p in base.iterdir() if p.is_file()}
        set_sensor_mode(model, name, "Normal")
        writer.save_image([0, 1])
        restored = writer.data_source
        assert Path(writer.save_directory) == base / "camera-settings-002"
        assert restored is not original and restored is not light_sheet
        assert not model.stop_acquisition
    finally:
        writer.close()
    for source, expected_frames, expected_scan in (
        (original, model.data_buffer[:2], 1),
        (light_sheet, model.data_buffer[2:], 2),
        (restored, model.data_buffer[:2], 1),
    ):
        pixels, settings = read_saved(source, kind)
        np.testing.assert_array_equal(pixels, expected_frames)
        assert settings["scan_speed"] == expected_scan
    assert all(p.read_bytes() == content for p, content in before.items())
    np.testing.assert_array_equal(writer.mip[0], model.data_buffer[1])
    assert (base / "MIP" / "P0000_CH00_000000.tiff").exists()
    assert (base / "camera-settings-001" / "MIP" / "P0000_CH00_000000.tiff").exists()


@pytest.mark.parametrize("kind", ["TIFF", "OME-TIFF", "H5", "N5", "OME-Zarr"])
def test_unknown_settings_clear_previous_metadata(acquisition, kind):
    model = acquisition
    model.configuration["experiment"]["Saving"]["file_type"] = kind
    writer = ImageWriter(model)
    try:
        writer.save_image([0, 1])
        original = writer.data_source
        model.active_microscope._camera_settings_metadata = {}
        writer.save_image([2, 3])
        unknown = writer.data_source
        assert unknown is not original
    finally:
        writer.close()
    assert read_saved(original, kind)[1]["scan_speed"] == 1
    assert read_saved(unknown, kind)[1] == {}


def test_existing_segments_are_not_overwritten(acquisition):
    model = acquisition
    model.configuration["experiment"]["Saving"]["file_type"] = "H5"
    base = Path(model.configuration["experiment"]["Saving"]["save_directory"])
    existing = base / "camera-settings-001"
    existing.mkdir()
    sentinel = existing / "capture.h5"
    sentinel.write_bytes(b"previous acquisition")
    writer = ImageWriter(model, image_name="capture.h5")
    try:
        writer.save_image([0, 1])
        set_sensor_mode(model, "scope", "Light-Sheet")
        writer.save_image([2, 3])
        assert Path(writer.save_directory) == base / "camera-settings-002"
        assert Path(writer.data_source.file_name).name == "capture.h5"
    finally:
        writer.close()
    assert sentinel.read_bytes() == b"previous acquisition"
    assert read_saved(writer.data_source, "H5")[1]["scan_speed"] == 2


def test_camera_restart_waits_for_pending_writer_batch(acquisition, monkeypatch):
    """Exercise the real data-loop and restart barrier around a slow file write."""
    from threading import Event, Lock, Thread

    from navigate.model.features.update_setting import SetCameraParameters

    model = acquisition
    model.is_data_thread_on = True
    model.ask_to_pause_data_thread = False
    model.pause_data_event = Event()
    model.camera_wait_iterations = 10
    model.signal_acquisition_complete = False
    model.logger = SimpleNamespace(info=lambda *a: None, performance=lambda *a: None)
    model.show_img_pipe = SimpleNamespace(send=lambda *a: None)
    model.end_acquisition = lambda: None
    scope = model.active_microscope
    scope.end_acquisition = scope.camera.close_image_series
    scope.prepare_next_channel = lambda: None
    ready = Event()
    release_write = Event()
    pause_requested = Event()

    class ObservedPauseLock:
        """Expose the real pause request after the model sets its pause flag."""

        def __init__(self):
            self.lock = Lock()

        def acquire(self):
            if model.ask_to_pause_data_thread:
                pause_requested.set()
            return self.lock.acquire()

        def release(self):
            return self.lock.release()

        def locked(self):
            return self.lock.locked()

    model.pause_data_ready_lock = ObservedPauseLock()
    failures = []
    prepared_after_frames = []
    frames = iter(([0, 1], [2, 3]))
    monkeypatch.setattr(scope.camera, "get_new_frame", lambda: next(frames))
    writer = ImageWriter(model)
    original = writer.data_source
    write = original.write

    def pending_write(*args, **kwargs):
        if original._current_frame == 0:
            ready.set()
            assert release_write.wait(5), "test did not release pending write"
        return write(*args, **kwargs)

    monkeypatch.setattr(original, "write", pending_write)

    def prepare():
        prepared_after_frames.append(original._current_frame)
        scope.configure_camera()
        return {}

    scope.prepare_acquisition = prepare

    def run(function):
        try:
            function()
        except BaseException as exc:
            failures.append(exc)

    data = Thread(
        target=run,
        args=(lambda: model.run_data_process(4, writer.save_image),),
        daemon=True,
    )
    change = Thread(
        target=run,
        args=(SetCameraParameters(model, sensor_mode="Light-Sheet").signal_func,),
        daemon=True,
    )
    try:
        data.start()
        assert ready.wait(5)
        change.start()
        assert pause_requested.wait(5)
        # The GUI request already changed, but the confirmed acquisition snapshot
        # cannot change until the in-flight file write and its batch complete.
        assert model.get_camera_settings_metadata()["scan_speed"] == 1
        release_write.set()
        change.join(5)
        data.join(5)
        assert not change.is_alive() and not data.is_alive()
        assert failures == []
        assert prepared_after_frames == [2]
        assert writer.data_source is not original
    finally:
        release_write.set()
        model.stop_acquisition = True
        model.resume_data_thread()
        data.join(5)
        if change.ident is not None:
            change.join(5)
        writer.close()
    np.testing.assert_array_equal(
        read_saved(original, "TIFF")[0], model.data_buffer[:2]
    )
    assert read_saved(original, "TIFF")[1]["scan_speed"] == 1
    np.testing.assert_array_equal(
        read_saved(writer.data_source, "TIFF")[0], model.data_buffer[2:]
    )
    assert read_saved(writer.data_source, "TIFF")[1]["scan_speed"] == 2


def test_segment_open_failure_stops_acquisition_without_overwriting(
    acquisition, monkeypatch
):
    model = acquisition
    writer = ImageWriter(model)
    writer.save_image([0, 1])
    original = writer.data_source
    set_sensor_mode(model, "scope", "Light-Sheet")

    def unavailable_source(*args, **kwargs):
        raise OSError("storage unavailable")

    monkeypatch.setattr(
        "navigate.model.features.image_writer.data_sources.get_data_source",
        unavailable_source,
    )
    try:
        writer.save_image([2, 3])
        assert model.stop_acquisition
        assert model.event_queue.get_nowait()[0] == "warning"
    finally:
        if writer.data_source is not None:
            writer.close()
    pixels, settings = read_saved(original, "TIFF")
    np.testing.assert_array_equal(pixels, model.data_buffer[:2])
    assert settings["scan_speed"] == 1
