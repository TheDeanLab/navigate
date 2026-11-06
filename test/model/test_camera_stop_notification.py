"""The GUI may query camera capabilities immediately after receiving stop."""

import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from navigate.model.model import Model


@pytest.mark.parametrize("data_thread", [True, False])
@pytest.mark.parametrize("cleanup_fails", [False, True])
def test_capture_stop_notification_follows_camera_cleanup(data_thread, cleanup_fails):
    events = []
    pause_lock = threading.Lock()
    pause_lock.acquire()

    def cleanup():
        if data_thread:
            assert not pause_lock.locked()
        events.append("close_camera")
        if cleanup_fails:
            raise RuntimeError("cleanup failed")

    model = SimpleNamespace(
        camera_wait_iterations=1,
        stop_acquisition=True,
        _should_drain_signal_completed_frames=lambda: False,
        pause_data_ready_lock=pause_lock,
        logger=Mock(),
        end_acquisition=cleanup,
        show_img_pipe=SimpleNamespace(send=lambda value: events.append(value)),
        signal_container=SimpleNamespace(end_flag=True),
        is_data_thread_on=data_thread,
        available_image_count=0,
        imaging_mode="single",
    )
    run = Model.run_data_process if data_thread else Model.run_acquisition
    if cleanup_fails:
        with pytest.raises(RuntimeError, match="cleanup failed"):
            run(model)
    else:
        run(model)
    assert events == ["close_camera", "stop"]
