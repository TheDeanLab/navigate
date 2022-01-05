"""
Synthetic Zoom Device
Adopted from mesoSPIM
"""
# Local Imports
from model.zoom.ZoomBase import ZoomBase

class Zoom(ZoomBase):
    def __init__(self, model, verbose):
        self.verbose = verbose
        self.model = model

    def set_zoom(self, zoom, wait_until_done=False):
        """
        Changes zoom after checking that the commanded value exists
        """
        print("set_zoom for Zoom servo not implemented")

    def move(self, position=0, wait_until_done=False):
        print("move for Zoom servo not implemented")

    def read_position(self):
        '''
        Returns position as an int between 0 and 4096
        Opens & closes the port
        '''
        print("read_position(self) not implemented for Zoom servo")

