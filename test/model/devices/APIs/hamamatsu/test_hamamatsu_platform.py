"""Native-library boundary tests that do not require a camera or DCAM driver."""

import ctypes
import ctypes.util
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

API_PATH = (
    Path(__file__).resolve().parents[5]
    / "src/navigate/model/devices/APIs/hamamatsu/HamamatsuAPI.py"
)


class NativeLibrary:
    """Expose ctypes functions, including their native pointer/type semantics."""

    def __getattr__(self, name):
        function = ctypes.CFUNCTYPE(ctypes.c_int32)(lambda: 1)
        setattr(self, name, function)
        return function


def load_api(
    monkeypatch,
    system="Linux",
    library=None,
    error=None,
    found_library="libdcamapi.so.4",
):
    """Import a fresh wrapper with only the external native loader replaced."""
    library = library if library is not None else NativeLibrary()
    loader = Mock(return_value=library, side_effect=error)
    monkeypatch.setattr("platform.system", lambda: system)
    monkeypatch.setattr(ctypes.util, "find_library", lambda name: found_library)
    monkeypatch.setattr(ctypes, "CDLL", loader)
    if system == "Windows":
        monkeypatch.setattr(
            ctypes, "windll", SimpleNamespace(LoadLibrary=loader), raising=False
        )
    else:
        monkeypatch.delattr(ctypes, "windll", raising=False)
    spec = importlib.util.spec_from_file_location(
        "navigate.test_dcam_platform", API_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, loader


@pytest.mark.parametrize(
    "system,library_name", [("Linux", "libdcamapi.so.4"), ("Windows", "dcamapi.dll")]
)
def test_platform_loads_native_library(monkeypatch, system, library_name):
    api, loader = load_api(monkeypatch, system)
    loader.assert_called_once_with(library_name)
    assert callable(api.dcamapi_init)


def test_missing_linux_library_explains_driver_requirement(monkeypatch):
    with pytest.raises(OSError, match="DCAM-API") as exc:
        load_api(monkeypatch, error=OSError("libdcamapi.so.4: not found"))
    assert isinstance(exc.value.__cause__, OSError)


def test_linux_uses_soname_when_library_discovery_is_unavailable(monkeypatch):
    api, loader = load_api(monkeypatch, found_library=None)
    loader.assert_called_once_with("libdcamapi.so.4")
    assert callable(api.dcamdev_open)


def test_unsupported_platform_reports_it_explicitly(monkeypatch):
    with pytest.raises(OSError, match="Windows and Linux, not Darwin"):
        load_api(monkeypatch, system="Darwin")


def test_capture_passes_buffer_descriptor_by_pointer(monkeypatch):
    api, _ = load_api(monkeypatch)
    received = []

    def attach(handle, descriptor):
        descriptor = ctypes.cast(descriptor, ctypes.POINTER(api.DCAMBUF_ATTACH))
        received.append((handle.value, descriptor.contents.buffercount))
        return 1

    monkeypatch.setattr(api, "dcambuf_attach", attach)
    monkeypatch.setattr(api, "dcamcap_start", lambda handle, mode: 1)
    camera = api.DCAM.__new__(api.DCAM)
    camera._DCAM__hdcam = ctypes.c_void_p(0x123456789)
    camera._DCAM__hdcamwait = 0
    # No native device exists in this test; prevent finalization of a fake handle.
    monkeypatch.setattr(api.DCAM, "__del__", lambda self: None)
    frame = (ctypes.c_uint16 * 4)()
    buffer = SimpleNamespace(ctypes=SimpleNamespace(data=ctypes.addressof(frame)))
    assert camera.start_acquisition([buffer], 1)
    assert received == [(0x123456789, 1)]


def test_repeated_close_does_not_unregister_another_camera(monkeypatch):
    api, _ = load_api(monkeypatch)
    camera = api.DCAM.__new__(api.DCAM)
    camera._DCAM__hdcam = ctypes.c_void_p(123)
    camera._DCAM__hdcamwait = 0
    api.camReg.numCameras = 2
    assert camera.dev_close()
    assert camera.dev_close()
    assert api.camReg.numCameras == 1


def test_failed_open_releases_api_registration(monkeypatch):
    api, _ = load_api(monkeypatch)
    api.camReg.numCameras = 1  # Another camera has already initialized DCAM.
    monkeypatch.setattr(api, "dcamdev_open", lambda param: -1)
    camera = api.DCAM.__new__(api.DCAM)
    camera._DCAM__hdcam = 0
    camera._DCAM__hdcamwait = 0
    assert camera.dev_open(0) is False
    assert api.camReg.numCameras == 1


@pytest.fixture
def capture_helpers():
    path = Path(__file__).with_name("test_hamamatsu_single_frame.py")
    spec = importlib.util.spec_from_file_location("navigate.test_capture_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def native_camera_api():
    class Open(ctypes.Structure):
        _fields_ = [("hdcam", ctypes.c_void_p)]

    class Registry:
        numCameras = 0

        @classmethod
        def regCamera(cls):
            cls.numCameras += 1

        @classmethod
        def unregCamera(cls):
            cls.numCameras -= 1

    values = {1: 2.0, 2: 0.01}
    writes = []

    def open_device(param):
        param._obj.hdcam = 123
        return 1

    def get_value(handle, prop, output):
        if prop not in values:
            return -1
        output._obj.value = values[prop]
        return 1

    def set_value(handle, prop, value):
        writes.append((prop, value))
        values[prop] = value
        return 1

    return SimpleNamespace(
        DCAMDEV_OPEN=Open,
        camReg=Registry,
        dcamdev_open=open_device,
        dcamdev_close=lambda handle: 1,
        dcamprop_getvalue=get_value,
        dcamprop_setvalue=set_value,
        values=values,
        writes=writes,
    )


def test_capture_failed_snapshot_never_writes_invalid_values(
    capture_helpers, native_camera_api
):
    api = native_camera_api
    with pytest.raises(AssertionError):
        with capture_helpers.preserve_settings(api, {"sensor": 1, "missing": 999}):
            pytest.fail("Incomplete snapshot must not enter capture")
    assert api.writes == []
    assert api.camReg.numCameras == 0


def test_capture_restores_settings_when_connection_raises(
    capture_helpers, native_camera_api
):
    api = native_camera_api
    with pytest.raises(RuntimeError, match="connection failed"):
        with capture_helpers.preserve_settings(api, {"subarray": 1, "exposure": 2}):
            api.values[1] = 1.0  # Simulate a partial camera constructor.
            raise RuntimeError("connection failed")
    assert api.values == {1: 2.0, 2: 0.01}
    assert api.camReg.numCameras == 0


def test_capture_rejects_failed_zero_offset_read(capture_helpers):
    camera = SimpleNamespace(prop_getvalue=lambda prop: False)
    with pytest.raises(AssertionError):
        capture_helpers.read_property(camera, 0x00420350)


def test_reinitialize_refuses_to_reset_other_open_cameras(monkeypatch):
    api, _ = load_api(monkeypatch)
    monkeypatch.setattr(api.DCAM, "__del__", lambda self: None)
    camera = api.DCAM.__new__(api.DCAM)
    api.camReg.numCameras = 2
    with pytest.raises(RuntimeError, match="only open camera"):
        camera.reinitialize()


def test_reinitialize_restores_settings_including_zero_positions(monkeypatch):
    api, _ = load_api(monkeypatch)
    monkeypatch.setattr(api.DCAM, "__del__", lambda self: None)
    camera = api.DCAM.__new__(api.DCAM)
    camera._DCAM__iDevice = 7
    api.camReg.numCameras = 1
    original = {name: 1.0 for name in api.property_dict}
    original.update(
        sensor_mode=12,
        subarray_hsize=512,
        subarray_vsize=512,
        subarray_hpos=0,
        subarray_vpos=896,
        internal_line_interval=72.96e-6,
        exposure_time=729.6e-6,
        trigger_delay=0,
    )
    state = original.copy()
    events = []
    camera.get_property_value = lambda name: state[name]

    def close():
        events.append("close")
        state.clear()

    def open_device(index):
        assert index == 7
        events.append("open")
        return True

    camera.dev_close = close
    camera.dev_open = open_device
    camera._DCAM__open_hdcamwait = lambda: True
    names_by_id = {prop: name for name, prop in api.property_dict.items()}

    def set_value(prop, value):
        state[names_by_id[prop]] = value
        return True

    camera.prop_setvalue = set_value
    assert camera.reinitialize()
    assert events == ["close", "open"]
    assert state
    assert all(value == original[name] for name, value in state.items())
    assert state["subarray_hpos"] == 0
    assert state["subarray_vpos"] == 896
    assert state["internal_line_interval"] == 72.96e-6
