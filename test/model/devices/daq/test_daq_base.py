import numpy as np

from navigate.model.devices.daq.base import DAQBase


class _ConcreteDAQ(DAQBase):
    def stop_acquisition(self):
        return None

    def prepare_acquisition(self, channel_key):
        self.current_channel_key = channel_key

    def run_acquisition(self, wait_until_done=True):
        return wait_until_done

    def wait_acquisition_done(self):
        return None


def _build_configuration(camera_delay_ms=7):
    return {
        "waveform_constants": {"other_constants": {"camera_delay": camera_delay_ms}},
        "experiment": {
            "MicroscopeState": {
                "microscope_name": "ScopeA",
                "channels": {
                    "channel_1": {"is_selected": True},
                    "channel_2": {"is_selected": False},
                },
            }
        },
        "configuration": {
            "microscopes": {
                "ScopeA": {"daq": {"sample_rate": 1000}},
                "ScopeB": {"daq": {"sample_rate": 2000}},
            }
        },
    }


def test_initialize_daq_base():
    daq = _ConcreteDAQ(_build_configuration())

    assert str(daq) == "DAQBase"
    assert daq.sample_rate == 1000
    assert daq.camera_delay == 0.007
    assert daq.trigger_mode == "self-trigger"


def test_calculate_all_waveforms_only_selected_channels():
    daq = _ConcreteDAQ(_build_configuration())
    exposure_times = {"channel_1": 0.02, "channel_2": 0.03}
    sweep_times = {"channel_1": 0.05, "channel_2": 0.06}

    waveform_dict = daq.calculate_all_waveforms("ScopeA", exposure_times, sweep_times)

    assert "channel_1" in waveform_dict
    assert "channel_2" not in waveform_dict
    assert len(waveform_dict["channel_1"]) == int(daq.sample_rate * 0.05)
    assert np.sum(waveform_dict["channel_1"] > 0) == int(daq.sample_rate * 0.02)


def test_enable_microscope_updates_rate_and_delay():
    daq = _ConcreteDAQ(_build_configuration(camera_delay_ms=9))

    daq.enable_microscope("ScopeB")

    assert daq.microscope_name == "ScopeB"
    assert daq.sample_rate == 2000
    assert daq.camera_delay == 0.009


def test_set_external_trigger_updates_trigger_mode():
    daq = _ConcreteDAQ(_build_configuration())

    daq.set_external_trigger("Dev1/PFI0")
    assert daq.trigger_mode == "external-trigger"

    daq.set_external_trigger(None)
    assert daq.trigger_mode == "self-trigger"
