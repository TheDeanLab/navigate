# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

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
#

# Standard Library Imports
import logging

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ZoomBase:
    """ "ZoomBase parent class.

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocesing.managers.DictProxy
        Global configuration of the microscope
    """

    def __init__(self, microscope_name, device_controller, configuration):
        self.zoomdict = configuration["configuration"]["microscopes"][microscope_name][
            "zoom"
        ]["position"]
        self.zoomvalue = None

    def set_zoom(self, zoom, wait_until_done=False):
        """ "Change the Zoom Servo.

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
            raise ValueError("Zoom designation not in the configuration")
        logger.debug(f"Changed Zoom to {zoom}")
        logger.debug(f"Zoom position: {self.read_position()}")

    def move(self, position=0, wait_until_done=False):
        """ "Move the Zoom Servo

        Parameters
        ----------
        position : int
            Location to move to.
        wait_until_done : bool
            Delay parameter
        """
        logger.debug(f"Changing Zoom to {position}")
        pass

    def read_position(self):
        """ "Read the position of the Zoom Servo

        Returns
        -------
        cur_position : int
            Current position of Zoom
        """
        cur_position = None
        logger.debug(f"Zoom position: {cur_position}")
        return cur_position
