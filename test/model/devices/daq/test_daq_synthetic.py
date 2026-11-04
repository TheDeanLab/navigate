from navigate.model.devices.daq.synthetic import SyntheticDAQ
import pytest


class _FakeCamera:
    def __init__(self, is_acquiring=True, minimum_frame_interval=0.0):
        self.generate_calls = 0
        self.is_acquiring = is_acquiring
        self.minimum_frame_interval = minimum_frame_interval

    def generate_new_frame(self):
        if self.is_acquiring:
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
    monkeypatch.setattr(
        "navigate.model.devices.daq.synthetic.time.sleep", lambda *_: None
    )

    daq.wait_acquisition_done()

    assert camera_a.generate_calls == 1
    assert camera_b.generate_calls == 1


def test_wait_acquisition_done_external_trigger_skips_camera(monkeypatch):
    daq = SyntheticDAQ(_build_configuration())
    camera = _FakeCamera()
    daq.add_camera("ScopeA", camera)
    daq.trigger_mode = "external-trigger"
    monkeypatch.setattr(
        "navigate.model.devices.daq.synthetic.time.sleep", lambda *_: None
    )

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


@pytest.mark.parametrize(
    "channel, duration", [("channel_1", 0.08), ("channel_2", 0.25)]
)
def test_software_trigger_waits_for_channel_sweep(monkeypatch, channel, duration):
    """Wait for exposure/readout before the next channel changes or trigger."""
    daq = SyntheticDAQ(_build_configuration())
    daq.sweep_times = {"channel_1": 0.08, "channel_2": 0.25}
    daq.prepare_acquisition(channel)
    events = []
    camera = _FakeCamera()
    monkeypatch.setattr(camera, "generate_new_frame", lambda: events.append("trigger"))
    daq.add_camera("ScopeA", camera)
    monkeypatch.setattr(
        "navigate.model.devices.daq.synthetic.time.sleep",
        lambda seconds: events.append(("wait", seconds)),
    )

    daq.run_acquisition()

    assert events == ["trigger", ("wait", duration)]


def test_usb_camera_period_can_exceed_light_sheet_sweep(monkeypatch):
    daq = SyntheticDAQ(_build_configuration())
    daq.sweep_times = {"channel_1": 0.012}
    daq.prepare_acquisition("channel_1")
    camera = _FakeCamera()
    camera.minimum_frame_interval = 0.057
    daq.add_camera("ScopeA", camera)
    sleeps = []
    monkeypatch.setattr(
        "navigate.model.devices.daq.synthetic.time.sleep", sleeps.append
    )
    daq.run_acquisition()
    assert camera.generate_calls == 1
    assert sleeps[0] >= 0.057
    assert daq.sweep_times["channel_1"] == 0.012


@pytest.mark.parametrize(
    "camera_states,sweep,expected_wait",
    [
        ([(True, 0.01), (False, 1.0)], 0.02, 0.02),
        ([(True, 0.02), (True, 0.08), (False, 1.0)], 0.015, 0.084),
        ([(False, 1.0)], 0.02, 0.02),
        ([(False, 1.0)], None, 0.01),
        ([], 0.02, 0.02),
    ],
    ids=["stopped-camera", "multiple-active", "all-stopped", "fallback", "no-cameras"],
)
def test_only_acquiring_cameras_extend_frame_wait(
    monkeypatch, camera_states, sweep, expected_wait
):
    daq = SyntheticDAQ(_build_configuration())
    daq.sweep_times = {} if sweep is None else {"channel_1": sweep}
    daq.prepare_acquisition("channel_1")
    cameras = [_FakeCamera(active, period) for active, period in camera_states]
    for index, camera in enumerate(cameras):
        daq.add_camera(f"Scope{index}", camera)
    sleeps = []
    monkeypatch.setattr(
        "navigate.model.devices.daq.synthetic.time.sleep", sleeps.append
    )

    daq.run_acquisition()

    assert sleeps == pytest.approx([expected_wait])
    assert [camera.generate_calls for camera in cameras] == [
        int(active) for active, _ in camera_states
    ]
