"""
ASLM resolution estimates.

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


import numpy as np
import numpy.matlib
from tifffile import imread, imsave
import logging
from pathlib import Path
# Logger Setup
p = Path(__file__).resolve().parts[7]
logger = logging.getLogger(p)

def image_to_polar(input_image):
    '''
    # imP = im2pol(imC)
    # Transform an image from carthesian to polar coordinate
    # Inputs:
    #  input_image        	Input image in carthesian coordinate
    # Outputs:
    #  imP        	Output image in polar coordinate
    '''
    from scipy import ndimage
    from scipy import interpolate

    radius_minimum = 0
    radius_maximum = 1
    Ny, Nx = np.shape(input_image)

    xc = (Ny + 1) / 2
    yc = (Nx + 1) / 2
    sx = (Ny - 1) / 2
    sy = (Nx - 1) / 2

    Nr = 2 * Ny
    Nth = 2 * Nx

    dr = (radius_maximum - radius_minimum) / (Nr - 1)
    dth = 2 * np.pi / Nth

    r = np.linspace(radius_minimum, radius_maximum, Nr)
    th = np.linspace(0, (Nth - 1) * dth, Nth)
    [r, th] = np.meshgrid(r, th)

    x = np.multiply(r, np.cos(th))
    y = np.multiply(r, np.sin(th))
    xR = x * sx + xc
    yR = y * sy + yc

    #imP = ndimage.map_coordinates(input_image, [xR, yR])
    #imP = interp2(imC, xR, yR,'cubic');
    a = (len(input_image))
    imP = interpolate.interp2d(xR[:, 0], yR[:, 0], input_image, kind='cubic')

    test1 = np.mean(imP)
    test2 = np.min(imP)
    test3 = np.max(imP)
    imP[np.isnan(imP)] = 0
    print('test')

    return imP


def get_radial_average(input_image):
    '''
    # Return the radial average of input square image im
    # Inputs:
    #  im        	Square image
    # Outputs:
    #  r        	Radial average
    '''
    image_size = np.shape(input_image)
    if len(image_size) != 2:
        raise ValueError('Input image must 2D')
    elif image_size[0] != image_size[1]:
        N = np.min(image_size)
        x_start = int(np.floor(np.shape(input_image)[0] / 2 - N / 2) + 1)
        x_end = int(np.floor(np.shape(input_image)[0] / 2 - N / 2) + N)
        y_start = int(np.floor(np.shape(input_image)[1] / 2 - N / 2) + 1)
        y_end = int(np.floor(np.shape(input_image)[1] / 2 - N / 2) + N)

        input_image = input_image[x_start:x_end, y_start:y_end]
        r = np.mean(image_to_polar(input_image), axis=0)
        # r = imresize(r,[1 ceil(size(im,2)/2)],'bilinear')
        return r


def get_decorrelation_local_maxima(decorrelation_function):
    '''
    # Return the local maxima of the decorrelation function decorrelation_function
    # Inputs:
    #  decorrelation_function        	        Decorrelation function
    # Outputs:
    #  max_index        	Position of the local maxima
    #  max_amplitude		Amplitude of the local maxima
    '''

    decorrelation_function = np.array(decorrelation_function)

    number_of_elements = np.shape(decorrelation_function)[0]
    if number_of_elements < 1:
        max_index = 0
        max_amplitude = decorrelation_function[0]
    else:
        # Find the Maxima of the decorrelation function
        max_index = np.argmax(decorrelation_function)
        max_amplitude = decorrelation_function[max_index]

        while np.shape(decorrelation_function)[0] > 0:
            if max_index == np.shape(decorrelation_function)[0]:
                decorrelation_function = decorrelation_function[0:np.shape(
                    decorrelation_function)[0] - 1]
                max_index = np.argmax(decorrelation_function)
                max_amplitude = decorrelation_function[max_index]
            elif max_index == 0:
                break
            elif (max_amplitude - np.min(decorrelation_function[max_index:np.shape(decorrelation_function)[0]])) >= 0.0005:
                # Between max index and end of array
                break
            else:
                decorrelation_function = decorrelation_function[0:np.shape(
                    decorrelation_function)[0] - 1]
                max_index = np.argmax(decorrelation_function)
                max_amplitude = decorrelation_function[max_index]

        if np.size(max_index) == 0:
            max_index = 0
            max_amplitude = decorrelation_function[0]
        else:
            max_amplitude = decorrelation_function[max_index]
    return max_index, max_amplitude


def linear_map(input_value,
               minimum_value,
               maximum_value,
               mapped_minimum_value=None,
               mapped_maximum_value=None
               ):
    '''
    # Performs a linear mapping of input_value from the range [minimum_value,maximum_value] to the range [mapped_minimum_value,mapped_maximum_value]
    # Inputs:
    #  input_value        	Input value
    #  minimum_value		Minimum value of the range of input_value
    #  maximum_value		Maximum value of the range of input_value
    #  mapped_minimum_value		Minimum value of the new range of input_value
    #  mapped_maximum_value		Maximum value of the new range of input_value
    # Outputs:
    #  rescaled_value        	Rescaled value
    '''

    if mapped_minimum_value or mapped_maximum_value is None:
        mapped_minimum_value = minimum_value  # Correct
        mapped_maximum_value = maximum_value  # Correct
        minimum_value = np.min(input_value)  # Correct
        maximum_value = np.max(input_value)  # Incorrect.

    # convert the input value between 0 and 1
    temporary_value = (input_value - minimum_value) / \
        (maximum_value - minimum_value)

    # clamp the value between 0 and 1
    map0 = temporary_value < 0
    map1 = temporary_value > 1
    temporary_value[map0] = 0
    temporary_value[map1] = 1

    # rescale and return
    rescaled_value = np.multiply(
        temporary_value,
        (mapped_maximum_value - mapped_minimum_value)) + mapped_minimum_value
    return rescaled_value


def apodize_image(input_image,
                  number_pixels):
    '''
    # Apodize the edges of a 2D image
    # Inputs:
    #  input_image        	    Input image
    #  number_pixels            Number of pixels of the apodization
    # Outputs:
    #  output_image        	Apodized image
    '''

    # CALCULATE SIZE OF IMAGE AND MEAN VALUE
    y_pixels, x_pixels = np.shape(input_image)
    image_mean = np.mean(input_image)  # image_mean is correct

    # GENERATE X_MASK
    x = np.abs(np.linspace(-x_pixels / 2, x_pixels / 2, x_pixels))
    x_map = x > ((x_pixels / 2) - number_pixels)
    d4 = np.multiply(-np.abs(x) - np.mean(-np.abs(x[x_map])), x_map)
    d = linear_map(d4, -np.pi / 2, np.pi / 2)

    for i in range(0, np.size(d)):
        if not x_map[i]:
            d[i] = np.pi / 2

    x_mask = (np.sin(d) + 1) / 2

    # GENERATE Y_MASK
    y = np.abs(np.linspace(-y_pixels / 2, y_pixels / 2, y_pixels))
    y_map = y > ((y_pixels / 2) - number_pixels)
    d4 = np.multiply(-np.abs(y) - np.mean(-np.abs(y[y_map])), y_map)
    d = linear_map(d4, -np.pi / 2, np.pi / 2)

    for i in range(0, np.size(d)):
        if not y_map[i]:
            d[i] = np.pi / 2

    y_mask = (np.sin(d) + 1) / 2

    # 1D TO 2D
    y_mask = np.matlib.repmat(y_mask, x_pixels, 1)
    x_mask = np.matlib.repmat(x_mask, y_pixels, 1)
    xy_mask = np.multiply(y_mask, np.transpose(x_mask))

    # IMAGE APODIZATION
    output_image = np.multiply(
        (input_image - image_mean),
        np.transpose(xy_mask)) + image_mean
    return output_image


def get_correlation_coefficient(image_1,
                                image_2,
                                c1=None,
                                c2=None):
    '''
    # Return the normalized correlation coefficient expressed in Fourier space
    #
    # Inputs:
    #  image_1        	Complex Fourier transform of image 1
    #  image_2           Complex Fourier transform of image 2
    #
    # Outputs:
    #  correlation_coefficient        	Normalized cross-correlation coefficient
    '''

    # Suppress numpy warnings for invalid values
    numpy.seterr(invalid='ignore')

    if c2 is None:
        c2 = np.sqrt(np.sum(np.square(np.abs(image_2))))

    if c1 is None:
        c1 = np.sqrt(np.sum(np.square(np.abs(image_1))))

    #  cross-correlation between two signals is the product of the signal 1
    #  and the complex conjugate of signal 2.
    #  Here it is normalized to provide a convenient value between 0 and 1.
    correlation_coefficient = np.divide(
        np.sum(
            np.real(
                np.multiply(
                    image_1, np.conj(image_2)))), np.multiply(
            c1, c2))
    correlation_coefficient = np.floor(1000 * correlation_coefficient) / 1000
    return correlation_coefficient


def get_image_decorrelation(input_image,
                            fourier_sampling=None,
                            number_highpass_filters=None):
    '''
    # Estimate the image cut-off frequency based on decorrelation analysis
    # Inputs:
    #  input_image        	2D image to be analyzed
    #  fourier_sampling           	Fourier space sampling of the analysis (default: fourier_sampling = linspace(0,1,50)
    #  number_highpass_filters			Number of high-pass filtering (default: number_highpass_filters = 10)
    # Outputs:
    #  kcMax        Estimated cut-off frequency of the image in normalized frequency
    #  A0			Amplitude of the local maxima of d0
    '''

    if number_highpass_filters is None:
        number_highpass_filters = 10

    if fourier_sampling is None:
        fourier_sampling = np.linspace(0, 1, 50)

    if np.shape(fourier_sampling)[0] < 30:
        fourier_sampling = np.linspace(
            np.min(fourier_sampling), np.max(fourier_sampling), 30)

    if number_highpass_filters < 5:
        number_highpass_filters = 5

    # Calculate the number of samples we will evaluate
    number_fourier_samples = np.shape(fourier_sampling)[0]

    # convert image to type single, and make odd sized only
    input_image = np.single(input_image)
    x_pixels, y_pixels = np.shape(input_image)
    if np.mod(x_pixels, 2) == 0:
        input_image = np.delete(input_image, x_pixels - 1, 0)
    if np.mod(y_pixels, 2) == 0:
        input_image = np.delete(input_image, y_pixels - 1, 1)
    x_pixels, y_pixels = np.shape(input_image)

    # Calculate the first mask
    x = np.linspace(-1, 1, x_pixels)
    y = np.linspace(-1, 1, y_pixels)
    x, y = np.meshgrid(x, y)
    zero_frequency_distance = np.transpose(np.sqrt(x**2 + y**2))
    mask0 = zero_frequency_distance**2 < 1**2

    # Masked Fourier Normalized Image
    fourier_normalized_image = np.fft.fftshift(
        np.fft.fft2(np.fft.fftshift(input_image)))
    fourier_normalized_image = np.divide(
        fourier_normalized_image,
        np.abs(fourier_normalized_image))
    fourier_normalized_image[np.isinf(fourier_normalized_image)] = 0
    fourier_normalized_image[np.isnan(fourier_normalized_image)] = 0
    fourier_normalized_image = np.multiply(fourier_normalized_image, mask0)

    # Masked Fourier Image
    fourier_image = np.fft.fftshift(np.fft.fft2(np.fft.fftshift(input_image)))
    fourier_image = np.multiply(fourier_image, mask0)
    c = np.real(
        np.sqrt(
            np.sum(
                np.multiply(
                    fourier_image,
                    np.conjugate(fourier_image)))))

    sampling_interval = np.linspace(
        fourier_sampling[0], fourier_sampling[-1], number_fourier_samples)

    # Preallocate memory
    d0 = np.zeros(np.shape(fourier_sampling)[0])

    # Get correlation coefficient for the first masked image
    # Iterate through different frequency masks, and calculate the correlation
    # coefficient
    for k in range(np.shape(fourier_sampling)[0] - 1, -1, -1):
        mask1 = zero_frequency_distance**2 < sampling_interval[k]**2
        masked_image = np.multiply(fourier_normalized_image, mask1)
        cc = get_correlation_coefficient(fourier_image, masked_image, c)
        if np.isnan(cc):
            cc = 0
        d0[k] = cc

    # Find the local maxima of d0, which is the maximum correlation coefficient
    ind0, snr0 = get_decorrelation_local_maxima(d0[k:-1])

    # Identify what frequency the maximum correlation coefficient is at
    k0 = fourier_sampling[ind0]
    gMax = 2 / sampling_interval[ind0]
    if np.isinf(gMax):
        gMax = max(np.shape(input_image)[0], np.shape(input_image)[1]) / 2

    # Search for the Highest Frequency Peak.
    number_iterations = 2

    # Secondary sampling interval
    g = np.hstack(
        (np.shape(input_image)[0] / 4,
         np.exp(
            np.linspace(
                np.log(gMax),
                np.log(0.15),
                number_highpass_filters))))

    # Preallocate memory
    kc = np.zeros(np.shape(g)[0] * number_iterations + 1)
    SNR = np.zeros(np.shape(g)[0] * number_iterations + 1)
    d = np.zeros((number_fourier_samples, 2 * number_highpass_filters))

    # Populate the results from the initial correlation coefficient
    kc[0] = k0
    SNR[0] = snr0
    ind0 = 0

    # Two Step Refinement
    for iteration_idx in range(number_iterations):  # 0, 1.
        for sampling_idx in range(np.shape(g)[0] - 1):  # 0..10

            # Fourier Gaussian Filtering
            Ir = np.multiply(fourier_image, (1 - np.exp(-2 * \
                             g[sampling_idx] * g[sampling_idx] * zero_frequency_distance**2)))
            c = np.sqrt(np.sum(np.abs(Ir)**2))
            for k in range(
                    np.shape(fourier_sampling)[0] - 1, ind0 - 1, -1):  # 49...0
                mask = zero_frequency_distance**2 < fourier_sampling[k]**2
                cc = get_correlation_coefficient(
                    Ir[mask], fourier_normalized_image[mask], c)
                if np.isnan(cc):
                    cc = 0
                d[k, sampling_idx + number_highpass_filters * iteration_idx] = cc
                # d is 50 rows x 20 columns.
                # sampling_idx = 0:9,
                # number_highpass_filters = 10,
                # iteration_idx = 0:1

            ind, amp = get_decorrelation_local_maxima(
                d[k:len(d), sampling_idx + number_highpass_filters * iteration_idx])
            snr = d[ind, sampling_idx + number_highpass_filters * iteration_idx]
            ind = ind + k
            kc[sampling_idx + number_highpass_filters *
                iteration_idx + 1] = fourier_sampling[ind]
            SNR[sampling_idx + number_highpass_filters * iteration_idx + 1] = snr

        # refining the high-pass threshold and the radius sampling
        # Correct Above
        if iteration_idx == 0:
            # High-Pass Filtering Refinement
            indmax = np.where(kc == np.max(kc))[0]
            ind1 = indmax[-1]
            if ind1 == 0:  # Peak only without highpass.
                ind1 = 0
                ind2 = 1
                g1 = np.shape(input_image)[0]
                g2 = g[0]
            elif ind1 >= np.shape(g)[0]:
                ind2 = ind1 - 1
                ind1 = ind1 - 2
                g1 = g[ind1]
                g2 = g[ind2]
            else:
                ind2 = ind1
                ind1 = ind1 - 1
                g1 = g[ind1]
                g2 = g[ind2]

            g = np.exp(
                np.linspace(
                    np.log(g1),
                    np.log(g2),
                    number_highpass_filters))
            # Radius Sampling Refinement
            r1 = kc[indmax[-1]] - (fourier_sampling[1] - fourier_sampling[0])
            r2 = kc[indmax[-1]] + 0.4
            if r1 < 0:
                r1 = 0
            if r2 > 1:
                r2 = 1

            # np.minimum is the pairwise minimum of the array elements.
            fourier_sampling = np.linspace(r1, np.minimum(
                r2, fourier_sampling[-1]), number_fourier_samples)
            ind0 = 0
            r2 = fourier_sampling

    # Add d0 results to the analysis (useful for high noise images)
    kc = np.append(kc, k0)
    SNR = np.append(SNR, snr0)

    # Need at least 0.05 of SNR to be even considered
    kc[SNR < 0.05] = 0
    SNR[SNR < 0.05] = 0
    snr = SNR

    # output results computation
    if kc.size != 0:
        # highest resolution found
        ind = np.argmax(kc)
        kcMax = kc[ind]
        A0 = snr0
    else:
        kcMax = fourier_sampling[1]
        res = fourier_sampling[1]
        A0 = 0

    return kcMax, A0


def main_image_decorr():
    '''
    https://github.com/Ades91/ImDecorr/blob/master/main_imageDecorr.m
    '''

    # User Inputs
    image_location = '/Users/S155475/Local/Publication materials/2020-SOLS/Data/MV3Membrane/LateralInsets/DetailVesicleTimepoint30.tif'
    #image_location = '/Users/S155475/Downloads/test_image.tif'
    number_high_pass_filters = 10
    fourier_samples = 50
    apodization_pixels = 20

    # Load the Data
    raw_image = np.array(imread(image_location))
    raw_image = np.double(raw_image)

    # Apodize Image Edges with a Cosine Function over 20 pixels
    image = apodize_image(raw_image, apodization_pixels)

    # Compute Resolution
    kcMax, A0 = get_image_decorrelation(image, np.linspace(
        0, 1, fourier_samples), number_high_pass_filters)

    print("kcMax:", kcMax)
    print("A0:", A0)
    pixel_size = 110
    print("Resolution:", 2 * pixel_size / kcMax)

    get_radial_average(raw_image)


if (__name__ == '__main__'):
    main_image_decorr()
