# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Standard library imports

# Third-party imports
import numpy as np
import numpy.typing as npt

# Local application imports

# Mostly follows Lin R, Clowsley AH, Jayasinghe ID, Baddeley D, Soeller C.
# Algorithmic corrections for localization microscopy with sCMOS cameras -
# characterisation of a computationally efficient localization approach.
# Optics Express. 2017;25(10):11701–11701.


def compute_scmos_offset_and_variance_map(
    image: npt.ArrayLike,
) -> tuple[npt.ArrayLike, npt.ArrayLike]:
    """Compute the offset and variance map of an sCMOS camera.

    Parameters
    ----------
    image : npt.ArrayLike
        ZYX image of multiple dark camera frames, taken sequentially.

    Returns
    -------
    offset_map : npt.ArrayLike
        XY image of camera offset in the absence of signal.
    """
    offset_map = np.mean(image, axis=0).astype(image.dtype)
    variance_map = np.var(image, axis=0).astype(image.dtype)

    return offset_map, variance_map


def compute_flatfield_map(
    image: npt.ArrayLike, offset_map: npt.ArrayLike, local: bool = False
) -> npt.ArrayLike:
    """Compute the flatfield map for an evenly-illuminated set of frames from
    an sCMOS camera.

    Parameters
    ----------
    image : npt.ArrayLike
        ZYX image of multiple camera frames with defocused, even signal.
    offset_map : np.ArrayLike
        XY image of camera offset in the absence of signal.
    local : bool
        Compute the local flatfield map (as opposed to global).

    Returns
    -------
    flatfield_map : npt.ArrayLike
        XY image of flatfield map.
    """
    offset_image = np.mean(image, axis=0) - offset_map
    if local:
        from scipy.ndimage import gaussian_filter

        gaussian_image = gaussian_filter(offset_image, 9)
        return offset_image / (gaussian_image + 1)
    else:
        return offset_image / (np.max(np.abs(offset_image)) + 1)


def compute_noise_sigma(Fn=1.0, qe=0.82, S=0.0, Ib=0.0, Nr=1.4, M=1.0):
    """Compute the noise model for an sCMOS camera.

    Using https://www.hamamatsu.com/content/dam/hamamatsu-photonics/sites/documents/
    99_SALES_LIBRARY/sys/SCAS0134E_C13440-20CU_tec.pdf
    the sCMOS mean noise sigma is given by

    Parameters
    ----------
    Fn : float
        Excess noise factor (unitless)
    qe : float
        Quantum efficiency (unitless)
    S : float or np.array
        Signal (photons/pixel/frame)
    Ib : float or np.array
        Background (photons/pixel/frame)
    Nr : float
        Readout noise (e- rms)
    M : float
        EM gain

    Returns
    --------
    noise : float or np.array
        Estimated noise model (electrons)
    """
    noise = np.sqrt(Fn * Fn * qe * (S + Ib) + (Nr / M) ** 2)
    return noise


def compute_signal_to_noise(image, offset_map, variance_map):
    """Compute the signal-to-noise ratio of an image from offset and variance maps.

    Parameters
    ----------
    image : np.array
        ZYX image of camera frames.
    offset_map : np.array
        XY image of camera offset in the absence of signal.
    variance_map : np.array
        XY image of camera variance in the absence of signal.

    Returns
    -------
    snr : np.array
        XY image of signal-to-noise ratio.
    """
    S = image.astype(float) - offset_map.astype(float)
    S[S < 0] = 0  # clip
    N = np.sqrt(S + variance_map.astype(float) + 1.0)  # +1 to avoid div by zero error
    # print(f"Image min: {image.min()} offset_map min: {offset_map.min()}
    # S min: {S.min()} variance_map min: {variance_map.min()} N min: {N.min()}")

    return 1.0 * S / N
