import pytest

import navigate.model.devices.stage.base as stage_base_module
import navigate.model.devices.stage.conex as conex_module


def _build_conex_configuration():
    return {
        "configuration": {
            "microscopes": {
                "scope": {
                    "stage": {
                        "hardware": [
                            {
                                "name": "conex",
                                "type": "CONEX",
                                "port": "COM9",
                                "baudrate": 921600,
                                "axes": ["x"],
                                "axes_mapping": ["X"],
                            }
                        ],
                        "x_min": -5000,
                        "x_max": 50000,
                    }
                }
            }
        }
    }


class _FakeSerial:
    def __init__(
        self,
        responses=None,
        write_exception=None,
        readline_exception=None,
    ):
        self.responses = list(responses or [])
        self.write_exception = write_exception
        self.readline_exception = readline_exception
        self.writes = []
        self.reset_calls = 0
        self.closed = False
        self.is_open = True

    def reset_input_buffer(self):
        self.reset_calls += 1

    def write(self, data):
        if self.write_exception is not None:
            raise self.write_exception
        self.writes.append(data)

    def readline(self):
        if self.readline_exception is not None:
            raise self.readline_exception
        if self.responses:
            return self.responses.pop(0)
        return b""

    def close(self):
        self.closed = True
        self.is_open = False


class _FakeConexDevice:
    def __init__(self):
        self.position_mm = 1.25
        self.fail_get = False
        self.fail_move = False
        self.fail_stop = False
        self.move_calls = []
        self.stop_calls = 0
        self.disconnect_calls = 0

    def get_position(self):
        if self.fail_get:
            raise conex_module.ConexCCError("read failure")
        return self.position_mm

    def move_absolute(self, position, wait=True):
        self.move_calls.append((position, wait))
        if self.fail_move:
            raise conex_module.ConexCCError("move failure")
        self.position_mm = position

    def stop_motion(self):
        self.stop_calls += 1
        if self.fail_stop:
            raise conex_module.ConexCCError("stop failure")

    def disconnect(self):
        self.disconnect_calls += 1


@pytest.fixture(autouse=True)
def _patch_listproxy(monkeypatch):
    monkeypatch.setattr(stage_base_module, "ListProxy", list)


def test_conex_api_connect_success(monkeypatch):
    created = {}

    def fake_serial_ctor(**kwargs):
        created["kwargs"] = kwargs
        created["serial"] = _FakeSerial(responses=[b"1VE 2.4.6\r\n"])
        return created["serial"]

    monkeypatch.setattr(conex_module, "Serial", fake_serial_ctor)
    api = conex_module.ConexCCAPI("COM9")

    assert api.connect() is True
    assert created["kwargs"]["port"] == "COM9"
    assert created["kwargs"]["baudrate"] == 921600
    assert created["serial"].writes == [b"1VE?\r\n"]


def test_conex_api_connect_rejects_empty_version(monkeypatch):
    fake_serial = _FakeSerial(responses=[b"\r\n"])
    monkeypatch.setattr(conex_module, "Serial", lambda **_: fake_serial)
    api = conex_module.ConexCCAPI("COM7")

    with pytest.raises(conex_module.ConexCCError, match="Failed to verify version"):
        api.connect()

    assert api.ser is None
    assert fake_serial.closed is True


def test_conex_api_connect_permission_error(monkeypatch):
    def raise_permission(**_):
        raise conex_module.SerialException("PermissionError: busy")

    monkeypatch.setattr(conex_module, "Serial", raise_permission)
    api = conex_module.ConexCCAPI("COM11")

    with pytest.raises(conex_module.ConexCCError, match="Port may be in use"):
        api.connect()


def test_conex_api_connect_generic_serial_error(monkeypatch):
    monkeypatch.setattr(
        conex_module,
        "Serial",
        lambda **_: (_ for _ in ()).throw(conex_module.SerialException("boom")),
    )
    api = conex_module.ConexCCAPI("COM12")

    with pytest.raises(conex_module.ConexCCError, match="Failed to connect to COM12"):
        api.connect()


def test_conex_api_query_requires_connection():
    api = conex_module.ConexCCAPI("COM3")

    with pytest.raises(conex_module.ConexCCError, match="Not connected"):
        api.query("VE?")


def test_conex_api_query_disconnects_on_serial_error():
    api = conex_module.ConexCCAPI("COM8")
    serial_obj = _FakeSerial(write_exception=conex_module.SerialException("io error"))
    api.ser = serial_obj

    with pytest.raises(conex_module.ConexCCError, match="Serial communication error"):
        api.query("TP?")

    assert api.ser is None
    assert serial_obj.closed is True


def test_conex_api_get_position_parse_failure(monkeypatch):
    api = conex_module.ConexCCAPI("COM5")
    monkeypatch.setattr(api, "query", lambda *_: "1TPnot-a-float")

    with pytest.raises(conex_module.ConexCCError, match="Could not parse position"):
        api.get_position()


def test_conex_api_get_status_handles_known_and_unknown_codes(monkeypatch):
    api = conex_module.ConexCCAPI("COM5")

    monkeypatch.setattr(api, "query", lambda *_: "1TS123432")
    status = api.get_status()
    assert status["raw_state_code"] == "32"
    assert status["state"] == "READY (Err: 1234)"

    monkeypatch.setattr(api, "query", lambda *_: "1TS9999ZZ")
    status = api.get_status()
    assert status["raw_state_code"] == "ZZ"
    assert status["state"] == "Unknown(ZZ) (Err: 9999)"

    monkeypatch.setattr(api, "query", lambda *_: "")
    status = api.get_status()
    assert status == {"state": "Unknown", "raw_state_code": None}


def test_conex_api_initialize_controller_homes_until_ready(monkeypatch):
    api = conex_module.ConexCCAPI("COM4")
    issued_commands = []
    states = iter(
        [
            {"raw_state_code": "0A"},
            {"raw_state_code": "1E"},
            {"raw_state_code": "32"},
        ]
    )
    monkeypatch.setattr(api, "get_status", lambda: next(states))
    monkeypatch.setattr(api, "query", lambda cmd: issued_commands.append(cmd) or "")
    monkeypatch.setattr(conex_module.time, "sleep", lambda _: None)

    api.initialize_controller()

    assert issued_commands == ["HT0", "OR"]


def test_conex_api_initialize_controller_timeout(monkeypatch):
    api = conex_module.ConexCCAPI("COM4")
    states = iter(
        [
            {"raw_state_code": "0A"},
            {"raw_state_code": "1E"},
        ]
    )
    monkeypatch.setattr(api, "get_status", lambda: next(states))
    monkeypatch.setattr(api, "query", lambda *_: "")
    monkeypatch.setattr(conex_module.time, "sleep", lambda *_: None)
    time_values = iter([0, 61])
    monkeypatch.setattr(conex_module.time, "time", lambda: next(time_values))

    with pytest.raises(
        conex_module.ConexCCError, match="Timeout waiting for controller to become READY"
    ):
        api.initialize_controller()


def test_conex_api_wait_for_motion_to_stop_timeout_calls_stop(monkeypatch):
    api = conex_module.ConexCCAPI("COM6")
    stop_calls = []
    monkeypatch.setattr(api, "is_motion_done", lambda: False)
    monkeypatch.setattr(api, "stop_motion", lambda: stop_calls.append(True))
    time_values = iter([0, 61])
    monkeypatch.setattr(conex_module.time, "time", lambda: next(time_values))

    with pytest.raises(
        conex_module.ConexCCError, match="Timeout waiting for motion to stop"
    ):
        api.wait_for_motion_to_stop(timeout_sec=60)

    assert stop_calls == [True]


def test_conex_api_move_absolute_respects_wait_flag(monkeypatch):
    api = conex_module.ConexCCAPI("COM6")
    sent_commands = []
    wait_calls = []
    monkeypatch.setattr(api, "query", lambda cmd: sent_commands.append(cmd) or "")
    monkeypatch.setattr(api, "wait_for_motion_to_stop", lambda: wait_calls.append(True))

    api.move_absolute(12.3, wait=False)
    assert sent_commands == ["PA12.3"]
    assert wait_calls == []

    api.move_absolute(8.1, wait=True)
    assert sent_commands == ["PA12.3", "PA8.1"]
    assert wait_calls == [True]


def test_conex_stage_init_requires_connection():
    with pytest.raises(
        UserWarning, match="CONEX-CC stage connection object is missing"
    ):
        conex_module.ConexStage("scope", None, _build_conex_configuration())


def test_conex_stage_report_position_success_and_failure():
    device = _FakeConexDevice()
    stage = conex_module.ConexStage("scope", device, _build_conex_configuration())

    assert stage.x_pos == 1250.0
    device.position_mm = 2.0
    assert stage.report_position() == {"x_pos": 2000.0}

    device.fail_get = True
    assert stage.report_position() == {}
    assert stage.x_pos == 2000.0


def test_conex_stage_move_axis_invalid_returns_false():
    stage = conex_module.ConexStage(
        "scope", _FakeConexDevice(), _build_conex_configuration()
    )

    assert stage.move_axis_absolute("y", 100.0) is False


def test_conex_stage_move_absolute_out_of_bounds_returns_false():
    stage = conex_module.ConexStage(
        "scope", _FakeConexDevice(), _build_conex_configuration()
    )

    assert stage.move_absolute({"x_abs": 999999.0}) is False


def test_conex_stage_move_absolute_handles_missing_target_axis(monkeypatch):
    device = _FakeConexDevice()
    stage = conex_module.ConexStage("scope", device, _build_conex_configuration())
    monkeypatch.setattr(stage, "verify_abs_position", lambda *_: {"y": 123.0})

    assert stage.move_absolute({"x_abs": 1000.0}) is True
    assert device.move_calls == []


def test_conex_stage_move_absolute_failure_path():
    device = _FakeConexDevice()
    stage = conex_module.ConexStage("scope", device, _build_conex_configuration())
    device.fail_move = True

    assert stage.move_absolute({"x_abs": 3000.0}, wait_until_done=False) is False
    assert device.move_calls == [(3.0, False)]


def test_conex_stage_stop_swallows_errors():
    device = _FakeConexDevice()
    stage = conex_module.ConexStage("scope", device, _build_conex_configuration())
    device.fail_stop = True

    stage.stop()
    assert device.stop_calls == 1


def test_conex_stage_connect_success(monkeypatch):
    calls = []

    class _FakeAPI:
        def __init__(self, port, logger_func=None):
            self.port = port
            self.logger_func = logger_func

        def connect(self):
            calls.append("connect")

        def initialize_controller(self):
            calls.append("init")

    monkeypatch.setattr(conex_module, "ConexCCAPI", _FakeAPI)
    api = conex_module.ConexStage.connect("COM22", baud_rate=9600, timeout=5.0)

    assert isinstance(api, _FakeAPI)
    assert api.port == "COM22"
    assert calls == ["connect", "init"]


def test_conex_stage_connect_permission_error_is_reworded(monkeypatch):
    class _FakeAPI:
        def __init__(self, *args, **kwargs):
            pass

        def connect(self):
            raise conex_module.ConexCCError("PermissionError: denied")

        def initialize_controller(self):
            pass

    monkeypatch.setattr(conex_module, "ConexCCAPI", _FakeAPI)

    with pytest.raises(UserWarning, match="Could not open COM port COM22"):
        conex_module.ConexStage.connect("COM22", baud_rate=9600, timeout=5.0)


def test_conex_stage_connect_generic_error(monkeypatch):
    class _FakeAPI:
        def __init__(self, *args, **kwargs):
            pass

        def connect(self):
            raise conex_module.ConexCCError("offline")

        def initialize_controller(self):
            pass

    monkeypatch.setattr(conex_module, "ConexCCAPI", _FakeAPI)

    with pytest.raises(UserWarning, match="Could not communicate with CONEX-CC"):
        conex_module.ConexStage.connect("COM22", baud_rate=9600, timeout=5.0)
