# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import cv2
from tifffile import imread
import numpy as np


def yee_haw():
    image_path = r"/Users/S155475/Desktop/test_image.tif"
    image = imread(image_path)

    # Resize Data
    psf_support_diameter = 3
    image = cv2.resize(
        image,
        (
            int(np.shape(image)[0] / psf_support_diameter),
            int(np.shape(image)[1] / psf_support_diameter),
        ),
    )

    # L1 Norm
    l1_norm = np.linalg.norm(image, ord=1)

    # Normalize Image by L1 Norm
    image = np.divide(image, l1_norm)

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

    focus_metric = np.mean(
        np.abs(np.sum(right))
        + np.abs(np.sum(left))
        + np.abs(np.sum(up))
        + np.abs(np.sum(down))
    )

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
