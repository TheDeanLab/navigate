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

    Assumes (x_start, y_start, z_start) correspond to origin of grid space.

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

    # Error checking to prevent empty list when tiles are zero (or 1, due to np.arange)
    x_tiles = 2 if x_tiles <= 1 else x_tiles
    y_tiles = 2 if y_tiles <= 1 else y_tiles
    z_tiles = 2 if z_tiles <= 1 else z_tiles
    theta_tiles = 2 if theta_tiles <= 1 else theta_tiles
    f_tiles = 2 if f_tiles <= 1 else f_tiles

    x_step = x_length*(1 - sign(x_length)*x_overlap)
    y_step = y_length*(1 - sign(y_length)*y_overlap)
    z_step = z_length*(1 - sign(z_length)*z_overlap)
    theta_step = theta_length*(1 - sign(theta_length)*theta_overlap)
    f_step = f_length * (1 - sign(f_length) * f_overlap)

    def dim_vector(start, n_tiles, step):
        return start + np.arange(0, n_tiles, 1) * step
        # return np.arange(start, start + n_tiles * step, step)

    xs = dim_vector(x_start, x_tiles, x_step)
    ys = dim_vector(y_start, y_tiles, y_step)
    zs = dim_vector(z_start, z_tiles, z_step)
    thetas = dim_vector(theta_start, theta_tiles, theta_step)
    fs = dim_vector(f_start, f_tiles, f_step)

    # grid out the 4D space...
    x, y, z, t = np.meshgrid(xs, ys, zs, thetas)

    # we need to make f vary the same as z, for now, since focus changes with z
    f = np.repeat(fs, int(len(t.ravel())/len(fs)))

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
    if roi_length <= 0 or overlap >= 1 or dist < roi_length:
        num_tiles = 1
    else:
        ov = overlap * roi_length  # True overlap in distance units
        num_tiles = ceil((dist - ov) / (roi_length - ov))

    return int(num_tiles)


def update_table(table, pos):
    """
    Updates and redraws table based on given list. List is converted to a pandas dataframe before setting data in table.
    
    Parameters
    ----------
    table: Multi_Position_Table object
        Instance of multiposition table in GUI
    pos: list or np.array
        List or np.array of positions to be added to table. Each row contains an X, Y, Z, R, F position
        
    Returns
    -------
    None : 
        Table is updated
    """
    table.model.df = pd.DataFrame(pos, columns=list('XYZRF'))
    table.currentrow = table.model.df.shape[0]-1
    table.update_rowcolors()
    table.redraw()
    table.tableChanged()

