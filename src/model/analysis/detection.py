'''
Object detection functions
'''

# Third Party Modules
import numpy as np
from skimage.filters import threshold_otsu
from skimage.morphology import dilation, erosion, remove_small_objects
from skimage.measure import label, regionprops
from skimage.feature import blob_log, blob_dog, blob_doh
from scipy.ndimage import gaussian_filter, binary_fill_holes
from scipy import ndimage, signal
import matplotlib.pyplot as plt


def add_median_border(image_data):
    '''
    # Add Border to Image that is the Median of the Image
    # Requires 3D image.
    '''
    (z_len, y_len, x_len) = image_data.shape
    median_intensity = np.median(image_data)
    padded_image_data = np.full((z_len+2, y_len+2, x_len+2), median_intensity)
    padded_image_data[1:z_len+1, 1:y_len+1, 1:x_len+1]=image_data
    return padded_image_data

def make_sphere_3D(radius):
    '''
    # Make a 3D structured element in the shape of a sphere
    '''
    radius = int(radius)
    sphere = np.zeros((radius, radius, radius))
    (z_len, y_len, x_len) = sphere.shape
    for i in range(int(z_len)):
        for j in range(int(y_len)):
            for k in range(int(x_len)):
                if ((i**2+j**2+k**2)/radius**2) < 1:
                    sphere[i,j,k]=1
    return sphere

def make_inside_image(padded_image_data, insideGamma,insideBlur, insideDilateRadius, insideErodeRadius):
    '''
    # Function tries to fill the interior of a cell.
    # Gaussian blur followed by Otsu thresholding, dilation, hole filling, and erosion.
    '''
    image_blurred = padded_image_data**insideGamma
    image_blurred = gaussian_filter(image_blurred, sigma=insideBlur)
    image_binary = image_blurred > threshold_otsu(image_blurred)
    image_binary = dilation(image_binary, make_sphere_3D(insideDilateRadius))
    image_binary = ndimage.binary_fill_holes(image_binary)
    image_binary = np.double(erosion(image_binary, make_sphere_3D(insideErodeRadius)))
    inside_image = gaussian_filter(image_binary, sigma=1)
    return inside_image

def make_normalized_image(image_data):
    '''
    # Normalizes the image.  Subtracts Otsu threshold from the image, and normalizes it by the standard deviation.
    '''
    normalized_cell = padded_image_data - threshold_otsu(image_data)
    normalized_cell = normalized_cell/np.std(normalized_cell)
    return normalized_cell

def surface_filter_gauss_3D(image_data, sigma):
    '''
    # Function identifies surfaces in Z, Y, and Z directions. Returns each image.
    '''
    # Same Sigma Value for All 3 Dimensions
    w = np.ceil(5*sigma)
    x = np.arange(-w, w, 1)
    g = np.zeros(x.shape)

    # Calculate 1D Gaussian
    for i in range(int(x.size)):
        g[i] = np.exp(-x[i]**2/(2*sigma**2))

    # Calculate Second Derivative of 1D Gaussian
    d2g = np.zeros(x.shape)
    for i in range(int(x.size)):
        d2g[i] = (-(x[i]**2/sigma**2 - 1) / sigma**2)*(np.exp(-x[i]**2/(2*sigma**2)))

    gSum = np.sum(g)

    #1D Gaussian Kernel
    g = g/gSum
    #1D Second Derivative Kernel
    d2g = d2g/gSum

    # Second Derivative of 1D Gaussian Kernel in Z
    d2z_image = signal.fftconvolve(image_data, d2g[:, None, None], mode='same')
    d2z_image = signal.fftconvolve(d2z_image, g[None, :, None], mode='same')
    d2z_image = signal.fftconvolve(d2z_image, g[None, None, :], mode='same')

    # Second Derivative of 1D Gaussian Kernel in Y
    d2y_image = signal.fftconvolve(image_data, d2g[None, :, None], mode='same')
    d2y_image = signal.fftconvolve(d2y_image, g[None, None, :], mode='same')
    d2y_image = signal.fftconvolve(d2y_image, g[:, None, None], mode='same')

    # Second Derivative of 1D Gaussian Kernel in X
    d2x_image = signal.fftconvolve(image_data, d2g[None, None, :], mode='same')
    d2x_image = signal.fftconvolve(d2x_image, g[:, None, None], mode='same')
    d2x_image = signal.fftconvolve(d2x_image, g[None, :, None], mode='same')

    return d2z_image, d2y_image, d2x_image

def multiscale_surface_filter_3D(input, scales: list):
    '''
    # Function identifies surfaces at multiple scales.
    '''
    n_scales = np.size(scales)
    max_response = np.zeros(np.shape(input))
    max_response_scale = np.zeros(np.shape(input))

    for i in range(n_scales):
        d2z_temp, d2y_temp, d2x_temp = surface_filter_gauss_3D(input, scales[i])
        d2z_temp[d2z_temp < 0] = 0
        d2y_temp[d2y_temp < 0] = 0
        d2x_temp[d2x_temp < 0] = 0

        sMag = np.sqrt(d2z_temp**2 + d2y_temp**2 + d2x_temp**2)
        is_better = sMag > max_response
        max_response_scale[is_better] = i
        max_response[is_better] = sMag[is_better]

    surface_background_mean = np.mean(max_response)
    surface_background_std = np.std(max_response)
    surface_threshold = surface_background_mean + (nSTDsurface*surface_background_std)
    surface_cell = max_response - surface_threshold
    surface_cell = max_response/np.std(max_response)

    return surface_cell

def combine_images(inside_image, normalized_cell, surface_cell):
    '''
    # Function combines the inside image, normalized cell, and surface cell images.
    '''
    level = 0.999
    combined_image = np.maximum(np.maximum(inside_image, normalized_cell), surface_cell);
    combined_image[combined_image < 0] = 0
    combined_image = combined_image > level
    combined_image = binary_fill_holes(combined_image)

    # Label Connected Components
    labeled_image = label(combined_image)
    label_properties = regionprops(labeled_image)

    # Find Biggest Connected Component
    label_areas = np.zeros(np.size(label_properties[:]))
    for a in range(int(np.size(label_properties[:]))):
        label_areas[a] = label_properties[a].area
    max_label = np.argmax(label_areas, axis=None)

    # Take only the largest connected component.
    final_image = np.zeros(np.shape(labeled_image))
    final_image[labeled_image==max_label+1] = 1
    return final_image

def three_level_segmentation(image_data):
    padded_image_data = add_median_border(image_data)
    inside_image = make_inside_image(padded_image_data, insideGamma, insideBlur, insideDilateRadius, insideErodeRadius)
    normalized_cell = make_normalized_image(padded_image_data)
    surface_cell = multiscale_surface_filter_3D(padded_image_data, scales)
    final_image = combine_images(inside_image, normalized_cell, surface_cell)
    return final_image

def log_detection(image_data, image_threshold=None, pixel_size=0.206):
    # https://github.com/scikit-image/scikit-image/blob/v0.19.0/skimage/feature/blob.py#L401-L564
    blobs_log = blob_log(image_data, max_sigma=20, num_sigma=3, threshold=image_threshold)
    blobs_log[:, 2] = blobs_log[:, 2] * np.sqrt(2) * pixel_size

    blobs_dog = blob_dog(image_data, max_sigma=20, threshold=image_threshold)
    blobs_dog[:, 2] = blobs_dog[:, 2] * np.sqrt(2) * pixel_size

    blobs_list = [blobs_log, blobs_dog]
    colors = ['yellow', 'lime']
    titles = ['Laplacian of Gaussian', 'Difference of Gaussian']
    sequence = zip(blobs_list, colors, titles)

    fig, axes = plt.subplots(1, 2, figsize=(9, 3), sharex=True, sharey=True)
    ax = axes.ravel()

    image = np.amax(image_data, axis=0)

    for idx, (blobs, color, title) in enumerate(sequence):
        ax[idx].set_title(title)
        ax[idx].imshow(image)
        for blob in blobs:
            z, y, x, r = blob
            c = plt.Circle((x, y), r, color=color, linewidth=2, fill=False)
            ax[idx].add_patch(c)
            print("FWHM of Particle:", r)
        ax[idx].set_axis_off()

    plt.tight_layout()
    plt.show()

if (__name__ == "__main__"):
    from tifffile import imread

    # # Define Inputs
    # scales = [1, 2, 4]
    # nSTDsurface = 2
    # insideGamma = 0.7
    # insideBlur = 1
    # insideDilateRadius = 3
    # insideErodeRadius = 4
    #
    # image_directory = '/archive/MIL/morrison/20201105_mitochondria_quantification/ilastik'
    # image_name = 'ControlCell8_cyto.tif'
    # image_path = os.path.join(image_directory, image_name)
    # image_data = np.array(imread(image_path))
    # print('The Image Dimensions Are: ' + str(image_data.shape))
    #

    image_directory = '/Users/S155475/Downloads/1_CH00_000000-1.tif'
    image_data = np.array(imread(image_directory))
    log_detection(image_data, image_threshold=None, pixel_size=0.206)

