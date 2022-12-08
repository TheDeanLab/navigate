# Third Party Imports
import nidaqmx
from nidaqmx.constants import AcquisitionType, TerminalConfiguration, AccelUnits, AccelSensitivityUnits, ExcitationSource
import numpy as np
import matplotlib.pyplot as plt


def make_measurement(analog_input_line='cDAQ1Mod1/ai0', sampling_frequency=1 * 10 ** 3, experiment_duration=1, sensitivity=1000, current_excit_val=0.004):
    """
    Measure samples from a NIDAQ accelerometer.

    Parameters
    ----------
    analog_input_line : str
        Location of analog input(s) to record from.
    sampling_frequency : float
        Rate for acquiring samples (Hz)
    experiment_duration : float
        Duration of acquisition (seconds)
    sensitivity : float
        Sensitivity of the sensor in mV/G
    current_excit_val : float
        Milliamps of excitation for sensor

    Returns
    -------
    data : list
        List (yes, a list! not an array) of samples
    """
    # samps_per_chan and number_of_samples_per_channel must be an integer
    total_samples = int(round(experiment_duration * sampling_frequency))
    timeout_duration = float(experiment_duration + 5)

    # Construct analog input task
    analog_input = nidaqmx.Task()
    analog_input.ai_channels.add_ai_accel_chan(analog_input_line,
                                               terminal_config=TerminalConfiguration.PSEUDODIFFERENTIAL,
                                               min_val=-5,
                                               max_val=5,
                                               units=AccelUnits.G,
                                               sensitivity=sensitivity,
                                               sensitivity_units=AccelSensitivityUnits.M_VOLTS_PER_G,
                                               current_excit_source=ExcitationSource.INTERNAL,
                                               current_excit_val=current_excit_val)
    analog_input.timing.cfg_samp_clk_timing(rate=float(sampling_frequency),
                                            samps_per_chan=total_samples,
                                            sample_mode=AcquisitionType.FINITE)
    # Read the samples
    data = analog_input.read(number_of_samples_per_channel=total_samples,
                             timeout=timeout_duration)
    analog_input.close()

    return data


def calculate_single_sided_spectrum(data, sampling_frequency):
    """
    Convert a set of samples into a single-sided frequency power spectrum.

    TODO: Support when data is list of lists.

    Parameters
    ----------
    data : list
        List of sample values.
    sampling_frequency : float
        Rate at which samples were collected in data (seconds)

    Returns
    -------
    frequency_axis : np.array
        Frequency bins for single_sided_spectrum
    single_sided_spectrum : np.array
        Single-sided frequency power spectrum of samples in data
    """
    n_samples = len(data)
    frequency_domain_data = np.fft.fft(data)
    two_sided_spectrum = np.abs(frequency_domain_data) / n_samples  # convert to power spectrum
    single_sided_spectrum = two_sided_spectrum[0:int(n_samples / 2)]  # cut
    single_sided_spectrum[1:] = 2 * single_sided_spectrum[1:]  # reflect power (except on DC term)
    frequency_axis = (sampling_frequency / n_samples) * np.arange(0, int(n_samples / 2))

    return frequency_axis, single_sided_spectrum


def fast_moving_average(data, n=3):
    ret = np.cumsum(data)  # cumulative sum
    ret[n:] = ret[n:] - ret[:-n]  # sum of n previous points
    return ret[(n - 1):] / n  # averaged


def moving_average(data, n=3):
    return np.convolve(data, np.ones(n), 'valid') / n


def plot_frequency_response(frequency_axis, single_sided_spectrum, ax=None, title=None):
    """
    Display a frequency response plot.
    """
    if ax is None:
        fig, ax = plt.subplots()
    ax.plot(frequency_axis, single_sided_spectrum)
    # ax.set_yscale("log")
    ax.set_ylabel('Amplitude')
    ax.set_xlabel('Frequency (Hz)')
    if title is not None:
        ax.set_title(title)


if __name__ == '__main__':
    sampling_frequency = 1 * 10 ** 4  # Hz
    experiment_duration = 10          # seconds
    w = 10                            # size of power spectrum smoothing window (average over w frequencies)

    # Multiscale, camera off...
    ms_cam_off_data = make_measurement(sampling_frequency=sampling_frequency, experiment_duration=experiment_duration)
    ms_cam_off_freq_ax, ms_cam_off_sssp = calculate_single_sided_spectrum(ms_cam_off_data, sampling_frequency)

    fig, axs = plt.subplots(1, 2, figsize=(12, 6))
    plot_frequency_response(ms_cam_off_freq_ax, ms_cam_off_sssp, axs[0], "Raw power spectrum")
    plot_frequency_response(ms_cam_off_freq_ax[(w - 1):], fast_moving_average(ms_cam_off_sssp, w), axs[1],
                            f"Moving average (w={w}) power spectrum")
    fig.tight_layout()
