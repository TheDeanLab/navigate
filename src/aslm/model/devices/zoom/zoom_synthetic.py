"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

# Standard Library Imports
import logging

# Third Party Imports

# Local Imports
from aslm.model.devices.zoom.zoom_base import ZoomBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class SyntheticZoom(ZoomBase):
    """SyntheticZoom Class

    Controls the SyntheticZoom Servo.

    Methods
    -------
    set_zoom(zoom, wait_until_done)
        Change the DynamixelZoom position to zoom value of the microscope.
    move(position, wait_until_done)
        Move the DynamixelZoom position.
    read_position()
        Read the position of the DynamixelZoom servo.
    """

    def __init__(self, configuration, verbose):
        super().__init__(configuration, verbose)
        logger.debug("SyntheticZoom Servo Initialized")

    def __del__(self):
        logger.debug("SyntheticZoom Servo instance Deleted")
        pass

    def set_zoom(self, zoom, wait_until_done=False):
        r"""Change the SyntheticZoom Servo.

        Confirms tha the zoom position is available in the zoomdict

        Parameters
        ----------
        zoom : dict
            Zoom dictionary
        wait_until_done : bool
            Delay parameter.

        # Changes zoom after checking that the commanded value exists
        """
        if zoom in self.zoomdict:
            self.zoomvalue = zoom
        else:
            logger.error(f"Zoom designation, {zoom}, not in the configuration")
            raise ValueError('Zoom designation not in the configuration')
        logger.debug(f"Changed SyntheticZoom to {zoom}")
        logger.debug(f"SyntheticZoom position: {self.read_position()}")

    def move(self, position=0, wait_until_done=False):
        r""" Move the SyntheticZoom Servo

        Parameters
        ----------
        position : int
            Location to move to.
        wait_until_done : bool
            Delay parameter
        """
        logger.debug(f"Changing SyntheticZoom to {zoom}")
        pass

    def read_position(self):
        r"""Read the position of the Zoom Servo

        Returns
        -------
        cur_position : int
            Current position of SyntheticZoom
        """
        cur_position = None
        logger.debug(f"SyntheticZoom position: {cur_position}")
        return cur_position
