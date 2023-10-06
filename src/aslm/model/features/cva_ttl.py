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


class CVATTL:
    # def __init__(self, model, axis='z', saving_flag=False, saving_dir="cva"):
    def __init__(self, model, axis='z'):
        self.model = model

        # Update stage position
        # self.model.active_microscope.ask_stage_for_position = True
        # stage_positions = self.model.active_microscope.get_stage_position()
        # success = self.model.active_microscope.move_stage(
        #     pos_dict=stage_positions,
        #     wait_until_done=True,
        #     update_focus=False)
        # print("Moving stages successful:", success)

        self.axis = axis
        self.default_speed = None
        self.asi_stage = None

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
        22 nm. It is a quadrature device, so the minimum step size is 88 nm.

        Assumes stage motion is 45 degrees relative to the optical axis.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        # Inject new trigger source.
        # self.model.active_microscope.prepare_next_channel()
        # # TODO: retrieve this parameter from configuration file
 
        # self.model.active_microscope.daq.set_external_trigger("/PXI6259/PFI1")
        # self.model.active_microscope.daq.number_triggers = 0
        # self.model.active_microscope.daq.set_external_trigger("/PXI6259/PFI1")
         
        print("pre func initiated")
        self.asi_stage = self.model.active_microscope.stages[self.axis]
        print("self.asi stage")
        microscope_state = self.model.configuration["experiment"]["MicroscopeState"]
        self.stack_cycling_mode = microscope_state["stack_cycling_mode"]
        self.channels = microscope_state["selected_channels"]
        self.current_channel_in_list = 0
        print(f"current channel = {self.channels}")

        # self.received_frames = 0
        # self.end_channel = False
        self.end_acquisition = False
        # self.recieved_frames_v2 = 0
        self.received_frames = 1
        self.end_signal_temp = 0


        # get the current exposure time for that channel.
        # exposure_time = float( 
        #     self.model.configuration["experiment"][
        #         "MicroscopeState"]["channels"][f"channel_{self.model.active_microscope.current_channel}"][
        #         "camera_exposure_time"]) / 1000.0
        # self.model.active_microscope.current_channel = 2
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

        # Provide just a bit of breathing room for the sweep time...
        current_sweep_time = current_sweep_time * scaling_factor
        
        print("*** current sweep time:", current_sweep_time)
        logger.info(f"*** current sweep time: {current_sweep_time}")
        logger.info(f"*** sweep time scaling: {scaling_factor}")
        # self.sweep_time = current_sweep_time
        # logger.debug(f"running signal node: {self.curr_node.node_name}")

        # print("*** current exposure time:", self.model.active_microscope.current_channel, exposure_time)

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
        

        
        # logger.debug("*** step size um:", desired_sampling_um)

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
        max_speed = 4.288497*2

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
        
        logger.info(f"*** z start position: {self.start_position}")
        logger.info(f"*** z end position: {self.stop_position}")
        logger.info(f"*** Expected number of steps: {self.number_z_steps}")
        pos = self.asi_stage.get_axis_position(self.axis)
        print(f"Current Position = {pos}")
        print(f"Start position = {self.start_position*1000}")
        
        # move to start position:
        self.asi_stage.move_axis_absolute(self.axis, self.start_position * 1000.0, wait_until_done=True)
        posw = self.asi_stage.get_axis_position(self.axis)
        print(f"Current Position = {posw}")
        print(f"Start position = {self.start_position*1000}")

        # Set the x-axis of the ASI stage to operate at that velocity.

        # TODO: stage name and stage controller!
        # self.default_speed = self.asi_stage.default_speed
        # self.default_speed = 3.745760

        # basic speed - essentially the minimum speed value permitted by the
        # stage, of which subsequent values are multiples of.
        self.asi_stage.set_speed(percent=0.0001/max_speed)
        basic_speed = self.asi_stage.get_speed(self.axis)  # mm/s
        print("Basic Speed = ",basic_speed)

        # TODO: set the speed from GUI? step size?
        # Calculate the stage velocity in mm/seconds. 5.28 * 10^-3 s
        # stage_velocity = step_size_mm / (exposure_time * 1.15)
        # step_size = float(self.model.configuration["experiment"]["MicroscopeState"]["step_size"]) * np.sqrt(2) / 1000.0
        # get exposure time
        # expected_speed = step_size / exposure_time
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

        # expected_frames = np.ceil(((self.number_z_steps * step_size_mm)/stage_velocity)/current_sweep_time)
        expected_frames_v1 = np.ceil(((self.number_z_steps * step_size_mm)/stage_velocity)/current_sweep_time)
        expected_frames = int(np.ceil(abs(self.start_position - self.stop_position)/stage_velocity/current_sweep_time))
        print(f"*** Expected Frames V1:{expected_frames_v1}")
        print(f"*** Expected Frames: {expected_frames}")
        logger.info(f"*** Expected Frames: {expected_frames}")
        self.model.configuration["experiment"]["MicroscopeState"]["waveform_template"] = "CVACONPRO"
        # self.model.configuration["waveform_templates"]["CVACONPRO"]["expand"] = int(np.ceil(int(expected_frames)/2))
        # self.model.configuration["waveform_templates"]["CVACONPRO"]["expand"] = int(expected_frames)

        self.model.configuration["waveform_templates"]["CVACONPRO"]["expand"] = expected_frames
        # self.model.configuration["waveform_templates"]["CVACONPRO"]["repeat"] = int(expected_frames)
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
        
        self.model.active_microscope.current_channel = 0
        self.waveform_dict = self.model.active_microscope.calculate_all_waveform()
        # #   ms calculated v2 {self.waveform_dict}")
        self.model.active_microscope.prepare_next_channel()
        # print("microscope channel prepared")
        print("channel prepared after model")
        self.model.active_microscope.daq.set_external_trigger("/PXI6259/PFI1")
        print(f"external trigger set to {self.model.active_microscope.daq.external_trigger}")

        # self.model.active_microscope.current_channel = 0
        
        
        # print("stage moving to stop position at speed")
        # posw = self.asi_stage.get_axis_position(self.axis)
        # print(f"before scan to stop Current Position = {posw}")
        # print(f"Start position = {self.start_position*1000}")
        # self.asi_stage.move_axis_absolute(self.axis, self.stop_position * 1000.0, wait_until_done=True)
        # posw = self.asi_stage.get_axis_position(self.axis)
        # print(f"stop position Current Position = {posw}")
        # print(f"stop position = {self.stop_position*1000}")
        # print("stage moving to stop position at speed")
        # self.asi_stage.move_axis_absolute(self.axis, self.start_position * 1000.0, wait_until_done=True)
        # posw = self.asi_stage.get_axis_position(self.axis)
        # print(f"start position after scan to start Current Position = {posw}")
        # print(f"Start position = {self.start_position*1000}")
        # Configure the encoder to operate in constant velocity mode.
        self.asi_stage.scanr(
            start_position_mm=self.start_position,
            end_position_mm=self.stop_position,
            enc_divide=step_size_mm,
            # round(
            #     float(
            #         self.model.configuration[
            #             "experiment"]["MicroscopeState"][
            #             "start_focus"])) / 45397.6,
            axis=self.axis
        )
        print("scan r initalized")

        # Start the daq acquisition.  Basically places all of the waveforms in a ready
        # state so that they will be run one time when the trigger is received.
        

        # Start the stage scan.  Also get this functionality into the ASI stage class.
        self.asi_stage.start_scan(self.axis)
        print("scan started")

        # self.model.active_microscope.daq.set_external_trigger("/PXI6259/PFI1")

        # start scan won't start the scan, but when calling stop_scan it will start scan. So weird.
        # self.asi_stage.stop_scan()
        # if self.asi_stage.get_speed(self.axis) == stage_velocity:
        #     self.model.active_microscope.daq.run_acquisition()
        #     print("microscope running")
        # else:
        #     # time.sleep(1)
        #     self.model.active_microscope.daq.run_acquisition()
        #     print("microscope running after sleep")


        # time.sleep(5) #seconds
        # # self.model.active_microscope.daq.set_external_trigger("/PXI6259/PFI1",self.asi_stage)
        # pos = self.asi_stage.get_axis_position(self.axis)
        # TODO: after scan, the stage will go back to the start position and stop sending out triggers.
        # if abs(pos - self.stop_position * 1000) < 1:
        #     self.cleanup()
        #     return True
        # TODO: wait time to be more reasonable
        # time.sleep(7)


        # Stage starts to move and sends a trigger to the DAQ.
        # HOw do we know how many images to acquire?
       
       
       # acquired_frame_num = self.model.active_microscope.run_data_process()
        # print(f"frames run data process init = {acquired_frame_num}") 
        

    def end_func_signal(self):
        print("in end_func_signal")
        print(f"self.recieved frames = {self.received_frames}")
        print(f"model.stop_acquisition = {self.model.stop_acquisition}")
        print(f"self.end_acquisition = {self.end_acquisition}")
        pos = self.asi_stage.get_axis_position(self.axis)
        print(f"pos = {pos} stop position:{self.stop_position*1000}")
        self.end_signal_temp += 1
        print(f"self.end_signal_temp = {self.end_signal_temp}")
        print(f"DAQ Trigger SENT test = {self.end_signal_temp>0}")
        # self.end_acquisition_v2 = self.
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
                    self.cleanup()
                    print("clean up finished")
                    return True
            else:
                print("in else true statement")
                return True
        
        # elif 
        #     print("returning True from stop acquisition end_func_signal")
        #     return True

        # if self.end_acquisition:
        #     print("return True from end_func_signal")
        #     # Update channel
        #     return True
        # acquired_frame_num_v2 = self.model.active_microscope.run_data_process() 
        # pos = self.asi_stage.get_axis_position(self.axis)
        # print(f"Current Position = {pos}")
        # logger.info(f"Current Position = {pos}")
        # print(f"Stop position = {self.stop_position*1000}")
        # # print(f"self.acquired_frame_num end func = {acquired_frame_num_v2}")
        # self.received_frames += 1
        # print(f"Recieved Frames = {self.received_frames}")
        # # if abs(pos - self.stop_position * 1000) < 1:
        # #     print("position met")
        # #     # self.model.active_microscope.daq.stop_acquisition()
        # #     # print("stop acquisition")
        # #     # self.cleanup()
        # #     # print("Clean up finished")
        # #     return True
        # if self.received_frames >= self.expected_frames:
        #     print("end function called")
        #     print(f"End Recieved Frames = {self.received_frames}")
        #     print(f"End Expected Frames = {self.expected_frames}")
        #     return True
        # if self.acquired_frame_num == self.expected_frames:
        #         print("end function called")
        #         print(f"End Recieved Frames = {self.received_frames}")
        #         print(f"End Expected Frames = {self.expected_frames}")
        #         return True

        
        # pos_temp = []
        # lengthframes = 2
        
        # pos_temp.append(pos)
        
        # TODO: after scan, the stage will go back to the start position and stop sending out triggers.
        
        
       
            
        # elif pos_temp(2)-pos_temp(1):
        #     print("testdataset") 
        #     return True 
        # TODO: wait time to be more reasonable
        # time.sleep(5)
        print("returning False from end_func_signal")
        return False

    def update_channel(self):
            print("update channel")
            print(f"channel before in update channel = {self.channels}")
            print(f"channel before in update channel list = {self.current_channel_in_list}")
            self.current_channel_in_list = (
                self.current_channel_in_list + 1
            ) % self.channels
            # self.end_signal_temp = 0
            self.received_frames = 1
            print(f"channel after in update channel = {self.channels}")
            print(f"channel before in update channel list = {self.current_channel_in_list}")
            # self.model.active_microscope.prepare_next_channel()
            pos1 = self.asi_stage.get_axis_position(self.axis)
            print(f"Current Position Before move to start position = {pos1}")
            self.asi_stage.set_speed(percent=0.7)
            print("Stage speed set")

            # self.asi_stage.move_axis_absolute(self.axis, self.start_position * 1000.0, wait_until_done=True)
            # print("stage moved to original position")
            # self.asi_stage.move_axis_absolute(self.axis, self.start_position * 1000.0, wait_until_done=True)
            # print("stage moved to start position")
           
            self.asi_stage.move_axis_absolute(self.axis, self.start_position * 1000.0, wait_until_done=True)
            print("stage moved to start position")
            posw = self.asi_stage.get_axis_position(self.axis)
            print(f"Current Position update channel = {posw}")
            print(f"Start position channel = {self.start_position*1000}")

            # self.model.active_microscope.current_channel = 0
            self.asi_stage.set_speed(percent=self.percent_speed)
            print("original stage speed set")
            
            print(f"current channel = {self.model.active_microscope.current_channel}")
            self.model.active_microscope.prepare_next_channel()
            print("channel prepared after model")
            self.model.active_microscope.daq.set_external_trigger("/PXI6259/PFI1")
            print(f"external trigger set to {self.model.active_microscope.daq.external_trigger}")

            self.asi_stage.start_scan(self.axis)
            # self.asi_stage.stop_scan()
            # self.pre_func_signal()
            print("pre function signal initiated")
    
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
        self.asi_stage.set_speed(percent=0.9)

        # self.asi_stage.set_speed(0.9)
        print("speed set")
        end_speed = self.asi_stage.get_speed(self.axis)  # mm/s
        print("end Speed = ",end_speed)
        self.asi_stage.stop()
        print("stage stop")
        
        print("external trigger none")
        # return to start position
        # self.start_position = float(
        #     self.model.configuration[
        #         "experiment"]["MicroscopeState"]["abs_z_start"])
        # self.asi_stage.move_absolute({f"{self.axis}_abs: {self.start_position}"})
        self.asi_stage.move_axis_absolute(self.axis, self.start_position * 1000.0, wait_until_done=True)
        print("stage moved to original position")
        pos = self.asi_stage.get_axis_position(self.axis)
        print(f"Current Position = {pos}")
        print(f"start position = {self.start_position*1000}")
        self.model.active_microscope.daq.stop_acquisition()
        self.model.configuration[
            "experiment"]["MicroscopeState"]["waveform_template"] = "Default"
        print("config set to default")
        self.model.active_microscope.current_channel = 0
        print(
            f"self.model.active_microscope.current_channel = {self.model.active_microscope.current_channel})")
        self.model.active_microscope.daq.external_trigger = None
        print("external trigger set to none")
        self.model.active_microscope.prepare_next_channel()
        print("clean up channel prepared")
        self.model.active_microscope.daq.set_external_trigger(None)
        print("external trigger set to none v2")

    def pre_data_func(self):
        # self.received_frames = 
        self.received_frames_v2 = self.received_frames
        

    def in_data_func(self, frame_ids):
        # print(f"frame_ids = {len(frame_ids)}")
        self.received_frames += len(frame_ids)
        # self.received_frames_v2 = self.received_frames
        # self.recieved_frames_v2 += self.recieved_frames
        # print(f"received_Frames v2: {self.recieved_frames_v2}")

    def end_data_func(self):
        pos = self.asi_stage.get_axis_position(self.axis)
        # self.received_frames_v2 += self.received_frames
        # self.received_frames_v2 = 0
        print(f"Received: {self.received_frames} Expected: {self.expected_frames}")
        # print(f"Received V2: {self.received_frames_v2} Expected: {self.expected_frames}")
        print(f"Position: {pos} Stop Position: {self.stop_position*1000} ")
        logger.info(f"Received: {self.received_frames} Expected: {self.expected_frames}")
        # logger.info(f"Received V2: {self.recieved_frames_v2} Expected: {self.expected_frames}")

        # logger.info(f"Position: {pos} Stop Position: {self.stop_position*1000} ")
        # self.end_acquisition = self.received_frames_v2 >= self.expected_frames
        # self.end_acquisition = self.received_frames_v2 >= self.expected_frames or pos >= self.stop_position*1000
        
        # if self.received_frames >= self.expected_frames:
        #    self.end_acquisition = self.received_frames >= self.expected_frames or pos >= self.stop_position*1000
            # self.end_acquisition = self.received_frames >= self.expected_frames
            # self.received_frames_v2 = self.received_frames + 1
        self.end_acquisition = self.received_frames >= self.expected_frames
        print(f"end acquistion statement = {self.end_acquisition}")
            # print(f"end acquistion in if statement = {self.end_acquisition}")
        # If channel is ended, but there are more channels to go, return False
        # If channel is ended and this was the last channel, return True  
        # return self.end_channel
        return self.end_acquisition