import cv2
from tifffile import imread
import numpy as np

def yee_haw():
    image_path = r"/Users/S155475/Desktop/test_image.tif"
    image = imread(image_path)


    # Resize Data
    psf_support_diameter = 3
    image = cv2.resize(image, (int(np.shape(image)[0] / psf_support_diameter),
                               int(np.shape(image)[1] / psf_support_diameter)))

    # L1 Norm
    l1_norm = np.linalg.norm(image,
                             ord=1)

    # Normalize Image by L1 Norm
    image = np.divide(image,
                      l1_norm)

    I1 = np.zeros_like(image)
    I2 = np.zeros_like(image)
    I1[0:-1, :] = image[1:, :]
    I2[0:-2, :] = image[2:, :]
    right = np.multiply(image, np.subtract(I1, I2))

    I1 = np.zeros_like(image)
    I2 = np.zeros_like(image)
    I1[1:, :] = image[0:-1, :]
    I2[2:, :] = image[0:-2, :]
    left = np.multiply(image, np.subtract(I1, I2))

    I1 = np.zeros_like(image)
    I2 = np.zeros_like(image)
    I1[:, 1:] = image[:, 0:-1]
    I2[:, 2:] = image[:, 0:-2]
    up = np.multiply(image, np.subtract(I1, I2))

    I1 = np.zeros_like(image)
    I2 = np.zeros_like(image)
    I1[:, 0:-1] = image[:, 1:]
    I2[:, 0:-2] = image[:, 2:]
    down = np.multiply(image, np.subtract(I1, I2))

    focus_metric = np.mean(np.abs(np.sum(right)) + np.abs(np.sum(left)) + np.abs(np.sum(up)) + np.abs(np.sum(down)))

    print(focus_metric)

"""
        Image = double(Image);
        I1 = Image; I1(1:end-1,:) = Image(2:end,:);
        I2 = Image; I2(1:end-2,:) = Image(3:end,:);
        Image = Image.*(I1-I2);
        FM = mean2(Image);
        """


if __name__ == "__main__":
    yee_haw()