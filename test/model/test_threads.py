from queue import Queue
from unittest.mock import MagicMock

import pytest

import navigate.model.utils.threads as threads_module
from navigate.model.utils.exceptions import UserVisibleException


def test_thread_with_warning_enqueues_user_visible_exception():
    warning_queue = Queue()
    logger = MagicMock()

    def target():
        raise UserVisibleException("Camera disconnected")

    thread = threads_module.ThreadWithWarning(
        target=target,
        name="worker-visible",
        warning_queue=warning_queue,
        logger=logger,
    )

    with pytest.raises(UserVisibleException, match="Camera disconnected"):
        thread.run()

    logger.error.assert_called_once_with(
        "Error in thread worker-visible: Camera disconnected"
    )
    assert warning_queue.get_nowait() == ("warning", "Camera disconnected")


def test_thread_with_warning_does_not_enqueue_non_user_visible_exception():
    warning_queue = Queue()
    logger = MagicMock()

    def target():
        raise RuntimeError("boom")

    thread = threads_module.ThreadWithWarning(
        target=target,
        name="worker-generic",
        warning_queue=warning_queue,
        logger=logger,
    )

    with pytest.raises(RuntimeError, match="boom"):
        thread.run()

    logger.error.assert_called_once_with("Error in thread worker-generic: boom")
    assert warning_queue.empty()


def test_thread_with_warning_uses_module_logger_by_default(monkeypatch):
    logger = MagicMock()
    monkeypatch.setattr(threads_module, "logger", logger)
    calls = []

    thread = threads_module.ThreadWithWarning(
        target=lambda: calls.append("ran"),
        name="worker-success",
    )

    thread.run()

    assert calls == ["ran"]
    assert not hasattr(thread, "_warning_queue")
    logger.error.assert_not_called()
