"""
Module for creating waveforms and analog output signals
Original Author: Fabian Voigt
Modified by Kevin Dean
"""

from scipy import signal
import numpy as np


def single_pulse(samplerate=100000, sweeptime=0.4, delay=10,
                 pulsewidth=1, amplitude=1, offset=0):
    '''
    Returns a numpy array with a single pulse
    Used for creating TTL pulses out of analog outputs and laser intensity
    pulses.

    Units:
    samplerate (samples/second): Integer
    sweeptime:  Seconds
    delay:      Percent
    pulsewidth: Percent
    amplitude:  Volts
    offset:     Volts

    Examples:
    typical_TTL_pulse = single_pulse(samplerate, sweeptime, 10, 1, 5, 0)
    typical_laser_pulse = single_pulse(samplerate, sweeptime, 10, 80, 1.25, 0)
    '''

    # get an integer number of samples
    samples = int(np.floor(np.multiply(samplerate, sweeptime)))

    # create an array just containing the offset voltage:
    array = np.zeros((samples)) + offset

    # convert pulsewidth and delay in % into number of samples
    pulsedelaysamples = int(samples * delay / 100)
    pulsesamples = int(samples * pulsewidth / 100)

    # modify the array
    array[pulsedelaysamples:pulsesamples + pulsedelaysamples] = amplitude
    return np.array(array)


def tunable_lens_ramp(samplerate=100000, sweeptime=0.4, delay=7.5,
                      rise=85, fall=2.5, amplitude=1, offset=0):
    '''
    Returns a numpy array with a ETL ramp
    The waveform starts at offset and stays there for the delay period, then
    rises linearly to 2x amplitude (amplitude here refers to 1/2 peak-to-peak)
    and drops back down to the offset voltage during the fall period.

    Switching from a left to right ETL ramp is possible by exchanging the
    rise and fall periods.

    Units of parameters
    samplerate: Integer
    sweeptime:  Seconds
    delay:      Percent
    rise:       Percent
    fall:       Percent
    amplitude:  Volts
    offset:     Volts
    '''
    # get an integer number of samples
    samples = int(np.floor(np.multiply(samplerate, sweeptime)))

    # create an array just containing the negative amplitude voltage:
    array = np.zeros((samples)) - amplitude + offset

    # convert rise, fall, and delay in % into number of samples
    delaysamples = int(samples * delay / 100)
    risesamples = int(samples * rise / 100)
    fallsamples = int(samples * fall / 100)

    risearray = np.arange(0, risesamples)
    risearray = amplitude * \
        (2 * np.divide(risearray, risesamples) - 1) + offset

    fallarray = np.arange(0, fallsamples)
    fallarray = amplitude * \
        (1 - 2 * np.divide(fallarray, fallsamples)) + offset

    # rise phase
    array[delaysamples:delaysamples + risesamples] = risearray

    # fall phase
    array[delaysamples + risesamples:delaysamples +
          risesamples + fallsamples] = fallarray

    return np.array(array)


def sawtooth(samplerate=100000, sweeptime=0.4, frequency=10, amplitude=1,
             offset=0, duty_cycle=50, phase=np.pi / 2):
    '''
    Returns a numpy array with a sawtooth function. Used for creating the galvo signal. Example:
    galvosignal =  sawtooth(100000, 0.4, 199, 3.67, 0, 50, np.pi)
    '''

    samples = samplerate * sweeptime
    # the signal.sawtooth width parameter has to be between 0 and 1
    duty_cycle = duty_cycle / 100
    t = np.linspace(0, int(sweeptime), int(samples))

    # Using the signal toolbox from scipy for the sawtooth:
    waveform = signal.sawtooth(
        2 * np.pi * frequency * t + phase,
        width=duty_cycle)

    # Scale the waveform to a certain amplitude and apply an offset:
    waveform = amplitude * waveform + offset

    return waveform


def dc_value(samplerate=100000, sweeptime=0.4, amplitude=1, offset=0):
    '''
    Returns a numpy array with a DC value
    Used for creating the resonant galvo drive voltage.
    '''

    samples = int(samplerate * sweeptime)
    t = np.linspace(0, sweeptime, samples)
    waveform = np.ones(np.shape(t)) * amplitude + offset
    return waveform


def square(samplerate=100000, sweeptime=0.4, frequency=10,
           amplitude=1, offset=0, duty_cycle=50, phase=np.pi):
    # Returns a numpy array with a rectangular waveform
    samples = int(samplerate * sweeptime)
    # the signal.square duty parameter has to be between 0 and 1
    duty_cycle = duty_cycle / 100
    t = np.linspace(0, sweeptime, samples)

    # Using the signal toolbox from scipy for the sawtooth:
    waveform = signal.square(
        2 * np.pi * frequency * t + phase,
        duty=duty_cycle)

    # Scale the waveform to a certain amplitude and apply an offset:
    waveform = amplitude * waveform + offset
    return waveform


def sine_wave(samplerate=100000, sweeptime=0.4, frequency=10,
              amplitude=1, offset=0, phase=0):         # in rad, np.pi/2 is 90 degrees

    # Returns a numpy array with a sine waveform
    samples = int(samplerate * sweeptime)
    t = np.linspace(0, sweeptime, samples)

    # Using the signal toolbox from scipy for the sawtooth:
    waveform = amplitude * np.sin((2 * np.pi * frequency * t) - phase) + offset
    return waveform


def smooth_waveform(waveform, percent_smoothing=10):
    waveform_length = np.size(waveform)
    window_len = int(np.floor(waveform_length * percent_smoothing / 100))
    smoothed_waveform = np.convolve(
        waveform,
        np.ones(window_len),
        'valid') / window_len
    return smoothed_waveform


if (__name__ == "__main__"):
    # Test the waveform functions:
    import matplotlib.pyplot as plt
    plt.plot(smooth_waveform(tunable_lens_ramp(), 10))
    plt.show()
