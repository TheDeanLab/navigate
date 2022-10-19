"""
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

# Local Imports
from aslm.model.devices.stages.stage_base import StageBase
from aslm.model.devices.APIs.asi.asi_tiger_controller import TigerController

# Logger Setup
# p = __name__.split(".")[1]
# logger = logging.getLogger(p)

def build_ASI_Stage_connection(com_port="COM7", baud_rate=115200):

    # wait until pi_device is ready
    blockflag = True
    while blockflag:
        asi_stage = TigerController(com_port=com_port, baud_rate=baud_rate)
        asi_stage.connect_to_serial()
        if asi_stage.is_open():
            blockflag = False
        else:
            print("Trying to connect to the ASI Stage again")
            time.sleep(0.1)
    return asi_stage

class ASIStage(StageBase):
    """
    Detailed documentation: http://asiimaging.com/docs/products/serial_commands
    Quick Start Guide: http://asiimaging.com/docs/command_quick_start
    """
    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        super().__init__(microscope_name, device_connection, configuration, device_id)
        self.axes = ["x", "y", "z"]

        # Mapping from self.axes to corresponding ASI axis labelling
        axes_mapping = {
            'x': 'X',
            'y': 'Y',
            'z': 'Z',
        }
        self.asi_axes = list(map(lambda a: axes_mapping[a], self.axes))
        self.tiger_controller = build_ASI_Stage_connection()

    def __del__(self):
        try:
            """
            Close the ASI Stage connection
            """
            self.tiger_controller.disconnect_from_serial()
            # logger.debug("ASI stage connection closed")
        except BaseException as e:
            print('Error while disconnecting the ASI stage')
            # logger.exception(e)
            raise

    def report_position(self):
        """
        Reports the position of the stage for all axes in microns
        Creates the hardware position dictionary.
        Updates the internal position dictionary.
        """
        try:
            # positions from the device are in microns
            for ax, n in zip(self.axes, self.asi_axes):
                self.tiger_controller.send_command("WHERE " + str(n))
                pos = self.tiger_controller.read_response()
                
                # Remove leading :A from response. e.g., ":A -57585.3"
                pos = pos[2:].strip()

                # Set class attributes
                setattr(self, f"{ax}_pos", float(pos))
        except BaseException as e:
            print('Failed to report ASI Stage Position')
            #logger.exception(e)

        # Update internal dictionaries
        self.update_position_dictionaries()
        return self.position_dict

    def move_axis_absolute(self, axis, axis_num, move_dictionary):
        """
        Implement movement logic along a single axis.

        Move absolute command for ASI is MOVE [Axis]=[units 1/10 microns
        Move relative command for ASI is MOVREL [Axis]= [units 1/10 microns]

        Example calls:

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary. For example, axis='x' corresponds to 'x_abs', 'x_min', etc.
        axis_num : int
            The corresponding number of this axis on a PI stage.
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', 'x_min', etc. for one or more axes.
            Expects values in micrometers.
            
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
            self.pidevice.MOV({axis_num: pos})

            return True
        except BaseException as e:
            #logger.exception(GCSError(e))
            return False

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """
        # ASI move absolute method.
        # XYZ Values should remain in microns for the ASI API
        # Theta Values are not accepted.

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

        for ax, n in zip(self.axes, self.asi_axes):
            success = self.move_axis_absolute(ax, n, move_dictionary)

        if wait_until_done is True:
            try:
                # TODO: Implement some sort of wait on target.
                #self.pitools.waitontarget(self.pidevice)
                pass
            except BaseException as e:
                print("Wait on target failed for the ASI stage")
                success = False
                #logger.exception(e)

        return success

    def stop(self):
        try:
            self.tiger_controller.send_command("HALT")
            response = self.tiger_controller.read_response()
        except BaseException as e:
            #logger.exception(e)
            pass

        if response == ":A":
            print("ASI Stages Stopped")
        elif response == ":N-21":
            print("Stp[] Failed for ASI Stage")
        else:
            print("Unknown ASI Stage response to stop command")
            
    # def zero_axes(self, list):
    #     for axis in list:
    #         try:
    #             exec(
    #                 'self.int_' +
    #                 axis +
    #                 '_pos_offset = -self.' +
    #                 axis +
    #                 '_pos')
    #         except BaseException:
    #             logger.exception(f"Zeroing of axis: {axis} failed")
    #             print('Zeroing of axis: ', axis, 'failed')

    # def unzero_axes(self, list):
    #     for axis in list:
    #         try:
    #             exec('self.int_' + axis + '_pos_offset = 0')
    #         except BaseException:
    #             logger.exception(f"Unzeroing of axis: {axis} failed")
    #             print('Unzeroing of axis: ', axis, 'failed')

    # def load_sample(self):
    #     y_abs = self.y_load_position / 1000
    #     try:
    #         self.pidevice.MOV({2: y_abs})
    #     except GCSError as e:
    #         logger.exception(GCSError(e))

    # def unload_sample(self):
    #     y_abs = self.y_unload_position / 1000
    #     try:
    #         self.pidevice.MOV({2: y_abs})
    #     except GCSError as e:
    #         logger.exception(GCSError(e))

