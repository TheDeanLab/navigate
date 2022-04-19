"""
ASLM image contrast estimates.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

#  Python Imports
import os
import time

# Second Party Imports
from tifffile import imread
import numpy as np
from scipy.fftpack import dctn
import tensorflow as tf


def normalized_dct_shannon_entropy(
        input_array,
        psf_support_diameter_xy,
        verbose=False):
    '''
    # input_array : 2D or 3D image.  If 3D, will iterate through each 2D plane.
    # OTF_support_x : Support for the OTF in the x-dimension.
    # OTF_support_y : Support for the OTF in the y-dimension.
    # Returns the entropy value.
    '''

    #use_cpu = initiate_gpu()
    use_cpu = False

    # Image Attributes
    input_array = np.double(input_array)
    image_dimensions = input_array.ndim

    if image_dimensions == 2:
        (image_height, image_width) = input_array.shape
        number_of_images = 1
    elif image_dimensions == 3:
        (number_of_images, image_height, image_width) = input_array.shape
    else:
        raise ValueError("Only 2D and 3D Images Supported.")

    OTF_support_x = image_width / psf_support_diameter_xy
    OTF_support_y = image_height / psf_support_diameter_xy

    #  Preallocate Array
    entropy = np.zeros(number_of_images)
    execution_time = np.zeros(number_of_images)

    if use_cpu:
        for image_idx in range(int(number_of_images)):
            if verbose:
                start_time = time.time()

            if image_dimensions == 2:
                numpy_array = input_array
            else:
                numpy_array = np.array(input_array[image_idx, :, :])

            # Forward 2D DCT
            dct_array = dctn(numpy_array, type=2)

            # Normalize the DCT
            dct_array = np.divide(dct_array, np.linalg.norm(dct_array, ord=2))
            image_entropy = calculate_entropy(
                dct_array, OTF_support_x, OTF_support_y)

            if verbose:
                print("DCTS Entropy:", image_entropy)
                execution_time[image_idx] = time.time() - start_time
                print("Execution Time:", execution_time[image_idx])

        entropy[image_idx] = image_entropy

    else:
        tensor = tf.convert_to_tensor(input_array)

        #  Iterate through each 2D image.
        for image_idx in range(int(number_of_images)):
            if verbose:
                start_time = time.time()

            if image_dimensions == 2:
                tensor_array = tensor
            else:
                tensor_array = tensor[image_idx, :, :]

            # Forward DCT  - e.g., dct(dct(mtrx.T, norm='ortho').T,
            # norm='ortho')
            tensor_array = tf.signal.dct(tensor_array, type=2)
            tensor_array = tf.signal.dct(tf.transpose(tensor_array), type=2)

            # Normalize DCT - dtype = 'float64'
            tensor_array = tf.math.divide(
                tensor_array, tf.norm(
                    tensor_array, ord=2))

            #  Entropy Calculation
            dct_array = tensor_array.numpy()
            image_entropy = calculate_entropy(
                dct_array, OTF_support_x, OTF_support_y)

            if verbose:
                print("DCTS Entropy:", image_entropy)
                execution_time[image_idx] = time.time() - start_time
                print("Execution Time:", execution_time[image_idx])

        entropy[image_idx] = image_entropy

    if verbose:
        print("Mean Entropy:", np.mean(entropy), "Std. Dev:", np.std(entropy))
        print(
            "Mean Execution Time:",
            np.mean(execution_time),
            "Std. Dev:",
            np.std(execution_time))

    return entropy


def calculate_entropy(dct_array, OTF_support_x, OTF_support_y):
    i = dct_array > 0
    image_entropy = np.sum(dct_array[i] * np.log(dct_array[i]))
    image_entropy = image_entropy + \
        np.sum(-dct_array[~i] * np.log(-dct_array[~i]))
    image_entropy = -2 * image_entropy / (OTF_support_x * OTF_support_y)
    return image_entropy


def initiate_gpu():
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        use_cpu = False
        # Create 2 virtual GPUs with 24GB memory each
        try:
            tf.config.set_logical_device_configuration(
                gpus[0], [
                    tf.config.LogicalDeviceConfiguration(
                        memory_limit=23000), tf.config.LogicalDeviceConfiguration(
                        memory_limit=23000)])
            logical_gpus = tf.config.list_logical_devices('GPU')
        except RuntimeError as e:
            # Virtual devices must be set before GPUs have been initialized
            print(e)
    else:
        use_cpu = True
    return use_cpu


if (__name__ == "__main__"):
    # Contrast metrics testing
    image_data = imread(os.path.join("E:", "test_data", "CH01_003b.tif"))
    PSF_support = 3
    verbose = True
    entropy = normalized_dct_shannon_entropy(image_data, PSF_support, verbose)
