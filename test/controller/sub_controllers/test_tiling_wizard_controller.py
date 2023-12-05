import random
import pytest


@pytest.fixture(scope="module")
def tiling_wizard_controller(dummy_view, dummy_controller):
    from navigate.view.popups.tiling_wizard_popup2 import TilingWizardPopup
    from navigate.controller.sub_controllers.tiling_wizard_controller2 import (
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
        assert len(tinfo) == 1
        assert tinfo[0][0][0] == "write"
        assert "lambda" in tinfo[0][1]

    for ax in ["x", "y", "z", "f"]:
        # self.variables["x_start"], etc. should all be bound to two lambda functions
        # calling calculate_distance() and update_fov()
        for bound in ["start", "end"]:
            tinfo = tiling_wizard_controller.variables[f"{ax}_{bound}"].trace_info()
            assert len(tinfo) == 2
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
        tiling_wizard_controller.stack_acq_widgets["abs_z_start"].get_variable()
    )
    assert_one_trace(
        tiling_wizard_controller.stack_acq_widgets["abs_z_end"].get_variable()
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

    # Default to fixed theta
    r_start = tiling_wizard_controller.stage_position_vars["theta"].get()
    r_stop = tiling_wizard_controller.stage_position_vars["theta"].get()

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
    assert tiling_wizard_controller.multipoint_table.model.df["R"].min() == r_start
    assert tiling_wizard_controller.multipoint_table.model.df["F"].min() == f_start
