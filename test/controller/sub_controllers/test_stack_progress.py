"""Real Tk schematic updates remain display-only and reject obsolete captures."""

from dataclasses import replace

import pytest

from navigate.tools.common_functions import copy_proxy_object
from test.controller.sub_controllers.test_stack_endpoint_order import (
    controller as controller,  # noqa: PLC0414 -- pytest fixture export
)
from test.tools.test_stack_progress import plan


def start(controller, relative=True, flipped=False):
    state = controller.microscope_state_dict
    state["image_mode"] = "z-stack"
    frame = controller.view.stack_acq_frame
    frame.position_mode.set("Relative" if relative else "Absolute")
    name = controller.parent_controller.configuration_controller.microscope_name
    token = (1, name)
    controller.set_mode("z-stack")
    controller.begin_stack_progress(token)
    progress_plan = plan(capture_token=token, relative=relative)
    if flipped:
        g = progress_plan.geometry
        progress_plan = replace(
            progress_plan,
            geometry=replace(g, z=replace(g.z, start=250, end=-250, step=-50)),
        )
    return frame, progress_plan


@pytest.mark.parametrize("relative", [False, True])
@pytest.mark.parametrize("flipped", [False, True])
def test_marker_moves_without_mutating_settings_or_creating_new_canvas_items(
    controller, relative, flipped
):
    frame, p = start(controller, relative, flipped)
    parent = controller.parent_controller
    before = copy_proxy_object(parent.configuration["experiment"])
    controller.update_stack_progress(p.snapshot(1))
    canvas = frame.relative_schematic
    ids = canvas.find_all()
    y1 = canvas.coords("acquisition_plane")[1]
    controller.update_stack_progress(p.snapshot(5))
    y2 = canvas.coords("acquisition_plane")[1]
    assert (y2 > y1) is flipped
    assert canvas.find_all() == ids
    assert canvas.itemcget("progress_slice", "text") == "Slice 5/10 · Ch 1"
    controller.update_stack_progress(p.snapshot(61))
    assert canvas.itemcget("progress_position", "text") == "Position 2/2 · Time 2/2"
    expected_z = "2250" if flipped else "1750"
    assert expected_z in canvas.itemcget("progress_coordinate", "text")
    assert copy_proxy_object(parent.configuration["experiment"]) == before
    assert parent.commands == []
    assert frame.cubic_image_label.winfo_manager() == ""
    assert frame.inputs["top"].winfo_manager() == ""
    controller.set_mode("stop")
    assert not canvas.find_withtag("acquisition_plane")
    assert frame.inputs["top"].winfo_manager() == "grid"
    assert (frame.cubic_image_label.winfo_manager() == "grid") is not relative
    controller.update_stack_progress(p.snapshot(80))
    assert not canvas.find_withtag("acquisition_plane")


@pytest.mark.parametrize("stale", ["token", "scope", "axis", "mode", "count", "reset"])
def test_stale_progress_cannot_overwrite_active_schematic(controller, stale):
    frame, p = start(controller)
    controller.update_stack_progress(p.snapshot(5))
    marker = frame.relative_schematic.coords("acquisition_plane")
    snapshot = p.snapshot(6)
    if stale == "token":
        snapshot = replace(snapshot, capture_token=(0, p.capture_token[1]))
    elif stale == "scope":
        snapshot = replace(snapshot, capture_token=(1, "other"))
    elif stale == "axis":
        snapshot = replace(snapshot, z_axis="x")
    elif stale == "mode":
        snapshot = replace(snapshot, relative=False)
    elif stale == "count":
        snapshot = p.snapshot(4)
    else:
        controller.begin_stack_progress((2, p.capture_token[1]))
        marker = []
    controller.update_stack_progress(snapshot)
    assert frame.relative_schematic.coords("acquisition_plane") == marker


def test_late_reference_cannot_replace_received_plane_and_reload_clears_token(
    controller,
):
    frame, p = start(controller)
    controller.update_stack_progress(p.snapshot(5))
    marker = frame.relative_schematic.coords("acquisition_plane")
    controller.set_stack_reference({"microscope_name": p.capture_token[1]})
    assert frame.relative_schematic.coords("acquisition_plane") == marker
    controller.populate_experiment_values()
    assert controller._stack_progress_token is None
    controller.update_stack_progress(p.snapshot(10))
    assert not frame.relative_schematic.find_withtag("acquisition_plane")
