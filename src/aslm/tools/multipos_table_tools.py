"""
This holds functions commonly used to interact with the Multiposition Pandas Table in the GUI

"""

import numpy as np
import itertools
import pandas as pd
# TODO should we just import the Multiposition table here and only access via the tools module?


def compute_tiles_from_bounding_box(x_start, x_stop, x_tiles, y_start, y_stop, y_tiles, z_start, z_stop, z_tiles,
                                    r_start=0, r_stop=0, r_tiles=1, f_start=0, f_stop=0, f_tiles=1):
    """
    Creates a multiposition grid based on the start position, stop position, and number of tiles
    of each dimension.

    Focus currently tracks with z, since focus is z-dependent. TODO: Change this behavior? Make it a flag?

    Parameters
    ----------
    x_start, x_stop: float
        Start and end of X position
    x_tiles: int
        Num of tiles for X dimension (cannot be 0)
    y_start, y_stop: float
        Start and end of Y position
    y_tiles: int
        Num of tiles for Y dimension (cannot be 0)
    z_start, z_stop: float
        Start and end of Z position
    z_tiles: int
        Num of tiles for Z dimension (cannot be 0)
    r_start, r_stop: float, default 0
        Start and end of R (theta) position
    r_tiles: int, default 0
        Num of tiles for R (theta) dimension
    f_start, f_stop: float, default 0
        Start and end of F position
    f_tiles: int, default 0
        Num of tiles for F dimension

    Returns
    -------
    table_of_values: list
        Each element in the list is a row in the multiposition table (x, y, z)
    """
    
    # Error checking to prevent empty list when tiles are zero
    x_tiles = 1 if x_tiles <= 0 else x_tiles
    y_tiles = 1 if y_tiles <= 0 else y_tiles
    z_tiles = 1 if z_tiles <= 0 else z_tiles
    r_tiles = 1 if r_tiles <= 0 else r_tiles
    f_tiles = 1 if f_tiles <= 0 else f_tiles

    xs = np.linspace(x_start, x_stop, x_tiles)
    ys = np.linspace(y_start, y_stop, y_tiles)
    zs = np.linspace(z_start, z_stop, z_tiles)
    rs = np.linspace(r_start, r_stop, r_tiles)
    fs = np.linspace(f_start, f_stop, z_tiles)  # currently tracks with zs
    table_of_values = list(itertools.product(xs, ys, zip(zs, fs), rs))  # zip to force zs and fs to match

    # Unravel the zip
    # TODO: This is slow as heck and effectively undoes all of the speed benefits of np and itertools. Find
    #       a better way to do this.
    for i in range(len(table_of_values)):
        table_of_values[i] = (table_of_values[i][0],
                              table_of_values[i][1],
                              table_of_values[i][2][0],
                              table_of_values[i][3],
                              table_of_values[i][2][1])

    return table_of_values


def update_table(table, pos_list):
    """
    Updates and redraws table based on given list. List is converted to a pandas dataframe before setting data in table.
    
    Parameters
    ----------
    table: Multi_Position_Table object
        Instance of multiposition table in GUI
    pos_list: list
        List of positions to be added to table
    
        
    Returns
    -------
    None : 
        Table is updated
    """
    table.model.df = pd.DataFrame(pos_list, columns=list('XYZRF'))
    table.currentrow = table.model.df.shape[0]-1
    table.update_rowcolors()
    table.redraw()
    table.tableChanged()

