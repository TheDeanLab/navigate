def test_remote_focus_synthetic_functions():
    from navigate.model.devices.remote_focus.remote_focus_synthetic import (
        SyntheticRemoteFocus,
    )
    from test.model.dummy import DummyModel

    model = DummyModel()
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    rf = SyntheticRemoteFocus(microscope_name, None, model.configuration)

    funcs = ["move"]
    args = [[0.1, None]]

    for f, a in zip(funcs, args):
        if a is not None:
            getattr(rf, f)(*a)
        else:
            getattr(rf, f)()
