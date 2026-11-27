"""Endpoint capture regressions and downstream coordinate compatibility."""

import copy
import xml.etree.ElementTree as ET
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from navigate.config.config import build_nested_dict
from navigate.controller.configuration_controller import ConfigurationController
from navigate.controller.controller import Controller
from navigate.controller.sub_controllers.channels_tab import ChannelsTabController
from navigate.controller.sub_controllers.tiling import TilingWizardController
from navigate.model.data_sources.bdv_data_source import BigDataViewerDataSource
from navigate.model.features.common_features import ZStackAcquisition
from navigate.model.microscope import Microscope
from navigate.tools.common_functions import copy_proxy_object
from navigate.view.main_window_content.channels_tab import ChannelsTab


@pytest.fixture
def controller(dummy_controller, tk_root):
    """Use real Tk traces and an isolated experiment; issue no hardware commands."""
    parent = copy.copy(dummy_controller)
    isolated = {}
    build_nested_dict(
        parent.manager,
        isolated,
        "configuration",
        copy_proxy_object(dummy_controller.configuration),
    )
    parent.configuration = isolated["configuration"]
    parent.configuration_controller = ConfigurationController(parent.configuration)
    parent.event_listeners = {}
    parent.commands = []
    view = ChannelsTab(tk_root)
    result = ChannelsTabController(view, parent)
    parent.channels_tab_controller = result
    result.populate_experiment_values()
    result.in_initialization = True
    result.z_origin = result.focus_origin = 0
    for name, value in {
        "start_position": 0,
        "end_position": 200,
        "start_focus": 0,
        "end_focus": 0,
        "step_size": 50,
    }.items():
        result.stack_acq_vals[name].set(value)
    result.in_initialization = False
    result.update_z_steps()
    yield result
    view.destroy()


def capture(controller: ChannelsTabController, button: str, z: float, f: float) -> None:
    """Press a capture button at a known stage position."""
    z_axis = controller.stack_acq_vals["z_device"].get().split(" - ")[1]
    f_axis = controller.stack_acq_vals["f_device"].get().split(" - ")[1]
    controller.parent_controller.configuration["experiment"]["StageParameters"].update(
        {z_axis: z, f_axis: f}
    )
    getattr(controller, f"update_{button}_position")()


def physical_pairs(controller: ChannelsTabController) -> list[tuple[float, float]]:
    """Return the physical pairs represented by the existing acquisition fields."""
    state = controller.microscope_state_dict
    return [
        (
            state["stack_z_origin"] + state[f"{endpoint}_position"],
            state["stack_focus_origin"] + state[f"{endpoint}_focus"],
        )
        for endpoint in ("start", "end")
    ]


@pytest.mark.parametrize("button", ["start", "end"])
@pytest.mark.parametrize("flipped", [False, True])
def test_first_capture_after_load_reanchors_uncaptured_offsets(
    controller, button: str, flipped: bool
) -> None:
    """One capture far from the load position must not create a huge stack."""
    parent = controller.parent_controller
    parent.configuration_controller.microscope_config["stage"]["flip_z"] = flipped
    parent.configuration["experiment"]["StageParameters"].update(z=0, f=0)
    controller.microscope_state_dict.update(
        start_position=50 if flipped else -50,
        end_position=-50 if flipped else 50,
        start_focus=5 if flipped else -5,
        end_focus=-5 if flipped else 5,
        step_size=0.5,
    )
    controller.populate_experiment_values()
    capture(controller, button, 5000, 100)
    expected = (
        [(5000, 100), (5050, 105)] if button == "start" else [(4950, 95), (5000, 100)]
    )
    assert physical_pairs(controller) == (expected[::-1] if flipped else expected)
    assert controller.microscope_state_dict["number_z_steps"] == 100
    assert parent.commands == []

    # The second capture must retain the first physical point, in either order.
    other = "end" if button == "start" else "start"
    next_point = (5200, 120) if button == "start" else (4800, 80)
    capture(controller, other, *next_point)
    assert sorted(physical_pairs(controller)) == sorted([(5000, 100), next_point])


@pytest.mark.parametrize("fresh", [False, True])
@pytest.mark.parametrize("button", ["start", "end"])
@pytest.mark.parametrize("flipped", [False, True])
@pytest.mark.parametrize("coordinate", ["position", "focus"])
@pytest.mark.parametrize("text", ["", "-"])
def test_incomplete_other_endpoint_warns_without_partial_capture(
    controller,
    monkeypatch,
    fresh: bool,
    button: str,
    flipped: bool,
    coordinate: str,
    text: str,
) -> None:
    """Invalid Tk input is recoverable and cannot change the capture context."""
    controller.parent_controller.configuration_controller.microscope_config["stage"][
        "flip_z"
    ] = flipped
    order = ("end", "start") if flipped else ("start", "end")
    if not fresh:
        # Crossed endpoints ensure field identity is distinct from button identity.
        capture(controller, "start", 300, 30)
        capture(controller, "end", 100, 10)
        order = controller._stack_endpoint_order
    field = next(
        field for field, owner in zip(("start", "end"), order) if owner != button
    )
    variable = controller.stack_acq_vals[f"{field}_{coordinate}"]
    valid = variable.get()
    variable.set(text)
    before = copy_proxy_object(controller.microscope_state_dict)
    context = controller._stack_endpoint_context
    assignments = controller._stack_endpoint_order
    origins = (controller.z_origin, controller.focus_origin)
    raw_fields = {
        name: controller.view.getvar(str(controller.stack_acq_vals[name]))
        for name in ("start_position", "end_position", "start_focus", "end_focus")
    }
    warning = Mock()
    monkeypatch.setattr(
        "navigate.controller.sub_controllers.channels_tab.messagebox.showwarning",
        warning,
    )
    capture(controller, button, 5000, 100)
    warning.assert_called_once()
    assert field.title() in warning.call_args.kwargs["message"]
    assert copy_proxy_object(controller.microscope_state_dict) == before
    assert controller._stack_endpoint_context == context
    assert controller._stack_endpoint_order == assignments
    assert (controller.z_origin, controller.focus_origin) == origins
    for name, value in raw_fields.items():
        assert controller.view.getvar(str(controller.stack_acq_vals[name])) == value
    assert controller.parent_controller.commands == []
    assert controller.in_initialization is False

    variable.set(valid)
    capture(controller, button, 5000, 100)
    assert (5000, 100) in physical_pairs(controller)
    warning.assert_called_once()


@pytest.mark.parametrize("buttons", [("start", "end"), ("end", "start")])
@pytest.mark.parametrize("flipped", [False, True])
@pytest.mark.parametrize("reverse_travel", [False, True])
def test_capture_order_preserves_legacy_stack(
    controller, buttons, flipped, reverse_travel
):
    """Either button order produces the same Z/F trajectory and legacy offsets."""
    config = controller.parent_controller.configuration_controller
    config.microscope_config["stage"]["flip_z"] = flipped
    endpoints = {"start": (100, 30), "end": (300, 10)}
    if reverse_travel:
        endpoints = {"start": endpoints["end"], "end": endpoints["start"]}
    for button in buttons:
        capture(controller, button, *endpoints[button])

    expected = [(100, 30), (300, 10)]
    assert physical_pairs(controller) == (expected[::-1] if flipped else expected)
    state = controller.microscope_state_dict
    assert state["stack_z_origin"] == 200
    assert state["stack_focus_origin"] == 20
    assert state["start_position"] == (100 if flipped else -100)
    assert state["end_position"] == (-100 if flipped else 100)
    assert state["step_size"] == (-50 if flipped else 50)
    assert state["number_z_steps"] == 4
    assert (state["abs_z_start"], state["abs_z_end"]) == (100, 300)
    assert controller.parent_controller.commands == []


@pytest.mark.parametrize("button", ["start", "end"])
@pytest.mark.parametrize("flipped", [False, True])
def test_recapture_retains_other_endpoint_across_crossings(controller, button, flipped):
    controller.parent_controller.configuration_controller.microscope_config["stage"][
        "flip_z"
    ] = flipped
    capture(controller, "start", 100, 10)
    capture(controller, "end", 300, 30)
    other = (300, 30) if button == "start" else (100, 10)
    for endpoint in [(400, 40), (50, 5), other, (200, 20)]:
        capture(controller, button, *endpoint)
        assert sorted(physical_pairs(controller)) == sorted([other, endpoint])


def test_capture_preserves_manual_edits_and_publishes_once(controller, monkeypatch):
    capture(controller, "start", 100, 10)
    capture(controller, "end", 300, 30)
    controller.stack_acq_vals["end_position"].set(150)
    controller.stack_acq_vals["end_focus"].set(25)
    assert controller.microscope_state_dict["end_focus"] == 25
    updates = []
    monkeypatch.setattr(
        controller,
        "update_timepoint_setting",
        lambda: updates.append(physical_pairs(controller)),
    )
    capture(controller, "start", 120, 12)
    assert updates == [[(120, 12), (350, 45)]]


def test_recapture_after_experiment_reload_discards_old_button_assignments(controller):
    capture(controller, "start", 300, 30)
    capture(controller, "end", 100, 10)
    # Experiment loading has always anchored offsets at StageParameters. Preserve
    # that behavior, while forgetting assignments belonging to the old captures.
    stage = controller.parent_controller.configuration["experiment"]["StageParameters"]
    stage.update(z=1000, f=100)
    controller.populate_experiment_values()
    assert physical_pairs(controller) == [(900, 90), (1100, 110)]
    capture(controller, "end", 1200, 120)
    assert physical_pairs(controller) == [(1100, 110), (1200, 120)]


def test_selected_axes_and_device_round_trip_reset_capture_assignments(controller):
    capture(controller, "start", 300, 30)
    capture(controller, "end", 100, 10)
    z_device = controller.stack_acq_vals["z_device"].get()
    # The assignments must be invalidated at the switch, even if the user comes
    # back to the original devices before pressing either capture button.
    controller.stack_acq_vals["z_device"].set("Synthetic - y")
    controller.stack_acq_vals["z_device"].set(z_device)
    capture(controller, "end", 400, 40)
    assert physical_pairs(controller) == [(300, 30), (400, 40)]
    controller.stack_acq_vals["z_device"].set("Synthetic - y")
    controller.stack_acq_vals["f_device"].set("Synthetic - x")
    capture(controller, "end", 600, 60)
    capture(controller, "start", 200, 20)
    assert physical_pairs(controller) == [(200, 20), (600, 60)]


@pytest.mark.parametrize("buttons", [("start", "end"), ("end", "start")])
def test_tiling_retains_stack_offsets_and_tile_coverage(
    controller, buttons, monkeypatch
):
    for button in buttons:
        capture(controller, button, *{"start": (100, 10), "end": (300, 30)}[button])
    wizard = TilingWizardController.__new__(TilingWizardController)
    wizard.parent_controller = controller
    wizard.primary_z_axis, wizard.primary_f_axis = "z", "f"
    wizard._axes = ["x", "y", "z", "f"]
    wizard._percent_overlap = 10
    wizard.is_validated = dict.fromkeys(wizard._axes, True)
    wizard.stack_acq_widgets = controller.stack_acq_widgets
    wizard.stage_position_vars = {"theta": SimpleNamespace(get=lambda: 0)}
    wizard.multipoint_table = object()
    wizard.variables = {}
    # Two Z tiles: physical coverage 100..300 and 280..480 (10% overlap).
    for axis, (start, stop, tiles, fov) in {
        "x": (0, 0, 1, 100),
        "y": (0, 0, 1, 100),
        "z": (100, 480, 2, 200),
        "f": (10, 30, 1, 20),
    }.items():
        for suffix, value in zip(
            ("start", "end", "tiles", "fov"), (start, stop, tiles, fov)
        ):
            wizard.variables[f"{axis}_{suffix}"] = SimpleNamespace(
                get=lambda v=value: v
            )
    table_updates = Mock()
    monkeypatch.setattr(
        "navigate.controller.sub_controllers.tiling.update_table", table_updates
    )
    wizard.set_table()
    _, rows, columns = table_updates.call_args.args
    z_values = np.asarray(rows)[:, columns.index("z")]
    f_values = np.asarray(rows)[:, columns.index("f")]
    np.testing.assert_allclose(z_values, [200, 380])
    np.testing.assert_allclose(f_values, [20, 20])
    state = controller.microscope_state_dict
    np.testing.assert_allclose(z_values + state["start_position"], [100, 280])
    np.testing.assert_allclose(z_values + state["end_position"], [300, 480])


@pytest.mark.parametrize("device_type", ["ASI", "Synthetic"])
def test_microscope_switch_keeps_offsets_and_resets_capture_context(
    controller, device_type
):
    """Exercise the real GUI switch and stage-offset calculation without devices."""
    capture(controller, "start", 300, 30)
    capture(controller, "end", 100, 10)
    parent = controller.parent_controller
    configuration = parent.configuration
    scopes = configuration["configuration"]["microscopes"]
    source_name = parent.configuration_controller.microscope_name
    target = copy_proxy_object(scopes[source_name])
    for stage in target["stage"]["hardware"]:
        stage["type"] = device_type
    target["stage"]["z_offset"] = scopes[source_name]["stage"].get("z_offset", 0) + 25
    target["stage"]["f_offset"] = scopes[source_name]["stage"].get("f_offset", 0) - 5
    build_nested_dict(parent.manager, scopes, "EndpointTarget", target)
    remote_focus = configuration["waveform_constants"]["remote_focus_constants"]
    build_nested_dict(
        parent.manager,
        remote_focus,
        "EndpointTarget",
        copy_proxy_object(remote_focus[source_name]),
    )
    for section in ("CameraParameters", "AutoFocusParameters"):
        entries = configuration["experiment"][section]
        if source_name in entries:
            build_nested_dict(
                parent.manager,
                entries,
                "EndpointTarget",
                copy_proxy_object(entries[source_name]),
            )

    stage = Mock()
    stage.move_absolute.return_value = True
    microscope = Microscope.__new__(Microscope)
    microscope.configuration = configuration
    microscope.microscope_name = "EndpointTarget"
    microscope.stages_list = [(stage, ["z", "f"])]
    microscope.get_stage_position = lambda: {"z_pos": 100, "f_pos": 10}
    assert microscope.move_stage_offset(source_name)
    stage.move_absolute.assert_called_once_with(
        {"z_abs": 125, "f_abs": 5}, wait_until_done=True
    )
    configuration["experiment"]["StageParameters"].update(z=125, f=5)
    parent.stage_controller = Mock()
    parent.camera_setting_controller = Mock()
    parent.camera_view_controller = Mock()
    zoom = configuration["experiment"]["MicroscopeState"]["zoom"]
    assert Controller.change_microscope(parent, "EndpointTarget", zoom)
    assert controller.stack_acq_vals["z_device"].get() == f"{device_type} - z"
    assert physical_pairs(controller) == [(25, -5), (225, 15)]
    capture(controller, "end", 325, 25)
    assert physical_pairs(controller) == [(225, 15), (325, 25)]
    assert parent.commands == []


@pytest.mark.parametrize("ext", ["h5", "n5"])
@pytest.mark.parametrize("buttons", [("start", "end"), ("end", "start")])
@pytest.mark.parametrize("positions,timepoints", [(2, 1), (1, 2)])
def test_bdv_saved_geometry_matches_legacy_stack(
    controller, tmp_path, ext, buttons, positions, timepoints
):
    """Save actual BDV volumes using the captured state and check pixels and XML."""
    for button in buttons:
        capture(controller, button, *{"start": (100, 10), "end": (300, 30)}[button])
    configuration = controller.parent_controller.configuration
    state = controller.microscope_state_dict
    state.update(
        image_mode="z-stack",
        is_multiposition=positions > 1,
        timepoints=timepoints,
        stack_cycling_mode="per_stack",
    )
    for channel in state["channels"].values():
        channel["is_selected"] = False
    for name in ("channel_1", "channel_2"):
        state["channels"][name]["is_selected"] = True
    configuration["multi_positions"] = [
        ["X", "Y", "Z", "THETA", "F"],
        [0, 0, 200, 0, 20],
        [100, 0, 380, 0, 40],
    ]
    configuration["multi_positions"] = configuration["multi_positions"][: positions + 1]
    scope = configuration["configuration"]["microscopes"][state["microscope_name"]]
    scope["stage"].pop("coupled_axes", None)
    scope["zoom"]["pixel_size"][state["zoom"]] = 1
    configuration["experiment"].pop("BDVParameters", None)
    camera = configuration["experiment"]["CameraParameters"][state["microscope_name"]]
    camera.update(img_x_pixels=4, img_y_pixels=4)
    # Use the real acquisition parameter readers, keeping the legacy excluded
    # end boundary: four planes at 100, 150, 200, 250 for the first tile.
    feature = ZStackAcquisition(SimpleNamespace())
    feature.get_z_stack_parameters(state)
    feature.get_f_stack_parameters(state)
    source = BigDataViewerDataSource(str(tmp_path / f"stack.{ext}"))
    source.set_metadata_from_configuration_experiment(configuration)
    try:
        for t in range(timepoints):
            for p, row in enumerate(configuration["multi_positions"][1:]):
                for c in range(2):
                    for z in range(feature.number_z_steps):
                        value = 100 * t + 20 * p + 5 * c + z
                        source.write(
                            np.full((4, 4), value, dtype=np.uint16),
                            x=row[0],
                            y=row[1],
                            z=row[2]
                            + feature.start_z_position
                            + z * feature.z_step_size,
                            theta=0,
                            f=row[4]
                            + feature.start_focus
                            + z * feature.focus_step_size,
                        )
        for t in range(timepoints):
            for p in range(positions):
                for c in range(2):
                    volume = source.get_slice(
                        slice(None), slice(None), c, slice(None), t, p
                    )
                    assert volume.shape == (4, 4, 4)
                    np.testing.assert_array_equal(
                        volume[:, 0, 0], 100 * t + 20 * p + 5 * c + np.arange(4)
                    )
    finally:
        source.close()
    root = ET.parse(tmp_path / "stack.xml").getroot()
    setups = root.findall("./SequenceDescription/ViewSetups/ViewSetup")
    assert len(setups) == 2 * positions
    for setup in setups:
        assert setup.findtext("size") == "4 4 4"
        np.testing.assert_allclose(
            np.fromstring(setup.findtext("voxelSize/size"), sep=" "), [1, 1, 50]
        )
    registrations = root.findall("./ViewRegistrations/ViewRegistration")
    assert len(registrations) == 2 * positions * timepoints
    for registration in registrations:
        p = int(registration.attrib["setup"]) // 2
        affine = np.fromstring(
            registration.findtext("ViewTransform/affine"), sep=" "
        ).reshape(3, 4)
        np.testing.assert_allclose(affine[:, :3], np.eye(3))
        np.testing.assert_allclose(affine[:, 3], [0, 100 * p, (175 + 180 * p) / 50])
