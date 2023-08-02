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

# Third Party Imports
import numpy as np

# Local imports


class ConstantVelocityAcquisition:
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
        self.model.active_microscope.prepare_next_channel()
        self.model.active_microscope.daq.set_external_trigger("/PXI6259/PFI1")
        self.asi_stage = self.model.active_microscope.stages[self.axis]

        # get the current sweep time for that channel.
        # Must account for any flyback, readout, etc.
        # Value in seconds.
        readout_time = self.model.active_microscope.get_readout_time()
        _, sweep_times = self.model.active_microscope.calculate_exposure_sweep_times(readout_time)
        current_sweep_time = sweep_times[f"channel_{self.model.active_microscope.current_channel}"]

        # Provide just a bit of breathing room for the sweep time...
        current_sweep_time = current_sweep_time * 1.05

        # Calculate Stage Velocity
        encoder_resolution = 22 # 22 nm
        minimum_encoder_divide = encoder_resolution * 4 # 88 nm

        # Retrieve the step size from the MicroscopeState/GUI, which is in microns.
        # Convert to nanometers.
        desired_sampling = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["step_size"]) * 1000.0

        # The stage is at 45 degrees relative to the optical axes.
        step_size = (desired_sampling * 2) / np.sqrt(2)  # 45 degrees, 226 nm
        print("Desired Axial Sampling:", desired_sampling)
        print("Desired Step Size of Stage:", step_size)

        # Calculate the desired encoder divide. Must be multiple of
        # minimum_encoder_divide. 2.6 encoder divides, round up to 3.
        # *** WHY IS THIS DIVIDE BY 2? TO CORRECT STEP SIZE ABOVE?
        desired_encoder_divide = np.ceil(step_size / minimum_encoder_divide)
        print("encoder divide:", desired_encoder_divide)

        # Calculate the actual step size in nanometers. 
        step_size_nm = desired_encoder_divide * minimum_encoder_divide
        print("Actual Step Size of Stage:", step_size_nm)

        # Calculate the actual step size in millimeters. 264 * 10^-6 mm
        step_size_mm = step_size_nm / 1 * 10**-6  # 264 * 10^-6 mm

        # Set the start and end position of the scan in millimeters.
        # Retrieved from the GUI.
        # Set Stage Limits - Units in millimeters
        # microns to mm
        start_position = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["abs_z_start"]) / 1000.0
        self.stop_position = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["abs_z_end"]) / 1000.0
        
        # move to start position:
        self.asi_stage.move_axis_absolute(self.axis, 
                                          start_position * 1000.0, 
                                          wait_until_done=True)
        print("stage moved to start position")

        # Set the x-axis of the ASI stage to operate at that velocity.
        # TODO: stage name and stage controller!
        self.default_speed = self.asi_stage.default_speed

        # basic speed - essentially the minimum speed value permitted by the
        # stage, of which subsequent values are multiples of.
        self.asi_stage.set_speed({self.axis: 0.0001})
        basic_speed = self.asi_stage.get_speed(self.axis)  # mm/s

        # Calculate the stage velocity in mm/seconds. 5.28 * 10^-3 s
        # stage_velocity = step_size_mm / exposure_time
        stage_velocity = step_size_mm / current_sweep_time
        print("Desired stage velocity (mm/s):", stage_velocity)

        self.asi_stage.set_speed({self.axis: stage_velocity})
        stage_velocity = self.asi_stage.get_speed(self.axis)
        print("Final stage velocity (mm/s):", stage_velocity)

        # Configure the encoder to operate in constant velocity mode.
        self.asi_stage.scanr(
            start_position_mm=start_position,
            end_position_mm=self.stop_position,
            enc_divide=step_size,
            axis=self.axis
        )
        print("stage scan initalized")

        # Start the daq acquisition.  Basically places all of the waveforms in a ready
        # state so that they will be run one time when the trigger is received.
        # self.model.active_microscope.daq.run_acquisition()

        # Start the stage scan.  Also get this functionality into the ASI stage class.
        try:
            self.asi_stage.start_scan(self.axis)
            print("Constant velocity acquisition started")

        # start scan won't start the scan, but when calling stop_scan it will start scan. So weird.
            self.asi_stage.stop_scan()
            print("Stop Scan Called")
            # self.model.active_microscope.daq.stop_acquisition()
            print("signal acquisition stopped")
            # self.end_func_signal()
            # print("end func signal passed")
            # self.cleanup()
            # print("clean up called try")
        except: 
            self.cleanup()
            print("clean up called except")

            pass
        # Stage starts to move and sends a trigger to the DAQ.
        # HOw do we know how many images to acquire?

    def end_func_signal(self):
        pos = self.asi_stage.get_axis_position(self.axis)
        # TODO: after scan, the stage will go back to the start position and stop sending out triggers.
        print("end function signal test")
        if abs(pos - self.stop_position * 1000) < 1:
            self.cleanup()
            return True
        # TODO: wait time to be more reasonable
        time.sleep(5)
        return False

    def cleanup(self):
        """Clean up the constant velocity acquisition.

        Need to reset the trigger source to the default.

        """
        # Reset DAQ outputs
        print("Print Cleanup Started")
        self.model.active_microscope.daq.stop_acquisition()
        #reset stage speed
        print("Print Active microscope daq stopped")
        # self.model.active_microscope.daq.set_external_trigger(None)
        self.asi_stage.set_speed({self.axis: self.default_speed})
        print("Set Speed Finished")
        self.asi_stage.stop()
        print("Stage Stopped Finished")
        self.model.active_microscope.daq.set_external_trigger(None)
        print("External Trigger Stopped")

        
        
        # return to start position
        start_position = float(
            self.model.configuration[
                "experiment"]["MicroscopeState"]["abs_z_start"])
        self.asi_stage.move_absolute({f"{self.axis}_abs: {start_position}"})
        print("Stage moved to start position")

