"""Tiling uses active focus offsets, not the remembered disabled ramp."""

from unittest.mock import Mock

import pytest

from navigate.config.config import build_nested_dict
from navigate.controller.controller import Controller
from navigate.model.stack_acquisition import relative_geometry
from navigate.tools.common_functions import copy_proxy_object
from navigate.tools.stack_geometry import StackReference
from test.controller.sub_controllers.test_stack_endpoint_order import (
    controller as controller,  # noqa: PLC0414 -- pytest fixture export
)


@pytest.fixture
def open_wizard(controller, monkeypatch, tmp_path):
    """Open the real popup with isolated settings and capture its table output."""
    from navigate.controller.sub_controllers import tiling

    monkeypatch.setattr(
        controller.parent_controller.view.settings, "channels_tab", controller.view
    )
    monkeypatch.setattr(
        controller.parent_controller, "camera_setting_controller", Mock(), raising=False
    )
    monkeypatch.setattr(tiling, "get_navigate_path", lambda: str(tmp_path))
    monkeypatch.setattr(tiling, "save_yaml_file", Mock())
    table_updates = Mock()
    monkeypatch.setattr(tiling, "update_table", table_updates)
    errors = []
    monkeypatch.setattr(
        controller.view.winfo_toplevel(),
        "report_callback_exception",
        lambda *args: errors.append(args),
    )
    opened = []

    def create():
        controller.launch_tiling_wizard()
        wizard = controller.tiling_wizard_controller
        opened.append(wizard)
        return wizard, table_updates

    yield create
    for wizard in opened:
        if wizard.view.popup.winfo_exists():
            wizard.close_window()
    assert not errors


def set_relative_ramp(controller, focus_axis: str = "f") -> None:
    """Remember a nonzero ramp at a reference focus of 50 microns."""
    state = controller.microscope_state_dict
    state["image_mode"] = "z-stack"
    controller.stack_acq_vals["f_device"].set(f"Synthetic - {focus_axis}")
    controller.parent_controller.configuration["experiment"]["StageParameters"].update(
        {"z": 1000, focus_axis: 50}
    )
    frame = controller.view.stack_acq_frame
    frame.position_mode.set("Relative")
    frame.relative_focus_ramp.set(True)
    controller.stack_acq_vals["start_focus"].set(10)
    controller.stack_acq_vals["end_focus"].set(20)


def table_row(
    controller, wizard, table_updates, reference_focus: float = 50
) -> dict[str, float]:
    """Build one tile at reference Z=1000 and a constant focus coordinate."""
    for axis in wizard._axes:
        for endpoint in ("start", "end"):
            value = 0
            if axis == wizard.primary_z_axis:
                value = 1000 + controller.stack_acq_vals[f"{endpoint}_position"].get()
            elif axis == wizard.primary_f_axis:
                value = reference_focus
            wizard.variables[f"{axis}_{endpoint}"].set(value)
    table_updates.reset_mock()
    wizard.set_table()
    table_updates.assert_called_once()
    _, rows, columns = table_updates.call_args.args
    assert len(rows) == 1
    return {axis: float(value) for axis, value in zip(columns, rows[0])}


@pytest.mark.parametrize("open_before_disable", [False, True])
@pytest.mark.parametrize("focus_axis", ["f", "y"])
@pytest.mark.parametrize("flipped", [False, True])
def test_disabled_ramp_keeps_tiled_focus_at_reference(
    controller, open_wizard, open_before_disable: bool, focus_axis: str, flipped: bool
) -> None:
    """The 10/20 -> off sequence must produce focus 50, not 30, and FOV zero."""
    stage = controller.parent_controller.configuration_controller.microscope_config[
        "stage"
    ]
    stage["flip_z"] = flipped
    set_relative_ramp(controller, focus_axis)
    if open_before_disable:
        wizard, updates = open_wizard()
    controller.view.stack_acq_frame.relative_focus_ramp.set(False)
    if not open_before_disable:
        wizard, updates = open_wizard()
    assert wizard.primary_f_axis == focus_axis
    assert float(wizard.variables[f"{focus_axis}_fov"].get()) == 0
    row = table_row(controller, wizard, updates)
    assert row[focus_axis] == 50

    state = controller.microscope_state_dict
    assert (state["start_focus"], state["end_focus"]) == (0, 0)
    assert (state["relative_start_focus"], state["relative_end_focus"]) == (10, 20)
    assert (
        controller.stack_acq_vals["start_focus"].get(),
        controller.stack_acq_vals["end_focus"].get(),
    ) == (10, 20)
    geometry = relative_geometry(state, stage)
    reference = StackReference(row["z"], row[focus_axis])
    assert all(
        geometry.position(reference, plane)[1] == 50
        for plane in range(geometry.z.count)
    )
    assert controller.parent_controller.commands == []


def test_open_wizard_follows_mode_ramp_and_focus_edits(controller, open_wizard) -> None:
    """Current Tk values avoid a one-edit lag behind the experiment-state trace."""
    controller.stack_acq_vals["start_focus"].set(2)
    controller.stack_acq_vals["end_focus"].set(6)
    set_relative_ramp(controller)
    wizard, _ = open_wizard()
    frame = controller.view.stack_acq_frame
    assert float(wizard.variables["f_fov"].get()) == 10
    frame.relative_focus_ramp.set(False)
    assert float(wizard.variables["f_fov"].get()) == 0
    frame.relative_focus_ramp.set(True)
    assert float(wizard.variables["f_fov"].get()) == 10
    controller.stack_acq_vals["start_focus"].set(15)
    assert float(wizard.variables["f_fov"].get()) == 5
    frame.position_mode.set("Absolute")
    assert float(wizard.variables["f_fov"].get()) == 4
    frame.relative_focus_ramp.set(False)
    assert float(wizard.variables["f_fov"].get()) == 4
    frame.position_mode.set("Relative")
    assert float(wizard.variables["f_fov"].get()) == 0
    frame.relative_focus_ramp.set(True)
    assert float(wizard.variables["f_fov"].get()) == 5
    assert controller.parent_controller.commands == []


def test_reload_updates_open_wizard_without_discarding_saved_ramp(
    controller, open_wizard
) -> None:
    """Reloading a ramp-off experiment must replace the old focus FOV."""
    set_relative_ramp(controller)
    wizard, updates = open_wizard()
    controller.microscope_state_dict["relative_focus_ramp"] = False
    controller.populate_experiment_values()
    assert float(wizard.variables["f_fov"].get()) == 0
    row = table_row(controller, wizard, updates)
    assert row["f"] == 50
    controller.view.stack_acq_frame.relative_focus_ramp.set(True)
    assert float(wizard.variables["f_fov"].get()) == 10


@pytest.mark.parametrize("device_type", ["Synthetic", "ASI"])
def test_scope_change_keeps_ramp_off_tiling_on_the_new_reference(
    controller, open_wizard, device_type: str
) -> None:
    """Switch microscope implementations through the real controller path."""
    set_relative_ramp(controller)
    wizard, updates = open_wizard()
    frame = controller.view.stack_acq_frame
    frame.relative_focus_ramp.set(False)
    parent = controller.parent_controller
    config = parent.configuration
    source = parent.configuration_controller.microscope_name
    target = "FocusTarget"
    scopes = config["configuration"]["microscopes"]
    scope = copy_proxy_object(scopes[source])
    for stage in scope["stage"]["hardware"]:
        stage["type"] = device_type
    build_nested_dict(parent.manager, scopes, target, scope)
    for entries in (
        config["waveform_constants"]["remote_focus_constants"],
        config["experiment"]["CameraParameters"],
        config["experiment"]["AutoFocusParameters"],
    ):
        if source in entries:
            build_nested_dict(
                parent.manager, entries, target, copy_proxy_object(entries[source])
            )
    config["experiment"]["StageParameters"].update(z=2000, f=75)
    parent.stage_controller = Mock()
    parent.camera_view_controller = Mock()
    assert Controller.change_microscope(
        parent, target, controller.microscope_state_dict["zoom"]
    )
    assert controller.stack_acq_vals["f_device"].get() == f"{device_type} - f"
    assert float(wizard.variables["f_fov"].get()) == 0
    assert table_row(controller, wizard, updates, reference_focus=75)["f"] == 75
    frame.relative_focus_ramp.set(True)
    assert float(wizard.variables["f_fov"].get()) == 10
    assert parent.commands == []


def test_closed_wizard_unsubscribes_before_reopening(
    controller, open_wizard, monkeypatch
) -> None:
    """Old popups must not keep reacting to changes in the main window."""
    set_relative_ramp(controller)
    old, _ = open_wizard()
    old.close_window()
    stale_update = Mock()
    monkeypatch.setattr(old, "update_fov", stale_update)
    frame = controller.view.stack_acq_frame
    frame.relative_focus_ramp.set(False)
    frame.position_mode.set("Absolute")
    frame.position_mode.set("Relative")
    stale_update.assert_not_called()
    current, _ = open_wizard()
    assert float(current.variables["f_fov"].get()) == 0
    frame.relative_focus_ramp.set(True)
    assert float(current.variables["f_fov"].get()) == 10
    stale_update.assert_not_called()
