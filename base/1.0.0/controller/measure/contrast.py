import numpy as np
from scipy.fftpack import dctn, fft2
from preprocessing import *

__all__ = ['downscale', 'vollath_F4', 'normalized_dct_shannon_entropy', 'entropy_shannon_sub_triangle_2D']

def brenner(input_array):
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
    """ 
    input_array : 2D image
    OTF_support_x : Support for the OTF in the x-dimension.
    OTF_support_y : Support for the OTF in the y-dimension.
    Returns the entropy value.
    """
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
    """ 
    entropy = entropy_shannon_sub_triangle_2D(input_array, OTF_support_x, OTF_support_y)
    final double lEntropy = pDoubleArrayImage.entropyShannonSubTriangle(0, 0, lOTFSupportX,lOTFSupportY,true);

    input_array : 3D image
    OTF_support_x : Support for the OTF in the x-dimension.
    OTF_support_y : Support for the OTF in the y-dimension.
    Returns the entropy value.
    """
    length = normalized_array.size
    temp_array = np.reshape(normalized_array, length)
    temp_array = np.double(temp_array)
    entropy = 0
    
    (p_height, p_width) = normalized_array.shape    
    for y in range(int(OTF_support_y)):
        yi = np.int(y * p_width)
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
