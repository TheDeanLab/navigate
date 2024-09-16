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
#

#  Standard Imports
import logging

# Third Party Imports
import numpy as np
from scipy.fftpack import dctn

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def fast_normalized_dct_shannon_entropy(input_array, psf_support_diameter_xy):
    """Calculates the entropy of an image.

    Parameters
    ----------
    input_array : np.ndarray
        2D or 3D image.  If 3D, will iterate through each 2D plane.
    psf_support_diameter_xy : float
        Support for the PSF in the x-dimension.

    Returns
    -------
    entropy : np.ndarray
        Entropy value.
    """

    dct_array = dctn(input_array, type=2)
    abs_array = np.abs(dct_array / np.linalg.norm(dct_array))
    yh = int(input_array.shape[1] // psf_support_diameter_xy)
    xh = int(input_array.shape[0] // psf_support_diameter_xy)
    entropy = (
        -2 * np.nansum(abs_array[:xh, :yh] * np.log2(abs_array[:xh, :yh])) / (yh * xh)
    )

    return np.atleast_1d(entropy)
