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

from pipython import GCSDevice, pitools, GCSError, gcserror

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class StageBase:
    def __init__(self, model, verbose):
        self.verbose = verbose
        self.model = model

        """
        Initial setting of all positions
        self.x_pos, self.y_pos etc are the true axis positions, no matter whether
        the stages are zeroed or not.
        """
        self.x_pos = 0
        self.y_pos = 0
        self.z_pos = 0
        self.f_pos = 0
        self.theta_pos = 0
        self.position_dict = {'x_pos': self.x_pos,
                              'y_pos': self.y_pos,
                              'z_pos': self.z_pos,
                              'f_pos': self.f_pos,
                              'theta_pos': self.theta_pos,
                              }
        """
        Internal (software) positions
        """
        self.int_x_pos = 0
        self.int_y_pos = 0
        self.int_z_pos = 0
        self.int_f_pos = 0
        self.int_theta_pos = 0
        self.int_position_dict = {'x_pos': self.int_x_pos,
                                  'y_pos': self.int_y_pos,
                                  'z_pos': self.int_z_pos,
                                  'f_pos': self.int_f_pos,
                                  'theta_pos': self.int_theta_pos,
                                  }
        """
        Create offsets. It should be: int_x_pos = x_pos + int_x_pos_offset
        self.int_x_pos = self.x_pos + self.int_x_pos_offset
        OR x_pos = int_x_pos - int_x_pos_offset
        self.x_pos = self.int_x_pos - self.int_x_pos_offset
        """
        self.int_x_pos_offset = 0
        self.int_y_pos_offset = 0
        self.int_z_pos_offset = 0
        self.int_f_pos_offset = 0
        self.int_theta_pos_offset = 0

        """
        Setting movement limits: currently hardcoded: Units are in microns
        """
        self.x_max = model.StageParameters['x_max']
        self.x_min = model.StageParameters['x_min']
        self.y_max = model.StageParameters['y_max']
        self.y_min = model.StageParameters['y_min']
        self.z_max = model.StageParameters['z_max']
        self.z_min = model.StageParameters['z_min']
        self.f_max = model.StageParameters['f_max']
        self.f_min = model.StageParameters['f_min']
        self.theta_max = model.StageParameters['theta_max']
        self.theta_min = model.StageParameters['theta_min']

        # Sample Position When Rotating
        self.x_rot_position = model.StageParameters['x_rot_position']
        self.y_rot_position = model.StageParameters['y_rot_position']
        self.z_rot_position = model.StageParameters['z_rot_position']

        # Starting Position of Focusing Device
        self.startfocus = model.StageParameters['startfocus']

    def create_position_dict(self):
        pass

    def create_internal_position_dict(self):
        pass

    def report_position(self):
        pass

    def move_relative(self, dict, wait_until_done=False):
        pass

    def move_absolute(self, dict, wait_until_done=False):
        pass

    def stop(self):
        pass

    def zero_axes(self, list):
        pass

    def unzero_axes(self, list):
        pass

    def load_sample(self):
        pass

    def unload_sample(self):
        pass

    def mark_rotation_position(self):
        pass

    def go_to_rotation_position(self, wait_until_done=False):
        pass


class SyntheticStage(StageBase):
    def __init__(self, model, verbose):
        super().__init__(model, verbose)

    def create_position_dict(self):
        self.position_dict = {'x_pos': self.x_pos,
                              'y_pos': self.y_pos,
                              'z_pos': self.z_pos,
                              'f_pos': self.f_pos,
                              'theta_pos': self.theta_pos,
                              }

    def create_internal_position_dict(self):
        self.int_position_dict = {'x_pos': self.int_x_pos,
                                  'y_pos': self.int_y_pos,
                                  'z_pos': self.int_z_pos,
                                  'f_pos': self.int_f_pos,
                                  'theta_pos': self.int_theta_pos,
                                  }

    def report_position(self):
        self.create_position_dict()
        self.int_x_pos = self.x_pos + self.int_x_pos_offset
        self.int_y_pos = self.y_pos + self.int_y_pos_offset
        self.int_z_pos = self.z_pos + self.int_z_pos_offset
        self.int_f_pos = self.f_pos + self.int_f_pos_offset
        self.int_theta_pos = self.theta_pos + self.int_theta_pos_offset
        self.create_internal_position_dict()
        if self.verbose:
            print("Stage Position: ", self.int_position_dict)
        logger.debug(f"Stage Position:, {self.int_position_dict}")

    def move_relative(self, move_dictionary, wait_until_done=False):
        """
        Move relative method
        """

        if 'x_rel' in move_dictionary:
            x_rel = move_dictionary['x_rel']
            if (self.x_min <= self.x_pos +
                    x_rel) and (self.x_max >= self.x_pos + x_rel):
                self.x_pos = self.x_pos + x_rel
            else:
                print('Relative movement stopped: X limit would be reached!', 1000)
                logger.info("Relative movement stopped: X limit would be reached!, 1000")

        if 'y_rel' in move_dictionary:
            y_rel = move_dictionary['y_rel']
            if (self.y_min <= self.y_pos +
                    y_rel) and (self.y_max >= self.y_pos + y_rel):
                self.y_pos = self.y_pos + y_rel
            else:
                print('Relative movement stopped: Y limit would be reached!', 1000)
                logger.info("Relative movement stopped: Y limit would be reached!")

        if 'z_rel' in move_dictionary:
            z_rel = move_dictionary['z_rel']
            if (self.z_min <= self.z_pos +
                    z_rel) and (self.z_max >= self.z_pos + z_rel):
                self.z_pos = self.z_pos + z_rel
            else:
                print('Relative movement stopped: Z limit would be reached!', 1000)
                logger.info("Relative movement stopped: Z limit would be reached!")

        if 'theta_rel' in move_dictionary:
            theta_rel = move_dictionary['theta_rel']
            if (self.theta_min <= self.theta_pos +
                    theta_rel) and (self.theta_max >= self.theta_pos + theta_rel):
                self.theta_pos = self.theta_pos + theta_rel
            else:
                print(
                    'Relative movement stopped: Rotation limit would be reached!',
                    1000)
                logger.info("Relative movement stopped: Rotation limit would be reached!")

        if 'f_rel' in move_dictionary:
            f_rel = move_dictionary['f_rel']
            if (self.f_min <= self.f_pos +
                    f_rel) and (self.f_max >= self.f_pos + f_rel):
                self.f_pos = self.f_pos + f_rel
            else:
                print(
                    'Relative movement stopped: Focus limit would be reached!',
                    1000)
                logger.info("Relative movement stopped: Focus limit would be reached!")

        if wait_until_done is True:
            time.sleep(0.02)

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """
        Move absolute method
        """

        if 'x_abs' in move_dictionary:
            x_abs = move_dictionary['x_abs']
            x_abs = x_abs - self.int_x_pos_offset
            if (self.x_min <= x_abs) and (self.x_max >= x_abs):
                self.x_pos = x_abs
            else:
                logger.info("Absolute movement stopped: X limit would be reached!, 1000")
                print('Absolute movement stopped: X limit would be reached!', 1000)

        if 'y_abs' in move_dictionary:
            y_abs = move_dictionary['y_abs']
            y_abs = y_abs - self.int_y_pos_offset
            if (self.y_min <= y_abs) and (self.y_max >= y_abs):
                self.y_pos = y_abs
            else:
                logger.info("Absolute movement stopped: Y limit would be reached!, 1000")
                print('Absolute movement stopped: Y limit would be reached!', 1000)

        if 'z_abs' in move_dictionary:
            z_abs = move_dictionary['z_abs']
            z_abs = z_abs - self.int_z_pos_offset
            if (self.z_min <= z_abs) and (self.z_max >= z_abs):
                self.z_pos = z_abs
            else:
                logger.info("Absolute movement stopped: Z limit would be reached!, 1000")
                print('Absolute movement stopped: Z limit would be reached!', 1000)

        if 'f_abs' in move_dictionary:
            f_abs = move_dictionary['f_abs']
            f_abs = f_abs - self.int_f_pos_offset
            if (self.f_min <= f_abs) and (self.f_max >= f_abs):
                self.f_pos = f_abs
            else:
                logger.info("Absolute movement stopped: Focus limit would be reached!, 1000")
                print(
                    'Absolute movement stopped: Focus limit would be reached!',
                    1000)

        if 'theta_abs' in move_dictionary:
            theta_abs = move_dictionary['theta_abs']
            theta_abs = theta_abs - self.int_theta_pos_offset
            if (self.theta_min <= theta_abs) and (self.theta_max >= theta_abs):
                self.theta_pos = theta_abs
            else:
                logger.info("Absolute movement stopped: Rotation limit would be reached!, 1000")
                print(
                    'Absolute movement stopped: Rotation limit would be reached!',
                    1000)

        if wait_until_done is True:
            time.sleep(.25)

        if self.verbose:
            print('stage moved to ', move_dictionary)
        logger.debug(f"stage moved to, {move_dictionary}")

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
        self.y_pos = self.model.StageParameters['y_load_position']

    def unload_sample(self):
        self.y_pos = self.model.StageParameters['y_unload_position']

    def mark_rotation_position(self):
        """
        # Take the current position and mark it as rotation location
        """
        self.x_rot_position = self.x_pos
        self.y_rot_position = self.y_pos
        self.z_rot_position = self.z_pos
        if self.verbose:
            print('Marking new rotation position (absolute coordinates): X: ',
                  self.x_pos, ' Y: ', self.y_pos, ' Z: ', self.z_pos)
        logger.debug(f"Marking new rotation position (absolute coordinates): X: {self.x_pos}, Y: {self.y_pos}, Z: {self.z_pos}")

    def go_to_rotation_position(self, wait_until_done=False):
        pass


class PIStage(StageBase):
    def __init__(self, model, verbose):
        super().__init__(model, verbose)
        pi_stages = self.model.StageParameters['stages']
        pi_refmodes = self.model.StageParameters['refmode']
        pi_stages = pi_stages.split()
        pi_refmodes = pi_refmodes.split()

        self.pitools = pitools
        self.controllername = self.model.StageParameters['controllername']
        self.pi_stages = pi_stages
        self.refmode = pi_refmodes
        self.serialnum = str(self.model.StageParameters['serialnum'])
        self.pidevice = GCSDevice(self.controllername)
        self.pidevice.ConnectUSB(serialnum=self.serialnum)
        self.pitools.startup(self.pidevice, stages=list(self.pi_stages), refmodes=list(self.refmode))
        self.block_till_controller_is_ready()

        # Move the Focusing Stage to the Start Position
        try:
            self.pidevice.MOV(5, self.startfocus / 1000)
        except GCSError as e:
            logger.exception(GCSError(e)) # Need to test this on the stage or somehow simulate, otherwise the documented way will work, but if this works it will be more clear what happened
            # raise

    def __del__(self):
        try:
            """
            # Close the PI connection
            """
            self.pidevice.unload()
            if self.verbose:
                print('PI connection closed')
            logger.debug("PI connection closed")
        except GCSError as e: #except BaseException:
            # logger.exception("Error while disconnecting the PI stage")
            print('Error while disconnecting the PI stage')
            logger.exception(GCSError(e))
            raise
            


    def create_position_dict(self):
        """
        # Creates a dictionary with the hardware stage positions.
        """
        self.position_dict = {'x_pos': self.x_pos,
                              'y_pos': self.y_pos,
                              'z_pos': self.z_pos,
                              'f_pos': self.f_pos,
                              'theta_pos': self.theta_pos,
                              }

    def create_internal_position_dict(self):
        """
        # Creates a dictionary with the software stage positions.
        # Internal position includes the offset for each stage position.
        # e.g, int_x_pos = x_pos + int_x_pos_offset
        """
        self.int_position_dict = {'x_pos': self.int_x_pos,
                                  'y_pos': self.int_y_pos,
                                  'z_pos': self.int_z_pos,
                                  'f_pos': self.int_f_pos,
                                  'theta_pos': self.int_theta_pos,
                                  }

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

        Returns
        -------
        None
        """

        try:
            # Get all necessary attributes. If we can't we'll move to the error case.
            # This could be refactored into its own function and used in the synthetic stage as well.
            axis_abs = move_dictionary[f"{axis}_abs"] - getattr(self, f"int_{axis}_pos_offset", 0)  # TODO: should we default to 0?
            axis_min, axis_max = getattr(self, f"{axis}_min"), getattr(self, f"{axis}_max")

            # Check that our position is within the axis bounds, fail if it's not.
            # This could be refactored into its own function and used in the synthetic stage as well.
            if (axis_min > axis_abs) or (axis_max < axis_abs):
                log_string = f"Absolute movement stopped: {axis} limit would be reached!" \
                             "{axis_abs} is not in the range {axis_min} to {axis_max}."
                logger.info(log_string)
                print(log_string)
                return

            # Move the stage
            # This is the only part that needs to be different from the synthetic stage. In theory, we could
            # refactor this entire function (move_axis_absolute()) to accept a function and input parameters
            # and this entire function could be used in synthetic stage as well.
            try:
                # TODO: The conversion should not be here, but instead addressed when put in move_dictionary.
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

        # if 'x_abs' in move_dictionary:
        #     x_abs = move_dictionary['x_abs']
        #     x_abs = x_abs - self.int_x_pos_offset
        #     if (self.x_min <= x_abs) and (self.x_max >= x_abs):
        #         x_abs = x_abs / 1000
        #         try:
        #             self.pidevice.MOV({1: x_abs})
        #         except GCSError as e:
        #             logger.exception(GCSError(e))
        #     else:
        #         logger.info("Absolute movement stopped: X Motion limit would be reached!, 1000")
        #         print(
        #             'Absolute movement stopped: X Motion limit would be reached!',
        #             1000)
        #
        # if 'y_abs' in move_dictionary:
        #     y_abs = move_dictionary['y_abs']
        #     y_abs = y_abs - self.int_y_pos_offset
        #     if (self.y_min <= y_abs) and (self.y_max >= y_abs):
        #         y_abs = y_abs / 1000
        #         try:
        #             self.pidevice.MOV({2: y_abs})
        #         except GCSError as e:
        #             logger.exception(GCSError(e))
        #     else:
        #         logger.info("Absolute movement stopped: Y Motion limit would be reached!, 1000")
        #         print(
        #             'Absolute movement stopped: Y Motion limit would be reached!',
        #             1000)
        #
        # if 'z_abs' in move_dictionary:
        #     z_abs = move_dictionary['z_abs']
        #     z_abs = z_abs - self.int_z_pos_offset
        #     if (self.z_min <= z_abs) and (self.z_max >= z_abs):
        #         z_abs = z_abs / 1000
        #         try:
        #             self.pidevice.MOV({3: z_abs})
        #         except GCSError as e:
        #             logger.exception(GCSError(e))
        #     else:
        #         logger.info("Absolute movement stopped: Z Motion limit would be reached!, 1000")
        #         print(
        #             'Absolute movement stopped: Z Motion limit would be reached!',
        #             1000)
        #
        # if 'f_abs' in move_dictionary:
        #     f_abs = move_dictionary['f_abs']
        #     f_abs = f_abs - self.int_f_pos_offset
        #     if (self.f_min <= f_abs) and (self.f_max >= f_abs):
        #         f_abs = f_abs / 1000
        #         try:
        #             self.pidevice.MOV({5: f_abs})
        #         except GCSError as e:
        #             logger.exception(GCSError(e))
        #     else:
        #         logger.info("Absolute movement stopped: F Motion limit would be reached!, 1000")
        #         print(
        #             'Absolute movement stopped: F Motion limit would be reached!',
        #             1000)
        #
        # if 'theta_abs' in move_dictionary:
        #     theta_abs = move_dictionary['theta_abs']
        #     theta_abs = theta_abs - self.int_theta_pos_offset
        #     if (self.theta_min <= theta_abs) and (self.theta_max >= theta_abs):
        #         try:
        #             self.pidevice.MOV({4: theta_abs})
        #         except GCSError as e:
        #             logger.exception(GCSError(e))
        #     else:
        #         logger.info("Absolute movement stopped: Theta Motion limit would be reached!, 1000")
        #         print(
        #             'Absolute movement stopped: Theta Motion limit would be reached!',
        #             1000)

        if wait_until_done is True:
            self.pitools.waitontarget(self.pidevice)

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
        y_abs = self.model.StageParameters['y_load_position'] / 1000
        try:
            self.pidevice.MOV({2: y_abs})
        except GCSError as e:
            logger.exception(GCSError(e))


    def unload_sample(self):
        y_abs = self.model.StageParameters['y_unload_position'] / 1000
        try:
            self.pidevice.MOV({2: y_abs})
        except GCSError as e:
            logger.exception(GCSError(e))

    def mark_rotation_position(self):
        """
        Take the current position and mark it as rotation location
        """
        self.x_rot_position = self.x_pos
        self.y_rot_position = self.y_pos
        self.z_rot_position = self.z_pos
        if self.verbose:
            print('Marking new rotation position (absolute coordinates): X: ',
                 self.x_pos, ' Y: ', self.y_pos, ' Z: ', self.z_pos)
        logger.debug(f"Marking new rotation position(absolute coordinates): X: , {self.x_pos},  Y: , {self.y_pos}, Z: , {self.z_pos}")

    def go_to_rotation_position(self, wait_until_done=False):
        x_abs = self.x_rot_position / 1000
        y_abs = self.y_rot_position / 1000
        z_abs = self.z_rot_position / 1000
        try:
            self.pidevice.MOV({1: x_abs, 2: y_abs, 3: z_abs})
        except GCSError as e:
            logger.exception(GCSError(e))
        if wait_until_done is True:
            self.pitools.waitontarget(self.pidevice)

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

