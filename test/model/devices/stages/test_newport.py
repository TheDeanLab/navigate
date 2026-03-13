import pytest
import sys
import types

import navigate.model.devices.stage.base as stage_base_module

if "telnetlib" not in sys.modules:
    telnetlib_stub = types.ModuleType("telnetlib")

    class _UnavailableTelnet:
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError("telnetlib unavailable in this Python runtime")

    telnetlib_stub.Telnet = _UnavailableTelnet
    sys.modules["telnetlib"] = telnetlib_stub

import navigate.model.devices.stage.newport as newport_module


def _build_newport_configuration(axes=("x", "y"), axes_mapping=(1, 2)):
    stage_block = {
        "hardware": [
            {
                "name": "newport",
                "type": "ESP302",
                "port": "10.0.0.2",
                "baudrate": 5001,
                "axes": list(axes),
                "axes_mapping": list(axes_mapping),
            }
        ]
    }
    for axis in axes:
        stage_block[f"{axis}_min"] = -1000
        stage_block[f"{axis}_max"] = 1000

    return {
        "configuration": {
            "microscopes": {
                "scope": {
                    "stage": stage_block,
                }
            }
        }
    }


class _FakeTelnet:
    def __init__(self, read_exception=None):
        self.read_exception = read_exception
        self.closed = False
        self.writes = []
        self.read_queue = []

    def write(self, data):
        self.writes.append(data)

    def read_until(self, _expected, timeout=None):
        if self.read_exception is not None:
            raise self.read_exception
        if self.read_queue:
            return self.read_queue.pop(0)
        return b"\r\n"

    def close(self):
        self.closed = True


class _FakeNewportDevice:
    def __init__(self):
        self.positions = {1: 10.0, 2: 20.0, 3: 30.0}
        self.home_calls = []
        self.motor_calls = []
        self.move_calls = []
        self.stop_calls = []
        self.disconnect_calls = 0
        self.fail_home = False
        self.fail_get = False
        self.fail_move = False
        self.fail_stop = False

    def home_axis(self, axis, wait=True):
        self.home_calls.append((axis, wait))
        if self.fail_home:
            raise newport_module.NewportESP302Error("home failed")

    def motor_on(self, axis):
        self.motor_calls.append(axis)

    def get_position(self, axis):
        if self.fail_get:
            raise newport_module.NewportESP302Error("read failed")
        return self.positions[axis]

    def move_absolute(self, axis, position, wait=True):
        self.move_calls.append((axis, position, wait))
        if self.fail_move:
            raise newport_module.NewportESP302Error("move failed")
        self.positions[axis] = position

    def stop_motion(self, axis):
        self.stop_calls.append(axis)
        if self.fail_stop:
            raise newport_module.NewportESP302Error("stop failed")

    def disconnect(self):
        self.disconnect_calls += 1


@pytest.fixture(autouse=True)
def _patch_listproxy(monkeypatch):
    monkeypatch.setattr(stage_base_module, "ListProxy", list)


def test_newport_api_connect_success_even_if_banner_read_hits_eof(monkeypatch):
    fake_tn = _FakeTelnet(read_exception=EOFError("no banner"))
    monkeypatch.setattr(
        newport_module.telnetlib,
        "Telnet",
        lambda host, port, timeout: fake_tn,
    )
    api = newport_module.NewportESP302API("10.0.0.2", port=5001, timeout=3)

    assert api.connect() is True
    assert api.tn is fake_tn


def test_newport_api_connect_failure_raises_custom_error(monkeypatch):
    def raise_connect_error(*_args, **_kwargs):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(newport_module.telnetlib, "Telnet", raise_connect_error)
    api = newport_module.NewportESP302API("10.0.0.2", port=5001, timeout=3)

    with pytest.raises(newport_module.NewportESP302Error, match="Failed to connect"):
        api.connect()


def test_newport_api_send_and_read_requires_connection():
    api = newport_module.NewportESP302API("10.0.0.2", port=5001, timeout=3)

    with pytest.raises(newport_module.NewportESP302Error, match="Not connected"):
        api._send_and_read("1TP?")


def test_newport_api_send_and_read_handles_eof_and_disconnects():
    api = newport_module.NewportESP302API("10.0.0.2", port=5001, timeout=3)
    fake_tn = _FakeTelnet(read_exception=EOFError("peer closed"))
    api.tn = fake_tn

    with pytest.raises(
        newport_module.NewportESP302Error, match="Connection closed by controller"
    ):
        api._send_and_read("1TP?")

    assert fake_tn.closed is True
    assert api.tn is None


def test_newport_api_send_and_read_handles_generic_telnet_errors():
    class _BrokenTelnet:
        def write(self, _):
            raise RuntimeError("write failure")

    api = newport_module.NewportESP302API("10.0.0.2", port=5001, timeout=3)
    api.tn = _BrokenTelnet()

    with pytest.raises(newport_module.NewportESP302Error, match="Telnet error"):
        api._send_and_read("1TP?")


def test_newport_api_check_controller_error_raises_on_nonzero_code(monkeypatch):
    api = newport_module.NewportESP302API("10.0.0.2", port=5001, timeout=3)
    monkeypatch.setattr(api, "_send_and_read", lambda *_: "7")

    with pytest.raises(newport_module.NewportESP302Error, match="error code: 7"):
        api.check_controller_error()


def test_newport_api_check_controller_error_swallow_transport_failure(monkeypatch):
    api = newport_module.NewportESP302API("10.0.0.2", port=5001, timeout=3)

    def raise_transport(*_):
        raise newport_module.NewportESP302Error("transport read failed")

    monkeypatch.setattr(api, "_send_and_read", raise_transport)
    api.check_controller_error()


def test_newport_api_get_position_parse_failure(monkeypatch):
    api = newport_module.NewportESP302API("10.0.0.2", port=5001, timeout=3)
    check_calls = []
    monkeypatch.setattr(api, "_send_and_read", lambda *_: "not-a-float")
    monkeypatch.setattr(api, "check_controller_error", lambda: check_calls.append(True))

    with pytest.raises(
        newport_module.NewportESP302Error, match="Could not parse position"
    ):
        api.get_position(axis=1)

    assert check_calls == [True]


def test_newport_api_move_absolute_respects_wait_flag(monkeypatch):
    api = newport_module.NewportESP302API("10.0.0.2", port=5001, timeout=3)
    commands = []
    check_calls = []
    wait_calls = []
    monkeypatch.setattr(api, "_send_and_read", lambda cmd: commands.append(cmd) or "")
    monkeypatch.setattr(api, "check_controller_error", lambda: check_calls.append(True))
    monkeypatch.setattr(
        api, "wait_for_motion_to_stop", lambda axis: wait_calls.append(axis)
    )

    api.move_absolute(axis=2, position=12.5, wait=False)
    assert commands == ["2PA12.5"]
    assert check_calls == [True]
    assert wait_calls == []

    api.move_absolute(axis=2, position=8.0, wait=True)
    assert commands == ["2PA12.5", "2PA8.0"]
    assert check_calls == [True, True]
    assert wait_calls == [2]


def test_newport_api_wait_for_motion_to_stop_timeout_calls_stop(monkeypatch):
    api = newport_module.NewportESP302API("10.0.0.2", port=5001, timeout=3)
    stop_calls = []
    monkeypatch.setattr(api, "is_motion_done", lambda axis: False)
    monkeypatch.setattr(api, "stop_motion", lambda axis: stop_calls.append(axis))
    time_values = iter([0, 61])
    monkeypatch.setattr(newport_module.time, "time", lambda: next(time_values))

    with pytest.raises(
        newport_module.NewportESP302Error,
        match="Timeout waiting for motion to stop on axis 1",
    ):
        api.wait_for_motion_to_stop(axis=1, timeout_sec=60)

    assert stop_calls == [1]


def test_newport_api_wait_for_motion_to_stop_success_checks_error(monkeypatch):
    api = newport_module.NewportESP302API("10.0.0.2", port=5001, timeout=3)
    done_states = iter([False, True])
    check_calls = []
    monkeypatch.setattr(api, "is_motion_done", lambda axis: next(done_states))
    monkeypatch.setattr(newport_module.time, "sleep", lambda *_: None)
    monkeypatch.setattr(api, "check_controller_error", lambda: check_calls.append(True))

    api.wait_for_motion_to_stop(axis=2, timeout_sec=60)
    assert check_calls == [True]


def test_newport_api_home_axis_wait_flag(monkeypatch):
    api = newport_module.NewportESP302API("10.0.0.2", port=5001, timeout=3)
    commands = []
    waits = []
    monkeypatch.setattr(api, "_send_and_read", lambda cmd: commands.append(cmd) or "")
    monkeypatch.setattr(api, "check_controller_error", lambda: None)
    monkeypatch.setattr(
        api,
        "wait_for_motion_to_stop",
        lambda axis, timeout_sec=0: waits.append((axis, timeout_sec)),
    )

    api.home_axis(axis=3, wait=False)
    assert commands == ["3OR"]
    assert waits == []

    api.home_axis(axis=3, wait=True)
    assert commands == ["3OR", "3OR"]
    assert waits == [(3, 1000)]


def test_newport_stage_init_requires_connection():
    with pytest.raises(
        UserWarning, match="Newport ESP302 stage connection object is missing"
    ):
        newport_module.NewportStage("scope", None, _build_newport_configuration())


def test_newport_stage_init_invalid_axes_mapping_raises():
    config = _build_newport_configuration(axes=("x", "y"), axes_mapping=("1", "bad"))

    with pytest.raises(UserWarning, match="axes_mapping in YAML must be a list"):
        newport_module.NewportStage("scope", _FakeNewportDevice(), config)


def test_newport_stage_init_failure_during_homing_raises():
    config = _build_newport_configuration(axes=("x", "y"), axes_mapping=(1, 2))
    device = _FakeNewportDevice()
    device.fail_home = True

    with pytest.raises(UserWarning, match="Failed to initialize Newport stage"):
        newport_module.NewportStage("scope", device, config)


def test_newport_stage_init_and_report_position_success():
    config = _build_newport_configuration(axes=("x", "y"), axes_mapping=(1, 2))
    device = _FakeNewportDevice()
    stage = newport_module.NewportStage("scope", device, config)

    assert stage.axes_mapping == {"x": 1, "y": 2}
    assert device.home_calls == [(1, True), (2, True)]
    assert device.motor_calls == [1, 2]
    assert stage.report_position() == {"x_pos": 10.0, "y_pos": 20.0}


def test_newport_stage_report_position_error_returns_cached_values():
    config = _build_newport_configuration(axes=("x", "y"), axes_mapping=(1, 2))
    device = _FakeNewportDevice()
    stage = newport_module.NewportStage("scope", device, config)

    baseline = stage.report_position()
    device.fail_get = True
    assert stage.report_position() == baseline


def test_newport_stage_move_axis_invalid_returns_false():
    stage = newport_module.NewportStage(
        "scope",
        _FakeNewportDevice(),
        _build_newport_configuration(axes=("x", "y"), axes_mapping=(1, 2)),
    )

    assert stage.move_axis_absolute("z", 10.0) is False


def test_newport_stage_move_absolute_out_of_bounds_returns_false():
    stage = newport_module.NewportStage(
        "scope",
        _FakeNewportDevice(),
        _build_newport_configuration(axes=("x",), axes_mapping=(1,)),
    )

    assert stage.move_absolute({"x_abs": 2000.0}) is False


def test_newport_stage_move_absolute_failure_path():
    config = _build_newport_configuration(axes=("x", "y"), axes_mapping=(1, 2))
    device = _FakeNewportDevice()
    stage = newport_module.NewportStage("scope", device, config)
    device.fail_move = True

    assert stage.move_absolute({"x_abs": 12.3}, wait_until_done=False) is False
    assert device.move_calls == [(1, 12.3, False)]


def test_newport_stage_stop_swallows_errors():
    stage = newport_module.NewportStage(
        "scope",
        _FakeNewportDevice(),
        _build_newport_configuration(axes=("x", "y"), axes_mapping=(1, 2)),
    )
    stage.stage.fail_stop = True

    stage.stop()
    assert stage.stage.stop_calls == [1]


def test_newport_stage_connect_success(monkeypatch):
    created = {}

    class _FakeAPI:
        def __init__(self, host, port, timeout, logger_func=None):
            created["init"] = (host, port, timeout)

        def connect(self):
            created["connected"] = True

    monkeypatch.setattr(newport_module, "NewportESP302API", _FakeAPI)
    api = newport_module.NewportStage.connect("192.168.0.7", baudrate=5001, timeout=9)

    assert isinstance(api, _FakeAPI)
    assert created["init"] == ("192.168.0.7", 5001, 9)
    assert created["connected"] is True


def test_newport_stage_connect_error_wrapped(monkeypatch):
    class _FakeAPI:
        def __init__(self, *args, **kwargs):
            pass

        def connect(self):
            raise newport_module.NewportESP302Error("offline")

    monkeypatch.setattr(newport_module, "NewportESP302API", _FakeAPI)

    with pytest.raises(
        UserWarning, match="Could not communicate with Newport ESP302 at 192.168.0.7:5001"
    ):
        newport_module.NewportStage.connect("192.168.0.7", baudrate=5001, timeout=9)
