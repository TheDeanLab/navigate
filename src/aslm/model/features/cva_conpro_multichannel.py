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
import re 

p = __name__.split(".")[1]
logger = logging.getLogger(p)

# Local imports


class CVACONPROMULTICHANNEL:
    """Class for acquiring data using the ASI internal encoder."""

    def __init__(self, model, axis='z'):
        self.model = model
        self.axis = axis
        self.default_speed = None
        self.asi_stage = None
        self.stack_cycling_mode = None
        self.channels = None
        self.current_channel_in_list = None
        self.end_acquisition = None
        self.received_frames = None
        self.end_signal_temp = None
        self.current_sweep_time = None
        self.readout_time = None
        self.start_position_mm = None
        self.start_position_um = None
        self.stop_position_mm = None
        self.stop_position_um = None
        self.number_z_steps = None
        self.waveform_dict = None
        logger.debug("Beginning Constant Velocity Acquisition Mode")

        self.config_table = {
            "signal": {
                "init": self.pre_func_signal,
                "end": self.end_func_signal,
                "cleanup": self.cleanup,
            },
            "data": {
                "init": self.pre_data_func,
                "main": self.in_data_func,
                "end": self.end_data_func,
            },
            "node": {
                "node_type": "multi-step",
                "device_related": True
            },
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

        self.asi_stage = self.model.active_microscope.stages[self.axis]
        microscope_state = self.model.configuration["experiment"]["MicroscopeState"]
        self.stack_cycling_mode = microscope_state["stack_cycling_mode"]
        self.channels = microscope_state["selected_channels"]
        self.current_channel_in_list = 0
        self.end_acquisition = False
        self.received_frames = 0
        self.end_signal_temp = 0

        # GET PARAMETERS FROM GUI
        desired_optical_step_size_um = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["step_size"])
        logger.debug(f"Desired Optical Step Size (um) {desired_optical_step_size_um}")

        # Start Position
        self.start_position_um = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["abs_z_start"])
        self.start_position_mm = self.start_position_um / 1000.0
        logger.debug(f"Scan Start Position (mm) {self.start_position_mm}")

        # Stop Position
        self.stop_position_um = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["abs_z_end"])
        self.stop_position_mm = self.stop_position_um / 1000.0
        logger.debug(f"Scan Stop Position (mm) {self.stop_position_mm}")

        # CALCULATE OBLIQUE SCAN PARAMETERS
        # The stage is at 45 degrees relative to the optical axes.
        desired_mechanical_step_size_um = (desired_optical_step_size_um * 2) / np.sqrt(2)
        desired_mechanical_step_size_mm = desired_mechanical_step_size_um / 1000
        logger.debug(f"Desired Mechanical Step Size (um) "
                     f"{desired_mechanical_step_size_um}")

        # Calculate Number of Z Steps.
        self.number_z_steps = np.floor(
                abs(
                    self.stop_position_mm - self.start_position_mm
                ) / desired_mechanical_step_size_mm
            )
        logger.debug(f"Number of Z Steps {self.number_z_steps}")

        # Get the maximum speed for the stage.
        self.asi_stage.set_speed(percent=1)
        max_speed = self.asi_stage.get_speed(self.axis)
        logger.debug(f"Axis {self.axis} Maximum Speed (mm/s): {max_speed}")

        # Get the minimum speed for the stage.
        self.asi_stage.set_speed(percent=0.0001)
        minimum_speed = self.asi_stage.get_speed(self.axis)
        logger.debug(f"Axis {self.axis} Minimum Speed (mm/s): {minimum_speed}")

        # Move to start position. Move axis absolute is in units microns.
        logger.debug(f"Moving Stage to Start Position (mm): {self.start_position_mm}")
        self.asi_stage.set_speed(percent=0.7)
        self.asi_stage.move_axis_absolute(
            self.axis,
            self.start_position_um,
            wait_until_done=True
        )
        logger.debug(f"Current Stage Position (mm) "
                     f"{self.asi_stage.get_axis_position(self.axis) / 1000.0}")

        # Configure the constant velocity/confocal projection mode
        self.model.configuration[
            "experiment"]["MicroscopeState"]["waveform_template"] = "CVACONPRO"
        self.model.configuration[
            "waveform_templates"]["CVACONPRO"]["expand"] = int(self.number_z_steps)
        self.model.configuration[
            "waveform_templates"]["CVACONPRO"]["repeat"] = int(1)

        # Get Readout time,exposure time, and sweep time.

        # Call prepare_acquisition in the model.
        # Sets flags, stops the stage, and calls prepare_acquisition in
        # the active microscope.
        # self.model.prepare_acquisition()

        # microscope.prepare_acquisition
        # sets current channel to 0, initializes image series,
        # calculates all waveforms.
        self.model.active_microscope.current_channel = 0
        self.model.active_microscope.calculate_all_waveform()
        self.model.active_microscope.prepare_next_channel()
        # prepare next channel should specify current channel as the first available.
        # sets filter, exposure time, and calls prepare acquisition in daq

        self.readout_time = self.model.active_microscope.get_readout_time()
        # calls the camera and gets the readout time

        _, sweep_times = self.model.active_microscope.calculate_exposure_sweep_times(
            self.readout_time
        )

        self.current_sweep_time = sweep_times[
            f"channel_{self.model.active_microscope.current_channel}"
        ]

        # Get the desired speed for the stage.
        desired_speed = desired_mechanical_step_size_mm / self.current_sweep_time
        logger.debug(f"Axis {self.axis} Desired Speed (mm/s): {desired_speed}")

        self.asi_stage.set_speed(velocity_dict={"X": desired_speed})
        stage_velocity = self.asi_stage.get_speed(self.axis)
        logger.debug(f"Axis {self.axis} Actual Speed (mm/s): {stage_velocity}")

        # Inaccurate velocity results in inaccurate step size.
        # We should convert from mechanical dimensions to optical dimensions, and update
        # the MicroscopeStateWe should record the actual step size
        actual_mechanical_step_size_mm = stage_velocity / self.current_sweep_time

        # Configure the constant velocity scan.
        self.asi_stage.scanr(
            start_position_mm=self.start_position_mm,
            end_position_mm=self.stop_position_mm,
            enc_divide=desired_mechanical_step_size_mm,
            axis=self.axis
        )

        # Start the stage scan.
        self.asi_stage.start_scan(self.axis)

        # Wait until complete
        self.asi_stage.wait_until_complete()

    def end_func_signal(self):
        self.end_signal_temp += 1
        if self.model.stop_acquisition or self.end_acquisition or self.end_signal_temp>0:
            if self.stack_cycling_mode == "per_stack":
                self.update_channel()
                if self.current_channel_in_list == 0:
                    self.cleanup()
                    return True
            else:
                return True
        return False

    def update_channel(self):
        self.current_channel_in_list = (self.current_channel_in_list + 1) % self.channels
        self.received_frames = 0

        # Move axis absolute - units in microns.
        self.asi_stage.move_axis_absolute(
            self.axis,
            self.start_position_um,
            wait_until_done=True
        )
        self.model.active_microscope.prepare_next_channel()
        self.asi_stage.start_scan(self.axis)
        self.asi_stage.stop_scan()

    def cleanup(self):
        """Clean up the constant velocity acquisition.

        Need to reset the trigger source to the default.

        """
        self.asi_stage.set_speed(percent=0.9)
        self.asi_stage.stop()
        self.asi_stage.move_axis_absolute(
            self.axis,
            self.start_position_um,
            wait_until_done=True
        )

    def pre_data_func(self):
        pass
        #self.received_frames_v2 = self.received_frames

    def in_data_func(self, frame_ids):
        self.received_frames += len(frame_ids)

    def end_data_func(self):
        # pos = self.asi_stage.get_axis_position(self.axis)
        self.end_acquisition = self.received_frames >= self.number_z_steps
        return self.end_acquisition
