# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
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

# Standard Imports
import logging
from multiprocessing.managers import ListProxy

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class StageBase:
    """StageBase Parent Class

    Parameters
    ----------
    microscope_name : str
        Name of microscope in configuration
    device_connection : object
        Hardware device to connect to
    configuration : multiprocessing.managers.DictProxy
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
        Max focus position
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

    def __init__(self, microscope_name, device_connection, configuration, device_id=0):

        self.position_dict = None
        stage = configuration["configuration"]["microscopes"][microscope_name]["stage"]
        if type(stage["hardware"]) == ListProxy:
            self.axes = stage["hardware"][device_id]["axes"]
        else:
            self.axes = stage["hardware"]["axes"]

        """Initial setting for all positions
        self.x_pos, self.y_pos etc are the true axis positions, no matter whether
        the stages are zeroed or not.
        """
        for ax in self.axes:
            setattr(self, f"{ax}_pos", 0)
            setattr(self, f"{ax}_min", stage[f"{ax}_min"])  # Units are in microns
            setattr(self, f"{ax}_max", stage[f"{ax}_max"])  # Units are in microns
        self.create_position_dict()

    def create_position_dict(self):
        """Creates a dictionary with the hardware stage positions."""
        self.position_dict = {}
        for ax in self.axes:
            ax_str = f"{ax}_pos"
            self.position_dict[ax_str] = getattr(self, ax_str)

    def get_abs_position(self, axis, move_dictionary):
        """Ensure the requested position is within axis bounds and return it.

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary. For example, axis='x' corresponds to 'x_abs', 'x_min', etc.
        move_dictionary : dict
            A dictionary of values required for movement.
            Includes 'x_abs', 'x_min', etc. for one or more axes.
            Expect values in micrometers, except for theta, which is in degrees.

        Returns
        -------
        float
            Position to move the stage to for this axis.
        """
        try:
            # Get all necessary attributes. If we can't we'll move to the error case.
            axis_abs = move_dictionary[f"{axis}_abs"] - getattr(
                self, f"int_{axis}_pos_offset", 0
            )
            # TODO: should we default to 0?
            axis_min, axis_max = getattr(self, f"{axis}_min"), getattr(
                self, f"{axis}_max"
            )

            # Check that our position is within the axis bounds, fail if it's not.
            if (axis_min > axis_abs) or (axis_max < axis_abs):
                log_string = (
                    f"Absolute movement stopped: {axis} limit would be reached!"
                    f"{axis_abs} is not in the range {axis_min} to {axis_max}."
                )
                logger.info(log_string)
                print(log_string)
                # Return a ridiculous value to make it clear we've failed.
                # This is to avoid returning a duck type.
                return -1e50
            return axis_abs
        except (KeyError, AttributeError):
            return -1e50

    def stop(self):
        """Stop all stage movement abruptly."""
        pass
