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

import cv2
from tifffile import imread
import numpy as np
from scipy.signal import convolve2d
from scipy.stats import kurtosis
from scipy.ndimage import laplace


def normalize_norm_l1(image):
    r"""Calculate and normalize image by L1 norm.

    Parameters
    ----------
    image : np.ndarray
        Input image.

    Returns
    -------
    image : np.ndarray
        Normalized image.
    """
    l1_norm = np.linalg.norm(image, ord=1)
    image = np.divide(image, l1_norm)
    return image


def down_sample_by_sum(input_array, binning_factor=3):
    r"""Down-sample image by taking sum of pixel neighborhood.

    Implemented using a 2D convolution.
    Parameters
    ----------
    input_array : numpy.ndarray
        Original Image
    binning_factor : int
        Factor to down-sample the data by.

    Returns
    -------
    down_sampled_image : numpy.ndarray
        Final image.

    """
    kernel = np.ones((binning_factor, binning_factor))
    convolved = convolve2d(input_array, kernel, mode="valid")
    return convolved[::binning_factor, ::binning_factor]


def brenner_method(input_array):
    image = down_sample_by_sum(input_array, binning_factor=3)
    width = np.shape(image)[1]
    height = np.shape(image)[0]
    image = np.reshape(image, (width * height, 1))
    image = image[1:-1] - image[:]
    print(np.shape(image))

    """		
		for (int yi = 0; yi < height * width; yi += width)
		{
			for (int x = 1; x < width - 1; x++)
			{
				final int i = yi + x;
				final double value = array[i - 1] - array[i + 1];
				accumulator += value * value;
			}
		}
		accumulator /= length;
		"""


def get_absolute_laplace(input_array):
    r"""Measure the absolute summed Laplace of an image.

    Convolution-based.

    Parameters
    ----------
    input_array : np.ndarray
        Input image.

    Returns
    -------
    absolute_laplace : float

    """
    input_array = down_sample_by_sum(input_array, binning_factor=3)
    input_array = normalize_norm_l1(input_array)
    kernel = np.array(np.mat("0, 1, 0; 1, -4, 1; 0, 1 ,0"))
    convolved = np.sum(np.abs(convolve2d(input_array, kernel, mode="same")))
    absolute_laplace = np.sum(convolved)
    return absolute_laplace


def get_basic_image_metrics(image):
    image_mean = np.mean(image)
    image_max = np.max(image)
    image_variance = np.var(image)
    image_normalized_variance = np.divide(
        image_variance, np.multiply(image_mean, image_mean)
    )
    image_kurtosis = kurtosis(image, axis=None, fisher=False, bias=False)
    absolute_laplace = get_absolute_laplace(image)
    descriptor_vector = np.array(
        (
            image_mean,
            image_max,
            image_variance,
            image_normalized_variance,
            image_kurtosis,
            absolute_laplace,
        )
    )
    return descriptor_vector


def test_down_sample_by_sum_2x():
    array = np.arange(24).reshape(4, 6)
    ds_array = down_sample_by_sum(array, binning_factor=2)
    assert np.shape(ds_array) == (2, 3)
    assert ds_array[0, 0] == 14
    assert ds_array[0, 1] == 22
    assert ds_array[0, 2] == 30


def test_down_sample_by_sum_3x():
    array = np.arange(24).reshape(4, 6)
    ds_array = down_sample_by_sum(array, binning_factor=3)
    assert np.shape(ds_array) == (1, 2)
    assert ds_array[0, 0] == 63
    assert ds_array[0, 1] == 90


if __name__ == "__main__":
    import time

    image_path = r"/Users/S155475/Desktop/test_image.tif"
    image = imread(image_path)
    brenner_method(image)
    # autopilot_laplace(image)
