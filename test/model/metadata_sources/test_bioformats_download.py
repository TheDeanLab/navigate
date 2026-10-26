"""Regression tests for interrupted downloads and Bio-Formats cache integrity."""

import hashlib
import io
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import ssl
from threading import Thread
import time

import pytest

from test.model.metadata_sources import bioformats

_PAYLOAD = b"complete archive fixture"


@pytest.fixture
def archive_server(monkeypatch):
    """Serve controlled HTTP failures and byte streams without external network."""
    responses = []
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            status, body, length = responses.pop(0)
            self.send_response(status)
            self.send_header("Content-Length", str(length))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
    thread.start()
    monkeypatch.setattr(
        bioformats, "_URL", f"http://127.0.0.1:{server.server_port}/bftools.zip"
    )
    monkeypatch.setattr(bioformats, "_SHA256", hashlib.sha256(_PAYLOAD).hexdigest())
    monkeypatch.setattr(time, "sleep", lambda seconds: None)
    try:
        yield responses, requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_download_is_cached_and_reused_without_network(tmp_path, archive_server):
    responses, requests = archive_server
    responses.append((200, _PAYLOAD, len(_PAYLOAD)))
    archive = bioformats._get_bftools_archive(tmp_path)
    assert archive.read_bytes() == _PAYLOAD
    assert bioformats._get_bftools_archive(tmp_path) == archive
    assert len(requests) == 1
    assert list(tmp_path.iterdir()) == [archive]


@pytest.mark.parametrize(
    "failure",
    [
        (200, _PAYLOAD[:5], len(_PAYLOAD)),  # Transfer closes early.
        (200, b"wrong archive", 13),  # Complete response, wrong digest.
        (503, b"unavailable", 11),
    ],
    ids=["truncated-transfer", "checksum-mismatch", "http-unavailable"],
)
def test_failed_download_is_retried(tmp_path, archive_server, failure):
    responses, requests = archive_server
    responses.extend([failure, (200, _PAYLOAD, len(_PAYLOAD))])
    archive = bioformats._get_bftools_archive(tmp_path)
    assert archive.read_bytes() == _PAYLOAD
    assert len(requests) == 2
    assert list(tmp_path.iterdir()) == [archive]


def test_corrupt_cached_archive_is_replaced(tmp_path, archive_server):
    responses, requests = archive_server
    responses.append((200, _PAYLOAD, len(_PAYLOAD)))
    archive = tmp_path / "bftools-8.1.0.zip"
    archive.write_bytes(b"corrupt cached archive")
    assert bioformats._get_bftools_archive(tmp_path) == archive
    assert archive.read_bytes() == _PAYLOAD
    assert len(requests) == 1


@pytest.mark.parametrize("status", [200, 503])
def test_exhausted_retries_fail_and_leave_no_partial_cache(
    tmp_path, archive_server, status
):
    responses, requests = archive_server
    responses.extend([(status, b"incomplete", len(_PAYLOAD))] * 3)
    with pytest.raises(RuntimeError, match="after 3 attempts"):
        bioformats._get_bftools_archive(tmp_path)
    assert len(requests) == 3
    assert list(tmp_path.iterdir()) == []


def test_timeouts_are_bounded_and_retried(tmp_path, monkeypatch):
    timeouts = []
    delays = []

    def timeout(url, *, timeout):
        timeouts.append(timeout)
        raise TimeoutError("stalled download")

    monkeypatch.setattr(bioformats, "urlopen", timeout)
    monkeypatch.setattr(time, "sleep", delays.append)
    with pytest.raises(RuntimeError, match="after 3 attempts") as error:
        bioformats._get_bftools_archive(tmp_path)
    assert isinstance(error.value.__cause__, TimeoutError)
    assert timeouts == [30, 30, 30]
    assert delays == [1, 2]
    assert list(tmp_path.iterdir()) == []


def test_cache_directory_is_created(tmp_path, archive_server):
    responses, _ = archive_server
    responses.append((200, _PAYLOAD, len(_PAYLOAD)))
    cache_dir = tmp_path / "new" / "cache"
    archive = bioformats._get_bftools_archive(cache_dir)
    assert archive.parent == cache_dir
    assert archive.read_bytes() == _PAYLOAD


@pytest.mark.parametrize("error_type", [socket.timeout, ssl.SSLError])
@pytest.mark.parametrize("failures", [1, 3], ids=["recover", "exhaust"])
def test_response_body_errors_are_retried(tmp_path, monkeypatch, error_type, failures):
    responses = []
    delays = []

    class BrokenBody(io.BytesIO):
        def read(self, size=-1):
            if self.tell() == 0:
                return super().read(5)
            raise error_type("response-body read failed")

    def open_response(url, *, timeout):
        response = (
            BrokenBody(_PAYLOAD) if len(responses) < failures else io.BytesIO(_PAYLOAD)
        )
        responses.append(response)
        return response

    monkeypatch.setattr(bioformats, "urlopen", open_response)
    monkeypatch.setattr(bioformats, "_SHA256", hashlib.sha256(_PAYLOAD).hexdigest())
    monkeypatch.setattr(time, "sleep", delays.append)

    if failures == 1:
        archive = bioformats._get_bftools_archive(tmp_path)
        assert archive.read_bytes() == _PAYLOAD
        assert len(responses) == 2
        assert delays == [1]
        assert list(tmp_path.iterdir()) == [archive]
    else:
        with pytest.raises(RuntimeError, match="after 3 attempts") as error:
            bioformats._get_bftools_archive(tmp_path)
        assert isinstance(error.value.__cause__, error_type)
        assert len(responses) == 3
        assert delays == [1, 2]
        assert list(tmp_path.iterdir()) == []
    assert all(response.closed for response in responses)


def test_filesystem_errors_are_not_retried(tmp_path, monkeypatch):
    responses = []
    original_open = Path.open

    def open_response(url, *, timeout):
        response = io.BytesIO(_PAYLOAD)
        responses.append(response)
        return response

    def deny_output(path, mode="r", *args, **kwargs):
        if mode == "wb":
            raise PermissionError("cache is not writable")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(bioformats, "urlopen", open_response)
    monkeypatch.setattr(Path, "open", deny_output)
    with pytest.raises(PermissionError, match="cache is not writable"):
        bioformats._get_bftools_archive(tmp_path)
    assert len(responses) == 1
    assert responses[0].closed
    assert list(tmp_path.iterdir()) == []
