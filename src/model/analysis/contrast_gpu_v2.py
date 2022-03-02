from tifffile import imread
import numpy as np
import time
from scipy.fftpack import dctn
import tensorflow as tf


def normalized_dct_shannon_entropy(input_array, PSF_support_diameter_xy, use_CPU, verbose=False):
    '''
    # input_array : 2D or 3D image.  If 3D, will iterate through each 2D plane.
    # OTF_support_x : Support for the OTF in the x-dimension.
    # OTF_support_y : Support for the OTF in the y-dimension.
    # Returns the entropy value.
    '''

    if use_CPU:
        if verbose:
            print("Using the CPU")
    else:
        initiate_gpu()
        if verbose:
            print("Using the GPU")

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

    #  Preallocate Array
    entropy = np.zeros(number_of_images)
    execution_time = np.zeros(number_of_images)
    tensor = tf.convert_to_tensor(input_array)

    #  Measure Entropy for each 2D Image
    for image_idx in range(int(number_of_images)):
        if verbose:
            start_time = time.time()

        tensor_array = tensor[image_idx, :, :]

        # Forward DCT  - e.g., dct(dct(mtrx.T, norm='ortho').T, norm='ortho')
        tensor_array = tf.signal.dct(tensor_array, type=2)
        tensor_array = tf.signal.dct(tf.transpose(tensor_array), type=2)

        # Normalize DCT - dtype = 'float64'
        tensor_array = tf.math.divide(tensor_array, tf.norm(tensor_array, ord=2))

        # Calculate Entropy
        tensorflow_math = True
        if tensorflow_math:
            #  Use TensorFlow Math Operations.  Still returns a NaN.  Need to figure out why...
            data_type = tf.float32
            entropy_threshold = tf.convert_to_tensor([1], dtype=data_type)
            tensor_array = tf.cast(tensor_array, dtype=data_type)
            i = tf.math.greater(tensor_array, entropy_threshold)
            image_entropy = tf.math.reduce_sum(tensor_array[i] * tf.math.log(tensor_array[i]))
            image_entropy = tf.math.add(image_entropy,
                                        tf.math.reduce_sum(-tensor_array[~i] * tf.math.log(-tensor_array[~i])))

            otf_constant = tf.constant([OTF_support_x * OTF_support_y], dtype=data_type)
            image_entropy = tf.math.divide(image_entropy, otf_constant)
            image_entropy = tf.multiply(tf.constant([-2], dtype=data_type), image_entropy)
            image_entropy = image_entropy.numpy()
        else:
            #  Switch back to Numpy for Math Operations
            dct_array = tensor_array.numpy()
            i = dct_array > 0
            image_entropy = np.sum(dct_array[i] * np.log(dct_array[i]))
            image_entropy = image_entropy + np.sum(-dct_array[~i] * np.log(-dct_array[~i]))
            image_entropy = -2 * image_entropy / (OTF_support_x * OTF_support_y)

        if verbose:
            print("DCTS Entropy:", image_entropy)
            execution_time[image_idx] = time.time() - start_time
            print("Execution Time:", execution_time[image_idx])

        entropy[image_idx] = image_entropy

    if verbose:
        print("Mean Entropy:", np.mean(entropy), "Std. Dev:", np.std(entropy))
        print("Mean Execution Time:", np.mean(execution_time), "Std. Dev:", np.std(execution_time))

    return entropy

def initiate_gpu():
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        # Create 2 virtual GPUs with 24GB memory each
        try:
            tf.config.set_logical_device_configuration(gpus[0],
                                                       [tf.config.LogicalDeviceConfiguration(memory_limit=23000),
                                                        tf.config.LogicalDeviceConfiguration(memory_limit=23000)])
            logical_gpus = tf.config.list_logical_devices('GPU')
            print(len(gpus), "Physical GPU,", len(logical_gpus), "Logical GPUs")
        except RuntimeError as e:
            # Virtual devices must be set before GPUs have been initialized
            print(e)

if (__name__ == "__main__"):

    # Contrast metrics testing
    import os

    # Contrast metrics testing
    image_data = imread(os.path.join("E:", "test_data", "CH01_003b.tif"))
    PSF_support = 3
    verbose = True
    use_CPU = False

    entropy = normalized_dct_shannon_entropy(image_data, PSF_support, use_CPU, verbose)
