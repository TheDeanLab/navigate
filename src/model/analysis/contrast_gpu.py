from tifffile import imread
import numpy as np
import tensorflow as tf
import time


def normalized_dct_shannon_entropy(input_array, PSF_support_diameter_xy=3, verbose=False):
    '''
    # input_array : 2D or 3D image.  If 3D, will iterate through each 2D plane.
    # OTF_support_x : Support for the OTF in the x-dimension.
    # OTF_support_y : Support for the OTF in the y-dimension.
    # Returns the entropy value.
    '''

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

    OTF_support_x = image_width / PSF_support_diameter_xy
    OTF_support_y = image_height / PSF_support_diameter_xy

    entropy = np.zeros(number_of_images)
    for image_idx in range(int(number_of_images)):
        if verbose:
            start_time = time.time()

        if image_dimensions == 2:
            tensor_array = tf.convert_to_tensor(input_array)
        else:
            tensor_array = tf.convert_to_tensor(input_array[image_idx, :, :])

        # Forward DCT
        tensor_array = tf.signal.dct(tf.transpose(tensor_array), type=2)
        tensor_array = tf.signal.dct(tensor_array, type=2)

        # Normalize DCT
        tensor_array = tf.math.divide(tensor_array, tf.norm(tensor_array, ord=2))

        # Convert to Numpy Array
        dct_array = tensor_array.numpy()

        # Calculate Entropy
        i = dct_array > 0
        image_entropy = np.sum(dct_array[i] * np.log(dct_array[i]))
        image_entropy = image_entropy + np.sum(-dct_array[~i] * np.log(-dct_array[~i]))
        image_entropy = -2*image_entropy / (OTF_support_x * OTF_support_y)

        if (verbose):
            print("DCTS Entropy:", image_entropy)
            print("Execution Time:", time.time() - start_time)

        entropy[image_idx] = image_entropy
    return entropy

if (__name__ == "__main__"):
    import os

    # Contrast metrics testing
    image_data = imread(os.path.join("E:", "test_data", "CH01_003.tif"))
    PSF_support = 3
    verbose = True

    entropy = normalized_dct_shannon_entropy(image_data, PSF_support, verbose)
