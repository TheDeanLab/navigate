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


class CVASINGLEWAVE:
    """Class for acquiring data using the ASI internal encoder."""

    def __init__(self, model, axis='z'):
        self.model = model
        self.axis = axis
        self.default_speed = None
        self.asi_stage = None

        self.config_table = {
            "signal": {
                "init": self.pre_func_signal,
                "end": self.end_func_signal,
                "cleanup": self.cleanup,
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
        print("pre func initiated")
        self.asi_stage = self.model.active_microscope.stages[self.axis]
        # print("self.asi stage")
        self.recieved_frames = 0

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
        self.readout_time = readout_time
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
        self.step_size_um = step_size_mm*1000
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
        # self.number_z_steps = float(
        #     self.model.configuration[
        #         "experiment"]["MicroscopeState"]["number_z_steps"])
        self.distance_traveled = abs(self.stop_position-self.start_position)
        print(f"*** Distance = {self.distance_traveled}")
        print(f"*** Step size = {step_size_mm}")
        self.number_z_steps = abs(self.stop_position-self.start_position)/step_size_mm
        logger.info(f"*** z start position (mm): {self.start_position}")
        logger.info(f"*** z end position (mm): {self.stop_position}")
        logger.info(f"*** Expected number of steps: {self.number_z_steps}")
        print(f"*** z start position (mm): {self.start_position}")
        print(f"*** z end position (mm): {self.stop_position}")
        print(f"*** Expected number of steps: {self.number_z_steps}")
        
        
        # move to start position:
        self.asi_stage.move_axis_absolute(self.axis, self.start_position * 1000.0, wait_until_done=True)

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

        self.asi_stage.set_speed(percent=expected_speed/max_speed)
        stage_velocity = self.asi_stage.get_speed(self.axis)
        print("Final stage velocity, (mm/s):", stage_velocity)
        print("Encoder divide step size = ",step_size_mm)
        logger.info(f"*** Expected stage velocity, (mm/s): {expected_speed}")
        logger.info(f"*** Final stage velocity, (mm/s): {stage_velocity}")

        expected_frames_v1 = np.ceil(((self.number_z_steps * step_size_mm)/stage_velocity)/current_sweep_time)
        expected_frames = np.ceil(abs(self.start_position - self.stop_position)/stage_velocity/current_sweep_time)
        print(f"*** Expected Frames V1: {expected_frames_v1}")
        print(f"*** Expected Frames: {expected_frames}")
        logger.info(f"*** Expected Frames: {expected_frames}")
        expand_frame = 1
        # self.model.configuration["experiment"]["MicroscopeState"]["waveform_template"] = "CVACONPRO"
        self.model.configuration["waveform_templates"]["CVACONPRO"]["repeat"] = int(expected_frames)
        self.model.configuration["waveform_templates"]["CVACONPRO"]["expand"] = int(expand_frame)
        # Expand_frames = float(self.model.configuration["waveform_templates"]["CVACONPRO"]["expand"])
        self.expected_frames = expected_frames
        print("waveforms obtained from config")
        # print(f"Expand Frames = {Expand_frames}")
        # logger.info(f"Expand Frames = {Expand_frames}")
        
        self.model.active_microscope.current_channel = 0
        self.waveform_dict = self.model.active_microscope.calculate_all_waveform()
        print(f"waveform dictionary test = {self.waveform_dict}")

        print("waveforms calculated v2")
        self.model.active_microscope.prepare_next_channel()
        print("microscope channel prepared")

        readout_time_v2 = self.model.active_microscope.get_readout_time()
        print(f"*** readout time before sweep time calc before scan == {readout_time}")
        print(f"*** readout time after sweep time calc before scan == {readout_time_v2}")
        # self.model.active_microscope.current_channel = 0
        
        # Configure the encoder to operate in constant velocity mode.
        self.asi_stage.scanr(
            start_position_mm=self.start_position,
            end_position_mm=self.stop_position+.001,
            enc_divide=step_size_mm,
            # round(
            #     float(
            #         self.model.configuration[
            #             "experiment"]["MicroscopeState"][
            #             "start_focus"])) / 45397.6,
            axis=self.axis
        )

        # Start the daq acquisition.  Basically places all of the waveforms in a ready
        # state so that they will be run one time when the trigger is received.
        

        # Start the stage scan.  Also get this functionality into the ASI stage class.
        self.asi_stage.start_scan(self.axis)

        # self.model.active_microscope.daq.set_external_trigger("/PXI6259/PFI1")

        # start scan won't start the scan, but when calling stop_scan it will start scan. So weird.
        self.asi_stage.stop_scan()
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
        # time.sleep(5)
        readout_time_v3 = self.model.active_microscope.get_readout_time()
        print(f"*** readout time after sweep time calc during scan == {readout_time_v3}")


        # Stage starts to move and sends a trigger to the DAQ.
        # HOw do we know how many images to acquire?
        # self.recieved_frames = 0
        self.tol = self.step_size_um/2
    def end_func_signal(self):
        self.recieved_frames += 1
        # print(self.recieved_frames)
        # if self.recieved_frames == self.expected_frames:
        #     print("end function called")
        #     print(f"End Recieved Frames = {self.recieved_frames}")
        #     print(f"End Expected Frames = {self.expected_frames}")
        #     return True
        # tol = self.step_size_um/2
        pos = self.asi_stage.get_axis_position(self.axis)
        # readout_time_v4 = self.model.active_microscope.get_readout_time()
        # print(f"*** readout time during end func == {readout_time_v4}")
        # pos_temp.append(pos)
        # print(f"Current Position = {pos}")
        # print(f"Stop position = {self.stop_position*1000}")
        # self.recieved_frames += 1
        # TODO: after scan, the stage will go back to the start position and stop sending out triggers.
        if pos>=(self.stop_position*1000):
            print("position exceeded")
            # self.model.active_microscope.daq.stop_acquisition()
            print("stop acquisition")
            # self.cleanup()
            print("clean up finished")
            print(f"Recieved frames = {self.recieved_frames}")
            print(f"Expected frames = {self.expected_frames}")
            logger.info(f"Recieved frames = {self.recieved_frames}")
            logger.info(f"Expected frames = {self.expected_frames}")
            readout_time_v5 = self.model.active_microscope.get_readout_time()
            print(f"*** readout time during end conditions met == {readout_time_v5}")
            exposure_times, sweep_times = self.model.active_microscope.calculate_exposure_sweep_times(readout_time_v5)
            print(f"*** end func exposure_times = f{exposure_times}")
            print(f"*** end func exposure_times = f{sweep_times}")
            return True
        elif abs(pos - self.stop_position * 1000) < self.tol:
            print("position met")
            # self.model.active_microscope.daq.stop_acquisition()
            print("stop acquisition")
            # self.cleanup()
            print("clean up finished")
            print(f"Recieved frames = {self.recieved_frames}")
            print(f"Expected frames = {self.expected_frames}")
            logger.info(f"Recieved frames = {self.recieved_frames}")
            logger.info(f"Expected frames = {self.expected_frames}")
            readout_time_v5 = self.model.active_microscope.get_readout_time()
            print(f"*** readout time during end conditions met == {readout_time_v5}")
            exposure_times, sweep_times = self.model.active_microscope.calculate_exposure_sweep_times(readout_time_v5)
            print(f"*** end func exposure_times = f{exposure_times}")
            print(f"*** end func exposure_times = f{sweep_times}")
            return True
        elif self.recieved_frames == self.expected_frames:
            print("frames met")
            # self.model.active_microscope.daq.stop_acquisition()
            print("stop acquisition")
            # self.cleanup()
            print("clean up finished")
            print(f"Recieved frames = {self.recieved_frames}")
            print(f"Expected frames = {self.expected_frames}")
            logger.info(f"Recieved frames = {self.recieved_frames}")
            logger.info(f"Expected frames = {self.expected_frames}")
            readout_time_v5 = self.model.active_microscope.get_readout_time()
            print(f"*** readout time during end conditions met == {readout_time_v5}")
            exposure_times, sweep_times = self.model.active_microscope.calculate_exposure_sweep_times(readout_time_v5)
            print(f"*** end func exposure_times = f{exposure_times}")
            print(f"*** end func exposure_times = f{sweep_times}")
            return True

        
        # pos_temp = []
        # lengthframes = 2
        # pos = self.asi_stage.get_axis_position(self.axis)
        # # pos_temp.append(pos)
        # print(f"Current Position = {pos}")
        # print(f"Stop position = {self.stop_position*1000}")
        # # TODO: after scan, the stage will go back to the start position and stop sending out triggers.
        
        # if abs(pos - self.stop_position * 1000) < 1:
        #     print("position met")
        #     # self.model.active_microscope.daq.stop_acquisition()
        #     # print("stop acquisition")
        #     # self.cleanup()
        #     # print("Clean up finished")
        #     return True
       
            
        # elif pos_temp(2)-pos_temp(1):
        #     print("testdataset") 
        #     return True 
        # TODO: wait time to be more reasonable
        # time.sleep(5)
        return False

    def cleanup(self):
        """Clean up the constant velocity acquisition.

        Need to reset the trigger source to the default.

        """
        # reset stage speed
        4.288497*2
        
        print("Clean up called")
        # self.asi_stage.set_speed({self.axis: self.default_speed})
        self.asi_stage.set_speed(percent=0.9)

        # self.asi_stage.set_speed(0.9)
        print("speed set")
        end_speed = self.asi_stage.get_speed(self.axis)  # mm/s
        print("end Speed = ",end_speed)
        self.asi_stage.stop()
        print("stage stop")
        self.model.active_microscope.daq.stop_acquisition()
        self.model.active_microscope.daq.set_external_trigger(None)
        print("external trigger none")
        # return to start position
        self.start_position = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["abs_z_start"])
        self.asi_stage.move_absolute({f"{self.axis}_abs: {self.start_position}"})
        print("stage moved to original position")

