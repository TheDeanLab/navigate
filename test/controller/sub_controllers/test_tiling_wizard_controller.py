import random
import pytest


@pytest.fixture(scope="module")
def tiling_wizard_controller(dummy_view, dummy_controller):
    from aslm.view.popups.tiling_wizard_popup2 import TilingWizardPopup
    from aslm.controller.sub_controllers.tiling_wizard_controller2 import (
        TilingWizardController,
    )

    tiling_wizard = TilingWizardPopup(dummy_view)

    class SubController:
        def __init__(self):
            self.parent_controller = dummy_controller

    return TilingWizardController(tiling_wizard, SubController())


def test_update_total_tiles(tiling_wizard_controller):
    tiling_wizard_controller.update_total_tiles()

    assert True


@pytest.mark.parametrize("axis", ["x", "y", "z", "f"])
def test_calculate_tiles(tiling_wizard_controller, axis):
    from aslm.tools.multipos_table_tools import calc_num_tiles

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


def test_update_overlay(tiling_wizard_controller):
    tiling_wizard_controller.variables["percent_overlap"].set("")
    tiling_wizard_controller.update_overlay()
    tiling_wizard_controller.variables["percent_overlap"].set("10")
    tiling_wizard_controller.update_overlay()

    assert True


def test_update_fov(tiling_wizard_controller):
    tiling_wizard_controller.update_fov()


def test_set_table(tiling_wizard_controller):
    # print(tiling_wizard_controller.cam_settings_widgets["FOV_X"].get())
    tiling_wizard_controller.set_table()

    assert True
