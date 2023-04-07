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
        # TODO: retrieve this parameter from configuration file
        self.model.active_microscope.daq.set_external_trigger("/PXI6259/PFI1")
        self.asi_stage = self.model.active_microscope.stages[self.axis]

        # get the current exposure time for that channel.
        exposure_time = float(
            self.model.configuration["experiment"][
                "MicroscopeState"]["channels"]["channel_1"][
                "camera_exposure_time"]) / 1000.0

        # Calculate Stage Velocity
        minimum_encoder_divide = 88 # nm

        # Get step size from the GUI. For now, assume 160 nm.
        # Default units should probably be microns I believe. Confirm.
        desired_sampling = 160  # nm

        # The stage is at 45 degrees relative to the optical axes.
        step_size = desired_sampling * np.sqrt(2)  # 45 degrees, 226 nm

        # Calculate the desired encoder divide. Must be multiple of
        # minimum_encoder_divide. 2.6 encoder divides, round up to 3.
        desired_encoder_divide = np.ceil(step_size / minimum_encoder_divide) / 2

        # Calculate the actual step size in nanometers. 264 nm.
        step_size_nm = desired_encoder_divide * minimum_encoder_divide

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

        # Set the x-axis of the ASI stage to operate at that velocity.

        # TODO: stage name and stage controller!
        self.default_speed = self.asi_stage.default_speed

        # basic speed - essentially the minimum speed value permitted by the
        # stage, of which subsequent values are multiples of.
        self.asi_stage.set_speed({self.axis: 0.0001})
        basic_speed = self.asi_stage.get_speed(self.axis)  # mm/s

        # TODO: set the speed from GUI? step size?
        # Calculate the stage velocity in mm/seconds. 5.28 * 10^-3 s
        # stage_velocity = step_size_mm / (exposure_time * 1.15)
        stage_velocity = basic_speed * round(
            float(self.model.configuration[
                      "experiment"]["MicroscopeState"]["step_size"]))
        self.asi_stage.set_speed({self.axis: stage_velocity})

        # Configure the encoder to operate in constant velocity mode.
        self.asi_stage.scanr(
            start_position_mm=start_position,
            end_position_mm=self.stop_position,
            enc_divide=round(
                float(
                    self.model.configuration[
                        "experiment"]["MicroscopeState"][
                        "start_focus"])) / 45397.6,
            axis=self.axis
        )

        # Start the daq acquisition.  Basically places all of the waveforms in a ready
        # state so that they will be run one time when the trigger is received.
        # self.model.active_microscope.daq.run_acquisition()

        # Start the stage scan.  Also get this functionality into the ASI stage class.
        self.asi_stage.start_scan(self.axis)

        # start scan won't start the scan, but when calling stop_scan it will start scan. So weird.
        self.asi_stage.stop_scan()

        # Stage starts to move and sends a trigger to the DAQ.
        # HOw do we know how many images to acquire?

    def end_func_signal(self):
        pos = self.asi_stage.get_position(self.axis)
        # TODO: after scan, the stage will go back to the start position and stop sending out triggers.
        if abs(pos - self.stop_position * 1000) < 100:
            return True
        # TODO: wait time to be more reasonable
        time.sleep(5)
        return False

    def cleanup(self):
        """Clean up the constant velocity acquisition.

        Need to reset the trigger source to the default.

        """
        # reset stage speed
        self.asi_stage.set_speed({self.axis: self.default_speed})
        self.asi_stage.stop()
        self.model.active_microscope.daq.set_external_trigger(None)

