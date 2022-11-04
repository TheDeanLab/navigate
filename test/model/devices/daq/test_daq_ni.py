import pytest

@pytest.mark.hardware
def test_initialize_daq_ni():
    from aslm.model.devices.daq.daq_ni import NIDAQ
    from aslm.model.dummy import DummyModel

    model = DummyModel()
    daq = NIDAQ(model.configuration)

@pytest.mark.hardware
def test_daq_ni_functions():
    import random

    from aslm.model.devices.daq.daq_ni import NIDAQ
    from aslm.model.dummy import DummyModel

    model = DummyModel()
    daq = NIDAQ(model.configuration)
    microscope_name = model.configuration['experiment']['MicroscopeState']['microscope_name']

    funcs = ['enable_microscope', 'prepare_acquisition', 'run_acquisition', 'stop_acquisition']
    args = [[microscope_name], [list(daq.waveform_dict.keys())[0], random.random()], None, None]

    for f, a in zip(funcs, args):
        if a is not None:
            getattr(daq, f)(*a)
        else:
            getattr(daq, f)()
