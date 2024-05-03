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
import logging

# Third Party Imports
import numpy as np
from navigate.model.features.image_writer import ImageWriter


p = __name__.split(".")[1]
logger = logging.getLogger(p)

# Local imports


class ConstantVelocityAcquisition:
    def __init__(self, model, axis="z", saving_flag=False, saving_dir="cva"):
        self.model = model

        self.axis = axis
        self.default_speed = None
        self.asi_stage = None
        self.saving_flag = saving_flag

        self.image_writer = None
        if self.saving_flag:
            self.image_writer = ImageWriter(model=self.model, sub_dir=saving_dir)

        self.config_table = {
            "signal": {
                "init": self.pre_func_signal,
                "main": self.main_func_signal,
                "end": self.end_func_signal,
                "cleanup": self.cleanup,
            },
            "data": {
                "init": self.pre_data_func,
                "main": self.in_data_func,
                "end": self.end_data_func,
                "cleanup": self.cleanup_data_function,
            },
            "node": {"node_type": "multi-step", "device_related": True},
        }

    def pre_func_signal(self):
        """Prepare the constant velocity acquisition.

        Injects a new trigger source and prepares the stage for a constant
        scan velocity mode. All tasks are triggered by the ASI stage
        encoder. Only operates in a per-stack acquisition mode.  Stage
        velocity is calculated based on the current exposure time,
        step size, and minimum encoder divide.

        Rotary encoder has a resolution of 45,396 counts/mm, or 1 count per
        10 nm. It is a quadrature device, so the minimum step size is 40 nm.

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

        # get the current exposure time for channel channel.
        (
            exposure_times,
            sweep_times,
        ) = self.model.active_microscope.calculate_exposure_sweep_times()
        channel_name = next(iter(sweep_times))

        channel_num = int(channel_name.split("_")[1])
        self.model.active_microscope.current_channel = channel_num
        current_sweep_time = sweep_times[
            f"channel_{self.model.active_microscope.current_channel}"
        ]
        current_expsure_time = exposure_times[
            f"channel_{self.model.active_microscope.current_channel}"
        ]
        self.current_sweep_time = current_sweep_time
        self.current_exposure_time = current_expsure_time
        scaling_factor = 1

        # Provide just a bit of breathing room for the sweep time...
        current_sweep_time = current_sweep_time * scaling_factor

        logger.info(f"*** current sweep time: {current_sweep_time}")
        logger.info(f"*** sweep time scaling: {scaling_factor}")

        # Calculate Stage Velocity
        encoder_resolution = 10  # nm
        minimum_encoder_divide = encoder_resolution * 4  # nm

        # Get step size from the GUI. For now, assume 160 nm.
        # Default units should probably be microns I believe. Confirm.
        # desired_sampling = 160  # nm
        desired_sampling = (
            float(
                self.model.configuration["experiment"]["MicroscopeState"]["step_size"]
            )
            * 1000.0
        )

        desired_sampling_um = float(
            self.model.configuration["experiment"]["MicroscopeState"]["step_size"]
        )

        logger.info(f"*** step size um: {desired_sampling_um}")

        # The stage is at 45 degrees relative to the optical axes.
        step_size = (desired_sampling * 2) / np.sqrt(2)  # 45 degrees, 226 nm

        # Calculate the desired encoder divide. Must be multiple of
        # minimum_encoder_divide. 2.6 encoder divides, round up to 3.
        desired_encoder_divide = np.ceil(step_size / minimum_encoder_divide)
        # Calculate the actual step size in nanometers. 264 nm.
        step_size_nm = desired_encoder_divide * minimum_encoder_divide

        # Calculate the actual step size in millimeters. 264 * 10^-6 mm
        step_size_mm = step_size_nm * 10**-6  # 264 * 10^-6 mm

        # Set the start and end position of the scan in millimeters.
        # Retrieved from the GUI.
        # Set Stage Limits - Units in millimeters
        # microns to mm
        self.start_position = (
            float(
                self.model.configuration["experiment"]["MicroscopeState"]["abs_z_start"]
            )
            / 1000.0
        )
        self.stop_position = (
            float(
                self.model.configuration["experiment"]["MicroscopeState"]["abs_z_end"]
            )
            / 1000.0
        )
        self.number_z_steps = float(
            self.model.configuration["experiment"]["MicroscopeState"]["number_z_steps"]
        )

        self.start_position_um = self.start_position * 1000
        self.stop_position_um = self.stop_position * 1000

        logger.info(f"*** z start position: {self.start_position}")
        logger.info(f"*** z end position: {self.stop_position}")
        logger.info(f"*** Expected number of steps: {self.number_z_steps}")
        self.step_size_mm = step_size_mm
        self.asi_stage.scanr(
            start_position_mm=self.start_position,
            end_position_mm=self.stop_position,
            enc_divide=self.step_size_mm,
            axis=self.axis,
        )

        self.asi_stage.wait_until_complete(self.axis)
        self.asi_stage.set_speed(percent=1)
        max_speed = self.asi_stage.get_speed(axis=self.axis)
        logger.debug(f"Axis {self.axis} Maximum Speed (mm/s): {max_speed}")
        self.asi_stage.set_speed(percent=0.0001 / max_speed)
        expected_speed = step_size_mm / current_sweep_time
        self.expected_speed = expected_speed
        self.max_speed = max_speed
        self.percent_speed = self.expected_speed / self.max_speed

        self.asi_stage.set_speed(percent=expected_speed / max_speed)
        stage_velocity = self.asi_stage.get_speed(self.axis)
        logger.info(f"*** Expected stage velocity, (mm/s): {expected_speed}")
        logger.info(f"*** Final stage velocity, (mm/s): {stage_velocity}")

        actual_mechanical_step_size_mm = stage_velocity * self.current_sweep_time
        self.actual_mechanical_step_size_um = actual_mechanical_step_size_mm * 1000

        expected_frames = int(
            np.ceil(
                abs(self.start_position - self.stop_position)
                / stage_velocity
                / current_sweep_time
            )
        )
        logger.info(f"*** Expected Frames: {expected_frames}")
        self.model.configuration["experiment"]["MicroscopeState"][
            "waveform_template"
        ] = "CVACONPRO"
        self.model.configuration["waveform_templates"]["CVACONPRO"][
            "expand"
        ] = expected_frames
        self.model.configuration["waveform_templates"]["CVACONPRO"]["repeat"] = 1

        self.repeat_waveform = self.model.configuration["waveform_templates"][
            "CVACONPRO"
        ]["repeat"]
        self.expand_waveform = self.model.configuration["waveform_templates"][
            "CVACONPRO"
        ]["expand"]

        expand_frames = float(
            self.model.configuration["waveform_templates"]["CVACONPRO"]["expand"]
        )
        self.expected_frames = expected_frames
        # np.ceil(expected_frames/(self.repeat_waveform*self.expand_waveform))

        logger.info(f"Self Expected Frames test = {self.expected_frames}")
        logger.info(f"Expand Frames = {expand_frames}")
        self.model.configuration["experiment"]["MicroscopeState"][
            "number_z_steps"
        ] = expected_frames

        # Updates metadata for saving each channel with the correct number of frames
        # self.file_type = self.model.configuration["experiment"]["Saving"]["file_type"]
        # self.data_source = data_sources.get_data_source(self.file_type)
        # self.data_source.set_metadata_from_configuration_experiment(self.model.configuration)

        self.model.active_microscope.current_channel = 0
        self.waveform_dict = self.model.active_microscope.calculate_all_waveform()
        self.model.active_microscope.daq.external_trigger = "/PXI6259/PFI1"
        self.model.active_microscope.prepare_next_channel()
        self.model.resume_data_thread()

    def main_func_signal(self):
        self.asi_stage.set_speed(percent=self.percent_speed)
        self.asi_stage.start_scan(self.axis)

    def end_func_signal(self):

        if self.model.stop_acquisition:
            return True

        self.end_signal_temp += 1
        if (
            self.model.stop_acquisition
            or self.end_acquisition
            or self.end_signal_temp > 0
        ):
            if self.stack_cycling_mode == "per_stack":
                self.update_channel()
                # if run through all the channels, move to next position
                if self.current_channel_in_list == 0:
                    return True
            else:
                return True

        return False

    def update_channel(self):
        self.current_channel_in_list = (
            self.current_channel_in_list + 1
        ) % self.channels
        self.asi_stage.wait_until_complete(self.axis)

        if self.current_channel_in_list > 0:
            self.model.pause_data_thread()

        self.asi_stage.set_speed(percent=0.5)
        self.asi_stage.wait_until_complete(self.axis)

        if self.current_channel_in_list == 0:
            return True

        self.asi_stage.set_speed(percent=self.percent_speed)
        self.model.active_microscope.prepare_next_channel()
        self.model.resume_data_thread()

    def cleanup(self):
        """Clean up the constant velocity acquisition.

        Need to reset the trigger source to the default.

        """
        self.asi_stage.set_speed(percent=0.5)
        self.asi_stage.stop()

        self.asi_stage.wait_until_complete(self.axis)
        self.model.active_microscope.daq.stop_acquisition()
        self.model.configuration["experiment"]["MicroscopeState"][
            "waveform_template"
        ] = "Default"
        self.model.active_microscope.current_channel = 0
        self.model.active_microscope.daq.external_trigger = None

    def pre_data_func(self):
        self.received_frames_v2 = self.received_frames
        self.total_frames = self.expected_frames * self.channels

    def in_data_func(self, frame_ids):
        self.received_frames += len(frame_ids)
        if self.image_writer is not None:
            self.image_writer.save_image(frame_ids)

    def end_data_func(self):
        pos = self.asi_stage.get_axis_position(self.axis)
        expected_channel = self.expected_frames * (self.end_signal_temp + 1)
        logger.info(
            f"Received: {self.received_frames} Per Channel: {expected_channel} "
            f"Expected Total: {self.total_frames}"
        )
        logger.info(f"Position: {pos} Stop Position: {self.stop_position*1000} ")
        self.end_acquisition = self.received_frames >= self.total_frames
        return self.end_acquisition

    def cleanup_data_function(self):
        """Clean up the constant velocity acquisition.

        Designed to be called in the case of a failure.
        Do not rely on this function being called.

        Cleans up the image writer.
        """
        if self.image_writer:
            self.image_writer.cleanup()
