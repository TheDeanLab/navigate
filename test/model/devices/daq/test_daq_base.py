from navigate.model.devices.daq.synthetic import SyntheticDAQ
from test.model.dummy import DummyModel
import numpy as np


def test_initialize_daq():
    model = DummyModel()
    SyntheticDAQ(model.configuration)


def test_calculate_all_waveforms():
    model = DummyModel()
    daq = SyntheticDAQ(model.configuration)
    microscope_state = model.configuration["experiment"]["MicroscopeState"]
    microscope_name = microscope_state["microscope_name"]
    exposure_times = {
        k: v["camera_exposure_time"] / 1000
        for k, v in microscope_state["channels"].items()
    }
    sweep_times = {
        k: 2 * v["camera_exposure_time"] / 1000
        for k, v in microscope_state["channels"].items()
    }
    waveform_dict = daq.calculate_all_waveforms(
        microscope_name, exposure_times, sweep_times
    )

    for k, v in waveform_dict.items():
        channel = microscope_state["channels"][k]
        if not channel["is_selected"]:
            continue
        exposure_time = channel["camera_exposure_time"] / 1000
        print(k, channel["is_selected"], np.sum(v > 0), exposure_time)
        assert np.sum(v > 0) == daq.sample_rate * exposure_time
