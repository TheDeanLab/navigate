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

from queue import Queue
from aslm.model.analysis.boundary_detect import (
    find_tissue_boundary_2d,
    binary_detect,
    map_boundary,
)


class VolumeSearch:
    def __init__(self, model, target_resolution="Nanoscale", target_zoom="N/A"):
        """
        Find the outer boundary of a tissue, moving the stage through z. Assumes
        there is no tissue out-of-frame in the x,y-directions.

        Construct a list of stage positions that will tile the entire tissue
        boundary in x,y,z at target_resolution, target_zoom. Current resolution
        and zoom is self.model.active_microscope_name and
        self.model.configuration["experiment"]["MicroscopeState"]["zoom"].

        Parameters
        ----------
        model : aslm.model.model.Model
            ASLM Model
        target_resolution : str
            Name of microscope to use for tiled imaging of tissue
        target_zoom : str
            Resolution of microscope (target_resolution) to use for tiled imaging
            of tissue
        """
        self.model = model
        self.target_resolution = target_resolution
        self.target_zoom = target_zoom

        self.z_steps = 0
        self.z_step_size = 0
        self.z_pos = 0
        self.f_step_size = 0
        self.f_pos = 0
        self.f_offset = 0
        self.curr_z_index = 0

        self.has_tissue_queue = Queue()
        self.direction = 1  # up: 1; down: -1
        self.has_tissue = False
        self.first_boundary = None
        self.pre_boundary = None

        self.end_flag = False

        self.config_table = {
            "signal": {
                "init": self.pre_signal_func,
                "main": self.signal_func,
                "main-response": self.signal_response_func,
                "end": self.signal_end,
                "cleanup": self.cleanup,
            },
            "data": {
                "init": self.init_data_func,
                "main": self.data_func,
                "end": self.end_data_func,
                "cleanup": self.cleanup,
            },
            "node": {"node_type": "multi-step", "device_related": True},
        }

    def pre_signal_func(self):
        self.model.active_microscope.current_channel = 0
        self.model.active_microscope.prepare_next_channel()

        self.z_pos = float(
            self.model.configuration["experiment"]["StageParameters"]["z"]
        )
        self.f_pos = float(
            self.model.configuration["experiment"]["StageParameters"]["f"]
        )

        self.z_steps = float(
            self.model.configuration["experiment"]["MicroscopeState"]["number_z_steps"]
        )
        self.z_step_size = float(
            self.model.configuration["experiment"]["MicroscopeState"]["step_size"]
        )

        f_start = float(
            self.model.configuration["experiment"]["MicroscopeState"]["start_focus"]
        )
        f_end = float(
            self.model.configuration["experiment"]["MicroscopeState"]["end_focus"]
        )
        self.f_step_size = (f_end - f_start) / self.z_steps

        self.curr_z_index = int(self.z_steps / 2)

        self.direction = 1  # up

    def signal_func(self):
        self.model.logger.debug(f"acquiring at z:{self.curr_z_index}")
        z = self.z_pos + self.curr_z_index * self.z_step_size
        f = self.f_pos + self.curr_z_index * self.f_step_size
        self.model.move_stage({"z_abs": z, "f_abs": f})
        return True

    def signal_response_func(self, *args):
        has_tissue = self.has_tissue_queue.get()

        if not has_tissue or self.curr_z_index == self.z_steps - 1:
            self.curr_z_index = int(self.z_steps / 2)
            self.direction = -1

        self.curr_z_index += self.direction
        return True

    def signal_end(self):
        return self.end_flag

    def init_data_func(self):
        # Establish current and target pixel sizes
        microscope_name = self.model.active_microscope_name
        curr_zoom = self.model.configuration["experiment"]["MicroscopeState"]["zoom"]
        curr_pixel_size = float(
            self.model.configuration["configuration"]["microscopes"][microscope_name][
                "zoom"
            ]["pixel_size"][curr_zoom]
        )
        target_pixel_size = float(
            self.model.configuration["configuration"]["microscopes"][
                self.target_resolution
            ]["zoom"]["pixel_size"][self.target_zoom]
        )

        # consider the image as a square
        img_width = self.model.configuration["experiment"]["CameraParameters"][
            "x_pixels"
        ]

        # The target image size in pixels
        self.mag_ratio = int(curr_pixel_size / target_pixel_size)
        self.target_grid_pixels = int(img_width // self.mag_ratio)
        # The target image size in microns
        self.target_grid_width = img_width * target_pixel_size

        print(
            f"img_width: {img_width} mag_ratio: {self.mag_ratio} target_grid_pixels: "
            f"{self.target_grid_pixels} target_grid_width: {self.target_grid_width} "
        )
        print(
            f"current_scope: {microscope_name} target_scope: {self.target_resolution}"
        )
        print(f"current_resolution: {curr_zoom} target_resolution: {self.target_zoom}")

        # For each axis, establish the offset between this image and the target
        # image as the difference in the physical offsets of the two microscopes
        axes = ["x", "y", "z", "theta", "f"]
        self.offset = [0, 0, 0, 0, 0]
        for i, axis in enumerate(axes):
            t = axis + "_offset"
            self.offset[i] = float(
                self.model.configuration["configuration"]["microscopes"][
                    self.target_resolution
                ]["stage"][t]
            ) - float(
                self.model.configuration["configuration"]["microscopes"][
                    microscope_name
                ]["stage"][t]
            )

        # Add to this the offset between
        self.offset[0] += (
            self.model.configuration["experiment"]["StageParameters"]["x"]
            - (img_width - self.target_grid_pixels) // 2 * curr_pixel_size
        )
        self.offset[1] += (
            self.model.configuration["experiment"]["StageParameters"]["y"]
            - (img_width - self.target_grid_pixels) // 2 * curr_pixel_size
        )
        self.offset[2] += self.z_pos
        self.offset[3] += self.model.configuration["experiment"]["StageParameters"][
            "theta"
        ]
        self.offset[4] += self.f_pos

        self.first_boundary = None
        self.pre_boundary = None
        self.boundary = {}

    def data_func(self, frame_ids):
        for idx in frame_ids:
            img_data = self.model.data_buffer[idx]
            # TODO: make sure set the right threshold_value in
            # model\analysis\boundary_detect.py when use if/else
            # boundary = find_tissue_boundary_2d(img_data, self.target_grid_pixels)

            if self.pre_boundary is None:
                boundary = find_tissue_boundary_2d(img_data, self.target_grid_pixels)
            else:
                off, var = self.model.get_offset_variance_maps()
                boundary = binary_detect(
                    img_data, self.pre_boundary, self.target_grid_pixels, off, var
                )

            self.has_tissue = any(boundary)
            self.boundary[self.curr_z_index] = boundary

            if (
                self.has_tissue
                and self.curr_z_index > 0
                and self.curr_z_index < self.z_steps - 1
            ):
                self.pre_boundary = boundary
            elif self.direction == 1:
                self.pre_boundary = self.first_boundary
            else:
                self.end_flag = True

            self.model.logger.debug(
                f"has tissue? {self.curr_z_index} - {self.has_tissue}"
            )
            self.has_tissue_queue.put(self.has_tissue)

    def end_data_func(self):
        if self.end_flag:
            direction = True
            positions = []
            for z_index in sorted(self.boundary.keys()):
                path = map_boundary(self.boundary[z_index], direction)
                direction = not direction
                positions += map(
                    lambda item: (
                        item[0] * self.target_grid_width + self.offset[0],
                        item[1] * self.target_grid_width + self.offset[1],
                        z_index * self.z_step_size + self.offset[2],
                        self.offset[3],
                        z_index * self.f_step_size + self.offset[4],
                    ),
                    path,
                )
            self.model.event_queue.put(("multiposition", positions))
        return self.end_flag

    def cleanup(self):
        self.has_tissue_queue.put(False)
