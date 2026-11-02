"""Preserving configured Tiger tuning when connecting a mixed stage profile."""

from unittest.mock import MagicMock
from multiprocessing import Manager

import pytest

from navigate.model.devices.stage.asi import ASIStage, MS2000Stage, MFC2000Stage


@pytest.fixture(scope="module")
def manager():
    with Manager() as instance:
        yield instance


@pytest.mark.parametrize("stage_class", [ASIStage, MS2000Stage, MFC2000Stage])
@pytest.mark.parametrize("apply_defaults", [None, True, False])
def test_controller_defaults_are_optional(apply_defaults, stage_class, manager):
    hardware = {"axes": ["x", "y", "z"], "axes_mapping": ["X", "Y", "Z"]}
    if apply_defaults is not None:
        hardware["apply_default_settings"] = apply_defaults
    config = {
        "configuration": {
            "microscopes": {
                "Scope": {
                    "stage": {"hardware": manager.list([manager.dict(hardware)])},
                    "zoom": {"pixel_size": {"1x": 4.6}},
                }
            }
        }
    }
    controller = MagicMock()
    controller.get_position.return_value = {"X": 100, "Y": 200, "Z": -300}
    stage = stage_class("Scope", controller, config)
    assert stage.axes_mapping == {"x": "X", "y": "Y", "z": "Z"}
    if apply_defaults is False:
        assert controller.mock_calls == []
    else:
        controller.set_feedback_alignment.assert_any_call("X", 85)
        assert controller.set_feedback_alignment.call_count == 3
        assert controller.set_finishing_accuracy.call_count == 3
        assert controller.set_error.call_count == 3
        assert controller.set_backlash.call_count == 3
        controller.set_speed_as_percent_max.assert_called_once_with(0.9)
    assert stage.report_position() == {"x_pos": 10.0, "y_pos": 20.0, "z_pos": -30.0}
    controller.get_position.assert_called_once_with(["X", "Y", "Z"])
