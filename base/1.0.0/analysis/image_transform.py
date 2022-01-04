'''
Image transforms
'''

import numpy as np

def deskew_image(image_data, shear_angle, z_pixel_size, xy_pixel_size):
    '''
    #  This function is designed to deskew an image.
    # return uint16 data to save as tiff
    '''
    (z_len, y_len, x_len) = image_data.shape
    scaled_shear_angle = np.cos(shear_angle * np.pi / 180) * z_pixel_size / xy_pixel_size
    scale_factor = np.uint16(np.ceil(z_len * np.cos(shear_angle * np.pi / 180) * z_pixel_size / xy_pixel_size))

    #  Create blank image to store the deskewed image.
    scaled_array = np.zeros((z_len, y_len, x_len + scale_factor))
    output_array = np.zeros((z_len, y_len, x_len + scale_factor))

    # Populate the scaled array with the original data
    scaled_array[:z_len, :y_len, :x_len] = image_data

    xF, yF = np.meshgrid(np.arange(x_len + scale_factor), np.arange(y_len))
    for k in range(z_len):
        image_slice = scaled_array[k, :, :]
        image_slice_fft = np.fft.fftshift(np.fft.fft2(image_slice))
        image_slice_fft_trans = image_slice_fft * np.exp(-1j * 2 * np.pi * xF * scaled_shear_angle * k / (x_len + scale_factor))
        output_array[k, :, :] = np.abs(np.fft.ifft2(np.fft.ifftshift(image_slice_fft_trans)))

    output_array[output_array < 0] = 0
    return np.uint16(output_array)

if (__name__ == "__main__"):
    ''' 
    Testing section
    '''

    from tifffile import imread, imsave
    data_path = 'path/to/data.tif'
    data = imread(data_path)
    shear_angle = 30
    z_pixel_size = 0.5
    xy_pixel_size = 0.2
    output_data = deskew_image(data, shear_angle, z_pixel_size, xy_pixel_size)
    imsave('path/to/output.tif', output_data)