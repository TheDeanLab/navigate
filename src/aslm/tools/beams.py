# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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

import numpy as np
import numpy.typing as npt


def gaussian_beam(
    r0: int,
    z0: int,
    rl: int,
    zl: int,
    w0: float,
    NA: float = 0.15,
    n: float = 1.33,
    wvl: float = 488.0,
    pixel_size: float = 1,
    I0: float = 1,
    bg: float = 0,
) -> npt.ArrayLike:
    """Generate a Gaussian beam

    Parameters
    ----------
    r0, z0 : int
        Offsets in pixels in radial and z direction of the beam.
    rl, zl : int
        Image size to generate
    w0 : float
        Beam waist width [nm]
    NA : float
        Numerical aperture of the optical system generating the Gaussian beam
    n : float
        Refractive index of the sample
    wvl : float
        Wavelength of the beam [nm]
    pixel_size : float
        Effective pixel size [nm]
    I0 : float
        Peak intensity of the beam
    bg : float
        Background intensity (what is "zero" in this image?)

    Returns
    -------
    np.ndarray
        2D array matching the size (rl, zl) of a Gaussian beam.
    """
    r = (np.arange(-rl // 2, rl // 2) - r0) * pixel_size * n / wvl
    z = (np.arange(-zl // 2, zl // 2) - z0) * pixel_size * n / wvl
    R, Z = np.meshgrid(r, z)
    z_r = n * w0 / NA
    w_z = w0 * np.sqrt(1 + (Z / z_r) ** 2)
    return I0 * (w0 / w_z) ** 2 * np.exp(-2 * R * R / (w_z * w_z)) + bg


######## Fitting functions #########
#
# E.g., for an image containing an isolated Gaussian beam...
#
# wvl = 488.0
# n = 1.56
# NA = 0.15
# pixel_size = 1044
# image = image0
# w0 = wvl
# rb, zb = image.shape[0]//2, image.shape[1]//2
#
# x0 = (np.argmax(np.max(image, axis=0))-1024, np.argmax(np.max(image, axis=1))-1024, w0, np.max(image), 100)
# # The bounds are optional
# res = least_squares(fit_gaussian_beam_error, x0, args=(image, NA, n, wvl, pixel_size),
#                     bounds=([-rb,-zb, 0, np.max(image)-100, 0], [rb, zb, 5*wvl, np.max(image), np.inf]))
# # res = minimize(fit_gaussian_beam_mse, x0, args=(image, NA, n, wvl, pixel_size))
#
# fig, axs = plt.subplots(1,2,figsize=(12,6))
# axs[0].imshow(image)
# axs[1].imshow(gaussian_beam(res.x[0], res.x[1], image.shape[0], image.shape[1], res.x[2],
#                             NA, n, wvl, pixel_size, res.x[3], res.x[4]))
#


def fit_gaussian_beam_error(x, image, NA, n, wvl, pixel_size, ravel=True):
    """x = (r0, z0, w0, I0, bg0)"""
    diff = (
        gaussian_beam(
            x[0],
            x[1],
            image.shape[0],
            image.shape[1],
            x[2],
            NA,
            n,
            wvl,
            pixel_size,
            x[3],
            x[4],
        )
        - image
    )
    # diff += x[2]  # regularize by beam waist size
    if ravel:
        return diff.ravel()
    else:
        return diff


def fit_gaussian_beam_mse(x, image, NA, n, wvl, pixel_size):
    return (
        fit_gaussian_beam_error(x, image, NA, n, wvl, pixel_size, ravel=False) ** 2
    ).mean()


######## End fitting functions #########
