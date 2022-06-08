"""
Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

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
