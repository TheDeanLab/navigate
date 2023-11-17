# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

#  Standard Imports

# Third Party Imports
import numpy as np

# Local imports


def affine_rotation(x=0, y=0, z=0):
    """Calculate the general 3D affine transform for rotation.

    Returns a rotation matrix for a rotation about the x, y, and z axes.

    Rotation about x:
    [1, 0, 0, 0,
    0, cos(theta), -sin(theta), 0,
    0, sin(theta), cos(theta), 0,
    0, 0, 0, 1]

    Rotation about Y:
    [cos(theta), 0, sin(theta), 0,
    0, 1, 0, 0,
    -sin(theta), 0, cos(theta), 0,
    0, 0, 0, 1]

    Rotation about Z:
    [cos(theta), -sin(theta), 0, 0,
    sin(theta), cos(theta), 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1]


    Parameters
    ----------
    x : float
        Rotation about the x axis in degrees.
    y : float
        Rotation about the y axis in degrees.
    z : float
        Rotation about the z axis in degrees.

    Returns
    -------
    affine_transform : numpy.ndarray
        A 4x4 affine transformation matrix.
    """
    if x != 0:
        cosine_theta = np.cos(np.deg2rad(x))
        sin_theta = np.sin(np.deg2rad(x))
        x_transform = np.eye(4, 4)
        x_transform[1, 1] = cosine_theta
        x_transform[1, 2] = -sin_theta
        x_transform[2, 1] = sin_theta
        x_transform[2, 2] = cosine_theta
    else:
        x_transform = None

    if y != 0:
        cosine_theta = np.cos(np.deg2rad(y))
        sin_theta = np.sin(np.deg2rad(y))
        y_transform = np.eye(4, 4)
        y_transform[0, 0] = cosine_theta
        y_transform[0, 2] = sin_theta
        y_transform[2, 0] = -sin_theta
        y_transform[2, 2] = cosine_theta
    else:
        y_transform = None

    if z != 0:
        cosine_theta = np.cos(np.deg2rad(z))
        sin_theta = np.sin(np.deg2rad(z))
        z_transform = np.eye(4, 4)
        z_transform[0, 0] = cosine_theta
        z_transform[0, 1] = -sin_theta
        z_transform[1, 0] = sin_theta
        z_transform[1, 1] = cosine_theta
    else:
        z_transform = None

    matrices = [x_transform, y_transform, z_transform]
    matrices = [x for x in matrices if x is not None]

    if len(matrices) == 0:
        return np.eye(4, 4)
    if len(matrices) == 1:
        return matrices[0]
    elif len(matrices) == 2:
        return np.matmul(matrices[0].T, matrices[1])
    else:
        rotation_transform = np.matmul(matrices[0].T, matrices[1])
        return np.matmul(rotation_transform.T, matrices[2])


def affine_shear(dz, dy, dx, dimension="YZ", angle=0):
    """Calculate the general 3D affine transform for shear.

    Returns a shear matrix for a shear about the x, y, and z axes.

    Affine Transform for shear has the following form:

    [1 hxy hxz, 0,
    hyx 1 hyz, 0,
    hzx hzy 1, 0,
    0, 0, 0, 1]

    Parameters
    ----------
    dz : float
        Voxel size in Z.
    dy : float
        Voxel size in Y.
    dx : float
        Voxel size in X.
    dimension : str, optional
        The dimension to shear in. Options are "XY", "XZ", and "YZ".
    angle : float, optional
        The angle to shear in degrees.

    Returns
    -------
    shear_transform : numpy.ndarray
        A 4x4 affine transformation matrix.
    """
    shear_transform = np.eye(4, 4)
    if dz == 0 or dy == 0 or dx == 0 or angle == 0:
        return shear_transform

    scaled_angle = np.multiply(
        np.cos(np.deg2rad(angle)),
        [dy / dx, dz / dx, dz / dy],
    )

    if dimension.upper() == "XY" or dimension.upper() == "YX":
        shear_transform[0, 1] = scaled_angle[0]
    elif dimension.upper() == "XZ" or dimension.upper() == "ZX":
        shear_transform[0, 2] = scaled_angle[1]
    elif dimension.upper() == "YZ" or dimension.upper() == "ZY":
        shear_transform[1, 2] = scaled_angle[2]
    return shear_transform
