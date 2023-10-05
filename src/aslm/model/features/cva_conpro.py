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
from aslm.model.features.image_writer import ImageWriter

p = __name__.split(".")[1]
logger = logging.getLogger(p)


# Local imports


class CVACONPRO:
    """Class for acquiring data using the ASI internal encoder."""

    def __init__(self, model, axis='z', saving_flag=False, saving_dir="cva"):
        # Microscope Parameters
        self.model = model
        self.microscope_state = None

        # Stage Parameters
        self.axis = axis
        self.default_speed = None
        self.asi_stage = None

        # Acquisition Parameters
        self.stack_cycling_mode = None
        # self.channels = 1
        self.current_channel_in_list = None
        self.readout_time = None
        self.waveform_dict = None

        # Scan Parameters
        self.actual_mechanical_step_size_um = None
        self.current_sweep_time = None
        self.start_position_mm = None
        self.start_position_um = None
        self.stop_position_mm = None
        self.stop_position_um = None
        self.number_z_steps = None
        self.total_frames = None
        self.current_z_position_um = None

        # Flags
        self.end_acquisition = None

        # Counters
        self.received_frames = None

        # Saving Parameters
        self.saving_flag = saving_flag
        self.image_writer = None
        if self.saving_flag:
            self.image_writer = ImageWriter(
                model=self.model,
                sub_dir=saving_dir)

        logger.debug("Constant Velocity Acquisition Mode Initialized.")

        self.config_table = {
            "signal": {
                "init": self.pre_signal_function,
                "main": self.main_signal_function,
                "end": self.end_signal_function,
                "cleanup": self.cleanup_signal_function,
            },
            "data": {
                "init": self.pre_data_function,
                "main": self.main_data_function,
                "end": self.end_data_function,
                "cleanup": self.cleanup_data_function,
            },
            "node": {
                "node_type": "multi-step",
                "device_related": True
            },
        }

    def pre_signal_function(self):
        """Prepare the constant velocity acquisition.

        Assumes stage motion is 45 degrees relative to the optical axis.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # Get Microscope State
        self.microscope_state = self.model.configuration[
            "experiment"]["MicroscopeState"]
        self.stack_cycling_mode = self.microscope_state["stack_cycling_mode"]
        self.channels = self.microscope_state["selected_channels"]
        self.current_channel_in_list = 0
        # self.model.active_microscope.current_channel = 0
        self.asi_stage = self.model.active_microscope.stages[self.axis]

        # Configure Flags and Counters
        self.end_acquisition = False
        self.received_frames = 0
        print("**** NEW CONPRO STARTED ****")
        print(f"self.channels: {self.channels}")
        print(f"self.current_channel_in_list: {self.current_channel_in_list}")
        print(f"self.received_frames: {self.received_frames}")

        # Configure Stage
        desired_optical_step_size_um = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["step_size"])
        logger.debug(f"Desired Optical Step Size (um) {desired_optical_step_size_um}")

        self.start_position_um = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["abs_z_start"])
        self.start_position_mm = self.start_position_um / 1000.0
        logger.debug(f"Scan Start Position (mm) {self.start_position_mm}")

        self.stop_position_um = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["abs_z_end"])
        self.stop_position_mm = self.stop_position_um / 1000.0
        logger.debug(f"Scan Stop Position (mm) {self.stop_position_mm}")

        # The stage is at 45 degrees relative to the optical axes.
        desired_mechanical_step_size_um = (desired_optical_step_size_um * 2) / np.sqrt(
            2)
        desired_mechanical_step_size_mm = desired_mechanical_step_size_um / 1000
        logger.debug(f"Desired Mechanical Step Size (um) "
                     f"{desired_mechanical_step_size_um}")

        # Calculate Number of Z Steps.
        self.number_z_steps = np.ceil(
            abs(
                self.stop_position_mm - self.start_position_mm
            ) / desired_mechanical_step_size_mm
        )
        logger.debug(f"Number of Z Steps {self.number_z_steps}")
        print(f"Number of Z Steps {self.number_z_steps}")

        # Get the maximum speed for the stage.
        self.asi_stage.set_speed(percent=1)
        max_speed = self.asi_stage.get_speed(axis=self.axis)
        logger.debug(f"Axis {self.axis} Maximum Speed (mm/s): {max_speed}")

        # Get the minimum speed for the stage.
        self.asi_stage.set_speed(percent=0.0001)
        minimum_speed = self.asi_stage.get_speed(axis=self.axis)
        logger.debug(f"Axis {self.axis} Minimum Speed (mm/s): {minimum_speed}")

        # Move to start position. Move axis absolute is in units microns.
        logger.debug(f"Moving Stage to Start Position (mm): {self.start_position_mm}")

        print(f"Current Stage Position before move (um) "
              f"{self.asi_stage.get_axis_position(self.axis)}, start position = {self.start_position_um}")

        self.asi_stage.set_speed(percent=0.7)
        self.asi_stage.move_axis_absolute(
            axis=self.axis,
            abs_pos=self.start_position_um,
            wait_until_done=True)
        logger.debug(f"Current Stage Position (mm) "
                     f"{self.asi_stage.get_axis_position(self.axis) / 1000.0}")
        print(f"Current Stage Position after move (um) "
              f"{self.asi_stage.get_axis_position(self.axis)}, start position = {self.start_position_um}")

        # Configure the constant velocity/confocal projection mode

        # Calculate the readout time for the camera and microscope sweep time.
        # self.model.active_microscope.current_channel = 0
        # print(f"current_channel = {self.model.active_microscope.current_channel})")
        self.readout_time = self.model.active_microscope.get_readout_time()
        print(f"readout_time = {self.readout_time}")
        _, sweep_times = self.model.active_microscope.calculate_exposure_sweep_times(
            self.readout_time)
        print(f"sweep_times = {sweep_times}")


        channel_name = next(iter(sweep_times))
        channel_name = str(channel_name)
        channel_num = re.findall(r'[\d.]+', channel_name)
        channel_num = int(channel_num[0])
        self.model.active_microscope.current_channel = channel_num
        print(f"channel_{self.model.active_microscope.current_channel}")

        self.current_sweep_time = sweep_times[
            f"channel_{self.model.active_microscope.current_channel}"]
        print(f"current_sweep_time = {self.current_sweep_time}")
        # Get the desired speed for the stage.
        desired_speed = desired_mechanical_step_size_mm / self.current_sweep_time
        logger.debug(f"Axis {self.axis} Desired Speed (mm/s): {desired_speed}")
        print(f"desired_speed = {desired_speed}")
        self.desired_speed = desired_speed

        self.asi_stage.set_speed(velocity_dict={"X": desired_speed})
        print(f"self.desired_speed pre signal = {self.desired_speed}")
        stage_velocity = self.asi_stage.get_speed(axis=self.axis)
        logger.debug(f"Axis {self.axis} Actual Speed (mm/s): {stage_velocity}")
        print(f"actual speed = {stage_velocity}")
        # Inaccurate velocity results in inaccurate step size.
        # Update the Microscope/Configuration to record the actual step size
        actual_mechanical_step_size_mm = stage_velocity * self.current_sweep_time
        self.actual_mechanical_step_size_um = actual_mechanical_step_size_mm * 1000
        self.desired_mechanical_step_size_mm = desired_mechanical_step_size_mm
        new_z_steps = np.floor(
            abs(self.stop_position_um - self.start_position_um) / self.actual_mechanical_step_size_um)
        print(
            f"self.desired_mechanical_step_size_mm pre signal = {self.desired_mechanical_step_size_mm}")
        print(
            f"self.actual_mechanical_step_size_mm pre signal = {self.actual_mechanical_step_size_um}")
        print(
            f"new_z_steps = {new_z_steps}, self.number_z_steps_set = {self.number_z_steps}")

        self.new_z_steps = new_z_steps
        actual_optical_step_size_mm = actual_mechanical_step_size_mm * np.sqrt(2) / 2
        actual_optical_step_size_um = actual_optical_step_size_mm * 1000
        logger.debug(f"Axis {self.axis} Actual Mechanical Step Size (mm): "
                     f"{actual_mechanical_step_size_mm}")
        logger.debug(f"Axis {self.axis} Actual Optical Step Size (um): "
                     f"{actual_optical_step_size_um}")

        self.model.configuration[
            "experiment"]["MicroscopeState"]["waveform_template"] = "CVACONPRO"
        self.model.configuration[
            "waveform_templates"]["CVACONPRO"]["expand"] = int(self.new_z_steps)
        self.model.configuration[
            "waveform_templates"]["CVACONPRO"]["repeat"] = int(1)
        print("CVACONPRO waveform template configured")
        print(f"current channel = {self.model.active_microscope.current_channel}")

        self.repeat_waveform = self.model.configuration["waveform_templates"]["CVACONPRO"]["repeat"]
        self.expand_waveform = self.model.configuration["waveform_templates"]["CVACONPRO"]["expand"]
        print(f"repeat num cva = {self.repeat_waveform}")
        print(f"expand num cva = {self.expand_waveform}")

        # Set filter, exposure time, and prepare acquisition in daq

        # self.model.active_microscope.prepare_next_channel()
        # print("channel prepared v2")
        self.model.active_microscope.current_channel = 0
        print(f"current channel = {self.model.active_microscope.current_channel}")
        print(f"channel set to 0")
        self.waveform_dict = self.model.active_microscope.calculate_all_waveform()
        # print(f"waveforms calculated = {self.waveform_dict}")
        self.model.active_microscope.prepare_next_channel()
        print("channel prepared after model")
        self.model.active_microscope.daq.set_external_trigger("/PXI6259/PFI1")
        print(f"external trigger set to {self.model.active_microscope.daq.external_trigger}")



        # print(f"current channel = {self.model.active_microscope.current_channel}")
        # print("channel prepared")


        # Configure the constant velocity scan.
        self.asi_stage.scanr(
            start_position_mm=self.start_position_mm,
            end_position_mm=self.stop_position_mm,
            enc_divide=actual_mechanical_step_size_mm,
            # enc_divide=self.desired_mechanical_step_size_mm,
            axis=self.axis
        )

        self.current_z_position_um = self.start_position_um
        self.end_signal_temp = 0

    def main_signal_function(self):
        print("main function called")
        if self.end_acquisition:
            return False

        self.asi_stage.start_scan(self.axis)
        print("main function stage scan started")
        return True

    def end_signal_function(self):
        self.end_signal_temp += 1
        # if self.model.stop_acquisition:
        #     return True
        #
        # # Should estimate the current position here.
        # self.current_z_position_um += self.actual_mechanical_step_size_um
        #
        # if self.model.stop_acquisition or self.end_acquisition:
        #     print("end_signal_function: Stop acquisition.")
        #     return True
        # else:
        #     print("end_signal_function: Continue acquisition.")
        #     return False
        # if done with all the channels,
        # set the channel back to 0, run prepare next channel, set external trigger.
        # Configure the constant velocity/confocal projection mode

        print("end signal function called")
        print(f"self.end_acquisition ={self.end_acquisition}")
        print(f"self.model.stop_acquisition = {self.model.stop_acquisition}")
        print(f"self.end_signal_temp = {self.end_signal_temp}")
        # pos = self.asi_stage.get_axis_position(self.axis)
        # print(f"end signal end pos = {pos}, stop position = {self.stop_position_um}, start position = {self.start_position_um}")

        if self.end_acquisition or self.model.stop_acquisition or self.end_signal_temp > 0:
            pos = self.asi_stage.get_axis_position(self.axis)
            print(
                f"end signal end pos = {pos}, stop position = {self.stop_position_um}, start position = {self.start_position_um}")
            self.model.configuration[
                "experiment"]["MicroscopeState"]["waveform_template"] = "Default"
            print("emd signal config set to default")
            self.model.active_microscope.current_channel = 0
            print(
                f"end signal self.model.active_microscope.current_channel = {self.model.active_microscope.current_channel})")
            self.model.active_microscope.daq.external_trigger = None
            print("end signal external trigger set to none")
            self.model.active_microscope.prepare_next_channel()
            return True
        # if self.end_acquisition or self.model.stop_acquisition or self.end_signal_temp>0:
        #     print("end acquisition statements True")
        #     if self.stack_cycling_mode == "per_stack":
        #         print(f"self.current_channel_in_list = {self.current_channel_in_list}")
        #         print(f"self.channels {self.channels}")
        #         print("stack cycling mode = per stack")
        #         # self.model.active_microscope.current_channel = 0
        #         # self.model.active_microscope.prepare_next_channel()
        #         # self.model.active_microscope.daq.set_external_trigger()
        #         self.update_channel()
        #         print("update channel ended")
        #         if self.current_channel_in_list == 0:
        #             print("current channel in list = 0")
        #             # Reset the settings - This should only be done after the last channel.
        #             self.model.configuration[
        #                 "experiment"]["MicroscopeState"]["waveform_template"] = "Default"
        #             # self.model.active_microscope.current_channel = 0
        #
        #             # self.model.active_microscope.prepare_next_channel()
        #             # self.model.active_microscope.daq.set_external_trigger()
        #             return True
        #         else:
        #             print("current channel in list != 0")
        #             return True
        # else:
        #     print("if else true statement")
        #     return True

    def update_channel(self):
        print("update channel called")
        print(f"channel before in update channel list = {self.current_channel_in_list}")
        self.current_channel_in_list = (
                                                   self.current_channel_in_list + 1) % self.channels
        # self.received_frames = 0
        print(f"channel after in update channel = {self.channels}")
        print(f"channel after in update channel list = {self.current_channel_in_list}")
        # self.pre_signal_function()
        # self.main_signal_function()
        self.asi_stage.set_speed(percent=0.7)
        self.asi_stage.move_axis_absolute(
            axis=self.axis,
            abs_pos=self.start_position_um,
            wait_until_done=True)
        print("stage moved to start position")
        self.model.configuration[
            "experiment"]["MicroscopeState"]["waveform_template"] = "CVACONPRO"
        self.model.configuration[
            "waveform_templates"]["CVACONPRO"]["expand"] = int(self.new_z_steps)
        self.model.configuration[
            "waveform_templates"]["CVACONPRO"]["repeat"] = int(1)
        print("waveform template set")
        self.model.active_microscope.prepare_next_channel()
        print("channel prepared")
        # self.model.active_microscope.daq.set_external_trigger("/PXI6259/PFI1")
        print("external trigger set")
        print(f"self.desired_speed = {self.desired_speed}")
        self.asi_stage.set_speed(velocity_dict={"X": self.desired_speed})
        print("stage speed set")
        print(
            f"self.desired_mechanical_step_size_mm = {self.desired_mechanical_step_size_mm}")
        self.asi_stage.scanr(
            start_position_mm=self.start_position_mm,
            end_position_mm=self.stop_position_mm,
            enc_divide=self.desired_mechanical_step_size_mm,
            axis=self.axis
        )
        # self.main_signal_function()
        self.asi_stage.start_scan(self.axis)
        print("stage scan started")

    def cleanup_signal_function(self):
        print("Clean up signal function called")
        pos = self.asi_stage.get_axis_position(self.axis)
        print(
            f"cleanup end pos = {pos}, stop position = {self.stop_position_um}, start position = {self.start_position_um}")
        self.asi_stage.set_speed(percent=0.7)
        self.model.configuration[
            "experiment"]["MicroscopeState"]["waveform_template"] = "Default"
        print("config set to default")
        self.model.active_microscope.current_channel = 0
        print(
            f"self.model.active_microscope.current_channel = {self.model.active_microscope.current_channel})")
        self.model.active_microscope.daq.external_trigger = None
        print("external trigger set to none")
        self.model.active_microscope.prepare_next_channel()
        # self.model.active_microscope.daq.set_external_trigger(None)
        """Clean up the constant velocity acquisition.

        Moves the stage back to the start position and resets the trigger
        source.

        """

        return True

    def pre_data_function(self):
        """Prepare the constant velocity acquisition.

        Sets the number of frames to receive and the total number of frames.
        """
        self.total_frames = self.channels * self.number_z_steps

    def main_data_function(self, frame_ids):
        """Process the data from the constant velocity acquisition.

        Writes data to disk.

        Parameters
        ----------
        frame_ids : list
            List of frame ids received from the camera.
        """

        self.received_frames += len(frame_ids)
        if self.saving_flag:
            self.image_writer.write_frames(frame_ids)

    def end_data_function(self):
        """Evaluate end condition for constant velocity acquisition.

        Returns
        -------
        bool
            True if the acquisition is complete, False otherwise.
        """
        pos = self.asi_stage.get_axis_position(self.axis)
        print(f"pos = {pos}, stop position = {self.stop_position_um}")
        print(
            f"self.received_frames = {self.received_frames}, self.number_z_steps = {self.new_z_steps}")
        logger.info(f"pos = {pos}, stop position = {self.stop_position_um}")
        logger.info(
            f"self.received_frames = {self.received_frames}, self.number_z_steps = {self.new_z_steps}")
        
        if self.received_frames >= self.new_z_steps:
            self.end_acquisition = True
            self.model.stop_acquisition = True
            logger.debug("Constant Velocity Acquisition Complete")
            print(f"end acquisition = {self.end_acquisition}")
            # self.asi_stage.wait_until_complete()
            return True
        return False

    def cleanup_data_function(self):
        """Clean up the constant velocity acquisition.

        Designed to be called in the case of a failure.
        Do not rely on this function being called.

        Cleans up the image writer.
        """
        print("clean up data function called")
        if self.saving_flag:
            self.image_writer.cleanup()
