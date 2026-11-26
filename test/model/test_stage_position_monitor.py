"""Idle telemetry scheduling and hardware-operation exclusion."""

import threading
from queue import Queue
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from navigate.model.devices.stage.readback import StagePositionReadback
from navigate.model.stage_position_monitor import (
    StagePositionMonitor,
    suspend_stage_polling,
)


class ReadbackStage(StagePositionReadback):
    def __init__(self, identity=None, positions=None):
        self.identity = identity if identity is not None else self
        self.positions = positions or {"x_pos": 12.345}
        self.read = Mock(side_effect=self._read)

    @property
    def position_readback_identity(self):
        return self.identity

    def _read(self, peers):
        positions = self.positions.copy()
        for peer in peers:
            positions.update(peer.positions)
        return positions

    def read_position_for_monitor(self, peers=()):
        return self.read(peers)


@pytest.fixture
def setup():
    stage = ReadbackStage()
    scope = SimpleNamespace(
        camera=SimpleNamespace(is_acquiring=False),
        stages_list=[(stage, ["x"])],
        ret_pos_dict={"x_pos": -100},
        ask_stage_for_position=False,
        central_focus=42,
    )
    model = SimpleNamespace(
        active_microscope=scope,
        active_microscope_name="scope",
        microscopes={"scope": scope},
        configuration={
            "configuration": {"microscopes": {"scope": {"stage": {}}}},
        },
        is_acquiring=False,
        signal_thread=None,
        data_thread=None,
    )
    now = [100.0]
    output = Queue(1)
    monitor = StagePositionMonitor(model, output, clock=lambda: now[0])
    model._stage_position_monitor = monitor
    return monitor, model, stage, output, now


def test_idle_read_is_fresh_and_does_not_mutate_acquisition_cache(setup):
    monitor, model, stage, output, _ = setup
    monitor.poll_once()
    assert output.get_nowait()["positions"] == {"x_pos": 12.35}
    assert model.active_microscope.ret_pos_dict == {"x_pos": -100}
    assert model.active_microscope.ask_stage_for_position is False
    assert model.active_microscope.central_focus == 42
    stage.read.assert_called_once_with(())


@pytest.mark.parametrize(
    "mode", ["live", "single", "z-stack", "customized", "autofocus"]
)
def test_all_acquisition_modes_disable_polling(setup, mode):
    monitor, model, stage, output, _ = setup
    model.is_acquiring = True
    model.imaging_mode = mode
    monitor.poll_once()
    stage.read.assert_not_called()
    assert output.empty()


@pytest.mark.parametrize(
    "state", ["prepared", "resolution", "signal", "data", "camera"]
)
def test_preparation_workers_and_cleanup_are_not_idle(setup, state):
    monitor, model, stage, _, _ = setup
    if state == "prepared":
        model._prepared_camera_token = (1,)
    elif state == "resolution":
        model._resolution_change_task = object()
    elif state in ("signal", "data"):
        setattr(model, f"{state}_thread", SimpleNamespace(is_alive=lambda: True))
    else:
        model.active_microscope.camera.is_acquiring = True
    monitor.poll_once()
    stage.read.assert_not_called()


def test_nested_operations_and_exceptions_release_suspension(setup):
    monitor, model, stage, _, _ = setup

    @suspend_stage_polling
    def operation(self):
        with monitor.suspended():
            monitor.poll_once()
        monitor.poll_once()
        raise ValueError("operation failed")

    with pytest.raises(ValueError):
        operation(model)
    stage.read.assert_not_called()
    monitor.poll_once()
    stage.read.assert_called_once()


def test_one_second_cadence_and_latest_only_output(setup):
    monitor, _, stage, output, now = setup
    monitor.poll_once()
    now[0] += 0.9
    monitor.poll_once()
    assert stage.read.call_count == 1
    now[0] += 0.1
    stage.positions["x_pos"] = 20
    monitor.poll_once()
    assert stage.read.call_count == 2
    assert output.qsize() == 1
    assert output.get_nowait()["positions"] == {"x_pos": 20}


def test_slow_reads_reduce_duty_cycle(setup):
    monitor, _, stage, _, now = setup

    def slow_read(peers):
        now[0] += 0.1
        return stage.positions

    stage.read.side_effect = slow_read
    monitor.poll_once()
    now[0] = 101.0
    monitor.poll_once()
    assert stage.read.call_count == 1
    now[0] = 102.1
    monitor.poll_once()
    assert stage.read.call_count == 2


@pytest.mark.parametrize(
    "bad_result", [{}, {"x_pos": float("nan")}, {"x_pos": float("inf")}]
)
def test_bad_reads_never_publish_cached_or_invalid_positions(setup, bad_result):
    monitor, _, stage, output, _ = setup
    stage.read.side_effect = None
    stage.read.return_value = bad_result
    monitor.poll_once()
    result = output.get_nowait()
    assert result["positions"] == {}
    assert result["unavailable_axes"] == ["x"]


def test_failures_back_off_then_recover(setup):
    monitor, _, stage, output, now = setup
    stage.read.side_effect = OSError("disconnected")
    monitor.poll_once()
    now[0] = 101
    monitor.poll_once()
    assert stage.read.call_count == 1
    now[0] = 102
    monitor.poll_once()
    assert stage.read.call_count == 2
    now[0] = 105
    monitor.poll_once()
    assert stage.read.call_count == 2
    stage.read.side_effect = stage._read
    now[0] = 106
    monitor.poll_once()
    assert output.get_nowait()["positions"] == {"x_pos": 12.35}


def test_shared_connection_gets_one_grouped_query(setup):
    monitor, model, stage, output, _ = setup
    peer = ReadbackStage(stage.identity, {"y_pos": 44})
    model.active_microscope.stages_list += [(stage, ["x"]), (peer, ["y"])]
    monitor.poll_once()
    stage.read.assert_called_once_with((peer,))
    peer.read.assert_not_called()
    assert output.get_nowait()["positions"] == {"x_pos": 12.35, "y_pos": 44}


@pytest.mark.parametrize("disabled", [True, False])
def test_disabled_and_unsupported_devices_are_not_queried(setup, disabled):
    monitor, model, stage, output, _ = setup
    if disabled:
        model.configuration["configuration"]["microscopes"]["scope"]["stage"][
            "position_polling"
        ] = False
    else:
        model.active_microscope.stages_list = [(object(), ["x"])]
    monitor.poll_once()
    stage.read.assert_not_called()
    assert output.get_nowait()["unavailable_axes"] == ["x"]


def test_operation_waits_for_current_read_and_discards_its_result(setup):
    monitor, model, stage, output, _ = setup
    other = ReadbackStage(positions={"y_pos": 3})
    model.active_microscope.stages_list.append((other, ["y"]))
    reading = threading.Event()
    release = threading.Event()
    entered = threading.Event()
    operation_requested = threading.Event()

    def read(peers):
        reading.set()
        assert release.wait(5)
        return stage.positions

    def operation():
        with monitor.suspended():
            entered.set()

    # Instrument the condition's wait to deterministically observe the suspension.
    original_wait = monitor._condition.wait

    def wait(*args):
        operation_requested.set()
        return original_wait(*args)

    monitor._condition.wait = wait
    stage.read.side_effect = read
    reader = threading.Thread(target=monitor.poll_once)
    worker = threading.Thread(target=operation)
    reader.start()
    assert reading.wait(5)
    worker.start()
    try:
        assert operation_requested.wait(5)
        assert not entered.is_set()
    finally:
        release.set()
        reader.join(5)
        worker.join(5)
    assert not reader.is_alive() and not worker.is_alive()
    assert entered.is_set()
    other.read.assert_not_called()
    assert output.empty()


def test_shutdown_wakes_sleeping_worker_and_is_idempotent(setup):
    monitor, _, stage, _, _ = setup
    monitor.start()
    monitor.close()
    monitor.close()
    monitor.start()
    assert not monitor._thread.is_alive()
    monitor.poll_once()
    stage.read.assert_not_called()


def test_shutdown_finishes_read_before_hardware_can_be_closed(setup):
    monitor, _, stage, output, _ = setup
    reading = threading.Event()
    release = threading.Event()
    closed = threading.Event()

    def read(peers):
        reading.set()
        assert release.wait(5)
        assert not closed.is_set()
        return stage.positions

    stage.read.side_effect = read
    monitor._thread = threading.Thread(target=monitor.poll_once)
    monitor._thread.start()
    assert reading.wait(5)

    def close_devices():
        monitor.close()
        closed.set()

    closer = threading.Thread(target=close_devices)
    closer.start()
    try:
        assert monitor._stop.wait(5)
        assert not closed.is_set()
    finally:
        release.set()
        closer.join(5)
    assert not closer.is_alive()
    assert closed.is_set()
    assert output.empty()


def test_microscope_change_preserves_shared_connection_rate_limit(setup):
    monitor, model, stage, output, now = setup
    monitor.poll_once()
    peer = ReadbackStage(stage.identity, {"y_pos": 55})
    other = SimpleNamespace(
        stages_list=[(peer, ["y"])], camera=SimpleNamespace(is_acquiring=False)
    )
    with monitor.suspended():
        model.active_microscope = other
        model.active_microscope_name = "other"
        model.microscopes["other"] = other
        model.configuration["configuration"]["microscopes"]["other"] = {"stage": {}}
    now[0] += 0.5
    monitor.poll_once()
    peer.read.assert_not_called()
    now[0] += 0.5
    monitor.poll_once()
    assert output.get_nowait()["microscope_name"] == "other"
    peer.read.assert_called_once()
