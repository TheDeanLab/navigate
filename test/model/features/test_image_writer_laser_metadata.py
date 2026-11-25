"""Laser confirmations are persisted for every format and on failed capture."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from navigate.model.features.image_writer import ImageWriter
from navigate.model.metadata_sources.laser_metadata import LaserMetadata
from test.model.features.test_image_writer_camera_segments import (
    acquisition,
)  # noqa: F401


@pytest.mark.parametrize("file_type", ["TIFF", "OME-TIFF", "H5", "N5", "OME-Zarr"])
def test_saved_laser_metadata_preserves_history_and_failure(acquisition, file_type):
    model = acquisition
    model.configuration["experiment"]["Saving"]["file_type"] = file_type
    metadata = model.active_microscope.laser_metadata = LaserMetadata()
    requested = {
        "power_source": "serial",
        "requested_percent": 20,
        "confirmed_setpoint_mw": None,
        "measured_power_mw": None,
        "verification": "pending",
        "event": "requested",
    }
    metadata.record("channel_1", requested)
    writer = ImageWriter(model)
    first = {
        **requested,
        "confirmed_setpoint_mw": 10.1,
        "percent_reference_mw": 50,
        "verification": "readback",
        "event": "prepared",
    }
    metadata.record("channel_1", first)
    writer.save_image([0])
    assert not model.stop_acquisition
    metadata.record(
        "channel_1",
        {
            **requested,
            "requested_percent": 40,
            "verification": "failed",
            "event": "failed",
            "error": "timeout",
        },
    )
    writer.close()
    writer.close()
    path = Path(writer.save_directory) / "laser-settings-scope.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()]
    assert [r["event"] for r in records] == ["requested", "prepared", "failed"]
    assert [r["confirmed_setpoint_mw"] for r in records] == [None, 10.1, None]
    assert all(r["measured_power_mw"] is None for r in records)
    assert (
        "confirmed_setpoint_mw"
        not in model.configuration["experiment"]["MicroscopeState"]["channels"][
            "channel_1"
        ]
    )


def test_metadata_copies_records_and_deduplicates_unchanged_settings():
    metadata = LaserMetadata()
    record = {"confirmed_setpoint_mw": 10, "confirmed_at": "first"}
    assert metadata.record("channel_1", record)
    record["confirmed_setpoint_mw"] = 500
    assert not metadata.record(
        "channel_1", {"confirmed_setpoint_mw": 10, "confirmed_at": "later"}
    )
    cursor, records = metadata.read_since()
    assert cursor == 1
    assert records[0]["confirmed_setpoint_mw"] == 10
    records[0]["confirmed_setpoint_mw"] = 999
    assert metadata.read_since()[1][0]["confirmed_setpoint_mw"] == 10
    assert metadata.read_since(cursor)[1] == []


def test_metadata_io_failure_stops_before_writing_images(acquisition, monkeypatch):
    model = acquisition
    writer = ImageWriter(model)
    source = writer.data_source

    def fail():
        raise OSError("metadata disk is full")

    monkeypatch.setattr(writer, "_write_laser_metadata", fail)
    writer.save_image([0])
    assert model.stop_acquisition is True
    assert model.event_queue.get_nowait()[0] == "warning"
    assert source._current_frame == 0


def test_closed_writer_never_appends_later_live_history(acquisition):
    metadata = acquisition.active_microscope.laser_metadata = LaserMetadata()
    metadata.record("channel_1", {"confirmed_setpoint_mw": 10})
    writer = ImageWriter(acquisition)
    writer.close()
    path = Path(writer.save_directory) / "laser-settings-scope.jsonl"
    saved = path.read_bytes()
    acquisition.active_microscope.laser_metadata = LaserMetadata()
    acquisition.active_microscope.laser_metadata.record(
        "channel_1", {"confirmed_setpoint_mw": 20}
    )
    writer.close()
    writer._write_laser_metadata()
    assert path.read_bytes() == saved
    # Opening another output on the same writer explicitly re-enables recording.
    writer.initialize_saving(sub_dir="second")
    writer.close()
    new_path = Path(writer.save_directory) / "laser-settings-scope.jsonl"
    records = [json.loads(line) for line in new_path.read_text().splitlines()]
    assert [r["confirmed_setpoint_mw"] for r in records] == [20]
    assert path.read_bytes() == saved


def test_final_metadata_failure_closes_source_and_does_not_skip_model_cleanup(
    acquisition,
):
    model = acquisition
    writer = ImageWriter(model)
    source_close = writer.data_source.close = Mock(wraps=writer.data_source.close)
    writer._write_laser_metadata = Mock(side_effect=OSError("metadata disk full"))
    model.active_microscope.end_acquisition = Mock()
    virtual_writer = Mock()
    virtual_writer.close.side_effect = OSError("virtual disk full")
    virtual_scope = SimpleNamespace(end_acquisition=Mock(), image_writer=virtual_writer)
    model.virtual_microscopes = {"virtual": virtual_scope}
    model.image_writer = writer
    model.plugin_acquisition_modes = {}
    model.signal_container = Mock()
    model.data_container = Mock()
    signal_cleanup = model.signal_container.cleanup
    data_cleanup = model.data_container.cleanup
    model.logger = Mock()
    model.addon_feature = object()
    model.end_acquisition()
    model.active_microscope.end_acquisition.assert_called_once()
    virtual_scope.end_acquisition.assert_called_once()
    signal_cleanup.assert_called_once()
    data_cleanup.assert_called_once()
    source_close.assert_called_once()
    assert model.addon_feature is None
    assert model.stop_acquisition
    warnings = [model.event_queue.get_nowait() for _ in range(2)]
    assert all(event == "warning" for event, _ in warnings)
    assert "metadata disk full" in warnings[-1][1]
    writer.close()
    source_close.assert_called_once()
