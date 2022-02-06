"""
Synthetic Zoom Device
Adopted from mesoSPIM
"""
# Local Imports
from model.devices.zoom.ZoomBase import ZoomBase


class Zoom(ZoomBase):
    def __init__(self, model, verbose):
        super().__init__(model, verbose)
        if self.verbose:
            print('Synthetic Zoom Initialized')

    def set_zoom(self, zoom, wait_until_done=False):
        """
        # Changes zoom after checking that the commanded value exists
        """
        if zoom in self.zoomdict:
            self.zoomvalue = zoom
        else:
            raise ValueError('Zoom designation not in the configuration')
        if self.verbose:
            print('Zoom set to {}'.format(zoom))

    def move(self, position=0, wait_until_done=False):
        print("move for Zoom servo not implemented")

    def read_position(self):
        """
        # Returns position as an int between 0 and 4096
        # Opens & closes the port
        """
        print("read_position(self) not implemented for Zoom servo")
