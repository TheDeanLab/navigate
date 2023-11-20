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
# from aslm.model import data_sources
# from aslm.model.data_sources import data_source
# # from aslm.model.data_sources import D
# import os


p = __name__.split(".")[1]
logger = logging.getLogger(p)

# Local imports


class CVACONPRO:
    def __init__(self, model, axis='z', saving_flag=False, saving_dir="cva"):
        self.model = model


        self.axis = axis
        self.default_speed = None
        self.asi_stage = None
        self.saving_flag = saving_flag
        
        self.image_writer = None
        if self.saving_flag:
            self.image_writer = ImageWriter(
                model=self.model,
                sub_dir=saving_dir)
            
            

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
                "cleanup":self.cleanup_data_function,
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
        
        print("**** CVA TTL STARTED pre signal func initiated****") 
        self.asi_stage = self.model.active_microscope.stages[self.axis]
        microscope_state = self.model.configuration["experiment"]["MicroscopeState"]
        self.stack_cycling_mode = microscope_state["stack_cycling_mode"]
        self.channels = microscope_state["selected_channels"]
        self.current_channel_in_list = 0
        print(f"current channel = {self.channels}")

        self.end_acquisition = False
        self.received_frames = 0
        self.end_signal_temp = 0


        # get the current exposure time for channel channel.
        readout_time = self.model.active_microscope.get_readout_time()
        print("readout time calculated")
        print(f"*** readout time = {readout_time} s")
        exposure_times, sweep_times = self.model.active_microscope.calculate_exposure_sweep_times(readout_time)
        print("sweep times and exposure times calculated")
        print(f"exposure time = {exposure_times}")
        print(f"sweep time = {sweep_times}")
        channel_name = next(iter(sweep_times))
        channel_name = str(channel_name)
        channel_num = re.findall(r'[\d.]+',channel_name)
        channel_num = int(channel_num[0])
        self.model.active_microscope.current_channel = channel_num
        print(f"channel_{self.model.active_microscope.current_channel}")
        current_sweep_time = sweep_times[f"channel_{self.model.active_microscope.current_channel}"]
        current_expsure_time = exposure_times[f"channel_{self.model.active_microscope.current_channel}"]
        self.current_sweep_time = current_sweep_time
        self.current_exposure_time = current_expsure_time
        self.readout_time = readout_time
        print("sweep time calculated")
        scaling_factor = 1
        print("*** current sweep time before scaling:", current_sweep_time)

        # Provide just a bit of breathing room for the sweep time...
        current_sweep_time = current_sweep_time * scaling_factor
        
        print("*** current sweep time after scaling:", current_sweep_time)
        print(f"*** Scaling Factor = {scaling_factor}")
        logger.info(f"*** current sweep time: {current_sweep_time}")
        logger.info(f"*** sweep time scaling: {scaling_factor}")
        
        # Calculate Stage Velocity
        encoder_resolution = 10 # nm
        minimum_encoder_divide = encoder_resolution*4 # nm

        # Get step size from the GUI. For now, assume 160 nm.
        # Default units should probably be microns I believe. Confirm.
        # desired_sampling = 160  # nm
        desired_sampling = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["step_size"]) * 1000.0
        
        desired_sampling_um = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["step_size"])
        
        print("*** step size um:", desired_sampling_um)
        logger.info(f"*** step size um: {desired_sampling_um}")
    
        # The stage is at 45 degrees relative to the optical axes.
        step_size = (desired_sampling * 2) / np.sqrt(2)  # 45 degrees, 226 nm
        print("Desired Axial Sampling:", desired_sampling)
        print("Desired Step Size of Stage:", step_size)

        # Calculate the desired encoder divide. Must be multiple of
        # minimum_encoder_divide. 2.6 encoder divides, round up to 3.
        # *** WHY IS THIS DIVIDE BY 2? TO CORRECT STEP SIZE ABOVE?
        desired_encoder_divide = np.ceil(step_size / minimum_encoder_divide)
        print("*** desired encoder divide:", desired_encoder_divide)
        # Calculate the actual step size in nanometers. 264 nm.
        step_size_nm = desired_encoder_divide * minimum_encoder_divide
        print("Actual Step Size of Stage:", step_size_nm)

        # Calculate the actual step size in millimeters. 264 * 10^-6 mm
        step_size_mm = step_size_nm / 1 * 10**-6  # 264 * 10^-6 mm
        #TODO set max speed in configuration file
        # max_speed = 4.288497*2

        

        # Set the start and end position of the scan in millimeters.
        # Retrieved from the GUI.
        # Set Stage Limits - Units in millimeters
        # microns to mm
        self.start_position = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["abs_z_start"]) / 1000.0
        self.stop_position = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["abs_z_end"]) / 1000.0
        self.number_z_steps = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["number_z_steps"])
        
        self.start_position_um = self.start_position*1000
        self.stop_position_um = self.stop_position*1000
        
        logger.info(f"*** z start position: {self.start_position}")
        logger.info(f"*** z end position: {self.stop_position}")
        logger.info(f"*** Expected number of steps: {self.number_z_steps}")
        pos = self.asi_stage.get_axis_position(self.axis)
        print(f"Current Position = {pos}")
        print(f"Start position = {self.start_position*1000}")
        
        self.step_size_mm = step_size_mm
        self.asi_stage.scanr(
            start_position_mm=self.start_position,
            end_position_mm=self.stop_position,
            enc_divide=self.step_size_mm,
            axis=self.axis
            )
        print("scan r initalized update channel")
        
        self.asi_stage.wait_until_complete(self.axis)
        print("Stage wait until complete completed after scanr")

        #TODO set max speed in configuration file
        # max_speed = 4.288497*2
        self.asi_stage.set_speed(percent=1)
        max_speed = self.asi_stage.get_speed(axis=self.axis)
        print(f"Axis {self.axis} Maximum Speed (mm/s): {max_speed}")
        logger.debug(f"Axis {self.axis} Maximum Speed (mm/s): {max_speed}")


        
        self.asi_stage.set_speed(percent=0.0001/max_speed)
        basic_speed = self.asi_stage.get_speed(self.axis)  # mm/s
        print("Basic Speed = ",basic_speed)

        expected_speed = step_size_mm / current_sweep_time
        print("Expected velocity = ",expected_speed)

        self.expected_speed = expected_speed
        self.max_speed = max_speed
        self.percent_speed = self.expected_speed/self.max_speed

        self.asi_stage.set_speed(percent=expected_speed/max_speed)
        stage_velocity = self.asi_stage.get_speed(self.axis)
        print("Final stage velocity, (mm/s):", stage_velocity)
        print("Encoder divide step size = ",step_size_mm)
        logger.info(f"*** Expected stage velocity, (mm/s): {expected_speed}")
        logger.info(f"*** Final stage velocity, (mm/s): {stage_velocity}")

        actual_mechanical_step_size_mm = stage_velocity * self.current_sweep_time
        self.actual_mechanical_step_size_um = actual_mechanical_step_size_mm * 1000
        # self.desired_mechanical_step_size_mm = desired_mechanical_step_size_mm
        new_z_steps = np.floor(
            abs(self.stop_position_um - self.start_position_um) / self.actual_mechanical_step_size_um)
        

        expected_frames_v1 = np.ceil(((new_z_steps * step_size_mm)/stage_velocity)/current_sweep_time)
        expected_frames = int(np.ceil(abs(self.start_position - self.stop_position)/stage_velocity/current_sweep_time))
        print(f"*** Expected Frames from zsteps:{expected_frames_v1}")
        print(f"*** Expected Frames from start and stop position: {expected_frames}")
        print(f"*** new_z_steps = {new_z_steps}")
        logger.info(f"*** Expected Frames: {expected_frames}")
        self.model.configuration["experiment"]["MicroscopeState"]["waveform_template"] = "CVACONPRO"
        self.model.configuration["waveform_templates"]["CVACONPRO"]["expand"] = expected_frames
        self.model.configuration["waveform_templates"]["CVACONPRO"]["repeat"] = 1

        self.repeat_waveform = self.model.configuration["waveform_templates"]["CVACONPRO"]["repeat"]
        self.expand_waveform = self.model.configuration["waveform_templates"]["CVACONPRO"]["expand"]
        print(f"repeat num = {self.repeat_waveform}")
        print(f"expand num = {self.expand_waveform}")
        Expand_frames = float(self.model.configuration["waveform_templates"]["CVACONPRO"]["expand"])
        self.expected_frames = expected_frames  # np.ceil(expected_frames/(self.repeat_waveform*self.expand_waveform))
        print("waveforms obtained from config")
        print(f"Expand Frames = {Expand_frames}")
        print(f"Self Expected Frames test = {self.expected_frames}")
        logger.info(f"Self Expected Frames test = {self.expected_frames}")
        logger.info(f"Expand Frames = {Expand_frames}") 
        self.model.configuration["experiment"]["MicroscopeState"]["number_z_steps"] = expected_frames
        
        # Updates metadata for saving each channel with the correct number of frames
        # self.file_type = self.model.configuration["experiment"]["Saving"]["file_type"]
        # self.data_source = data_sources.get_data_source(self.file_type)
        # self.data_source.set_metadata_from_configuration_experiment(self.model.configuration)   
        
        self.model.active_microscope.current_channel = 0
        self.waveform_dict = self.model.active_microscope.calculate_all_waveform()
        # #   ms calculated v2 {self.waveform_dict}")
        self.model.active_microscope.daq.external_trigger = "/PXI6259/PFI1"
        print(f"external trigger set to {self.model.active_microscope.daq.external_trigger}")
        self.model.active_microscope.prepare_next_channel()
        
        posw = self.asi_stage.get_axis_position(self.axis)
        print(f"current position = {posw}, start position = {self.start_position_um}")
            
        self.model.resume_data_thread()
        print("DATA THREAD RESUMED")
        
    def main_func_signal(self):
        print("main function started")
        self.asi_stage.set_speed(percent=self.percent_speed)
        print("original stage speed set")
        posw = self.asi_stage.get_axis_position(self.axis)
        print(f"current position = {posw}, start position = {self.start_position_um}")
        self.asi_stage.start_scan(self.axis)
        print("scan started")
 
    def end_func_signal(self):
        print("in end_func_signal")

        if self.model.stop_acquisition:
            print("PRESSED STOP BUTTON")
            return True

        print(f"self.recieved frames = {self.received_frames}")
        print(f"model.stop_acquisition = {self.model.stop_acquisition}")
        print(f"self.end_acquisition = {self.end_acquisition}")
        pos = self.asi_stage.get_axis_position(self.axis)
        print(f"pos = {pos} stop position:{self.stop_position*1000}")
        self.end_signal_temp += 1
        print(f"self.end_signal_temp = {self.end_signal_temp}")
        print(f"DAQ Trigger SENT test = {self.end_signal_temp>0}")
        if self.model.stop_acquisition or self.end_acquisition or self.end_signal_temp>0:
            print("returning true from stop or end acquisition end_func_signal")
            if self.stack_cycling_mode == "per_stack":
                print("per stack if statment called")
                print(f"channel list: {self.current_channel_in_list}")
                self.update_channel()
                print("if statement update channel finished")
                # if run through all the channels, move to next position
                if self.current_channel_in_list == 0:
                    print(f"in if channel list = 0 statement, channel = {self.current_channel_in_list}")
                    return True
            else:
                print("in else true statement")
                return True
        
        print("returning False from end_func_signal")
        return False

    def update_channel(self):
            print("update channel")
            print(f"channel before in update channel = {self.channels}")
            print(f"channel before in update channel list = {self.current_channel_in_list}")
            self.current_channel_in_list = (
                self.current_channel_in_list + 1
            ) % self.channels
            print(f"channel after in update channel = {self.channels}")
            print(f"channel before in update channel list = {self.current_channel_in_list}")
            self.asi_stage.wait_until_complete(self.axis)
            print("Stage wait until complete completed")
            
            if self.current_channel_in_list>0:
                print("PAUSING DATA THREAD IF STATEMENT IN CHANNEL")
                self.model.pause_data_thread
                print("DATA THREAD PAUSED IN CHANNEL")

            self.asi_stage.set_speed(percent=0.5)
            print("Stage speed set")
            self.asi_stage.wait_until_complete(self.axis)
            print("Stage wait until complete completed")
            
            if self.current_channel_in_list == 0:
                print("if current channel is zero statement")
                return True            
                            
            self.asi_stage.set_speed(percent=self.percent_speed)
            print("original stage speed set")
            
            print(f"current channel = {self.model.active_microscope.current_channel}")
            self.model.active_microscope.prepare_next_channel()
            print("channel prepared after model")

            self.model.resume_data_thread()
            print("DATA THREAD RESUMED IN CHANNEL")

    def cleanup(self):
        """Clean up the constant velocity acquisition.

        Need to reset the trigger source to the default.

        """
        # reset stage speed
        # 4.288497*2
        pos = self.asi_stage.get_axis_position(self.axis)
        print(f"Current Position = {pos}")
        print(f"Stop position = {self.stop_position*1000}")
        print("Clean up called")
        # self.asi_stage.set_speed({self.axis: self.default_speed})
        self.asi_stage.set_speed(percent=0.5)

        # self.asi_stage.set_speed(0.9)
        print("speed set")
        end_speed = self.asi_stage.get_speed(self.axis)  # mm/s
        print("end Speed = ",end_speed)
        self.asi_stage.stop()
        print("stage stop")
        # print("external trigger none")
        # return to start position
        # self.start_position = float(
        #     self.model.configuration[
        #         "experiment"]["MicroscopeState"]["abs_z_start"])
        # self.asi_stage.move_absolute({f"{self.axis}_abs: {self.start_position}"})
        
        # self.asi_stage.move_axis_absolute(self.axis, self.start_position * 1000.0, wait_until_done=True)
        # print("stage moved to original position")
        # pos = self.asi_stage.get_axis_position(self.axis)
        # print(f"Current Position = {pos}")
        # print(f"start position = {self.start_position*1000}")
        
        
        self.asi_stage.wait_until_complete(self.axis)
        print("Stage wait until complete completed after update scan")
            

        # self.asi_stage.stop_scan()
        # print("stage stop scan")
        print("DAQ STOP ACQUISITION CALLED CLEAN UP")
        self.model.active_microscope.daq.stop_acquisition()
        print("DAQ STOP ACQUISITION FINISHED CLEAN UP")
        self.model.configuration[
            "experiment"]["MicroscopeState"]["waveform_template"] = "Default"
        print("config set to default")
        self.model.active_microscope.current_channel = 0
        print(
            f"self.model.active_microscope.current_channel = {self.model.active_microscope.current_channel})")
        self.model.active_microscope.daq.external_trigger = None
        print("external trigger set to none")
        print("DAQ set external trigger to none called")
        # self.model.active_microscope.daq.set_external_trigger(None)
        print("external trigger set to none v2")
        # self.model.active_microscope.prepare_next_channel()
        # print("clean up channel prepared")
        # self.model.active_microscope.daq.set_external_trigger()
        # print("external trigger set to none v2")

    def pre_data_func(self):
        self.received_frames_v2 = self.received_frames
        self.total_frames = self.expected_frames * self.channels
        print(f"total channels = {self.channels}")
        print(f"total frames = {self.total_frames}")

    def in_data_func(self, frame_ids):
        # print(f"frame_ids = {len(frame_ids)}")
        self.received_frames += len(frame_ids)
        if self.image_writer is not None:
            self.image_writer.save_image(frame_ids)
        # self.received_frames_v2 = self.received_frames
        # self.recieved_frames_v2 += self.recieved_frames
        # print(f"received_Frames v2: {self.recieved_frames_v2}")

    def end_data_func(self):
        pos = self.asi_stage.get_axis_position(self.axis)
        expected_channel = self.expected_frames * (self.end_signal_temp + 1)
        time_total = (self.total_frames * self.current_sweep_time)/60
        time_per_channel = (expected_channel * self.current_sweep_time)/60
        time_remaining_total = round(((self.total_frames - self.received_frames) * self.current_sweep_time)/(60),2)
        time_remaining_per_channel = round(((expected_channel - self.received_frames) * self.current_sweep_time)/(60),2)
        print(f"Received: {self.received_frames} Per Channel: {expected_channel} Expected Total: {self.total_frames} Channel = {self.end_signal_temp + 1} of {self.channels}")
        print(f"time remaining per channel min: {time_remaining_per_channel}, time remaining total min: {time_remaining_total}")
        logger.info(f"Received: {self.received_frames} Per Channel: {expected_channel} Expected Total: {self.total_frames}")
        # print(f"Received V2: {self.received_frames_v2} Expected: {self.expected_frames}")
        print(f"Position: {pos} Stop Position: {self.stop_position*1000} ")
        logger.info(f"Position: {pos} Stop Position: {self.stop_position*1000} ")
        self.end_acquisition = self.received_frames >= self.total_frames
        return self.end_acquisition
    
    def cleanup_data_function(self):
        """Clean up the constant velocity acquisition.

        Designed to be called in the case of a failure.
        Do not rely on this function being called.

        Cleans up the image writer.
        """
        print("clean up data function called")
        if self.image_writer:
            self.image_writer.cleanup()