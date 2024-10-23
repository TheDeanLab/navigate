# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Standard Library Imports
import logging

# Third Party Imports
import numpy as np
from scipy import signal

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def camera_exposure(
    sample_rate=100000, sweep_time=0.4, exposure=0.4, camera_delay=0.001
):
    """Calculates timing and duration of camera exposure.
    Not actually used to trigger the camera.  Only meant for visualization.

    Parameters
    ----------
    sample_rate : Integer
        Unit - Hz
    sweep_time : Float
        Unit - Seconds
    exposure : Float
        Unit - Seconds
    camera_delay : Float
        Unit - Seconds

    Returns
    -------
    exposure_start : Float
        Unit - Seconds
    exposure_end : Float
        Unit - Seconds

    Examples
    --------
        >>> exposure_start, exposure_end = camera_exposure(sample_rate, sweep_time,
        exposure, camera_delay)

    """
    amplitude = 5

    # get an integer number of samples
    samples = int(np.multiply(sample_rate, sweep_time))

    # create an array just containing the offset voltage:
    array = np.zeros(samples)

    # convert pulse width and delay in % into number of samples
    pulse_delay_samples = int(camera_delay * sample_rate)
    pulse_samples = int(exposure * sample_rate)

    # modify the array
    array[pulse_delay_samples : (pulse_samples + pulse_delay_samples)] = amplitude
    return np.array(array)


def single_pulse(
    sample_rate=100000, sweep_time=0.4, delay=10, pulse_width=1, amplitude=1, offset=0
):
    """
    Returns a numpy array with a single pulse
    Used for creating TTL pulses out of analog outputs and laser intensity
    pulses.

    Parameters
    ----------
    sample_rate : Integer
        Unit - Hz
    sweep_time : Float
        Unit - Seconds
    delay : Float
        Unit - Percent
    pulse_width : Float
        Unit - Percent
    amplitude : Float
        Unit - Volts
    offset : Float
        Unit - Volts

    Returns
    -------
    waveform : np.array

    Examples
    --------
    >>> typical_TTL_pulse = single_pulse(sample_rate, sweep_time, 10, 1, 1, 0)
    """
    # get an integer number of samples
    samples = int(np.floor(np.multiply(sample_rate, sweep_time)))

    # create an array just containing the offset voltage:
    array = np.zeros(samples) + offset

    # convert pulse width and delay in % into number of samples
    pulsedelay_samples = int(samples * delay / 100)
    pulsesamples = int(samples * pulse_width / 100)

    # modify the array
    array[pulsedelay_samples : pulsesamples + pulsedelay_samples] = amplitude
    return np.array(array)


def remote_focus_ramp(
    sample_rate=100000,
    exposure_time=0.2,
    sweep_time=0.24,
    remote_focus_delay=0.005,
    camera_delay=0.001,
    fall=0.05,
    amplitude=1,
    offset=0,
):
    """Returns a numpy array with a sawtooth ramp - typically used for remote focusing.

    The waveform starts at offset and stays there for the delay period, then
    rises linearly to 2x amplitude (amplitude here refers to 1/2 peak-to-peak)
    and drops back down to the offset voltage during the fall period.

    Switching from a left to right remote focus ramp is possible by exchanging the
    rise and fall periods.

    Parameters
    ----------
    sample_rate : Integer
        Unit - Hz
    exposure_time : Float
        Unit - Seconds
    sweep_time : Float
        Unit - Seconds
    remote_focus_delay : Float
        Unit - seconds
    camera_delay : Float
        Unit - seconds
    fall : Float
        Unit - seconds
    amplitude : Float
        Unit - Volts
    offset : Float
        Unit - Volts

    Returns
    -------
    waveform : np.array

    Examples
    --------
    >>> etl_ramp = tunable_lens_ramp(sample_rate, exposure_time, sweep_time, etl_delay,
        camera_delay, fall, amplitude, offset)

    """
    # create an array just containing the negative amplitude voltage:
    delay_samples = int(remote_focus_delay * sample_rate)
    delay_array = np.zeros(delay_samples) + offset - amplitude

    # 10-7.5 -> 1.025 * .2
    #
    ramp_samples = int(
        (exposure_time + camera_delay - remote_focus_delay) * sample_rate
    )
    ramp_array = np.linspace(offset - amplitude, offset + amplitude, ramp_samples)

    # fall_samples = .025 * .2 * 100000 = 500
    fall_samples = int(fall * sample_rate)
    fall_array = np.linspace(offset + amplitude, offset - amplitude, fall_samples)

    extra_samples = int(
        int(np.multiply(sample_rate, sweep_time))
        - (delay_samples + ramp_samples + fall_samples)
    )
    if extra_samples > 0:
        extra_array = np.zeros(extra_samples) + offset - amplitude
        waveform = np.hstack([delay_array, ramp_array, fall_array, extra_array])
    else:
        waveform = np.hstack([delay_array, ramp_array, fall_array])

    return waveform


def remote_focus_ramp_triangular(
    sample_rate=100000,
    exposure_time=0.2,
    sweep_time=0.24,
    remote_focus_delay=0.005,
    camera_delay=0.001,
    amplitude=1,
    offset=0,
    ramp_type="Rising",
):
    """Returns a numpy array with a triangular ramp typically used for remote focusing

    The waveform starts at offset and stays there for the delay period, then
    rises linearly to 2x amplitude (amplitude here refers to 1/2 peak-to-peak).

    Switching from a left to right remote focus ramp is possible by exchanging the
    rise and fall periods.

    Parameters
    ----------
    sample_rate : Integer
        Unit - Hz
    exposure_time : Float
        Unit - Seconds
    sweep_time : Float
        Unit - Seconds
    remote_focus_delay : Float
        Unit - Seconds
    camera_delay : Float
        Unit - Seconds
    amplitude : Float
        Unit - Volts
    offset : Float
        Unit - Volts
    ramp_type : String


    Returns
    -------
    waveform : np.array

    Examples
    --------
    >>> etl_ramp = tunable_lens_ramp(sample_rate, exposure_time, sweep_time, etl_delay,
        camera_delay, fall, amplitude, offset)

    """
    # create an array just containing the negative amplitude voltage:
    # In theory, delay here should be 4H.
    delay_samples = int(remote_focus_delay * sample_rate)
    delay_array = np.zeros(delay_samples) + offset

    # ramp samples
    ramp_samples = int(
        (exposure_time + camera_delay - remote_focus_delay) * sample_rate
    )
    rise_ramp_array = np.linspace(offset - amplitude, offset + amplitude, ramp_samples)
    fall_ramp_array = np.linspace(offset + amplitude, offset - amplitude, ramp_samples)

    settle_samples = int(
        int(np.multiply(sample_rate, sweep_time)) - (delay_samples + ramp_samples)
    )
    settle_array = np.zeros(settle_samples) + offset

    if ramp_type == "Rising":
        waveform = np.hstack(
            [
                delay_array - amplitude,
                rise_ramp_array,
                settle_array + amplitude,
                delay_array + amplitude,
                fall_ramp_array,
                settle_array - amplitude,
            ]
        )
    elif ramp_type == "Falling":
        waveform = np.hstack(
            [
                delay_array + amplitude,
                fall_ramp_array,
                settle_array - amplitude,
                delay_array - amplitude,
                rise_ramp_array,
                settle_array + amplitude,
            ]
        )

    return waveform


def sawtooth(
    sample_rate=100000,
    sweep_time=0.4,
    frequency=10,
    amplitude=1,
    offset=0,
    duty_cycle=50,
    phase=np.pi / 2,
):
    """
    Returns a numpy array with a sawtooth function.
    Used for creating the galvo signal.

    Parameters
    ----------
    sample_rate : Integer
        Unit - Hz
    sweep_time : Float
        Unit - Seconds
    frequency : Float
        Unit - Hz
    amplitude : Float
        Unit - Volts
    offset : Float
        Unit - Volts
    duty_cycle : Float
        Unit - Percent
    phase : Float
        Unit - Radians

    Returns
    -------
    waveform : np.array

    Examples
    --------
    >>> typical_galvo = sawtooth(sample_rate, sweep_time, 10, 1, 0, 50, np.pi/2)
    """

    samples = int(np.multiply(sample_rate, sweep_time))
    duty_cycle = duty_cycle / 100
    t = np.linspace(0, sweep_time, samples)
    waveform = signal.sawtooth(2 * np.pi * frequency * (t - phase), width=duty_cycle)
    waveform = amplitude * waveform + offset

    return waveform


def dc_value(sample_rate=100000, sweep_time=0.4, amplitude=1):
    """
    Returns a numpy array with a DC value
    Used for creating the resonant galvo drive voltage.

    Parameters
    ----------
    sample_rate : Integer
        Unit - Hz
    sweep_time : Float
        Unit - Seconds
    amplitude : Float
        Unit - Volts

    Returns
    -------
    waveform : np.array

    Examples
    --------
    >>> typical_galvo = dc_value(sample_rate, sweep_time, 1)

    """
    samples = np.multiply(float(sample_rate), sweep_time)
    waveform = np.zeros(int(samples))
    waveform[:] = amplitude
    return waveform


def square(
    sample_rate=100000,
    sweep_time=0.4,
    frequency=10,
    amplitude=1,
    offset=0,
    duty_cycle=50,
    phase=np.pi,
):
    """Returns a numpy array with a square function.
    Used for creating analog laser drive voltage.

    Parameters
    ----------
    sample_rate : Integer
        Unit - Hz
    sweep_time : Float
        Unit - Seconds
    frequency : Float
        Unit - Hz
    amplitude : Float
        Unit - Volts
    offset : Float
        Unit - Volts
    duty_cycle : Float
        Unit - Percent
    phase : Float
        Unit - Radians

    Returns
    -------
    waveform : np.array

    Examples
    --------
    >>> typical_laser = square(sample_rate, sweep_time, 10, 1, 0, 50, np.pi)
    """
    samples = int(sample_rate * sweep_time)
    duty_cycle = duty_cycle / 100
    t = np.linspace(0, sweep_time, samples)
    waveform = signal.square(2 * np.pi * frequency * t + phase, duty=duty_cycle)
    waveform = amplitude * waveform + offset
    return waveform


def sine_wave(
    sample_rate=100000, sweep_time=0.4, frequency=10, amplitude=1, offset=0, phase=0
):
    """Returns a numpy array with a sine waveform

    Used for creating analog laser drive voltage.

    Parameters
    ----------
    sample_rate : int, optional
        Unit - Hz, by default 100000
    sweep_time : float, optional
        Unit - Seconds, by default 0.4
    frequency : int, optional
        Unit - Hz, by default 10
    amplitude : float, optional
        Unit - Volts, by default 1
    offset : float, optional
        Unit - Volts, by default 0
    phase : float, optional
        Unit - Radians, by default 0

    Returns
    -------
    waveform : np.array

    Examples
    --------
    >>> typical_laser = sine_wave(sample_rate, sweep_time, 10, 1, 0, 0)

    """
    samples = int(sample_rate * sweep_time)
    t = np.linspace(0, sweep_time, samples)
    waveform = amplitude * np.sin((2 * np.pi * frequency * t) - phase) + offset
    return waveform


def smooth_waveform(waveform, percent_smoothing=10):
    """Smooths a numpy array via convolution

    Parameters
    ----------
    waveform : np.array
        The waveform to be smoothed
    percent_smoothing : float
        The percentage of the waveform to be smoothed

    Returns
    -------
    smoothed_waveform : np.array
        The smoothed waveform
    """
    waveform_length = np.size(waveform)
    window_length = int(np.ceil(waveform_length * percent_smoothing / 100))
    if window_length == 0:
        # cannot smooth
        return waveform
    waveform_padded = np.pad(waveform, window_length, mode="edge")
    smoothed_waveform = (
        np.convolve(waveform_padded, np.ones(window_length), "valid") / window_length
    )

    return smoothed_waveform
