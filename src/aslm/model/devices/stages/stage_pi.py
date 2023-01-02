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


def build_PIStage_connection(controller_name,
                             serial_number,
                             stages,
                             reference_modes):
    """Connect to the Physik Instrumente Stage"""
    pi_stages = stages.split()
    pi_reference_modes = reference_modes.split()
    pi_tools = pitools
    pi_device = GCSDevice(controller_name)
    pi_device.ConnectUSB(serialnum=serial_number)
    pi_tools.startup(pi_device,
                     stages=list(pi_stages),
                     refmodes=list(pi_reference_modes))

    # wait until pi_device is ready
    block_flag = True
    while block_flag:
        if pi_device.IsControllerReady():
            block_flag = False
        else:
            time.sleep(0.1)
    
    stage_connection = {
        'pi_tools': pi_tools,
        'pi_device': pi_device
    }
    return stage_connection


class PIStage(StageBase):
    """StageBase Parent Class

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_connection : object
            Hardware device to connect to
        configuration : multiprocesing.managers.DictProxy
            Global configuration of the microscope

        Attributes
        -----------
        x_pos : float
            True x position
        y_pos : float
            True y position
        z_pos : float
            True z position
        f_pos : float
            True focus position
        theta_pos : float
            True rotation position
        position_dict : dict
            Dictionary of true stage positions
        x_max : float
            Max x position
        y_max : float
            Max y position
        z_max : float
            Max y position
        f_max : float
            Max focus positoin
        theta_max : float
            Max rotation position
        x_min : float
            Min x position
        y_min : float
            Min y position
        z_min : float
            Min y position
        f_min : float
            Min focus positoin
        theta_min : float
            Min rotation position

        Methods
        -------
        create_position_dict()
            Creates a dictionary with the hardware stage positions.
        get_abs_position()
            Makes sure that the move is within the min and max stage limits.
        stop()
            Emergency halt of stage operation.

        """
    def __init__(self,
                 microscope_name,
                 device_connection,
                 configuration,
                 device_id=0):
        super().__init__(microscope_name,
                         device_connection,
                         configuration,
                         device_id)

        # Mapping from self.axes to corresponding PI axis labelling
        axes_mapping = {
            'x': 1,
            'y': 2,
            'z': 3,
            'f': 5,
            'theta': 4
        }
        self.pi_axes = list(map(lambda a: axes_mapping[a], self.axes))
        self.pi_tools = device_connection['pi_tools']
        self.pi_device = device_connection['pi_device']

    def __del__(self):
        """Delete the PI Connection"""
        try:
            self.stop()
            logger.debug("PI connection closed")
        except GCSError as e:  # except BaseException:
            print('Error while disconnecting the PI stage')
            logger.exception(e)
            raise

    def report_position(self):
        """Reports the position for all axes, and create position dictionary.

        Positions from Physik Instrumente device are in millimeters
        """
        try:
            positions = self.pi_device.qPOS(self.pi_device.axes)

            # convert to um
            for ax, n in zip(self.axes, self.pi_axes):
                pos = positions[str(n)]
                if ax != 'theta':
                    pos = round(pos * 1000, 2)
                setattr(self, f"{ax}_pos", pos)
        except GCSError as e:
            print('Failed to report position')
            logger.exception(e)

        # Update Position Dictionary
        self.create_position_dict()
        return self.position_dict

    def move_axis_absolute(self,
                           axis,
                           axis_num,
                           move_dictionary):
        """ Move stage along a single axis.

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

        axis_abs = self.get_abs_position(axis, move_dictionary)
        if axis_abs == -1e50:
            return False

        # Move the stage
        try:
            pos = axis_abs
            if axis != 'theta':
                pos /= 1000  # convert to mm
            self.pi_device.MOV({axis_num: pos})
            return True
        except GCSError as e:
            logger.exception(GCSError(e))
            return False

    def move_absolute(self,
                      move_dictionary,
                      wait_until_done=False):
        """ Move Absolute Method.
        XYZF Values are converted to millimeters for PI API.
        Theta Values are not converted.

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for one or more axes.
            Expect values in micrometers, except for theta, which is in degrees.
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
                self.pi_tools.waitontarget(self.pi_device)
            except GCSError as e:
                print("wait on target failed")
                success = False
                logger.exception(e)
        return success

    def stop(self):
        """Stop all stage movement abruptly."""
        try:
            self.pi_device.STP(noraise=True)
        except GCSError as e:
            logger.exception(e)
