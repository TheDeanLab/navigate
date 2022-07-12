'''
This holds functions commonly used to interact with the Multiposition Pandas Table in the GUI

'''

import numpy as np
import itertools
import pandas as pd
# TODO should we just import the Multiposition table here and only access via the tools module?

def compute_grid(x_start, x_stop, x_tiles, y_start, y_stop, y_tiles, z_start, z_stop, z_tiles):
    '''
    Creates a multiposition grid based on the start position, stop position, and number of tiles
    of each dimension. 

    Parameters
    ----------
    x_start, x_stop: float
        Start and end of X position
    x_tiles: int
        Num of tiles for X dimension (can not be 0)
    y_start, y_stop: float
        Start and end of Y position
    y_tiles: int
        Num of tiles for Y dimension (can not be 0)
    z_start, z_stop: float
        Start and end of Z position
    z_tiles: int
        Num of tiles for Z dimension (can not be 0)
        

    Returns
    -------
    table_of_values: list
        Each element in the list is a row in the multiposition table (x, y, z)
    '''
    
    # Error checking to prevent empty list when tiles are zero
    for tiles in [x_tiles, y_tiles, z_tiles]:
        if tiles <= 0:
            tiles = 1

    xs = np.linspace(x_start, x_stop, x_tiles)
    ys = np.linspace(y_start, y_stop, y_tiles)
    zs = np.linspace(z_start, z_stop, z_tiles)
    rs = np.linspace(0,0,1)
    fs = np.linspace(0,0,1)
    table_of_values = list(itertools.product(xs, ys, zs, rs, fs))


    return table_of_values

def update_table(table, list):
    '''
    Updates and redraws table based on given list. List is converted to a pandas dataframe before setting data in table.
    
    Parameters
    ----------
    table: Multi_Position_Table object
        Instance of multiposition table in GUI
    list: list
        List of positions to be added to table
    
        
    Returns
    -------
    None : 
        Table is updated
    '''
    table.model.df = pd.DataFrame([list], columns=list('XYZRF'))
    table.currentrow = table.model.df.shape[0]-1
    table.update_rowcolors()
    table.redraw()
    table.tableChanged()
