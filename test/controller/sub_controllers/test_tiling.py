import random
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(scope="module")
def tiling_wizard_controller(dummy_view, dummy_controller):
    from navigate.view.popups.tiling_wizard_popup import TilingWizardPopup
    from navigate.controller.sub_controllers.tiling import (
        TilingWizardController,
    )

    tiling_wizard = TilingWizardPopup(dummy_view)

    class SubController:
        def __init__(self):
            self.parent_controller = dummy_controller

    return TilingWizardController(tiling_wizard, SubController())


def test_traces(tiling_wizard_controller):
    """TODO: Find a way to access the actual lambda functions.

    If we can, inspect.getsource(myfunc) should provide us the lambda definition.
    """

    def assert_one_trace(var):
        tinfo = var.trace_info()
        assert len(tinfo) >= 1
        assert tinfo[0][0][0] == "write"
        assert "lambda" in tinfo[0][1]

    for ax in ["x", "y", "z", "f"]:
        # self.variables["x_start"], etc. should all be bound to two lambda functions
        # calling calculate_distance() and update_fov()
        for bound in ["start", "end"]:
            tinfo = tiling_wizard_controller.variables[f"{ax}_{bound}"].trace_info()
            assert len(tinfo) >= 1
            for ti in tinfo:
                assert ti[0][0] == "write"
                assert "lambda" in ti[1]

        # fov should be bound to one lambda, calling calculate_tiles()
        assert_one_trace(tiling_wizard_controller.variables[f"{ax}_fov"])

        # dist should be bound to one lambda, calling calculate_tiles()
        assert_one_trace(tiling_wizard_controller.variables[f"{ax}_dist"])

    # Special cases
    assert_one_trace(tiling_wizard_controller.variables["percent_overlap"])
    assert_one_trace(
        tiling_wizard_controller.cam_settings_widgets["FOV_X"].get_variable()
    )
    assert_one_trace(
        tiling_wizard_controller.cam_settings_widgets["FOV_Y"].get_variable()
    )
    assert_one_trace(
        tiling_wizard_controller.stack_acq_widgets["start_position"].get_variable()
    )
    assert_one_trace(
        tiling_wizard_controller.stack_acq_widgets["end_position"].get_variable()
    )
    # Channels tab controller binds these a bunch
    # assert_one_trace(
    #     tiling_wizard_controller.stack_acq_widgets["start_focus"].get_variable()
    # )
    # assert_one_trace(
    #     tiling_wizard_controller.stack_acq_widgets["end_focus"].get_variable()
    # )


def test_update_total_tiles(tiling_wizard_controller):
    tiling_wizard_controller.update_total_tiles()

    assert True


@pytest.mark.parametrize("axis", ["x", "y", "z", "f"])
def test_calculate_tiles(tiling_wizard_controller, axis):
    from navigate.tools.multipos_table_tools import calc_num_tiles

    ov, dist, fov = random.random(), random.random() * 100, random.random() * 10
    tiling_wizard_controller._percent_overlap = ov * 100
    tiling_wizard_controller.variables[f"{axis}_dist"].set(dist)
    tiling_wizard_controller.variables[f"{axis}_fov"].set(fov)
    tiling_wizard_controller.calculate_tiles(axis)

    if axis == "x" or axis == "y":
        dist += fov

    assert int(
        tiling_wizard_controller.variables[f"{axis}_tiles"].get()
    ) == calc_num_tiles(dist, ov, fov)


@pytest.mark.parametrize("axis", ["x", "y", "z", "f"])
def test_calculate_distance(tiling_wizard_controller, axis):
    start, end = random.random() * 10, random.random() * 100
    tiling_wizard_controller.variables[axis + "_start"].set(start)
    tiling_wizard_controller.variables[axis + "_end"].set(end)
    tiling_wizard_controller.calculate_distance(axis)
    assert float(tiling_wizard_controller.variables[axis + "_dist"].get()) == abs(
        start - end
    )


def test_update_overlap(tiling_wizard_controller):
    tiling_wizard_controller.variables["percent_overlap"].set("")
    tiling_wizard_controller.update_overlap()
    tiling_wizard_controller.variables["percent_overlap"].set("10")
    tiling_wizard_controller.update_overlap()

    assert True


@pytest.mark.parametrize("axis", ["x", "y", "z", "f"])
def test_update_fov(tiling_wizard_controller, axis):
    import random
    from navigate.tools.multipos_table_tools import sign

    if axis == "y":
        tiling_wizard_controller.cam_settings_widgets["FOV_X"].set(
            int(random.random() * 1000)
        )
        tiling_wizard_controller.variables["x_start"].set(random.random() * 10)
        tiling_wizard_controller.variables["x_end"].set(random.random() * 1000)
        var = float(
            tiling_wizard_controller.cam_settings_widgets["FOV_X"].get()
        ) * sign(
            float(tiling_wizard_controller.variables["x_end"].get())
            - float(tiling_wizard_controller.variables["x_start"].get())
        )
    elif axis == "x":
        tiling_wizard_controller.cam_settings_widgets["FOV_Y"].set(
            int(random.random() * 1000)
        )
        tiling_wizard_controller.variables["y_start"].set(random.random() * 10)
        tiling_wizard_controller.variables["y_end"].set(random.random() * 1000)
        var = float(
            tiling_wizard_controller.cam_settings_widgets["FOV_Y"].get()
        ) * sign(
            float(tiling_wizard_controller.variables["y_end"].get())
            - float(tiling_wizard_controller.variables["y_start"].get())
        )
    elif axis == "z":
        tiling_wizard_controller.stack_acq_widgets["start_position"].set(
            random.random() * 10
        )
        tiling_wizard_controller.stack_acq_widgets["end_position"].set(
            random.random() * 1000
        )
        var = float(
            tiling_wizard_controller.stack_acq_widgets["end_position"].get()
        ) - float(tiling_wizard_controller.stack_acq_widgets["start_position"].get())
    elif axis == "f":
        tiling_wizard_controller.stack_acq_widgets["start_focus"].set(
            random.random() * 10
        )
        tiling_wizard_controller.stack_acq_widgets["end_focus"].set(
            random.random() * 1000
        )
        var = float(
            tiling_wizard_controller.stack_acq_widgets["end_focus"].get()
        ) - float(tiling_wizard_controller.stack_acq_widgets["start_focus"].get())
    tiling_wizard_controller.update_fov(axis)

    assert float(tiling_wizard_controller.variables[f"{axis}_fov"].get()) == abs(var)


def test_set_table(tiling_wizard_controller):
    # from navigate.tools.multipos_table_tools import compute_tiles_from_bounding_box
    tiling_wizard_controller.stage_position_vars["theta"].set(0)
    tiling_wizard_controller.set_table()

    x_start = float(tiling_wizard_controller.variables["x_start"].get())
    x_stop = float(tiling_wizard_controller.variables["x_end"].get())

    y_start = float(tiling_wizard_controller.variables["y_start"].get())
    y_stop = float(tiling_wizard_controller.variables["y_end"].get())

    # shift z by coordinate origin of local z-stack
    z_start = float(tiling_wizard_controller.variables["z_start"].get()) - float(
        tiling_wizard_controller.stack_acq_widgets["start_position"].get()
    )
    z_stop = float(tiling_wizard_controller.variables["z_end"].get()) - float(
        tiling_wizard_controller.stack_acq_widgets["end_position"].get()
    )

    # Default to fixed theta. Empty widget values are treated as 0.0.
    r_start = float(tiling_wizard_controller.stage_position_vars["theta"].get() or 0.0)
    r_stop = float(tiling_wizard_controller.stage_position_vars["theta"].get() or 0.0)

    f_start = float(tiling_wizard_controller.variables["f_start"].get()) - float(
        tiling_wizard_controller.stack_acq_widgets["start_focus"].get()
    )
    f_stop = float(tiling_wizard_controller.variables["f_end"].get()) - float(
        tiling_wizard_controller.stack_acq_widgets["end_focus"].get()
    )

    # for consistency, always go from low to high
    def sort_vars(a, b):
        if a > b:
            return b, a
        return a, b

    x_start, x_stop = sort_vars(x_start, x_stop)
    y_start, y_stop = sort_vars(y_start, y_stop)
    z_start, z_stop = sort_vars(z_start, z_stop)
    r_start, r_stop = sort_vars(r_start, r_stop)
    f_start, f_stop = sort_vars(f_start, f_stop)

    assert tiling_wizard_controller.multipoint_table.model.df["X"].min() == x_start
    assert tiling_wizard_controller.multipoint_table.model.df["Y"].min() == y_start
    assert tiling_wizard_controller.multipoint_table.model.df["Z"].min() == z_start
    assert tiling_wizard_controller.multipoint_table.model.df["THETA"].min() == r_start
    assert tiling_wizard_controller.multipoint_table.model.df["F"].min() == f_start


def test_load_settings_uses_defaults_when_missing_file():
    from navigate.controller.sub_controllers.tiling import TilingWizardController

    class Var:
        def __init__(self):
            self.value = None

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    controller = TilingWizardController.__new__(TilingWizardController)
    controller._percent_overlap = 13.0
    controller._axes = ["x", "y", "z", "f"]
    controller.parent_controller = SimpleNamespace(
        parent_controller=SimpleNamespace(
            configuration_controller=SimpleNamespace(stage_step={"theta": 0.0})
        )
    )
    controller.variables = {"percent_overlap": Var(), "total_tiles": Var()}
    for axis in controller._axes:
        controller.variables[f"{axis}_start"] = Var()
        controller.variables[f"{axis}_end"] = Var()
        controller.variables[f"{axis}_dist"] = Var()
        controller.variables[f"{axis}_fov"] = Var()
        controller.variables[f"{axis}_tiles"] = Var()

    with (
        patch(
            "navigate.controller.sub_controllers.tiling.get_navigate_path",
            return_value="/tmp/navigate",
        ),
        patch(
            "navigate.controller.sub_controllers.tiling.os.path.exists",
            return_value=False,
        ),
    ):
        controller.load_settings()

    assert controller.variables["percent_overlap"].get() == 13.0
    assert controller.variables["total_tiles"].get() == 1
    assert controller.variables["x_start"].get() == 0.0
    assert controller.variables["x_tiles"].get() == 1


def test_load_settings_reads_existing_yaml_values():
    from navigate.controller.sub_controllers.tiling import TilingWizardController

    class Var:
        def __init__(self):
            self.value = None

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    positions = {
        "x_start": 1.0,
        "x_end": 2.0,
        "x_dist": 3.0,
        "x_fov": 4.0,
        "x_tiles": 5,
    }
    controller = TilingWizardController.__new__(TilingWizardController)
    controller._percent_overlap = 15.0
    controller._axes = ["x"]
    controller.parent_controller = SimpleNamespace(
        parent_controller=SimpleNamespace(
            configuration_controller=SimpleNamespace(stage_step={"theta": 0.0})
        )
    )
    controller.variables = {
        "percent_overlap": Var(),
        "total_tiles": Var(),
        "x_start": Var(),
        "x_end": Var(),
        "x_dist": Var(),
        "x_fov": Var(),
        "x_tiles": Var(),
    }

    with (
        patch(
            "navigate.controller.sub_controllers.tiling.get_navigate_path",
            return_value="/tmp/navigate",
        ),
        patch(
            "navigate.controller.sub_controllers.tiling.os.path.exists",
            return_value=True,
        ),
        patch(
            "navigate.controller.sub_controllers.tiling.load_yaml_file",
            return_value=positions,
        ),
    ):
        controller.load_settings()

    assert controller.variables["x_start"].get() == 1.0
    assert controller.variables["x_tiles"].get() == 5


def test_close_window_saves_state_and_removes_controller_attr():
    from navigate.controller.sub_controllers.tiling import TilingWizardController

    class Var:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    parent = SimpleNamespace(tiling_wizard_controller=object())
    controller = TilingWizardController.__new__(TilingWizardController)
    controller.variables = {"a": Var(1), "b": Var(2)}
    controller.view = SimpleNamespace(popup=SimpleNamespace(dismiss=MagicMock()))
    controller.parent_controller = parent

    with patch(
        "navigate.controller.sub_controllers.tiling.save_yaml_file"
    ) as mock_save:
        controller.close_window()

    mock_save.assert_called_once()
    controller.view.popup.dismiss.assert_called_once()
    assert not hasattr(parent, "tiling_wizard_controller")


def test_calculate_tiles_unknown_axis_logs_warning(tiling_wizard_controller):
    with patch(
        "navigate.controller.sub_controllers.tiling.logger.warning"
    ) as mock_warning:
        tiling_wizard_controller.calculate_tiles("unknown_axis")

    mock_warning.assert_called_once()


def test_calculate_tiles_marks_axis_invalid_on_inf_fov(tiling_wizard_controller):
    tiling_wizard_controller.variables["x_fov"].set("inf")
    tiling_wizard_controller.is_validated["x"] = True

    tiling_wizard_controller.calculate_tiles("x")

    assert tiling_wizard_controller.is_validated["x"] is False


def test_calculate_tiles_handles_value_error(tiling_wizard_controller):
    original_dist = tiling_wizard_controller.variables["x_dist"].get()
    tiling_wizard_controller.variables["x_fov"].set("10")
    tiling_wizard_controller.variables["x_dist"].set("not_a_number")
    tiling_wizard_controller.is_validated["x"] = True

    with patch(
        "navigate.controller.sub_controllers.tiling.logger.warning"
    ) as mock_warning:
        tiling_wizard_controller.calculate_tiles("x")

    assert tiling_wizard_controller.is_validated["x"] is False
    mock_warning.assert_called_once()
    tiling_wizard_controller.variables["x_dist"].set(original_dist)


def test_set_table_warns_when_input_is_invalid(tiling_wizard_controller):
    original = dict(tiling_wizard_controller.is_validated)
    tiling_wizard_controller.is_validated["x"] = False

    with (
        patch(
            "navigate.controller.sub_controllers.tiling.messagebox.showwarning"
        ) as mock_warning,
        patch(
            "navigate.controller.sub_controllers.tiling.compute_tiles_from_bounding_box"
        ) as mock_compute,
    ):
        tiling_wizard_controller.set_table()

    mock_warning.assert_called_once()
    mock_compute.assert_not_called()
    tiling_wizard_controller.is_validated = original


def test_set_table_updates_coupled_axis_step_size(tiling_wizard_controller):
    config = tiling_wizard_controller.parent_controller.parent_controller.configuration
    microscope_name = config["experiment"]["MicroscopeState"]["microscope_name"]
    scope = config["configuration"]["microscopes"][microscope_name]
    original_coupled_axes = scope["stage"].get("coupled_axes", None)
    scope["stage"]["coupled_axes"] = {"z": "F"}

    for axis in ["x", "y", "z", "f"]:
        tiling_wizard_controller.is_validated[axis] = True
    tiling_wizard_controller.variables["f_fov"].set(42.5)
    tiling_wizard_controller.stage_position_vars["theta"].set(0)

    with (
        patch(
            "navigate.controller.sub_controllers.tiling.compute_tiles_from_bounding_box",
            return_value=(["X"], [[0.0]]),
        ),
        patch("navigate.controller.sub_controllers.tiling.update_table"),
    ):
        tiling_wizard_controller.set_table()

    assert config["experiment"]["MicroscopeState"]["f_step_size"] == "42.5"
    scope["stage"]["coupled_axes"] = original_coupled_axes


def test_position_handler_stops_stage_and_sets_widget(tiling_wizard_controller):
    tiling_wizard_controller.stage_position_vars["x"].set(123.4)
    expected_position = tiling_wizard_controller.stage_position_vars["x"].get()
    set_mock = MagicMock()
    tiling_wizard_controller.widgets["x_start"].widget.set = set_mock

    parent = tiling_wizard_controller.parent_controller.parent_controller
    parent.execute = MagicMock()
    parent.view.after = MagicMock(side_effect=lambda _ms, callback: callback())

    handler = tiling_wizard_controller.position_handler("x", "start")
    handler()

    parent.execute.assert_called_once_with("stop_stage")
    parent.view.after.assert_called_once()
    set_mock.assert_called_once_with(expected_position)


def test_update_fov_switches_primary_axes(tiling_wizard_controller):
    original_primary_z = tiling_wizard_controller.primary_z_axis
    original_primary_f = tiling_wizard_controller.primary_f_axis
    original_z_device = tiling_wizard_controller.stack_acq_widgets["z_device"].get()
    original_f_device = tiling_wizard_controller.stack_acq_widgets["f_device"].get()

    new_z = "f" if original_primary_z != "f" else "z"
    new_f = "z" if original_primary_f != "z" else "f"

    tiling_wizard_controller.variables[f"{original_primary_z}_fov"].set(11.0)
    tiling_wizard_controller.variables[f"{new_z}_fov"].set(1.0)
    tiling_wizard_controller.stack_acq_widgets["z_device"].set(f"Device - {new_z}")
    tiling_wizard_controller.update_fov("z_device")
    assert tiling_wizard_controller.primary_z_axis == new_z
    assert float(tiling_wizard_controller.variables[f"{new_z}_fov"].get()) == 11.0
    assert (
        float(tiling_wizard_controller.variables[f"{original_primary_z}_fov"].get())
        == 0
    )

    tiling_wizard_controller.variables[f"{original_primary_f}_fov"].set(22.0)
    tiling_wizard_controller.variables[f"{new_f}_fov"].set(2.0)
    tiling_wizard_controller.stack_acq_widgets["f_device"].set(f"Device - {new_f}")
    tiling_wizard_controller.update_fov("f_device")
    assert tiling_wizard_controller.primary_f_axis == new_f
    assert float(tiling_wizard_controller.variables[f"{new_f}_fov"].get()) == 22.0
    assert (
        float(tiling_wizard_controller.variables[f"{original_primary_f}_fov"].get())
        == 0
    )

    tiling_wizard_controller.stack_acq_widgets["z_device"].set(original_z_device)
    tiling_wizard_controller.stack_acq_widgets["f_device"].set(original_f_device)


def test_update_fov_defaults_to_all_axes(tiling_wizard_controller):
    tiling_wizard_controller.variables["x_dist"].set(1)
    tiling_wizard_controller.variables["x_fov"].set(1)
    tiling_wizard_controller.variables["y_dist"].set(1)
    tiling_wizard_controller.variables["y_fov"].set(1)
    tiling_wizard_controller.variables["z_dist"].set(1)
    tiling_wizard_controller.variables["z_fov"].set(1)
    tiling_wizard_controller.variables["f_dist"].set(1)
    tiling_wizard_controller.variables["f_fov"].set(1)
    tiling_wizard_controller.update_fov()

    assert True


def test_update_fov_handles_conversion_error(tiling_wizard_controller):
    tiling_wizard_controller.cam_settings_widgets["FOV_X"].get = MagicMock(
        return_value="bad"
    )
    with patch("navigate.controller.sub_controllers.tiling.logger.debug") as mock_debug:
        tiling_wizard_controller.update_fov("y")

    mock_debug.assert_called_once()


def test_showup_brings_popup_to_front(tiling_wizard_controller):
    tiling_wizard_controller.view.popup.deiconify = MagicMock()
    tiling_wizard_controller.view.popup.attributes = MagicMock()

    tiling_wizard_controller.showup()

    tiling_wizard_controller.view.popup.deiconify.assert_called_once()
    tiling_wizard_controller.view.popup.attributes.assert_called_once_with(
        "-topmost", 1
    )
