"""Channel preparation applies serial power and records confirmed state."""

from queue import Queue
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from navigate.model.metadata_sources.laser_metadata import LaserMetadata
from navigate.model.microscope import Microscope
from navigate.model.model import Model, ASIModel
from navigate.model.devices.laser.settings.base import LaserControlError
from test.model.devices.lasers.test_laser_software import make_laser


class Shutter:
    state = True

    def close_shutter(self):
        self.state = False

    def open_shutter(self):
        self.state = True


@pytest.fixture
def scope():
    scope = Microscope.__new__(Microscope)
    scope.microscope_name = "scope"
    scope.laser = {"488": make_laser()}
    scope.laser_wavelength = [488]
    scope.channels = {
        "channel_1": {"laser_index": 0, "laser_power": 25, "is_selected": True},
        "channel_2": {"laser_index": 0, "laser_power": 50, "is_selected": True},
    }
    scope.laser_metadata = LaserMetadata()
    scope.output_event_queue = Queue()
    scope.shutter = Shutter()
    scope.filter_wheel = {}
    scope.daq = Mock()
    scope.set_camera_exposure_time = Mock()
    scope._ensure_zero_defocus_focus = Mock()
    scope.zero_defocus_focus = None
    scope.prepare_laser_settings()
    scope.shutter.open_shutter()
    return scope


def test_channel_preparation_routes_percentage_and_keeps_intent(scope):
    scope.prepare_channel("channel_1")
    assert scope.laser["488"].settings.get_power_setpoint_mw() == 25
    assert scope.channels["channel_1"]["laser_power"] == 25
    assert scope.shutter.state
    assert scope.daq.method_calls[0][0] == "stop_acquisition"
    assert scope.daq.method_calls[-1][0] == "prepare_acquisition"
    _, records = scope.laser_metadata.read_since()
    assert records[-1]["event"] == "prepared"
    assert records[-1]["confirmed_setpoint_mw"] == 25
    assert records[-1]["measured_power_mw"] is None
    assert records[-1]["verification"] == "simulated"


def test_bench_metadata_identifies_ungated_requests_and_failures(scope):
    from dataclasses import replace

    laser = scope.laser["488"]
    laser.options = replace(laser.options, bench_mode=True)
    scope.begin_laser_acquisition()
    scope.prepare_laser_settings()
    laser.settings.set_power_mw = Mock(side_effect=LaserControlError("rejected"))
    with pytest.raises(LaserControlError, match="rejected"):
        scope.prepare_channel("channel_1")
    records = scope.laser_metadata.read_since()[1]
    assert all(record["bench_mode"] for record in records)
    assert records[-1]["event"] == "failed"


def test_shared_laser_channel_switches_and_live_changes(scope):
    for channel, expected in [("channel_1", 25), ("channel_2", 50), ("channel_1", 25)]:
        scope.prepare_channel(channel)
        assert scope.laser["488"].settings.get_power_setpoint_mw() == expected
    scope.channels["channel_1"]["laser_power"] = 12
    scope.prepare_channel("channel_1")
    assert scope.laser["488"].settings.get_power_setpoint_mw() == 12
    _, records = scope.laser_metadata.read_since()
    channel_records = [r for r in records if r["channel"] == "channel_1"]
    assert [r["confirmed_setpoint_mw"] for r in channel_records] == [None, 25, 12]


def test_serial_changes_are_applied_with_shutter_closed(scope):
    settings = scope.laser["488"].settings
    original = settings.set_power_mw

    def apply(value):
        assert scope.shutter.state is False
        return original(value)

    settings.set_power_mw = apply
    scope.prepare_channel("channel_1")
    assert scope.shutter.state is True


def test_mid_acquisition_preparation_keeps_unflushed_history_and_skips_mode_writes(
    scope,
):
    from dataclasses import replace
    from navigate.model.devices.laser.settings.base import LaserMode

    laser = scope.laser["488"]
    laser.options = replace(laser.options, mode="digital")
    laser.settings.set_mode = Mock(wraps=laser.settings.set_mode)
    scope.begin_laser_acquisition()
    scope.prepare_laser_settings()
    scope.prepare_channel("channel_1")
    acquisition_id = scope.laser_metadata.acquisition_id
    _, before = scope.laser_metadata.read_since()
    scope.prepare_laser_settings()
    _, after = scope.laser_metadata.read_since()
    assert scope.laser_metadata.acquisition_id == acquisition_id
    assert after[: len(before)] == before
    laser.settings.set_mode.assert_called_once_with(LaserMode.DIGITAL)
    laser.settings.mode = LaserMode.ANALOG
    with pytest.raises(LaserControlError, match="requested mode"):
        scope.prepare_laser_settings()
    laser.settings.set_mode.assert_called_once()


def test_live_edit_returning_to_same_power_republishes_confirmation_without_io(
    scope, monkeypatch
):
    scope.prepare_channel("channel_1")
    laser = scope.laser["488"]
    laser.settings.set_power_mw = Mock(wraps=laser.settings.set_power_mw)
    cursor, _ = scope.laser_metadata.read_since()
    while not scope.output_event_queue.empty():
        scope.output_event_queue.get_nowait()
    # The UI's 25 -> 30 -> 25 edit is debounced into one unchanged final request.
    model = Model.__new__(Model)
    model.configuration = {
        "experiment": {"MicroscopeState": {"microscope_name": "scope"}}
    }
    model.active_microscope_name = "scope"
    model.active_microscope = scope
    model.is_acquiring = True
    model.imaging_mode = "live"
    model.acquisition_modes_feature_setting = {"live": []}
    model.signal_thread = Mock()
    model.event_queue = Queue()
    model.logger = Mock()
    scope.calculate_all_waveform = Mock(return_value={})
    monkeypatch.setattr(
        "navigate.model.model.load_features", Mock(return_value=(Mock(), Mock()))
    )
    monkeypatch.setattr("navigate.model.model.ThreadWithWarning", Mock())
    model._update_setting("channel")
    scope.prepare_channel("channel_1")
    kind, payload = scope.output_event_queue.get_nowait()
    assert kind == "laser_power"
    assert payload["confirmed_setpoint_mw"] == 25
    assert scope.laser_metadata.read_since(cursor)[1] == []
    laser.settings.set_power_mw.assert_not_called()
    scope.prepare_channel("channel_1")
    assert scope.output_event_queue.empty()


@pytest.mark.parametrize("failed_device", ["shutter", "laser"])
def test_failed_blanking_prevents_serial_power_write_and_waveforms(
    scope, failed_device
):
    laser = scope.laser["488"]
    laser.settings.set_power_mw = Mock(wraps=laser.settings.set_power_mw)
    if failed_device == "shutter":
        scope.shutter.close_shutter = Mock(side_effect=OSError("blank failed"))
    else:
        laser.external.turn_off = Mock(side_effect=OSError("blank failed"))
    with pytest.raises(LaserControlError, match="blank failed"):
        scope.apply_laser_power("channel_1", scope.channels["channel_1"])
    laser.settings.set_power_mw.assert_not_called()
    scope.daq.prepare_acquisition.assert_not_called()
    assert laser.power_metadata is None
    assert scope.laser_metadata.read_since()[1][-1]["event"] == "failed"
    laser.external.turn_off.assert_called()


def test_failed_write_blocks_waveform_preparation_and_records_failure(scope):
    scope.prepare_channel("channel_1")
    scope.daq.reset_mock()
    scope.channels["channel_1"]["laser_power"] = 70
    scope.laser["488"].settings.set_power_mw = Mock(
        side_effect=LaserControlError("disconnected")
    )
    with pytest.raises(LaserControlError, match="disconnected"):
        scope.prepare_channel("channel_1")
    scope.daq.prepare_acquisition.assert_not_called()
    assert scope.shutter.state is False
    _, records = scope.laser_metadata.read_since()
    assert records[-1]["event"] == "failed"
    assert records[-1]["confirmed_setpoint_mw"] is None
    assert records[-2]["confirmed_setpoint_mw"] == 25


def test_metadata_read_is_incremental_and_resets_for_new_acquisition(scope):
    model = Model.__new__(Model)
    model.active_microscope_name = "scope"
    model.virtual_microscopes = {}
    model.microscopes = {"scope": scope}
    cursor, records = model.get_laser_settings_metadata()
    assert len(records) == 2
    assert model.get_laser_settings_metadata(cursor=cursor)[1] == []
    scope.prepare_channel("channel_1")
    next_cursor, records = model.get_laser_settings_metadata(cursor=cursor)
    assert len(records) == 1
    assert records[0]["confirmed_setpoint_mw"] == 25
    scope.begin_laser_acquisition()
    scope.prepare_laser_settings()
    cursor, records = model.get_laser_settings_metadata(cursor=next_cursor)
    assert len(records) == 2
    assert cursor[0] != next_cursor[0]
    assert all(record["confirmed_setpoint_mw"] is None for record in records)


@pytest.mark.parametrize("backend", ["OBIS", "LuxX"])
def test_new_adapters_record_confirmed_channel_power_and_clear_failed_confirmation(
    scope, backend
):
    from test.model.devices.lasers.test_obis_luxx_settings import adapter

    laser = scope.laser["488"]
    laser.settings, connection = adapter(backend)
    scope.prepare_laser_settings()
    scope.prepare_channel("channel_1")
    _, records = scope.laser_metadata.read_since()
    confirmed = records[-1]
    assert confirmed["verification"] == "readback"
    assert confirmed["requested_percent"] == 25
    assert confirmed["requested_mw"] == 50
    assert confirmed["confirmed_setpoint_mw"] == pytest.approx(50, abs=0.05)
    assert confirmed["measured_power_mw"] == 7.25
    assert scope.channels["channel_1"]["laser_power"] == 25
    connection.ignore_writes = True
    with pytest.raises(LaserControlError, match="readback"):
        scope.prepare_channel("channel_2")
    _, records = scope.laser_metadata.read_since()
    assert records[-1]["verification"] == "failed"
    assert records[-1]["confirmed_setpoint_mw"] is None
    assert scope.shutter.state is False


@pytest.mark.parametrize(
    "model_class,method", [(Model, "snap_image"), (ASIModel, "snap_zstack")]
)
def test_failed_feature_preparation_never_reaches_daq(model_class, method):
    model = model_class.__new__(model_class)
    model.signal_container = SimpleNamespace(run=Mock(), is_closed=True)
    model.stop_acquisition = False
    model.active_microscope = Mock()
    getattr(model, method)()
    assert model.stop_acquisition is True
    model.active_microscope.turn_on_laser.assert_not_called()
    model.active_microscope.daq.run_acquisition.assert_not_called()
