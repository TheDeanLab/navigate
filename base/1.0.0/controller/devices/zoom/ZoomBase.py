"""
Base Module for controlling a discrete zoom changer

Adopted from mesoSPIM

"""

import time

class ZoomBase():
    def __init__(self, session, verbose):
        self.zoomdict = session.ZoomParameters['zoom_position']

    def set_zoom(self, zoom_position, wait_until_done=False):
        if zoom_position in self.zoomdict:
            if verbose:
                print('Setting zoom to {}'.format(zoom_position))
            if wait_until_done:
                time.sleep(1)

    def move(selfself, position, wait_until_done=False):
        return True

    def read_position(self):
        return True

if (__name__ == "__main__"):
    print("Testing Section - ZoomBase Class")