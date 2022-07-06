"""
ASLM stage communication classes.
Class for mixed digital and analog modulation of laser devices.
Goal is to set the DC value of the laser intensity with the analog voltage, and then rapidly turn it on and off
with the digital signal.

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

# Standard Imports
import logging
import time

# Third Party Imports
from pipython import GCSDevice, pitools, GCSError

# Local Imports
from aslm.model.devices.stages.stage_base import StageBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class PIStage(StageBase):
    def __init__(self, configuration, verbose):
        super().__init__(configuration, verbose)

        pi_stages = self.configuration.StageParameters['stages']
        pi_refmodes = self.configuration.StageParameters['refmode']
        pi_stages = pi_stages.split()
        pi_refmodes = pi_refmodes.split()

        # Mapping from self.axes to corresponding PI axis labelling
        self.pi_axes = [1, 2, 3, 5, 4]  # x, y, z, f, theta

        self.pitools = pitools
        self.controllername = self.configuration.StageParameters['controllername']
        self.pi_stages = pi_stages
        self.refmode = pi_refmodes
        self.serialnum = str(self.configuration.StageParameters['serialnum'])
        self.pidevice = GCSDevice(self.controllername)
        self.pidevice.ConnectUSB(serialnum=self.serialnum)
        self.pitools.startup(self.pidevice, stages=list(self.pi_stages), refmodes=list(self.refmode))
        self.block_till_controller_is_ready()

    def __del__(self):
        try:
            """
            # Close the PI connection
            """
            self.stop()
            self.pidevice.unload()
            if self.verbose:
                print('PI connection closed')
            logger.debug("PI connection closed")
        except GCSError as e:  # except BaseException:
            # logger.exception("Error while disconnecting the PI stage")
            print('Error while disconnecting the PI stage')
            logger.exception(e)
            raise

    def report_position(self):
        """
        # Reports the position of the stage for all axes, and creates the hardware
        # position dictionary.
        """
        try:
            positions = self.pidevice.qPOS(self.pidevice.axes)  # positions from the device are in mm

            # convert to um
            for ax, n in zip(self.axes, self.pi_axes):
                pos = positions[str(n)]
                if ax != 'theta':
                    pos = round(pos * 1000, 2)
                setattr(self, f"{ax}_pos", pos)
        except GCSError as e:
            print('Failed to report position')
            logger.exception(e)

        # Update internal dictionaries
        self.update_position_dictionaries()

        return self.position_dict

    def move_axis_absolute(self, axis, axis_num, move_dictionary):
        """
        Implement movement logic along a single axis.

        To move relative, self.pidevice.MVR({1: x_rel}).

        Example calls:

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary. For example, axis='x' corresponds to 'x_abs', 'x_min', etc.
        axis_num : int
            The corresponding number of this axis on a PI stage.
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', 'x_min', etc. for one or more axes.
            Expects values in micrometers, except for theta, which is in degrees.

        Returns
        -------
        bool
            Was the move successful?
        """

        try:
            # Get all necessary attributes. If we can't we'll move to the error case.
            axis_abs = move_dictionary[f"{axis}_abs"] - getattr(self, f"int_{axis}_pos_offset", 0)  # TODO: should we default to 0?
            axis_min, axis_max = getattr(self, f"{axis}_min"), getattr(self, f"{axis}_max")

            # Check that our position is within the axis bounds, fail if it's not.
            if (axis_min > axis_abs) or (axis_max < axis_abs):
                log_string = f"Absolute movement stopped: {axis} limit would be reached!" \
                             "{axis_abs} is not in the range {axis_min} to {axis_max}."
                logger.info(log_string)
                print(log_string)
                return

            # Move the stage
            try:
                pos = axis_abs
                if axis != 'theta':
                    pos /= 1000  # convert to mm
                self.pidevice.MOV({axis_num: pos})

                return True
            except GCSError as e:
                logger.exception(GCSError(e))
                return False

        except (KeyError, AttributeError):
            return False

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """
        # PI move absolute method.
        # XYZF Values are converted to millimeters for PI API.
        # Theta Values are not converted.

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for one or more axes.
            Expects values in micrometers, except for theta, which is in degrees.
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        success : bool
            Was the move successful?
        """

        for ax, n in zip(self.axes, self.pi_axes):
            success = self.move_axis_absolute(ax, n, move_dictionary)

        if wait_until_done is True:
            try:
                self.pitools.waitontarget(self.pidevice)
            except GCSError as e:
                print("wait on target failed")
                success = False
                logger.exception(e)

        return success

    def stop(self):
        try:
            self.pidevice.STP(noraise=True)
        except GCSError as e:
            logger.exception(e)

    def zero_axes(self, list):
        for axis in list:
            try:
                exec(
                    'self.int_' +
                    axis +
                    '_pos_offset = -self.' +
                    axis +
                    '_pos')
            except BaseException:
                logger.exception(f"Zeroing of axis: {axis} failed")
                print('Zeroing of axis: ', axis, 'failed')

    def unzero_axes(self, list):
        for axis in list:
            try:
                exec('self.int_' + axis + '_pos_offset = 0')
            except BaseException:
                logger.exception(f"Unzeroing of axis: {axis} failed")
                print('Unzeroing of axis: ', axis, 'failed')

    def load_sample(self):
        y_abs = self.configuration.StageParameters['y_load_position'] / 1000
        try:
            self.pidevice.MOV({2: y_abs})
        except GCSError as e:
            logger.exception(GCSError(e))

    def unload_sample(self):
        y_abs = self.configuration.StageParameters['y_unload_position'] / 1000
        try:
            self.pidevice.MOV({2: y_abs})
        except GCSError as e:
            logger.exception(GCSError(e))

    def block_till_controller_is_ready(self):
        """
        Blocks further execution (especially during referencing moves)
        till the PI controller returns ready
        """
        blockflag = True
        while blockflag:
            if self.pidevice.IsControllerReady():
                blockflag = False
            else:
                time.sleep(0.1)
