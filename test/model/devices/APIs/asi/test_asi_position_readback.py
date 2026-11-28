"""Strict, low-priority ASI telemetry using emulated serial responses."""

from unittest.mock import MagicMock

import pytest

from navigate.model.devices.APIs.asi.asi_MS2000_controller import MS2000Controller
from navigate.model.devices.APIs.asi.asi_tiger_controller import (
    ASIException,
    TigerController,
)
from navigate.model.devices.stage.asi import ASIStage


@pytest.fixture(params=[TigerController, MS2000Controller])
def adapter(request):
    controller = request.param("unused", 115200)
    controller.default_axes_sequence = ["X", "Y", "Z"]
    controller.serial = MagicMock()
    controller.serial.timeout = 1.0
    controller.serial.write_timeout = 1.0
    controller.serial.write.side_effect = len
    controller.serial.read_until.return_value = b":A 100 200\r\n"
    return controller


def test_query_uses_one_transaction_in_hardware_axis_order(adapter):
    assert adapter.try_position_readback(["Y", "X"]) == {"X": 100, "Y": 200}
    adapter.serial.write.assert_called_once_with(b"WHERE X Y\r")
    adapter.serial.read_until.assert_called_once_with(b"\n", 256)
    assert adapter.serial.timeout == 1
    assert adapter.serial.write_timeout == 1
    assert adapter.safe_to_write.is_set()


@pytest.mark.parametrize("timeout", [None, 0, -1, 2, float("inf"), float("nan")])
@pytest.mark.parametrize("setting", ["timeout", "write_timeout"])
def test_unbounded_or_incompatible_timeout_is_not_polled(adapter, timeout, setting):
    setattr(adapter.serial, setting, timeout)
    assert adapter.try_position_readback(["X"]) is None
    adapter.serial.write.assert_not_called()
    assert adapter.safe_to_write.is_set()


def test_busy_connection_is_skipped_without_waiting(adapter):
    adapter._begin_transaction()
    try:
        assert adapter.try_position_readback(["X"]) is None
        adapter.serial.write.assert_not_called()
        assert not adapter.safe_to_write.is_set()
    finally:
        adapter._end_transaction()


def test_pending_ordinary_command_has_priority(adapter):
    adapter._transaction_waiters = 1
    assert adapter.try_position_readback(["X"]) is None
    adapter.serial.write.assert_not_called()


@pytest.mark.parametrize(
    "reply",
    [b"", b":A 1", b":A 1\r\n", b":N -1\r\n", b":A nan 2\r\n", b":A 1 2 3\r\n"],
)
def test_invalid_or_incomplete_reply_raises_and_unlocks(adapter, reply):
    adapter.serial.read_until.return_value = reply
    with pytest.raises(ASIException):
        adapter.try_position_readback(["X", "Y"])
    assert adapter.safe_to_write.is_set()
    assert adapter._transaction_lock.acquire(False)
    adapter._transaction_lock.release()


@pytest.mark.parametrize("method", ["write", "read_until", "reset_input_buffer"])
def test_serial_failure_releases_transaction(adapter, method):
    getattr(adapter.serial, method).side_effect = OSError("disconnected")
    with pytest.raises(OSError):
        adapter.try_position_readback(["X", "Y"])
    assert adapter.safe_to_write.is_set()
    assert adapter._transaction_lock.acquire(False)
    adapter._transaction_lock.release()


def test_partial_write_is_failure(adapter):
    adapter.serial.write.side_effect = lambda command: 1
    with pytest.raises(ASIException):
        adapter.try_position_readback(["X", "Y"])
    adapter.serial.read_until.assert_not_called()


def test_shared_stage_wrappers_group_axes_and_preserve_cached_positions(adapter):
    stage = ASIStage.__new__(ASIStage)
    peer = ASIStage.__new__(ASIStage)
    stage.asi_controller = peer.asi_controller = adapter
    stage.asi_axes = {"X": "x"}
    peer.asi_axes = {"Y": "theta"}
    stage.x_pos = -99
    peer.theta_pos = -5
    try:
        assert stage.read_position_for_monitor((peer,)) == {
            "x_pos": 10,
            "theta_pos": 0.2,
        }
        assert stage.x_pos == -99 and peer.theta_pos == -5
        adapter.serial.write.assert_called_once_with(b"WHERE X Y\r")
    finally:
        # Avoid device destructor side effects; no real connection was opened.
        stage.asi_controller = peer.asi_controller = None
