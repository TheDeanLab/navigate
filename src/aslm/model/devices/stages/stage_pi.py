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
            logger.exception(GCSError(e))
            raise

    def report_position(self):
        """
        # Reports the position of the stage for all axes, and creates the hardware
        # position dictionary.
        """
        positions = self.pidevice.qPOS(self.pidevice.axes)
        self.x_pos = round(positions['1'] * 1000, 2)
        self.y_pos = round(positions['2'] * 1000, 2)
        self.z_pos = round(positions['3'] * 1000, 2)
        self.f_pos = round(positions['5'] * 1000, 2)
        self.theta_pos = positions['4']
        self.create_position_dict()

        self.int_x_pos = self.x_pos + self.int_x_pos_offset
        self.int_y_pos = self.y_pos + self.int_y_pos_offset
        self.int_z_pos = self.z_pos + self.int_z_pos_offset
        self.int_f_pos = self.f_pos + self.int_f_pos_offset
        self.int_theta_pos = self.theta_pos + self.int_theta_pos_offset
        self.create_internal_position_dict()

        if self.verbose:
            print("Stage Positions:", self.int_position_dict)
        logger.debug(f"Stage Positions: {self.int_position_dict}")

    def move_relative(self, move_dictionary, wait_until_done=False):
        """
        # PI move relative method.
        # Checks to make sure that the move does not exceed the stage limits prior to movement.
        """
        if 'x_rel' in move_dictionary:
            x_rel = move_dictionary['x_rel']
            if (self.x_min <= self.x_pos +
                x_rel) and (self.x_max >= self.x_pos + x_rel):
                x_rel = x_rel / 1000
                try:
                    self.pidevice.MVR({1: x_rel})
                except GCSError as e:
                    logger.exception(GCSError(e))
            else:
                logger.info("Relative movement stopped: X Motion limit would be reached!, 1000")
                print(
                    'Relative movement stopped: X Motion limit would be reached!',
                    1000)

        if 'y_rel' in move_dictionary:
            y_rel = move_dictionary['y_rel']
            if (self.y_min <= self.y_pos +
                y_rel) and (self.y_max >= self.y_pos + y_rel):
                y_rel = y_rel / 1000
                try:
                    self.pidevice.MVR({2: y_rel})
                except GCSError as e:
                    logger.exception(GCSError(e))
            else:
                logger.info("Relative movement stopped: Y Motion limit would be reached!, 1000")
                print(
                    'Relative movement stopped: Y Motion limit would be reached!',
                    1000)

        if 'z_rel' in move_dictionary:
            z_rel = move_dictionary['z_rel']
            if (self.z_min <= self.z_pos +
                z_rel) and (self.z_max >= self.z_pos + z_rel):
                z_rel = z_rel / 1000
                try:
                    self.pidevice.MVR({3: z_rel})
                except GCSError as e:
                    logger.exception(GCSError(e))
            else:
                logger.info("Relative movement stopped: Z Motion limit would be reached!, 1000")
                print(
                    'Relative movement stopped: Z Motion limit would be reached!',
                    1000)

        if 'theta_rel' in move_dictionary:
            theta_rel = move_dictionary['theta_rel']
            if (self.theta_min <= self.theta_pos + theta_rel) and (self.theta_max >= self.theta_pos + theta_rel):
                try:
                    self.pidevice.MVR({4: theta_rel})
                except GCSError as e:
                    logger.exception(GCSError(e))
            else:
                logger.info("Relative movement stopped: Theta Motion limit would be reached!, 1000")
                print(
                    'Relative movement stopped: theta Motion limit would be reached!',
                    1000)

        if 'f_rel' in move_dictionary:
            f_rel = move_dictionary['f_rel']
            if (self.f_min <= self.f_pos + f_rel) and (self.f_max >= self.f_pos + f_rel):
                f_rel = f_rel / 1000
                try:
                    self.pidevice.MVR({5: f_rel})
                except GCSError as e:
                    logger.exception(GCSError(e))
            else:
                logger.info("Relative movement stopped: F Motion limit would be reached!, 1000")
                print(
                    'Relative movement stopped: f Motion limit would be reached!',
                    1000)

        if wait_until_done is True:
            self.pitools.waitontarget(self.pidevice)

    def move_axis_absolute(self, axis, axis_num, move_dictionary):
        """
        Implement movement logic along a single axis.

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
        None
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
                if axis != 'theta':
                    axis_abs /= 1000  # convert to mm
                self.pidevice.MOV({axis_num: axis_abs})
            except GCSError as e:
                logger.exception(GCSError(e))

        except (KeyError, AttributeError):
            return

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """
        # PI move absolute method.
        # XYZF Values are converted to millimeters for PI API.
        # Theta Values are not converted.
        """

        axes = ['x', 'y', 'z', 'f', 'theta']
        axis_nums = [1, 2, 3, 5, 4]

        for ax, n in zip(axes, axis_nums):
            self.move_axis_absolute(ax, n, move_dictionary)

        if wait_until_done is True:
            try:
                self.pitools.waitontarget(self.pidevice)
            except GCSError as e:
                print("wait on target failed")
                logger.exception(e)

    def stop(self):
        self.pidevice.STP(noraise=True)

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
