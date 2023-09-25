 # Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
#

# Standard Library Imports
import time
import logging

# Third Party Imports
import numpy as np

# Local imports

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ConstantVelocityAcquisition:
    """Class for acquiring data using the ASI internal encoder."""

    def __init__(self, model, axis='z'):
        self.model = model
        self.axis = axis
        self.default_speed = None
        self.asi_stage = None
        self.received_frames = None
        self.readout_time = None
        self.start_position_um = None
        self.stop_position_um = None
        self.number_z_steps = None
        self.expected_frames = None

        self.config_table = {
            "signal": {
                "init": self.pre_func_signal,
                "cleanup": self.cleanup,
            },
            "node": {"node_type": "multi-step", "device_related": True},
        }

    def pre_func_signal(self):
        """Prepare the constant velocity acquisition.

        Assumes stage motion is 45 degrees relative to the optical axis.

        Parameters 
        ----------
        None

        Returns
        -------
        None
        """
        # Bookkeeping and Stage Selection
        self.received_frames = 0
        self.model.active_microscope.prepare_next_channel()
        self.asi_stage = self.model.active_microscope.stages[self.axis]

        # Get readout time, sweep time, and exposure time.
        readout_time = self.model.active_microscope.get_readout_time()
        _, sweep_times = self.model.active_microscope.calculate_exposure_sweep_times(
            readout_time
        )
        current_sweep_time = sweep_times[
            f"channel_{self.model.active_microscope.current_channel}"
        ]
        self.readout_time = readout_time
        logger.info(f"*** current sweep time: {current_sweep_time}")

        # Calculate Stage Velocity
        optical_step_size_um = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["step_size"])

        # The stage is at 45 degrees relative to the optical axes.
        mechanical_step_size_um = (optical_step_size_um * 2) / np.sqrt(2)

        # Calculate the actual step size in millimeters. 264 * 10^-6 mm
        mechanical_step_size_mm = mechanical_step_size_um / 1 * 10**-6

        #TODO set max speed in configuration file or get from device
        # Is this really our max speed?
        self.asi_stage.set_speed(percent=1)
        max_speed = self.asi_stage.get_speed(self.axis)
        print("Max Speed:", max_speed)
        # max_speed = 4.288497*2

        # Set the start and end position of the scan in millimeters.
        self.start_position_um = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["abs_z_start"])

        self.stop_position_um = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["abs_z_end"])

        self.number_z_steps = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["number_z_steps"])
        
        logger.info(f"*** z start position: {self.start_position_um}")
        logger.info(f"*** z end position: {self.stop_position_um}")
        logger.info(f"*** Expected number of steps: {self.number_z_steps}")
        
        # move to start position.
        self.asi_stage.move_axis_absolute(
            self.axis,
            self.start_position_um,
            wait_until_done=True)

        # Identify the minimum speed permitted by the stage, of which subsequent values
        # are multiples of.
        self.asi_stage.set_speed(percent=0.0001/max_speed)
        minimum_stage_speed = self.asi_stage.get_speed(self.axis)

        # Calculate the stage velocity in mm/seconds.
        stage_velocity_mm_per_s = mechanical_step_size_mm / current_sweep_time
        print("Desired Stage Velocity:", stage_velocity_mm_per_s)

        self.asi_stage.set_speed(percent=stage_velocity_mm_per_s/max_speed)

        stage_velocity = self.asi_stage.get_speed(self.axis)
        print("Actual Stage Velocity:", stage_velocity)

        self.expected_frames = self.number_z_steps

        # Configure the stage to operate in constant velocity mode.
        # Encoder resolution doesn't matter - we aren't using it.
        self.asi_stage.scanr(
            start_position_mm=self.start_position,
            end_position_mm=self.stop_position,
            enc_divide=10,
            axis=self.axis
        )

        # Start the stage scan.  Also get this functionality into the ASI stage class.
        self.asi_stage.start_scan(self.axis)
        self.asi_stage.stop_scan()


    def cleanup(self):
        """Clean up the constant velocity acquisition.

        Need to reset the trigger source to the default.

        """
        print("Clean up called")
        self.asi_stage.set_speed(percent=0.9)
        print("speed set")
        end_speed = self.asi_stage.get_speed(self.axis)  # mm/s
        print("end Speed = ", end_speed)
        self.asi_stage.stop()
        print("stage stop")
        self.model.active_microscope.daq.set_external_trigger(None)
        print("external trigger none")
        # return to start position
        self.asi_stage.move_absolute({f"{self.axis}_abs: {self.start_position_um}"})
        print("stage moved to original position")

