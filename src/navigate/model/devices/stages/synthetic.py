# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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

# Standard Imports
import logging
import time

# Third Party Imports

# Local Imports
from navigate.model.devices.stages.base import StageBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class SyntheticStage(StageBase):
    """Synthetically generated stage for testing purposes."""

    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        """Initialize the stage.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : str
            Connection string for the device.
        configuration : dict
            Configuration dictionary for the device.
        device_id : int
            Device ID for the device.
        """
        super().__init__(microscope_name, device_connection, configuration, device_id)

        #: float: The default speed of the stage in mm/s.
        self.default_speed = 7.68 * 0.67

        # Default axes mapping
        axes_mapping = {"x": "X", "y": "Y", "z": "Z", "theta": "Theta", "f": "F"}
        if not self.axes_mapping:
            #: dict: Dictionary mapping software axes to hardware axes.
            self.axes_mapping = {
                axis: axes_mapping[axis] for axis in self.axes if axis in axes_mapping
            }

        self.sample_rate = 10000
        self.volts_per_micron = "0.1 * x"
        self.camera_delay = 0.01

    def report_position(self):
        """Report the current position of the stage.

        Returns
        -------
        position_dict : dict
            Dictionary containing the current position of the stage.
        """
        return self.get_position_dict()

    def move_axis_absolute(self, axis, abs_pos, wait_until_done=False):
        """Implement movement logic along a single axis.

        Parameters
        ----------
        axis : str
            An axis. For example, 'x', 'y', 'z', 'f', 'theta'.
        abs_pos : float
            Absolute position value
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        bool
            Was the move successful?
        """
        axis_abs = self.get_abs_position(axis, abs_pos)
        if axis_abs == -1e50:
            return False

        if wait_until_done:
            time.sleep(0.025)

        # Move the stage
        setattr(self, f"{axis}_pos", axis_abs)
        return True

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """Move stage along a single axis.

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for one
            or more axes. Expects values in micrometers, except for theta, which is
            in degrees.
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        success : bool
            Was the move successful?
        """
        abs_pos_dict = self.verify_abs_position(move_dictionary)
        if not abs_pos_dict:
            return False

        for axis in abs_pos_dict:
            setattr(self, f"{axis}_pos", abs_pos_dict[axis])
        if wait_until_done is True:
            time.sleep(0.025)

        return True

    def load_sample(self):
        """Load a sample.

        Warning
        -------
            Not implemented.
        """
        self.y_pos = self.y_load_position

    def unload_sample(self):
        """Unload a sample.

        Warning
        -------
            Not implemented.
        """
        self.y_pos = self.y_unload_position

    def get_axis_position(self, axis):
        """Get the current position of the stage along a single axis.

        Parameters
        ----------
        axis : str
            An axis. For example, 'x', 'y', 'z', 'f', 'theta'.

        Returns
        -------
        float
            The current position of the stage along the specified axis.
        """
        return getattr(self, f"{axis}_pos")

    def set_speed(self, velocity_dict):
        """Set the speed of the stage.

        Parameters
        ----------
        velocity_dict : dict
            Dictionary containing the speed of the stage along each axis.
        """
        pass

    def get_speed(self, axis):
        """Get the speed of the stage.

        Parameters
        ----------
        axis : str
            An axis. For example, 'x', 'y', 'z', 'f', 'theta'.

        Returns
        -------
        float
            The speed of the stage along the specified axis.
        """

        return 1

    def scanr(self, start_position_mm, end_position_mm, enc_divide, axis="z"):
        """Scan the stage using the constant velocity mode along a single axis.

        Parameters
        ----------
        start_position_mm : float
            Starting position of the scan in mm.
        end_position_mm : float
            Ending position of the scan in mm.
        enc_divide : int
            Encoder divide value.
        axis : str
            An axis. For example, 'x', 'y', 'z', 'f', 'theta'.

        """

        pass

    def start_scan(self, axis):
        """Start a scan along a single axis.

        Parameters
        ----------
        axis : str
            An axis. For example, 'x', 'y', 'z', 'f', 'theta'.

        """
        pass

    def stop_scan(self):
        """Stop a scan."""
        pass

    def update_waveform(self, waveform_dict):
        print("*** update waveform:", waveform_dict.keys())
        pass
