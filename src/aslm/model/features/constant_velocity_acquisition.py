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

    def __init__(self, model):
        self.model = model

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

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        # Change hardware Triggering.
        # Default run_acquisition in daq_ni triggers on the rising edge of the
        # trigger_source: /PXI6259/PFI0
        # When 5V is received at the trigger_source, the acquisition starts.

        # Inject new trigger source.
        # self.model.active_microscope.daq.trigger_source = "/PXI6259/PFI1"
        self.model.active_microscope.prepare_next_channel()
        self.model.active_microscope.daq.set_trigger_mode(1, "/PXI6259/PFI1")
        self.asi_stage = self.model.active_microscope.stages['z']

        # Create all of our tasks so that they are triggered by the new trigger source.
        # get the current channel - only operating in a per-stack mode.
        channel = 0
        # # get the current exposure time for that channel.
        exposure_time = float(self.model.configuration["experiment"]["MicroscopeState"]["channels"]["channel_1"]["camera_exposure_time"]) / 1000.0
        # self.model.active_microscope.daq.prepare_acquisition(channel, exposure_time)

        # Prepare the stage for a constant scan velocity mode.
        # Calculate Stage Velocity
        # Rotary encoder has a resolution of 45,396 counts/mm, or 1 count per 22 nm.
        # But it is in quadrature, so I thought it was actually 4x.
        minimum_encoder_divide = 88  # Smallest step size in nanometers is 88 nm.

        # Get step size from the GUI. For now, assume 160 nm.
        # Default units should probably be microns I believe. Confirm.
        desired_sampling = 160  # nm

        # The stage is at 45 degrees relative to the illumination and detection paths.
        step_size = desired_sampling * np.sqrt(2)  # 45 degrees, 226 nm

        # Calculate the desired encoder divide. Must be multiple of
        # minimum_encoder_divide. 2.6 encoder divides, round up to 3.
        desired_encoder_divide = np.ceil(step_size / minimum_encoder_divide) / 2

        # Calculate the actual step size in nanometers. 264 nm.
        step_size_nm = desired_encoder_divide * minimum_encoder_divide

        # Calculate the actual step size in millimeters. 264 * 10^-6 mm
        step_size_mm = step_size_nm / 1 * 10**-6  # 264 * 10^-6 mm

        # Calculate the stage velocity in mm/seconds. 5.28 * 10^-3 s
        stage_velocity = step_size_mm / (exposure_time * 1.15)

        # Set the start and end position of the scan in millimeters.
        # Retrieved from the GUI.
        # Set Stage Limits - Units in millimeters
        # microns to mm
        start_position = float(self.model.configuration["experiment"]["MicroscopeState"]["abs_z_start"]) / 1000.0
        self.stop_position = float(self.model.configuration["experiment"]["MicroscopeState"]["abs_z_end"]) / 1000.0

        # Set the x-axis of the ASI stage to operate at that velocity.
        # uses the scanr command from the TigerASI repository that I mention in Github
        # Need to add a similar command to the ASI stage class.
        # TODO: stage name and stage controller!
        self.default_speed = self.asi_stage.default_speed
        # basic speed
        self.asi_stage.tiger_controller.set_speed(X=0.0001)
        basic_speed = self.asi_stage.tiger_controller.get_speed("X")
        # mm/s
        # TODO: set the speed from GUI? step size?
        stage_velocity = basic_speed * round(float(self.model.configuration["experiment"]["MicroscopeState"]["step_size"]))
        self.asi_stage.tiger_controller.set_speed(X=stage_velocity)


        # Configure the encoder to operate in constant velocity mode.
        # Must add similar scanr functionality to our ASI stage class.
        self.asi_stage.tiger_controller.scanr(
            start_position_mm=start_position,
            end_position_mm=self.stop_position,
            enc_divide=round(float(self.model.configuration["experiment"]["MicroscopeState"]["start_position"])) / 45397.6,
        )

        # Start the daq acquisition.  Basically places all of the waveforms in a ready
        # state so that they will be run one time when the trigger is received.
        # self.model.active_microscope.daq.run_acquisition()

        # Start the stage scan.  Also get this functionality into the ASI stage class.
        self.asi_stage.tiger_controller.start_scan("X")
        # start scan won't start the scan, but when calling stop_scan it will start scan. So weird.
        self.asi_stage.tiger_controller.stop_scan()
        # the position will be set to start_position_mm after scan by default
        # self.asi_stage.tiger_controller.send_command("SCAN a")

        # Stage starts to move and sends a trigger to the DAQ.
        # HOw do we know how many images to acquire?

    def end_func_signal(self):
        pos = self.asi_stage.tiger_controller.get_position('x')
        print("*** stage position:", pos)
        # TODO: after scan, the stage will go back to the start position and stop sending out triggers.
        if abs(pos - self.stop_position * 10000) < 100:
            return True
        # TODO: wait time to be more reasonable
        time.sleep(5)
        return False

    def cleanup(self):
        """Clean up the constant velocity acquisition.

        Need to reset the trigger source to the default.

        """
        self.model.active_microscope.daq.set_trigger_mode(0, None)
        self.asi_stage.tiger_controller.stop()
        # reset stage speed
        self.asi_stage.tiger_controller.set_speed(X=self.default_speed)
