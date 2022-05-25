"""
ASLM camera communication classes.

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

#  Standard Imports
import os
import time
import logging
from pathlib import Path

# Third Party Imports
from tifffile import imread
import numpy as np
from scipy.fftpack import dctn
import tensorflow as tf

# Local Imports

class AnalysisBase:
    def __init__(self, verbose=False):

        # Logger Setup
        p = Path(__file__).resolve().parts[7]
        logger = logging.getLogger(p)

        self.verbose = verbose

    def __del__(self):
        pass

    def calculate_entropy(self, dct_array, otf_support_x, otf_support_y):
        i = dct_array > 0
        image_entropy = np.sum(dct_array[i] * np.log(dct_array[i]))
        image_entropy = image_entropy + \
                        np.sum(-dct_array[~i] * np.log(-dct_array[~i]))
        image_entropy = -2 * image_entropy / (otf_support_x * otf_support_y)
        return image_entropy


class CPUAnalysis(AnalysisBase):
    def __init__(self, verbose=False):

        # Logger Setup
        p = Path(__file__).resolve().parts[7]
        logger = logging.getLogger(p)

        super().__init__(verbose)

    def __del__(self):
        pass

    def normalized_dct_shannon_entropy(self, input_array, psf_support_diameter_xy):
        '''
        # input_array : 2D or 3D image.  If 3D, will iterate through each 2D plane.
        # otf_support_x : Support for the OTF in the x-dimension.
        # otf_support_y : Support for the OTF in the y-dimension.
        # Returns the entropy value.
        '''
        # Get Image Attributes
        # input_array = np.double(input_array)
        image_dimensions = input_array.ndim

        if image_dimensions == 2:
            (image_height, image_width) = input_array.shape
            number_of_images = 1
        elif image_dimensions == 3:
            (number_of_images, image_height, image_width) = input_array.shape
        else:
            raise ValueError("Only 2D and 3D Images Supported.")

        otf_support_x = image_width / psf_support_diameter_xy
        otf_support_y = image_height / psf_support_diameter_xy

        #  Preallocate Array
        entropy = np.zeros(number_of_images)
        execution_time = np.zeros(number_of_images)
        for image_idx in range(int(number_of_images)):
            if self.verbose:
                start_time = time.time()
            if image_dimensions == 2:
                numpy_array = input_array
            else:
                numpy_array = np.array(input_array[image_idx, :, :])

            # Forward 2D DCT
            dct_array = dctn(numpy_array, type=2)

            # Normalize the DCT
            dct_array = np.divide(dct_array, np.linalg.norm(dct_array, ord=2))
            image_entropy = self.calculate_entropy(dct_array, otf_support_x, otf_support_y)

            if self.verbose:
                print("DCTS Entropy:", image_entropy)
                execution_time[image_idx] = time.time() - start_time
                print("Execution Time:", execution_time[image_idx])

            entropy[image_idx] = image_entropy
        return entropy


class GPUAnalysis(AnalysisBase):
    def __init__(self, verbose=False):

        # Logger Setup
        p = Path(__file__).resolve().parts[7]
        logger = logging.getLogger(p)

        super().__init__(verbose)

    def __del__(self):
        pass

    def normalized_dct_shannon_entropy(self, input_array, psf_support_diameter_xy):
        '''
        # input_array : 2D or 3D image.  If 3D, will iterate through each 2D plane.
        # otf_support_x : Support for the OTF in the x-dimension.
        # otf_support_y : Support for the OTF in the y-dimension.
        # Returns the entropy value.
        '''
        # Get Image Attributes
        input_array = np.double(input_array)
        image_dimensions = input_array.ndim

        if image_dimensions == 2:
            (image_height, image_width) = input_array.shape
            number_of_images = 1
        elif image_dimensions == 3:
            (number_of_images, image_height, image_width) = input_array.shape
        else:
            raise ValueError("Only 2D and 3D Images Supported.")

        otf_support_x = image_width / psf_support_diameter_xy
        otf_support_y = image_height / psf_support_diameter_xy

        #  Preallocate Array
        entropy = np.zeros(number_of_images)
        execution_time = np.zeros(number_of_images)

        #  Push to GPU, and iterate through each 2D Image.
        tensor = tf.convert_to_tensor(input_array)
        for image_idx in range(int(number_of_images)):
            if self.verbose:
                start_time = time.time()

            if image_dimensions == 2:
                tensor_array = tensor
            else:
                tensor_array = tensor[image_idx, :, :]

            #  2D DCT performed in series.
            tensor_array = tf.signal.dct(tensor_array, type=2)
            tensor_array = tf.signal.dct(tf.transpose(tensor_array), type=2)
            tensor_array = tf.math.divide(
                tensor_array, tf.norm(
                    tensor_array, ord=2))

            #  Entropy Calculation
            dct_array = tensor_array.numpy()
            image_entropy = self.calculate_entropy(dct_array, otf_support_x, otf_support_y)

            if self.verbose:
                print("DCTS Entropy:", image_entropy)
                execution_time[image_idx] = time.time() - start_time
                print("Execution Time:", execution_time[image_idx])

            entropy[image_idx] = image_entropy
            return entropy


