"""
ASLM Model Waveforms

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

from scipy import signal
import numpy as np
import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)


def single_pulse(sample_rate=100000,
                 sweep_time=0.4,
                 delay=10,
                 pulse_width=1,
                 amplitude=1,
                 offset=0):
    '''
    Returns a numpy array with a single pulse
    Used for creating TTL pulses out of analog outputs and laser intensity
    pulses.

    Units:
    sample_rate (samples/second): Integer
    sweep_time:  Seconds
    delay:      Percent
    pulse_width: Percent
    amplitude:  Volts
    offset:     Volts

    Examples:
    typical_TTL_pulse = single_pulse(sample_rate, sweep_time, 10, 1, 5, 0)
    typical_laser_pulse = single_pulse(sample_rate, sweep_time, 10, 80, 1.25, 0)
    '''
    # get an integer number of samples
    samples = int(np.floor(np.multiply(sample_rate, sweep_time)))

    # create an array just containing the offset voltage:
    array = np.zeros((samples)) + offset

    # convert pulse width and delay in % into number of samples
    pulsedelay_samples = int(samples * delay / 100)
    pulsesamples = int(samples * pulse_width / 100)

    # modify the array
    array[pulsedelay_samples:pulsesamples + pulsedelay_samples] = amplitude
    return np.array(array)


def tunable_lens_ramp(sample_rate=100000,
                      sweep_time=0.4,
                      delay=7.5,
                      rise=85,
                      fall=2.5,
                      amplitude=1,
                      offset=0):
    '''
    Returns a numpy array with a ETL ramp
    The waveform starts at offset and stays there for the delay period, then
    rises linearly to 2x amplitude (amplitude here refers to 1/2 peak-to-peak)
    and drops back down to the offset voltage during the fall period.

    Switching from a left to right ETL ramp is possible by exchanging the
    rise and fall periods.

    Units of parameters
    sample_rate: Integer
    sweep_time:  Seconds
    delay:      Percent
    rise:       Percent
    fall:       Percent
    amplitude:  Volts
    offset:     Volts
    '''

    # get an integer number of samples
    samples = int(np.floor(np.multiply(sample_rate, sweep_time)))

    # create an array just containing the negative amplitude voltage:
    array = np.zeros(samples) - amplitude + offset

    # convert rise, fall, and delay in % into number of samples
    delay_samples = int(samples * delay / 100)
    rise_samples = int(samples * rise / 100)
    fall_samples = int(samples * fall / 100)

    rise_array = np.arange(0, rise_samples)
    rise_array = amplitude * (2 * np.divide(rise_array, rise_samples) - 1) + offset

    fall_array = np.arange(0, fall_samples)
    fall_array = amplitude * (1 - 2 * np.divide(fall_array, fall_samples)) + offset

    # rise phase
    array[delay_samples:delay_samples + rise_samples] = rise_array

    # fall phase
    array[delay_samples + rise_samples:delay_samples + rise_samples + fall_samples] = fall_array

    return np.array(array)


def sawtooth(sample_rate=100000,
             sweep_time=0.4,
             frequency=10,
             amplitude=1,
             offset=0,
             duty_cycle=50,
             phase=np.pi / 2):
    '''
    Returns a numpy array with a sawtooth function.
    Used for creating the galvo signal.
    Example:  galvosignal =  sawtooth(100000, 0.4, 199, 3.67, 0, 50, np.pi)
    '''

    samples = np.multiply(float(sample_rate), sweep_time)
    duty_cycle = duty_cycle / 100
    t = np.linspace(0, sweep_time, int(samples))
    waveform = signal.sawtooth(2 * np.pi * frequency * t + phase, width=duty_cycle)
    waveform = amplitude * waveform + offset
    return waveform


def dc_value(sample_rate=100000,
             sweep_time=0.4,
             amplitude=1):
    '''
    Returns a numpy array with a DC value
    Used for creating the resonant galvo drive voltage.
    '''
    samples = np.multiply(float(sample_rate), sweep_time)
    waveform = np.zeros(int(samples))
    waveform[:] = amplitude
    return waveform

def square(sample_rate=100000,
           sweep_time=0.4,
           frequency=10,
           amplitude=1,
           offset=0,
           duty_cycle=50,
           phase=np.pi):
    '''
    Returns a numpy array with a square waveform
    Used for creating analog laser drive voltage.
    '''
    samples = int(sample_rate * sweep_time)
    duty_cycle = duty_cycle / 100
    t = np.linspace(0, sweep_time, samples)
    waveform = signal.square(2 * np.pi * frequency * t + phase, duty=duty_cycle)
    waveform = amplitude * waveform + offset
    return waveform

def sine_wave(sample_rate=100000,
              sweep_time=0.4,
              frequency=10,
              amplitude=1,
              offset=0,
              phase=0):
    """
    # Returns a numpy array with a sine waveform
    """
    samples = int(sample_rate * sweep_time)
    t = np.linspace(0, sweep_time, samples)
    waveform = amplitude * np.sin((2 * np.pi * frequency * t) - phase) + offset
    return waveform

def smooth_waveform(waveform,
                    percent_smoothing=10):
    """
    # Smooths a numpy array via convolution
    """
    waveform_length = np.size(waveform)
    window_len = int(np.floor(waveform_length * percent_smoothing / 100))
    smoothed_waveform = np.convolve(waveform, np.ones(window_len), 'valid') / window_len
    return smoothed_waveform

if (__name__ == "__main__"):
    import matplotlib.pyplot as plt
    sample_rate = 100000
    sweep_time = 0.4
    data = square(sample_rate=sample_rate, sweep_time=sweep_time, frequency=10, amplitude=5)
    plt.plot(data)
    plt.show()
