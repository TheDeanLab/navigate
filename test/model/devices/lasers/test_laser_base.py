from navigate.model.devices.laser.synthetic import SyntheticLaser
from test.model.dummy import DummyModel
import random


def test_laser_base_functions():

    model = DummyModel()
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    laser = SyntheticLaser(microscope_name, None, model.configuration, 0)

    funcs = ["set_power", "turn_on", "turn_off", "close"]
    args = [[random.random()], None, None, None]

    for f, a in zip(funcs, args):
        if a is not None:
            getattr(laser, f)(*a)
        else:
            getattr(laser, f)()
