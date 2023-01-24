import pytest


@pytest.mark.hardware
def test_laser_ni_functions():
    import random

    from aslm.model.devices.lasers.laser_base import LaserNI
    from aslm.model.dummy import DummyModel

    model = DummyModel()
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    laser = LaserNI(microscope_name, None, model.configuration, 0)

    funcs = ["set_power", "turn_on", "turn_off", "close", "initialize_laser"]
    args = [[random.random()], None, None, None]

    for f, a in zip(funcs, args):
        if a is not None:
            getattr(laser, f)(*a)
        else:
            getattr(laser, f)()
