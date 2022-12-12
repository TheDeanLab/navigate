def test_remote_focus_synthetic_functions():
    from aslm.model.devices.remote_focus.remote_focus_synthetic import SyntheticRemoteFocus
    from aslm.model.dummy import DummyModel

    model = DummyModel()
    microscope_name = model.configuration['experiment']['MicroscopeState']['microscope_name']
    rf = SyntheticRemoteFocus(microscope_name, None, model.configuration)

    funcs = ['prepare_task', 'start_task', 'stop_task', 'close_task']
    args = [['channel_dummy'], None, None, None]

    for f, a in zip(funcs, args):
        if a is not None:
            getattr(rf, f)(*a)
        else:
            getattr(rf, f)()
