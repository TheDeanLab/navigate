"""Idle Quest exposure probes restore timing and block capture on failed rollback."""

import math
import pytest
from test.model.devices.camera.test_quest2_lightsheet import camera  # noqa: F401


@pytest.fixture
def timed_camera(camera):  # noqa: F811
    c = camera
    values = {
        "sensor_mode": 1,
        "internal_line_interval": 33.94909090909091e-6,
        "exposure_time": 100 * 33.94909090909091e-6,
        "minimum_trigger_interval": 0.02,
    }
    c.camera_controller.get_property_value.side_effect = lambda name: values[name]
    c.camera_controller.get_property_range.side_effect = lambda name: (
        (7.2e-6, 1800, 1e-8) if name == "exposure_time" else (7.2e-6, 237.6e-6, 0.24e-6)
    )

    def write(name, value, **kwargs):
        if name == "exposure_time":
            interval = values["internal_line_interval"]
            value = math.ceil(value / interval - 1e-9) * interval
        values[name] = value
        return True

    c.camera_controller.set_property_value.side_effect = write
    c.camera_exposure_time = values["exposure_time"]
    c.minimum_frame_interval = values["minimum_trigger_interval"]
    c.y_pixels = 512
    return c, values


def test_normal_confirmation_returns_actual_and_restores_original_timing(timed_camera):
    c, values = timed_camera
    before = dict(values)
    result = c.confirm_exposure_timing(0.001)
    assert result.exposure_time == pytest.approx(0.0010184727272727272)
    assert result.sweep_time == result.exposure_time
    assert result.line_interval is None
    assert values == before
    assert c.camera_exposure_time == before["exposure_time"]


def test_light_sheet_confirmation_keeps_sweep_and_row_units(timed_camera):
    c, values = timed_camera
    values.update(
        sensor_mode=12, internal_line_interval=10.08e-6, exposure_time=0.001008
    )
    before = dict(values)
    result = c.confirm_exposure_timing(0.02, 20)
    assert result.exposure_time == pytest.approx(0.0007296)
    assert result.line_interval == pytest.approx(72.96e-6)
    assert result.sweep_time == pytest.approx(0.020064)
    assert values == before
    assert "line_interval" not in c.camera_parameters


def test_failed_probe_restores_original_values(timed_camera):
    c, values = timed_camera
    before = dict(values)
    write = c.camera_controller.set_property_value.side_effect
    c.camera_controller.set_property_value.side_effect = lambda name, value, **kw: (
        False
        if name == "exposure_time" and value != before[name]
        else write(name, value, **kw)
    )
    with pytest.raises(RuntimeError):
        c.confirm_exposure_timing(0.001)
    assert values == before
    assert c._setting_error() is None


def test_failed_exposure_restore_blocks_shared_camera(timed_camera):
    c, values = timed_camera
    old = values["exposure_time"]
    write = c.camera_controller.set_property_value.side_effect
    c.camera_controller.set_property_value.side_effect = lambda name, value, **kw: (
        False if name == "exposure_time" and value == old else write(name, value, **kw)
    )
    with pytest.raises(RuntimeError, match="reconnect|restor"):
        c.confirm_exposure_timing(0.001)
    assert c.camera_controller._advanced_settings_error
    with pytest.raises(RuntimeError):
        c.initialize_image_series([], 0)


def test_busy_confirmation_has_no_writes(timed_camera):
    c, _ = timed_camera
    c.is_acquiring = True
    with pytest.raises(RuntimeError):
        c.confirm_exposure_timing(0.001)
    c.camera_controller.set_property_value.assert_not_called()


@pytest.mark.parametrize("mode,width", [(1, 20), (12, None), (99, None)])
def test_confirmation_requires_actual_mode_match(timed_camera, mode, width):
    c, values = timed_camera
    values["sensor_mode"] = mode
    with pytest.raises((RuntimeError, ValueError)):
        c.confirm_exposure_timing(0.001, width)
    c.camera_controller.set_property_value.assert_not_called()
