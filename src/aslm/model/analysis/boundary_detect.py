# Copyright (c) 2021-2023  The University of Texas Southwestern Medical Center.
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
from typing import Optional

from skimage import filters
from skimage.transform import downscale_local_mean
import numpy as np
import numpy.typing as npt

# from aslm.model.analysis.camera import compute_signal_to_noise


def has_tissue(
    image_data: npt.ArrayLike,
    x: int,
    y: int,
    width: int,
    offset: Optional[npt.ArrayLike] = None,
    variance: Optional[npt.ArrayLike] = None,
) -> bool:
    """
    Determine if an image contains tissue.

    Parameters
    ----------
    image_data : npt.ArrayLike
        Image
    x : int
        Starting x-position of subimage. Must be smaller than image_data.shape[0].
    y : int
        Starting y-position of subimage. Must be smaller than image_data.shape[1].
    width : int
        Width of subimage. Must be smaller than min(image_data.shape[:1])
    offset : npt.ArrayLike
        Camera pixel offset map. Same size as image_data.
    variance : npt.ArrayLike
        Camera pixel variance map. Same size as image_data.

    Returns
    -------
    bool
        Is tissue present?
    """
    # TODO: threshold value, other is_tissue() method
    xsl = slice(x * width, (x + 1) * width)
    ysl = slice(y * width, (y + 1) * width)

    # Decide tissue is present by hard SNR threshold
    # if offset is not None and variance is not None:
    #     threshold_value = 2  # snr threshold
    #     snr = compute_signal_to_noise(
    #         image_data[xsl, ysl], offset[xsl, ysl], variance[xsl, ysl]
    #     )
    #     return (
    #         np.sum(snr > threshold_value) / np.prod(snr.shape) > 0.0625
    #     )  # at least 6.25% of pixels have to be above this value

    # Decide tissue is present by hard pixel count threshold
    # threshold_value = 1000
    return np.any(image_data[xsl, ysl] > np.mean(image_data))


def find_tissue_boundary_2d(
    image_data: npt.ArrayLike, mag_ratio: Optional[float] = 1.0
) -> list:
    """
    Find all pixels containing tissue, based on an Otsu threshold. Optionally,
    return pixels in image space resampled by mag_ratio.

    Parameters
    ----------
    image_data : npt.ArrayLike
        Image
    mag_ratio : float
        Ratio between pixel sizes of current over target tiles.

    Returns
    -------
    boundary : list
        List of boundaries of tissue by row of downsampled image.
    """

    # Threshold
    thresh_img = image_data > filters.threshold_otsu(image_data)

    if mag_ratio > 1:
        ds_img = downscale_local_mean(thresh_img, (mag_ratio, mag_ratio))
    else:
        ds_img = image_data
        mag_ratio = 1

    idx_x, idx_y = np.where(ds_img)

    # Assume square image
    m = math.ceil(image_data.shape[0] / mag_ratio)
    # n = math.ceil(image_data.shape[1] / mag_ratio)
    boundary = [None] * m
    for x, y in zip(idx_x, idx_y):
        if boundary[x] is None:
            boundary[x] = [y, y]
        else:
            boundary[x][1] = y
    return boundary


def binary_detect(
    img_data: npt.ArrayLike,
    boundary: list,
    width: int = 1,
    offset: Optional[npt.ArrayLike] = None,
    variance: Optional[npt.ArrayLike] = None,
):
    """
    Perform a binary search for tissue on an image. Return locations of pixels
    containing tissue.


    Parameters
    ----------
    image_data : npt.ArrayLike
        Image
    boundary : dict
        List of xy pixel positions indicating presence of tissue as values.
    width : int
        Width of subimage. Must be smaller than min(image_data.shape[:1])
    offset : npt.ArrayLike
        Camera pixel offset map. Same size as image_data.
    variance : npt.ArrayLike
        Camera pixel variance map. Same size as image_data.

    Returns
    -------
    boundary : list
        List of boundaries of tissue by row of downsampled image.

    """
    m, n = img_data.shape
    m = int(m / width)
    n = int(n / width)

    def binary_search_func_left(row, left, right):
        """Binary search function.

        Parameters
        ----------
        row : int
            Row of image.
        left : int
            Left boundary of subimage.
        right : int
            Right boundary of subimage.

        Returns
        -------
        int
            Left boundary of subimage.
        """
        while left < right:
            mid = (left + right) // 2
            if has_tissue(img_data, row, mid, width, offset, variance):
                right = mid
            else:
                left = mid + 1
        return right

    def binary_search_func_right(row, left, right):
        """Binary search function.

        Parameters
        ----------
        row : int
            Row of image.
        left : int
            Left boundary of subimage.
        right : int
            Right boundary of subimage.

        Returns
        -------
        int
            Right boundary of subimage.
        """
        while left < right:
            mid = (left + right) // 2
            if has_tissue(img_data, row, mid, width, offset, variance):
                left = mid + 1
            else:
                right = mid
        return right - 1

    def find_tissue_range(row, left, right):
        """Find range of tissue.

        Parameters
        ----------
        row : int
            Row of image.
        left : int
            Left boundary of subimage.
        right : int
            Right boundary of subimage.

        Returns
        -------
        int
            Left boundary of subimage.
        int
            Middle boundary of subimage.
        int
            Right boundary of subimage.
        """
        temp = [(left, right)]
        while temp:
            temp2 = []
            for ll, r in temp:
                mid = (ll + r) // 2
                if has_tissue(img_data, row, mid, width, offset, variance):
                    return ll, mid, r
                if mid > ll + 1:
                    temp2.append((ll, mid))
                if r > mid + 1:
                    temp2.append((mid, r))
            temp = temp2
        return -1, -1, -1

    def detect_row_boundary(row_id, left, right):
        """Detect row boundary.

        Parameters
        ----------
        row_id : int
            Row of image.
        left : int
            Left boundary of subimage.
        right : int
            Right boundary of subimage.

        Returns
        -------
        int
            Left boundary of subimage.
        int
            Right boundary of subimage.
        """
        is_tissue_left = has_tissue(img_data, row_id, left, width, offset, variance)
        is_tissue_right = has_tissue(img_data, row_id, right, width, offset, variance)

        if is_tissue_left and is_tissue_right:
            left_l, left_r = 0, left
            right_l, right_r = right, n
        elif is_tissue_left:
            left_l, left_r = 0, left
            right_l, right_r = left, right
        elif is_tissue_right:
            left_l, left_r = left, right
            right_l, right_r = right, n
        else:
            ll, mid, r = find_tissue_range(row_id, left, right)
            left_l, left_r = ll, mid
            right_l, right_r = mid, r

        if left_l == -1:
            return None, None
        return binary_search_func_left(
            row_id, left_l, left_r
        ), binary_search_func_right(row_id, right_l, right_r)

    def expand_row(row_id, limits, direction, boundary):
        """Expand row.

        Parameters
        ----------
        row_id : int
            Row of image.
        limits : int
            Limits of row.
        direction : int
            Direction of expansion.
        boundary : dict
            List of xy pixel positions indicating presence of tissue as values.

        Returns
        -------
        dict
            List of xy pixel positions indicating presence of tissue as values.
        """
        for i in range(row_id, limits, direction):
            left, right = boundary[i][0], boundary[i][1]
            left = left - 1 if left > 0 else 0
            right = right + 1 if (right + 1) < (n - 1) else (n - 1)
            ll, r = detect_row_boundary(i + direction, left, right)
            if ll is None:
                boundary[i + direction] = None
                break
            boundary[i + direction] = [ll, r]

    new_boundary = boundary[:]
    top, bottom = None, None
    expand_top, expand_bottom = True, True

    for i, row in enumerate(new_boundary):
        if row is None:
            continue
        if expand_bottom is False:
            new_boundary[i] = None
            continue
        if len(row) < 2:
            row.append(row[0])
        left, right = detect_row_boundary(i, row[0], row[1])
        if left is None:
            new_boundary[i] = None
            if top is None:
                expand_top = False
            if bottom is not None:
                expand_bottom = False
        else:
            new_boundary[i] = [left, right]

        if top is None:
            top = i
        bottom = i

    # detect top/bottom if necessary
    if expand_top:
        expand_row(top, 0, -1, new_boundary)

    if expand_bottom:
        expand_row(bottom, n - 1, 1, new_boundary)

    return new_boundary


def map_boundary(boundary, direction=True):
    """Map boundary to path

    Parameters
    ----------
    boundary : list
        List of xy pixel positions indicating presence of tissue as values.
    direction : bool
        Direction of path

    Returns
    -------
    list
        List of xy pixel positions indicating presence of tissue as values.
    """
    if direction:
        start, end, step = 0, len(boundary), 1
        offset = -1
    else:
        start, end, step = len(boundary) - 1, -1, -1
        offset = 1

    def dp_shortest_path(start, end, step, offset=-1):
        """Dynamic programming shortest path

        Parameters
        ----------
        start : int
            Start index.
        end : int
            End index.
        step : int
            Step size.
        offset : int
            Offset.

        Returns
        -------
        list
            List of xy pixel positions indicating presence of tissue as values.
        """

        dp_path = []
        dp_cost = [0, 0]
        visited = False
        for i in range(start, end, step):
            if boundary[i] is None:
                if visited:
                    break
                continue
            w = boundary[i][1] - boundary[i][0] + 1
            if not visited:
                visited = True
                dp_cost[0], dp_cost[1] = w, w
                dp_path.append([i, -1, -1])
            else:
                dp_path.append([i, 0, 0])
                for j in range(2):
                    ll = abs(boundary[i + offset][0] - boundary[i][j])
                    r = abs(boundary[i + offset][1] - boundary[i][j])
                    if ll < r:
                        dp_cost[1 - j] += w + ll
                        dp_path[-1][2 - j] = 0
                    else:
                        dp_cost[1 - j] += w + r
                        dp_path[-1][2 - j] = 1

        # reverse path
        if dp_cost[0] < dp_cost[1]:
            idx = 0
        else:
            idx = 1
        path = []
        for item in reversed(dp_path):
            x = item[0]
            if idx == 0:
                path += map(lambda y: (x, y), range(boundary[x][0], boundary[x][1] + 1))
            else:
                path += map(
                    lambda y: (x, y), range(boundary[x][1], boundary[x][0] - 1, -1)
                )
            idx = item[idx + 1]
        path.reverse()
        return path

    result = dp_shortest_path(start, end, step, offset)
    return result
