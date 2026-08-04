# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Tests for cancellable feature-driven setting updates."""

import threading
from queue import SimpleQueue
from types import SimpleNamespace
from unittest.mock import MagicMock

from navigate.model.features.update_setting import ChangeResolution


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
