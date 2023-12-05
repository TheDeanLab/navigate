# Copyright (c) 2021-2023  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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

# https://iquilezles.org/articles/distfunctions/


def volume_from_sdf(sdf, N, pixel_size=1, subsample_z=1):
    """Generate an (N, N, N) image from sdf.

    Parameters
    ----------
    sdf : function
        A function that accepts (3, NxNxN) points as input and returns the Euclidean
        distance from each point to the object defined by the SDF.
    N : int
        Length of volume axis.
    pixel_size : float
        Rescale the image. Scaling must match object.
    subsample_z : int
        Return only the values every subsample slices.

    Returns
    -------
    npt.ArrayLike
        (N, N, N) image of SDF evaluated for each pixel.

    Examples
    --------
    >>> volume_from_sdf(lambda p: box(p, (15,15,30,)), 128)

    Generates a (128, 128, 128) image of a box sdf. The sdf is <= 0 within 128//2-30 to
    128//2+29 in z, 128//2-15 to 128//2+14 in x and y.
    """
    # Evaluate the SDF at the center of each pixel
    x = (np.arange(-N // 2, N // 2) + 0.5) * pixel_size
    z = (np.arange(-N // 2, N // 2, subsample_z) + 0.5) * pixel_size
    X, Y, Z = np.meshgrid(x, x, z)

    return sdf(np.vstack([X.ravel(), Y.ravel(), Z.ravel()])).reshape(N, N, -1).T


def sphere(p, R):
    """Signed distance function for a sphere.

    Parameters
    ----------
    p : npt.ArrayLike
        (3, N) array of points on which to evaluate the sdf.
    R : float
        Radius of the sphere.

    Returns
    -------
    npt.ArrayLike
        Signed distances from p to the sphere
    """
    return np.linalg.norm(p, axis=0) - R


def box(p, w):
    """Signed distance function for a box.

    Parameters
    ----------
    p : npt.ArrayLike
        (3, N) array of points on which to evaluate the sdf.
    w : tuple
        (3,) tuple of box half widths

    Returns
    -------
    npt.ArrayLike
        Signed distances from p to the box
    """
    w = np.array(w)  # Ensure w is an array

    q = np.abs(p) - w[:, None]
    return np.linalg.norm(np.maximum(q, 0.0), axis=0) + np.minimum(
        np.maximum(q[0, :], np.maximum(q[1, :], q[2, :])), 0.0
    )
