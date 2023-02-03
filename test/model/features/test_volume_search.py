# Copyright (c) 2021-2023  The University of Texas Southwestern Medical Center.
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
import queue

import pytest
import numpy as np

from aslm.model.features.volume_search import VolumeSearch


class TestVolumeSearch:
    @pytest.fixture(autouse=True)
    def _prepare_test(self, dummy_model_to_test_features):
        self.model = dummy_model_to_test_features
        self.config = self.model.configuration["experiment"]["MicroscopeState"]
        self.record_num = 0
        self.feature_list = [
            [
                {
                    "name": VolumeSearch,
                    "args": (
                        "Nanoscale",
                        "N/A",
                    ),
                }
            ]
        ]

        self.model.active_microscope_name = self.config["microscope_name"]
        curr_zoom = self.model.configuration["experiment"]["MicroscopeState"]["zoom"]
        self.curr_pixel_size = float(
            self.model.configuration["configuration"]["microscopes"][
                self.model.active_microscope_name
            ]["zoom"]["pixel_size"][curr_zoom]
        )
        self.target_pixel_size = float(
            self.model.configuration["configuration"]["microscopes"]["Nanoscale"][
                "zoom"
            ]["pixel_size"]["N/A"]
        )

        self.N = 128
        # The target image size in pixels
        self.mag_ratio = int(self.curr_pixel_size / self.target_pixel_size)
        self.target_grid_pixels = int(self.N // self.mag_ratio)
        # The target image size in microns
        self.target_grid_width = self.N * self.target_pixel_size

        self.model.event_queue = queue.Queue(10)

        self.model.configuration["experiment"]["StageParameters"]["z"] = 100
        self.model.configuration["experiment"]["StageParameters"]["f"] = 100

        self.config["start_position"] = np.random.randint(-200, 0)
        self.config["end_position"] = self.config["start_position"] + 200
        self.config["number_z_steps"] = np.random.randint(5, 10)
        self.config["step_size"] = (
            self.config["end_position"] - self.config["start_position"]
        ) / self.config["number_z_steps"]
        self.config["start_focus"] = -10
        self.config["end_focus"] = 10

        self.focus_step = (
            self.config["end_focus"] - self.config["start_focus"]
        ) / self.config["number_z_steps"]

    def get_next_record(self, record_prefix, idx):
        idx += 1
        while self.model.signal_records[idx][0] != record_prefix:
            idx += 1
            if idx >= self.record_num:
                break
        return idx

    def verify_volume_search(self):
        self.record_num = len(self.model.signal_records)

        idx = -1

        z_pos = (
            self.model.configuration["experiment"]["StageParameters"]["z"]
            + self.config["number_z_steps"] // 2 * self.config["step_size"]
        )
        f_pos = (
            self.model.configuration["experiment"]["StageParameters"]["f"]
            + self.config["number_z_steps"] // 2 * self.focus_step
        )

        for j in range(self.config["number_z_steps"]):
            idx = self.get_next_record("move_stage", idx)
            if idx >= self.record_num:
                # volume search ended early
                break
            pos_moved = self.model.signal_records[idx][1][0]

            fact = (
                j
                if j < (self.config["number_z_steps"] + 1) // 2
                else (self.config["number_z_steps"] + 1) // 2 - j - 1
            )

            # z, f
            assert (
                pos_moved["z_abs"] - (z_pos + fact * self.config["step_size"])
            ) < 1e-6, (
                f"should move to z: {z_pos + fact * self.config['step_size']}, "
                f"but moved to {pos_moved['z_abs']}"
            )
            assert (pos_moved["f_abs"] - (f_pos + fact * self.focus_step)) < 1e-6, (
                f"should move to f: {f_pos + fact * self.focus_step}, "
                f"but moved to {pos_moved['f_abs']}"
            )

        for _ in range(100):
            event, value = self.model.event_queue.get()
            if event == "multiposition":
                break

        positions = np.vstack(value)  # Columns: X, Y, Z, Theta, F

        # Check the bounding box. TODO: Make exact.
        min_x = (
            self.model.configuration["experiment"]["StageParameters"]["x"] - self.lxy
        )
        max_x = (
            self.model.configuration["experiment"]["StageParameters"]["x"]
            + self.lxy
            + self.N // 2 * self.curr_pixel_size
        )
        min_y = (
            self.model.configuration["experiment"]["StageParameters"]["y"] - self.lxy
        )
        max_y = (
            self.model.configuration["experiment"]["StageParameters"]["y"]
            + self.lxy
            + self.N // 2 * self.curr_pixel_size
        )
        min_z = self.model.configuration["experiment"]["StageParameters"]["z"] - self.lz
        max_z = (
            self.model.configuration["experiment"]["StageParameters"]["z"]
            + self.lz
            + self.N // 2 * self.curr_pixel_size
        )

        assert np.min(positions[:, 0]) >= min_x
        assert np.max(positions[:, 0]) <= max_x
        assert np.min(positions[:, 1]) >= min_y
        assert np.max(positions[:, 1]) <= max_y
        assert np.min(positions[:, 2]) >= min_z
        assert np.max(positions[:, 2]) <= max_z

    def test_box_volume_search(self):
        from aslm.tools.sdf import volume_from_sdf, box

        M = int(self.config["number_z_steps"])
        self.model.configuration["experiment"]["CameraParameters"]["x_pixels"] = self.N
        self.lxy = (
            np.random.randint(int(0.1 * self.N), int(0.4 * self.N))
            * self.curr_pixel_size
        )
        self.lz = (
            np.random.randint(int(0.1 * self.N), int(0.4 * self.N))
            * self.curr_pixel_size
        )

        vol = volume_from_sdf(
            lambda p: box(
                p,
                (
                    self.lxy,
                    self.lxy,
                    self.lz,
                ),
            ),
            self.N,
            pixel_size=self.curr_pixel_size,
            subsample_z=self.N // M,
        )
        vol = (vol <= 0) * 100
        vol = vol[np.r_[(M // 2) : M, 0 : (M // 2)]]
        self.model.data_buffer = vol

        def get_offset_variance_maps():
            return np.zeros((self.N, self.N)), np.ones((self.N, self.N))

        self.model.get_offset_variance_maps = get_offset_variance_maps

        self.model.start(self.feature_list)
        self.verify_volume_search()
