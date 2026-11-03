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


@pytest.mark.parametrize("target", [-75.0, -12.5, 12.5, 75.0])
def test_existing_tiger_stage_maps_focus_to_piezo_without_new_driver(target):
    """Logical f uses P and 0.1 um commands, never the FTP slave F axis."""
    from navigate.model.devices.APIs.asi.asi_tiger_controller import TigerController

    controller = TigerController("unused-test-port", 115200)
    commands = []
    controller.send_command = commands.append
    controller.read_response = lambda: (
        ":A 125" if commands[-1].startswith("WHERE") else ":A"
    )
    controller.default_axes_sequence = ["X", "Y", "Z", "P"]
    config = {
        "configuration": {
            "microscopes": {
                "Scope": {
                    "stage": {
                        "hardware": {
                            "axes": ["f"],
                            "axes_mapping": ["P"],
                            "apply_default_settings": False,
                        },
                        "f_min": -75.0,
                        "f_max": 75.0,
                    }
                }
            }
        }
    }
    stage = ASIStage("Scope", controller, config)
    assert commands == []  # No motor-tuning writes on piezo initialization.
    assert stage.report_position() == {"f_pos": 12.5}
    assert stage.get_axis_position("f") == 12.5
    commands.clear()
    assert stage.move_axis_absolute("f", target)
    assert commands == [f"MOVE P={target * 10}\r"]
    commands.clear()
    stage.f_pos = 0.0
    assert stage.move_absolute({"f_abs": target})
    assert commands == [f"MOVE P={target * 10}\r"]
    commands.clear()
    assert stage.move_axis_absolute("f", -75.1) is False
    assert stage.move_absolute({"f_abs": 75.1}) is False
    assert commands == []
