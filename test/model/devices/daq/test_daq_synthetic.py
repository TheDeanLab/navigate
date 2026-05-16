from navigate.model.devices.daq.synthetic import SyntheticDAQ


class _FakeCamera:
    def __init__(self):
        self.generate_calls = 0

    def generate_new_frame(self):
        self.generate_calls += 1


class _FakeLock:
    def __init__(self, locked=False):
        self._locked = locked
        self.acquire_calls = 0
        self.release_calls = 0

    def acquire(self):
        self.acquire_calls += 1
        self._locked = True

    def release(self):
        self.release_calls += 1
        self._locked = False

    def locked(self):
        return self._locked


def _build_configuration():
    return {
        "waveform_constants": {"other_constants": {"camera_delay": 5}},
        "experiment": {
            "MicroscopeState": {
                "microscope_name": "ScopeA",
                "channels": {"channel_1": {"is_selected": True}},
            }
        },
        "configuration": {"microscopes": {"ScopeA": {"daq": {"sample_rate": 1000}}}},
    }


def test_initialize_daq_synthetic():
    daq = SyntheticDAQ(_build_configuration())
    assert str(daq) == "SyntheticDAQ"
    assert daq.trigger_mode == "self-trigger"


def test_add_camera_and_wait_acquisition_self_trigger(monkeypatch):
    daq = SyntheticDAQ(_build_configuration())
    camera_a = _FakeCamera()
    camera_b = _FakeCamera()
    daq.add_camera("ScopeA", camera_a)
    daq.add_camera("ScopeB", camera_b)
    monkeypatch.setattr("navigate.model.devices.daq.synthetic.time.sleep", lambda *_: None)

    daq.wait_acquisition_done()

    assert camera_a.generate_calls == 1
    assert camera_b.generate_calls == 1


def test_wait_acquisition_done_external_trigger_skips_camera(monkeypatch):
    daq = SyntheticDAQ(_build_configuration())
    camera = _FakeCamera()
    daq.add_camera("ScopeA", camera)
    daq.trigger_mode = "external-trigger"
    monkeypatch.setattr("navigate.model.devices.daq.synthetic.time.sleep", lambda *_: None)

    daq.wait_acquisition_done()

    assert camera.generate_calls == 0


def test_prepare_acquisition_releases_wait_lock():
    daq = SyntheticDAQ(_build_configuration())
    daq.wait_to_run_lock.acquire()
    daq.is_updating_analog_task = True

    daq.prepare_acquisition("channel_1")

    assert daq.current_channel_key == "channel_1"
    assert daq.is_updating_analog_task is False
    assert not daq.wait_to_run_lock.locked()


def test_run_acquisition_waits_for_update_and_calls_wait(monkeypatch):
    daq = SyntheticDAQ(_build_configuration())
    fake_lock = _FakeLock()
    daq.wait_to_run_lock = fake_lock
    daq.is_updating_analog_task = True
    called = {"wait": 0}
    monkeypatch.setattr(
        daq,
        "wait_acquisition_done",
        lambda: called.__setitem__("wait", called["wait"] + 1),
    )

    daq.run_acquisition(wait_until_done=True)

    assert fake_lock.acquire_calls == 1
    assert fake_lock.release_calls == 1
    assert called["wait"] == 1


def test_run_acquisition_without_wait_skips_wait_call(monkeypatch):
    daq = SyntheticDAQ(_build_configuration())
    called = {"wait": 0}
    monkeypatch.setattr(
        daq,
        "wait_acquisition_done",
        lambda: called.__setitem__("wait", called["wait"] + 1),
    )

    daq.run_acquisition(wait_until_done=False)

    assert called["wait"] == 0


def test_update_analog_task_busy_returns_false():
    daq = SyntheticDAQ(_build_configuration())
    daq.is_updating_analog_task = True

    assert daq.update_analog_task("Dev1") is False


def test_update_analog_task_successful_transition():
    daq = SyntheticDAQ(_build_configuration())
    fake_lock = _FakeLock()
    daq.wait_to_run_lock = fake_lock
    daq.is_updating_analog_task = False

    assert daq.update_analog_task("Dev1") is True
    assert daq.is_updating_analog_task is False
    assert fake_lock.acquire_calls == 1
    assert fake_lock.release_calls == 1


def test_stop_acquisition_is_noop():
    daq = SyntheticDAQ(_build_configuration())
    daq.stop_acquisition()
