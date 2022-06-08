# Standard Library Imports
import unittest
import sys

# Third Party Imports
import numpy as np

# Local Imports
sys.path.append('../../')
import src.model.aslm_model_waveforms as aslm_model_waveforms

class TestWaveforms(unittest.TestCase):
    """
    Unit Tests for the ASLM Model Waveforms
    """
    def test_single_pulse_max_default_amplitude(self):
        sample_rate = 100000
        sweep_time = 0.4
        data = aslm_model_waveforms.single_pulse(sample_rate=sample_rate,
                                                 sweep_time=sweep_time)
        self.assertEqual(np.max(data), 1)

    def test_single_pulse_max_specified_amplitude(self):
        sample_rate = 100000
        sweep_time = 0.4
        amplitude = 2
        data = aslm_model_waveforms.single_pulse(sample_rate=sample_rate,
                                                 sweep_time=sweep_time,
                                                 amplitude=amplitude)
        self.assertEqual(np.max(data), amplitude)

    def test_single_pulse_min_default_amplitude(self):
        sample_rate = 100000
        sweep_time = 0.4
        data = aslm_model_waveforms.single_pulse(sample_rate=sample_rate,
                                                 sweep_time=sweep_time)
        self.assertEqual(np.min(data), 0)

    def test_single_pulse_onset_default_delay(self):
        sample_rate = 100000
        sweep_time = 0.4
        default_delay = 10
        data = aslm_model_waveforms.single_pulse(sample_rate=sample_rate,
                                                 sweep_time=sweep_time)
        first_index = next(x for x, val in enumerate(data)
                           if val > 0.5)
        self.assertEqual(int(sample_rate * sweep_time * default_delay / 100), first_index)

    def test_single_pulse_onset_specified_delay(self):
        sample_rate = 100000
        sweep_time = 0.4
        delay = 20
        data = aslm_model_waveforms.single_pulse(sample_rate=sample_rate,
                                                 sweep_time=sweep_time,
                                                 delay=delay)
        first_index = next(x for x, val in enumerate(data)
                           if val > 0.5)
        self.assertEqual(int(sample_rate * sweep_time * delay / 100), first_index)

    def test_single_pulse_default_offset(self):
        sample_rate = 100000
        sweep_time = 0.4
        default_offset = 0
        data = aslm_model_waveforms.single_pulse(sample_rate=sample_rate,
                                                 sweep_time=sweep_time)
        self.assertEqual(np.min(data), default_offset)

    def test_single_pulse_specified_offset(self):
        sample_rate = 100000
        sweep_time = 0.4
        offset = 0.2
        data = aslm_model_waveforms.single_pulse(sample_rate=sample_rate,
                                                 sweep_time=sweep_time,
                                                 offset=offset)
        self.assertEqual(np.min(data), offset)

    # def test_tunable_lens_ramp_default_delay(self):
    #     sample_rate = 100000
    #     sweep_time = 0.4
    #     default_delay = 7.5
    #     data = aslm_model_waveforms.tunable_lens_ramp(sample_rate=sample_rate,
    #                                                   sweep_time=sweep_time)



if (__name__ == "__main__"):
    unittest.main()
