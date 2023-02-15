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

# Third Party Imports
import numpy as np

# Local imports


class ConstantVelocityAcquisition:
    """ Class for acquiring data using the ASI internal encoder. """

    def __init__(self, model):
        self.model = model


        self.config_table = {
            "signal": {
                "init": self.pre_func_signal,
                "main": self.in_func_signal,
                "end": self.end_func_signal,
            },
            "data": {
                "init": self.pre_func_data,
                "main": self.in_func_data,
                "end": self.end_func_data,
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

        # Calculate Stage Velocity and set it.
        # Rotary encoder has a resolution of 45,396 counts/mm, or 1 count per 22 nm.
        # But it is in quadrature, so I thought it was actually 4x.
        minimum_encoder_divide = 88
        desired_sampling = 160  # nm
        step_size = desired_sampling * np.sqrt(2)  # 45 degrees, 226 nm
        desired_encoder_divide = np.ceil(step_size / minimum_encoder_divide) # 3
        step_size_nm = desired_encoder_divide * minimum_encoder_divide # 264 nm.
        step_size_mm = step_size_nm / 1*10**6  # 264 * 10^-6 mm
        camera_integration_time = 0.05  # 50 ms.
        stage_velocity = step_size_mm / camera_integration_time  # 5.28 * 10^-3 mm/s.
        self.model.dev

        # Set Stage Limits - Units in millimeters
        start_position = -55.2320
        stop_position = -54.2320

        box.set_speed(X=0.01, y=0.02)

        box.scanr(scan_start_mm=12.7, scan_stop_mm=10.7, pulse_interval_enc_ticks=8)

        # Change hardware Triggering




        settings = self.model.configuration["experiment"]["AutoFocusParameters"]
        # self.focus_pos = args[2]  # Current position
        self.focus_pos = self.model.configuration["experiment"]["StageParameters"]["f"]
        # self.focus_pos = self.model.get_stage_position()['f_pos']
        self.total_frame_num = self.get_autofocus_frame_num()  # Total frame num
        self.coarse_steps, self.init_pos = 0, 0
        if settings["fine_selected"]:
            self.fine_step_size = int(settings["fine_step_size"])
            fine_steps, self.fine_pos_offset = self.get_steps(
                int(settings["fine_range"]), self.fine_step_size
            )
            self.init_pos = self.focus_pos - self.fine_pos_offset
        if settings["coarse_selected"]:
            self.coarse_step_size = int(settings["coarse_step_size"])
            self.coarse_steps, coarse_pos_offset = self.get_steps(
                int(settings["coarse_range"]), self.coarse_step_size
            )
            self.init_pos = self.focus_pos - coarse_pos_offset
        self.signal_id = 0
