import pytest


@pytest.mark.hardware
def test_remote_focus_ni_functions():
    import random

    from navigate.model.devices.daq.daq_ni import NIDAQ
    from navigate.model.devices.remote_focus.remote_focus_ni import RemoteFocusNI
    from navigate.model.dummy import DummyModel

    model = DummyModel()
    daq = NIDAQ(model.configuration)
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    rf = RemoteFocusNI(microscope_name, daq, model.configuration)

    funcs = ["adjust"]
    args = [
        [
            {"channel_1": 0.2, "channel_2": 0.1, "channel_3": 0.15},
            {"channel_1": 0.3, "channel_2": 0.2, "channel_3": 0.25},
        ]
    ]

    for f, a in zip(funcs, args):
        if a is not None:
            getattr(rf, f)(*a)
        else:
            getattr(rf, f)()
