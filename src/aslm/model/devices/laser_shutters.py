"""
ASLM shutter communication classes.
Triggering for shutters delivered from DAQ using digital outputs.
Each output keeps their last digital state for as long the device is not powered down.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
import logging

import nidaqmx
from nidaqmx.constants import LineGrouping

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ShutterBase:
    """
    Parent Shutter Class
    """

    def __init__(self, model, experiment, verbose=False):
        self.model = model
        self.experiment = experiment
        self.verbose = verbose

        # Right Shutter - High Resolution Mode
        self.shutter_right = self.model.DAQParameters['shutter_right']
        self.shutter_right_state = False

        # Left Shutter - Low Resolution Mode
        self.shutter_left = self.model.DAQParameters['shutter_left']
        self.shutter_left_state = False

    def __del__(self):
        pass

    def open_left(self):
        pass

    def open_right(self):
        pass

    def close_shutters(self):
        pass

    def state(self):
        pass


class SyntheticShutter(ShutterBase):
    """
    Virtual Shutter Device
    """

    def __init__(self, model, experiment, verbose=False):
        super().__init__(model, experiment, verbose)

    def open_left(self):
        self.shutter_right_state = False
        self.shutter_left_state = True
        if self.verbose:
            print('Shutter left opened')
        logger.debug("Shutter left opened")

    def open_right(self):
        self.shutter_right_state = True
        self.shutter_left_state = False
        if self.verbose:
            print('Shutter right opened')
        logger.debug("Shutter right opened")

    def close_shutters(self):
        self.shutter_right_state = False
        self.shutter_left_state = False
        if self.verbose:
            print('Both shutters closed')
        logger.debug("Both shutters closed")

    def state(self):
        return self.shutter_left_state, self.shutter_right_state


class ThorlabsShutter(ShutterBase):
    """
    Triggers Thorlabs-based shutter device using National Instruments DAQ
    Requires 5V signal for triggering
    https://www.thorlabs.com/thorproduct.cfm?partnumber=SHB1#ad-image-0
    """

    def __init__(self, model, experiment, verbose=False):
        super().__init__(model, experiment, verbose)

        # Right Shutter - High Resolution Mode
        self.shutter_right_task = nidaqmx.Task()
        self.shutter_right_task.do_channels.add_do_chan(
            self.shutter_right, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        self.shutter_right_task.write(
            self.shutter_right_state, auto_start=True)

        # Left Shutter - Low Resolution Mode
        self.shutter_left_task = nidaqmx.Task()
        self.shutter_left_task.do_channels.add_do_chan(
            self.shutter_left, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        self.shutter_left_task.write(self.shutter_left_state, auto_start=True)

    def __del__(self):
        """
        Closes the NI DAQ tasks.
        """
        self.shutter_right_task.close()
        self.shutter_left_task.close()

    def open_left(self):
        """
        Opens the Left Shutter
        Closes the Right Shutter
        """
        self.shutter_right_state = False
        self.shutter_right_task.write(
            self.shutter_right_state, auto_start=True)

        self.shutter_left_state = True
        self.shutter_left_task.write(self.shutter_left_state, auto_start=True)

        if self.verbose:
            print('Shutter left opened')
        logger.debug("Shutter left opened")

    def open_right(self):
        """
        Opens the Right Shutter
        Closes the Left Shutter
        """
        self.shutter_right_state = True
        self.shutter_right_task.write(
            self.shutter_right_state, auto_start=True)

        self.shutter_left_state = False
        self.shutter_left_task.write(self.shutter_left_state, auto_start=True)

        if self.verbose:
            print('Shutter right opened')
        logger.debug("Shutter right opened")


    def close_shutters(self):
        """
        Closes both Shutters
        """
        self.shutter_right_state = False
        self.shutter_right_task.write(
            self.shutter_right_state, auto_start=True)

        self.shutter_left_state = False
        self.shutter_left_task.write(self.shutter_left_state, auto_start=True)

        if self.verbose:
            print('Both shutters closed')
        logger.debug("Both shutters closed")

    def state(self):
        """
        Returns the state of the shutters
        """
        return self.shutter_left_state, self.shutter_right_state
