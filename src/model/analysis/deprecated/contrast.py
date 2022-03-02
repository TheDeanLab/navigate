'''
Contrast metrics used for autofocusing the microscope and optimizing the imaging parameters (e.g., remote focus, etc.).
Converted to Python from Java by: Sampath Rapuri
Java functions found here: https://github.com/MicroscopeAutoPilot/AutoPilot
'''

import numpy as np
from scipy.fftpack import dctn, fft2

__all__ = ['downscale', 'vollath_F4', 'normalized_dct_shannon_entropy', 'entropy_shannon_sub_triangle_2D',
           'downscale', 'mean', 'variance', 'normalize_norm_L2', 'normalize_norm_L1', 'norm_L2', 'norm_L1',
           'normalize_DC']

def downscale(input_array, verbose=False):
    '''
    # This function downscales 2D data by a factor of 3
    # Can be changed to accept 2D and 3D data
    # Can be changed to accept different downscaling factors
    '''
    downscale_factor = 3
    (width, height) = input_array.shape
    input_array = input_array.reshape(width * height)
    dswidth, dsheight = int(width/downscale_factor), int(height/downscale_factor)
    final_array = np.zeros([dswidth*dsheight])

    # What is this doing?
    # width = downscale_factor * int(width/downscale_factor)
    # height = downscale_factor * int(height/downscale_factor)
    y = 0
    while y < height:
        yi = y * width
        yip = int(y/downscale_factor) * dswidth
        y += 1
        x = 0
        while x < width:
            i = yi + x
            xp = int(x/downscale_factor)
            ip = yip + xp
            x += 1
            if ip < dswidth*dsheight:
                final_array[ip] += input_array[i]
    if verbose:
        print("**** downscale ****")
        print("The shape of the output array is: ", np.shape(final_array))
    final_array = np.reshape(final_array, )
    return(final_array)

def mean(input_array):
    '''
    # Downscales the data and returns the mean
    '''
    downscaled = downscale(input_array)
    return(np.mean(downscaled))

def variance(input_array):
    '''
    # Downscales the data and returns the variance
    '''
    downscaled = downscale(input_array)
    return(np.var(downscaled))

def normalize_norm_L2(input_array, verbose=False):
    """
    # Function accepts a 2D or 3D image, and returns the L2 normalized image
    # L2 norm is the square root of the sum of the squares of the elements
    """
    norm = norm_L2(input_array, verbose)

    if (norm != 0):
        invnorm = np.double(1 / norm)
        normalized_array = np.dot(input_array, invnorm)

        if (verbose):
            print("**** normalize_norm_L2 ****")
            print("Norm != 0: Input data is finite.")
            print("Inverse Norm = " + str(invnorm))
            print("Normalized Array has shape = " + str(np.shape(normalized_array)))
    else:
        if (verbose):
            print("Norm=0: Input data non-finite.")
    return normalized_array

def normalize_norm_L1(input_array, verbose=False):
    '''
    # Function accepts a 2D or 3D image, and returns the L1 normalized image
    # L1 norm is the sum of the absolute values of the elements
    '''
    norm = norm_L1(input_array, verbose)
    if (norm != 0):
        invnorm = np.double(1 / norm)
        normalized_array = np.dot(input_array, invnorm)

    if (verbose):
        print("**** normalize_norm_L1 ****")
        print("Norm != 0: Input data is finite.")
        print("Inverse Norm = " + str(invnorm))
        print("Normalized Array has shape = " + str(np.shape(normalized_array)))
    else:
        if (verbose):
            print("Norm=0: Input data non-finite.")
        return normalized_array

def norm_L2(input_array, verbose=False):
    '''
    # input_array : 2D or 3D image
    # Returns the sum of the L2 norm for the image
    '''
    input_array = np.square(input_array)
    norm = np.sum(input_array)
    norm = np.sqrt(norm)

    if (verbose):
        print("**** norm_L2 ****")
        print("The Norm = " + str(norm))

    return (norm)

def norm_L1(input_array, verbose=False):
    '''
    # input_array : 2D or 3D image
    # Returns the sum of the L1 norm for the image
    '''
    input_array = np.abs(input_array)
    sum = np.sum(input_array)
    if (verbose):
        print("**** norm_L1 ****")
    return sum

def normalize_DC(input_array, new_DC, verbose=False):
    '''
    # Function accepts a 2D or 3D image, and returns the normalized image
    '''
    image_average_value = np.mean(np.reshape(normalized_array, input_array.size))
    correction_value = new_DC - image_average_value
    corrected_array = np.sum(input_array, correction_value)

    if (verbose):
        print("**** normalize_DC ****")
        print("The Image Average Intensity: " + str(image_average_value))
    return corrected_array

def brenner(input_array):
    '''
    # Function accepts a 2D or 3D image, and returns the Brenner's method
    '''
    normalized_array = normalize_norm_L1(input_array)
    length = len(normalized_array)
    (width, height) = input_array.shape
    width = int(width /3)
    height = int(height/3)
    accumulator = 0
    yi = 0
    while yi < height * width:
        x = 1
        while x < width - 1:
            i = int(yi + x)
            value = normalized_array[i - 1] - normalized_array[i + 1]
            accumulator += value * value
            x+= 1
        yi += width
    accumulator /= length
    return(accumulator)

def vollath_F4(input_array, verbose=False):
    '''
    # Function accepts a 2D or 3D image, and returns the Vollath's F4 method
    '''
    input_array = downscale(input_array, verbose=verbose)
    input_array = normalize_norm_L1(input_array, verbose=verbose)
    (width, height) = input_array.shape

    accumulator, x, yi, i, value = 0, 0, 0, 0, 0
    while yi < dsheight * dswidth:
        while x < (dswidth-2):
            i = yi + x
            value = input_array[i] * input_array[i+1] - input_array[i + 2]
            accumulator = accumulator + value
            x = x + 1
        yi = yi + dswidth

    if verbose:
        print("**** Vollath_F4 ****")

    return accumulator

def normalized_dct_shannon_entropy(input_array, verbose=False):
    '''
    # input_array : 2D image
    # OTF_support_x : Support for the OTF in the x-dimension.
    # OTF_support_y : Support for the OTF in the y-dimension.
    # Returns the entropy value.
    '''
    PSF_support_diameter_xy = 3
    (image_height, image_width) = input_array.shape      
    
    # Forward DCT
    input_array = np.double(input_array)
    dct_array = dctn(input_array, type=2)
    normalized_dct_array = normalize_norm_L2(dct_array, verbose)
   
    OTF_support_x = image_width/PSF_support_diameter_xy
    OTF_support_y = image_height/PSF_support_diameter_xy
    
    entropy = entropy_shannon_sub_triangle_2D(normalized_dct_array, OTF_support_x, OTF_support_y, verbose)
    if(verbose):
        print("**** double_dct_2D ****")
        print("DCTS: Received data of height: " + str(image_width))
        print("DCTS: Received data of width: " + str(image_height))
        print("DCTS: Max value: " + str(np.max(dct_array)))
        print("DCTS: Entropy = " + str(entropy))
        
        # Plot the Data
        plt.figure(1)
        plt.subplot(121)
        plt.imshow(input_array)
        plt.subplot(122)
        plt.imshow(dct_array)
    return entropy
    
def entropy_shannon_sub_triangle_2D(normalized_array, OTF_support_x, OTF_support_y, verbose=False):
    '''
    # entropy = entropy_shannon_sub_triangle_2D(input_array, OTF_support_x, OTF_support_y)
    # final double lEntropy = pDoubleArrayImage.entropyShannonSubTriangle(0, 0, lOTFSupportX,lOTFSupportY,true);
    # input_array : 3D image
    # OTF_support_x : Support for the OTF in the x-dimension.
    # OTF_support_y : Support for the OTF in the y-dimension.
    # returns the entropy value.
    '''
    length = normalized_array.size
    temp_array = np.reshape(normalized_array, length)
    temp_array = np.double(temp_array)
    entropy = 0
    
    (p_height, p_width) = normalized_array.shape    
    for y in range(int(OTF_support_y)):
        yi = int(y * p_width)
        xend = OTF_support_x - y * (OTF_support_x/OTF_support_y)

        for x in range(int(xend)):
            i = yi + x
            value = 0
            value = temp_array[i]
            if(value > 0):
                entropy += value * np.log(value)
            elif(value < 0):
                entropy += -value*np.log(-value)
    entropy = -entropy
    entropy = 2*entropy/(OTF_support_x*OTF_support_y)
    
    if(verbose):
        print("**** entropy_shannon_sub_triangle_2D ****")
        print("Entropy = " + str(entropy))
        print("Range of OTF_support_y = " + str())
    return entropy

if (__name__ == "__main__"):
    import matplotlib.pyplot as plt
    # Contrast metrics testing
