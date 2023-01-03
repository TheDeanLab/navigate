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

"""
Python and cupy implementation of BaSiC flat-field correction (doi: 10.1038/ncomms14836)
Adapted by Doug Shepherd: https://github.com/QI2lab/OPM/blob/master/flat_field.py
Original code found at: https://github.com/peng-lab/PyBasicCellprofilerPlugin

TO DO: Tons of optimization opportunities with cupy, numba, and cucim.
Maybe need to write our own DCT operator for use on GPU?Last updated: Shepherd 06/21
"""

import numpy as np
from skimage.transform import resize as skresize

# from scipy.fftpack import dct, idct
import cupy as cp
import logging
from pathlib import Path

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

RESIZE_ORDER = 1
RESIZE_MODE = "symmetric"
PRESERVE_RANGE = True
OUTPUT_IMAGE = "OutputImage"
FIRST_CYCLE = "First Cycle"
LAST_CYCLE = "Last Cycle"


def calculate_flat_field(
    images,
    if_dark_field=True,
    lambda_flat_field=0,
    lambda_dark_field=0,
    max_iterations=100,
    optimization_tolerance=1.0e-6,
    max_reweight_iterations=10,
    epsilon=0.1,
    varying_coeff=True,
    reweight_tolerance=1.0e-3,
):
    """
    Function to calculate dark_field and brightfield correction from an image stack

    :param images: ndarray
    :param if_dark_field: boolean
    :param lambda_flat_field: float
    :param lambda_dark_field: float
    :param max_iterations: int
    :param optimization_tolerance: float
    :param max_reweight_iterations: int
    :param epsilon: float
    :param varying_coeff: boolean
    :param reweight_tolerance: float

    :return dark_field: ndarray
    :return flat_field: ndarray
    """

    _saved_size = images[0].shape
    number_of_rows = _saved_size[0] // 16
    number_of_columns = _saved_size[1] // 16

    D = np.zeros((images.shape[0], number_of_rows, number_of_columns), dtype=np.uint16)

    for i in range(images.shape[0]):
        D[i, :, :] = _resize_image(
            image=images[i, :],
            y_side_size=number_of_columns,
            x_side_size=number_of_rows,
        )

    meanD = np.mean(D, axis=2)
    meanD = meanD / np.mean(meanD)
    W_meanD = _dct2d(meanD.T)

    # setting lambda_flat_field and lambda_dark_field if they are not set by
    # the user
    if lambda_flat_field <= 0:
        lambda_flat_field = np.sum(np.abs(W_meanD)) / 400 * 0.5
    if lambda_dark_field <= 0:
        lambda_dark_field = lambda_flat_field * 0.2

    D = np.sort(D, axis=2)

    XAoffset = np.zeros((number_of_rows, number_of_columns))
    weight = np.ones(D.shape)

    reweighting_iter = 0
    flag_reweighting = True
    flat_field_last = np.ones((number_of_rows, number_of_columns))
    dark_field_last = np.random.randn(number_of_rows, number_of_columns)

    while flag_reweighting:
        reweighting_iter += 1

        initial_flat_field = False
        if initial_flat_field:
            raise IOError("Initial flat_field option not implemented yet!")
        else:
            X_k_A, X_k_E, X_k_Aoffset = _inexact_alm_rspca_l1(
                images=D,
                lambda_flat_field=lambda_flat_field,
                if_dark_field=if_dark_field,
                lambda_dark_field=lambda_dark_field,
                optimization_tolerance=optimization_tolerance,
                max_iterations=max_iterations,
                weight=weight,
            )

        XA = np.reshape(X_k_A, [number_of_rows, number_of_columns, -1], order="F")
        XE = np.reshape(X_k_E, [number_of_rows, number_of_columns, -1], order="F")
        XAoffset = np.reshape(
            X_k_Aoffset, [number_of_rows, number_of_columns], order="F"
        )
        XE_norm = XE / np.mean(XA, axis=(0, 1))

        weight = np.ones_like(XE_norm) / (np.abs(XE_norm) + epsilon)

        weight = weight * weight.size / np.sum(weight)

        temp = np.mean(XA, axis=2) - XAoffset
        flat_field_current = temp / np.mean(temp)
        dark_field_current = XAoffset
        mad_flat_field = np.sum(np.abs(flat_field_current - flat_field_last)) / np.sum(
            np.abs(flat_field_last)
        )
        temp_diff = np.sum(np.abs(dark_field_current - dark_field_last))
        if temp_diff < 1e-7:
            mad_dark_field = 0
        else:
            mad_dark_field = temp_diff / np.maximum(
                np.sum(np.abs(dark_field_last)), 1e-6
            )
        flat_field_last = flat_field_current
        dark_field_last = dark_field_current
        if (
            np.maximum(mad_flat_field, mad_dark_field) <= reweight_tolerance
            or reweighting_iter >= max_reweight_iterations
        ):
            flag_reweighting = False

    shading = np.mean(XA, 2) - XAoffset
    flat_field = _resize_image(
        image=shading, x_side_size=_saved_size[0], y_side_size=_saved_size[1]
    )
    flat_field = flat_field / np.mean(flat_field)

    if if_dark_field:
        dark_field = _resize_image(
            image=XAoffset, x_side_size=_saved_size[0], y_side_size=_saved_size[1]
        )
    else:
        dark_field = np.zeros_like(flat_field)

    return flat_field.astype(np.float32), dark_field.astype(np.float32)


def baseline_drift(
    images_list,
    working_size=128,
    flat_field: np.ndarray = None,
    dark_field: np.ndarray = None,
):
    # TODO: Rename s.t. fluorescence is included? E.g. background_fluorescence?
    """
    Estimation of background fluorescence signal for time-lapse movie.
    Used in conjunction with BaSiC.
    """
    number_of_rows = number_of_columns = working_size

    # Preparing input images
    resized_images = np.stack(
        _resize_images_list(images_list=images_list, side_size=working_size)
    )
    resized_images = resized_images.reshape(
        [-1, number_of_rows * number_of_rows], order="F"
    )

    # Resizing flat- and dark-field
    resized_flat_field = _resize_image(image=flat_field, side_size=working_size)
    resized_dark_field = _resize_image(image=dark_field, side_size=working_size)

    # reweighting
    _weights = np.ones(resized_images.shape)
    epsilon = 0.1
    tol = 1e-6
    for reweighting_iter in range(1, 6):
        W_idct_hat = np.reshape(resized_flat_field, (1, -1), order="F")
        A_offset = np.reshape(resized_dark_field, (1, -1), order="F")
        A1_coeff = np.mean(resized_images, 1).reshape([-1, 1])

        # main iteration loop starts:
        # The first element of the second array of np.linalg.svd
        _temp = np.linalg.svd(resized_images, full_matrices=False)[1]
        norm_two = _temp[0]

        mu = 12.5 / norm_two  # this one can be tuned
        mu_bar = mu * 1e7
        rho = 1.5  # this one can be tuned
        d_norm = np.linalg.norm(resized_images, ord="fro")
        ent1 = 1
        _iter = 0
        total_svd = 0
        converged = False
        a1_hat = np.zeros(resized_images.shape)
        e1_hat = np.zeros(resized_images.shape)
        Y1 = 0

        while not converged:
            _iter = _iter + 1
            a1_hat = W_idct_hat * A1_coeff + A_offset

            # update E1 using l0 norm
            e1_hat = e1_hat + np.divide(
                (resized_images - a1_hat - e1_hat + (1 / mu) * Y1), ent1
            )
            e1_hat = np.maximum(e1_hat - _weights / (ent1 * mu), 0) + np.minimum(
                e1_hat + _weights / (ent1 * mu), 0
            )
            # update A1_coeff, A2_coeff and A_offset
            # if coeff_flag

            R1 = resized_images - e1_hat
            A1_coeff = np.mean(R1, 1).reshape(-1, 1) - np.mean(A_offset, 1)

            A1_coeff[A1_coeff < 0] = 0

            Z1 = resized_images - a1_hat - e1_hat

            Y1 = Y1 + mu * Z1

            mu = min(mu * rho, mu_bar)

            # stop Criterion
            stopCriterion = np.linalg.norm(Z1, ord="fro") / d_norm
            if stopCriterion < tol:
                converged = True

        # updating weight
        # XE_norm = e1_hat / np.mean(a1_hat)
        XE_norm = e1_hat
        mean_vec = np.mean(a1_hat, axis=1)
        XE_norm = np.transpose(np.tile(mean_vec, (16384, 1))) / XE_norm
        _weights = 1.0 / (abs(XE_norm) + epsilon)

        _weights = np.divide(
            np.multiply(_weights, _weights.shape[0] * _weights.shape[1]),
            np.sum(_weights),
        )

    return A1_coeff


def _inexact_alm_rspca_l1(
    images,
    lambda_flat_field,
    if_dark_field,
    lambda_dark_field,
    optimization_tolerance,
    max_iterations,
    weight=None,
):

    if weight is not None and weight.size != images.size:
        raise IOError("weight matrix has different size than input sequence")

    # if
    # Initialization and given default variables
    p = images.shape[2]
    q = images.shape[1]
    m = p * q
    n = images.shape[0]
    images = np.reshape(images, (m, n), order="F")

    if weight is not None:
        weight = np.reshape(weight, (m, n), order="F")
    else:
        weight = np.ones_like(images)
    # _, svd, _ = np.linalg.svd(images, full_matrices=False) #TODO: Is there a
    # more efficient implementation of SVD?
    c_images = cp.asarray(images)
    _, c_svd, _ = cp.linalg.svd(c_images, full_matrices=False)
    svd = cp.asnumpy(c_svd)
    norm_two = svd[0]
    Y1 = 0
    # Y2 = 0
    ent1 = 1
    ent2 = 10

    a1_hat = np.zeros_like(images)
    A1_coeff = np.ones((1, images.shape[1]))

    e1_hat = np.zeros_like(images)
    W_hat = _dct2d(np.zeros((p, q)).T)
    mu = 12.5 / norm_two
    mu_bar = mu * 1e7
    rho = 1.5
    d_norm = np.linalg.norm(images, ord="fro")

    A_offset = np.zeros((m, 1))
    B1_uplimit = np.min(images)
    B1_offset = 0
    # A_uplimit = np.expand_dims(np.min(images, axis=1), 1)
    A_inmask = np.zeros((p, q))
    A_inmask[
        int(np.round(p / 6) - 1) : int(np.round(p * 5 / 6)),
        int(np.round(q / 6) - 1) : int(np.round(q * 5 / 6)),
    ] = 1

    # main iteration loop starts
    iter = 0
    total_svd = 0
    converged = False

    # time_zero = time.time()
    # time_zero_it = time.time()
    while not converged:
        #    time_zero_it = time.time()
        iter += 1

        if len(A1_coeff.shape) == 1:
            A1_coeff = np.expand_dims(A1_coeff, 0)
        if len(A_offset.shape) == 1:
            A_offset = np.expand_dims(A_offset, 1)
        W_idct_hat = _idct2d(W_hat.T)
        a1_hat = np.dot(np.reshape(W_idct_hat, (-1, 1), order="F"), A1_coeff) + A_offset

        temp_W = (images - a1_hat - e1_hat + (1 / mu) * Y1) / ent1
        temp_W = np.reshape(temp_W, (p, q, n), order="F")
        temp_W = np.mean(temp_W, axis=2)
        W_hat = W_hat + _dct2d(temp_W.T)
        W_hat = np.maximum(W_hat - lambda_flat_field / (ent1 * mu), 0) + np.minimum(
            W_hat + lambda_flat_field / (ent1 * mu), 0
        )
        W_idct_hat = _idct2d(W_hat.T)
        if len(A1_coeff.shape) == 1:
            A1_coeff = np.expand_dims(A1_coeff, 0)
        if len(A_offset.shape) == 1:
            A_offset = np.expand_dims(A_offset, 1)
        a1_hat = np.dot(np.reshape(W_idct_hat, (-1, 1), order="F"), A1_coeff) + A_offset
        e1_hat = images - a1_hat + (1 / mu) * Y1 / ent1
        e1_hat = _shrinkageOperator(e1_hat, weight / (ent1 * mu))
        R1 = images - e1_hat
        A1_coeff = np.mean(R1, 0) / np.mean(R1)
        A1_coeff[A1_coeff < 0] = 0

        if if_dark_field:
            validA1coeff_idx = np.where(A1_coeff < 1)

            B1_coeff = (
                np.mean(
                    R1[
                        np.reshape(W_idct_hat, -1, order="F")
                        > np.mean(W_idct_hat) - 1e-6
                    ][:, validA1coeff_idx[0]],
                    0,
                )
                - np.mean(
                    R1[
                        np.reshape(W_idct_hat, -1, order="F")
                        < np.mean(W_idct_hat) + 1e-6
                    ][:, validA1coeff_idx[0]],
                    0,
                )
            ) / np.mean(R1)
            k = np.array(validA1coeff_idx).shape[1]
            temp1 = np.sum(A1_coeff[validA1coeff_idx[0]] ** 2)
            temp2 = np.sum(A1_coeff[validA1coeff_idx[0]])
            temp3 = np.sum(B1_coeff)
            temp4 = np.sum(A1_coeff[validA1coeff_idx[0]] * B1_coeff)
            temp5 = temp2 * temp3 - temp4 * k
            if temp5 == 0:
                B1_offset = 0
            else:
                B1_offset = (temp1 * temp3 - temp2 * temp4) / temp5
            # limit B1_offset: 0<B1_offset<B1_uplimit

            B1_offset = np.maximum(B1_offset, 0)
            B1_offset = np.minimum(B1_offset, B1_uplimit / (np.mean(W_idct_hat) + 1e-5))

            B_offset = B1_offset * np.reshape(W_idct_hat, -1, order="F") * (-1)

            B_offset = B_offset + np.ones_like(B_offset) * B1_offset * np.mean(
                W_idct_hat
            )
            A1_offset = np.mean(R1[:, validA1coeff_idx[0]], axis=1) - np.mean(
                A1_coeff[validA1coeff_idx[0]]
            ) * np.reshape(W_idct_hat, -1, order="F")
            A1_offset = A1_offset - np.mean(A1_offset)
            A_offset = A1_offset - np.mean(A1_offset) - B_offset

            # smooth A_offset
            W_offset = _dct2d(np.reshape(A_offset, (p, q), order="F").T)
            W_offset = np.maximum(
                W_offset - lambda_dark_field / (ent2 * mu), 0
            ) + np.minimum(W_offset + lambda_dark_field / (ent2 * mu), 0)
            A_offset = _idct2d(W_offset.T)
            A_offset = np.reshape(A_offset, -1, order="F")

            # encourage sparse A_offset
            A_offset = np.maximum(
                A_offset - lambda_dark_field / (ent2 * mu), 0
            ) + np.minimum(A_offset + lambda_dark_field / (ent2 * mu), 0)
            A_offset = A_offset + B_offset

        Z1 = images - a1_hat - e1_hat
        Y1 = Y1 + mu * Z1
        mu = np.minimum(mu * rho, mu_bar)

        # Stop Criterion
        stopCriterion = np.linalg.norm(Z1, ord="fro") / d_norm
        if stopCriterion < optimization_tolerance:
            converged = True

        if not converged and iter >= max_iterations:
            converged = True
    A_offset = np.squeeze(A_offset)
    A_offset = A_offset + B1_offset * np.reshape(W_idct_hat, -1, order="F")

    return a1_hat, e1_hat, A_offset


def _resize_image(
    image: np.ndarray, x_side_size: float = None, y_side_size: float = None
):

    if image.shape[0] != x_side_size or image.shape[1] != y_side_size:
        return skresize(
            image,
            (x_side_size, y_side_size),
            order=RESIZE_ORDER,
            mode=RESIZE_MODE,
            preserve_range=PRESERVE_RANGE,
        )
    else:
        return image


def _shrinkageOperator(matrix, epsilon):
    temp1 = matrix - epsilon
    temp1[temp1 < 0] = 0
    temp2 = matrix + epsilon
    temp2[temp2 > 0] = 0
    res = temp1 + temp2
    return res


def _dct2d(mtrx: np.array):
    """
    Calculates 2D discrete cosine transform.

    Parameters
    ----------
    mtrx
        Input matrix.

    Returns
    -------
    Discrete cosine transform of the input matrix.
    """

    # Check if input object is 2D.
    if mtrx.ndim != 2:
        raise ValueError(
            "Passed object should be a matrix or a numpy array with dimension of two."
        )

    CPU = False
    if CPU:
        from scipy.fftpack import dct

        result = dct(mtrx.T, norm="ortho").T
        result = dct(result, norm="ortho")
    else:
        import tensorflow as tf
        from tensorflow.signal import dct

        print("Num GPUs Available: ", len(tf.config.list_physical_devices("GPU")))
        mtrx = tf.convert_to_tensor(mtrx)
        result = dct(tf.transpose(mtrx), norm="ortho")
        result = dct(result, norm="ortho")
        result = result.numpy()
    return result


def _idct2d(mtrx: np.array):
    """
    Calculates 2D inverse discrete cosine transform.

    Parameters
    ----------
    mtrx
        Input matrix.

    Returns
    -------
    Inverse of discrete cosine transform of the input matrix.
    """
    # Check if input object is 2D.
    if mtrx.ndim != 2:
        raise ValueError(
            "Passed object should be a matrix or a numpy array with dimension of two."
        )

    CPU = False
    if CPU:
        from scipy.fftpack import idct

        result = idct(mtrx.T, norm="ortho").T
        result = idct(result, norm="ortho")
    else:
        import tensorflow as tf
        from tensorflow.signal import idct

        mtrx = tf.convert_to_tensor(mtrx)
        print("Num GPUs Available: ", len(tf.config.list_physical_devices("GPU")))
        result = idct(tf.transpose(mtrx), norm="ortho")
        result = idct(result, norm="ortho")
        result = result.numpy()
    return result


if __name__ == "__main__":
    """
    Testing section for the flat_field correction
    In a windows command prompt, typing nvidia-smi will all you to confirm the
    CUDA Version.  Here, on the acquisition computer, we have 11.4
    GPU Type: Quadro K420
    """
    from tifffile import imread, imsave
    import time
    import os

    # image_path = "E:\test_data\CH01_003.tif"
    input_path = os.path.join("E:", "test_data", "CH01_003b.tif")
    data = imread(input_path)
    start = time.time()
    corrected_data = correct_flat_field(data)
    end = time.time()
    print("The time of execution of above program is :", end - start)

    output_path = os.path.join("E:", "test_data", "corrected_CH01_003.tif")
    imsave(output_path, corrected_data)
