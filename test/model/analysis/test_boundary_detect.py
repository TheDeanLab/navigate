# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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

import math

import numpy as np


def im_circ(r=1, N=128):
    X, Y = np.meshgrid(range(-N // 2, N // 2), range(-N // 2, N // 2))
    return (X * X + Y * Y) < r * r


def test_has_tissue():
    from navigate.model.analysis.boundary_detect import has_tissue

    for _ in range(100):
        N = 2 ** np.random.randint(5, 9)
        r = np.random.randint(math.ceil(0.2 * N), int(0.4 * N))
        ds = np.random.randint(1, 6)

        print(N, r, ds)

        im = im_circ(r, N) * 1001

        mu, sig = 100 * np.random.rand() + 1, 10 * np.random.rand() + 1
        print(mu, sig)
        offsets = [None, np.ones((N, N)) * mu]
        variances = [None, np.ones((N, N)) * sig]

        for off, var in zip(offsets, variances):
            assert has_tissue(im, 0, 0, N, off, var) and not has_tissue(
                im, 0, 0, N // 2 - r, off, var
            )


def test_find_tissue_boundary_2d():
    from skimage.transform import downscale_local_mean

    from navigate.model.analysis.boundary_detect import find_tissue_boundary_2d

    for _ in range(100):
        N = 2 ** np.random.randint(5, 9)
        r = np.random.randint(1, int(0.4 * N))
        ds = np.random.randint(1, 6)

        print(N, r, ds)

        im = im_circ(r, N)
        b = find_tissue_boundary_2d(im, ds)
        b = np.vstack([x for x in b if x is not None])

        idx_x, idx_y = np.where(downscale_local_mean(im, (ds, ds)))
        iixy = (np.unique(idx_x)[:, None] == idx_x[None, :]) * idx_y
        low, high = idx_y[np.argmax(iixy != 0, 1)], np.max(iixy, 1)

        np.testing.assert_equal(b, np.vstack([low, high]).T)


def test_binary_detect():
    from navigate.model.analysis.boundary_detect import (
        find_tissue_boundary_2d,
        binary_detect,
    )

    for _ in range(100):
        N = 2 ** np.random.randint(5, 9)
        r = np.random.randint(1, int(0.4 * N))
        ds = np.random.randint(1, 6)

        print(N, r, ds)

        im = im_circ(r, N)
        b = find_tissue_boundary_2d(im, ds)

        assert binary_detect(im * 1001, b, ds) == b


def test_map_boundary():
    from navigate.model.analysis.boundary_detect import map_boundary

    assert map_boundary([[1, 2]]) == [(0, 1), (0, 2)]
    assert map_boundary([None, [1, 2]]) == [(1, 1), (1, 2)]
    assert map_boundary([None, [1, 2], None]) == [(1, 1), (1, 2)]


def test_map_labels():

    def generate_labeled_stack_with_3d_blobs(
        depth=50,
        height=1024,
        width=1024,
        num_labels=30,
        blob_size=5,
    ):
        stack = np.zeros((depth, height, width), dtype=np.uint16)
        rng = np.random.default_rng()

        r = blob_size // 2  # radius for spherical blob

        for label in range(1, num_labels + 1):
            # Choose center location, ensuring the blob stays inside boundaries
            cz = rng.integers(r, depth - r)
            cy = rng.integers(r, height - r)
            cx = rng.integers(r, width - r)

            # Fill a cube: 5x5x5
            stack[
                cz - r : cz + r + 1,
                cy - r : cy + r + 1,
                cx - r : cx + r + 1
            ] = label

        return stack
    
    from navigate.model.analysis.boundary_detect import map_labels

    labeled_image = generate_labeled_stack_with_3d_blobs()

    z_range, position_table, target_labels = map_labels(
        labeled_image,
        position = [0, 0, 0, 0, 0],
        z_start = -100,
        z_step = 1,
        x_direction = "x",
        y_direction = "y",
        current_pixel_size = 1,
        current_image_width = 1024,
        current_image_height = 1024,
        target_pixel_size = 0.05,
        target_image_width = 1024,
        target_image_height = 1024,
        overlap=0.05,
        filter_pixel_number=1,
    )

    assert z_range == 5 # blob size in z direction

    assert position_table[0] == ["X", "Y", "Z", "THETA", "F"]

