"""
ASLM camera communication classes.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

# Standard Library Imports
import logging
import time
import ctypes

# Third Party Imports
import numpy as np

# Local Imports
from aslm.model.analysis import noise_model
from aslm.model.devices.camera.camera_base import CameraBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class SyntheticCameraController:
    def __init__(self):
        self.is_acquiring = False

    def get_property_value(self, name):
        """
        Provides the idprop value after looking it up in the property_dict
        """
        # return self.prop_getvalue(property_dict[name])

        return -1  # {}


class SyntheticCamera(CameraBase):
    def __init__(self, camera_id, model, experiment, verbose=False):
        super().__init__(camera_id, model, experiment, verbose)

        self.x_pixels = experiment.CameraParameters['x_pixels']
        self.y_pixels = experiment.CameraParameters['y_pixels']

        self._mean_background_count = 100.0
        self._noise_sigma = noise_model.compute_noise_sigma(Ib=self._mean_background_count)
        self.blah = noise_model.compute_noise_sigma

        self.camera_controller = SyntheticCameraController()

        if self.verbose:
            print("Synthetic Camera Class Initialized")
        logger.debug("Synthetic Camera Class Initialized")

    def __del__(self):
        pass

    @property
    def serial_number(self):
        return None

    def stop(self):
        self.stop_flag = True

    def report_settings(self):
        pass

    def close_camera(self):
        pass

    def set_sensor_mode(self, mode):
        pass

    def set_exposure_time(self, exposure_time):
        self.camera_exposure_time = exposure_time

    def set_line_interval(self, line_interval_time):
        pass

    def set_binning(self, binning_string):
        self.x_binning = int(binning_string[0])
        self.y_binning = int(binning_string[2])
        self.x_pixels = int(self.x_pixels / self.x_binning)
        self.y_pixels = int(self.y_pixels / self.y_binning)

    def initialize_image_series(self, data_buffer=None, number_of_frames=100):
        self.data_buffer = data_buffer
        self.num_of_frame = number_of_frames
        self.current_frame_idx = 0
        self.pre_frame_idx = 0
        self.camera_controller.is_acquiring = True

    def get_images_in_series(self):
        images = []
        for i in range(10):
            images.append(
                np.random.randint(
                    low=255,
                    size=(
                        self.x_pixels,
                        self.y_pixels),
                    dtype=np.uint16))
        return images

    def close_image_series(self):
        self.pre_frame_idx = 0
        self.current_frame_idx = 0
        self.camera_controller.is_acquiring = False

    def get_image(self):
        image = np.random.normal(1000, 400, (self.y_pixels, self.x_pixels))
        image = np.around(image)
        time.sleep(self.camera_exposure_time / 1000)
        return image

    def initialize_live_mode(self):
        pass

    def get_live_image(self):
        images = []
        for i in range(10):
            images.append(
                np.random.randint(
                    low=255,
                    size=(
                        self.x_pixels,
                        self.y_pixels),
                    dtype=np.uint16))
        return images

    def close_live_mode(self):
        pass

    def generate_new_frame(self):
        # image = np.random.randint(
        #     low=255,
        #     size=(
        #         self.x_pixels,
        #         self.y_pixels),
        #     dtype=np.uint16)
        image = np.random.normal(self._mean_background_count,
                                 self._noise_sigma,
                                 size=(self.x_pixels, self.y_pixels),
                                 ).astype(np.uint16)
        ctypes.memmove(self.data_buffer[self.current_frame_idx].ctypes.data,
                       image.ctypes.data, self.x_pixels * self.y_pixels * 2)
        self.current_frame_idx = (
                                         self.current_frame_idx + 1) % self.num_of_frame

    def get_new_frame(self):
        time.sleep(self.camera_exposure_time / 1000)
        timeout = 500
        while self.pre_frame_idx == self.current_frame_idx and timeout:
            time.sleep(0.001)
            timeout -= 1
        if timeout <= 0:
            return []
        if self.pre_frame_idx < self.current_frame_idx:
            frames = list(range(self.pre_frame_idx, self.current_frame_idx))
        else:
            frames = list(range(self.pre_frame_idx, self.num_of_frame))
            frames += list(range(0, self.current_frame_idx))
        self.pre_frame_idx = self.current_frame_idx
        if self.verbose:
            print('get a new frame from camera', frames)
        logger.debug(f"get a new frame from camera, {frames}")
        return frames

    def set_ROI(self, roi_height=2048, roi_width=2048):
        self.x_pixels = roi_width
        self.y_pixels = roi_height

    def get_minimum_waiting_time(self):
        return 0.01


