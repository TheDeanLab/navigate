import json
import logging
import queue
from datetime import datetime, timedelta

from navigate.log_files.log_functions import (
    PERFORMANCE,
    eliminate_old_log_files,
    find_filename,
    get_folder_date,
    load_performance_log,
    log_setup,
)


def _snapshot_handlers():
    snapshots = {}
    root_logger = logging.getLogger()
    snapshots[root_logger] = list(root_logger.handlers)

    for name, obj in logging.root.manager.loggerDict.items():
        if isinstance(obj, logging.Logger):
            logger = logging.getLogger(name)
            snapshots[logger] = list(logger.handlers)

    return snapshots


def _restore_handlers(snapshots):
    for logger, handlers in snapshots.items():
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()
        logger.handlers = handlers


def test_find_filename_only_matches_filename_key():
    assert find_filename("filename", "debug.log") is True
    assert find_filename("level", "DEBUG") is False


def test_get_folder_date_parses_valid_names_and_rejects_invalid_names():
    assert get_folder_date("2026-03-21-1530") == datetime(2026, 3, 21, 15, 30)
    assert get_folder_date("not-a-date") is False


def test_eliminate_old_log_files_removes_only_expired_timestamp_dirs(tmp_path):
    expired = tmp_path / (datetime.now() - timedelta(days=31)).strftime("%Y-%m-%d-%H%M")
    current = tmp_path / datetime.now().strftime("%Y-%m-%d-%H%M")
    invalid = tmp_path / "keep-me"

    expired.mkdir()
    current.mkdir()
    invalid.mkdir()

    eliminate_old_log_files(tmp_path)

    assert not expired.exists()
    assert current.exists()
    assert invalid.exists()


def test_load_performance_log_reads_latest_valid_log_and_skips_invalid_json(
    tmp_path, monkeypatch
):
    logs_dir = tmp_path / "logs"
    older_dir = logs_dir / "2026-03-20-1200"
    latest_dir = logs_dir / "2026-03-21-1200"
    hidden_dir = logs_dir / ".ignored"

    older_dir.mkdir(parents=True)
    latest_dir.mkdir()
    hidden_dir.mkdir()

    (older_dir / "performance.log").write_text(json.dumps({"run": "older"}) + "\n")
    (latest_dir / "performance.log").write_text(
        json.dumps({"run": "latest"}) + "\nnot-json\n" + json.dumps({"step": 2}) + "\n"
    )

    monkeypatch.setattr(
        "navigate.log_files.log_functions.get_navigate_path", lambda: tmp_path
    )

    assert load_performance_log() == [{"run": "latest"}, {"step": 2}]


def test_log_setup_returns_provided_queue_and_start_listener_creates_listener(
    tmp_path, monkeypatch
):
    handler_snapshots = _snapshot_handlers()
    monkeypatch.setattr(
        "navigate.log_files.log_functions.mp.Queue", lambda *args, **kwargs: queue.Queue()
    )

    provided_queue = queue.Queue()
    listener = None
    try:
        returned_queue = log_setup("logging.yml", tmp_path, queue=provided_queue)

        assert returned_queue is provided_queue

        log_queue, listener = log_setup("logging.yml", tmp_path, start_listener=True)
        assert log_queue is not None
        logger = logging.getLogger("model")
        logger.log(PERFORMANCE, json.dumps({"kind": "perf"}))
    finally:
        try:
            if listener is not None:
                listener.stop()
        finally:
            _restore_handlers(handler_snapshots)
            logging.shutdown()

    timestamp_dirs = [path for path in tmp_path.iterdir() if path.is_dir()]
    assert timestamp_dirs


def test_load_performance_log_returns_none_when_latest_log_file_is_missing(
    tmp_path, monkeypatch
):
    logs_dir = tmp_path / "logs"
    latest_dir = logs_dir / "2026-03-21-1200"
    latest_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "navigate.log_files.log_functions.get_navigate_path", lambda: tmp_path
    )

    assert load_performance_log() is None
