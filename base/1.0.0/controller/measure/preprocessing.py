import numpy as np
from scipy.fftpack import dctn, fft2

__all__ = ['downscale', 'mean', 'variance', 'normalize_norm_L2',
           'normalize_norm_L1', 'norm_L2', 'norm_L1', 'normalize_DC']

def downscale(input_array, verbose=False):
    (width, height) = input_array.shape
    input_array = input_array.reshape(width * height)
    dswidth, dsheight = int(width/3), int(height/3)
    final_array = np.zeros([dswidth*dsheight])
    y = 0
    width = 3 * int(width/3)
    height = 3 * int(height/3)
    while y < height:
        yi = y * width
        yip = int(y/3) * dswidth
        y += 1
        x = 0
        while x < width:
            i = yi + x
            xp = int(x/3)
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
    downscaled = downscale(input_array)
    return(np.mean(downscaled))

def variance(input_array):
    downscaled = downscale(input_array)
    return(np.var(downscaled))

def normalize_norm_L2(input_array, verbose=False):
    """ input_array : 2D or 3D image
    Returns the normalized L2 norm for the image
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
    """
    input_array : 2D or 3D image
    Returns the sum of the L2 norm for the image
    """
    input_array = np.square(input_array)
    norm = np.sum(input_array)
    norm = np.sqrt(norm)

    if (verbose):
        print("**** norm_L2 ****")
        print("The Norm = " + str(norm))

    return (norm)

def norm_L1(input_array, verbose=False):
    """
    input_array : 2D or 3D image
    Returns the sum of the L1 norm for the image
    """
    input_array = np.abs(input_array)
    sum = np.sum(input_array)
    if (verbose):
        print("**** norm_L1 ****")
    return sum

def normalize_DC(input_array, new_DC, verbose=False):
    image_average_value = np.mean(np.reshape(normalized_array, input_array.size))
    correction_value = new_DC - image_average_value
    corrected_array = np.sum(input_array, correction_value)

    if (verbose):
        print("**** normalize_DC ****")
        print("The Image Average Intensity: " + str(image_average_value))
    return corrected_array
