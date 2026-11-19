"""Waveforms use device-confirmed timing without confusing sweep and row units."""

import math
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from navigate.model.devices.camera.format import CameraImageFormat
from navigate.model.microscope import Microscope


class ConfirmingCamera:
    requires_exposure_confirmation = True
    is_acquiring = False
    quantum = 33.94909090909091e-6

    def __init__(self):
        self.confirmed = []
        self.writes = []
        self.camera_exposure_time = 0.01

    def confirm_exposure_timing(self, requested, shutter_width=None):
        assert not self.is_acquiring
        self.confirmed.append((requested, shutter_width))
        if shutter_width is not None:
            return SimpleNamespace(
                exposure_time=0.0007296, sweep_time=0.020064, line_interval=0.00007296
            )
        actual = math.ceil(requested / self.quantum - 1e-9) * self.quantum
        return SimpleNamespace(
            exposure_time=actual, sweep_time=actual, line_interval=None
        )

    def set_exposure_time(self, requested):
        self.writes.append(requested)
        self.camera_exposure_time = requested
        return True

    def get_exposure_time(self):
        return self.camera_exposure_time

    def set_line_interval(self, value):
        self.line_interval = value
        return True

    def get_line_interval(self):
        return self.line_interval

    def initialize_image_series(self, *_):
        self.is_acquiring = True

    def close_image_series(self):
        self.is_acquiring = False

    def calculate_readout_time(self):
        return 0.001

    def calculate_light_sheet_exposure_time(self, *_):
        return 0.0007296, 0.00007296, 0.020064


@pytest.fixture
def microscope():
    m = Microscope.__new__(Microscope)
    m.microscope_name = "scope"
    m.camera = ConfirmingCamera()
    channels = {
        "channel_1": {"is_selected": True, "camera_exposure_time": 1.0},
        "channel_2": {"is_selected": True, "camera_exposure_time": 2.0},
        "channel_3": {"is_selected": False, "camera_exposure_time": 3.0},
    }
    m.configuration = {
        "configuration": {"microscopes": {"scope": {"camera": {}}}},
        "experiment": {
            "MicroscopeState": {"channels": channels},
            "CameraParameters": {
                "scope": {
                    "sensor_mode": "Normal",
                    "readout_direction": "Top-to-Bottom",
                    "number_of_pixels": 20,
                }
            },
        },
        "waveform_constants": {
            "other_constants": {
                "camera_delay": 0,
                "remote_focus_ramp_falling": 0,
                "remote_focus_settle_duration": 0,
            }
        },
    }
    m.configure_camera = lambda: CameraImageFormat.for_bit_depth(16)
    m.report_camera_settings = lambda: None
    m.data_buffer = None
    m.number_of_frames = 2
    m.shutter = SimpleNamespace(open_shutter=Mock())
    m.daq = SimpleNamespace(calculate_all_waveforms=Mock(return_value={}))
    m.remote_focus = SimpleNamespace(adjust=Mock(return_value={}))
    m.galvo = {"g": SimpleNamespace(adjust=Mock(return_value={}))}
    m.stages_list = []
    m.output_event_queue = SimpleNamespace(put=Mock())
    return m


def test_selected_exposures_confirmed_idle_before_waveform_planning(microscope):
    m = microscope
    m.prepare_acquisition()
    assert m.camera.confirmed == [(0.001, None), (0.002, None)]
    expected = 0.0010184727272727272
    for device in (
        m.daq.calculate_all_waveforms,
        m.remote_focus.adjust,
        m.galvo["g"].adjust,
    ):
        args = device.call_args.args
        exposures = args[1] if device is m.daq.calculate_all_waveforms else args[0]
        assert exposures["channel_1"] == pytest.approx(expected + 0.001)
    m.set_camera_exposure_time(m.channels["channel_1"])
    assert m.current_exposure_time == pytest.approx(expected)
    assert m.camera.camera_exposure_time == pytest.approx(expected)
    assert len(m.camera.confirmed) == 2
    assert m.channels["channel_1"]["camera_exposure_time"] == 1.0


@pytest.mark.parametrize("requested", [1.5, 2.0])
def test_changed_channel_exposure_requires_new_plan(microscope, requested):
    m = microscope
    m.prepare_acquisition()
    m.channels["channel_1"]["camera_exposure_time"] = requested
    with pytest.raises(RuntimeError, match="[Pp]repar|[Rr]estart|[Cc]onfirm"):
        m.set_camera_exposure_time(m.channels["channel_1"])
    assert not m.camera.writes


def test_readback_change_is_rejected_before_daq_can_use_stale_plan(microscope):
    m = microscope
    m.prepare_acquisition()
    m.camera.get_exposure_time = lambda: 0.009
    with pytest.raises(RuntimeError, match="[Ee]xposure|[Tt]iming"):
        m.set_camera_exposure_time(m.channels["channel_1"])


def test_light_sheet_waveform_keeps_full_sweep_and_camera_row_exposure(microscope):
    m = microscope
    m.configuration["experiment"]["CameraParameters"]["scope"][
        "sensor_mode"
    ] = "Light-Sheet"
    m.configuration["experiment"]["MicroscopeState"]["channels"]["channel_1"][
        "camera_exposure_time"
    ] = 20
    m.prepare_acquisition()
    assert m.remote_focus.adjust.call_args.args[0]["channel_1"] == pytest.approx(
        0.020064
    )
    m.set_camera_exposure_time(m.channels["channel_1"])
    assert m.current_exposure_time == pytest.approx(0.0007296)
    assert m.camera.line_interval == pytest.approx(0.00007296)


def test_confirmation_failure_does_not_start_camera_or_open_shutter(microscope):
    m = microscope
    m.camera.confirm_exposure_timing = Mock(side_effect=RuntimeError("no readback"))
    with pytest.raises(RuntimeError, match="no readback"):
        m.prepare_acquisition()
    assert not m.camera.is_acquiring
    m.shutter.open_shutter.assert_not_called()


def test_legacy_camera_keeps_requested_timing_without_probe(microscope):
    m = microscope
    m.camera.requires_exposure_confirmation = False
    m.prepare_acquisition()
    assert not m.camera.confirmed
    assert m.exposure_times["channel_1"] == 0.002
