# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

import threading
from copy import deepcopy
from queue import SimpleQueue
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from navigate.model.device_startup_functions import load_devices
from navigate.model.features.update_setting import (
    ChangeResolution,
    UpdateExperimentSetting,
)
from navigate.model.microscope import Microscope


@pytest.fixture
def synthetic_microscope_model(dummy_model):
    microscope_name = dummy_model.active_microscope_name
    devices_dict = load_devices(
        microscope_name,
        dummy_model.configuration,
        is_synthetic=True,
    )
    microscope = Microscope(
        microscope_name,
        dummy_model.configuration,
        devices_dict,
        is_synthetic=True,
        is_virtual=False,
    )
    model = MagicMock()
    model.configuration = dummy_model.configuration
    model.active_microscope = microscope
    model.event_queue = MagicMock()
    model.image_writer = None
    model.frame_id = 99
    return model


def test_update_experiment_setting_applies_gui_channel_changes_to_next_acquisition(
    synthetic_microscope_model,
):
    model = synthetic_microscope_model
    microscope = model.active_microscope
    state = model.configuration["experiment"]["MicroscopeState"]
    original_channels = deepcopy(state["channels"])
    original_focus = microscope.get_stage_position()["f_pos"]

    updated_channels = deepcopy(original_channels)
    for channel in updated_channels.values():
        channel["is_selected"] = False
    filter_key = next(iter(microscope.filter_wheel.keys()))
    updated_channels["channel_2"].update(
        {
            "is_selected": True,
            "laser": "562nm",
            "laser_index": 1,
            "filter": "RFP - FF01-595/31-32",
            filter_key: "RFP - FF01-595/31-32",
            "filter_position": 2,
            "camera_exposure_time": 123.4,
            "laser_power": 37.5,
            "interval_time": "1",
            "defocus": 8.0,
        }
    )

    filter_wheel = next(iter(microscope.filter_wheel.values()))
    laser = microscope.laser["562"]
    filter_wheel.set_filter = MagicMock()
    laser.set_power = MagicMock(wraps=laser.set_power)
    microscope.daq.prepare_acquisition = MagicMock(
        wraps=microscope.daq.prepare_acquisition
    )

    try:
        feature = UpdateExperimentSetting(
            model,
            experiment_parameters={"MicroscopeState.channels": updated_channels},
        )

        assert feature.signal_func() is True

        assert microscope.available_channels == [2]
        assert microscope.current_channel == 2
        filter_wheel.set_filter.assert_any_call("RFP - FF01-595/31-32")
        laser.set_power.assert_called_with(37.5)
        assert microscope.camera.camera_exposure_time == pytest.approx(0.1234)
        microscope.daq.prepare_acquisition.assert_called_with("channel_2")
        assert microscope.get_stage_position()["f_pos"] == pytest.approx(
            microscope.zero_defocus_focus + 8.0
        )
        model.event_queue.put.assert_called_once()
        assert model.frame_id == 0
    finally:
        state["channels"] = original_channels
        microscope.move_stage({"f_abs": original_focus}, wait_until_done=True)


def test_update_experiment_setting_preserves_shared_channels_dict_and_laser_index(
    synthetic_microscope_model,
):
    model = synthetic_microscope_model
    state = model.configuration["experiment"]["MicroscopeState"]
    original_channels = deepcopy(state["channels"])
    gui_channel_setting_dict = state["channels"]
    gui_channel_1_setting_dict = gui_channel_setting_dict["channel_1"]

    try:
        feature = UpdateExperimentSetting(
            model,
            experiment_parameters={
                "MicroscopeState.channels": {
                    "channel_1": {
                        "laser_power": 100,
                        "laser": "488nm",
                        "laser_index": 1,
                    }
                }
            },
        )

        assert feature.signal_func() is True

        assert gui_channel_setting_dict["channel_1"]["laser_power"] == 100
        assert gui_channel_setting_dict["channel_1"]["laser"] == "488nm"
        assert gui_channel_setting_dict["channel_1"]["laser_index"] == 0
        assert gui_channel_1_setting_dict["laser_power"] == 100
        assert gui_channel_1_setting_dict["laser"] == "488nm"
        assert gui_channel_1_setting_dict["laser_index"] == 0
    finally:
        gui_channel_setting_dict.clear()
        gui_channel_setting_dict.update(original_channels)


def make_change_resolution_model():
    """Build the complete model contract consumed by ChangeResolution."""
    task = SimpleNamespace(cancel_event=threading.Event())
    model = MagicMock()
    model.configuration = {
        "configuration": {
            "microscopes": {
                "low": {"zoom": {"position": {"1x": {}}}},
                "high": {"zoom": {"position": {"1x": {}}}},
            }
        },
        "experiment": {
            "CameraParameters": {
                "low": {"img_x_pixels": 2048, "img_y_pixels": 2048},
                "high": {"img_x_pixels": 2048, "img_y_pixels": 2048},
            },
            "MicroscopeState": {"microscope_name": "low", "zoom": "1x"},
        },
    }
    model.active_microscope_name = "low"
    model.active_microscope = MagicMock()
    model.event_queue = SimpleQueue()
    model._begin_resolution_change.return_value = task
    model._perform_resolution_change.return_value = False
    model.change_resolution.return_value = False
    model.stop_acquisition = False
    model.stop_send_signal = False
    return model, task


def test_change_resolution_feature_does_not_prepare_after_cancellation():
    model, task = make_change_resolution_model()
    feature = ChangeResolution(model, "high", "1x")

    result = feature.signal_func()

    assert result is False
    assert model.stop_acquisition is True
    assert model.stop_send_signal is True
    model.active_microscope.prepare_acquisition.assert_not_called()
    model.active_microscope.prepare_next_channel.assert_not_called()
    assert model.event_queue.empty()
    model._finish_resolution_change.assert_called_once_with(task, False)
