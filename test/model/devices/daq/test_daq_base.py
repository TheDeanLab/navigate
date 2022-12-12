def test_initialize_daq():
    from aslm.model.devices.daq.daq_base import DAQBase
    from aslm.model.dummy import DummyModel

    model = DummyModel()
    daq = DAQBase(model.configuration)


def test_calculate_all_waveforms():
    import numpy as np

    from aslm.model.devices.daq.daq_base import DAQBase
    from aslm.model.dummy import DummyModel

    model = DummyModel()
    daq = DAQBase(model.configuration)
    microscope_name = model.configuration['experiment']['MicroscopeState']['microscope_name']
    waveform_dict = daq.calculate_all_waveforms(microscope_name, np.random.rand())

    for k, v in waveform_dict.items():
        try:
            channel = model.configuration['experiment']['MicroscopeState']['channels'][k]
            if not channel['is_selected']:
                continue
            exposure_time = channel['camera_exposure_time']/1000
            print(k, channel['is_selected'], np.sum(v>0), exposure_time)
            assert(np.sum(v>0) == daq.sample_rate*exposure_time) 
        except KeyError:
            # The channel doesn't exist. Points to an issue in how waveform dict is created.
            continue
