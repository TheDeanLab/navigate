# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import logging
from logging.handlers import QueueHandler
from queue import SimpleQueue
from threading import Event

import pytest

from navigate.controller.thread_pool import SelfLockThread, SynchronizedThreadPool
from navigate.controller import thread_pool


@pytest.mark.parametrize("pooled", [False, True])
def test_thread_exceptions_preserve_traceback_and_format_for_queue(
    caplog, monkeypatch, pooled
):
    def fail(**kwargs):
        raise ZeroDivisionError("invalid acquisition total")

    # Controller integration tests configure non-propagating application loggers.
    # Use real logging handlers without depending on that global configuration.
    logger = logging.Logger("thread-pool-test", level=logging.ERROR)
    monkeypatch.setattr(thread_pool, "logger", logger)
    logger.addHandler(caplog.handler)
    queue = SimpleQueue()
    handler = QueueHandler(queue)
    logger.addHandler(handler)
    callback = Event()
    pool = SynchronizedThreadPool()
    pool.registerResource("camera")
    target = (
        pool.threadTaskWrapping("camera", fail, callback=callback.set)
        if pooled
        else fail
    )
    thread = SelfLockThread(target=target, name="camera", kwargs={})
    try:
        thread.start()
        thread.join(timeout=2)
        assert not thread.is_alive()
    finally:
        logger.removeHandler(handler)
        handler.close()

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert "camera" in record.getMessage()
    assert record.exc_info[0] is ZeroDivisionError
    assert "invalid acquisition total" in caplog.text
    queued_record = queue.get_nowait()
    assert "Traceback (most recent call last)" in queued_record.getMessage()
    assert "ZeroDivisionError: invalid acquisition total" in queued_record.getMessage()
    if pooled:
        assert callback.is_set()
        assert not pool.resources["camera"].waitlist
        # The resource remains usable after the failed task.
        completed = Event()
        next_thread = pool.createThread("camera", completed.set, kwargs={})
        next_thread.join(timeout=2)
        assert not next_thread.is_alive()
        assert completed.is_set()
