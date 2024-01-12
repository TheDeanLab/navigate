def test_initialize_daq_synthetic():
    from navigate.model.devices.daq.daq_synthetic import SyntheticDAQ
    from test.model.dummy import DummyModel

    model = DummyModel()
    daq = SyntheticDAQ(model.configuration)


def test_synthetic_daq_functions():
    import random

    from navigate.model.devices.daq.daq_synthetic import SyntheticDAQ
    from test.model.dummy import DummyModel

    model = DummyModel()
    daq = SyntheticDAQ(model.configuration)
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]

    funcs = [
        "add_camera",
        "create_camera_task",
        "create_master_trigger_task",
        "create_galvo_remote_focus_tasks",
        "start_tasks",
        "stop_tasks",
        "close_tasks",
        "prepare_acquisition",
        "run_acquisition",
        "stop_acquisition",
        "write_waveforms_to_tasks",
    ]
    args = [
        [microscope_name, model.camera[microscope_name]],
        None,
        None,
        None,
        None,
        None,
        None,
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
