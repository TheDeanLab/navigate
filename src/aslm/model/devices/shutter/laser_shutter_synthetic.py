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
from aslm.model.devices.shutter.laser_shutter_base import ShutterBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class SyntheticShutter(ShutterBase):
    """SyntheticShutter Class

    Triggering for shutters delivered from synthetically.

    Attributes
    ----------
    configuration : Session
        Global configuration of the microscope
    experiment : Session
        Experiment configuration of the microscope
    shutter_right_state : bool
        Right shutter state
    shutter_left_state : bool
        Left shutter state

    Methods
    -------
    open_left()
        Open the left shutter, close the right shutter.
    open_right()
        Open the right shutter, close the left shutter.
    close_shutters()
        Close both shutters
    state()
        Return the current state of the shutters
    """

    def __init__(self, configuration, experiment):
        super().__init__(configuration, experiment)

    def __del__(self):
        r"""Close the SyntheticShutter at exit.
        """
        pass

    def open_left(self):
        r"""Open the left shutter, close the right shutter.
        """
        self.shutter_right_state = False
        self.shutter_left_state = True
        logger.debug("SyntheticShutter - Shutter left opened")

    def open_right(self):
        r"""Open the right shutter, close the left shutter.
        """
        self.shutter_right_state = True
        self.shutter_left_state = False
        logger.debug("SyntheticShutter - Shutter right opened")

    def close_shutters(self):
        r"""CLose both shutters
        """
        self.shutter_right_state = False
        self.shutter_left_state = False
        logger.debug("SyntheticShutter - Both shutters closed")

    def state(self):
        r"""Return the state of both shutters

        Returns
        -------
        shutter_left_state : bool
            State of the left shutter.
        shutter_right_state : bool
            State of the right shutter
        """
        return self.shutter_left_state, self.shutter_right_state
