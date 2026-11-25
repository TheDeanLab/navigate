"""ASI command/reply ownership across acquisition and stage worker threads."""

import threading
import time
from unittest.mock import MagicMock

import pytest
import serial

from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController
from navigate.model.devices.APIs.asi.asi_MS2000_controller import MS2000Controller


@pytest.fixture(params=[TigerController, MS2000Controller])
def controller(request):
    device = request.param("unused", 115200)
    device.default_axes_sequence = ["X"]
    device.serial = MagicMock()
    device.serial.readline.return_value = b":A 10\r\n"
    return device


def read_on_worker(controller):
    results = []
    errors = []

    def read():
        try:
            results.append(controller.get_position(["X"]))
        except Exception as error:
            errors.append(error)

    worker = threading.Thread(target=read, daemon=True)
    worker.start()
    worker.join(timeout=2)
    assert not worker.is_alive(), "An earlier serial error left the connection locked"
    assert not errors
    assert results == [{"X": 10.0}]


@pytest.mark.parametrize(
    "operation",
    ["read_all", "reset_input_buffer", "reset_output_buffer", "write", "readline"],
)
def test_serial_exception_releases_transaction(controller, operation):
    failed = getattr(controller.serial, operation)
    failed.side_effect = serial.SerialException("device disconnected")
    with pytest.raises(serial.SerialException, match="device disconnected"):
        controller.get_position(["X"])
    assert controller.safe_to_write.is_set()
    failed.side_effect = None
    read_on_worker(controller)


def test_strict_write_timeout_releases_transaction(controller):
    controller.serial.write.side_effect = serial.SerialTimeoutException("timeout")
    with pytest.raises(serial.SerialTimeoutException):
        controller.send_command("WHERE X", strict=True)
    assert controller.safe_to_write.is_set()
    controller.serial.readline.assert_not_called()
    controller.serial.write.side_effect = None
    read_on_worker(controller)


def test_legacy_write_timeout_keeps_reply_paired(controller):
    controller.serial.write.side_effect = serial.SerialTimeoutException("timeout")
    controller.send_command("WHERE X")
    assert not controller.safe_to_write.is_set()
    assert controller.read_response() == ":A 10"
    assert controller.safe_to_write.is_set()
    controller.serial.write.side_effect = None
    read_on_worker(controller)


def test_standalone_read_preserves_serial_api(controller):
    assert controller.read_response() == ":A 10"
    read_on_worker(controller)


def test_concurrent_position_queries_keep_command_and_reply_together(controller):
    """Multiple waiters must never consume or overwrite another caller's reply."""
    owner = None
    collisions = []
    errors = []
    results = []
    start = threading.Barrier(4)
    aborted = threading.Event()

    def write(command):
        nonlocal owner
        if owner is not None:
            collisions.append(command)
        owner = threading.get_ident()
        return len(command)

    def readline():
        nonlocal owner
        # Let other workers queue while a reply is in flight, as real serial I/O does.
        time.sleep(0.005)
        if owner != threading.get_ident():
            raise serial.SerialException("another worker consumed the reply")
        owner = None
        return b":A 10\r\n"

    controller.serial.write.side_effect = write
    controller.serial.readline.side_effect = readline

    def read_many():
        try:
            start.wait(timeout=2)
            for _ in range(5):
                if aborted.is_set():
                    break
                results.append(controller.get_position(["X"]))
        except Exception as error:
            errors.append(error)
            aborted.set()
            # Unblock legacy Event waiters when exercising the unfixed code.
            controller.safe_to_write.set()

    workers = [threading.Thread(target=read_many, daemon=True) for _ in range(4)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=4)
    assert all(not worker.is_alive() for worker in workers)
    assert not collisions
    assert not errors
    assert results == [{"X": 10.0}] * 20
