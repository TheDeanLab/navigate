"""Quest timing and constraints; hardware I/O is replaced at the DCAM boundary."""

import math
import sys
import types
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def camera(monkeypatch):
    module_name = "navigate.model.devices.camera.hamamatsu"
    api_name = "navigate.model.devices.APIs.hamamatsu.HamamatsuAPI"
    api = types.ModuleType(api_name)
    api.DCAM = object
    monkeypatch.setitem(sys.modules, api_name, api)
    monkeypatch.delitem(sys.modules, module_name, raising=False)
    from navigate.model.devices.camera.hamamatsu import HamamatsuOrcaQuest2Camera

    c = object.__new__(HamamatsuOrcaQuest2Camera)
    c.camera_controller = MagicMock()
    c.camera_controller.get_property_range.return_value = (7.2e-6, 237.6e-6, 0.24e-6)
    c.camera_controller.get_property_range.side_effect = lambda name: (
        (7.2e-6, 1800, 1e-8)
        if name == "exposure_time"
        else c.camera_controller.get_property_range.return_value
    )
    c.camera_controller.set_property_value.return_value = True
    c.camera_controller.get_property_value.side_effect = lambda name: {
        "sensor_mode": 12,
        "internal_line_interval": 10.08e-6,
        "minimum_trigger_interval": 0.05652864,
        "exposure_time": 100.8e-6,
        "bits_per_channel": 16,
    }[name]
    c.camera_parameters = {}
    c.y_pixels = 2304
    c.is_acquiring = False
    c.minimum_frame_interval = 0.0
    yield c
    sys.modules.pop(module_name, None)


@pytest.mark.parametrize("width", [19, 20])
def test_paired_rows_and_quantized_line_interval(camera, width):
    exposure, interval, sweep = camera.calculate_light_sheet_exposure_time(
        0.01171, width
    )
    assert interval == pytest.approx(10.08e-6)
    assert exposure == pytest.approx(100.8e-6)
    assert sweep == pytest.approx(0.01180368)
    assert camera.camera_parameters["line_interval"] == interval


@pytest.mark.parametrize(
    "requested, interval, sweep",
    [
        (1e-6, 7.2e-6, 0.0084312),
        (10, 237.6e-6, 0.2782296),
    ],
)
def test_line_interval_limits(camera, requested, interval, sweep):
    exposure, actual, effective = camera.calculate_light_sheet_exposure_time(
        requested, 20
    )
    assert actual == pytest.approx(interval)
    assert effective == pytest.approx(sweep)
    assert exposure == pytest.approx(interval * 10)


@pytest.mark.parametrize(
    "duration,width",
    [
        (0, 20),
        (-1, 20),
        (math.nan, 20),
        (math.inf, 20),
        (0.01, 0),
        (0.01, 2305),
        (0.01, 1.5),
    ],
)
def test_invalid_timing_rejected(camera, duration, width):
    with pytest.raises(ValueError):
        camera.calculate_light_sheet_exposure_time(duration, width)


def test_unsupported_directions_rejected(camera):
    with pytest.raises(ValueError, match="direction"):
        camera.set_readout_direction("Bidirectional")
    camera.camera_controller.set_property_value.assert_not_called()


def test_light_sheet_rejects_binning(camera):
    with pytest.raises(ValueError, match="1x1"):
        camera.set_binning("2x2")


def test_failed_setting_is_not_silently_accepted(camera):
    camera.camera_controller.set_property_value.return_value = False
    with pytest.raises(RuntimeError, match="readout_direction"):
        camera.set_readout_direction("Bottom-to-Top")


def test_driver_period_used_for_pacing(camera):
    assert camera.set_exposure_time(100.8e-6)
    assert camera.minimum_frame_interval == pytest.approx(0.05652864)


def test_failed_capture_start_does_not_mark_camera_acquiring(camera):
    camera.camera_controller.start_acquisition.return_value = False
    with pytest.raises(RuntimeError, match="start"):
        camera.initialize_image_series([], 0)
    assert not camera.is_acquiring


def test_opt_in_restart_reinitializes_before_attaching_buffers(camera):
    camera.camera_parameters["reinitialize_on_restart"] = True
    camera.camera_controller.start_acquisition.return_value = True
    camera.camera_controller.stop_acquisition.return_value = True
    camera.camera_controller.reinitialize.return_value = True
    camera.initialize_image_series([], 0)
    camera.close_image_series()
    camera.initialize_image_series([], 0)
    calls = [call[0] for call in camera.camera_controller.method_calls]
    assert (
        calls.index("stop_acquisition") < calls.index("reinitialize") < len(calls) - 1
    )
    assert calls[-1] == "start_acquisition"
    assert camera.is_acquiring


def test_microscope_preserves_quantized_sweep_before_setting_camera(camera):
    from queue import Queue
    from navigate.model.microscope import Microscope

    microscope = object.__new__(Microscope)
    microscope.microscope_name = "Quest2"
    microscope.camera = camera
    camera.y_pixels = 512
    microscope.output_event_queue = Queue()
    channel = {"is_selected": True, "camera_exposure_time": 20.0}
    microscope.configuration = {
        "configuration": {"microscopes": {"Quest2": {"camera": {}}}},
        "experiment": {
            "MicroscopeState": {"channels": {"channel_1": channel}},
            "CameraParameters": {
                "Quest2": {
                    "sensor_mode": "Light-Sheet",
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
    # The SDK readback follows the exposure/line writes performed by preparation.
    read = camera.camera_controller.get_property_value.side_effect
    values = {}
    camera.camera_controller.set_property_value.side_effect = (
        lambda name, value, **kwargs: values.update({name: value}) is None
    )
    camera.camera_controller.get_property_value.side_effect = (
        lambda name: values[name] if name in values else read(name)
    )
    microscope.confirm_camera_exposures()
    exposures, sweeps = microscope.calculate_exposure_sweep_times()
    assert channel["camera_exposure_time"] == 20.0
    assert exposures["channel_1"] == pytest.approx(0.020064)
    assert sweeps["channel_1"] == pytest.approx(0.020064)
    microscope.set_camera_exposure_time(channel)
    assert microscope.current_exposure_time == pytest.approx(0.0007296)


def test_gui_can_preview_timing_before_switching_out_of_normal_mode(camera):
    camera.camera_controller.get_property_value.side_effect = lambda name: 1
    camera.camera_controller.get_property_range.return_value = (7.2e-6, 7.2e-6, 0)
    assert camera.calculate_light_sheet_exposure_time(0.01171, 20) == pytest.approx(
        (100.8e-6, 10.08e-6, 0.01180368)
    )
    camera.camera_controller.set_property_value.assert_not_called()


def test_invalid_driver_range_in_light_sheet_is_not_hidden(camera):
    camera.camera_controller.get_property_range.return_value = (None, None, None)
    with pytest.raises(RuntimeError, match="range"):
        camera.calculate_light_sheet_exposure_time(0.02, 20)


@pytest.mark.parametrize("requested", [0.0001, 0.001, 0.01])
def test_exposure_accepts_one_current_line_of_quantization(camera, requested):
    interval = 33.94909090909091e-6
    actual = math.ceil(requested / interval) * interval
    values = {
        "internal_line_interval": interval,
        "exposure_time": actual,
        "minimum_trigger_interval": 0.05652523636363636,
    }
    sdk = camera.camera_controller
    sdk.get_property_value.side_effect = values.__getitem__
    sdk.get_property_range.return_value = (interval, 1800.0, 1e-8)
    sdk.set_property_value.side_effect = lambda name, value, **kw: math.isclose(
        value, actual, rel_tol=0, abs_tol=kw.get("absolute_tolerance", 0)
    )
    assert camera.set_exposure_time(requested)
    assert camera.camera_exposure_time == pytest.approx(actual)
    assert camera.minimum_frame_interval == values["minimum_trigger_interval"]


@pytest.mark.parametrize("interval", [False, None, 0, -1, math.nan, math.inf])
def test_unknown_exposure_quantum_prevents_write(camera, interval):
    camera.camera_controller.get_property_value.side_effect = lambda name: interval
    with pytest.raises(RuntimeError, match="interval"):
        camera.set_exposure_time(0.001)
    camera.camera_controller.set_property_value.assert_not_called()


@pytest.mark.parametrize("actual", [False, None, math.nan, math.inf, -1, 0.01])
def test_exposure_rejects_unconfirmed_or_distant_readback(camera, actual):
    values = {
        "internal_line_interval": 33.94909090909091e-6,
        "exposure_time": actual,
        "minimum_trigger_interval": 0.01,
    }
    camera.camera_controller.get_property_value.side_effect = values.__getitem__
    camera.camera_controller.get_property_range.return_value = (
        33.94909090909091e-6,
        1800,
        1e-8,
    )
    with pytest.raises(RuntimeError, match="exposure"):
        camera.set_exposure_time(0.001)
