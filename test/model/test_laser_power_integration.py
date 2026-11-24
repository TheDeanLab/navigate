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
    scope.prepare_laser_settings()
    cursor, records = model.get_laser_settings_metadata(cursor=next_cursor)
    assert len(records) == 2
    assert cursor[0] != next_cursor[0]
    assert all(record["confirmed_setpoint_mw"] is None for record in records)


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
