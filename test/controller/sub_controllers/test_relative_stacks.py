"""Relative-mode UI traces preserve absolute endpoints and acquisition ownership."""

import pytest
import yaml

from navigate.config.config import build_nested_dict
from navigate.tools.file_functions import save_yaml_file
from test.controller.sub_controllers.test_stack_endpoint_order import (
    capture,
    physical_pairs,
)
from test.controller.sub_controllers.test_stack_endpoint_order import (
    controller as controller,  # noqa: PLC0414 -- explicit pytest fixture export
)


def relative(controller, extent=500):
    controller.microscope_state_dict["image_mode"] = "z-stack"
    frame = controller.view.stack_acq_frame
    frame.relative_range.set(extent)
    frame.position_mode.set("Relative")
    return frame


def test_relative_preview_follows_position_until_acquisition_then_freezes(controller):
    frame = relative(controller)
    state = controller.microscope_state_dict
    positions = controller.parent_controller.configuration["experiment"][
        "StageParameters"
    ]
    positions.update(z=1000, f=50)
    controller.refresh_stack_reference_preview()
    assert (state["abs_z_start"], state["abs_z_end"]) == (750, 1250)
    assert (state["start_focus"], state["end_focus"]) == (0, 0)
    assert state["stack_focus_origin"] == 50
    controller.mode = "z-stack"
    positions.update(z=2000, f=80)
    controller.refresh_stack_reference_preview()
    assert state["stack_z_origin"] == 1000
    controller.set_stack_reference(
        {
            "microscope_name": controller.parent_controller.configuration_controller.microscope_name,
            "z": 1000,
            "focus": 50,
            "multiposition": False,
        }
    )
    text = [
        frame.idle_schematic.itemcget(i, "text")
        for i in frame.idle_schematic.find_all()
        if frame.idle_schematic.type(i) == "text"
    ]
    assert "Frozen at Acquire" in text
    controller.mode = "stop"
    controller.refresh_stack_reference_preview()
    assert state["stack_z_origin"] == 2000
    controller.set_stack_reference(
        {
            "microscope_name": state["microscope_name"],
            "z": 1000,
            "focus": 50,
            "multiposition": False,
        }
    )
    assert state["stack_z_origin"] == 2000  # Late events cannot revive a stopped run.
    assert controller.parent_controller.commands == []


def test_toggle_preserves_fixed_endpoints_and_ramp_settings_without_moving(controller):
    capture(controller, "start", 100, 10)
    capture(controller, "end", 300, 30)
    expected = physical_pairs(controller)
    frame = relative(controller)
    frame.relative_focus_ramp.set(True)
    controller.stack_acq_vals["start_focus"].set(-5)
    controller.stack_acq_vals["end_focus"].set(5)
    assert controller.microscope_state_dict["start_focus"] == -5
    frame.relative_focus_ramp.set(False)
    assert controller.microscope_state_dict["start_focus"] == 0
    # Disabled inputs remain visible and retain the saved ramp, but cannot edit
    # the effective constant-focus stack while the ramp is off.
    for endpoint, saved in (("start", -5), ("end", 5)):
        widget = frame.inputs[f"{endpoint}_focus"].widget
        widget.delete(0, "end")
        widget.insert(0, "999")
        assert controller.stack_acq_vals[f"{endpoint}_focus"].get() == saved
        assert controller.microscope_state_dict[f"{endpoint}_focus"] == 0
    frame.position_mode.set("Absolute")
    assert physical_pairs(controller) == expected
    frame.position_mode.set("Relative")
    frame.relative_focus_ramp.set(True)
    assert (
        controller.microscope_state_dict["start_focus"],
        controller.microscope_state_dict["end_focus"],
    ) == (-5, 5)
    assert controller.parent_controller.commands == []


@pytest.mark.parametrize("extent", [0, -1, float("nan"), float("inf")])
def test_invalid_relative_range_cannot_leave_a_valid_previous_stack(controller, extent):
    frame = relative(controller)
    frame.relative_range.set(extent)
    assert controller.microscope_state_dict["number_z_steps"] == 0
    assert controller._relative_stack_error


def test_relative_mode_reload_and_capture_shortcuts(controller, tmp_path):
    frame = relative(controller, 400)
    state = controller.microscope_state_dict
    assert save_yaml_file(str(tmp_path), state)
    saved = yaml.safe_load((tmp_path / "experiment.yml").read_text())
    parent = controller.parent_controller
    build_nested_dict(
        parent.manager, parent.configuration["experiment"], "MicroscopeState", saved
    )
    controller.populate_experiment_values()
    state = controller.microscope_state_dict
    assert frame.position_mode.get() == "Relative"
    assert frame.relative_range.get() == 400
    before = (state["start_position"], state["end_position"], state["stack_z_origin"])
    capture(controller, "end", 1234, 99)
    assert (
        state["start_position"],
        state["end_position"],
        state["stack_z_origin"],
    ) == before
    assert str(controller.stack_acq_buttons["set_end"].cget("state")) == "disabled"
    assert (
        str(controller.stack_acq_widgets["start_position"].widget.cget("state"))
        == "readonly"
    )


def test_switching_scope_reanchors_restored_absolute_offsets(controller):
    capture(controller, "start", 100, 10)
    capture(controller, "end", 300, 30)
    frame = relative(controller)
    controller.microscope_state_dict["absolute_stack_context"] = ("other", "z", "f")
    controller.parent_controller.configuration["experiment"]["StageParameters"].update(
        z=125, f=5
    )
    frame.position_mode.set("Absolute")
    assert physical_pairs(controller) == [(25, -5), (225, 15)]


def test_relative_controls_and_schematic_switch_with_mode(controller):
    frame = relative(controller)
    assert frame.relative_controls.winfo_manager() == "grid"
    assert frame.idle_schematic.winfo_manager() == "grid"
    assert frame.inputs["start_focus"].winfo_manager() == "grid"
    assert str(frame.inputs["start_focus"].widget.cget("state")) == "disabled"
    assert frame.buttons["set_start"].winfo_manager() == "grid"
    assert frame.buttons["set_start"].instate(["disabled"])
    assert not frame.relative_focus_ramp_widget.instate(["disabled"])
    assert frame.mode_frame.grid_info()["row"] < frame.stack_frame.grid_info()["row"]
    frame.relative_focus_ramp.set(True)
    assert frame.inputs["start_focus"].winfo_manager() == "grid"
    assert str(frame.inputs["start_focus"].widget.cget("state")) == "normal"
    controller.mode = "z-stack"
    controller._configure_stack_position_mode()
    assert str(frame.position_mode_widget.cget("state")) == "disabled"
    assert str(frame.relative_range_widget.widget.cget("state")) == "disabled"
    assert str(frame.inputs["start_focus"].widget.cget("state")) == "disabled"
    assert frame.relative_focus_ramp_widget.instate(["disabled"])
    controller.mode = "stop"
    frame.position_mode.set("Absolute")
    assert frame.idle_schematic.winfo_manager() == "grid"
    assert frame.relative_controls.winfo_manager() == "grid"
    assert str(frame.relative_range_widget.widget.cget("state")) == "disabled"
    assert frame.relative_focus_ramp_widget.instate(["disabled"])
    assert str(frame.inputs["start_focus"].widget.cget("state")) == "normal"
    assert frame.buttons["set_start"].winfo_manager() == "grid"
    assert not frame.buttons["set_start"].instate(["disabled"])
