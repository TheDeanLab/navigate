import copy
import importlib
import sys
import types
from unittest.mock import MagicMock

import numpy as np
import pytest


MODULE_PATH = "navigate.model.devices.remote_focus.base"
WAVEFORMS_MODULE_PATH = "navigate.model.waveforms"


@pytest.fixture
def base_module(monkeypatch):
    real_waveforms = importlib.import_module(WAVEFORMS_MODULE_PATH)
    fake_waveforms = types.ModuleType(WAVEFORMS_MODULE_PATH)
    fake_waveforms.__dict__.update(real_waveforms.__dict__)
    fake_waveforms.remote_focus_ramp = lambda **kwargs: np.zeros(1, dtype=float)
    fake_waveforms.remote_focus_ramp_triangular = lambda **kwargs: np.zeros(1, dtype=float)
    fake_waveforms.smooth_waveform = lambda waveform, percent_smoothing: waveform

    monkeypatch.setitem(sys.modules, WAVEFORMS_MODULE_PATH, fake_waveforms)

    sys.modules.pop(MODULE_PATH, None)
    module = importlib.import_module(MODULE_PATH)
    return importlib.reload(module)


def _build_config(
    sensor_mode="Widefield",
    readout_direction="Top-to-Bottom",
    percent_smoothing="0",
):
    return {
        "configuration": {
            "microscopes": {
                "TestScope": {
                    "remote_focus": {
                        "hardware": {
                            "max": 1.0,
                            "min": -1.0,
                            "channel": "Dev7/ao3",
                            "axis": "B",
                        }
                    },
                    "daq": {"sample_rate": 10, "trigger_source": "PFI1"},
                }
            }
        },
        "experiment": {
            "CameraParameters": {
                "TestScope": {
                    "sensor_mode": sensor_mode,
                    "readout_direction": readout_direction,
                }
            },
            "MicroscopeState": {
                "microscope_name": "test_mode",
                "zoom": "1x",
                "channels": {
                    "ch1": {"is_selected": True, "laser": "488"},
                    "ch2": {"is_selected": False, "laser": "561"},
                },
            },
        },
        "waveform_constants": {
            "other_constants": {
                "camera_delay": "5",
                "remote_focus_ramp_falling": "20",
                "remote_focus_delay": "10",
                "percent_smoothing": str(percent_smoothing),
            },
            "remote_focus_constants": {
                "test_mode": {
                    "1x": {
                        "488": {"amplitude": "2.5", "offset": "0.1"},
                        "561": {"amplitude": "1.0", "offset": "0.0"},
                    }
                }
            },
        },
    }


def _make_remote_focus(base_module, config):
    class _ConcreteRemoteFocus(base_module.RemoteFocusBase):
        def move(self, exposure_times, sweep_times, offset=None):
            return None

    return _ConcreteRemoteFocus("TestScope", None, copy.deepcopy(config))


def test_adjust_ramp_branch_with_smoothing_and_clipping(base_module, monkeypatch):
    config = _build_config(percent_smoothing="25")
    laser_constants = config["waveform_constants"]["remote_focus_constants"]["test_mode"][
        "1x"
    ]["488"]
    laser_constants["amplitude"] = "-"
    laser_constants["offset"] = "."

    waveform_constants = config.pop("waveform_constants")
    rf = _make_remote_focus(base_module, config)
    rf.configuration["waveform_constants"] = waveform_constants
    rf.waveform_dict = {"stale_key": np.array([0.0])}

    ramp_kwargs = {}

    def fake_ramp(**kwargs):
        ramp_kwargs.update(kwargs)
        return np.array([-2.0, 0.5, 1.8, 0.1], dtype=float)

    smooth_mock = MagicMock(
        return_value=np.array([-2.0, 0.5, 1.8, 0.1, 0.0], dtype=float)
    )
    triangle_mock = MagicMock(side_effect=AssertionError("triangle branch not expected"))

    monkeypatch.setattr(base_module, "remote_focus_ramp", fake_ramp)
    monkeypatch.setattr(base_module, "smooth_waveform", smooth_mock)
    monkeypatch.setattr(base_module, "remote_focus_ramp_triangular", triangle_mock)

    waveforms = rf.adjust(
        exposure_times={"ch1": 0.1, "ch2": 0.05},
        sweep_times={"ch1": 0.3, "ch2": 0.15},
        offset=0.25,
    )

    assert waveforms["stale_key"] is None
    assert "ch2" not in waveforms
    np.testing.assert_allclose(waveforms["ch1"], np.array([-1.0, 0.5, 1.0]))

    assert ramp_kwargs["sample_rate"] == 10
    assert ramp_kwargs["exposure_time"] == 0.1
    assert ramp_kwargs["sweep_time"] == 0.3
    assert ramp_kwargs["remote_focus_delay"] == pytest.approx(0.01)
    assert ramp_kwargs["camera_delay"] == pytest.approx(0.005)
    assert ramp_kwargs["fall"] == pytest.approx(0.02)
    assert ramp_kwargs["amplitude"] == 0.0
    assert ramp_kwargs["offset"] == pytest.approx(0.25)

    called_waveform = smooth_mock.call_args.kwargs["waveform"]
    np.testing.assert_allclose(called_waveform, np.array([-2.0, 0.5, 1.8, 0.1]))
    assert smooth_mock.call_args.kwargs["percent_smoothing"] == 25.0
    triangle_mock.assert_not_called()


def test_adjust_triangle_branch_rev_bidirectional(base_module, monkeypatch):
    config = _build_config(
        sensor_mode="Light-Sheet",
        readout_direction="Rev. Bidirectional",
        percent_smoothing="10",
    )
    rf = _make_remote_focus(base_module, config)

    triangle_kwargs = {}

    def fake_triangle(**kwargs):
        triangle_kwargs.update(kwargs)
        return np.array([0.2, 0.4], dtype=float)

    ramp_mock = MagicMock(side_effect=AssertionError("ramp branch not expected"))
    smooth_mock = MagicMock(return_value=np.array([0.2, 0.4, 0.6, 0.8, 1.1], dtype=float))

    monkeypatch.setattr(base_module, "remote_focus_ramp_triangular", fake_triangle)
    monkeypatch.setattr(base_module, "remote_focus_ramp", ramp_mock)
    monkeypatch.setattr(base_module, "smooth_waveform", smooth_mock)

    waveforms = rf.adjust(
        exposure_times={"ch1": 0.05, "ch2": 0.03},
        sweep_times={"ch1": 0.2, "ch2": 0.2},
    )

    np.testing.assert_allclose(waveforms["ch1"], np.array([0.2, 0.4, 0.6, 0.8]))
    assert len(waveforms["ch1"]) == 4
    assert triangle_kwargs["sample_rate"] == 10
    assert triangle_kwargs["exposure_time"] == 0.05
    assert triangle_kwargs["sweep_time"] == 0.2
    assert triangle_kwargs["remote_focus_delay"] == pytest.approx(0.01)
    assert triangle_kwargs["camera_delay"] == pytest.approx(0.005)
    assert triangle_kwargs["amplitude"] == 2.5
    assert triangle_kwargs["offset"] == 0.1
    ramp_mock.assert_not_called()
    smooth_mock.assert_called_once()


def test_adjust_triangle_branch_without_smoothing(base_module, monkeypatch):
    config = _build_config(
        sensor_mode="Light-Sheet",
        readout_direction="Bidirectional",
        percent_smoothing="0",
    )
    rf = _make_remote_focus(base_module, config)

    triangle_mock = MagicMock(return_value=np.array([-2.0, 0.0, 2.0, 0.1], dtype=float))
    ramp_mock = MagicMock(side_effect=AssertionError("ramp branch not expected"))
    smooth_mock = MagicMock(side_effect=AssertionError("smooth should not be called"))

    monkeypatch.setattr(base_module, "remote_focus_ramp_triangular", triangle_mock)
    monkeypatch.setattr(base_module, "remote_focus_ramp", ramp_mock)
    monkeypatch.setattr(base_module, "smooth_waveform", smooth_mock)

    waveforms = rf.adjust(
        exposure_times={"ch1": 0.05, "ch2": 0.05},
        sweep_times={"ch1": 0.2, "ch2": 0.2},
    )

    np.testing.assert_allclose(waveforms["ch1"], np.array([-1.0, 0.0, 1.0, 0.1]))
    triangle_mock.assert_called_once()
    ramp_mock.assert_not_called()
    smooth_mock.assert_not_called()
