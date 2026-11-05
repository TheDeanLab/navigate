"""Camera settings transactions and idle format negotiation without hardware."""

from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from navigate.model.devices.camera.format import (
    CameraImageFormat,
    CameraSettingCapability,
)
from navigate.model.model import Model
from navigate.model.microscope import Microscope


class Camera:
    def __init__(self):
        self.depth = 16
        self.is_acquiring = False
        self.writes = []
        self.camera_controller = object()

    def get_image_format(self):
        return CameraImageFormat.for_bit_depth(self.depth)

    def get_advanced_setting_capabilities(self):
        return {
            "bit_depth": CameraSettingCapability(
                self.depth, (8, 12, 16), True, reason=""
            )
        }

    def set_bit_depth(self, value):
        CameraImageFormat.for_bit_depth(value)
        if value not in (8, 12, 16):
            raise ValueError("Unsupported depth")
        self.writes.append(value)
        self.depth = value
        return value


@pytest.fixture
def model():
    m = Model.__new__(Model)
    m.is_acquiring = False
    m.active_microscope_name = "scope"
    camera = Camera()
    microscope = SimpleNamespace(camera=camera)
    microscope.configure_camera = Mock(side_effect=lambda: camera.get_image_format())
    microscope.update_data_buffer = Mock()
    m.active_microscope = microscope
    m.microscopes = {"scope": microscope}
    m.virtual_microscopes = {}
    m.data_buffer = None
    m.number_of_frames = 2
    m.img_width, m.img_height = 3, 2
    m.binning = "1x1"
    m.configuration = {
        "experiment": {
            "MicroscopeState": {"microscope_name": "scope"},
            "CameraParameters": {
                "scope": {"img_x_pixels": 3, "img_y_pixels": 2, "binning": "1x1"}
            },
        }
    }
    yield m
    if m.data_buffer:
        for frame in m.data_buffer:
            frame.shared_memory.close()
            frame.shared_memory.unlink()


def request(model, **values):
    return model.camera_advanced_settings(
        {"microscope": "scope", "request_id": 1, **values}
    )


def test_read_has_identity_and_no_side_effects(model):
    result = request(model)
    assert result["identity"]
    assert result["capability"].current_value == 16
    assert model.active_microscope.camera.writes == []
    assert (
        "bit_depth"
        not in model.configuration["experiment"]["CameraParameters"]["scope"]
    )


def test_confirmed_write_persists_and_replaces_active_buffer(model):
    identity = request(model)["identity"]
    result = request(model, identity=identity, bit_depth=8)
    assert result["error"] is None
    assert result["capability"].current_value == 8
    assert result["data_buffer"][0].dtype == np.uint8
    assert (
        model.configuration["experiment"]["CameraParameters"]["scope"]["bit_depth"] == 8
    )


@pytest.mark.parametrize("failure", ["busy", "identity", "invalid"])
def test_rejected_request_does_not_write_or_persist(model, failure):
    identity = request(model)["identity"]
    values = dict(identity=identity, bit_depth=8)
    if failure == "busy":
        # Another adapter wrapping the same physical camera must lock this popup.
        model.microscopes["alias"] = SimpleNamespace(
            camera=SimpleNamespace(is_acquiring=True)
        )
    elif failure == "identity":
        values["identity"] = "stale"
    else:
        values["bit_depth"] = True
    result = request(model, **values)
    assert result["error"]
    assert model.active_microscope.camera.writes == []
    assert (
        "bit_depth"
        not in model.configuration["experiment"]["CameraParameters"]["scope"]
    )


def test_allocation_failure_restores_previous_depth(model, monkeypatch):
    identity = request(model)["identity"]
    monkeypatch.setattr(
        model, "get_data_buffer", Mock(side_effect=MemoryError("no memory"))
    )
    result = request(model, identity=identity, bit_depth=8)
    assert result["error"]
    assert model.active_microscope.camera.depth == 16
    assert (
        "bit_depth"
        not in model.configuration["experiment"]["CameraParameters"]["scope"]
    )


def test_prepare_negotiates_after_mode_change_before_allocation(model):
    def configure():
        model.active_microscope.camera.depth = 8
        return CameraImageFormat.for_bit_depth(8)

    model.active_microscope.configure_camera.side_effect = configure
    result = model.prepare_camera_buffers("scope")
    assert result["data_buffer"][0].dtype == np.uint8
    assert model.active_microscope._buffer_image_format.bit_depth == 8


@pytest.mark.parametrize("saved", [None, 8, 12])
def test_microscope_applies_optional_depth_after_mode_and_roi(saved):
    m = Microscope.__new__(Microscope)
    m.microscope_name = "scope"
    m.camera = Camera()
    calls = []
    m.set_camera_trigger_mode = lambda: calls.append("trigger")
    m.set_camera_sensor_mode = lambda: calls.append("sensor")
    m.set_camera_roi_and_binning = lambda: calls.append("roi") or True
    original = m.camera.set_bit_depth
    m.camera.set_bit_depth = lambda value: calls.append("depth") or original(value)
    parameters = {} if saved is None else {"bit_depth": saved}
    m.configuration = {"experiment": {"CameraParameters": {"scope": parameters}}}
    assert m.configure_camera().bit_depth == (16 if saved is None else saved)
    assert calls == ["trigger", "sensor", "roi"] + ([] if saved is None else ["depth"])


def test_busy_read_does_not_query_sdk(model):
    model.is_acquiring = True
    model.active_microscope.camera.get_advanced_setting_capabilities = Mock(
        side_effect=AssertionError("SDK read")
    )
    result = request(model)
    assert not result["capability"].writable
    assert "acquisition" in result["capability"].reason.lower()


@pytest.mark.parametrize("depth", [8, 12, 16])
def test_synthetic_apply_save_experiment_reload_capture_and_save(
    model, tmp_path, depth
):
    from queue import Queue
    from types import MethodType
    import tifffile
    from navigate.model.devices.camera.synthetic import SyntheticCamera
    from navigate.model.features.image_writer import ImageWriter
    from navigate.tools.file_functions import save_yaml_file, load_yaml_file

    model.configuration["configuration"] = {
        "microscopes": {
            "scope": {
                "camera": {
                    "hardware": {"serial_number": "depth-test"},
                    "x_pixels": 3,
                    "y_pixels": 2,
                },
                "stage": {},
                "zoom": {"pixel_size": {"1x": 1}},
            }
        }
    }
    experiment = model.configuration["experiment"]
    experiment["MicroscopeState"].update(
        zoom="1x",
        step_size=1,
        timepoint_interval=0,
        image_mode="single",
        timepoints=1,
        channels={"channel_1": {"is_selected": True}},
        is_multiposition=False,
        stack_cycling_mode="per_stack",
    )
    experiment["Saving"] = {"file_type": "TIFF", "save_directory": str(tmp_path)}
    camera = SyntheticCamera("scope", None, model.configuration)
    microscope = model.active_microscope
    microscope.camera = camera
    microscope.configuration = model.configuration
    microscope.microscope_name = "scope"
    microscope.current_channel = 0
    microscope.set_camera_trigger_mode = lambda: camera.set_trigger_mode("Internal")
    microscope.set_camera_sensor_mode = lambda: camera.set_sensor_mode("Normal")
    microscope.set_camera_roi_and_binning = lambda: True
    microscope.configure_camera = MethodType(Microscope.configure_camera, microscope)
    result = request(model, identity=request(model)["identity"], bit_depth=depth)
    assert result["error"] is None
    assert save_yaml_file(str(tmp_path), experiment)
    camera.set_bit_depth(16)
    model.configuration["experiment"] = load_yaml_file(tmp_path / "experiment.yml")
    frames = model.prepare_camera_buffers("scope")["data_buffer"]
    assert camera.get_bit_depth() == depth
    pattern = np.array(
        [0, 1, 127, 128, 254, (1 << depth) - 1], dtype=frames[0].dtype
    ).reshape(2, 3)
    camera.initialize_image_series(frames, model.number_of_frames)
    camera.load_images(ds=[[pattern]])
    camera.generate_new_frame()
    np.testing.assert_array_equal(frames[0], pattern)
    model.data_buffer_positions = np.zeros((model.number_of_frames, 5))
    model.asi = False
    model.imaging_mode = "single"
    model.event_queue = Queue()
    model.stop_acquisition = False
    writer = ImageWriter(model)
    try:
        writer.save_image([0])
    finally:
        writer.close()
        camera.close_image_series()
    filename = writer.data_source.file_name[0]
    np.testing.assert_array_equal(tifffile.imread(filename), pattern)
    with tifffile.TiffFile(filename) as image:
        assert image.pages[0].dtype == frames[0].dtype
        assert f'"camera_bit_depth": {depth}' in image.pages[0].description
