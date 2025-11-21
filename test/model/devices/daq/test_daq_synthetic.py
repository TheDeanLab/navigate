def test_initialize_daq_synthetic():
    from navigate.model.devices.daq.synthetic import SyntheticDAQ
    from test.model.dummy import DummyModel

    model = DummyModel()
    _ = SyntheticDAQ(model.configuration)


def test_synthetic_daq_functions():
    import random

    from navigate.model.devices.daq.synthetic import SyntheticDAQ
    from test.model.dummy import DummyModel

    model = DummyModel()
    daq = SyntheticDAQ(model.configuration)
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]

    funcs = [
        "add_camera",
        "prepare_acquisition",
        "run_acquisition",
        "stop_acquisition",
        "wait_acquisition_done",
    ]
    args = [
        [microscope_name, model.camera[microscope_name]],
        [f"channel_{random.randint(1, 5)}"],
        None,
        None,
        None,
    ]

    for f, a in zip(funcs, args):
        if a is not None:
            getattr(daq, f)(*a)
        else:
            getattr(daq, f)()
