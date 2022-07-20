"""
This holds functions commonly used to interact with the Multiposition Pandas Table in the GUI

"""

import numpy as np
import itertools
import pandas as pd
from math import ceil


def sign(x):
    return -1 if x < 0 else 1  # (1 if x > 0 else 0)


def compute_tiles_from_bounding_box(x_start, x_tiles, x_length, x_overlap,
                                    y_start, y_tiles, y_length, y_overlap,
                                    z_start, z_tiles, z_length, z_overlap,
                                    theta_start, theta_tiles, theta_length, theta_overlap,
                                    f_start, f_tiles, f_length, f_overlap):
    r"""Create a grid of ROIs to image based on start position, number of tiles, and signed FOV length in each dimension.

    Focus currently tracks with z, since focus is z-dependent. TODO: Change this behavior? Make it a flag?

    Parameters
    ----------
    x_start : float
        Starting position along x-dimension.
    x_tiles : int
        Number of tiles to take along x-dimension.
    x_length : float
        Signed length of the FOV along x-dimension.
    x_overlap : float
        Fractional overlap of ROIs along x-dimension.
    y_start : float
        Starting position along y-dimension.
    y_tiles : int
        Number of tiles to take along y-dimension.
    y_length : float
        Signed length of the FOV along y-dimension.
    y_overlap : float
        Fractional overlap of ROIs along y-dimension.
    z_start : float
        Starting position along z-dimension.
    z_tiles : int
        Number of tiles to take along z-dimension.
    z_length : float
        Signed length of the FOV along z-dimension.
    z_overlap : float
        Fractional overlap of ROIs along z-dimension.
    theta_start : float
        Starting position along rotation dimension.
    theta_tiles : int
        Number of tiles to take along rotation dimension.
    theta_length : float
        Signed length of the FOV along rotation dimension.
    theta_overlap : float
        Fractional overlap of ROIs along rotation dimension.
    f_start : float
        Starting position along focus dimension.
    f_tiles : int
        Number of tiles to take along focus dimension.
    f_length : float
        Signed length of the FOV along focus dimension.
    f_overlap : float
        Fractional overlap of ROIs along focus dimension.

    Returns
    -------
    np.array
        (n_positions x (x, y, z, theta, f)) array of positions, gridding out the space
    """

    # Error checking to prevent empty list when tiles are zero
    x_tiles = 1 if x_tiles <= 0 else x_tiles
    y_tiles = 1 if y_tiles <= 0 else y_tiles
    z_tiles = 1 if z_tiles <= 0 else z_tiles
    theta_tiles = 1 if theta_tiles <= 0 else theta_tiles
    f_tiles = 1 if f_tiles <= 0 else f_tiles

    # Calculate the step between the edge of each frame
    x_step = x_length*(1 - x_overlap)
    y_step = y_length*(1 - y_overlap)
    z_step = z_length*(1 - z_overlap)
    theta_step = theta_length * (1 - theta_overlap)
    f_step = f_length * (1 - f_overlap)              # Although we assume focus FOVs have no thickness, we include
                                                     # overlap to adjust for z-ramping. We have no excuse for the
                                                     # theta overlap.

    # grid out each dimension starting from (x_start, y_start, z_start) in steps
    def dim_vector(start, n_tiles, step):
        return start + np.arange(0, n_tiles, 1) * step

    xs = dim_vector(x_start, x_tiles, x_step)                  # x-coordinate is centered on FOV
    ys = dim_vector(y_start, y_tiles, y_step)                  # y-coordinate is centered on FOV
    zs = dim_vector(z_start, z_tiles, z_step)                  # z-coordinate is centered on local z-stack origin
    thetas = dim_vector(theta_start, theta_tiles, theta_step)  # we assume theta FOVs have no thickness
    fs = dim_vector(f_start, f_tiles, f_step)                  # we assume focus FOVs have no thickness

    # grid out the 4D space...
    x, y, z, t = np.meshgrid(xs, ys, zs, thetas)

    # we need to make f vary the same as z, for now, since focus changes with z
    f = np.repeat(fs, int(len(t.ravel())/len(fs)))  # This only works if len(fs) = len(zs)

    return np.vstack([x.ravel(), y.ravel(), z.ravel(), t.ravel(), f]).T


def calc_num_tiles(dist, overlap, roi_length):
    r"""Calculate the number of tiles to divide a space dist along a single axis with an ROI of size roi_length
    and a fractional overlap between ROIs of overlap.

    Watch out! This has no indication of what the tiles should actually look like (no information about sign, etc.).

    Parameters
    ----------
    dist : float
        Total distance to tile with ROIs. A measure from the closed boundaries of the region to tile (e.g. left side
        of the first tile all the way to the right side of the last tile for x-dimension low -> high). Positive.
    overlap : float
        Fraction of roi_length that overlaps in each tile. Value between 0 and 1.
    roi_length : float
        The length of the ROI along this dimension. Positive.

    Returns
    -------
    num_tiles : int
        Number of tiles needed to cover this distance.

    """
    if dist == 0 or roi_length <= 0 or overlap >= 1:
        num_tiles = 1
    else:
        ov = overlap * roi_length  # True overlap in distance units
        num_tiles = ceil(abs(dist - ov) / abs(roi_length - ov))

    return int(num_tiles)


def update_table(table, pos, append=False):
    """
    Updates and redraws table based on given list. List is converted to a pandas dataframe before setting data in table.
    
    Parameters
    ----------
    table: Multi_Position_Table object
        Instance of multiposition table in GUI
    pos: list or np.array
        List or np.array of positions to be added to table. Each row contains an X, Y, Z, R, F position
    append: bool
        Append the new positions to the table
        
    Returns
    -------
    None : 
        Table is updated
    """
    frame = pd.DataFrame(pos, columns=list('XYZRF'))
    if append:
        table.model.df.append(frame, ignore_index=True)
    else:
        table.model.df = frame
    table.currentrow = table.model.df.shape[0]-1
    table.update_rowcolors()
    table.redraw()
    table.tableChanged()

