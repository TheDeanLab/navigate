"""Regression tests for switching camera dtype without changing geometry."""

from types import SimpleNamespace

import numpy as np
import pytest

from navigate.model.devices.camera.format import CameraImageFormat
from navigate.model.model import Model


@pytest.fixture
def buffer_model():
    camera = SimpleNamespace(image_format=CameraImageFormat(), is_acquiring=False)
    camera.get_image_format = lambda: camera.image_format
    microscope = SimpleNamespace(camera=camera)
    microscope.update_data_buffer = lambda data, count: setattr(
        microscope, "data_buffer", data
    )
    model = Model.__new__(Model)
    model.is_acquiring = False
    model.data_buffer = None
    model.number_of_frames = 2
    model.img_width, model.img_height = 3, 2
    model.binning = "1x1"
    model.active_microscope_name = "camera"
    model.active_microscope = microscope
    model.microscopes = {"camera": microscope}
    model.configuration = {
        "experiment": {"CameraParameters": {"camera": {"binning": "1x1"}}}
    }
    yield model
    if model.data_buffer is not None:
        for frame in model.data_buffer:
            frame.shared_memory.close()
            try:
                frame.shared_memory.unlink()
            except FileNotFoundError:
                pass


def test_same_geometry_dtype_change_replaces_and_rebinds_buffers(buffer_model):
    model = buffer_model
    first = model.get_data_buffer(3, 2)
    assert first[0].dtype == np.uint16
    names = [frame.shared_memory.name for frame in first]
    model.active_microscope.camera.image_format = CameraImageFormat.for_bit_depth(8)
    second = model.get_data_buffer(3, 2)
    assert second[0].dtype == np.uint8
    assert second[0].nbytes == 6
    assert [frame.shared_memory.name for frame in second] != names
    assert model.active_microscope.data_buffer is second
    assert model.get_data_buffer(3, 2) is second


def test_same_dtype_depth_change_keeps_buffer(buffer_model):
    model = buffer_model
    model.active_microscope.camera.image_format = CameraImageFormat.for_bit_depth(12)
    first = model.get_data_buffer(3, 2)
    assert first is not None and first[0].dtype == np.uint16
    model.active_microscope.camera.image_format = CameraImageFormat.for_bit_depth(16)
    assert model.get_data_buffer(3, 2) is first


def test_reallocation_is_rejected_while_camera_acquires(buffer_model):
    model = buffer_model
    first = model.get_data_buffer(3, 2)
    first[0][:] = 1234
    model.active_microscope.camera.is_acquiring = True
    with pytest.raises(RuntimeError, match="acquisition"):
        model.get_data_buffer(4, 2)
    np.testing.assert_array_equal(first[0], np.full((2, 3), 1234))
    assert model.data_buffer is first


def test_allocation_failure_keeps_existing_live_mapping(buffer_model, monkeypatch):
    model = buffer_model
    first = model.get_data_buffer(3, 2)
    first[0][:] = 4321

    def fail(*args, **kwargs):
        raise MemoryError("allocation failed")

    monkeypatch.setattr("navigate.model.model.SharedNDArray", fail)
    with pytest.raises(MemoryError):
        model.get_data_buffer(4, 2)
    assert model.data_buffer is first
    np.testing.assert_array_equal(first[0], np.full((2, 3), 4321))


def test_controller_rebinds_same_size_buffer_after_depth_change(buffer_model):
    import pickle
    from navigate.controller.controller import Controller

    model = buffer_model
    model.update_data_buffer(3, 2)
    controller = Controller.__new__(Controller)
    controller.model = model
    controller.img_width, controller.img_height = 3, 2
    controller.data_buffer = pickle.loads(pickle.dumps(model.data_buffer))
    controller.configuration = model.configuration
    model.configuration["experiment"]["MicroscopeState"] = {"microscope_name": "camera"}
    model.configuration["experiment"]["CameraParameters"]["camera"].update(
        img_x_pixels=3, img_y_pixels=2
    )
    model.active_microscope.camera.image_format = CameraImageFormat.for_bit_depth(8)
    controller.update_buffer()
    assert controller.data_buffer[0].dtype == np.uint8
    assert controller.data_buffer is model.data_buffer


def test_virtual_microscope_allocates_selected_camera_dtype(buffer_model, monkeypatch):
    model = buffer_model
    model.virtual_microscopes = {}
    model.active_microscope.camera.image_format = CameraImageFormat.for_bit_depth(8)
    model.active_microscope.laser_wavelength = []
    model.active_microscope.laser = {}
    model.configuration["experiment"]["CameraParameters"]["camera"].update(
        img_x_pixels=3, img_y_pixels=2
    )
    virtual = SimpleNamespace()
    virtual.update_data_buffer = lambda data, count: setattr(
        virtual, "data_buffer", data
    )
    monkeypatch.setattr(
        "navigate.model.model.Microscope", lambda *args, **kwargs: virtual
    )
    monkeypatch.setattr("navigate.model.devices.SyntheticDAQ", lambda *args: object())
    frames = model.launch_virtual_microscope("camera", {})
    try:
        assert frames[0].dtype == np.uint8
        assert virtual.data_buffer is frames
    finally:
        for frame in frames:
            frame.shared_memory.close()
            frame.shared_memory.unlink()


def test_replaced_controller_mapping_lives_until_consumers_release_it(buffer_model):
    import gc
    import pickle
    import weakref
    from navigate.controller.controller import Controller

    model = buffer_model
    model.update_data_buffer(3, 2)
    model.data_buffer[0][:] = 1234
    controller = Controller.__new__(Controller)
    controller.model = model
    controller.img_width, controller.img_height = 3, 2
    controller.data_buffer = pickle.loads(pickle.dumps(model.data_buffer))
    controller.configuration = model.configuration
    model.configuration["experiment"]["MicroscopeState"] = {"microscope_name": "camera"}
    model.configuration["experiment"]["CameraParameters"]["camera"].update(
        img_x_pixels=3, img_y_pixels=2
    )
    # Real display and histogram callbacks retain either a frame or a flipped view.
    display = SimpleNamespace(image=controller.data_buffer[0][:, ::-1])
    pending = SimpleNamespace(image=controller.data_buffer[0])
    mapping_ref = weakref.ref(pending.image.shared_memory)
    model.active_microscope.camera.image_format = CameraImageFormat.for_bit_depth(8)
    controller.update_buffer()
    assert (
        mapping_ref()._mmap is not None
    )  # Check before dereferencing unmapped memory.
    np.testing.assert_array_equal(np.asarray(display.image), np.full((2, 3), 1234))
    np.testing.assert_array_equal(np.asarray(pending.image), np.full((2, 3), 1234))
    display.image = pending.image = None
    gc.collect()
    assert mapping_ref() is None


def test_controller_allocates_for_selected_microscope_before_resolution_switch(
    buffer_model,
):
    import pickle
    from navigate.controller.controller import Controller

    model = buffer_model
    model.update_data_buffer(3, 2)
    selected = SimpleNamespace(
        camera=SimpleNamespace(
            is_acquiring=False,
            get_image_format=lambda: CameraImageFormat.for_bit_depth(8),
        )
    )
    selected.update_data_buffer = lambda data, count: setattr(
        selected, "data_buffer", data
    )
    model.microscopes["selected"] = selected
    model.configuration["experiment"]["CameraParameters"]["selected"] = {
        "img_x_pixels": 3,
        "img_y_pixels": 2,
        "binning": "1x1",
    }
    model.configuration["experiment"]["MicroscopeState"] = {
        "microscope_name": "selected"
    }
    controller = Controller.__new__(Controller)
    controller.model = model
    controller.configuration = model.configuration
    controller.img_width, controller.img_height = 3, 2
    controller.data_buffer = pickle.loads(pickle.dumps(model.data_buffer))
    controller.update_buffer()
    assert model.active_microscope_name == "camera"
    assert controller.data_buffer[0].dtype == np.uint8
    assert selected.data_buffer is model.data_buffer
